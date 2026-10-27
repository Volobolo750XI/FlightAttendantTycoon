"""CLASSEMENT du lobby : podium a 3 places + grand panneau "TOP PILOTS", style cartoon (vert argent, blanc,
gros contour sombre). Les joueurs (Player Reference) se posent sur les marches, les scores sur les billboards.
Ordre des marches de gauche a droite (vu de face) : 2 - 1 - 3.
Repere : face avant vers -Z, Y en haut, sol a y = 0, centre en x = 0.
Sortie : Modeles/Lobby/Classement.glb (+ apercu_classement.png)   Usage : python3 generate_classement.py
"""
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(HERE))
SORTIE = os.path.join(os.path.dirname(HERE), "Lobby", "Classement.glb")
POLICE = os.path.join(RACINE, "Outils", "TitanOne-Regular.ttf")
PBR = trimesh.visual.material.PBRMaterial
CONTOUR = (22, 27, 48)


def lin(rgb):
    c = np.asarray(rgb, float) / 255.0
    return list(np.round(np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4) * 255).astype(int)) + [255]


def col(nom, rgb, rugo=0.5, em=None):
    return PBR(name=nom, baseColorFactor=lin(rgb), roughnessFactor=rugo, metallicFactor=0.0, emissiveFactor=em)


def tex_titre(txt, w=2048, h=512, taille=300):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(POLICE, taille)
    d.text((w / 2, h / 2 + 10), txt, font=f, fill=(255, 255, 255, 255), anchor="mm", stroke_width=26, stroke_fill=CONTOUR)
    return img


def tex_numero(n):
    img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([40, 40, 472, 472], fill=(255, 255, 255, 255), outline=CONTOUR, width=26)
    d.text((256, 270), str(n), font=ImageFont.truetype(POLICE, 300), fill=(30, 170, 90, 255), anchor="mm",
           stroke_width=10, stroke_fill=CONTOUR)
    return img


def mat_tex(nom, img):
    return PBR(name=nom, baseColorTexture=img, alphaMode="MASK", alphaCutoff=0.5, doubleSided=False,
               roughnessFactor=0.5, metallicFactor=0.0)


M = {
    "vert": col("ClassementVert", (40, 185, 100), 0.45),
    "vert_fonce": col("ClassementVertFonce", (18, 118, 66), 0.5),
    "blanc": col("ClassementBlanc", (246, 248, 250), 0.45),
    "contour": col("ClassementContour", CONTOUR, 0.6),
    "poteau": col("ClassementPoteau", (150, 156, 166), 0.5),
    "lumiere": col("ClassementLumiere", (255, 255, 255), 0.3, [1.0, 1.0, 1.0]),
    "titre": mat_tex("ClassementTitre", tex_titre("TOP PILOTS")),
}
for n in range(1, 4):
    M[f"num_{n}"] = mat_tex(f"ClassementNumero{n}", tex_numero(n))

SC = trimesh.Scene()
PARTS = {}


def add(obj, k, m):
    if m.is_watertight and m.volume < 0:
        m.invert()
    PARTS.setdefault(obj, {}).setdefault(k, []).append(m)


def boite(x0, y0, z0, x1, y1, z1):
    m = trimesh.creation.box((x1 - x0, y1 - y0, z1 - z0))
    m.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return m


def quad(k, cx, cy, z, w, h):
    """panneau texture face -Z (lu depuis l'avant)"""
    v = np.array([[cx - w / 2, cy - h / 2, z], [cx + w / 2, cy - h / 2, z], [cx + w / 2, cy + h / 2, z], [cx - w / 2, cy + h / 2, z]])
    m = trimesh.Trimesh(v, [[0, 2, 1], [0, 3, 2]], process=False)
    m.visual = trimesh.visual.TextureVisuals(uv=np.array([[1, 0], [0, 0], [0, 1], [1, 1]]), material=M[k])
    return m


# ------------------------------------------------------------------ podium
MARCHES = [(2, 4.4, 1.4), (1, 0.0, 2.0), (3, -4.4, 1.05)]  # vu de face (depuis -Z) la droite est -X   # (place, x, hauteur)
for place, x, h in MARCHES:
    o = f"Marche_{place}"
    add(o, "contour", boite(x - 2.2, 0, -1.9, x + 2.2, h, 1.9))
    add(o, "vert", boite(x - 2.1, 0, -2.0, x + 2.1, h - 0.12, 2.0))
    add(o, "blanc", boite(x - 2.15, h - 0.12, -1.95, x + 2.15, h + 0.05, 1.95))
    add(o, "vert_fonce", boite(x - 2.12, 0.0, -2.02, x + 2.12, 0.25, 2.02))
    s = min(1.3, h * 0.75)
    m = quad(f"num_{place}", x, h * 0.48, -2.03, s, s)
    PARTS.setdefault(o, {}).setdefault(f"num_{place}", []).append(m)
    # repere au sol pour poser le Player Reference (petit rond blanc)
    c = trimesh.creation.cylinder(radius=0.9, height=0.03, sections=32)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    c.apply_translation([x, h + 0.065, 0.0])
    add(o, "vert_fonce", c)

