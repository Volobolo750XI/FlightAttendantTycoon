# Rendu par lancer de rayons (embree) : vrai z-buffer, pas d'erreurs d'ordre.
import sys, numpy as np, trimesh
from PIL import Image
f, out = sys.argv[1], sys.argv[2]
cam = np.array([float(v) for v in sys.argv[3].split(',')]); cible = np.array([float(v) for v in sys.argv[4].split(',')])
sc = trimesh.load(f, force='scene')
meshes, cols = [], []
for node in sc.graph.nodes_geometry:
    T, g = sc.graph[node]; m = sc.geometry[g].copy(); m.apply_transform(T)
    c = np.array([180, 180, 190.])
    try:
        mat = m.visual.material
        if getattr(mat, 'baseColorTexture', None) is not None:
            c = np.array(mat.baseColorTexture.convert('RGB').resize((1, 1)).getpixel((0, 0)), float)
        elif getattr(mat, 'baseColorFactor', None) is not None:
            c = np.array(mat.baseColorFactor[:3], float)
    except Exception:
        pass
    meshes.append(trimesh.Trimesh(m.vertices, m.faces, process=False)); cols.append(np.tile(c, (len(m.faces), 1)))
M = trimesh.util.concatenate(meshes); C = np.vstack(cols)
W, H, fo = 1000, 560, 500
fwd = cible - cam; fwd /= np.linalg.norm(fwd)
right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right); up = np.cross(right, fwd)
u, v = np.meshgrid(np.arange(W) - W / 2, H / 2 - np.arange(H))
d = fwd[None] * fo + u.reshape(-1, 1) * right + v.reshape(-1, 1) * up
d /= np.linalg.norm(d, axis=1, keepdims=True)
from trimesh.ray.ray_pyembree import RayMeshIntersector
r = RayMeshIntersector(M)
tri = r.intersects_first(np.tile(cam, (len(d), 1)), d)
img = np.zeros((len(d), 3)) + [255, 0, 255]
ok = tri >= 0
n = M.face_normals[tri[ok]]
sh = 0.35 + 0.65 * np.abs((n * d[ok]).sum(1))
img[ok] = C[tri[ok]] * sh[:, None]
Image.fromarray(img.reshape(H, W, 3).clip(0, 255).astype(np.uint8)).save(out)
