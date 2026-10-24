#!/usr/bin/env python3
"""Decide whether a TDD phase should keep cycling.

Usage: stall.py --log PATH --phase N

Reads the '- cycle N.K [covered=C]' lines that log.py wrote for the phase. C is the
cumulative number of spec behaviors with a passing test after that cycle.

Output (key=value):
  status=continue            keep cycling
  status=note                15 cycles done: print a one-line progress note, keep going
  status=stop reason=stalled 3 consecutive cycles added no covered behavior: ask the user
  status=stop reason=max-cycles  30 cycles done: ask the user
  also: cycles=<n> covered=<c>
Errors: status=error/message=/hint= on stdout, exit 2.
"""
import argparse

import speclog as S

NOTE_AT, STALL_WINDOW, MAX_CYCLES = 15, 3, 30


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--log", required=True)
    p.add_argument("--phase", required=True, type=int)
    a = p.parse_args()

    done = S.cycles(S.read(a.log), a.phase)
    if any(c is None for _, c in done[:-1]):
        S.die(f"an earlier cycle of phase {a.phase} has no covered count",
              "run log.py cycle-done for every finished cycle")
    covered = [c for _, c in done if c is not None]  # the in-flight last cycle may not be done yet
    n = len(covered)
    last = covered[-1] if covered else 0

    if n >= MAX_CYCLES:
        status = "status=stop reason=max-cycles"
    elif n >= STALL_WINDOW and last == ([0] + covered)[n - STALL_WINDOW]:
        status = "status=stop reason=stalled"
    elif n == NOTE_AT:
        status = "status=note"
    else:
        status = "status=continue"
    print(status)
    print(f"cycles={n}")
    print(f"covered={last}")


if __name__ == "__main__":
    main()