# ------------------------------------------------------------------ grand panneau + compteurs de rebirths
# Les compteurs : la barre rose "rebirth" du HUD (Textures/Interface/FondRebirth.png) avec 4 TAMBOURS
# (Tambour_Chiffres.glb, un prop par chiffre) qui tournent pour afficher le nombre de rebirths, comme un compteur.
M["fond_rebirth"] = mat_tex("ClassementFondRebirth", Image.open(os.path.join(RACINE, "Textures", "Interface", "FondRebirth.png")).convert("RGBA"))
o = "Panneau_TopPilots"
for x in (-7.6, 7.6):
    add(o, "poteau", boite(x - 0.3, 0, 3.0, x + 0.3, 13.6, 3.6))
add(o, "contour", boite(-8.7, 6.0, 3.6, 8.7, 13.8, 4.1))
add(o, "vert", boite(-8.5, 6.2, 3.55, 8.5, 13.6, 3.62))
add(o, "vert_fonce", boite(-8.5, 6.2, 3.54, 8.5, 6.7, 3.61))
PARTS[o].setdefault("titre", []).append(quad("titre", 0, 11.7, 3.53, 15.0, 3.75))
for i in range(9):                                                           # petites lumieres
    x = -8.0 + i * 2.0
    add(o, "lumiere", trimesh.creation.icosphere(1, 0.22).apply_translation([x, 13.6, 3.45]))

ZP = 3.53 - 1.45                     # face avant des barres roses (les tambours sont derriere, dans un caisson)
YC = 8.35                            # hauteur du centre de la barre
TAMBOURS = []                        # (place, chiffre 0..3 de gauche a droite, x, y, z du centre du tambour)
for place, cx in ((1, 0.0), (2, 4.4), (3, -4.4)):
    oc = f"Compteur_{place}"
    add(oc, "contour", boite(cx - 2.05, YC - 0.62, ZP + 0.02, cx + 2.05, YC + 0.62, 3.55))     # caisson
    add(oc, "contour", boite(cx - 2.02, YC - 0.75, ZP + 0.004, cx + 2.02, YC + 0.75, ZP + 0.03))   # fond qui cache le tambour
    PARTS.setdefault(oc, {}).setdefault("fond_rebirth", []).append(quad("fond_rebirth", cx, YC, ZP, 4.0, 1.0))
    xbar = cx + 2.0 - 4.0 * (570 / 1024)        # centre de la partie rose (vue de face, la gauche est +X)
    ybar = YC + 0.5 - 130 / 256                 # centre vertical de la partie rose
    for i in range(4):
        TAMBOURS.append((place, i, round(xbar + (1.5 - i) * 0.56, 3), round(ybar, 3)))

# ------------------------------------------------------------------ export (un noeud par objet)
for obj, d in PARTS.items():
    for k, ms in d.items():
        m = trimesh.util.concatenate(ms)
        if not k.startswith("num_") and k not in ("titre", "fond_rebirth"):
            m.visual = trimesh.visual.TextureVisuals(material=M[k])
        else:
            m.visual = trimesh.visual.TextureVisuals(uv=np.vstack([x.visual.uv for x in ms]), material=M[k])
        SC.add_geometry(m, node_name=f"{obj}__{k}", geom_name=f"{obj}__{k}")
SC.export(SORTIE)

import json
import struct
b = open(SORTIE, "rb").read()
lj = struct.unpack("<I", b[12:16])[0]
js = json.loads(b[20:20 + lj])
rest = b[20 + lj:]
meshes, nodes, idx = [], [], {}
for nd in js["nodes"]:
    if "mesh" not in nd:
        continue
    o = nd["name"].split("__")[0]
    if o not in idx:
        idx[o] = len(meshes)
        meshes.append({"name": o, "primitives": []})
        nodes.append({"name": o, "mesh": idx[o]})
    meshes[idx[o]]["primitives"] += js["meshes"][nd["mesh"]]["primitives"]
