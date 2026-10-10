"""Bulle de ciel (dôme inversé, vu de l'intérieur) + nuages cartoon pour la phase « en vol ».

- Ciel.glb : sphère de 300 m de rayon, faces tournées vers l'intérieur, texture émissive
  (bleu profond en haut, horizon clair, mer de nuages blanche en dessous). Pivot au centre.
- Nuage_1..4.glb : nuages ronds cartoon (amas de boules), blancs avec dessous légèrement gris.
Usage : python3 ciel.py
"""
import os
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFilter

SORTIE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Modeles", "Ciel")
ROT = trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])   # Z-up -> Y-up glTF


def texture_ciel(W=2048, H=1024, graine=3):
    rng = np.random.default_rng(graine)
    v = np.linspace(0, 1, H)[:, None]                  # 0 = zénith, 0.5 = horizon, 1 = nadir
    haut = np.array([38, 110, 215]); horizon = np.array([190, 225, 250]); mer = np.array([245, 248, 252])
    t = np.clip(v / 0.5, 0, 1) ** 1.6
    ciel = haut * (1 - t[..., None]) + horizon * t[..., None]
    img = np.where(v[..., None] < 0.5, ciel, mer * np.ones_like(ciel)).repeat(W, axis=1).reshape(H, W, 3)
    im = Image.fromarray(img.astype(np.uint8))
    # mer de nuages : bosses blanches sur la ligne d'horizon et ombres douces dessous
    nu = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(nu)
    for _ in range(420):
        x = rng.uniform(0, W); y = H * rng.uniform(0.47, 0.62); r = rng.uniform(18, 70) * (1 + (y / H - 0.47) * 3)
        d.ellipse((x - r * 1.6, y - r, x + r * 1.6, y + r), fill=255)
        if x + r * 1.6 > W:                               # raccord gauche / droite
            d.ellipse((x - W - r * 1.6, y - r, x - W + r * 1.6, y + r), fill=255)
    nu = nu.filter(ImageFilter.GaussianBlur(6))
    ombre = nu.filter(ImageFilter.GaussianBlur(14)).transform(nu.size, Image.AFFINE, (1, 0, 0, 0, 1, -10))
    im.paste((200, 214, 232), mask=ombre.point(lambda a: a * 0.5))
    im.paste((255, 255, 255), mask=nu)
    # quelques petits nuages hauts dans le ciel
    hn = Image.new("L", (W, H), 0); d = ImageDraw.Draw(hn)
    for _ in range(40):
        x = rng.uniform(0, W); y = H * rng.uniform(0.25, 0.44); r = rng.uniform(8, 26)
        for k in range(5):
            d.ellipse((x + k * r * 0.9 - r, y - r * (0.6 + 0.4 * (k % 2)), x + k * r * 0.9 + r, y + r * 0.5), fill=200)
    im.paste((255, 255, 255), mask=hn.filter(ImageFilter.GaussianBlur(5)))
    return im


def ciel():
    R = 300.0
    s = trimesh.creation.uv_sphere(radius=R, count=[64, 128])
    s.invert()                                           # on le voit de l'intérieur
    p = s.vertices / R
    u = (np.arctan2(p[:, 1], p[:, 0]) / (2 * np.pi)) % 1.0
    v = np.arccos(np.clip(p[:, 2], -1, 1)) / np.pi       # 0 en haut
    # couture : on duplique les sommets de la couture pour éviter le dégradé qui fait le tour
    tex = texture_ciel()
    mat = trimesh.visual.material.PBRMaterial("Ciel", baseColorTexture=tex, emissiveTexture=tex,
                                              emissiveFactor=[1.0, 1.0, 1.0], roughnessFactor=1.0, metallicFactor=0.0,
                                              doubleSided=True)
    f = s.faces
    uf = u[f]
    # faces qui chevauchent la couture : on décale les u < 0.5 de +1
    fix = (uf.max(1) - uf.min(1)) > 0.5
    V = s.vertices[f.reshape(-1)]
    U = uf.copy(); U[fix] = np.where(U[fix] < 0.5, U[fix] + 1, U[fix])
    UV = np.c_[U.reshape(-1), 1 - v[f].reshape(-1)]
    m = trimesh.Trimesh(V, np.arange(len(V)).reshape(-1, 3), process=False)
    m.visual = trimesh.visual.TextureVisuals(uv=UV, material=mat)
    m.apply_transform(ROT)
    m.export(os.path.join(SORTIE, "Ciel.glb"))
    tex.save(os.path.join(SORTIE, "texture_ciel.png"))


def nuage(n, graine):
    rng = np.random.default_rng(graine)
    boules = []
    L = rng.uniform(14, 24)
    for _ in range(rng.integers(9, 15)):
        x = rng.uniform(-L / 2, L / 2)
        r = rng.uniform(2.5, 5.5) * (1 - abs(x) / L)  + 1.5
        b = trimesh.creation.icosphere(subdivisions=3, radius=r)
        b.apply_translation([x, rng.uniform(-3, 3), r * 0.55 + rng.uniform(-0.5, 1.5)])
        boules.append(b)
    m = trimesh.boolean.union(boules) if False else trimesh.util.concatenate(boules)
    m.vertices[:, 2] = np.maximum(m.vertices[:, 2], 0.0)            # dessous aplati
    mat = trimesh.visual.material.PBRMaterial("Nuage", baseColorFactor=[255, 255, 255, 255],
                                              emissiveFactor=[0.35, 0.37, 0.4], roughnessFactor=1.0, metallicFactor=0.0)
    m.visual = trimesh.visual.TextureVisuals(material=mat)
    m.apply_transform(ROT)
    m.export(os.path.join(SORTIE, f"Nuage_{n}.glb"))


if __name__ == "__main__":
    os.makedirs(SORTIE, exist_ok=True)
    ciel()
    for n in range(1, 5):
        nuage(n, 10 + n)
    print("ok")
