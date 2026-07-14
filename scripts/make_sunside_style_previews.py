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


def expressive_selfie():
    im = grad((220, 200, 180), (160, 140, 130))
    dr = ImageDraw.Draw(im)
    dr.ellipse([28, 10, 100, 95], fill=(210, 175, 155))
    dr.ellipse([46, 42, 56, 52], fill=(40, 30, 25))
    dr.ellipse([72, 42, 82, 52], fill=(40, 30, 25))
    dr.arc([50, 55, 78, 78], 20, 160, fill=(120, 70, 70), width=2)
    phone(dr, 95, 70, 18, 30, screen=(90, 160, 220))
    return label_bar(noise(im), 'selfie + emotion')


def mirror_selfie():
    im = grad((190, 195, 200), (140, 145, 150))
    dr = ImageDraw.Draw(im)
    dr.rectangle([10, 6, 118, 100], outline=(90, 90, 95), width=3)
    dr.ellipse([40, 16, 90, 70], fill=(205, 170, 150))
    phone(dr, 55, 55, 16, 28, screen=(70, 140, 200))
    return label_bar(noise(im, 8), 'mirror selfie')


def hidden_camera():
    im = grad((90, 95, 100), (40, 42, 48))
    dr = ImageDraw.Draw(im)
    person_silhouette(dr, 85, 55, 0.7, fill=(70, 60, 55))
    dr.ellipse([6, 88, 28, 110], fill=(20, 20, 22))
    dr.ellipse([12, 94, 22, 104], fill=(180, 40, 40))
    for i in range(20):
        dr.rectangle([i, i, SIZE - 1 - i, SIZE - 1 - i], outline=(max(0, 30 - i),) * 3)
    return label_bar(noise(im), 'hidden / voyeur')


def tripod_phone():
    im = grad((200, 205, 210), (150, 155, 160))
    dr = ImageDraw.Draw(im)
    person_silhouette(dr, 64, 40, 1.0, fill=(95, 80, 70))
    phone(dr, 56, 78, 16, 26, screen=(100, 180, 230))
    dr.polygon([(64, 104), (58, 118), (70, 118)], fill=(50, 50, 55))
    return label_bar(noise(im, 6), 'tripod full body')


def spontaneous_snap():
    im = grad((180, 170, 160), (120, 130, 140))
    dr = ImageDraw.Draw(im)
    person_silhouette(dr, 50, 45, 0.95, fill=(100, 85, 75))
    for i, o in enumerate(range(0, 24, 4)):
        dr.line([(70 + o, 20 + i), (110 + o, 50 + i)], fill=(200, 200, 205), width=2)
    im = im.filter(ImageFilter.GaussianBlur(0.8))
    return label_bar(noise(im, 18), 'caught in moment')


def through_doorway():
    im = grad((70, 65, 60), (30, 28, 28))
    dr = ImageDraw.Draw(im)
    dr.rectangle([0, 0, 28, SIZE], fill=(55, 45, 38))
    dr.rectangle([78, 0, SIZE, SIZE], fill=(55, 45, 38))
    for y in range(12, 100):
        t = (y - 12) / 88
        col = (int(180 - 40 * t), int(140 - 30 * t), int(100 - 20 * t))
        dr.line([(30, y), (76, y)], fill=col)
    person_silhouette(dr, 55, 50, 0.75, fill=(90, 70, 60))
    return label_bar(noise(im, 10), 'through doorway')


def bedside_night():
    im = grad((25, 20, 35), (10, 8, 15))
    dr = ImageDraw.Draw(im)
    dr.ellipse([10, 70, 118, 120], fill=(60, 40, 50))
    person_silhouette(dr, 70, 55, 0.85, fill=(120, 95, 85))
    dr.ellipse([8, 40, 40, 72], fill=(255, 180, 80))
    return label_bar(noise(im, 20), 'bed / night lamp')


