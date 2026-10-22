# Kit d'interface cartoon "argent" du PC (Textures/InterfacePC) : verts pétants, gros contours
# foncés, reflets brillants. Aucune couleur jaune.
#   Fond.png                         : fond plein écran (2048 x 1024) : vert, rayons, billets/pièces
#   Carte / CarteChoisie / CarteAchetee / CarteGrise : les cartes de vol (512 x 1024)
#   BoutonVert / BoutonCyan / BoutonGris / BoutonChoisi : gros boutons (512 x 256)
#   OngletVert / OngletSombre        : onglets et CLOSE (512 x 128)
#   Bandeau.png                      : le bandeau "prochain vol" (1024 x 128)
#   python Outils/interface_pc.py
import math, os, random
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "..", "Textures", "InterfacePC")
K = 3
NOIR = (5, 46, 22, 255)          # contour vert très foncé
POLICE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def hexa(h, a=255):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def degrade(l, h, haut, bas):
    a, b = hexa(haut), hexa(bas)
    g = Image.new("RGBA", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        g.putpixel((0, y), tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3)) + (255,))
    return g.resize((l, h))


def masque_arrondi(l, h, box, r):
    m = Image.new("L", (l, h), 0)
    ImageDraw.Draw(m).rounded_rectangle(box, r, fill=255)
    return m


def forme(nom, l, h, rayon, ep, haut, bas, bague=None, bague_ep=0, reflet=70):
    """Rectangle arrondi cartoon : contour foncé, dégradé, bague de couleur, reflet en haut."""
    L, H, r, e = l * K, h * K, rayon * K, ep * K
    im = Image.new("RGBA", (L, H), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, L - 1, H - 1], r, fill=NOIR)
    x0 = e
    if bague:
        b = bague_ep * K
        ImageDraw.Draw(im).rounded_rectangle([e, e, L - 1 - e, H - 1 - e], r - e, fill=hexa(bague))
        x0 = e + b
    box = [x0, x0, L - 1 - x0, H - 1 - x0]
    m = masque_arrondi(L, H, box, max(4, r - x0))
    im.paste(degrade(L, H, haut, bas), (0, 0), m)
    # reflet brillant en haut
    rf = Image.new("L", (L, H), 0)
    hr = int((H - 2 * x0) * 0.22)
    ImageDraw.Draw(rf).rounded_rectangle([x0 + r // 2, x0 + int(H * 0.04), L - 1 - x0 - r // 2, x0 + int(H * 0.04) + hr], hr // 2, fill=reflet)
    im.paste(Image.new("RGBA", (L, H), (255, 255, 255, 255)), (0, 0), ImageChops.multiply(rf, m))
    im.resize((l, h), Image.LANCZOS).save(os.path.join(SORTIE, nom + ".png"))


def fond():
    L, H = 2048 * 2, 1024 * 2
    cx, cy = L / 2, H * 0.42
    im = Image.new("RGBA", (L, H))
    # dégradé radial vert
    centre, bord = hexa("1FA055"), hexa("052E16")
    import numpy as np
    y, x = np.mgrid[0:H, 0:L].astype(np.float32)
    d = np.clip(np.sqrt(((x - cx) / (L * 0.62)) ** 2 + ((y - cy) / (H * 0.85)) ** 2), 0, 1) ** 1.2
    c = np.array(centre[:3], np.float32) * (1 - d[..., None]) + np.array(bord[:3], np.float32) * d[..., None]
    # rayons de soleil cartoon
    ang = np.arctan2(y - cy, x - cx)
    rayons = (np.sin(ang * 14) > 0.35).astype(np.float32) * (1 - d) * 0.10
    c = c + 255 * rayons[..., None] * np.array([0.6, 1.0, 0.7], np.float32)
    im = Image.fromarray(np.clip(c, 0, 255).astype(np.uint8)).convert("RGBA")
    # billets et pièces flottants, très discrets
    deco = Image.new("RGBA", (L, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(deco)
    rnd = random.Random(7)
    f = ImageFont.truetype(POLICE, 120)
    for i in range(46):
        px, py = rnd.uniform(0, L), rnd.uniform(0, H)
        s = rnd.uniform(0.7, 1.4)
        if rnd.random() < 0.5:
            # pièce
            rr = 70 * s
            dd.ellipse([px - rr, py - rr, px + rr, py + rr], fill=(167, 243, 208, 34), outline=(220, 252, 231, 50), width=int(10 * s))
            dd.text((px, py), "$", font=ImageFont.truetype(POLICE, int(100 * s)), fill=(220, 252, 231, 46), anchor="mm")
        else:
            # billet
            bl, bh = 230 * s, 110 * s
            billet = Image.new("RGBA", (int(bl) + 40, int(bh) + 40), (0, 0, 0, 0))
            bd = ImageDraw.Draw(billet)
            bd.rounded_rectangle([20, 20, 20 + bl, 20 + bh], 14 * s, fill=(134, 239, 172, 30), outline=(220, 252, 231, 46), width=int(8 * s))
            bd.text((20 + bl / 2, 20 + bh / 2), "$", font=ImageFont.truetype(POLICE, int(80 * s)), fill=(220, 252, 231, 46), anchor="mm")
            billet = billet.rotate(rnd.uniform(-35, 35), expand=True, resample=Image.BICUBIC)
            deco.alpha_composite(billet, (int(px - billet.width / 2), int(py - billet.height / 2)))
    deco = deco.filter(ImageFilter.GaussianBlur(3))
    im.alpha_composite(deco)
    # vignette
    v = Image.fromarray((np.clip(1 - (d - 0.55) * 0.9, 0.55, 1) * 255).astype(np.uint8))
    im = Image.composite(im, Image.new("RGBA", (L, H), (2, 30, 14, 255)), v)
    im.resize((2048, 1024), Image.LANCZOS).save(os.path.join(SORTIE, "Fond.png"))


if __name__ == "__main__":
    os.makedirs(SORTIE, exist_ok=True)
    fond()
    # cartes de vol : corps vert, bague de couleur selon l'état
    forme("Carte", 512, 1024, 70, 14, "1B7A43", "0F5132", bague="BBF7D0", bague_ep=8, reflet=40)
    forme("CarteChoisie", 512, 1024, 70, 14, "1B7A43", "0F5132", bague="4ADE80", bague_ep=16, reflet=40)
    forme("CarteAchetee", 512, 1024, 70, 14, "1B7A43", "0F5132", bague="22D3EE", bague_ep=12, reflet=40)
    forme("CarteGrise", 512, 1024, 70, 14, "3F4F5F", "2A3542", bague="64748B", bague_ep=8, reflet=25)
    # boutons
    forme("BoutonVert", 512, 256, 70, 12, "4ADE80", "15803D", reflet=90)
    forme("BoutonCyan", 512, 256, 70, 12, "22D3EE", "0E7490", reflet=90)
    forme("BoutonGris", 512, 256, 70, 12, "94A3B8", "475569", reflet=60)
    forme("BoutonChoisi", 512, 256, 70, 12, "10B981", "065F46", reflet=80)
    # onglets
    forme("OngletVert", 512, 128, 56, 10, "4ADE80", "15803D", reflet=90)
    forme("OngletSombre", 512, 128, 56, 10, "1F6B45", "0B3D24", reflet=50)
    # bandeau du prochain vol
    forme("Bandeau", 1024, 128, 56, 10, "22C55E", "116D35", reflet=70)
    print("ok")
