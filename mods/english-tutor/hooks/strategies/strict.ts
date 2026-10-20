import type { Strategy } from '../types.ts'
import { correctionLabel } from '../label.ts'

export function createStrictStrategy(): Strategy {
  return {
    // A second consecutive correction of the same kind passes through — Haiku
    // flagging the same kind of issue twice in a row, even with different
    // wording, is a strong signal it's nagging rather than catching a real
    // problem (e.g. flip-flopping between singular and plural). "Consecutive"
    // is read from the session's own log: the previous entry must be a blocked
    // correction of the same kind. A clean, passed or other-kind entry means
    // this one is blocked.
    decide(_config, correction, previous) {
      if (previous && previous.action === 'drop' && previous.result === correction.kind) {
        return { type: 'pass' }
      }

      // Single line: embedded \n in a drop reason renders as U+FFFD on 2.1.288, still on 2.1.300 (reported upstream).
      // correctedText can itself span multiple lines, so collapse it before embedding.
      const singleLineCorrection = correction.correctedText.replace(/\s*\n\s*/g, ' ')
      return {
        type: 'drop',
        message: '[EN Strict] ' + correctionLabel(correction) + ': "' + singleLineCorrection + '" — retype your message using this phrasing.',
      }
    },
  }
}