js["meshes"], js["nodes"] = meshes, nodes
js["scenes"], js["scene"] = [{"nodes": list(range(len(nodes)))}], 0
s = json.dumps(js, separators=(",", ":")).encode()
s += b" " * ((4 - len(s) % 4) % 4)
open(SORTIE, "wb").write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(s) + len(rest)) + struct.pack("<II", len(s), 0x4E4F534A) + s + rest)
print(SORTIE, round(os.path.getsize(SORTIE) / 1e3), "Ko", [n["name"] for n in nodes])


# ------------------------------------------------------------------ le tambour (un prop par chiffre)
# Decagone : 10 faces, une par chiffre. Chiffre 0 face a l'avant (-Z) ; en tournant de +36 deg autour de X
# on passe au chiffre suivant. Pivot = centre du tambour (pour qu'il tourne sur lui-meme).
S_FACE, L_FACE = 0.42, 0.50
R = S_FACE / (2 * np.sin(np.radians(18)))
APO = R * np.cos(np.radians(18))


def atlas():
    W, H = 256, 2048
    img = Image.new("RGB", (W, H), (236, 92, 145))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(POLICE, 170)
    for k in range(10):
        y0 = k * H / 10
        d.rectangle([0, y0, W, y0 + 14], fill=(255, 150, 190))                 # reflet en haut
        d.rectangle([0, y0 + H / 10 - 10, W, y0 + H / 10], fill=CONTOUR)       # separation
        d.text((W / 2, y0 + H / 20 + 4), str(k), font=f, fill=(255, 255, 255), anchor="mm", stroke_width=12,
               stroke_fill=CONTOUR)
    return img


def tambour():
    V, F, UV = [], [], []
    for k in range(10):
        b = np.radians(36 * k)
        n = np.array([-np.sin(b), -np.cos(b)])        # (y, z) normale de la face k
        t = np.array([np.cos(b), -np.sin(b)])         # (y, z) "haut" de la face k
        c = n * APO
        haut, bas = c + t * S_FACE / 2, c - t * S_FACE / 2
        v0 = 1 - (k + 1) / 10 + 0.003
        v1 = 1 - k / 10 - 0.003
        i = len(V)
        # vue de face (depuis -Z), la droite est -X : u = 0 a +X
        V += [[L_FACE / 2, bas[0], bas[1]], [-L_FACE / 2, bas[0], bas[1]], [-L_FACE / 2, haut[0], haut[1]], [L_FACE / 2, haut[0], haut[1]]]
        UV += [[0, v0], [1, v0], [1, v1], [0, v1]]
        F += [[i, i + 2, i + 1], [i, i + 3, i + 2]]
    m = trimesh.Trimesh(np.array(V), np.array(F), process=False)
    if np.mean(np.einsum("ij,ij->i", m.face_normals, m.triangles_center)) < 0:
        m.invert()
    m.visual = trimesh.visual.TextureVisuals(uv=np.array(UV), material=PBR(
        name="TambourChiffres", baseColorTexture=atlas(), roughnessFactor=0.45, metallicFactor=0.0))
    ang = np.radians(np.arange(10) * 36 + 18)
    cap = []
    for sx in (1, -1):
        pts = np.c_[np.full(10, sx * L_FACE / 2), -np.sin(ang) * R, -np.cos(ang) * R]
        c = trimesh.Trimesh(np.vstack([pts, [[sx * L_FACE / 2, 0, 0]]]),
                            [[10, j, (j + 1) % 10] for j in range(10)], process=False)
        if c.face_normals[0][0] * sx < 0:
            c.invert()
        cap.append(c)
    cap = trimesh.util.concatenate(cap)
    cap.visual = trimesh.visual.TextureVisuals(material=PBR(name="TambourFlancs", baseColorFactor=lin(CONTOUR), roughnessFactor=0.6))
    sc = trimesh.Scene()
    sc.add_geometry(m, node_name="Tambour", geom_name="Tambour_Faces")
    sc.add_geometry(cap, node_name="Tambour_Flancs", geom_name="Tambour_Flancs")
    return sc


T_OUT = os.path.join(os.path.dirname(HERE), "Lobby", "Tambour_Chiffres.glb")
tambour().export(T_OUT)
print(T_OUT, round(os.path.getsize(T_OUT) / 1e3), "Ko")
print("Centres des tambours (metres, repere du podium ; x vers la GAUCHE vue de face, y haut, z profondeur) :")
for place, i, x, y in TAMBOURS:
    print(f"  place {place}, chiffre {i + 1}/4 : x={x:+.3f}  y={y:.3f}  z={ZP - 0.03 + APO:.3f}")
