// Not a TS `enum` — that emits real runtime code, which type-stripping
// environments (Node's --experimental-strip-types, and likely this engine)
// reject. A frozen const object is erasable-syntax-safe and gives the same
// type-safe string values.
export const Mode = {
  Lenient: 'lenient',
  Strict: 'strict',
} as const
