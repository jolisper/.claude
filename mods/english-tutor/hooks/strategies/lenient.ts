import type { Strategy } from '../types.ts'
import { correctionLabel } from '../label.ts'

const TOAST_DURATIONS = { short: 4000, medium: 8000, long: 12000 }
const DEFAULT_TOAST_DURATION = 'medium'

// Never blocks — just surfaces the correction as a toast.
export const lenientStrategy: Strategy = {
  reset() {},
  decide(config, correction) {
    const timeoutMs = TOAST_DURATIONS[config.toastDuration ?? DEFAULT_TOAST_DURATION] ?? TOAST_DURATIONS[DEFAULT_TOAST_DURATION]
    return { type: 'toast', label: correctionLabel(correction), text: correction.correctedText, timeoutMs }
  },
}
