// Ports ~/.claude/scripts/english-tutor.py to a mod. $.model.complete has no
// conversation history, matching the isolation the old `claude --print`
// subprocess call provided — see the "English-Tutor Hook to Mod Migration"
// note for the full rationale.

import type { EngineInterface, On } from 'claude-code'
import type { Config, Correction } from './types.ts'
import { Mode } from './mode.ts'
import { lenientStrategy } from './strategies/lenient.ts'
import { createStrictStrategy } from './strategies/strict.ts'

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

const strictStrategy = createStrictStrategy()

const STRATEGIES = {
  [Mode.Lenient]: lenientStrategy,
  [Mode.Strict]: strictStrategy,
}

async function readConfig($: EngineInterface): Promise<Config> {
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
function extractCorrection(modelText: string, originalPrompt: string): Correction | null {
  const lines = modelText.split('\n')
  const firstLine = (lines[0] || '').trim()
  const stripped = firstLine.replace(/^>/, '').trim()

  let kind: 'error' | 'style'
  let prefix: string
  if (stripped.toUpperCase().startsWith('EN:')) {
    kind = 'error'
    prefix = 'EN:'
  } else if (stripped.toUpperCase().startsWith('STYLE:')) {
    kind = 'style'
    prefix = 'STYLE:'
  } else {
    return null
  }

  const block: string[] = []
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

export function register(on: On) {
  on('prompt.submit', async ($, e, next) => {
    const prompt = (e.text || '').trim()

    if (prompt.length < 8 || prompt.startsWith('/') || prompt.startsWith('<agent-message')) {
      strictStrategy.reset()
      return next(e)
    }

    const config = await readConfig($)
    const mode = config.strict === true ? Mode.Strict : Mode.Lenient
    const strategy = STRATEGIES[mode]

    const r = await $.model.complete({
      model: 'haiku',
      system: SYSTEM_PROMPT,
      prompt,
      maxTokens: 1024,
      timeoutMs: 20000,
    })

    if (!r.isAnswered) {
      strictStrategy.reset()
      return next(e)
    }

    const correction = extractCorrection(r.text.trim(), prompt)
    if (!correction) {
      strictStrategy.reset()
      return next(e)
    }

    const action = strategy.decide(config, correction)
    switch (action.type) {
      case 'toast':
        $.ui.toast('[EN] ' + action.label + ': ' + action.text, { timeoutMs: action.timeoutMs })
        return next(e)
      case 'drop':
        return { drop: action.message }
      case 'pass':
        return next(e)
    }
  })
}
