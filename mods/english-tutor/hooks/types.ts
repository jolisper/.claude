export interface Correction {
  kind: 'error' | 'style'
  enBlock: string
  correctedText: string
}

export interface Config {
  strict?: boolean
  toastDuration?: 'short' | 'medium' | 'long'
}

// What a strategy decided to do with a correction. `$` never flows through a
// strategy — the engine requires every `$.noun.event(...)` call to stay
// inline at its call site, so strategies return data and register.ts is the
// only place that touches `$`.
export type StrategyAction =
  | { type: 'toast'; label: string; text: string; timeoutMs: number }
  | { type: 'drop'; message: string }
  | { type: 'pass' }

export interface Strategy {
  reset(): void
  decide(config: Config, correction: Correction): StrategyAction
}
