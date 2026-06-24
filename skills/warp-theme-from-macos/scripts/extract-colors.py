#!/usr/bin/env python3
"""
extract-colors.py — Extract dominant colors from an aerial thumbnail PNG
and map them to Warp terminal theme roles.

Usage: python3 extract-colors.py --thumbnail <path>

Output (stdout): key=value lines for each Warp color role.
Errors go to stderr; exits with code 1 on failure.
"""

import struct, zlib, sys, argparse
from collections import Counter


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--thumbnail', required=True, help='Path to thumbnail PNG')
    return p.parse_args()


def paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def decode_png(path):
    """Decode a PNG to a flat list of (r, g, b) tuples. No dependencies."""
    with open(path, 'rb') as f:
        data = f.read()

    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError(f"Not a valid PNG file: {path}")

    i = 8
    ihdr = None
    idat_parts = []
    while i < len(data):
        length = struct.unpack('>I', data[i:i + 4])[0]
        ctype = data[i + 4:i + 8].decode('latin1')
        cdata = data[i + 8:i + 8 + length]
        if ctype == 'IHDR':
            ihdr = cdata
        elif ctype == 'IDAT':
            idat_parts.append(cdata)
        elif ctype == 'IEND':
            break
        i += 12 + length

    if not ihdr:
        raise ValueError("No IHDR chunk found")

    w, h = struct.unpack('>II', ihdr[:8])
    color_type = ihdr[9]
    cpp = 4 if color_type == 6 else 3  # RGBA=6, RGB=2

    raw = bytearray(zlib.decompress(b''.join(idat_parts)))
    stride = w * cpp
    pixels = []
    prev = bytearray(stride)

    for row in range(h):
        src = row * (stride + 1)
        ftype = raw[src]
        scanline = bytearray(raw[src + 1:src + 1 + stride])
        recon = bytearray(stride)
        for x in range(stride):
            a = recon[x - cpp] if x >= cpp else 0
            b = prev[x]
            c = prev[x - cpp] if x >= cpp else 0
            v = scanline[x]
            if ftype == 0:
                recon[x] = v
            elif ftype == 1:
                recon[x] = (v + a) & 0xff
            elif ftype == 2:
                recon[x] = (v + b) & 0xff
            elif ftype == 3:
                recon[x] = (v + (a + b) // 2) & 0xff
            elif ftype == 4:
                recon[x] = (v + paeth(a, b, c)) & 0xff
        prev = recon
        for col in range(w):
            p = col * cpp
            pixels.append((recon[p], recon[p + 1], recon[p + 2]))

    return pixels


def bucket(r, g, b):
    return (r // 16) * 16, (g // 16) * 16, (b // 16) * 16


def lum(r, g, b):
    return 0.299 * r + 0.587 * g + 0.114 * b


def lighten(r, g, b, amount=40):
    return min(255, r + amount), min(255, g + amount), min(255, b + amount)


def hex_color(r, g, b):
    return f'#{r:02x}{g:02x}{b:02x}'


def hue_score(r, g, b, target):
    if target == 'red':     return r - max(g, b)
    if target == 'green':   return g - max(r, b)
    if target == 'blue':    return b - max(r, g)
    if target == 'yellow':  return min(r, g) - b
    if target == 'cyan':    return min(g, b) - r
    if target == 'magenta': return min(r, b) - g
    return 0


def map_colors(clusters):
    by_lum = sorted(clusters, key=lambda c: lum(*c))
    n = len(by_lum)

    # Background: darkest cluster
    bg = by_lum[0]

    # Foreground: always near-white — must be readable over a background image.
    # Take a warm hint from the lightest cluster but always push bright.
    lightest = by_lum[-1]
    warm = max(0, lightest[0] - lightest[2]) // 4
    fg = (232, 232, min(232, 216 + warm))

    # Cursor: slightly brighter than foreground
    cursor = (240, 240, min(240, fg[2] + 8))

    # Accent: most saturated mid-range cluster, lifted
    mid = by_lum[n // 3: 2 * n // 3] or by_lum
    accent_base = max(mid, key=lambda c: max(c) - min(c))
    accent = lighten(*accent_base, 30)

    # Derive dominant mid-tone to guide hue synthesis
    dominant = by_lum[n // 3]
    dr, dg, db = dominant

    # Synthesized hue bases blended with dominant tone for cohesion
    hue_bases = {
        'red':     ((max(dr, 130) + dr) // 2, (min(dg, dr - 20) + dg) // 2, (min(db, dr - 20) + db) // 2),
        'green':   ((min(dr, dg - 20) + dr) // 2, (max(dg, 120) + dg) // 2, (min(db, dg - 20) + db) // 2),
        'yellow':  ((max(dr, 140) + dr) // 2, (max(dg, 130) + dg) // 2, (min(db, 80) + db) // 2),
        'blue':    ((min(dr, db - 20) + dr) // 2, (min(dg, db - 20) + dg) // 2, (max(db, 110) + db) // 2),
        'magenta': ((max(dr, 110) + dr) // 2, (min(dg, dr - 30) + dg) // 2, (max(db, 100) + db) // 2),
        'cyan':    ((min(dr, dg - 20) + dr) // 2, (max(dg, 120) + dg) // 2, (max(db, 120) + db) // 2),
    }

    normal_colors = {}
    used = {by_lum[0], by_lum[-1]}
    for hue in ('red', 'green', 'yellow', 'blue', 'magenta', 'cyan'):
        candidates = [c for c in clusters if c not in used]
        if candidates:
            best = max(candidates, key=lambda c: hue_score(*c, hue))
            if hue_score(*best, hue) > 20:
                normal_colors[hue] = best
                used.add(best)
                continue
        normal_colors[hue] = hue_bases[hue]

    normal_black = by_lum[0]
    normal_white = by_lum[n // 2] if n > 1 else by_lum[-1]

    return {
        'background':     bg,
        'foreground':     fg,
        'accent':         accent,
        'cursor':         cursor,
        'normal_black':   normal_black,
        'normal_red':     normal_colors['red'],
        'normal_green':   normal_colors['green'],
        'normal_yellow':  normal_colors['yellow'],
        'normal_blue':    normal_colors['blue'],
        'normal_magenta': normal_colors['magenta'],
        'normal_cyan':    normal_colors['cyan'],
        'normal_white':   normal_white,
        'bright_black':   lighten(*normal_black, 30),
        'bright_red':     lighten(*normal_colors['red'], 40),
        'bright_green':   lighten(*normal_colors['green'], 40),
        'bright_yellow':  lighten(*normal_colors['yellow'], 40),
        'bright_blue':    lighten(*normal_colors['blue'], 40),
        'bright_magenta': lighten(*normal_colors['magenta'], 40),
        'bright_cyan':    lighten(*normal_colors['cyan'], 40),
        'bright_white':   lighten(*normal_white, 50),
    }


def main():
    args = parse_args()

    try:
        pixels = decode_png(args.thumbnail)
    except Exception as e:
        print(f"Error reading PNG: {e}", file=sys.stderr)
        sys.exit(1)

    counts = Counter(bucket(*p) for p in pixels)
    clusters = [rgb for rgb, _ in counts.most_common(20)]

    if not clusters:
        print("Error: no pixels found in thumbnail", file=sys.stderr)
        sys.exit(1)

    colors = map_colors(clusters)
    for key, rgb in colors.items():
        print(f"{key}={hex_color(*rgb)}")


if __name__ == '__main__':
    main()
