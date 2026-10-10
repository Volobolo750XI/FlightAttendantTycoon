# Fonds de boutons arrondis (une seule forme, pas de bouton dans le bouton)
from PIL import Image, ImageDraw
S = 4
def bouton(nom, l, h, couleur):
    im = Image.new("RGBA", (l * S, h * S), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, l * S - 1, h * S - 1), radius=h * S * 0.22, fill=couleur)
    im.resize((l, h), Image.LANCZOS).save(f"Textures/MenuPC/{nom}.png")
for c, rgb in (("Bleu", (37, 99, 235)), ("Violet", (124, 58, 237)), ("Vert", (22, 163, 74)), ("Gris", (55, 65, 81))):
    bouton(f"Bouton_{c}", 512, 64, rgb + (255,))
bouton("Bouton_Gris_Court", 256, 64, (55, 65, 81, 255))
bouton("Bouton_Gris_Carre", 64, 64, (55, 65, 81, 255))
