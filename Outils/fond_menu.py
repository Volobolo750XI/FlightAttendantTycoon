# Fond du menu PC style GTA : bleu-gris sombre, vignette, 2 lignes fines
import sys
from PIL import Image, ImageDraw, ImageFilter
W, H = 1024, 512
im = Image.new("RGB", (W, H), (28, 42, 46))
halo = Image.new("L", (W, H), 0)
ImageDraw.Draw(halo).ellipse((-200, -150, W+200, H+150), fill=255)
halo = halo.filter(ImageFilter.GaussianBlur(120))
im = Image.composite(im, Image.new("RGB", (W, H), (14, 22, 25)), halo)
d = ImageDraw.Draw(im)
for y in (int(H*0.14), int(H*0.86)):
    d.line((0, y, W, y), fill=(52, 70, 75), width=1)
im.save(sys.argv[1], quality=92)
