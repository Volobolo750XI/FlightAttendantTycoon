"""Refait les 3 fonds du HUD (argent / revenu / rebirth) en 2048x512 : barre épaisse avec dégradé,
contour sombre et rebord 3D, icône d'origine gardée à gauche (taille et position identiques)."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ICI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Textures", "Interface")
W, H = 2048, 512
BARRE = (250, 92, 2030, 452)     # x0, y0, x1, y1 : même place pour les 3
LIMITE = {"FondArgent": 470}   # au-delà : restes de l'ancienne barre
ICONE = 400                      # hauteur de l'icône (px)
COULEURS = {"FondArgent": (76, 209, 55), "FondRevenu": (255, 166, 41), "FondRebirth": (255, 98, 148)}


def ton(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def icone(src, base, xmax=760):
    """Détoure l'icône à gauche de l'ancienne image (tout ce qui n'est pas la barre)."""
    a = np.array(src).astype(int)
    rgb, al = a[..., :3], a[..., 3]
    d = np.sqrt(((rgb - np.array(base)) ** 2).sum(-1))
    col = a[:, 1500, 3] > 200
    ys = np.where(col)[0]
    y0, y1 = ys[0], ys[-1]
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    dans_barre = (yy >= y0 - 4) & (yy <= y1 + 4) & (xx > 330)
    sombre = rgb.sum(-1) < 260          # contour sombre de l'ancienne barre
    # bords haut / bas de l'ancienne barre (traits sombres qui dépassent de l'icône)
    bords = (((abs(yy - y0) < 12) | (abs(yy - y1) < 12)) & (xx > 380) & (sombre | (d < 60)))
    garde = (al > 20) & (xx < xmax) & (~dans_barre | ((d > 95) & ~(sombre & (xx > 560)))) & ~bords
    m = Image.fromarray((garde * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(9)).filter(ImageFilter.MaxFilter(9))
    # on ne garde que les gros morceaux (l'icône), pas les petits restes de trait
    from scipy import ndimage
    lab, n = ndimage.label(np.array(m) > 0)
    if n:
        tailles = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
        ok = [i + 1 for i, t in enumerate(tailles) if t > 0.03 * tailles.max()]
        m = Image.fromarray((np.isin(lab, ok) * 255).astype(np.uint8))
    out = src.copy()
    out.putalpha(Image.fromarray(np.minimum(np.array(m), al).astype(np.uint8)))
    return out.crop(out.getbbox())


def barre(base):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x0, y0, x1, y1 = BARRE
    r = (y1 - y0) // 2 - 20
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x0, y0 + 14, x1, y1 + 14), r, fill=ton(base, 0.30) + (160,))           # ombre portée
    d.rounded_rectangle((x0, y0, x1, y1), r, fill=ton(base, 0.38) + (255,))                    # contour sombre
    d.rounded_rectangle((x0 + 12, y0 + 12, x1 - 12, y1 - 12), r - 12, fill=ton(base, 0.72) + (255,))   # rebord bas
    # face principale avec dégradé vertical (clair en haut)
    face = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(face)
    for y in range(y0 + 12, y1 - 34):
        t = (y - y0) / (y1 - y0)
        g.line([(0, y), (W, y)], fill=ton(base, 1.18 - 0.28 * t) + (255,))
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle((x0 + 12, y0 + 12, x1 - 12, y1 - 34), r - 14, fill=255)
    img.paste(face, (0, 0), mask)
    # reflet en haut
    ref = Image.new("L", (W, H), 0)
    ImageDraw.Draw(ref).rounded_rectangle((x0 + 50, y0 + 30, x1 - 50, y0 + 62), 16, fill=110)
    img.paste((255, 255, 255, 255), (0, 0), ref.filter(ImageFilter.GaussianBlur(4)))
    return img


for nom, base in COULEURS.items():
    src = Image.open(os.path.join(ICI, "source", nom + ".png")).convert("RGBA")
    ic = icone(src, base, LIMITE.get(nom, 760))
    s = ICONE / ic.height
    if ic.width * s > 560:
        s = 560 / ic.width
    ic = ic.resize((round(ic.width * s), round(ic.height * s)), Image.LANCZOS)
    img = barre(base)
    img.alpha_composite(ic, (max(0, 250 - ic.width // 2), (H - ic.height) // 2))
    img.save(os.path.join(ICI, nom + ".png"))
    print(nom, ic.size)
