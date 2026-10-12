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
  "4. Respond with exactly: OK whenever the text has no grammar mistakes, spelling errors, " +
  "or phrasing a native speaker would not naturally produce — even if a different, equally " +
  "valid wording also exists. Do not propose a correction merely because an alternative " +
  "phrasing is possible; only correct text that is actually wrong. " +
  "5. Otherwise, start your response with 'EN:' followed by the ENTIRE corrected text — " +
  "never a partial excerpt, summary, or just the sentence that changed. If the input has " +
  "multiple lines (code, file paths, commands, quoted material, etc.), return every line, " +
  "unchanged except for the parts that actually needed correction. The output must match " +
  "the input's full length and line count: a single sentence stays one line; multi-line " +
  "input gets back the same number of lines. " +
  "6. Never add explanations, commentary, or anything beyond the corrected text. " +
  "No text before 'EN:', nothing after the last corrected sentence."

async function readConfig($) {
  try {
    const home = await $.env.get('HOME')
    const text = await $.fs.read(home + '/.claude/english-tutor.json')
    return JSON.parse(text)
  } catch {
    return {}
  }
}

// Returns null when the model found nothing to correct (no "EN:" prefix) or
// when the "correction" is just an echo of the original prompt.
function extractCorrection(modelText, originalPrompt) {
  const lines = modelText.split('\n')
  const firstLine = (lines[0] || '').trim()
  const stripped = firstLine.replace(/^>/, '').trim()
  if (!stripped.toUpperCase().startsWith('EN:')) return null

  const block = []
  for (const line of lines) {
    if (!line.trim()) break
    block.push(line.replace(/^>/, '').trim())
  }

  // Strip the "EN:" prefix from the whole block, not just the first line —
  // for multi-line prompts the model may put "EN:" alone on its own line
  // and the actual correction on the lines that follow (see SYSTEM_PROMPT
  // rule 5). Using only `stripped` here left correctedText empty in that case.
  const correctedText = block.join('\n').replace(/^EN:\s*/i, '').trim()
  if (correctedText.toLowerCase() === originalPrompt.toLowerCase()) return null

  return { enBlock: block.join('\n'), correctedText }
}

export function register(on) {
  on('prompt.submit', async ($, e, next) => {
    const prompt = (e.text || '').trim()

    if (prompt.length < 8 || prompt.startsWith('/') || prompt.startsWith('<agent-message')) {
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
      return next(e)
    }

    const correction = extractCorrection(r.text.trim(), prompt)
    if (!correction) {
      return next(e)
    }

    if (!strict) {
      return next({ ...e, context: correction.enBlock })
    }

    // Single line: embedded \n in a drop reason renders as U+FFFD on 2.1.288 (reported upstream).
    // correctedText can itself span multiple lines, so collapse it before embedding.
    const singleLineCorrection = correction.correctedText.replace(/\s*\n\s*/g, ' ')
    return {
      drop: '[EN Strict] Correct your English before continuing: "' + singleLineCorrection + '" — retype your message using this phrasing.',
    }
  })
}
