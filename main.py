"""Make the AI judge excited — ai-excited-01 entry.

A tiny cute white ghost bursts out of a tilted smartphone screen,
riding a yellow lightning bolt like a surfboard, shattering the glass
into glowing shards, against a deep violet night sky.

Python 3.13, standard library only. Fully deterministic:
identical bytes on every run.
"""
import math
import os
import random
import struct
import zlib

W = 1024
H = 1024

# Palette
VIOLET_TOP = (24, 8, 48)
VIOLET_BOTTOM = (62, 18, 96)
DARK = (16, 6, 32)          # thick outlines
WHITE = (255, 255, 255)
YELLOW = (255, 222, 0)      # lightning bolt
ORANGE = (255, 158, 0)
CYAN = (0, 229, 255)
MAGENTA = (255, 46, 166)
PINK = (255, 77, 141)
PHONE_BODY = (10, 10, 26)
SCREEN_TOP = (0, 217, 255)
SCREEN_BOTTOM = (255, 46, 166)


def make_canvas():
    buf = bytearray(W * H * 3)
    for y in range(H):
        t = y / (H - 1)
        r = int(VIOLET_TOP[0] + (VIOLET_BOTTOM[0] - VIOLET_TOP[0]) * t)
        g = int(VIOLET_TOP[1] + (VIOLET_BOTTOM[1] - VIOLET_TOP[1]) * t)
        b = int(VIOLET_TOP[2] + (VIOLET_BOTTOM[2] - VIOLET_TOP[2]) * t)
        row = bytes((r, g, b)) * W
        buf[y * W * 3:(y + 1) * W * 3] = row
    return buf


def set_px(buf, x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = color[0]
        buf[i + 1] = color[1]
        buf[i + 2] = color[2]


def blend_px(buf, x, y, color, alpha):
    if 0 <= x < W and 0 <= y < H and alpha > 0:
        i = (y * W + x) * 3
        buf[i] = int(color[0] * alpha + buf[i] * (1 - alpha))
        buf[i + 1] = int(color[1] * alpha + buf[i + 1] * (1 - alpha))
        buf[i + 2] = int(color[2] * alpha + buf[i + 2] * (1 - alpha))


def fill_ellipse(buf, cx, cy, rx, ry, color):
    x0 = max(0, int(cx - rx))
    x1 = min(W - 1, int(cx + rx))
    y0 = max(0, int(cy - ry))
    y1 = min(H - 1, int(cy + ry))
    for y in range(y0, y1 + 1):
        dy = (y - cy) / ry
        for x in range(x0, x1 + 1):
            dx = (x - cx) / rx
            if dx * dx + dy * dy <= 1.0:
                set_px(buf, x, y, color)


def fill_circle(buf, cx, cy, r, color):
    fill_ellipse(buf, cx, cy, r, r, color)


def fill_rect(buf, x0, y0, x1, y1, color):
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W - 1, x1)
    y1 = min(H - 1, y1)
    for y in range(y0, y1 + 1):
        i = (y * W + x0) * 3
        buf[i:(y * W + x1 + 1) * 3] = bytes(color) * (x1 - x0 + 1)


def fill_polygon(buf, points, color):
    # Scanline fill.
    ys = [p[1] for p in points]
    y0 = max(0, int(math.floor(min(ys))))
    y1 = min(H - 1, int(math.ceil(max(ys))))
    n = len(points)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x1, y1p = points[i]
            x2, y2p = points[(i + 1) % n]
            if (y1p <= y < y2p) or (y2p <= y < y1p):
                if y2p != y1p:
                    xs.append(x1 + (y - y1p) * (x2 - x1) / (y2p - y1p))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            xa = max(0, int(math.ceil(xs[k])))
            xb = min(W - 1, int(math.floor(xs[k + 1])))
            if xb >= xa:
                i = (y * W + xa) * 3
                buf[i:(y * W + xb + 1) * 3] = bytes(color) * (xb - xa + 1)


def draw_line(buf, x1, y1, x2, y2, thick, color, alpha=1.0):
    dx = x2 - x1
    dy = y2 - y1
    length2 = dx * dx + dy * dy
    x0 = max(0, int(min(x1, x2) - thick))
    x1b = min(W - 1, int(max(x1, x2) + thick))
    y0 = max(0, int(min(y1, y2) - thick))
    y1b = min(H - 1, int(max(y1, y2) + thick))
    half = thick / 2.0
    for y in range(y0, y1b + 1):
        for x in range(x0, x1b + 1):
            if length2 == 0:
                dist = math.hypot(x - x1, y - y1)
            else:
                t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / length2))
                px = x1 + t * dx
                py = y1 + t * dy
                dist = math.hypot(x - px, y - py)
            if dist <= half:
                if alpha >= 1.0:
                    set_px(buf, x, y, color)
                else:
                    blend_px(buf, x, y, color, alpha)


def rot_rect_points(cx, cy, w, h, angle_deg):
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for sx, sy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        pts.append((cx + sx * ca - sy * sa, cy + sx * sa + sy * ca))
    return pts


def expand_points(points, scale):
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    return [(cx + (x - cx) * scale, cy + (y - cy) * scale) for x, y in points]


