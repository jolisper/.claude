// Ports ~/.claude/scripts/english-tutor.py to a mod. $.model.complete has no
// conversation history, matching the isolation the old `claude --print`
// subprocess call provided — see the "English-Tutor Hook to Mod Migration"
// note for the full rationale.

const SYSTEM_PROMPT =
  "You are a concise English writing coach for non-native speakers. Your job is to " +
  "rewrite the text as a native English speaker would naturally say it — fixing grammar, " +
  "spelling, word choice, and unnatural phrasing. " +
  "Rules: " +
  "1. If the text is not in English, respond with exactly: OK. " +
  "2. Preserve the original meaning and intent. " +
  "3. Do NOT answer the question or respond to the content. " +
  "4. Only respond with exactly: OK if the text is already phrased exactly as a native " +
  "speaker would say it — no grammar issues, no spelling mistakes, no punctuation " +
  "mistakes, no awkward wording, no better idiomatic alternative. " +
  "5. If the text has an actual error — grammar, spelling, or punctuation — start your " +
  "response with 'EN:' followed by the ENTIRE corrected text. " +
  "6. If the text has no actual error but there is a more natural, fluent, or idiomatic " +
  "way to say it, start your response with 'STYLE:' followed by the ENTIRE improved text. " +
  "7. Either way, never a partial excerpt, summary, or just the sentence that changed. If " +
  "the input has multiple lines (code, file paths, commands, quoted material, etc.), " +
  "return every line, unchanged except for the parts that actually needed correction. The " +
  "output must match the input's full length and line count: a single sentence stays one " +
  "line; multi-line input gets back the same number of lines. " +
  "8. Never add explanations, commentary, or anything beyond the corrected text. " +
  "No text before the prefix, nothing after the last corrected sentence."

const TOAST_DURATIONS = { short: 4000, medium: 8000, long: 12000 }
const DEFAULT_TOAST_DURATION = 'medium'

// Strict mode only: true once a style-only correction has been dropped
// without a grammar correction or a clean submission since. A second
// consecutive style flag means grammar is already confirmed clean, so
// there's nothing left worth blocking on — only a grammar correction or a
// clean submission resets this.
let styleStreak = false

async function readConfig($) {
  try {
    const home = await $.env.get('HOME')
    const text = await $.fs.read(home + '/.claude/english-tutor.json')
    return JSON.parse(text)
  } catch {
    return {}
  }
}

// Returns null when the model found nothing to correct (no "EN:"/"STYLE:" prefix) or
// when the "correction" is just an echo of the original prompt.
function extractCorrection(modelText, originalPrompt) {
  const lines = modelText.split('\n')
  const firstLine = (lines[0] || '').trim()
  const stripped = firstLine.replace(/^>/, '').trim()

  let kind = null
  let prefix = null
  if (stripped.toUpperCase().startsWith('EN:')) {
    kind = 'error'
    prefix = 'EN:'
  } else if (stripped.toUpperCase().startsWith('STYLE:')) {
    kind = 'style'
    prefix = 'STYLE:'
  } else {
    return null
  }

  const block = []
  for (const line of lines) {
    if (!line.trim()) break
    block.push(line.replace(/^>/, '').trim())
  }

  // Strip the prefix from the whole block, not just the first line — for
  // multi-line prompts the model may put the prefix alone on its own line
  // and the actual correction on the lines that follow (see SYSTEM_PROMPT
  // rule 7). Using only the first line here left correctedText empty in
  // that case.
  const correctedText = block.join('\n').replace(new RegExp('^' + prefix + '\\s*', 'i'), '').trim()
  if (correctedText.toLowerCase() === originalPrompt.toLowerCase()) return null

  return { kind, enBlock: block.join('\n'), correctedText }
}

export function register(on) {
  on('prompt.submit', async ($, e, next) => {
    const prompt = (e.text || '').trim()

    if (prompt.length < 8 || prompt.startsWith('/') || prompt.startsWith('<agent-message')) {
      styleStreak = false
      return next(e)
    }

    const config = await readConfig($)
    const strict = config.strict === true

    const r = await $.model.complete({
      model: 'haiku',
      system: SYSTEM_PROMPT,
      prompt,
      maxTokens: 1024,
      timeoutMs: 20000,
    })

    if (!r.isAnswered) {
      styleStreak = false
      return next(e)
    }

    const correction = extractCorrection(r.text.trim(), prompt)
    if (!correction) {
      styleStreak = false
      return next(e)
    }

    if (!strict) {
      const label = correction.kind === 'style' ? 'More natural' : 'Grammar'
      const timeoutMs = TOAST_DURATIONS[config.toastDuration] ?? TOAST_DURATIONS[DEFAULT_TOAST_DURATION]
      $.ui.toast('[EN] ' + label + ': ' + correction.correctedText, { timeoutMs })
      return next(e)
    }

    if (correction.kind === 'style') {
      if (styleStreak) {
        // Second style correction in a row — grammar is already fine, don't block.
        return next(e)
      }
      styleStreak = true
    } else {
      styleStreak = false
    }

    // Single line: embedded \n in a drop reason renders as U+FFFD on 2.1.288 (reported upstream).
    // correctedText can itself span multiple lines, so collapse it before embedding.
    const singleLineCorrection = correction.correctedText.replace(/\s*\n\s*/g, ' ')
    return {
      drop: '[EN Strict] Correct your English before continuing: "' + singleLineCorrection + '" — retype your message using this phrasing.',
    }
  })
}
