# Dibuja las etiquetas (Culata / Cilindro / Parte baja) sobre el render de despiece.
# Uso: python3 etiquetar.py <carpeta_salida>
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

d = sys.argv[1]
img = Image.open(os.path.join(d, '03_despiece.png')).convert('RGB')
labels = json.load(open(os.path.join(d, 'etiquetas.json')))
draw = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 34)
    small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)
except OSError:
    font = small = ImageFont.load_default()
sub = {'CULATA': 'aletas + bujía + tuercas', 'CILINDRO': 'aletas, escape, admisión', 'PARTE BAJA': 'cárter + tapas + piñón + ejes'}
W = img.width
for name, (x, y) in labels.items():
    tx = x + 230 if x < W * 0.55 else x - 430
    ty = y - 60
    draw.line([(x, y), (tx + (0 if tx > x else 400), ty + 22)], fill=(235, 190, 60), width=3)
    draw.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(235, 190, 60))
    draw.text((tx, ty), name, font=font, fill=(245, 245, 245))
    draw.text((tx, ty + 40), sub[name], font=small, fill=(200, 200, 200))
draw.text((40, 30), 'MOTOR AX100 — PIEZAS INDEPENDIENTES', font=font, fill=(245, 245, 245))
img.save(os.path.join(d, '03_despiece_etiquetado.png'))
print('ok')
