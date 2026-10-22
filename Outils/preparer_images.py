# Recadre les images des villes (faites avec Gemini) au format du jeu : 1024 x 512 (2:1).
#   python Outils/preparer_images.py DOSSIER_DES_IMAGES
# Les images vont dans Textures/Villes avec le même nom (Paris.png, Tokyo.png, ...).
import os, sys
from PIL import Image

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "..", "Textures", "Villes")
NOMS = ["Paris", "London", "Rome", "Madrid", "Istanbul", "Cairo", "NewYork", "Dubai", "Rio", "MexicoCity",
        "LosAngeles", "Delhi", "Singapore", "Tokyo", "Sydney", "BoraBora", "Bangkok", "HongKong", "Seoul", "Vancouver"]

source = sys.argv[1]
fichiers = {os.path.splitext(f)[0].lower().replace(" ", "").replace("_", ""): f for f in os.listdir(source)}
for nom in NOMS:
    f = fichiers.get(nom.lower())
    if not f:
        print("MANQUE :", nom)
        continue
    im = Image.open(os.path.join(source, f)).convert("RGB")
    L, H = im.size
    if L / H > 2:                       # trop large : on coupe les côtés
        nl = H * 2
        im = im.crop(((L - nl) // 2, 0, (L - nl) // 2 + nl, H))
    else:                               # trop haut : on coupe surtout le ciel en haut
        nh = L // 2
        haut = (H - nh) * 2 // 3
        im = im.crop((0, haut, L, haut + nh))
    im.resize((1024, 512), Image.LANCZOS).save(os.path.join(SORTIE, nom + ".png"))
    print("ok", nom)
