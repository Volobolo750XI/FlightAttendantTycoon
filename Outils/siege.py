"""Siege d'avion simplifie, low poly mais tout en rondeurs.

Un seul mesh, un seul materiau : les couleurs viennent d'une petite texture
palette (bleu / blanc / gris / gris fonce), chaque piece pointe sur sa case.
Pivot au sol, au centre ; l'avant du siege regarde vers +Z. Unites : metres.

Usage : python3 siege.py [sortie.glb]
"""
import sys

import numpy as np
import trimesh
from PIL import Image
from trimesh.transformations import rotation_matrix
from trimesh.visual.material import PBRMaterial

PALETTE = {"bleu": (92, 122, 184), "blanc": (238, 240, 243), "gris": (190, 195, 202), "fonce": (70, 76, 88)}
NAMES = list(PALETTE)
CELL = 16


def palette_texture():
    img = Image.new("RGB", (CELL * len(NAMES), CELL))
    for i, n in enumerate(NAMES):
        img.paste(PALETTE[n], (i * CELL, 0, (i + 1) * CELL, CELL))
    return img


def uv_of(color):
    i = NAMES.index(color)
    return ((i + 0.5) / len(NAMES), 0.5)


def blob(size, center, color, tilt=0.0, roundness=0.45, res=(22, 14)):
    """Superellipsoide : une boite aux bords tres arrondis (roundness 0 = cube, 1 = ovale)."""
    a, b, c = np.asarray(size) / 2
    nu, nv = res
    u = np.linspace(-np.pi, np.pi, nu, endpoint=False)
    v = np.linspace(-np.pi / 2, np.pi / 2, nv)
    U, V = np.meshgrid(u, v)
    f = lambda w, e: np.sign(w) * np.abs(w) ** e
    x = a * f(np.cos(V), roundness) * f(np.cos(U), roundness)
    z = c * f(np.cos(V), roundness) * f(np.sin(U), roundness)
    y = b * f(np.sin(V), roundness)
    verts = np.column_stack([x.ravel(), y.ravel(), z.ravel()])
    faces = []
    for j in range(nv - 1):
        for i in range(nu):
            p, q = j * nu + i, j * nu + (i + 1) % nu
            faces += [[p, q + nu, q], [p, p + nu, q + nu]]
    m = trimesh.Trimesh(verts, faces)  # fusionne les poles et la couture -> ombrage lisse
    if tilt:
        m.apply_transform(rotation_matrix(np.radians(tilt), [1, 0, 0]))
    m.apply_translation(center)
    return color, m


def tube(p0, p1, r, color):
    """Barre arrondie (capsule)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    m = trimesh.creation.capsule(height=np.linalg.norm(d), radius=r, count=[10, 6])
    m.apply_translation([0, 0, np.linalg.norm(d) / 2])
    m.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], d / np.linalg.norm(d)))
    m.apply_translation(p0)
    return color, m


def build():
    parts = [
        # assise et dossier (incline vers l'arriere)
        blob((0.46, 0.13, 0.50), (0, 0.45, 0.03), "bleu"),
        blob((0.46, 0.80, 0.13), (0, 0.90, -0.24), "bleu", tilt=-12),
        # appui-tete avec housse blanche
        blob((0.40, 0.20, 0.10), (0, 1.27, -0.27), "bleu", tilt=-12, roundness=0.55),
        blob((0.24, 0.10, 0.03), (0, 1.27, -0.215), "blanc", tilt=-12, roundness=0.6),
        # coque blanche sous l'assise
        blob((0.50, 0.12, 0.50), (0, 0.35, 0.0), "blanc", roundness=0.5),
    ]
    for s in (-1, 1):
        x = s * 0.265
        parts += [
            # flancs blancs + accoudoirs
            blob((0.05, 0.30, 0.50), (x, 0.47, -0.02), "blanc", roundness=0.5),
            blob((0.07, 0.06, 0.40), (x, 0.66, 0.01), "gris", roundness=0.55),
            blob((0.075, 0.025, 0.36), (x, 0.695, 0.01), "fonce", roundness=0.6),
            # pieds : montant avant, montant arriere, rail au sol
            tube((x * 0.8, 0.30, 0.16), (x * 0.8, 0.02, 0.20), 0.018, "gris"),
            tube((x * 0.8, 0.30, -0.18), (x * 0.8, 0.02, -0.22), 0.018, "gris"),
            tube((x * 0.8, 0.02, -0.26), (x * 0.8, 0.02, 0.24), 0.018, "gris"),
        ]
    # barre transversale entre les pieds
    parts.append(tube((-0.21, 0.12, 0.0), (0.21, 0.12, 0.0), 0.015, "gris"))

    meshes = []
    for color, m in parts:
        m.visual = trimesh.visual.TextureVisuals(uv=np.tile(uv_of(color), (len(m.vertices), 1)))
        meshes.append(m)
    seat = trimesh.util.concatenate(meshes)
    seat.visual = trimesh.visual.TextureVisuals(
        uv=seat.visual.uv,
        material=PBRMaterial(name="Siege", baseColorTexture=palette_texture(),
                             metallicFactor=0.0, roughnessFactor=0.7))
    return seat


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "siege.glb"
    s = build()
    trimesh.Scene({"Siege": s}).export(out)
    print(out, len(s.faces), "triangles", s.extents)
