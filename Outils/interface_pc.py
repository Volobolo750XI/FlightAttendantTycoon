# Kit d'interface cartoon "argent" du PC (Textures/InterfacePC) : verts pétants, gros contours
# foncés, reflets brillants. Aucune couleur jaune.
#   Fond.png                         : fond plein écran (2048 x 1024) : vert, rayons, billets/pièces
#   Carte / CarteChoisie / CarteAchetee / CarteGrise : les cartes de vol (512 x 1024)
#   BoutonVert / BoutonCyan / BoutonGris / BoutonChoisi : gros boutons (512 x 256)
#   OngletVert / OngletSombre        : onglets et CLOSE (512 x 128)
#   Bandeau.png                      : le bandeau "prochain vol" (1024 x 128)
#   CarteCarree / CarteCarreeGrise   : cartes du menu du PC et des produits (512 x 512)
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


def icone_argent():
    """Une liasse de billets verts cartoon avec une pièce : l'icône des gains."""
    T = 512 * K
    s = T / 512
    im = Image.new("RGBA", (T, T), (0, 0, 0, 0))

    def poser(dessin, couleur, contour=14):
        m = Image.new("L", (T, T), 0)
        dessin(ImageDraw.Draw(m))
        if contour:
            im.paste(Image.new("RGBA", (T, T), NOIR), (0, 0), m.filter(ImageFilter.MaxFilter(int(contour * 2 * s) | 1)))
        im.paste(Image.new("RGBA", (T, T), hexa(couleur)), (0, 0), m)
        return m

    def billet(dx, dy, angle, c1, c2):
        b = Image.new("RGBA", (T, T), (0, 0, 0, 0))
        d = ImageDraw.Draw(b)
        box = [96 * s + dx, 170 * s + dy, 416 * s + dx, 330 * s + dy]
        d.rounded_rectangle([box[0] - 12 * s, box[1] - 12 * s, box[2] + 12 * s, box[3] + 12 * s], 34 * s, fill=NOIR)
        d.rounded_rectangle(box, 24 * s, fill=hexa(c1))
        d.rounded_rectangle([box[0] + 22 * s, box[1] + 20 * s, box[2] - 22 * s, box[3] - 20 * s], 16 * s, outline=hexa(c2), width=int(8 * s))
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        d.ellipse([cx - 46 * s, cy - 46 * s, cx + 46 * s, cy + 46 * s], fill=hexa(c2))
        d.text((cx, cy + 2 * s), "$", font=ImageFont.truetype(POLICE, int(76 * s)), fill=hexa(c1), anchor="mm")
        return b.rotate(angle, center=(T / 2, T / 2), resample=Image.BICUBIC)

    im.alpha_composite(billet(-10 * s, 40 * s, 14, "16A34A", "BBF7D0"))
    im.alpha_composite(billet(0, 0, -6, "22C55E", "DCFCE7"))
    # la pièce (argent / blanc, pas de jaune)
    poser(lambda d: d.ellipse([300 * s, 280 * s, 450 * s, 430 * s], fill=255), "E2E8F0")
    ImageDraw.Draw(im).ellipse([322 * s, 302 * s, 428 * s, 408 * s], outline=hexa("94A3B8"), width=int(8 * s))
    ImageDraw.Draw(im).text((375 * s, 357 * s), "$", font=ImageFont.truetype(POLICE, int(70 * s)), fill=hexa("475569"), anchor="mm")
    # reflet
    ImageDraw.Draw(im).ellipse([330 * s, 300 * s, 370 * s, 330 * s], fill=(255, 255, 255, 150))
    im.resize((256, 256), Image.LANCZOS).save(os.path.join(SORTIE, "IconeArgent.png"))


