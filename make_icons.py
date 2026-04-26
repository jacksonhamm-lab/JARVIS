"""Generate JARVIS PWA icons (192, 512, maskable 512) without external deps.
Pure stdlib: writes PNGs by hand using zlib + struct.
"""
import os, struct, zlib, math

OUT = os.path.dirname(os.path.abspath(__file__))

BG = (10, 10, 15, 255)            # #0a0a0f
ARC = (0, 212, 255, 255)          # #00d4ff
ARC_DIM = (0, 212, 255, 90)
WHITE = (255, 255, 255, 230)

def blend(dst, src):
    sa = src[3] / 255.0
    return (
        int(src[0] * sa + dst[0] * (1 - sa)),
        int(src[1] * sa + dst[1] * (1 - sa)),
        int(src[2] * sa + dst[2] * (1 - sa)),
        255,
    )

def make_canvas(size, bg):
    return [[bg for _ in range(size)] for _ in range(size)]

def put(canvas, x, y, color):
    if 0 <= x < len(canvas) and 0 <= y < len(canvas):
        canvas[y][x] = blend(canvas[y][x], color)

def draw_ring(canvas, cx, cy, r, thickness, color):
    rmin = r - thickness / 2
    rmax = r + thickness / 2
    bb = int(rmax) + 2
    for dy in range(-bb, bb + 1):
        for dx in range(-bb, bb + 1):
            d = math.sqrt(dx * dx + dy * dy)
            if rmin <= d <= rmax:
                # antialias edges
                edge = min(d - rmin, rmax - d)
                a = max(0, min(1, edge))
                c = (color[0], color[1], color[2], int(color[3] * a))
                put(canvas, cx + dx, cy + dy, c)

def draw_arc(canvas, cx, cy, r, thickness, color, start_deg, end_deg):
    rmin = r - thickness / 2
    rmax = r + thickness / 2
    bb = int(rmax) + 2
    for dy in range(-bb, bb + 1):
        for dx in range(-bb, bb + 1):
            d = math.sqrt(dx * dx + dy * dy)
            if rmin <= d <= rmax:
                ang = math.degrees(math.atan2(-dy, dx))  # 0 right, 90 up
                if ang < 0:
                    ang += 360
                if start_deg <= ang <= end_deg:
                    edge = min(d - rmin, rmax - d)
                    a = max(0, min(1, edge))
                    c = (color[0], color[1], color[2], int(color[3] * a))
                    put(canvas, cx + dx, cy + dy, c)

def draw_disc(canvas, cx, cy, r, color):
    bb = int(r) + 2
    for dy in range(-bb, bb + 1):
        for dx in range(-bb, bb + 1):
            d = math.sqrt(dx * dx + dy * dy)
            if d <= r:
                edge = r - d
                a = max(0, min(1, edge))
                c = (color[0], color[1], color[2], int(color[3] * a))
                put(canvas, cx + dx, cy + dy, c)

def draw_glow(canvas, cx, cy, r, color):
    bb = int(r) + 4
    for dy in range(-bb, bb + 1):
        for dx in range(-bb, bb + 1):
            d = math.sqrt(dx * dx + dy * dy)
            if d <= r:
                t = 1 - (d / r)
                a = int(color[3] * t * t)
                if a > 0:
                    put(canvas, cx + dx, cy + dy, (color[0], color[1], color[2], a))

# Bitmap font for the letter J (block-based) — drawn as rectangles
def draw_J(canvas, cx, cy, size, color):
    # J shape: a bar at top, a stem going down, hook at bottom-left
    w = size
    h = int(size * 1.2)
    bar_h = max(2, size // 8)
    stem_w = max(2, size // 7)
    # top bar
    for y in range(cy - h // 2, cy - h // 2 + bar_h):
        for x in range(cx - w // 2, cx + w // 2):
            put(canvas, x, y, color)
    # stem (right-aligned)
    for y in range(cy - h // 2, cy + h // 4):
        for x in range(cx + w // 2 - stem_w, cx + w // 2):
            put(canvas, x, y, color)
    # hook curve (bottom)
    hook_r = w // 2
    for dy in range(0, hook_r + 2):
        for dx in range(-hook_r, hook_r + 1):
            d = math.sqrt(dx * dx + dy * dy)
            if hook_r - stem_w <= d <= hook_r and dy >= 0:
                edge = min(d - (hook_r - stem_w), hook_r - d)
                a = max(0, min(1, edge))
                c = (color[0], color[1], color[2], int(color[3] * a))
                put(canvas, cx + dx, cy + h // 4 + dy, c)

def write_png(path, canvas):
    size = len(canvas)
    raw = bytearray()
    for row in canvas:
        raw.append(0)
        for px in row:
            raw.extend(px)
    def chunk(tag, data):
        c = tag + data
        crc = zlib.crc32(c) & 0xffffffff
        return struct.pack(">I", len(data)) + c + struct.pack(">I", crc)
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)  # 8-bit RGBA
    idat = zlib.compress(bytes(raw), 9)
    iend = b""
    with open(path, "wb") as f:
        f.write(sig)
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", idat))
        f.write(chunk(b"IEND", iend))

def make_icon(size, maskable=False):
    canvas = make_canvas(size, BG)
    cx = size // 2
    cy = size // 2
    inset = 0.85 if maskable else 1.0  # maskable safe zone
    R = int(size * 0.42 * inset)
    # outer faint ring
    draw_ring(canvas, cx, cy, R, max(1, size // 96), ARC_DIM)
    # mid ring
    draw_ring(canvas, cx, cy, int(R * 0.78), max(1, size // 110), ARC_DIM)
    # inner solid ring
    draw_ring(canvas, cx, cy, int(R * 0.55), max(2, size // 70), ARC)
    # arc highlight (top-right quarter)
    draw_arc(canvas, cx, cy, R, max(2, size // 60), ARC, 30, 130)
    # glow center
    draw_glow(canvas, cx, cy, int(R * 0.5), (0, 212, 255, 80))
    # J letter
    draw_J(canvas, cx, cy, int(R * 0.55), WHITE)
    # corner ticks (only for non-maskable to avoid clipping)
    if not maskable:
        tick = max(2, size // 40)
        edge = max(2, size // 25)
        for (sx, sy, dx, dy) in [
            (edge, edge, 1, 1),
            (size - edge - 1, edge, -1, 1),
            (edge, size - edge - 1, 1, -1),
            (size - edge - 1, size - edge - 1, -1, -1),
        ]:
            for i in range(tick):
                put(canvas, sx + i * dx, sy, ARC)
                put(canvas, sx, sy + i * dy, ARC)
    return canvas

def main():
    for size in (192, 512):
        c = make_icon(size, maskable=False)
        write_png(os.path.join(OUT, f"icon-{size}.png"), c)
        print(f"wrote icon-{size}.png")
    c = make_icon(512, maskable=True)
    write_png(os.path.join(OUT, "icon-maskable-512.png"), c)
    print("wrote icon-maskable-512.png")

if __name__ == "__main__":
    main()
