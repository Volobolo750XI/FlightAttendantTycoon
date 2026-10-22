# Carte du monde des vols (Textures/Destinations/CarteVols.png, 2048 x 1024).
#   python Outils/carte_monde.py
# Projection Mercator : longitude -180..180, latitude LAT_HAUT..LAT_BAS.
# Une ville (lon, lat) est au point U = (lon + 180) / 360, V = (Y(LAT_HAUT) - Y(lat)) / (Y(LAT_HAUT) - Y(LAT_BAS))
# avec Y(lat) = ln(tan(pi/4 + lat/2)) : c'est ce que fait villes_uv() plus bas pour le Verse.
# Les formes des pays viennent de Natural Earth (domaine public), téléchargées au besoin.
import json, math, os, sys, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

ICI = os.path.dirname(os.path.abspath(__file__))
DONNEES = os.path.join(ICI, "donnees")
SORTIE = os.path.join(ICI, "..", "Textures", "Destinations", "CarteVols.png")
LAT_HAUT, LAT_BAS = 72.0, -58.0
L, H = 4096, 2048           # dessin en grand, réduit à 2048 x 1024 à la fin
NE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"


def merc(lat):
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


YH, YB = merc(LAT_HAUT), merc(LAT_BAS)


def uv(lon, lat):
    lat = max(min(lat, 85.0), -85.0)
    return (lon + 180.0) / 360.0, (YH - merc(lat)) / (YH - YB)


def xy(lon, lat):
    u, v = uv(lon, lat)
    return u * L, v * H


def charger(nom):
    os.makedirs(DONNEES, exist_ok=True)
    f = os.path.join(DONNEES, nom)
    if not os.path.exists(f):
        urllib.request.urlretrieve(NE + nom, f)
    return json.load(open(f))


