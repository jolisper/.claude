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
  "speaker would say it — no grammar issues, no awkward wording, no better idiomatic " +
  "alternative. If there is a more natural, fluent, or idiomatic way to say it, provide " +
  "the correction even if the original is grammatically correct. " +
  "5. Otherwise, start your response with 'EN:' followed by the full corrected version. " +
  "Match the length of the original: a single sentence stays one line; multiple sentences " +
  "may span multiple lines. " +
  "6. Never add explanations, commentary, or anything beyond the corrected text. " +
  "No text before 'EN:', nothing after the last corrected sentence."

const SIMILARITY_THRESHOLD = 0.85

// Replaces /tmp/en_tutor_strict_<session_id>.txt. One mod instance runs per
// Claude Code session process, so a single variable needs no session-id key.
let pendingCorrection = null

function normalize(text) {
  return text.toLowerCase().replace(/[^\w\s]/g, '').trim().split(/\s+/).filter(Boolean).join(' ')
}

// Approximates difflib.SequenceMatcher.ratio() (2*M/T) using LCS length as M.
// Not algorithmically identical to Python's Ratcliff/Obershelp matcher, but
// close enough to judge whether a retry matches the suggested correction.
function similarityRatio(a, b) {
  const na = normalize(a)
  const nb = normalize(b)
  if (na.length === 0 && nb.length === 0) return 1
  const m = na.length
  const n = nb.length
  const dp = new Array(n + 1).fill(0)
  for (let i = 1; i <= m; i++) {
    let prev = 0
    for (let j = 1; j <= n; j++) {
      const temp = dp[j]
      dp[j] = na[i - 1] === nb[j - 1] ? prev + 1 : Math.max(dp[j], dp[j - 1])
      prev = temp
    }
  }
  return (2 * dp[n]) / (m + n)
}

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

  const correctedText = stripped.slice(3).trim()
  if (correctedText.toLowerCase() === originalPrompt.toLowerCase()) return null

  return { enBlock: block.join('\n'), correctedText }
}

export function register(on) {
  on('prompt.submit', async ($, e, next) => {
    const prompt = (e.text || '').trim()

    if (prompt.length < 8 || prompt.startsWith('/') || prompt.startsWith('<agent-message')) {
      pendingCorrection = null
      return next(e)
    }

    const config = await readConfig($)
    const strict = config.strict === true

    if (strict && pendingCorrection && similarityRatio(prompt, pendingCorrection) >= SIMILARITY_THRESHOLD) {
      pendingCorrection = null
      return next(e)
    }

    const r = await $.model.complete({
      model: 'haiku',
      system: SYSTEM_PROMPT,
      prompt,
      maxTokens: 1024,
      timeoutMs: 20000,
    })

    if (!r.isAnswered) {
      pendingCorrection = null
      return next(e)
    }

    const correction = extractCorrection(r.text.trim(), prompt)
    if (!correction) {
      pendingCorrection = null
      return next(e)
    }

    if (!strict) {
      return next({ ...e, context: correction.enBlock })
    }

    const isRetry = pendingCorrection !== null
    pendingCorrection = correction.correctedText
    const label = isRetry ? 'Still not quite right — try again' : 'Correct your English before continuing'
    // Single line: embedded \n in a drop reason renders as U+FFFD on 2.1.288 (reported upstream).
    return {
      drop: '[EN Strict] ' + label + ': "' + correction.correctedText + '" — retype your message using this phrasing.',
    }
  })
}
