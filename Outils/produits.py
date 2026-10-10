# Genere les icones produits (objet seul, fond transparent, 256x256 PNG)
import sys, math, random
from PIL import Image, ImageDraw, ImageFilter
S = 1024  # dessin en haute resolution puis reduction
OUT = sys.argv[1]

def grad(size, c1, c2, horiz=True):
    w, h = size
    g = Image.new("RGBA", size)
    d = ImageDraw.Draw(g)
    n = w if horiz else h
    for i in range(n):
        t = i / max(1, n - 1)
        # degrade avec reflet : clair au tiers, sombre aux bords
        k = 1 - abs(t - 0.35) * 1.6 if horiz else 1 - t
        k = max(0, min(1, k))
        c = tuple(int(c2[j] + (c1[j] - c2[j]) * k) for j in range(3)) + (255,)
        if horiz: d.line((i, 0, i, h), fill=c)
        else: d.line((0, i, w, i), fill=c)
    return g

def forme(im, dessin, c1, c2, horiz=True, bbox=None):
    m = Image.new("L", im.size, 0); dessin(ImageDraw.Draw(m))
    bb = bbox or m.getbbox()
    if not bb: return
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    g.paste(grad((bb[2]-bb[0], bb[3]-bb[1]), c1, c2, horiz), bb[:2])
    im.paste(g, (0, 0), m)

def ombre(im):
    d = ImageDraw.Draw(im)
    o = Image.new("RGBA", im.size, (0,0,0,0))
    ImageDraw.Draw(o).ellipse((260, 900, 764, 970), fill=(0,0,0,90))
    o = o.filter(ImageFilter.GaussianBlur(25))
    return Image.alpha_composite(o, im)

