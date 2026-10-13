import type { Correction, Strategy } from '../types.ts'
import { correctionLabel } from '../label.ts'

export function createStrictStrategy(): Strategy {
  // The kind of the last correction that was blocked, or null once reset. A
  // second consecutive correction of the same kind passes through — Haiku
  // flagging the same kind of issue twice in a row, even with different
  // wording, is a strong signal it's nagging rather than catching a real
  // problem (e.g. flip-flopping between singular and plural). Only a
  // different kind or a clean submission resets this.
  let blockedKind: Correction['kind'] | null = null

  return {
    reset() {
      blockedKind = null
    },
    decide(_config, correction) {
      if (correction.kind === blockedKind) {
        return { type: 'pass' }
      }
      blockedKind = correction.kind

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
