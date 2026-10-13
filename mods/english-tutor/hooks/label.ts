import type { Correction } from './types.ts'

export function correctionLabel(correction: Correction): string {
  return correction.kind === 'style' ? 'STYLE' : 'GRAMMAR'
}
