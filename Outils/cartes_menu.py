# Genere les 3 cartes du menu PC (512x512, style GTA)
import sys
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
SRC, OUT = sys.argv[1], sys.argv[2]
F = ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf", 40)
CARTES = [("65.jpg","Carte_Destinations","DESTINATIONS"),
          ("66.jpg","Carte_Marchandises","SUPPLIES"),
          ("67.jpg","Carte_Ameliorations","UPGRADES")]
W, BARRE, BANDE = 512, 10, 120
H_IMG = W - BARRE - BANDE
for src, nom, titre in CARTES:
    im = Image.open(f"{SRC}/{src}").convert("RGB")
    r = W / im.width; im = im.resize((W, round(im.height*r)), Image.LANCZOS)
    y = (im.height - H_IMG)//2; im = im.crop((0, y, W, y+H_IMG))
    for verrou in ((False, True) if nom == "Carte_Ameliorations" else (False,)):
        c = Image.new("RGB", (W, W), (12,12,14)); d = ImageDraw.Draw(c)
        p = im
        if verrou: p = ImageEnhance.Brightness(ImageEnhance.Color(im).enhance(0.1)).enhance(0.45)
        c.paste(p, (0, BARRE))
        d.rectangle((0,0,W,BARRE-1), fill=(90,90,90) if verrou else (215,35,35))
        col = (110,110,110) if verrou else (240,240,240)
        bb = d.textbbox((0,0), titre, font=F)
        d.text(((W-bb[2])//2, W-BANDE//2-(bb[3]+bb[1])//2), titre, font=F, fill=col)
        c.save(f"{OUT}/{nom}{'_Verrou' if verrou else ''}.jpg", quality=90)
