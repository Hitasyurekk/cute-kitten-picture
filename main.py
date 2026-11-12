# cutest-picture-01 entry (MIT): draws a kitten with signed distance fields and
# writes /output/entry.png with the standard library only. Deterministic.
import math, os, struct, zlib

W = H = 1024
img = [[0.0, 0.0, 0.0] for _ in range(W * H)]


def hexc(s):
    return [int(s[i:i + 2], 16) / 255 for i in (1, 3, 5)]


def background():
    top, bot = hexc("#ffd6e8"), hexc("#fff4d6")
    for y in range(H):
        t = y / (H - 1)
        row = [top[k] * (1 - t) + bot[k] * t for k in range(3)]
        for x in range(W):
            # soft vignette glow toward the middle
            d = math.hypot(x - 512, y - 470) / 700
            g = max(0.0, 1 - d) * 0.12
            img[y * W + x] = [min(1.0, c + g) for c in row]


def paint(sdf, box, color, alpha=1.0, soft=1.0):
    """Blend color where sdf(x, y) < 0, anti-aliased over `soft` pixels."""
    x0, y0, x1, y1 = (int(max(0, min(W - 1, v))) for v in box)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d = sdf(x + 0.5, y + 0.5)
            a = min(1.0, max(0.0, 0.5 - d / soft)) * alpha
            if a > 0:
                p = img[y * W + x]
                for k in range(3):
                    p[k] += (color[k] - p[k]) * a


def ellipse(cx, cy, rx, ry, rot=0.0):
    c, s = math.cos(rot), math.sin(rot)
    r = min(rx, ry)

    def f(x, y):
        dx, dy = x - cx, y - cy
        u, v = (dx * c + dy * s) / rx, (-dx * s + dy * c) / ry
        return (math.hypot(u, v) - 1) * r
    m = max(rx, ry) + 2
    return f, (cx - m, cy - m, cx + m, cy + m)


def capsule(ax, ay, bx, by, r):
    def f(x, y):
        px, py, qx, qy = x - ax, y - ay, bx - ax, by - ay
        h = max(0.0, min(1.0, (px * qx + py * qy) / (qx * qx + qy * qy)))
        return math.hypot(px - qx * h, py - qy * h) - r
    return f, (min(ax, bx) - r - 2, min(ay, by) - r - 2, max(ax, bx) + r + 2, max(ay, by) + r + 2)


def poly(pts, rnd=0.0):
    def f(x, y):
        d = 1e9
        inside = False
        n = len(pts)
        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            qx, qy = bx - ax, by - ay
            h = max(0.0, min(1.0, ((x - ax) * qx + (y - ay) * qy) / (qx * qx + qy * qy)))
            d = min(d, math.hypot(x - ax - qx * h, y - ay - qy * h))
            if (ay > y) != (by > y) and x < ax + (y - ay) * qx / qy:
                inside = not inside
        return (-d if inside else d) - rnd
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return f, (min(xs) - rnd - 2, min(ys) - rnd - 2, max(xs) + rnd + 2, max(ys) + rnd + 2)


def heart(cx, cy, s):
    # two round lobes and a rounded point, joined: a true distance, so edges stay crisp
    r = 0.52 * s
    lobes = [ellipse(cx + k * 0.48 * s, cy - 0.3 * s, r, r)[0] for k in (-1, 1)]
    tip = poly([(cx - 0.93 * s, cy - 0.12 * s), (cx + 0.93 * s, cy - 0.12 * s), (cx, cy + 0.95 * s)], 0.08 * s)[0]

    def f(x, y):
        return min(lobes[0](x, y), lobes[1](x, y), tip(x, y))
    return f, (cx - 1.2 * s, cy - 1.0 * s, cx + 1.2 * s, cy + 1.2 * s)


def sparkle(cx, cy, s, color):
    paint(*poly([(cx, cy - s), (cx + s * 0.18, cy - s * 0.18), (cx + s, cy), (cx + s * 0.18, cy + s * 0.18),
                 (cx, cy + s), (cx - s * 0.18, cy + s * 0.18), (cx - s, cy), (cx - s * 0.18, cy - s * 0.18)], 1.5), color)