def anneaux(geo):
    for feat in geo["features"]:
        g = feat["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for p in polys:
            yield p


def lignes(geo):
    for feat in geo["features"]:
        g = feat["geometry"]
        ls = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
        for l in ls:
            yield l


def masque(geo, trous=True):
    m = Image.new("L", (L, H), 0)
    d = ImageDraw.Draw(m)
    for p in anneaux(geo):
        d.polygon([xy(*pt) for pt in p[0]], fill=255)
        for trou in (p[1:] if trous else []):
            d.polygon([xy(*pt) for pt in trou], fill=0)
    return m


def bruit(taille, flou, graine):
    """Bruit lisse entre 0 et 1, calculé en nombres décimaux (pas de marches visibles)."""
    rng = np.random.default_rng(graine)
    a = rng.random((H // taille + 3, L // taille + 3)).astype(np.float32)
    im = Image.fromarray(a, "F").resize(((L // taille + 3) * taille, (H // taille + 3) * taille), Image.BICUBIC)
    return np.asarray(im, np.float32)[taille:taille + H, taille:taille + L]


def fbm(graine):
    """Bruit fractal (plusieurs échelles) entre 0 et 1 : relief naturel, pas de motifs."""
    total = np.zeros((H, L), np.float32)
    poids = 0.0
    for i, (taille, w) in enumerate(((512, 1.0), (256, 0.55), (128, 0.32), (64, 0.18), (32, 0.1), (16, 0.05))):
        total += bruit(taille, 0, graine + i) * w
        poids += w
    t = total / poids
    return (t - t.min()) / (t.max() - t.min())


# Les grands déserts (lon min, lon max, lat min, lat max).
DESERTS = [(-17, 33, 16, 31), (34, 58, 14, 31), (44, 70, 25, 36), (75, 92, 36, 43), (92, 112, 39, 46),
           (118, 142, -30, -20), (14, 26, -28, -19), (-118, -104, 28, 37), (-72, -68, -27, -17), (-70, -66, -45, -38)]


def zones_desert():
    m = Image.new("L", (L, H), 0)
    d = ImageDraw.Draw(m)
    for a, b, c, e in DESERTS:
        x0, y0 = xy(a, e)
        x1, y1 = xy(b, c)
        d.ellipse([x0, y0, x1, y1], fill=255)
    return np.asarray(m.filter(ImageFilter.GaussianBlur(60))).astype(np.float32) / 255.0


def couleur(hexa):
    return np.array([int(hexa[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def melange(a, b, t):
    return a * (1 - t[..., None]) + b * t[..., None]


def carte():
    terre = masque(charger("ne_50m_land.geojson"), trous=False)
    # seulement les grands lacs (sinon des centaines de petits points blancs)
    geo_lacs = charger("ne_50m_lakes.geojson")
    def grand(f):
        c = f["geometry"]["coordinates"]
        pts = [pt for p in (c if f["geometry"]["type"] == "MultiPolygon" else [c]) for pt in p[0]]
        xs, ys = [q[0] for q in pts], [q[1] for q in pts]
        return (max(xs) - min(xs)) * (max(ys) - min(ys)) > 6.0
    geo_lacs["features"] = [f for f in geo_lacs["features"] if grand(f)]
    lacs = masque(geo_lacs)
    terre = ImageChops.subtract(terre, lacs)
    T = np.asarray(terre).astype(np.float32) / 255.0

    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None] * np.ones((1, L), np.float32)
    xx = np.ones((H, 1), np.float32) * np.linspace(0, 1, L, dtype=np.float32)[None, :]

    # --- l'océan : bleu profond, plus clair au centre, eaux peu profondes le long des côtes
    centre = np.clip(1.0 - np.sqrt(((xx - 0.5) * 1.1) ** 2 + ((yy - 0.45) * 1.6) ** 2), 0, 1)
    ocean = melange(np.broadcast_to(couleur("0A1F3D"), (H, L, 3)).copy(), np.broadcast_to(couleur("17457A"), (H, L, 3)).copy(), centre ** 1.3)
    ocean += (bruit(256, 0, 1) - 0.5)[..., None] * 14
    pres = np.asarray(terre.filter(ImageFilter.GaussianBlur(28))).astype(np.float32) / 255.0
    proche = np.asarray(terre.filter(ImageFilter.GaussianBlur(9))).astype(np.float32) / 255.0
    ocean = melange(ocean, np.broadcast_to(couleur("2B7FB8"), (H, L, 3)).copy(), np.clip(pres * 1.6, 0, 1) * 0.55)
    ocean = melange(ocean, np.broadcast_to(couleur("5FC4E8"), (H, L, 3)).copy(), np.clip(proche * 1.8, 0, 1) * 0.55)

    # --- la terre : couleur selon la latitude (neige, forêts, déserts, tropiques) + relief
    lat = np.array([LAT_HAUT], np.float32)
    # latitude de chaque ligne de pixels
    ys = YH - (np.arange(H, dtype=np.float32) + 0.5) / H * (YH - YB)
    lats = np.degrees(2 * np.arctan(np.exp(ys)) - np.pi / 2)[:, None] * np.ones((1, L), np.float32)
    a = np.abs(lats)
    vert = couleur("5E9C4F")
    foret = couleur("2E6B3A")
    sable = couleur("D8B57A")
    roche = couleur("9C8B6E")
    toundra = couleur("8E9E7E")
    neige = couleur("F2F6FA")
    relief = fbm(10)
    sol = np.broadcast_to(vert, (H, L, 3)).copy()
    # forêts tropicales près de l'équateur, et un peu partout selon le bruit
    sol = melange(sol, np.broadcast_to(foret, (H, L, 3)).copy(), np.clip(1 - np.abs(a - 3) / 14, 0, 1) * 0.85 + np.clip((fbm(20) - 0.55) * 2, 0, 0.4))
    # déserts aux bons endroits (Sahara, Arabie, Australie...)
    desert = np.clip(zones_desert() * 2.2, 0, 1) * np.clip(0.85 + (fbm(30) - 0.5) * 0.8, 0, 1)
    sol = melange(sol, np.broadcast_to(sable, (H, L, 3)).copy(), desert)
    # montagnes : plus rocheuses là où le relief est haut
    sol = melange(sol, np.broadcast_to(roche, (H, L, 3)).copy(), np.clip((relief - 0.68) * 3.5, 0, 0.7))
    sol = melange(sol, np.broadcast_to(toundra, (H, L, 3)).copy(), np.clip((a - 57) / 9, 0, 0.85))
    sol = melange(sol, np.broadcast_to(neige, (H, L, 3)).copy(), np.clip((a - 67) / 5, 0, 1))
    sol = melange(sol, np.broadcast_to(neige, (H, L, 3)).copy(), np.clip((relief - 0.82) * 6, 0, 0.8) * np.clip((a - 38) / 10, 0, 1))
    # ombrage du relief (lumière en haut à gauche), doux
    gy, gx = np.gradient(relief)
    pente = -gx - gy
    lumiere = np.clip(0.5 + pente / (np.percentile(np.abs(pente), 98) * 2.2), 0, 1)
    sol *= (0.88 + 0.24 * lumiere)[..., None]
    interieur = np.asarray(terre.filter(ImageFilter.GaussianBlur(14))).astype(np.float32) / 255.0
    sol *= (0.94 + 0.08 * (1 - interieur))[..., None]

    img = melange(ocean, sol, T)

    # --- frontières discrètes
    fr = Image.new("L", (L, H), 0)
    d = ImageDraw.Draw(fr)
    for l in lignes(charger("ne_50m_admin_0_boundary_lines_land.geojson")):
        pts = [xy(*pt) for pt in l]
        for p, q in zip(pts, pts[1:]):
            if abs(p[0] - q[0]) < L / 2:
                d.line([p, q], fill=255, width=3)
    F = np.asarray(fr.filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32) / 255.0 * T
    img = melange(img, np.broadcast_to(couleur("1D3B2A"), (H, L, 3)).copy(), F * 0.35)

    # --- trait de côte fin et lumineux
    bord = np.asarray(terre.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255.0
    img = melange(img, np.broadcast_to(couleur("E8F7FF"), (H, L, 3)).copy(), np.clip(bord * 2.5, 0, 1) * 0.5)

    # --- quadrillage léger sur l'océan (méridiens / parallèles tous les 30 degrés)
    g = Image.new("L", (L, H), 0)
    d = ImageDraw.Draw(g)
    for lon in range(-180, 181, 30):
        x, _ = xy(lon, 0)
        d.line([(x, 0), (x, H)], fill=255, width=2)
    for la in (-30, 0, 30, 60):
        _, y = xy(0, la)
        d.line([(0, y), (L, y)], fill=255, width=2)
    G = np.asarray(g.filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32) / 255.0 * (1 - T)
    img = melange(img, np.broadcast_to(couleur("9FD3FF"), (H, L, 3)).copy(), G * 0.12)

    # --- vignette douce sur les bords
    vig = np.clip(1.0 - (np.maximum(np.abs(xx - 0.5) * 2, np.abs(yy - 0.5) * 2) - 0.82) * 2.2, 0.55, 1.0)
    img *= vig[..., None]

    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((2048, 1024), Image.LANCZOS)
    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    out.save(SORTIE, optimize=True)
    print("ok", SORTIE)


# Les coordonnées (U, V) des villes du jeu sur cette carte.
VILLES = [("PARIS", 2.35, 48.86), ("LONDON", -0.13, 51.51), ("ROME", 12.50, 41.90), ("MADRID", -3.70, 40.42),
          ("ISTANBUL", 28.98, 41.01), ("CAIRO", 31.24, 30.04), ("NEW YORK", -74.01, 40.71), ("DUBAI", 55.27, 25.20),
          ("RIO", -43.17, -22.91), ("MEXICO CITY", -99.13, 19.43), ("LOS ANGELES", -118.24, 34.05),
          ("DELHI", 77.21, 28.61), ("SINGAPORE", 103.82, 1.35), ("TOKYO", 139.69, 35.69), ("SYDNEY", 151.21, -33.87),
          ("BORA BORA", -151.74, -16.50), ("BANGKOK", 100.50, 13.76), ("HONG KONG", 114.17, 22.32),
          ("SEOUL", 126.98, 37.57), ("VANCOUVER", -123.12, 49.28), ("AMSTERDAM", 4.90, 52.37), ("ATHENS", 23.73, 37.98),
          ("MARRAKECH", -7.99, 31.63), ("CAPE TOWN", 18.42, -33.92), ("MIAMI", -80.19, 25.76),
          ("SAN FRANCISCO", -122.42, 37.77), ("SHANGHAI", 121.47, 31.23), ("MALDIVES", 73.51, 4.18),
          ("BALI", 115.19, -8.65), ("CUSCO", -71.97, -13.53)]


def villes_uv():
    return [(n,) + uv(lon, lat) for n, lon, lat in VILLES]


if __name__ == "__main__":
    if "uv" in sys.argv:
        for n, u, v in villes_uv():
            print(f"{n:15s} U := {u:.4f}, V := {v:.4f}")
    else:
        carte()
