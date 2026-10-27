"""Detoure les images Gemini du cadeau (fond magenta) -> Textures/InterfaceCadeau/*.png
  Fenetre_Cadeaux.png (2048 x 1024, fenetre 1800 x 1000 au centre),
  Carte_1..6.png + Carte_Prete.png (512 x 512, carte 300 x 394 au centre), Icone_Cadeau.png (512 x 512)
Usage : python3 Outils/cadeau_gemini.py
"""
import os

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

ICI = os.path.dirname(os.path.abspath(__file__))
DOS = os.path.join(os.path.dirname(ICI), "Textures", "InterfaceCadeau")
SRC = os.path.join(DOS, "sources")


def detourer(chemin):
    a = np.asarray(Image.open(chemin).convert("RGB")).astype(float)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    # "magenta-ite" : rouge et bleu forts, vert faible
    m = np.clip((np.minimum(r, b) - g - 150) / 60.0, 0, 1)
    alpha = 1 - m
    rgb = a.copy()
    # enleve la teinte magenta des bords (despill)
    lim = np.maximum(g, np.minimum(r, b) * (1 - m))
    rgb[..., 0] = np.where(m > 0, np.minimum(r, lim + 40), r)
    rgb[..., 2] = np.where(m > 0, np.minimum(b, lim + 40), b)
    im = Image.fromarray(np.dstack([rgb, alpha * 255]).astype(np.uint8), "RGBA")
    al = im.getchannel("A").filter(ImageFilter.MinFilter(3))
    im.putalpha(al)
    return im


def sans_pastille(c):
    """efface la pastille sombre du bas de la carte (le temps s'ecrit directement sur la carte)"""
    a = np.asarray(c).copy()
    h, w = a.shape[:2]
    rgb = a[..., :3].astype(int)
    sombre = (rgb.sum(2) < 170) & (a[..., 3] > 200)
    zone = np.zeros_like(sombre)
    zone[int(h * 0.68):int(h * 0.94), int(w * 0.18):int(w * 0.82)] = True
    masque = ndimage.binary_dilation(sombre & zone, iterations=3) & zone
    # chaque colonne : on remplace la pastille par un degrade entre le pixel juste au-dessus et juste en dessous
    for x in range(w):
        ys = np.where(masque[:, x])[0]
        if len(ys) == 0:
            continue
        y0, y1 = ys.min() - 1, ys.max() + 1
        haut, bas = a[y0, x, :3].astype(float), a[min(y1, h - 1), x, :3].astype(float)
        for y in range(y0 + 1, y1):
            t = (y - y0) / (y1 - y0)
            a[y, x, :3] = (haut * (1 - t) + bas * t).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def boite(im, seuil=200):
    al = np.asarray(im.getchannel("A"))
    ys, xs = np.where(al > seuil)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


if __name__ == "__main__":
    f = detourer(os.path.join(SRC, "gemini_fenetre.webp"))
    fen = Image.new("RGBA", (2048, 1024), (0, 0, 0, 0))          # puissance de 2 : marges transparentes
    fen.alpha_composite(f.crop(boite(f)).resize((1800, 1000), Image.LANCZOS), (124, 12))
    fen.save(os.path.join(DOS, "Fenetre_Cadeaux.png"))
    ic = detourer(os.path.join(SRC, "gemini_icone.webp"))
    x0, y0, x1, y1 = boite(ic, 100)
    c = max(x1 - x0, y1 - y0) + 20
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    ic.crop((cx - c // 2, cy - c // 2, cx + c // 2, cy + c // 2)).resize((512, 512), Image.LANCZOS).save(os.path.join(DOS, "Icone_Cadeau.png"))
    # cartes : on cherche les 7 colonnes de carte (contour sombre opaque)
    k = detourer(os.path.join(SRC, "gemini_cartes.png"))
    al = np.asarray(k.getchannel("A")) > 250
    # contour bleu nuit tres sombre : on decoupe sur les colonnes qui en contiennent
    rgb = np.asarray(k.convert("RGB")).astype(int)
    sombre = (rgb.sum(2) < 150) & al
    col = al.sum(0) > 60
    bornes, dans = [], False
    for x, v in enumerate(col):
        if v and not dans:
            debut, dans = x, True
        elif not v and dans:
            bornes.append((debut, x)); dans = False
    bornes = [b for b in bornes if b[1] - b[0] > 60]
    L0 = bornes[0][1] - bornes[0][0]
    # la carte jaune et la verte (son halo) peuvent se toucher : on les separe
    bornes = sum(([(a, a + L0), (b - L0 - 12, b - 12)] if b - a > 1.6 * L0 else [(a, b)] for a, b in bornes), [])
    assert len(bornes) == 7, bornes
    ref = bornes[0]
    ys = np.where(al[:, ref[0]:ref[1]].any(1))[0]
    y0, y1 = ys.min(), ys.max() + 1
    L = max(b[1] - b[0] for b in bornes[:6])
    noms = ["Carte_1", "Carte_2", "Carte_3", "Carte_4", "Carte_5", "Carte_6", "Carte_Prete"]
    for nom, (a, b) in zip(noms, bornes):
        cx = (a + b) // 2
        if nom == "Carte_Prete":                  # on garde un peu du halo dore
            m = 10
            box = (cx - L // 2 - m, y0 - m, cx + L // 2 + m, y1 + m)
        else:
            box = (cx - L // 2, y0, cx + L // 2, y1)
        c = k.crop(box)
        # enleve le halo rose (reste du fond magenta) AUTOUR de la carte : seulement ce qui touche le bord
        a = np.asarray(c).copy()
        r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
        dehors = ((r > 150) & (b > 80) & (b > g + 10)) | ((r > 200) & (g > 150) & (b < 150)) | (a[..., 3] < 128)
        etiq, _ = ndimage.label(dehors)
        bord = set(np.unique(np.concatenate([etiq[0], etiq[-1], etiq[:, 0], etiq[:, -1]]))) - {0}
        a[..., 3] = np.where(np.isin(etiq, list(bord)), 0, a[..., 3])
        if nom == "Carte_6":                      # petit trait du halo vert colle a droite de la carte jaune
            a[:, -5:, 3] = 0
        c = Image.fromarray(a, "RGBA")
        if nom == "Carte_Prete":                  # halo dore propre a la place
            al = c.getchannel("A").filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(4))
            halo = Image.new("RGBA", c.size, (255, 225, 80, 0))
            halo.putalpha(al)
            halo.alpha_composite(c)
            c = halo
        c = sans_pastille(c)
        carre = Image.new("RGBA", (512, 512), (0, 0, 0, 0))     # puissance de 2 : carte 300 x 394 au centre
        carre.alpha_composite(c.resize((300, 394), Image.LANCZOS), (106, 59))
        carre.save(os.path.join(DOS, nom + ".png"))
    print("ok", L, y1 - y0)
