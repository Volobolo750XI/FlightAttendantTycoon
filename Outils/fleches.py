# Génère les 2 flèches discrètes (chevrons) de la liste des destinations.
from PIL import Image, ImageDraw, ImageFilter

S = 1024           # dessin en grand puis réduit (bords lisses)
TAILLE = 256
BLEU = (90, 220, 255)

def chevron(vers_le_haut):
    trait = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(trait)
    l, h, e = 0.30 * S, 0.15 * S, int(0.075 * S)
    cx, cy = S / 2, S / 2
    if vers_le_haut:
        pts = [(cx - l, cy + h), (cx, cy - h), (cx + l, cy + h)]
    else:
        pts = [(cx - l, cy - h), (cx, cy + h), (cx + l, cy - h)]
    d.line(pts, fill=255, width=e, joint="curve")
    for x, y in (pts[0], pts[2]):
        d.ellipse([x - e / 2, y - e / 2, x + e / 2, y + e / 2], fill=255)
    halo = trait.filter(ImageFilter.GaussianBlur(S * 0.03)).point(lambda v: int(v * 0.55))
    alpha = Image.composite(trait, halo, trait)
    img = Image.new("RGBA", (S, S), BLEU + (0,))
    img.putalpha(alpha)
    return img.resize((TAILLE, TAILLE), Image.LANCZOS)

chevron(True).save("Textures/Destinations/FlecheHaut.png")
chevron(False).save("Textures/Destinations/FlecheBas.png")
