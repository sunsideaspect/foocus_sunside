"""Generate 128x128 style preview JPGs for Sunside styles (Fooocus hover overlay)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import random

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'sdxl_styles', 'samples')
SIZE = 128

try:
    font_sm = ImageFont.truetype('arial.ttf', 9)
except Exception:
    font_sm = ImageFont.load_default()


def noise(im, amount=12, seed=42):
    px = im.load()
    w, h = im.size
    rnd = random.Random(seed)
    for _ in range(w * h // 8):
        x, y = rnd.randrange(w), rnd.randrange(h)
        r, g, b = px[x, y]
        d = rnd.randint(-amount, amount)
        px[x, y] = (max(0, min(255, r + d)), max(0, min(255, g + d)), max(0, min(255, b + d)))
    return im


def grad(c1, c2):
    im = Image.new('RGB', (SIZE, SIZE))
    dr = ImageDraw.Draw(im)
    for i in range(SIZE):
        t = i / (SIZE - 1)
        col = tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))
        dr.line([(0, i), (SIZE, i)], fill=col)
    return im


def label_bar(im, text):
    dr = ImageDraw.Draw(im)
    dr.rectangle([0, SIZE - 22, SIZE, SIZE], fill=(12, 12, 14))
    dr.text((4, SIZE - 17), text, fill=(240, 240, 240), font=font_sm)
    return im


def person_silhouette(dr, cx, cy, scale=1.0, fill=(40, 35, 32)):
    r = int(10 * scale)
    dr.ellipse([cx - r, cy - r - 18, cx + r, cy - 18 + r], fill=fill)
    dr.rounded_rectangle(
        [cx - int(16 * scale), cy - 8, cx + int(16 * scale), cy + int(40 * scale)],
        radius=8,
        fill=fill,
    )


def phone(dr, x, y, w=14, h=24, fill=(30, 30, 35), screen=(180, 210, 230)):
    dr.rounded_rectangle([x, y, x + w, y + h], radius=2, fill=fill)
    dr.rectangle([x + 2, y + 3, x + w - 2, y + h - 4], fill=screen)


def phone_raw():
    im = grad((220, 200, 180), (160, 140, 130))
    dr = ImageDraw.Draw(im)
    person_silhouette(dr, 64, 40, 0.95, fill=(200, 165, 145))
    phone(dr, 95, 70, 18, 30, screen=(90, 160, 220))
    return label_bar(noise(im, 22), 'phone raw')


def mirror_glass():
    im = grad((190, 195, 200), (140, 145, 150))
    dr = ImageDraw.Draw(im)
    dr.rectangle([10, 6, 118, 100], outline=(90, 90, 95), width=3)
    person_silhouette(dr, 64, 35, 0.8, fill=(205, 170, 150))
    phone(dr, 55, 55, 16, 28, screen=(70, 140, 200))
    return label_bar(noise(im, 8), 'mirror glass')


def cctv_grain():
    im = grad((90, 95, 100), (40, 42, 48))
    dr = ImageDraw.Draw(im)
    person_silhouette(dr, 85, 55, 0.7, fill=(70, 60, 55))
    dr.ellipse([6, 88, 28, 110], fill=(20, 20, 22))
    dr.ellipse([12, 94, 22, 104], fill=(180, 40, 40))
    for i in range(20):
        dr.rectangle([i, i, SIZE - 1 - i, SIZE - 1 - i], outline=(max(0, 30 - i),) * 3)
    return label_bar(noise(im, 28), 'cctv grain')


def tripod_still():
    im = grad((200, 205, 210), (150, 155, 160))
    dr = ImageDraw.Draw(im)
    person_silhouette(dr, 64, 40, 1.0, fill=(95, 80, 70))
    phone(dr, 56, 78, 16, 26, screen=(100, 180, 230))
    dr.polygon([(64, 104), (58, 118), (70, 118)], fill=(50, 50, 55))
    return label_bar(noise(im, 6), 'tripod still')


def candid_snap():
    im = grad((180, 170, 160), (120, 130, 140))
    dr = ImageDraw.Draw(im)
    person_silhouette(dr, 50, 45, 0.95, fill=(100, 85, 75))
    for i, o in enumerate(range(0, 24, 4)):
        dr.line([(70 + o, 20 + i), (110 + o, 50 + i)], fill=(200, 200, 205), width=2)
    im = im.filter(ImageFilter.GaussianBlur(0.8))
    return label_bar(noise(im, 18), 'candid snap')


def doorway_ambient():
    im = grad((70, 65, 60), (30, 28, 28))
    dr = ImageDraw.Draw(im)
    dr.rectangle([0, 0, 28, SIZE], fill=(55, 45, 38))
    dr.rectangle([78, 0, SIZE, SIZE], fill=(55, 45, 38))
    for y in range(12, 100):
        t = (y - 12) / 88
        col = (int(180 - 40 * t), int(140 - 30 * t), int(100 - 20 * t))
        dr.line([(30, y), (76, y)], fill=col)
    person_silhouette(dr, 55, 50, 0.75, fill=(90, 70, 60))
    return label_bar(noise(im, 10), 'doorway')


def night_iso():
    im = grad((25, 20, 35), (10, 8, 15))
    dr = ImageDraw.Draw(im)
    dr.ellipse([10, 70, 118, 120], fill=(60, 40, 50))
    person_silhouette(dr, 70, 55, 0.85, fill=(120, 95, 85))
    dr.ellipse([8, 40, 40, 72], fill=(255, 180, 80))
    return label_bar(noise(im, 26), 'night iso')


def steam_humidity():
    im = grad((170, 180, 185), (130, 145, 150))
    dr = ImageDraw.Draw(im)
    for x in range(0, SIZE, 16):
        dr.line([(x, 0), (x, SIZE)], fill=(150, 160, 165))
    person_silhouette(dr, 64, 45, 0.9, fill=(160, 140, 130))
    fog = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fog)
    for cx, cy, r in [(30, 40, 35), (90, 50, 40), (50, 80, 45), (70, 30, 25)]:
        fd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(230, 235, 240, 110))
    im = Image.alpha_composite(im.convert('RGBA'), fog).convert('RGB')
    return label_bar(noise(im, 8), 'steam')


def close_detail():
    im = grad((210, 180, 160), (170, 140, 120))
    dr = ImageDraw.Draw(im)
    dr.ellipse([-20, -10, 140, 120], fill=(215, 175, 155))
    dr.ellipse([40, 35, 70, 65], fill=(50, 35, 30))
    return label_bar(noise(im, 14), 'close detail')


def wet_room():
    im = grad((100, 110, 115), (60, 70, 75))
    dr = ImageDraw.Draw(im)
    person_silhouette(dr, 85, 50, 0.7, fill=(140, 120, 110))
    for x, y in [(60, 30), (72, 45), (95, 35), (88, 60), (100, 50)]:
        dr.ellipse([x, y, x + 3, y + 5], fill=(220, 230, 235))
    return label_bar(noise(im, 10), 'wet room')


def post_shower():
    im = grad((175, 185, 190), (130, 140, 145))
    dr = ImageDraw.Draw(im)
    person_silhouette(dr, 58, 35, 0.95, fill=(200, 165, 145))
    dr.polygon([(70, 50), (105, 70), (95, 105), (55, 90)], fill=(230, 230, 235))
    return label_bar(noise(im, 10), 'post shower')


def dim_room():
    im = grad((40, 35, 45), (20, 18, 25))
    dr = ImageDraw.Draw(im)
    person_silhouette(dr, 64, 45, 0.9, fill=(120, 95, 85))
    dr.ellipse([90, 20, 118, 48], fill=(255, 200, 100))
    return label_bar(noise(im, 20), 'dim room')


STYLES = {
    'sunside_phone_raw.jpg': phone_raw,
    'sunside_mirror_glass.jpg': mirror_glass,
    'sunside_cctv_grain.jpg': cctv_grain,
    'sunside_tripod_still.jpg': tripod_still,
    'sunside_candid_snap.jpg': candid_snap,
    'sunside_doorway_ambient.jpg': doorway_ambient,
    'sunside_night_iso.jpg': night_iso,
    'sunside_steam_humidity.jpg': steam_humidity,
    'sunside_close_detail.jpg': close_detail,
    'sunside_wet_room.jpg': wet_room,
    'sunside_post_shower.jpg': post_shower,
    'sunside_dim_room.jpg': dim_room,
}


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, fn in STYLES.items():
        path = os.path.abspath(os.path.join(OUT_DIR, name))
        im = fn()
        im.save(path, 'JPEG', quality=85, optimize=True)
        print(f'{name} ({os.path.getsize(path)} bytes)')
    print(f'done: {len(STYLES)} previews -> {os.path.abspath(OUT_DIR)}')


if __name__ == '__main__':
    main()