def ruban():
    """Ruban cartoon vert avec les bouts repliés (titre du récap)."""
    L, H = 1024 * K, 256 * K
    s = L / 1024
    im = Image.new("RGBA", (L, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    P = lambda pts: [(x * s, y * s) for x, y in pts]
    # bouts repliés (derrière)
    for pts in ([(20, 90), (190, 90), (190, 230), (20, 230), (80, 160)], [(1004, 90), (834, 90), (834, 230), (1004, 230), (944, 160)]):
        d.polygon(P(pts), fill=NOIR)
        inner = [(x + (8 if x < 512 else -8), y + (8 if y < 160 else -8)) for x, y in pts]
        d.polygon(P(inner), fill=hexa("15803D"))
    # bande principale
    d.rounded_rectangle(P([(130, 30), (894, 200)]), 30 * s, fill=NOIR)
    m = masque_arrondi(L, H, [140 * s, 40 * s, 884 * s, 190 * s], 22 * s)
    im.paste(degrade(L, H, "4ADE80", "15803D"), (0, 0), m)
    rf = Image.new("L", (L, H), 0)
    ImageDraw.Draw(rf).rounded_rectangle([170 * s, 52 * s, 854 * s, 82 * s], 15 * s, fill=90)
    im.paste(Image.new("RGBA", (L, H), (255, 255, 255, 255)), (0, 0), ImageChops.multiply(rf, m))
    im.resize((1024, 256), Image.LANCZOS).save(os.path.join(SORTIE, "Ruban.png"))


def fond_recap():
    """Fond du récap : un beau dégradé doux (turquoise -> vert -> bleu ciel), quelques grosses
    bulles de lumière floues et de petites étincelles. Joyeux, propre, presque uni."""
    import numpy as np
    L, H = 2048, 1024
    y, x = np.mgrid[0:H, 0:L].astype(np.float32)
    t = np.clip((x / L) * 0.65 + (y / H) * 0.35, 0, 1)
    pts = [(0.0, "0EA5A4"), (0.45, "22C55E"), (1.0, "38BDF8")]
    c = np.zeros((H, L, 3), np.float32)
    for (t0, c0), (t1, c1) in zip(pts, pts[1:]):
        m = ((t >= t0) & (t <= t1))[..., None]
        k = ((t - t0) / (t1 - t0))[..., None]
        c = np.where(m, np.array(hexa(c0)[:3], np.float32) * (1 - k) + np.array(hexa(c1)[:3], np.float32) * k, c)
    # lumière douce au centre, bords un peu plus profonds
    d = np.sqrt(((x - L / 2) / (L * 0.55)) ** 2 + ((y - H * 0.45) / (H * 0.75)) ** 2)
    c = c * (1 + 0.18 * np.clip(1 - d, 0, 1)[..., None]) * (1 - 0.18 * np.clip(d - 0.7, 0, 1)[..., None])
    im = Image.fromarray(np.clip(c, 0, 255).astype(np.uint8)).convert("RGBA")
    # grosses bulles de lumière très floues
    bulles = Image.new("RGBA", (L, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bulles)
    rnd = random.Random(11)
    for i in range(16):
        px, py, r = rnd.uniform(0, L), rnd.uniform(0, H), rnd.uniform(60, 220)
        bd.ellipse([px - r, py - r, px + r, py + r], fill=(255, 255, 255, rnd.randint(18, 40)))
    im.alpha_composite(bulles.filter(ImageFilter.GaussianBlur(28)))
    # (les étoiles ne sont plus dans le fond : elles scintillent dans le jeu, image Etoile.png)
    im.save(os.path.join(SORTIE, "FondRecap.png"))


def etoile():
    """Une étoile blanche à 4 branches avec un petit halo : elle scintille sur le fond du récap."""
    T = 256
    im = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    halo = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([88, 88, 168, 168], fill=(255, 255, 255, 110))
    im.alpha_composite(halo.filter(ImageFilter.GaussianBlur(14)))
    c, r = T / 2, 110
    pts = [(c, c - r), (c + r * 0.16, c - r * 0.16), (c + r, c), (c + r * 0.16, c + r * 0.16),
           (c, c + r), (c - r * 0.16, c + r * 0.16), (c - r, c), (c - r * 0.16, c - r * 0.16)]
    ImageDraw.Draw(im).polygon(pts, fill=(255, 255, 255, 255))
    im.filter(ImageFilter.GaussianBlur(0.6)).save(os.path.join(SORTIE, "Etoile.png"))


if __name__ == "__main__":
    os.makedirs(SORTIE, exist_ok=True)
    fond()
    # cartes de vol : corps vert, bague de couleur selon l'état
    forme("Carte", 512, 1024, 70, 14, "1B7A43", "0F5132", bague="BBF7D0", bague_ep=8, reflet=0)
    forme("CarteChoisie", 512, 1024, 70, 14, "1B7A43", "0F5132", bague="4ADE80", bague_ep=16, reflet=0)
    forme("CarteAchetee", 512, 1024, 70, 14, "1B7A43", "0F5132", bague="22D3EE", bague_ep=12, reflet=0)
    forme("CarteGrise", 512, 1024, 70, 14, "3F4F5F", "2A3542", bague="64748B", bague_ep=8, reflet=0)
    # boutons
    forme("BoutonVert", 512, 256, 70, 12, "4ADE80", "15803D", reflet=90)
    forme("BoutonCyan", 512, 256, 70, 12, "22D3EE", "0E7490", reflet=90)
    forme("BoutonGris", 512, 256, 70, 12, "94A3B8", "475569", reflet=60)
    forme("BoutonChoisi", 512, 256, 70, 12, "10B981", "065F46", reflet=80)
    # onglets
    forme("OngletVert", 512, 128, 56, 10, "4ADE80", "15803D", reflet=90)
    forme("OngletSombre", 512, 128, 56, 10, "1F6B45", "0B3D24", reflet=50)
    # cartes carrées : menu du PC et produits de la boutique
    forme("CarteCarree", 512, 512, 70, 14, "1B7A43", "0F5132", bague="BBF7D0", bague_ep=8, reflet=0)
    forme("CarteCarreeGrise", 512, 512, 70, 14, "3F4F5F", "2A3542", bague="64748B", bague_ep=8, reflet=0)
    # bandeau du prochain vol
    forme("Bandeau", 1024, 128, 56, 10, "22C55E", "116D35", reflet=70)
    # récap de fin de vol
    forme("PanneauRecap", 1024, 1024, 90, 18, "15803D", "0B3D24", bague="FFFFFF", bague_ep=14, reflet=0)
    fond_recap()
    etoile()
    icone_argent()
    ruban()
    print("ok")
