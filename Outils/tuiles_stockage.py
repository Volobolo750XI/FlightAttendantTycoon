# Tuiles des emplacements de stockage : carre gris arrondi (style de l'image modele) + produit au centre.
import sys, glob, os
from PIL import Image, ImageDraw, ImageFilter
SRC, OUT = sys.argv[1], sys.argv[2]
S = 512; R = 70
def tuile():
    t = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    masque = Image.new("L", (S, S), 0)
    ImageDraw.Draw(masque).rounded_rectangle((4, 4, S - 5, S - 5), R, fill=255)
    grad = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(grad)
    for y in range(S):
        v = int(150 - 20 * y / S)
        d.line((0, y, S, y), fill=(v, v, v, 255))
    t.paste(grad, (0, 0), masque)
    ImageDraw.Draw(t).rounded_rectangle((4, 4, S - 5, S - 5), R, outline=(175, 175, 175, 255), width=8)
    return t
for f in sorted(glob.glob(os.path.join(SRC, "Produit_*.png"))):
    nom = os.path.basename(f).replace("Produit_", "Stockage_")
    if "Champagne" in nom:
        continue
    p = Image.open(f).convert("RGBA").resize((340, 340), Image.LANCZOS)
    t = tuile()
    ombre = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    a = p.split()[3].point(lambda v: int(v * 0.45))
    ombre.paste((0, 0, 0, 255), ((S - 340) // 2 + 6, (S - 340) // 2 + 14), a)
    t.alpha_composite(ombre.filter(ImageFilter.GaussianBlur(10)))
    t.alpha_composite(p, ((S - 340) // 2, (S - 340) // 2))
    t.save(os.path.join(OUT, nom), optimize=True)