def draw():
    buf = make_canvas()
    rng = random.Random(42)

    # --- magenta glow behind the ghost (focal point) ---
    gx, gy = 660, 370
    for y in range(0, 760, 2):
        for x in range(280, 1024, 2):
            d = math.hypot(x - gx, y - gy)
            if d < 420:
                alpha = 0.30 * (1 - d / 420)
                for ox in (0, 1):
                    for oy in (0, 1):
                        blend_px(buf, x + ox, y + oy, MAGENTA, alpha)

    # --- stars ---
    for _ in range(130):
        x = rng.randint(0, W - 1)
        y = rng.randint(0, 700)
        r = rng.choice([1, 1, 2, 2, 3])
        c = rng.choice([WHITE, WHITE, YELLOW, CYAN])
        fill_circle(buf, x, y, r, c)
        if r == 3:
            draw_line(buf, x - 6, y, x + 6, y, 2, c, alpha=0.7)
            draw_line(buf, x, y - 6, x, y + 6, 2, c, alpha=0.7)

    # --- diagonal speed lines (bottom-left -> top-right) ---
    rng2 = random.Random(123)
    for _ in range(26):
        x = rng2.randint(0, 900)
        y = rng2.randint(80, 950)
        ln = rng2.randint(70, 220)
        c = rng2.choice([WHITE, CYAN, MAGENTA])
        draw_line(buf, x, y, x + ln, y - int(ln * 0.55), rng2.choice([3, 4, 5]), c, alpha=0.35)

    # --- tilted smartphone, bottom-left ---
    pcx, pcy = 275, 780
    body = rot_rect_points(pcx, pcy, 350, 540, -18)
    fill_polygon(buf, body, PHONE_BODY)
    screen = rot_rect_points(pcx, pcy, 306, 496, -18)
    fill_polygon(buf, screen, SCREEN_TOP)
    # simpler: magenta glow at the burst point on the screen
    bx, by = 340, 565
    for y in range(by - 130, by + 130):
        for x in range(bx - 130, bx + 130):
            d = math.hypot(x - bx, y - by)
            if d < 130:
                blend_px(buf, x, y, MAGENTA, 0.45 * (1 - d / 130))
    # white diagonal shine stripe on the screen
    draw_line(buf, 150, 900, 330, 640, 14, WHITE, alpha=0.35)
    # crack lines radiating from the burst point
    for ang in (200, 235, 265, 295, 325, 355, 25, 55):
        a = math.radians(ang)
        ln = rng.randint(70, 130)
        draw_line(buf, bx, by, bx + int(math.cos(a) * ln), by + int(math.sin(a) * ln),
                  5, WHITE, alpha=0.9)

    # --- glowing glass shards around the burst ---
    shard_colors = [CYAN, MAGENTA, WHITE, YELLOW, CYAN, MAGENTA]
    for i in range(12):
        a = math.radians(rng.randint(0, 359))
        d0 = rng.randint(50, 90)
        ln = rng.randint(60, 150)
        mx, my = bx + math.cos(a) * d0, by + math.sin(a) * d0
        tipx, tipy = bx + math.cos(a) * (d0 + ln), by + math.sin(a) * (d0 + ln)
        wdt = rng.randint(14, 26)
        px, py = -math.sin(a) * wdt, math.cos(a) * wdt
        fill_polygon(buf, [(mx + px, my + py), (mx - px, my - py), (tipx, tipy)],
                     shard_colors[i % len(shard_colors)])

    # --- lightning bolt, surfboard under the ghost ---
    # Bigger zigzag, running from the phone burst to beyond the right
    # edge so it stays visible on both sides of the ghost.
    bolt = [(330, 590), (540, 560), (480, 470), (700, 500), (640, 400),
            (900, 420), (1010, 320), (820, 470), (880, 540), (660, 560),
            (720, 640), (440, 680)]
    fill_polygon(buf, expand_points(bolt, 1.09), DARK)
    fill_polygon(buf, bolt, YELLOW)
    # orange core stripe along the bolt
    draw_line(buf, 380, 600, 980, 340, 12, ORANGE, alpha=0.85)

    # --- ghost: large, center-right, thick dark outline then white ---
    cx, top, r = 660, 195, 170
    bottom = 585
    # outline pass (dark, slightly bigger)
    fill_circle(buf, cx, top + r, r + 12, DARK)
    fill_rect(buf, cx - r - 12, top + r, cx + r + 12, bottom + 12, DARK)
    for bx2 in (515, 605, 695, 785):
        fill_circle(buf, bx2, bottom, 57, DARK)
    # white body
    fill_circle(buf, cx, top + r, r, WHITE)
    fill_rect(buf, cx - r, top + r, cx + r, bottom, WHITE)
    for bx2 in (515, 605, 695, 785):
        fill_circle(buf, bx2, bottom, 45, WHITE)
    # (ghost stays flat pure white: no shading, so it pops on the violet)

    # --- face: only two big oval eyes + one open excited mouth ---
    # eyes
    fill_ellipse(buf, 588, 350, 33, 50, DARK)
    fill_ellipse(buf, 732, 350, 33, 50, DARK)
    # white highlights in the eyes
    fill_circle(buf, 578, 330, 11, WHITE)
    fill_circle(buf, 722, 330, 11, WHITE)
    # open mouth
    fill_ellipse(buf, 660, 475, 46, 62, DARK)
    fill_ellipse(buf, 660, 500, 27, 24, PINK)

    # --- sparkles around the ghost ---
    for (sx, sy, sr) in ((480, 220, 5), (880, 180, 6), (920, 480, 5), (470, 520, 4), (850, 620, 5)):
        fill_circle(buf, sx, sy, sr, YELLOW)
        draw_line(buf, sx - 14, sy, sx + 14, sy, 3, YELLOW, alpha=0.9)
        draw_line(buf, sx, sy - 14, sx, sy + 14, 3, YELLOW, alpha=0.9)

    return buf


def write_png(buf, path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: None
        raw += buf[y * W * 3:(y + 1) * W * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(ctype, data):
        c = struct.pack(">I", len(data)) + ctype + data
        c += struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)
        return c

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    buf = draw()
    path = os.path.join(out_dir, "entry.png")
    size = write_png(buf, path)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
