"""Fusionne un modele en plusieurs morceaux / avec des trous en UN SEUL mesh ferme (sans trou),
leger, avec la texture d'origine recuite dessus.

Usage : python3 fermer_modele.py entree.glb sortie.glb [triangles=6000] [texture=1024] [resolution=200]
"""
import sys
import numpy as np
import trimesh
import pyfqmr
import xatlas
from scipy import ndimage
from skimage import measure
from trimesh.visual.material import PBRMaterial
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from alleger_personnage import bake

a = sys.argv
entree, sortie = a[1], a[2]
cible = int(a[3]) if len(a) > 3 else 6000
taille = int(a[4]) if len(a) > 4 else 1024
reso = int(a[5]) if len(a) > 5 else 200

s = trimesh.load(entree)
geoms = []
for nom in s.graph.nodes_geometry:
    T, g = s.graph[nom]
    m = s.geometry[g].copy()
    m.apply_transform(T)
    geoms.append(m)
tex = geoms[0].visual.material.baseColorTexture
V = np.vstack([g.vertices for g in geoms])
UV = np.vstack([g.visual.uv for g in geoms])
off = np.cumsum([0] + [len(g.vertices) for g in geoms[:-1]])
F = np.vstack([g.faces + o for g, o in zip(geoms, off)])
orig = trimesh.Trimesh(V, F, process=False, visual=trimesh.visual.TextureVisuals(
    uv=UV, material=PBRMaterial(baseColorTexture=tex)))

# 1. voxels : surface -> volume plein (on bouche les trous et les jointures)
pitch = orig.extents.max() / reso
vox = orig.voxelized(pitch)
g = vox.matrix
g = ndimage.binary_closing(np.pad(g, 3), iterations=2)
g = ndimage.binary_fill_holes(g)
lab, n = ndimage.label(g)
if n > 1:
    tailles = ndimage.sum(g, lab, range(1, n + 1))
    g = lab == (np.argmax(tailles) + 1)
# 2. surface fermee
vv, ff, _, _ = measure.marching_cubes(g.astype(np.float32), 0.5)
vv = (vv - 3) * pitch
vv = trimesh.transform_points(vv, vox.transform) if False else vv + vox.translation
ferme = trimesh.Trimesh(vv, ff[:, ::-1])
trimesh.smoothing.filter_taubin(ferme, iterations=15)
# 3. allegement
sim = pyfqmr.Simplify()
sim.setMesh(ferme.vertices, ferme.faces)
sim.simplify_mesh(target_count=cible, aggressiveness=5, preserve_border=False, verbose=0)
v, f, _ = sim.getMesh()
# 4. UV + texture recuite depuis l'original
vmap, idx, uv = xatlas.parametrize(v, f)
v2 = v[vmap]
img = bake(orig, v2, idx, uv, taille)
low = trimesh.Trimesh(v2, idx, process=False, visual=trimesh.visual.TextureVisuals(
    uv=uv, material=PBRMaterial(baseColorTexture=img, metallicFactor=0.0, roughnessFactor=0.85)))
low.export(sortie)
chk = trimesh.Trimesh(v, f)
print(sortie, len(idx), "triangles, ferme :", chk.is_watertight, "morceaux :", len(chk.split(only_watertight=False)))
print("bornes orig", orig.bounds.round(3).tolist(), "nouveau", chk.bounds.round(3).tolist())