def bathroom_steam():
    im = grad((170, 180, 185), (130, 145, 150))
    dr = ImageDraw.Draw(im)
    for x in range(0, SIZE, 16):
        dr.line([(x, 0), (x, SIZE)], fill=(150, 160, 165))
    for y in range(0, SIZE, 16):
        dr.line([(0, y), (SIZE, y)], fill=(150, 160, 165))
    person_silhouette(dr, 64, 45, 0.9, fill=(160, 140, 130))
    fog = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fog)
    for cx, cy, r in [(30, 40, 35), (90, 50, 40), (50, 80, 45), (70, 30, 25)]:
        fd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(230, 235, 240, 110))
    im = Image.alpha_composite(im.convert('RGBA'), fog).convert('RGB')
    return label_bar(noise(im, 8), 'steam bathroom')


def zoom_crop():
    im = grad((210, 180, 160), (170, 140, 120))
    dr = ImageDraw.Draw(im)
    dr.ellipse([-20, -10, 140, 120], fill=(215, 175, 155))
    dr.ellipse([40, 35, 70, 65], fill=(50, 35, 30))
    dr.ellipse([48, 42, 58, 52], fill=(220, 220, 230))
    for pts in (
        [(8, 8), (8, 28), (28, 8)],
        [(120, 8), (100, 8), (120, 28)],
        [(8, 100), (8, 80), (28, 100)],
        [(120, 100), (120, 80), (100, 100)],
    ):
        dr.line(pts, fill=(255, 255, 255), width=3)
    return label_bar(noise(im, 14), 'tight zoom crop')


def shower_peek():
    im = grad((100, 110, 115), (60, 70, 75))
    dr = ImageDraw.Draw(im)
    dr.polygon([(0, 0), (45, 8), (45, 120), (0, SIZE)], fill=(70, 58, 50))
    for i in range(40):
        dr.ellipse([50 + i // 2, 20 + i, 110 - i // 3, 100 - i // 2], outline=(200, 210, 215))
    person_silhouette(dr, 85, 50, 0.7, fill=(140, 120, 110))
    for x, y in [(60, 30), (72, 45), (95, 35), (88, 60), (100, 50)]:
        dr.ellipse([x, y, x + 3, y + 5], fill=(220, 230, 235))
    return label_bar(noise(im, 10), 'shower peek')


def towel_drop():
    im = grad((175, 185, 190), (130, 140, 145))
    dr = ImageDraw.Draw(im)
    for x in range(0, SIZE, 18):
        dr.line([(x, 0), (x, SIZE)], fill=(155, 165, 170))
    person_silhouette(dr, 58, 35, 0.95, fill=(200, 165, 145))
    dr.polygon([(70, 50), (105, 70), (95, 105), (55, 90)], fill=(230, 230, 235))
    for i in range(3):
        dr.arc([75 + i * 3, 55 + i * 2, 115 + i * 2, 100 + i * 3], 200, 330, fill=(255, 255, 255), width=1)
    return label_bar(noise(im, 10), 'towel dropping')


def send_nudes_crop():
    im = grad((40, 35, 45), (20, 18, 25))
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle([18, 4, 110, 106], radius=8, fill=(25, 25, 28))
    dr.rounded_rectangle([24, 12, 104, 96], radius=4, fill=(55, 45, 50))
    dr.ellipse([42, 16, 86, 58], fill=(200, 160, 140))
    dr.ellipse([48, 55, 80, 95], fill=(195, 155, 135))
    dr.rounded_rectangle([78, 78, 118, 98], radius=4, fill=(60, 180, 90))
    dr.text((82, 82), 'send', fill=(255, 255, 255), font=font_sm)
    return label_bar(noise(im, 12), 'front cam crop')


STYLES = {
    'sunside_expressive_selfie.jpg': expressive_selfie,
    'sunside_mirror_selfie.jpg': mirror_selfie,
    'sunside_hidden_camera.jpg': hidden_camera,
    'sunside_tripod_phone.jpg': tripod_phone,
    'sunside_spontaneous_snap.jpg': spontaneous_snap,
    'sunside_through_doorway.jpg': through_doorway,
    'sunside_bedside_night.jpg': bedside_night,
    'sunside_bathroom_steam.jpg': bathroom_steam,
    'sunside_zoom_crop.jpg': zoom_crop,
    'sunside_shower_peek.jpg': shower_peek,
    'sunside_towel_drop.jpg': towel_drop,
    'sunside_send_nudes_crop.jpg': send_nudes_crop,
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