def finir(im, nom):
    im = ombre(im)
    bb = im.getbbox(); im = im.crop(bb)
    w, h = im.size; k = 900 / max(w, h)
    im = im.resize((int(w*k), int(h*k)), Image.LANCZOS)
    c = Image.new("RGBA", (S, S), (0,0,0,0)); c.paste(im, ((S-im.width)//2, (S-im.height)//2), im)
    c.resize((256, 256), Image.LANCZOS).save(f"{OUT}/Produit_{nom}.png")

def neuf(): return Image.new("RGBA", (S, S), (0,0,0,0))

# 1 Eau
im = neuf()
forme(im, lambda d: d.rounded_rectangle((380, 300, 640, 900), 60, fill=255), (215,240,255), (120,180,225))
forme(im, lambda d: d.polygon([(380,360),(450,220),(570,220),(640,360)], fill=255), (215,240,255), (120,180,225))
forme(im, lambda d: d.rectangle((380, 480, 640, 680), fill=255), (250,250,250), (190,200,210))
forme(im, lambda d: d.rounded_rectangle((440, 140, 580, 230), 15, fill=255), (80,150,255), (20,70,170))
ImageDraw.Draw(im).rectangle((410, 320, 430, 860), fill=(255,255,255,120))
finir(im, "01_Eau")

# 2 Cafe
im = neuf()
forme(im, lambda d: d.polygon([(330,330),(690,330),(640,900),(380,900)], fill=255), (245,240,232), (180,170,160))
forme(im, lambda d: d.polygon([(345,480),(675,480),(660,700),(362,700)], fill=255), (190,135,85), (120,80,45))
forme(im, lambda d: d.rounded_rectangle((300, 260, 720, 350), 30, fill=255), (240,240,240), (150,150,150))
forme(im, lambda d: d.rounded_rectangle((350, 220, 670, 280), 25, fill=255), (240,240,240), (150,150,150))
d = ImageDraw.Draw(im)
for x in (430, 510, 590):
    d.arc((x-40, 60, x+40, 160), 90, 270, fill=(255,255,255,140), width=14)
    d.arc((x-40, 140, x+40, 220), 270, 90, fill=(255,255,255,140), width=14)
finir(im, "02_Cafe")

# 3 Soda
im = neuf()
forme(im, lambda d: d.rounded_rectangle((350, 250, 670, 900), 50, fill=255), (240,70,70), (130,15,20))
forme(im, lambda d: d.ellipse((350, 210, 670, 300), fill=255), (235,235,240), (140,140,150))
forme(im, lambda d: d.rectangle((350, 860, 670, 900), fill=255), (220,220,225), (130,130,140))
d = ImageDraw.Draw(im); d.ellipse((470, 225, 550, 265), fill=(110,110,120,255))
d.rectangle((350, 520, 670, 600), fill=(255,255,255,230))
finir(im, "03_Soda")

# 4 Croissant
im = neuf()
segs = [(-2, 0.55), (-1, 0.8), (0, 1.0), (1, 0.8), (2, 0.55)]
for i, k in segs:
    cx, cy = 512 + i * 130, 560 + abs(i) ** 1.6 * 60
    r = 170 * k
    forme(im, lambda d, cx=cx, cy=cy, r=r: d.ellipse((cx-r, cy-r*0.85, cx+r, cy+r*0.85), fill=255),
          (245,190,100), (170,95,30), horiz=False)
finir(im, "04_Croissant")

# 5 Sandwich
im = neuf()
tri = lambda o: [(200, 820+o), (820, 820+o), (380, 260+o)]
forme(im, lambda d: d.polygon(tri(40), fill=255), (245,225,180), (200,160,110), horiz=False)
d = ImageDraw.Draw(im)
d.polygon([(190,800),(830,800),(820,840),(200,840)], fill=(90,180,60,255))
d.polygon([(200,770),(820,770),(815,800),(205,800)], fill=(220,60,50,255))
d.polygon([(205,745),(815,745),(810,770),(210,770)], fill=(250,200,60,255))
forme(im, lambda d: d.polygon(tri(-80), fill=255), (250,235,195), (205,165,115), horiz=False)
finir(im, "05_Sandwich")

# 6 Repas chaud
im = neuf()
forme(im, lambda d: d.rounded_rectangle((170, 460, 860, 820), 60, fill=255), (235,235,240), (140,140,150), horiz=False)
forme(im, lambda d: d.rounded_rectangle((210, 480, 820, 760), 50, fill=255), (200,200,210), (250,250,250), horiz=False)
forme(im, lambda d: d.ellipse((280, 450, 760, 700), fill=255), (250,200,90), (200,130,40), horiz=False)
d = ImageDraw.Draw(im); random.seed(3)
for _ in range(14):
    x, y = random.randint(340, 690), random.randint(500, 640)
    d.ellipse((x-28, y-22, x+28, y+22), fill=(200,40,30,255))
for x in (420, 512, 600):
    d.arc((x-35, 250, x+35, 340), 90, 270, fill=(255,255,255,130), width=12)
    d.arc((x-35, 330, x+35, 420), 270, 90, fill=(255,255,255,130), width=12)
finir(im, "06_Repas")

# 7 Vin
im = neuf()
forme(im, lambda d: d.chord((330, 120, 690, 560), 0, 180, fill=255), (190,30,60), (90,0,20))
forme(im, lambda d: d.rectangle((330, 120, 690, 340), fill=255), (235,240,250), (170,180,200))
forme(im, lambda d: d.chord((330, 120, 690, 560), 0, 180, fill=255), (190,30,60), (90,0,20))
d = ImageDraw.Draw(im)
d.line((345, 340, 675, 340), fill=(235,240,250,200), width=6)
d.line((330, 120, 330, 340), fill=(235,240,250,200), width=8); d.line((690, 120, 690, 340), fill=(235,240,250,200), width=8)
forme(im, lambda d: d.rectangle((495, 550, 529, 840), fill=255), (240,245,250), (170,180,200))
forme(im, lambda d: d.ellipse((370, 820, 650, 890), fill=255), (240,245,250), (170,180,200))
finir(im, "07_Vin")

# 8 Champagne
im = neuf()
forme(im, lambda d: d.rounded_rectangle((390, 400, 630, 920), 50, fill=255), (60,110,60), (15,40,20))
forme(im, lambda d: d.polygon([(390,430),(470,250),(550,250),(630,430)], fill=255), (60,110,60), (15,40,20))
forme(im, lambda d: d.rectangle((465, 100, 555, 330), fill=255), (250,215,90), (170,120,20))
forme(im, lambda d: d.rectangle((390, 560, 630, 740), fill=255), (250,240,210), (200,180,140))
ImageDraw.Draw(im).rectangle((390, 620, 630, 660), fill=(200,160,40,255))
finir(im, "08_Champagne")

# 9 Homard
im = neuf()
d0 = lambda f: forme(im, f, (240,90,50), (150,30,15), horiz=False)
for i in range(5):
    y = 380 + i * 95; w = 150 - i * 18
    d0(lambda d, y=y, w=w: d.ellipse((512-w, y, 512+w, y+120), fill=255))
d0(lambda d: d.polygon([(512,840),(400,930),(624,930)], fill=255))
for s in (-1, 1):
    d0(lambda d, s=s: d.line((512+s*80, 420, 512+s*230, 260), fill=255, width=50))
    d0(lambda d, s=s: d.ellipse((512+s*230-110, 90, 512+s*230+110, 300), fill=255))
    ImageDraw.Draw(im).polygon([(512+s*230, 120), (512+s*200, 250), (512+s*260, 250)], fill=(0,0,0,0))
    ImageDraw.Draw(im).line((512+s*40, 380, 512+s*150, 120), fill=(200,60,30,255), width=8)
finir(im, "09_Homard")

# 10 Caviar
im = neuf()
forme(im, lambda d: d.rectangle((240, 520, 784, 760), fill=255), (220,220,230), (110,110,125))
forme(im, lambda d: d.ellipse((240, 690, 784, 830), fill=255), (220,220,230), (110,110,125))
forme(im, lambda d: d.ellipse((240, 430, 784, 610), fill=255), (60,60,70), (10,10,15), horiz=False)
d = ImageDraw.Draw(im); random.seed(7)
for _ in range(260):
    a = random.random() * 2 * math.pi; r = math.sqrt(random.random())
    x = 512 + math.cos(a) * r * 245; y = 520 + math.sin(a) * r * 75
    d.ellipse((x-13, y-13, x+13, y+13), fill=(25,25,30,255)); d.ellipse((x-6, y-8, x, y-2), fill=(120,120,130,255))
forme(im, lambda d: d.ellipse((290, 200, 830, 400), fill=255), (250,215,90), (170,120,20), horiz=False)
finir(im, "10_Caviar")

# 11 Sushi or
im = neuf()
for x in (330, 690):
    forme(im, lambda d, x=x: d.rounded_rectangle((x-150, 520, x+150, 800), 70, fill=255), (255,255,255), (200,200,205), horiz=False)
    forme(im, lambda d, x=x: d.rounded_rectangle((x-170, 400, x+170, 560), 60, fill=255), (255,225,110), (190,130,20), horiz=False)
    d = ImageDraw.Draw(im); random.seed(x)
    for _ in range(8):
        px, py = x + random.randint(-140, 140), random.randint(420, 530)
        d.ellipse((px-12, py-12, px+12, py+12), fill=(255,250,210,255))
finir(im, "11_Sushi_Or")

# 12 Gateau diamants
im = neuf()
forme(im, lambda d: d.polygon([(200,500),(820,500),(820,860),(200,860)], fill=255), (110,60,40), (50,25,15))
for y in (590, 700):
    forme(im, lambda d, y=y: d.rectangle((200, y, 820, y+35), fill=255), (255,240,230), (210,190,180))
forme(im, lambda d: d.polygon([(200,500),(820,500),(780,440),(240,440)], fill=255), (255,245,240), (210,190,190))
for x, y, r in ((360, 380, 70), (520, 340, 95), (680, 380, 70)):
    forme(im, lambda d, x=x, y=y, r=r: d.polygon([(x-r, y), (x-r*0.5, y-r*0.6), (x+r*0.5, y-r*0.6), (x+r, y), (x, y+r*1.1)], fill=255),
          (220,250,255), (90,170,230))
    ImageDraw.Draw(im).line((x-r, y, x+r, y), fill=(255,255,255,200), width=6)
finir(im, "12_Gateau_Diamants")
