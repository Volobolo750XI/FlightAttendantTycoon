"""Allege un modele sans texture (couleurs unies par materiau) en UN seul mesh,
1 materiau, petite texture palette. Chaque couleur est reduite separement (les petits
details comme les yeux gardent leur forme).
Usage : python3 alleger_couleurs.py entree.glb sortie.glb [triangles=15000]
"""
import sys
import numpy as np
import trimesh
import pyfqmr
from PIL import Image
from trimesh.visual.material import PBRMaterial

entree, sortie = sys.argv[1], sys.argv[2]
cible = int(sys.argv[3]) if len(sys.argv) > 3 else 15000
s = trimesh.load(entree)
groupes = {}
for nom in s.graph.nodes_geometry:
    T, gname = s.graph[nom]
    g = s.geometry[gname].copy()
    g.apply_transform(T)
    c = tuple(int(x) for x in g.visual.material.baseColorFactor[:3])
    groupes.setdefault(c, []).append(trimesh.Trimesh(g.vertices, g.faces, process=False))
total = sum(len(m.faces) for l in groupes.values() for m in l)
couleurs = list(groupes)
img = Image.new("RGB", (8 * len(couleurs), 8))
for i, c in enumerate(couleurs):
    img.paste(c, (i * 8, 0, i * 8 + 8, 8))
pieces = []
for i, c in enumerate(couleurs):
    m = trimesh.util.concatenate(groupes[c])
    m.merge_vertices()
    part = max(300, int(cible * len(m.faces) / total))
    if len(m.faces) > part and len(m.faces) > 3000:
        sim = pyfqmr.Simplify()
        sim.setMesh(m.vertices, m.faces)
        sim.simplify_mesh(target_count=part, aggressiveness=4, preserve_border=True, verbose=0)
        v, f, _ = sim.getMesh()
        m = trimesh.Trimesh(v, f)
    m.visual = trimesh.visual.TextureVisuals(uv=np.tile([(i + 0.5) / len(couleurs), 0.5], (len(m.vertices), 1)))
    pieces.append(m)
    print(c, len(m.faces))
out = trimesh.util.concatenate(pieces)
out.visual = trimesh.visual.TextureVisuals(uv=out.visual.uv, material=PBRMaterial(
    baseColorTexture=img, metallicFactor=0.0, roughnessFactor=0.45))
out.export(sortie)
print(sortie, len(out.faces), "triangles", out.bounds.round(2).tolist())
