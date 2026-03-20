#!/usr/bin/env bash
set -o pipefail

# Usage: sdk.sh --candidate CANDIDATE (--version VERSION [--install] | --list-available [FILTER])
#
# --version VERSION          Activate a specific version (install with --install if missing)
# --list-available [FILTER]  List available versions for a candidate, optionally filtered by prefix.
#                            Outputs one identifier per line, sorted: tem > amzn > zulu > graalce > others.
#
# Output for --version (structured key=value lines):
#   status=ok            — already installed; activated and set as default
#   status=installed     — freshly installed; activated and set as default
#   status=not-installed — not present locally; re-run with --install
#   status=error         — unexpected failure (details on stderr)
#
# Exit codes: 0 = ok/installed/list, 1 = error, 2 = not-installed

CANDIDATE=""
VERSION=""
DO_INSTALL=false
LIST_MODE=false
LIST_FILTER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --candidate)       CANDIDATE="$2"; shift 2 ;;
    --version)         VERSION="$2";   shift 2 ;;
    --install)         DO_INSTALL=true; shift ;;
    --list-available)
      LIST_MODE=true
      if [[ $# -gt 1 && "$2" != --* ]]; then
        LIST_FILTER="$2"; shift 2
      else
        shift
      fi ;;
    --help)
      printf 'Usage: sdk.sh --candidate CANDIDATE --version VERSION [--install]\n'
      printf '       sdk.sh --candidate CANDIDATE --list-available [FILTER]\n'
      printf '\n'
      printf '  --candidate       SDKMAN candidate name (e.g. java, node, gradle, maven)\n'
      printf '  --version         Full SDKMAN version identifier (e.g. 21.0.3-tem, 20.0.2-amzn)\n'
      printf '  --install         Install the candidate if not already present\n'
      printf '  --list-available  List available versions; optionally filter by prefix (e.g. 17)\n'
      printf '\n'
      printf 'Distribution priority for --list-available: tem > amzn > zulu > graalce > others\n'
      exit 0 ;;
    *) printf 'Error: unknown argument: %s\n' "$1" >&2; exit 1 ;;
  esac
done

if [[ -z "$CANDIDATE" ]]; then
  printf 'Error: --candidate is required.\n' >&2; exit 1
fi

# Locate and source SDKMAN
SDKMAN_INIT="${SDKMAN_DIR:-$HOME/.sdkman}/bin/sdkman-init.sh"
if [[ ! -f "$SDKMAN_INIT" ]]; then
  printf 'Error: SDKMAN not found at %s\n' "$SDKMAN_INIT" >&2
  printf 'Install SDKMAN from https://sdkman.io before using this skill.\n' >&2
  exit 1
fi

# shellcheck source=/dev/null
# sdkman-init.sh and the sdk function itself reference variables that may be unbound;
# nounset cannot be used in this script.
source "$SDKMAN_INIT"

# ── List mode ──────────────────────────────────────────────────────────────────
if [[ "$LIST_MODE" == "true" ]]; then
  # sdk list outputs a pipe-delimited table; the identifier is the last column.
  # Priority map: tem=1, amzn=2, zulu=3, graalce=4, everything else=5.
  sdk list "$CANDIDATE" 2>/dev/null \
    | awk -F'|' '
        {
          id = $NF
          gsub(/[[:space:]]/, "", id)
          if (id ~ /^[0-9]/) print id
        }
      ' \
    | grep "^${LIST_FILTER}" \
    | awk '
        BEGIN {
          split("tem amzn zulu graalce", prio)
          for (i in prio) order[prio[i]] = i
        }
        {
          n = split($0, a, "-")
          dist = a[n]
          p = (dist in order) ? order[dist] : 99
          print p "\t" $0
        }
      ' \
    | sort -t$'\t' -k1,1n -k2,2Vr \
    | cut -f2 \
    | head -20
  exit 0
fi

# ── Activate / install mode ────────────────────────────────────────────────────
if [[ -z "$VERSION" ]]; then
  printf 'Error: --version is required (or use --list-available).\n' >&2; exit 1
fi

CANDIDATE_HOME="${SDKMAN_DIR:-$HOME/.sdkman}/candidates/$CANDIDATE/$VERSION"

if [[ -d "$CANDIDATE_HOME" ]]; then
  sdk use "$CANDIDATE" "$VERSION" >/dev/null 2>&1 || true
  sdk default "$CANDIDATE" "$VERSION" >/dev/null 2>&1 || true
  printf 'status=ok\n'
  printf 'candidate=%s\n' "$CANDIDATE"
  printf 'version=%s\n' "$VERSION"
  printf 'home=%s\n' "$CANDIDATE_HOME"
  exit 0
fi

if [[ "$DO_INSTALL" == "false" ]]; then
  printf 'status=not-installed\n'
  printf 'candidate=%s\n' "$CANDIDATE"
  printf 'version=%s\n' "$VERSION"
  exit 2
fi

# Install
if ! sdk install "$CANDIDATE" "$VERSION" </dev/null; then
  printf 'status=error\n' >&2
  printf 'message=install-failed for %s %s\n' "$CANDIDATE" "$VERSION" >&2
  exit 1
fi

sdk default "$CANDIDATE" "$VERSION" >/dev/null 2>&1 || true

CANDIDATE_HOME="${SDKMAN_DIR:-$HOME/.sdkman}/candidates/$CANDIDATE/$VERSION"

printf 'status=installed\n'
printf 'candidate=%s\n' "$CANDIDATE"
printf 'version=%s\n' "$VERSION"
printf 'home=%s\n' "$CANDIDATE_HOME"