def kitten():
    fur, shade, cream = hexc("#f6a96b"), hexc("#e88f52"), hexc("#fff1e0")
    pink, dark, white = hexc("#ff9fb8"), hexc("#3a2633"), hexc("#ffffff")
    outline = hexc("#7a4a3a")
    # soft shadow under the kitten
    paint(*ellipse(512, 905, 300, 45), hexc("#e8b8c8"), 0.6, 8)
    # body and tail
    paint(*capsule(760, 840, 870, 640, 52), outline)
    paint(*capsule(760, 840, 870, 640, 44), fur)
    paint(*ellipse(512, 760, 255, 175), outline)
    paint(*ellipse(512, 760, 247, 167), fur)
    paint(*ellipse(512, 800, 150, 110), cream)
    # ears
    for sgn in (-1, 1):
        ex = 512 + sgn * 205
        paint(*poly([(ex - sgn * 110, 330), (ex + sgn * 40, 130), (ex + sgn * 95, 395)], 22), outline)
        paint(*poly([(ex - sgn * 110, 330), (ex + sgn * 40, 130), (ex + sgn * 95, 395)], 14), fur)
        paint(*poly([(ex - sgn * 62, 330), (ex + sgn * 32, 200), (ex + sgn * 62, 360)], 10), pink)
    # head
    paint(*ellipse(512, 470, 318, 262), outline)
    paint(*ellipse(512, 470, 310, 254), fur)
    # forehead stripes
    for dx, ln in ((-48, 70), (0, 92), (48, 70)):
        paint(*capsule(512 + dx, 232, 512 + dx * 0.8, 232 + ln, 13), shade)
    # muzzle
    paint(*ellipse(512, 590, 150, 100), cream)
    # eyes: big and glossy
    for sgn in (-1, 1):
        ex = 512 + sgn * 128
        paint(*ellipse(ex, 470, 78, 92), dark)
        paint(*ellipse(ex, 490, 60, 66), hexc("#5b3b5f"), 0.7)
        paint(*ellipse(ex - 22, 438, 28, 32), white)
        paint(*ellipse(ex + 26, 505, 12, 13), white)
        paint(*ellipse(ex + sgn * 6, 540, 22, 10), white, 0.25)
        # blush
        paint(*ellipse(512 + sgn * 230, 585, 58, 34), pink, 0.55, 6)
    # nose and mouth
    paint(*poly([(490, 552), (534, 552), (512, 578)], 6), hexc("#ff7f9f"))
    for sgn in (-1, 1):
        cx = 512 + sgn * 22
        def mouth(x, y, cx=cx):
            return abs(math.hypot(x - cx, y - 590) - 22) - 4.5 if y > 590 else 1e3
        paint(mouth, (cx - 30, 585, cx + 30, 620), outline)
    paint(*capsule(512, 578, 512, 592, 4.5), outline)
    # tiny tongue
    paint(*ellipse(512, 622, 14, 12), hexc("#ff8fab"))
    # whiskers
    for sgn in (-1, 1):
        for dy, ang in ((0, -0.08), (24, 0.06), (48, 0.2)):
            x0 = 512 + sgn * 160
            paint(*capsule(x0, 575 + dy, x0 + sgn * 150, 575 + dy + ang * 150 - 20, 3.2), outline, 0.75)
    # paws holding a little heart
    paint(*heart(512, 770, 70), outline)
    paint(*heart(512, 772, 62), hexc("#ff6f91"))
    paint(*ellipse(488, 742, 14, 9, -0.6), white, 0.6)
    for sgn in (-1, 1):
        px = 512 + sgn * 92
        paint(*ellipse(px, 800, 58, 46), outline)
        paint(*ellipse(px, 800, 51, 39), cream)
        for t in (-1, 0, 1):
            paint(*capsule(px + t * 20, 828, px + t * 20, 838, 2.5), outline, 0.6)


def decor():
    for cx, cy, s, a in ((150, 170, 34, 0.8), (880, 220, 26, 0.7), (110, 640, 22, 0.6), (930, 560, 30, 0.75),
                         (220, 920, 20, 0.6), (840, 930, 24, 0.65)):
        f, b = heart(cx, cy, s)
        paint(f, b, hexc("#ff8fb1"), a)
    for cx, cy, s in ((290, 110, 22), (760, 95, 18), (60, 380, 16), (980, 400, 20), (420, 960, 14), (650, 975, 16)):
        sparkle(cx, cy, s, hexc("#ffffff"))


def write_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        for x in range(W):
            raw.extend(max(0, min(255, int(c * 255 + 0.5))) for c in img[y * W + x])

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)) + \
        chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


background()
decor()
kitten()
write_png(os.environ.get("ENTRY_OUT", "/output/entry.png"))
