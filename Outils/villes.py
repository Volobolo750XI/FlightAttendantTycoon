"""Illustrations des villes du reseau (style jeu video : formes simples, couleurs franches).

Sortie : Textures/Villes/<Nom>.png en 1024 x 512 (puissance de 2), dessinees en 2048 x 1024 puis
reduites (bords lisses). Un monument par ville + ciel, eau, collines, immeubles, palmiers...
Noms : Paris, London, Rome, Madrid, Istanbul, Cairo, NewYork, Dubai, Rio, MexicoCity, LosAngeles,
Delhi, Singapore, Tokyo, Sydney, BoraBora (les memes que dans pc_destinations.verse).

Usage : python3 villes.py
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SORTIE = os.path.join(RACINE, "Textures", "Villes")
POLICE = os.path.join(RACINE, "Outils", "ArchivoBlack.ttf")
W, H = 2048, 1024


# ---------------------------------------------------------------- outils
def melange(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def degrade(img, haut, bas, y0=0, y1=H, couleurs=None):
    d = ImageDraw.Draw(img)
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0 - 1)
        if couleurs:
            n = len(couleurs) - 1
            k = min(n - 1, int(t * n))
            c = melange(couleurs[k], couleurs[k + 1], t * n - k)
        else:
            c = melange(haut, bas, t)
        d.line((0, y, W, y), fill=c)


def calque():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def coller(img, c, flou=0):
    if flou:
        c = c.filter(ImageFilter.GaussianBlur(flou))
    img.alpha_composite(c)


def soleil(img, x, y, r, coul, halo=(255, 255, 255)):
    c = calque()
    d = ImageDraw.Draw(c)
    for k in range(6, 0, -1):
        rr = r * (1 + k * 0.45)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=halo + (int(18 + 6 * (6 - k)),))
    coller(img, c, 30)
    d = ImageDraw.Draw(img)
    d.ellipse((x - r, y - r, x + r, y + r), fill=coul)


def nuages(img, n, ymin, ymax, coul=(255, 255, 255), alpha=200, graine=1, taille=1.0):
    r = random.Random(graine)
    c = calque()
    d = ImageDraw.Draw(c)
    for _ in range(n):
        x = r.randint(-100, W)
        y = r.randint(ymin, ymax)
        larg = r.randint(180, 380) * taille
        for k in range(5):
            dx = r.uniform(0, larg)
            rr = r.uniform(0.18, 0.32) * larg
            d.ellipse((x + dx - rr, y - rr * 0.8, x + dx + rr, y + rr * 0.6), fill=coul + (alpha,))
        d.rectangle((x + larg * 0.1, y - 4, x + larg * 0.95, y + larg * 0.12), fill=coul + (alpha,))
    coller(img, c, 3)


def etoiles(img, n, ymax, graine=3):
    r = random.Random(graine)
    d = ImageDraw.Draw(img)
    for _ in range(n):
        x, y = r.randint(0, W), r.randint(0, ymax)
        s = r.choice([2, 2, 3, 4])
        d.ellipse((x, y, x + s, y + s), fill=(255, 255, 240))


def collines(img, base, amp, coul, graine=2, rugosite=4, pas=8):
    r = random.Random(graine)
    phases = [r.uniform(0, 6.28) for _ in range(rugosite)]
    pts = [(0, H)]
    for x in range(0, W + pas, pas):
        y = base
        for k in range(rugosite):
            y -= amp / (k + 1) * (0.5 + 0.5 * math.sin(x / W * (k + 1) * 3.0 + phases[k]))
        pts.append((x, y))
    pts.append((W, H))
    ImageDraw.Draw(img).polygon(pts, fill=coul)


def eau(img, y0, haut, bas, reflets=(255, 255, 255), graine=4):
    degrade(img, haut, bas, y0, H)
    r = random.Random(graine)
    c = calque()
    d = ImageDraw.Draw(c)
    for _ in range(70):
        y = r.randint(y0 + 8, H)
        x = r.randint(0, W)
        l = r.randint(30, 140) * (0.5 + (y - y0) / (H - y0))
        d.line((x, y, x + l, y), fill=reflets + (110,), width=3)
    coller(img, c, 1)


def immeubles(img, sol, x0, x1, hmin, hmax, coul, fenetre=None, allume=0.3, graine=5, lmin=60, lmax=140):
    r = random.Random(graine)
    d = ImageDraw.Draw(img)
    x = x0
    while x < x1:
        l = r.randint(lmin, lmax)
        h = r.randint(hmin, hmax)
        d.rectangle((x, sol - h, x + l, sol), fill=coul)
        if r.random() < 0.3:
            d.rectangle((x + l * 0.3, sol - h - 30, x + l * 0.4, sol - h), fill=coul)
        if fenetre:
            for fy in range(int(sol - h + 16), int(sol - 10), 26):
                for fx in range(int(x + 10), int(x + l - 14), 22):
                    if r.random() < allume:
                        d.rectangle((fx, fy, fx + 10, fy + 12), fill=fenetre)
        x += l + r.randint(4, 20)


def palmier(img, x, y, h, tronc=(110, 70, 40), feuille=(40, 150, 70), graine=6):
    d = ImageDraw.Draw(img)
    r = random.Random(graine)
    courbe = r.uniform(-0.25, 0.25)
    pts = []
    for k in range(12):
        t = k / 11
        pts.append((x + courbe * h * t * t, y - h * t))
    for k in range(11):
        (a, b), (c, e) = pts[k], pts[k + 1]
        w = 18 - k
        d.line((a, b, c, e), fill=tronc, width=int(max(6, w)))
    tx, ty = pts[-1]
    for ang in range(0, 360, 45):
        a = math.radians(ang + r.uniform(-12, 12))
        L = h * 0.5
        bout = (tx + math.cos(a) * L, ty + math.sin(a) * L * 0.55 + L * 0.25)
        milieu = (tx + math.cos(a) * L * 0.5, ty + math.sin(a) * L * 0.3 - L * 0.08)
        d.polygon([(tx, ty), milieu, bout, (milieu[0], milieu[1] + 22)], fill=feuille)
    d.ellipse((tx - 12, ty - 8, tx + 12, ty + 12), fill=(90, 60, 30))


def finir(img, nom):
    # leger vignettage + contraste, puis reduction en 1024 x 512
    c = calque()
    d = ImageDraw.Draw(c)
    for k in range(40):
        d.rectangle((k * 6, k * 4, W - k * 6, H - k * 4), outline=(0, 0, 0, max(0, 60 - k * 2)), width=6)
    coller(img, c, 20)
    img.convert("RGB").resize((1024, 512), Image.LANCZOS).save(os.path.join(SORTIE, nom + ".png"))


def nouvelle(couleurs):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    degrade(img, None, None, 0, H, couleurs)
    return img


def ombre_face(d, pts_clair, pts_sombre, clair, sombre):
    d.polygon(pts_clair, fill=clair)
    d.polygon(pts_sombre, fill=sombre)


# ---------------------------------------------------------------- villes
def paris():
    img = nouvelle([(66, 52, 120), (238, 120, 120), (255, 196, 140)])
    soleil(img, 1500, 600, 90, (255, 230, 170), (255, 190, 140))
    nuages(img, 6, 120, 360, (255, 210, 200), 150, 11)
    collines(img, 830, 60, (150, 90, 120), 3)
    immeubles(img, 900, -20, W, 90, 180, (110, 70, 110), (255, 220, 150), 0.35, 7, 90, 170)
    d = ImageDraw.Draw(img)
    # Tour Eiffel
    cx, sol, h = 1000, 900, 760
    fer, fer2 = (70, 50, 70), (95, 70, 95)
    for cote in (-1, 1):
        pts = [(cx + cote * 230, sol), (cx + cote * 140, sol), (cx + cote * 70, sol - 260), (cx + cote * 120, sol - 260)]
        d.polygon(pts, fill=fer)
    d.chord((cx - 150, sol - 140, cx + 150, sol + 120), 180, 360, fill=fer)
    d.chord((cx - 108, sol - 100, cx + 108, sol + 130), 180, 360, fill=(238, 140, 130))
    d.rectangle((cx - 140, sol - 290, cx + 140, sol - 255), fill=fer2)
    d.polygon([(cx - 115, sol - 255), (cx + 115, sol - 255), (cx + 52, sol - 500), (cx - 52, sol - 500)], fill=fer)
    d.polygon([(cx - 60, sol - 380), (cx + 60, sol - 380), (cx + 30, sol - 480), (cx - 30, sol - 480)], fill=(238, 140, 130))
    d.rectangle((cx - 70, sol - 520, cx + 70, sol - 495), fill=fer2)
    d.polygon([(cx - 40, sol - 495), (cx + 40, sol - 495), (cx + 8, sol - h), (cx - 8, sol - h)], fill=fer)
    d.rectangle((cx - 4, sol - h - 40, cx + 4, sol - h), fill=fer)
    for k in range(10):
        y = sol - 265 - k * 22
        d.line((cx - 100 + k * 5, y, cx + 100 - k * 5, y), fill=fer2, width=3)
    d.rectangle((0, sol, W, H), fill=(80, 60, 90))
    eau(img, 940, (120, 90, 140), (60, 40, 80), (255, 200, 170))
    finir(img, "Paris")


def london():
    img = nouvelle([(110, 140, 175), (175, 200, 220), (215, 225, 230)])
    nuages(img, 10, 60, 420, (240, 244, 248), 220, 21, 1.4)
    immeubles(img, 880, -20, W, 100, 260, (90, 100, 120), (255, 230, 160), 0.15, 22)
    d = ImageDraw.Draw(img)
    # London Eye
    ox, oy, R = 1450, 520, 300
    for a in range(0, 360, 15):
        r_ = math.radians(a)
        d.line((ox, oy, ox + R * math.cos(r_), oy + R * math.sin(r_)), fill=(200, 210, 225), width=4)
    d.ellipse((ox - R, oy - R, ox + R, oy + R), outline=(235, 240, 250), width=16)
    for a in range(0, 360, 20):
        r_ = math.radians(a)
        x, y = ox + R * math.cos(r_), oy + R * math.sin(r_)
        d.ellipse((x - 16, y - 12, x + 16, y + 12), fill=(150, 200, 235))
    d.line((ox, oy, ox - 160, 900), fill=(220, 225, 235), width=16)
    d.line((ox, oy, ox + 160, 900), fill=(220, 225, 235), width=16)
    # Big Ben
    cx, sol = 700, 900
    pierre, ombre = (205, 170, 110), (165, 130, 80)
    d.rectangle((cx - 80, sol - 560, cx + 80, sol), fill=pierre)
    d.rectangle((cx + 30, sol - 560, cx + 80, sol), fill=ombre)
    d.rectangle((cx - 95, sol - 700, cx + 95, sol - 560), fill=pierre)
    d.ellipse((cx - 72, sol - 690, cx + 72, sol - 546), fill=(245, 240, 220), outline=(90, 70, 40), width=6)
    d.line((cx, sol - 618, cx, sol - 670), fill=(40, 30, 20), width=7)
    d.line((cx, sol - 618, cx + 38, sol - 618), fill=(40, 30, 20), width=7)
    d.rectangle((cx - 70, sol - 760, cx + 70, sol - 700), fill=ombre)
    d.polygon([(cx - 80, sol - 760), (cx + 80, sol - 760), (cx, sol - 930)], fill=(60, 70, 80))
    d.rectangle((cx - 4, sol - 980, cx + 4, sol - 930), fill=(60, 70, 80))
    for y in range(sol - 540, sol - 20, 60):
        d.rectangle((cx - 50, y, cx - 30, y + 36), fill=ombre)
        d.rectangle((cx - 10, y, cx + 10, y + 36), fill=ombre)
    d.rectangle((0, sol, W, H), fill=(70, 80, 95))
    eau(img, 930, (110, 130, 150), (60, 75, 95))
    finir(img, "London")


def rome():
    img = nouvelle([(110, 170, 230), (250, 210, 150), (255, 230, 180)])
    soleil(img, 300, 260, 80, (255, 245, 210), (255, 220, 150))
    nuages(img, 5, 80, 300, (255, 245, 230), 190, 31)
    collines(img, 760, 80, (150, 170, 110), 32)
    d = ImageDraw.Draw(img)
    # cypres
    for x in (180, 280, 1780, 1880, 1700):
        d.ellipse((x - 26, 520, x + 26, 860), fill=(50, 90, 50))
    # Colisee
    x0, x1, sol = 420, 1640, 900
    clair, sombre, arche = (225, 180, 120), (190, 140, 90), (120, 80, 50)
    d.rectangle((x0, sol - 520, x1, sol), fill=clair)
    d.polygon([(x1 - 260, sol - 520), (x1, sol - 400), (x1, sol - 520)], fill=(255, 230, 180))
    for k, (y, hh) in enumerate([(sol - 150, 120), (sol - 290, 110), (sol - 420, 100)]):
        d.rectangle((x0, y - 10, x1, y), fill=sombre)
        n = 14
        for i in range(n):
            ax = x0 + 30 + i * (x1 - x0 - 60) / n
            if k == 2 and ax > x1 - 260:
                continue
            d.rounded_rectangle((ax + 8, y + 18, ax + 58, y + hh - 6), 24, fill=arche)
    d.rectangle((x0, sol - 520, x1 - 260, sol - 500), fill=sombre)
    d.rectangle((0, sol, W, H), fill=(200, 170, 120))
    d.rectangle((0, sol + 40, W, H), fill=(180, 150, 100))
    finir(img, "Rome")


def madrid():
    img = nouvelle([(60, 130, 220), (130, 190, 245), (220, 235, 250)])
    soleil(img, 1700, 220, 90, (255, 240, 170), (255, 230, 150))
    nuages(img, 4, 100, 300, (255, 255, 255), 210, 41)
    immeubles(img, 900, -20, W, 120, 230, (230, 200, 160), (255, 250, 220), 0.0, 42, 100, 180)
    d = ImageDraw.Draw(img)
    for x in range(0, W, 140):
        for y in range(700, 880, 50):
            d.rectangle((x + 20, y, x + 40, y + 26), fill=(150, 110, 80))
    # Edificio Metropolis
    cx, sol = 1000, 900
    blanc, ombre = (245, 235, 215), (205, 190, 165)
    d.rectangle((cx - 260, sol - 420, cx + 260, sol), fill=blanc)
    d.rectangle((cx + 120, sol - 420, cx + 260, sol), fill=ombre)
    d.ellipse((cx - 170, sol - 600, cx + 170, sol - 340), fill=blanc)
    d.rectangle((cx - 170, sol - 470, cx + 170, sol - 420), fill=blanc)
    for k in range(6):
        x = cx - 140 + k * 56
        d.rectangle((x, sol - 400, x + 20, sol - 40), fill=(180, 160, 130))
    d.pieslice((cx - 150, sol - 760, cx + 150, sol - 460), 180, 360, fill=(40, 50, 70))
    d.rectangle((cx - 150, sol - 615, cx + 150, sol - 600), fill=(200, 160, 60))
    d.rectangle((cx - 12, sol - 860, cx + 12, sol - 760), fill=(220, 180, 60))
    d.polygon([(cx - 60, sol - 860), (cx + 60, sol - 860), (cx, sol - 930)], fill=(240, 200, 70))
    d.rectangle((0, sol, W, H), fill=(210, 180, 140))
    d.rectangle((0, sol + 30, W, sol + 50), fill=(200, 60, 50))
    d.rectangle((0, sol + 50, W, sol + 80), fill=(250, 200, 50))
    d.rectangle((0, sol + 80, W, sol + 100), fill=(200, 60, 50))
    finir(img, "Madrid")


def istanbul():
    img = nouvelle([(60, 40, 110), (200, 90, 110), (255, 170, 100)])
    soleil(img, 1600, 640, 110, (255, 200, 120), (255, 150, 90))
    nuages(img, 5, 100, 380, (255, 170, 160), 120, 51)
    collines(img, 820, 60, (100, 60, 100), 52)
    d = ImageDraw.Draw(img)
    cx, sol = 950, 880
    mur, ombre = (90, 60, 100), (70, 45, 80)
    # minarets
    for x in (cx - 470, cx - 330, cx + 330, cx + 470):
        d.rectangle((x - 16, sol - 640, x + 16, sol), fill=mur)
        d.rectangle((x - 24, sol - 480, x + 24, sol - 468), fill=ombre)
        d.polygon([(x - 18, sol - 640), (x + 18, sol - 640), (x, sol - 760)], fill=ombre)
    d.rectangle((cx - 330, sol - 220, cx + 330, sol), fill=mur)
    for x in (cx - 230, cx + 230):
        d.pieslice((x - 110, sol - 330, x + 110, sol - 110), 180, 360, fill=mur)
    d.pieslice((cx - 230, sol - 520, cx + 230, sol - 60), 180, 360, fill=mur)
    d.rectangle((cx - 6, sol - 560, cx + 6, sol - 290), fill=ombre)
    d.ellipse((cx - 16, sol - 580, cx + 16, sol - 548), fill=(255, 200, 120))
    for k in range(9):
        x = cx - 300 + k * 72
        d.rounded_rectangle((x, sol - 180, x + 30, sol - 90), 15, fill=(255, 190, 120))
    eau(img, sol, (190, 100, 120), (60, 40, 90), (255, 180, 130))
    finir(img, "Istanbul")


def cairo():
    img = nouvelle([(80, 150, 230), (180, 210, 240), (255, 230, 190)])
    soleil(img, 1700, 230, 100, (255, 250, 220), (255, 240, 190))
    d = ImageDraw.Draw(img)
    collines(img, 820, 50, (235, 195, 130), 61, 3, 12)
    # pyramides
    for cx, b, h in ((520, 360, 470), (1000, 440, 600), (1460, 300, 380)):
        sol = 860
        d.polygon([(cx - b, sol), (cx, sol - h), (cx, sol)], fill=(240, 200, 130))
        d.polygon([(cx, sol), (cx, sol - h), (cx + b, sol)], fill=(200, 155, 90))
        for k in range(1, 10):
            y = sol - h * k / 10
            w_ = b * (1 - k / 10)
            d.line((cx - w_, y, cx + w_, y), fill=(190, 150, 90), width=3)
    # sphinx
    sx, sy = 1700, 860
    d.rectangle((sx - 160, sy - 60, sx + 120, sy), fill=(215, 175, 110))
    d.rectangle((sx + 60, sy - 140, sx + 140, sy - 40), fill=(215, 175, 110))
    d.polygon([(sx + 50, sy - 140), (sx + 150, sy - 140), (sx + 160, sy - 60), (sx + 40, sy - 60)], fill=(190, 150, 90))
    d.rectangle((0, 860, W, H), fill=(230, 190, 120))
    collines(img, 990, 40, (215, 170, 100), 62, 3, 12)
    finir(img, "Cairo")


def newyork():
    img = nouvelle([(10, 15, 50), (30, 40, 100), (90, 70, 140)])
    etoiles(img, 160, 500)
    d = ImageDraw.Draw(img)
    d.ellipse((260, 140, 360, 240), fill=(250, 245, 220))
    immeubles(img, 860, -20, W, 220, 520, (25, 30, 60), (255, 220, 120), 0.45, 71, 70, 150)
    # Empire State
    cx, sol = 1100, 860
    c1 = (40, 45, 85)
    d.rectangle((cx - 120, sol - 480, cx + 120, sol), fill=c1)
    d.rectangle((cx - 80, sol - 620, cx + 80, sol - 480), fill=c1)
    d.rectangle((cx - 50, sol - 720, cx + 50, sol - 620), fill=c1)
    d.rectangle((cx - 24, sol - 800, cx + 24, sol - 720), fill=c1)
    d.rectangle((cx - 6, sol - 900, cx + 6, sol - 800), fill=c1)
    for y in range(sol - 700, sol - 20, 28):
        for x in range(cx - 100, cx + 100, 24):
            if (x + y) % 3:
                d.rectangle((x, y, x + 10, y + 12), fill=(255, 225, 130))
    eau(img, sol, (40, 50, 110), (10, 15, 50), (255, 220, 140))
    # Statue de la Liberte
    lx, ly = 420, 980
    vert, vert2 = (110, 190, 160), (80, 150, 125)
    d.polygon([(lx - 90, ly), (lx + 90, ly), (lx + 70, ly - 160), (lx - 70, ly - 160)], fill=(120, 110, 100))
    d.polygon([(lx - 45, ly - 160), (lx + 45, ly - 160), (lx + 28, ly - 420), (lx - 28, ly - 420)], fill=vert)
    d.polygon([(lx + 5, ly - 160), (lx + 45, ly - 160), (lx + 28, ly - 420), (lx + 5, ly - 420)], fill=vert2)
    d.ellipse((lx - 26, ly - 480, lx + 26, ly - 420), fill=vert)
    for a in range(-60, 61, 30):
        r_ = math.radians(a - 90)
        d.line((lx, ly - 460, lx + 50 * math.cos(r_), ly - 460 + 50 * math.sin(r_)), fill=vert, width=8)
    d.line((lx + 20, ly - 400, lx + 70, ly - 560), fill=vert, width=22)
    d.polygon([(lx + 56, ly - 560), (lx + 84, ly - 560), (lx + 76, ly - 590), (lx + 64, ly - 590)], fill=vert2)
    soleil(img, lx + 70, ly - 610, 16, (255, 220, 120), (255, 200, 100))
    finir(img, "NewYork")


def dubai():
    img = nouvelle([(250, 180, 90), (255, 140, 80), (250, 210, 150)])
    soleil(img, 500, 520, 120, (255, 230, 150), (255, 190, 110))
    d = ImageDraw.Draw(img)
    immeubles(img, 860, 1150, W, 200, 420, (150, 90, 70), (255, 230, 170), 0.2, 81, 70, 120)
    immeubles(img, 860, -20, 800, 150, 300, (150, 90, 70), (255, 230, 170), 0.2, 82, 70, 120)
    # Burj Khalifa
    cx, sol = 1000, 860
    c1, c2 = (200, 200, 215), (150, 150, 170)
    etages = [(110, 0, 200), (90, 200, 380), (70, 380, 530), (50, 530, 650), (34, 650, 740), (20, 740, 810)]
    for w_, a, b in etages:
        d.rectangle((cx - w_, sol - b, cx + w_, sol - a), fill=c1)
        d.rectangle((cx + w_ * 0.3, sol - b, cx + w_, sol - a), fill=c2)
    d.polygon([(cx - 12, sol - 810), (cx + 12, sol - 810), (cx, sol - 960)], fill=c1)
    # Burj Al Arab (voile)
    bx, by = 1550, 870
    d.polygon([(bx - 120, by), (bx - 100, by - 480), (bx + 150, by - 120), (bx + 60, by)], fill=(245, 245, 250))
    d.line((bx - 100, by - 480, bx - 140, by - 520), fill=(200, 200, 210), width=10)
    eau(img, sol + 10, (240, 160, 100), (60, 110, 160), (255, 230, 160))
    finir(img, "Dubai")


def rio():
    img = nouvelle([(70, 170, 240), (150, 215, 250), (230, 245, 250)])
    soleil(img, 1750, 200, 80, (255, 250, 210), (255, 240, 180))
    nuages(img, 5, 80, 300, (255, 255, 255), 220, 91)
    d = ImageDraw.Draw(img)
    # Corcovado + Christ
    d.polygon([(100, 860), (420, 330), (520, 300), (700, 520), (900, 860)], fill=(60, 130, 80))
    d.polygon([(470, 310), (520, 300), (700, 520), (600, 560)], fill=(45, 105, 65))
    cx, cy = 490, 300
    d.rectangle((cx - 14, cy - 150, cx + 14, cy), fill=(245, 245, 240))
    d.rectangle((cx - 80, cy - 135, cx + 80, cy - 115), fill=(245, 245, 240))
    d.ellipse((cx - 14, cy - 178, cx + 14, cy - 150), fill=(245, 245, 240))
    # Pain de sucre
    for x, h, w_ in ((1250, 520, 210), (1520, 380, 160)):
        d.ellipse((x - w_, 860 - h, x + w_, 860 + h * 0.6), fill=(70, 120, 90))
        d.ellipse((x - w_ * 0.6, 860 - h, x + w_ * 0.2, 860 - h * 0.4), fill=(90, 145, 110))
    eau(img, 860, (60, 160, 200), (30, 90, 150))
    d = ImageDraw.Draw(img)
    d.polygon([(0, 960), (W, 900), (W, H), (0, H)], fill=(245, 220, 160))
    for x in (120, 1900):
        palmier(img, x, 990, 380, graine=x)
    finir(img, "Rio")


def mexico():
    img = nouvelle([(60, 140, 230), (255, 190, 120), (255, 220, 160)])
    soleil(img, 1600, 300, 100, (255, 230, 150), (255, 200, 120))
    collines(img, 780, 90, (120, 140, 120), 101)
    d = ImageDraw.Draw(img)
    # pyramide a degres
    cx, sol = 1000, 880
    for k in range(6):
        w_ = 520 - k * 80
        y = sol - k * 90
        d.rectangle((cx - w_, y - 90, cx + w_, y), fill=(200, 140, 90) if k % 2 == 0 else (185, 125, 80))
        d.rectangle((cx + w_ * 0.4, y - 90, cx + w_, y), fill=(160, 100, 60))
    d.rectangle((cx - 60, sol - 540, cx + 60, sol), fill=(150, 90, 55))
    for y in range(sol - 540, sol, 18):
        d.line((cx - 60, y, cx + 60, y), fill=(120, 70, 40), width=3)
    d.rectangle((cx - 90, sol - 640, cx + 90, sol - 540), fill=(185, 125, 80))
    # cactus
    for x, h in ((300, 360), (1700, 300), (1850, 220)):
        vert = (60, 140, 80)
        d.rounded_rectangle((x - 30, 900 - h, x + 30, 900), 30, fill=vert)
        d.rounded_rectangle((x - 100, 900 - h * 0.7, x - 60, 900 - h * 0.35), 20, fill=vert)
        d.rectangle((x - 100, 900 - h * 0.45, x - 20, 900 - h * 0.35), fill=vert)
        d.rounded_rectangle((x + 60, 900 - h * 0.8, x + 100, 900 - h * 0.45), 20, fill=vert)
        d.rectangle((x + 20, 900 - h * 0.55, x + 100, 900 - h * 0.45), fill=vert)
    d.rectangle((0, 880, W, H), fill=(220, 170, 110))
    for k, c in enumerate([(230, 70, 90), (250, 190, 60), (60, 170, 160), (150, 80, 180)]):
        d.rectangle((0, 940 + k * 20, W, 960 + k * 20), fill=c)
    finir(img, "MexicoCity")


def losangeles():
    img = nouvelle([(80, 40, 120), (230, 90, 120), (255, 170, 110)])
    soleil(img, 1000, 700, 160, (255, 220, 140), (255, 160, 100))
    collines(img, 560, 120, (140, 80, 100), 111)
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(POLICE, 96)
    texte = "HOLLYWOOD"
    x = 560
    for i, ch in enumerate(texte):
        y = 380 + int(10 * math.sin(i))
        d.text((x, y), ch, font=f, fill=(250, 245, 240))
        x += f.getlength(ch) + 12
    collines(img, 780, 80, (100, 60, 90), 112)
    immeubles(img, 900, 400, 1700, 120, 330, (70, 40, 80), (255, 210, 140), 0.3, 113, 60, 120)
    d.rectangle((0, 900, W, H), fill=(60, 40, 70))
    for x, h in ((120, 600), (300, 520), (1720, 560), (1900, 640)):
        palmier(img, x, 1000, h, tronc=(50, 30, 50), feuille=(40, 25, 55), graine=x)
    finir(img, "LosAngeles")


def delhi():
    img = nouvelle([(130, 170, 220), (255, 200, 160), (255, 225, 190)])
    soleil(img, 350, 330, 90, (255, 235, 190), (255, 210, 160))
    nuages(img, 4, 100, 300, (255, 240, 230), 150, 121)
    d = ImageDraw.Draw(img)
    # dome blanc (au fond)
    tx, ty = 1500, 760
    blanc = (250, 245, 240)
    d.rectangle((tx - 220, ty - 160, tx + 220, ty), fill=blanc)
    d.ellipse((tx - 150, ty - 420, tx + 150, ty - 120), fill=blanc)
    d.polygon([(tx - 10, ty - 420), (tx + 10, ty - 420), (tx, ty - 480)], fill=(220, 190, 120))
    for x in (tx - 300, tx + 300):
        d.rectangle((x - 16, ty - 400, x + 16, ty), fill=blanc)
        d.ellipse((x - 26, ty - 440, x + 26, ty - 390), fill=blanc)
    d.rounded_rectangle((tx - 60, ty - 140, tx + 60, ty), 50, fill=(200, 190, 185))
    # Porte de l'Inde
    gx, sol = 750, 900
    grès, ombre = (220, 140, 100), (180, 105, 75)
    d.rectangle((gx - 260, sol - 560, gx + 260, sol), fill=grès)
    d.rectangle((gx + 150, sol - 560, gx + 260, sol), fill=ombre)
    d.rounded_rectangle((gx - 110, sol - 400, gx + 110, sol + 60), 110, fill=(150, 90, 70))
    d.rectangle((gx - 290, sol - 620, gx + 290, sol - 560), fill=ombre)
    d.rectangle((gx - 220, sol - 680, gx + 220, sol - 620), fill=grès)
    d.pieslice((gx - 60, sol - 740, gx + 60, sol - 620), 180, 360, fill=ombre)
    d.rectangle((0, sol, W, H), fill=(200, 170, 130))
    d.rectangle((0, sol + 40, W, sol + 60), fill=(90, 150, 80))
    finir(img, "Delhi")


def singapore():
    img = nouvelle([(10, 20, 60), (20, 60, 110), (60, 110, 150)])
    etoiles(img, 120, 400, 131)
    d = ImageDraw.Draw(img)
    immeubles(img, 820, -20, W, 200, 420, (20, 35, 70), (120, 220, 255), 0.4, 132, 60, 120)
    # Marina Bay Sands
    cx, sol = 1150, 820
    tour = (210, 220, 235)
    for k in range(3):
        x = cx - 300 + k * 260
        d.polygon([(x - 50, sol), (x + 50, sol), (x + 40, sol - 560), (x - 40, sol - 560)], fill=tour)
        for y in range(sol - 540, sol - 20, 30):
            d.line((x - 36, y, x + 36, y), fill=(150, 200, 240), width=3)
    d.polygon([(cx - 420, sol - 600), (cx + 300, sol - 600), (cx + 380, sol - 640), (cx - 400, sol - 630)], fill=(230, 235, 245))
    # supertrees
    for x, h in ((300, 420), (480, 340), (620, 380)):
        d.polygon([(x - 14, 840), (x + 14, 840), (x + 6, 840 - h), (x - 6, 840 - h)], fill=(80, 40, 110))
        d.polygon([(x - 6, 840 - h), (x + 6, 840 - h), (x + 100, 840 - h - 60), (x - 100, 840 - h - 60)], fill=(160, 60, 180))
        for k in range(8):
            px = x - 90 + k * 26
            d.ellipse((px - 6, 840 - h - 70, px + 6, 840 - h - 58), fill=(255, 120, 220))
    eau(img, 840, (30, 70, 120), (5, 15, 45), (120, 220, 255))
    finir(img, "Singapore")


def tokyo():
    img = nouvelle([(20, 20, 70), (120, 60, 140), (255, 140, 150)])
    etoiles(img, 80, 300, 141)
    d = ImageDraw.Draw(img)
    # Fuji
    d.polygon([(500, 760), (1050, 260), (1600, 760)], fill=(90, 90, 150))
    d.polygon([(900, 400), (1050, 260), (1200, 400), (1150, 430), (1100, 400), (1050, 440), (1000, 400), (950, 430)], fill=(250, 250, 255))
    immeubles(img, 860, -20, W, 160, 380, (40, 30, 70), (255, 120, 200), 0.35, 142, 60, 120)
    immeubles(img, 860, -20, W, 100, 200, (30, 20, 55), (120, 230, 255), 0.3, 143, 50, 100)
    # Tokyo Tower
    cx, sol = 1450, 860
    rouge, blanc = (230, 70, 50), (250, 245, 240)
    for cote in (-1, 1):
        d.polygon([(cx + cote * 150, sol), (cx + cote * 100, sol), (cx + cote * 40, sol - 420), (cx + cote * 70, sol - 420)], fill=rouge)
    d.rectangle((cx - 100, sol - 300, cx + 100, sol - 270), fill=blanc)
    d.rectangle((cx - 80, sol - 440, cx + 80, sol - 410), fill=blanc)
    d.polygon([(cx - 45, sol - 410), (cx + 45, sol - 410), (cx + 10, sol - 680), (cx - 10, sol - 680)], fill=rouge)
    for k, y in enumerate(range(sol - 680, sol - 410, 45)):
        d.rectangle((cx - 40, y, cx + 40, y + 16), fill=blanc if k % 2 else rouge)
    d.rectangle((cx - 4, sol - 780, cx + 4, sol - 680), fill=blanc)
    # cerisier
    tx, ty = 300, 900
    d.line((tx, ty, tx + 40, ty - 260), fill=(70, 40, 40), width=26)
    r = random.Random(144)
    for _ in range(40):
        x = tx + 40 + r.randint(-200, 200)
        y = ty - 300 + r.randint(-120, 80)
        s = r.randint(40, 80)
        d.ellipse((x - s, y - s, x + s, y + s), fill=r.choice([(255, 170, 200), (255, 190, 215), (240, 140, 180)]))
    d.rectangle((0, 900, W, H), fill=(30, 20, 50))
    finir(img, "Tokyo")


def sydney():
    img = nouvelle([(40, 140, 230), (120, 200, 245), (220, 240, 250)])
    soleil(img, 300, 200, 80, (255, 250, 220), (255, 240, 190))
    nuages(img, 5, 80, 280, (255, 255, 255), 220, 151)
    d = ImageDraw.Draw(img)
    # Harbour Bridge
    bx0, bx1, by = 1150, 2000, 640
    d.arc((bx0, by - 260, bx1, by + 260), 180, 360, fill=(90, 100, 115), width=34)
    d.rectangle((bx0 - 40, by - 20, bx1 + 40, by + 16), fill=(80, 90, 105))
    for x in range(bx0 + 40, bx1, 50):
        t = (x - bx0) / (bx1 - bx0)
        top = by - 260 * math.sin(math.pi * t)
        d.line((x, top, x, by), fill=(110, 120, 135), width=5)
    for x in (bx0, bx1 - 40):
        d.rectangle((x - 40, by - 140, x + 40, by + 200), fill=(200, 180, 150))
    eau(img, 800, (40, 140, 200), (20, 70, 140))
    d = ImageDraw.Draw(img)
    # Opera
    ox, sol = 650, 820
    d.rectangle((ox - 360, sol - 50, ox + 420, sol + 20), fill=(220, 180, 140))
    voiles = [(-300, 250, 0.0), (-120, 340, 0.1), (60, 300, 0.2), (220, 220, 0.3)]
    for dx, h, _ in voiles:
        x = ox + dx
        d.polygon([(x - 120, sol - 50), (x + 30, sol - 50 - h), (x + 120, sol - 50)], fill=(250, 250, 250))
        d.polygon([(x + 30, sol - 50 - h), (x + 120, sol - 50), (x + 30, sol - 50)], fill=(215, 220, 230))
        d.line((x - 120, sol - 50, x + 30, sol - 50 - h), fill=(200, 205, 215), width=4)
    finir(img, "Sydney")


def borabora():
    img = nouvelle([(40, 160, 240), (130, 210, 250), (230, 248, 255)])
    soleil(img, 1700, 180, 80, (255, 250, 220), (255, 240, 190))
    nuages(img, 5, 80, 300, (255, 255, 255), 220, 161)
    d = ImageDraw.Draw(img)
    # Mont Otemanu
    d.polygon([(500, 720), (760, 380), (860, 230), (960, 300), (1060, 260), (1180, 420), (1500, 720)], fill=(40, 120, 70))
    d.polygon([(860, 230), (960, 300), (1060, 260), (1000, 420), (900, 380)], fill=(30, 95, 55))
    eau(img, 700, (40, 210, 220), (20, 140, 190), (220, 255, 255))
    d = ImageDraw.Draw(img)
    d.ellipse((380, 680, 1620, 760), fill=(245, 225, 170))
    # bungalows sur pilotis
    d.rectangle((300, 860, 1800, 875), fill=(140, 100, 60))
    for k in range(6):
        x = 400 + k * 240
        for px in (x - 60, x + 60):
            d.rectangle((px - 6, 860, px + 6, 960), fill=(110, 80, 50))
        d.rectangle((x - 80, 780, x + 80, 860), fill=(200, 150, 90))
        d.polygon([(x - 110, 790), (x, 700), (x + 110, 790)], fill=(170, 120, 60))
        d.rectangle((x - 20, 810, x + 20, 860), fill=(120, 80, 40))
    for x in (150, 1880):
        palmier(img, x, 1000, 420, graine=x + 7)
    finir(img, "BoraBora")


if __name__ == "__main__":
    os.makedirs(SORTIE, exist_ok=True)
    for f in (paris, london, rome, madrid, istanbul, cairo, newyork, dubai, rio, mexico, losangeles,
              delhi, singapore, tokyo, sydney, borabora):
        f()
    print("ok :", SORTIE)
