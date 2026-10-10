# Detoure une image Gemini sur fond blanc : enleve le fond ET l'ombre grise,
# en partant des bords (les reflets blancs a l'interieur de l'objet restent).
import sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
src, dst = sys.argv[1], sys.argv[2]
im = np.asarray(Image.open(src).convert("RGB")).astype(float)
mx, mn = im.max(axis=2), im.min(axis=2)
# fond ou ombre : clair et peu colore
fond = (mn > 150) & ((mx - mn) < 28)
lab, _ = ndimage.label(fond)
bord = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
dehors = np.isin(lab, list(bord))
dehors = ndimage.binary_opening(dehors, iterations=2)
objet = ~dehors
objet = ndimage.binary_fill_holes(ndimage.binary_closing(objet, iterations=int(sys.argv[3]) if len(sys.argv) > 3 else 3))
# garder le plus gros morceau
lab2, n = ndimage.label(objet)
if n > 1:
    tailles = ndimage.sum(objet, lab2, range(1, n + 1))
    objet = lab2 == (np.argmax(tailles) + 1)
objet = ndimage.binary_erosion(objet, iterations=2)
a = Image.fromarray((objet * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(1.2))
rgba = Image.fromarray(im.astype("uint8")).convert("RGBA"); rgba.putalpha(a)
ys, xs = np.where(objet)
rgba = rgba.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
s = int(max(rgba.size) * 1.1)
c = Image.new("RGBA", (s, s), (0, 0, 0, 0)); c.paste(rgba, ((s - rgba.width) // 2, (s - rgba.height) // 2))
c.resize((256, 256), Image.LANCZOS).save(dst, optimize=True)
