"""Met un personnage (pose A, bras le long du corps) en pose T (bras à l'horizontale).

Pour chaque bras : on part de la main et on remonte le bras en suivant les arêtes du mesh,
sans passer sous l'aisselle (x > xc), ce qui isole le bras du torse. Le bras tourne ensuite
autour de l'épaule pour pointer à l'horizontale ; près de l'épaule la rotation est progressive
(pas de déchirure). La texture suit (les UV ne changent pas).

Usage : python3 pose_t.py entree.glb sortie.glb
"""
import sys
from collections import deque

import numpy as np
import trimesh


def soude(m):
    """Graphe des sommets fusionnés par position (les coutures UV coupent sinon le mesh)."""
    _, idx, inv = np.unique(np.round(m.vertices, 6), axis=0, return_index=True, return_inverse=True)
    inv = inv.ravel()
    w = trimesh.Trimesh(m.vertices[idx], inv[m.faces], process=False)
    return w, inv


def region_bras(m, cote, xc):
    w, inv = m
    r = _region(w, cote, xc)
    return r[inv]


def _region(m, cote, xc):
    v = m.vertices
    x = v[:, 0] * cote
    graines = np.where((x > 0.27) & (v[:, 1] < 0.86) & (v[:, 1] > 0.70))[0]
    # axe approximatif du bras (épaule -> main) : on refuse ce qui est trop du côté du corps
    S = np.array([cote * 0.19, 1.40])
    W = v[graines, :2].mean(0)
    d = (W - S) / np.linalg.norm(W - S)
    n_in = np.array([-d[1], d[0]])
    if np.dot(n_in, [-cote, 0]) < 0:
        n_in = -n_in
    vers_corps = (v[:, :2] - S) @ n_in
    ok = (x > xc) & (vers_corps < 0.075)
    voisins = m.vertex_neighbors
    vu = np.zeros(len(v), bool)
    q = deque(graines[ok[graines]])
    vu[list(q)] = True
    while q:
        i = q.popleft()
        for j in voisins[i]:
            if not vu[j] and ok[j]:
                vu[j] = True
                q.append(j)
    return vu


def pose_t(m):
    m = m.copy()
    v = m.vertices.copy()
    graphe = soude(m)
    bras = np.zeros(len(v), bool)
    for cote in (-1, 1):
        # plus petit xc qui isole le bras (la zone ne doit pas atteindre le milieu du corps)
        for xc in np.arange(0.13, 0.25, 0.005):
            r = region_bras(graphe, cote, xc)
            if r.any() and (np.abs(v[r, 0]) > 0.10).all() and v[r, 1].max() < 1.62:
                break
        x = v[:, 0] * cote
        main = r & (v[:, 1] < 0.86) & (x > 0.27)
        W = v[main].mean(0)
        S = np.array([cote * (xc + 0.04), 1.40, v[r & (v[:, 1] > 1.3), 2].mean()])
        d = W - S
        d[2] = 0
        d /= np.linalg.norm(d)
        cible = np.array([cote, 0.0, 0.0])
        ang = np.arctan2(np.cross(d, cible)[2], np.dot(d, cible))
        bras |= r
        t = (v[r] - S) @ d
        w = np.clip((t + 0.02) / 0.14, 0, 1)
        w = w * w * (3 - 2 * w)
        p = v[r] - S
        a = ang * w
        c, s = np.cos(a), np.sin(a)
        v[r, 0] = S[0] + c * p[:, 0] - s * p[:, 1]
        v[r, 1] = S[1] + s * p[:, 0] + c * p[:, 1]
        print("  bras", cote, "xc", round(xc, 3), "angle", round(np.degrees(ang), 1), "sommets", int(r.sum()))
    # membrane : triangles qui reliaient l'intérieur du bras au flanc (collés dans le modèle
    # d'origine) et qui s'étirent énormément une fois le bras levé -> on les retire
    v0 = m.vertices
    e0 = np.linalg.norm(v0[m.faces] - v0[np.roll(m.faces, 1, axis=1)], axis=2).max(1)
    e1 = np.linalg.norm(v[m.faces] - v[np.roll(m.faces, 1, axis=1)], axis=2).max(1)
    garder = e1 < np.maximum(1.8 * e0, 0.02)
    print("  triangles de membrane retirés :", int((~garder).sum()))
    retires = m.faces[~garder]
    m.vertices = v
    m.update_faces(garder)
    m = boucher(m, retires, bras)
    m.remove_unreferenced_vertices()
    return m


def boucher(m, retires, bras):
    """Rebouche les trous laissés par la membrane (éventail depuis le centre de chaque trou)."""
    _, idx, inv = np.unique(np.round(m.vertices, 6), axis=0, return_index=True, return_inverse=True)
    inv = inv.ravel()
    F = inv[m.faces]
    touches = set(inv[np.unique(retires)].tolist()) if len(retires) else set()
    e = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    cle = np.sort(e, axis=1)
    _, ii, cnt = np.unique(cle, axis=0, return_inverse=True, return_counts=True)
    bord = e[cnt[ii.ravel()] == 1]
    suivant = {}
    for a, b in bord:
        suivant.setdefault(a, []).append(b)
    uv = m.visual.uv
    V = list(m.vertices)
    UV = list(uv)
    faces = [m.faces]
    vus = set()
    nb = 0
    for depart in list(suivant):
        if depart in vus or depart not in touches:
            continue
        boucle, a = [depart], depart
        while True:
            nxt = [b for b in suivant.get(a, []) if b not in vus]
            if not nxt:
                break
            b = nxt[0]
            vus.add(b)
            if b == depart:
                break
            boucle.append(b)
            a = b
            if len(boucle) > 400:
                break
        if len(boucle) < 3 or b != depart:
            continue
        rep = idx[boucle]
        # le trou longe le bras ET le flanc : on bouche chaque côté séparément
        cote = bras[rep]
        n = len(rep)
        if cote.all() or not cote.any():
            morceaux = [list(range(n))]
        else:
            s0 = int(np.where(cote != np.roll(cote, 1))[0][0])
            ordre = [(s0 + i) % n for i in range(n)]
            morceaux, cur = [], [ordre[0]]
            for i in ordre[1:]:
                if cote[i] == cote[cur[-1]]:
                    cur.append(i)
                else:
                    morceaux.append(cur)
                    cur = [i]
            morceaux.append(cur)
        for mor in morceaux:
            if len(mor) < 3:
                continue
            rr = rep[mor]
            q = len(rr)
            # copies des sommets du bord avec une seule UV (couleur unie du tissu voisin)
            u0 = uv[rr[q // 2]]
            base = len(V)
            V.extend(m.vertices[rr])
            UV.extend([u0] * q)
            k = len(V)
            V.append(m.vertices[rr].mean(0))
            UV.append(u0)
            faces.append(np.array([[base + (i + 1) % q, base + i, k] for i in range(q)]))
            nb += 1
    print("  trous rebouchés :", nb)
    return trimesh.Trimesh(np.array(V), np.vstack(faces), process=False,
                           visual=trimesh.visual.TextureVisuals(uv=np.array(UV), material=m.visual.material))


if __name__ == "__main__":
    s = trimesh.load(sys.argv[1])
    m = s.to_geometry() if isinstance(s, trimesh.Scene) else s
    pose_t(m).export(sys.argv[2])
