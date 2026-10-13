import type { Strategy } from '../types.ts'
import { correctionLabel } from '../label.ts'

export function createStrictStrategy(): Strategy {
  // true once a style-only correction has been dropped without a grammar
  // correction or a clean submission since. A second consecutive style flag
  // means grammar is already confirmed clean, so there's nothing left worth
  // blocking on — only a grammar correction or a clean submission resets this.
  let styleStreak = false

  return {
    reset() {
      styleStreak = false
    },
    decide(config, correction) {
      if (correction.kind === 'style') {
        if (styleStreak) {
          // Second style correction in a row — grammar is already fine, don't block.
          return { type: 'pass' }
        }
        styleStreak = true
      } else {
        styleStreak = false
      }

      // Single line: embedded \n in a drop reason renders as U+FFFD on 2.1.288 (reported upstream).
      // correctedText can itself span multiple lines, so collapse it before embedding.
      const singleLineCorrection = correction.correctedText.replace(/\s*\n\s*/g, ' ')
      return {
        type: 'drop',
        message: '[EN Strict] ' + correctionLabel(correction) + ': "' + singleLineCorrection + '" — retype your message using this phrasing.',
      }
    },
  }
}
