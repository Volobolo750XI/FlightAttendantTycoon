# Nouveau style d'interface "gros cartoon" (comme les meilleurs tycoons Fortnite) :
#   - une POLICE en images (dossier Textures/TexteCartoon) : lettres blanches tres epaisses, gros contour
#     sombre, petite ombre dessous. Le Verse les assemble pour ecrire n'importe quel texte, en couleur
#     (teinte) : Verse/ecriture_cartoon.verse (genere par ce script, avec la largeur de chaque lettre).
#   - le KIT de l'ecran du PC (Textures/InterfacePC) redessine dans le meme style : gros contour
#     sombre, degrade, bord clair a l'interieur, reflet brillant, epaisseur 3D en bas.
#     Memes noms qu'avant (rien a changer dans le Verse pour eux) + Entete, Fermer, Panneau, Ligne...
# Aucune couleur jaune.
#   python Outils/interface_cartoon.py
import os

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
LETTRES = os.path.join(RACINE, "Textures", "TexteCartoon")
KIT = os.path.join(RACINE, "Textures", "InterfacePC")
VERSE = os.path.join(RACINE, "Verse", "ecriture_cartoon.verse")
POLICE = os.path.join(ICI, "TitanOne-Regular.ttf")       # police libre (SIL OFL), Google Fonts
CONTOUR = (22, 27, 48, 255)                                 # presque noir, bleute (comme la reference)
K = 4                                                       # sur-echantillonnage (bords lisses)


def hexa(h, a=255):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


# ------------------------------------------------------------------ police en images
H_IMG = 128                    # hauteur de chaque image de lettre
TAILLE = 92                    # taille de police (pixels a l'echelle 1)
TRAIT = 11                     # epaisseur du contour
OMBRE = 6                      # ombre portee vers le bas
SYMBOLES = {"$": "Dollar", ".": "Point", ",": "Virgule", ":": "DeuxPoints", "-": "Tiret", "+": "Plus",
            "/": "Slash", "%": "Pourcent", "!": "Exclamation", "?": "Question", "(": "ParentheseG",
            ")": "ParentheseD", "|": "Barre", "#": "Diese", "<": "Inferieur", ">": "Superieur", "=": "Egal",
            "*": "Etoile", "[": "CrochetG", "]": "CrochetD", "&": "Et"}
CARACTERES = [chr(c) for c in range(ord("A"), ord("Z") + 1)] + [chr(c) for c in range(ord("a"), ord("z") + 1)] + \
    [str(i) for i in range(10)] + list(SYMBOLES)


def nom_lettre(c):
    if c.isupper():
        return f"L_{c}"
    if c.islower():
        return f"L_{c}_min"
    if c.isdigit():
        return f"L_{c}"
    return f"L_{SYMBOLES[c]}"


def police_cartoon():
    os.makedirs(LETTRES, exist_ok=True)
    f = ImageFont.truetype(POLICE, TAILLE * K)
    asc, desc = f.getmetrics()
    _, haut_cap, _, bas_cap = f.getbbox("H")
    # ligne de base placee pour que les MAJUSCULES soient centrees dans l'image (ombre comprise)
    base = (H_IMG * K) / 2 + (bas_cap - haut_cap) / 2 - OMBRE * K / 2
    marge = TRAIT + 3
    largeurs = {}
    for c in CARACTERES:
        av = f.getlength(c)
        L = int(np.ceil(av + 2 * marge * K))
        im = Image.new("RGBA", (L, H_IMG * K), (0, 0, 0, 0))
        pos = (marge * K, base)
        # masques : lettre, lettre + contour
        m = Image.new("L", im.size, 0)
        ImageDraw.Draw(m).text(pos, c, font=f, fill=255, anchor="ls")
        mc = Image.new("L", im.size, 0)
        ImageDraw.Draw(mc).text(pos, c, font=f, fill=255, anchor="ls", stroke_width=TRAIT * K)
        # ombre portee (contour decale vers le bas)
        ombre = ImageChops.offset(mc, 0, OMBRE * K)
        im.paste(Image.new("RGBA", im.size, CONTOUR), (0, 0), ombre)
        im.paste(Image.new("RGBA", im.size, CONTOUR), (0, 0), mc)
        # remplissage : blanc en haut, gris-bleu tres clair en bas (relief)
        g = np.linspace(0, 1, im.size[1])[:, None]
        haut = (base - (bas_cap - haut_cap)) / im.size[1]
        t = np.clip((g - haut) / max(1e-3, (base / im.size[1] - haut)), 0, 1)
        coul = np.array([255, 255, 255]) * (1 - t * 0.85) + np.array([214, 224, 236]) * (t * 0.85)
        remp = Image.fromarray(np.repeat(coul[:, None, :], im.size[0], 1).astype(np.uint8)).convert("RGBA")
        im.paste(remp, (0, 0), m)
        # petit reflet en haut de la lettre
        ref = Image.new("L", im.size, 0)
        ImageDraw.Draw(ref).rectangle([0, base - (bas_cap - haut_cap) - 2 * K, im.size[0],
                                       base - (bas_cap - haut_cap) * 0.78], fill=60)
        im.paste(Image.new("RGBA", im.size, (255, 255, 255, 255)), (0, 0), ImageChops.multiply(ref, m))
        out = im.resize((max(1, round(L / K)), H_IMG), Image.LANCZOS)
        out.save(os.path.join(LETTRES, nom_lettre(c) + ".png"))
        largeurs[c] = out.size[0] / H_IMG
    espace = f.getlength(" ") / K / H_IMG
    return largeurs, marge / H_IMG, espace


def lit_verse(c):
    if c == "'":
        return "'\\''"
    return f"'{c}'"


def ecrire_verse(largeurs, marge, espace):
    g = ",\n            ".join(f"{lit_verse(c)} => TexteCartoon.{nom_lettre(c)}" for c in CARACTERES)
    l = ",\n            ".join(f"{lit_verse(c)} => {largeurs[c]:.4f}" for c in CARACTERES)
    v = f'''using {{ /Verse.org/Colors }}
using {{ /Verse.org/Assets }}
using {{ /UnrealEngine.com/Temporary/SpatialMath }}
using {{ /UnrealEngine.com/Temporary/UI }}

# Flight Attendant Tycoon - le TEXTE CARTOON de toutes les interfaces.
# FICHIER GENERE par Outils/interface_cartoon.py : ne pas modifier a la main.
#
# Chaque lettre est une image du dossier TexteCartoon (lettre blanche tres epaisse, gros contour sombre).
# Ecrire() les pose cote a cote, de la couleur voulue (teinte), centre / a gauche / a droite dans une
# boite. Si le texte est trop long pour la boite, il est reduit pour rentrer.
# Les positions sont celles d'un ecran 1920 x 1080 (X, Y = coin haut gauche de la boite).
# Dans le Tiroir a contenu : importer le dossier Textures/TexteCartoon (a la racine, comme InterfacePC).

ecriture_cartoon := class:
    Glyphes:[char]texture = map{{
            {g}}}

    # largeur de chaque image de lettre, divisee par sa hauteur
    Largeurs:[char]float = map{{
            {l}}}

    # bord transparent a gauche et a droite de chaque image (contour compris), divise par la hauteur
    Marge:float = {marge:.4f}
    # largeur d'un espace, divisee par la hauteur
    Espace:float = {espace:.4f}
    # hauteur de l'image d'une lettre par rapport a la hauteur de la boite
    Agrandir:float = 1.30
    # petit espace en plus entre 2 lettres (divise par la hauteur) : les contours ne se chevauchent pas trop
    Espacement:float = 0.025

    # Largeur du texte pour une hauteur d'image de 1.
    Mesure(S:string):float =
        var W:float = 0.0
        for (C : S):
            if (R := Largeurs[C]):
                set W += R - 2.0 * Marge + Espacement
            else:
                set W += Espace
        W + 2.0 * Marge - Espacement

    Ecrire(S:string, Hex:string, J:text_justification, X:float, Y:float, L:float, H:float, Couche:type{{_X:int where 0 <= _X, _X <= 2147483647}}):[]canvas_slot =
        EcrireAncre(S, Hex, J, X - 960.0, Y - 540.0, L, H, Couche, vector2{{X := 0.5, Y := 0.5}})

    # Comme Ecrire, mais X, Y sont des decalages depuis un point d'accroche de l'ecran (Ancre :
    # 0,0 = coin haut gauche ; 0,0.5 = milieu du bord gauche ; 0.5,0.5 = centre).
    EcrireAncre(S:string, Hex:string, J:text_justification, X:float, Y:float, L:float, H:float, Couche:type{{_X:int where 0 <= _X, _X <= 2147483647}}, Ancre:vector2):[]canvas_slot =
        W0 := Mesure(S)
        var T:float = H * Agrandir
        if (W0 * T > L, W0 > 0.0):
            set T = L / W0
        Largeur := W0 * T
        var PX:float = X + (L - Largeur) / 2.0
        if (J = text_justification.Left):
            set PX = X
        else if (J = text_justification.Right):
            set PX = X + L - Largeur
        Haut := Y + H / 2.0 - T / 2.0
        Teinte := MakeColorFromHex(Hex)
        var Slots:[]canvas_slot = array{{}}
        for (C : S):
            if (Img := Glyphes[C], R := Largeurs[C]):
                set Slots += array{{Lettre(Img, Teinte, PX, Haut, R * T, T, Couche, Ancre)}}
                set PX += (R - 2.0 * Marge + Espacement) * T
            else:
                set PX += Espace * T
        Slots

    Lettre(Img:texture, Teinte:color, X:float, Y:float, L:float, H:float, Couche:type{{_X:int where 0 <= _X, _X <= 2147483647}}, Ancre:vector2):canvas_slot =
        canvas_slot:
            Anchors := anchors{{Minimum := Ancre, Maximum := Ancre}}
            Alignment := vector2{{X := 0.0, Y := 0.0}}
            Offsets := margin{{Left := X, Top := Y, Right := L, Bottom := H}}
            SizeToContent := false
            ZOrder := Couche
            Widget := texture_block{{DefaultImage := Img, DefaultTint := Teinte, DefaultDesiredSize := vector2{{X := L, Y := H}}}}

    # Efface les lettres d'avant (Anciennes) de la toile et ecrit le nouveau texte. Renvoie les
    # nouvelles lettres (a garder pour la prochaine fois). Pour les textes qui changent.
    Remplacer(Toile:canvas, Anciennes:[]widget, S:string, Hex:string, J:text_justification, X:float, Y:float, L:float, H:float, Couche:type{{_X:int where 0 <= _X, _X <= 2147483647}}, Ancre:vector2):[]widget =
        for (W : Anciennes) {{ Toile.RemoveWidget(W) }}
        Slots := EcrireAncre(S, Hex, J, X, Y, L, H, Couche, Ancre)
        for (Slot : Slots) {{ Toile.AddWidget(Slot) }}
        for (Slot : Slots) {{ Slot.Widget }}
'''
    open(VERSE, "w").write(v)


# ------------------------------------------------------------------ kit : pieces cartoon
def degrade(L, H, haut, bas):
    g = np.linspace(0, 1, H)[:, None, None]
    c = np.array(hexa(haut)[:3]) * (1 - g) + np.array(hexa(bas)[:3]) * g
    return Image.fromarray(np.repeat(c, L, 1).astype(np.uint8)).convert("RGBA")


def piece(nom, l, h, r, haut, bas, ep=10, levre=None, bord=0.45, reflet=0.30, dossier=KIT):
    """Rectangle arrondi cartoon : contour sombre, epaisseur 3D en bas (levre), degrade,
    fin bord clair a l'interieur, reflet brillant en haut."""
    L, H, R, E = l * K, h * K, r * K, ep * K
    lv = (levre if levre is not None else max(4, h // 18)) * K
    im = Image.new("RGBA", (L, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, L - 1, H - 1], R, fill=CONTOUR)
    # epaisseur : la couleur du bas, assombrie, visible sous la face
    fonce = tuple(int(v * 0.62) for v in hexa(bas)[:3]) + (255,)
    d.rounded_rectangle([E, E, L - 1 - E, H - 1 - E], max(2, R - E), fill=fonce)
    face = [E, E, L - 1 - E, H - 1 - E - lv]
    m = Image.new("L", (L, H), 0)
    ImageDraw.Draw(m).rounded_rectangle(face, max(2, R - E), fill=255)
    im.paste(degrade(L, H, haut, bas), (0, 0), m)
    # bord clair a l'interieur de la face
    if bord:
        b = Image.new("L", (L, H), 0)
        e2 = max(3 * K, E // 2)
        ImageDraw.Draw(b).rounded_rectangle(face, max(2, R - E), outline=int(255 * bord), width=e2)
        im.paste(Image.new("RGBA", (L, H), (255, 255, 255, 255)), (0, 0), ImageChops.multiply(b, m))
    # reflet brillant (bande arrondie en haut)
    if reflet:
        rf = Image.new("L", (L, H), 0)
        fh = face[3] - face[1]
        ImageDraw.Draw(rf).rounded_rectangle([face[0] + R * 0.6, face[1] + fh * 0.07, face[2] - R * 0.6, face[1] + fh * 0.30],
                                             int(fh * 0.12), fill=int(255 * reflet))
        im.paste(Image.new("RGBA", (L, H), (255, 255, 255, 255)), (0, 0), ImageChops.multiply(rf.filter(ImageFilter.GaussianBlur(K * 2)), m))
    out = im.resize((l, h), Image.LANCZOS)
    out.save(os.path.join(dossier, nom + ".png"))
    return out


def fermer():
    """Bouton rouge carre avec une grosse croix blanche (fermer / retour)."""
    T = 256
    im = piece("Fermer", T, T, 40, "FF5A5F", "D7263D", ep=14, levre=16, reflet=0.35)
    s = K
    big = Image.new("RGBA", (T * s, T * s), (0, 0, 0, 0))
    for w, col in ((58, CONTOUR), (36, (255, 255, 255, 255))):
        d = ImageDraw.Draw(big)
        a, b = 78 * s, 170 * s
        d.line([(a, a - 6 * s), (b, b - 6 * s)], fill=col, width=w * s)
        d.line([(b, a - 6 * s), (a, b - 6 * s)], fill=col, width=w * s)
        for p in ((a, a - 6 * s), (b, b - 6 * s), (b, a - 6 * s), (a, b - 6 * s)):
            d.ellipse([p[0] - w * s / 2, p[1] - w * s / 2, p[0] + w * s / 2, p[1] + w * s / 2], fill=col)
    im.alpha_composite(big.resize((T, T), Image.LANCZOS))
    im.save(os.path.join(KIT, "Fermer.png"))


def kit():
    os.makedirs(KIT, exist_ok=True)
    # fenetres
    piece("Entete", 1024, 160, 34, "4FD8FF", "12A4E6", ep=10, levre=10, reflet=0.30)
    piece("Panneau", 1024, 1024, 46, "EEF3F8", "C9D3DF", ep=12, levre=14, bord=0.8, reflet=0)
    fermer()
    # lignes de la fenetre (comme les lignes de la boutique de la reference)
    for nom, a, b in (("LigneVerte", "7CF07A", "22B24C"), ("LigneCyan", "5BE3FF", "1497E0"),
                      ("LigneViolette", "C08CFF", "7A3FE6"), ("LigneRose", "FF8AB0", "E2386E"),
                      ("LigneGrise", "C9D0DA", "8B95A5")):
        piece(nom, 1024, 240, 34, a, b, ep=10, levre=10, reflet=0.25)
    # cartes (memes noms qu'avant : tout l'ecran du PC change de style d'un coup)
    piece("Carte", 512, 1024, 46, "5BE3FF", "1497E0", ep=12, levre=14, reflet=0.18)
    piece("CarteChoisie", 512, 1024, 46, "7CF07A", "22B24C", ep=16, levre=14, reflet=0.18)
    piece("CarteAchetee", 512, 1024, 46, "C08CFF", "7A3FE6", ep=12, levre=14, reflet=0.18)
    piece("CarteGrise", 512, 1024, 46, "C9D0DA", "8B95A5", ep=12, levre=14, reflet=0.12)
    piece("CarteCarree", 512, 512, 46, "5BE3FF", "1497E0", ep=12, levre=12, reflet=0.22)
    piece("CarteCarreeGrise", 512, 512, 46, "C9D0DA", "8B95A5", ep=12, levre=12, reflet=0.15)
    # boutons
    piece("BoutonVert", 512, 256, 56, "7CF07A", "22B24C", ep=12, levre=16, reflet=0.35)
    piece("BoutonCyan", 512, 256, 56, "5BE3FF", "1497E0", ep=12, levre=16, reflet=0.35)
    piece("BoutonGris", 512, 256, 56, "C9D0DA", "8B95A5", ep=12, levre=16, reflet=0.30)
    piece("BoutonChoisi", 512, 256, 56, "C08CFF", "7A3FE6", ep=12, levre=16, reflet=0.35)
    piece("BoutonRouge", 512, 256, 56, "FF5A5F", "D7263D", ep=12, levre=16, reflet=0.35)
    # onglets (actif = vert ; inactif = bleu nuit) et bandeau du prochain vol
    piece("OngletVert", 512, 128, 40, "7CF07A", "22B24C", ep=9, levre=9, reflet=0.35)
    piece("OngletSombre", 512, 128, 40, "3A4A78", "232E52", ep=9, levre=9, reflet=0.22, bord=0.25)
    piece("Bandeau", 1024, 128, 40, "4FD8FF", "12A4E6", ep=9, levre=9, reflet=0.30)


def fleches_rebirth(T):
    """Deux fleches en cercle (rebirth), blanches a gros contour, sur fond transparent (T x T)."""
    import math
    im = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    c, r, ep = T / 2, T * 0.30, T * 0.11
    def fleche(d, a0, a1, coul, trait):
        pts = []
        for i in range(40):
            a = math.radians(a0 + (a1 - a0) * i / 39)
            pts.append((c + r * math.cos(a), c + r * math.sin(a)))
        d.line(pts, fill=coul, width=int(ep + 2 * trait), joint="curve")
        a = math.radians(a1)
        tx, ty = -math.sin(a), math.cos(a)                  # tangente (sens des angles croissants)
        px, py = c + r * math.cos(a), c + r * math.sin(a)
        nx, ny = math.cos(a), math.sin(a)
        L, W = T * 0.17 + trait, T * 0.15 + trait
        d.polygon([(px + tx * L, py + ty * L), (px + nx * W, py + ny * W), (px - nx * W, py - ny * W)], fill=coul)
    for trait, coul in ((int(T * 0.035), CONTOUR), (0, (255, 255, 255, 255))):
        d = ImageDraw.Draw(im)
        fleche(d, 200, 330, coul, trait)
        fleche(d, 20, 150, coul, trait)
    return im


def hud():
    """Les 3 barres du compteur a gauche de l'ecran (Textures/Interface) : pastille ronde avec
    l'icone a gauche, barre cartoon a droite. 1024 x 256 (affichees 288 x 72 dans le jeu)."""
    dossier = os.path.join(RACINE, "Textures", "Interface")
    W, H = 1024, 256
    avion = Image.open(os.path.join(RACINE, "Textures", "JaugeVol", "Avion.png")).convert("RGBA")
    argent = Image.open(os.path.join(KIT, "IconeArgent.png")).convert("RGBA")
    for nom, haut, bas, icone in (("FondArgent", "7CF07A", "22B24C", argent),
                                  ("FondRevenu", "5BE3FF", "1497E0", avion),
                                  ("FondRebirth", "FF8AB0", "E2386E", fleches_rebirth(512))):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        barre = piece("_tmp", W - 120, 176, 44, haut, bas, ep=9, levre=12, reflet=0.30, dossier=dossier)
        im.alpha_composite(barre, (110, 40))
        # pastille : disque blanc bleute a gros contour, reflet, icone dedans
        P = 236
        p = Image.new("RGBA", (P * K, P * K), (0, 0, 0, 0))
        dp = ImageDraw.Draw(p)
        dp.ellipse([0, 0, P * K - 1, P * K - 1], fill=CONTOUR)
        e = 12 * K
        dp.ellipse([e, e, P * K - 1 - e, P * K - 1 - e], fill=hexa(bas))
        dp.ellipse([e + 6 * K, e + 6 * K, P * K - 1 - e - 6 * K, P * K - 1 - e - 14 * K], fill=hexa(haut))
        reflet = Image.new("RGBA", p.size, (0, 0, 0, 0))
        ImageDraw.Draw(reflet).ellipse([e + 40 * K, e + 18 * K, P * K - 1 - e - 40 * K, e + 66 * K], fill=(255, 255, 255, 90))
        p.alpha_composite(reflet)
        p = p.resize((P, P), Image.LANCZOS)
        ic = icone.copy()
        ic.thumbnail((182, 182), Image.LANCZOS)
        p.alpha_composite(ic, ((P - ic.width) // 2, (P - ic.height) // 2 + 2))
        im.alpha_composite(p, (4, 10))
        im.save(os.path.join(dossier, nom + ".png"))
    os.remove(os.path.join(dossier, "_tmp.png"))


def apercu(largeurs, marge):
    """Image de controle : une fenetre comme dans le jeu."""
    W, H = 1100, 820
    im = Image.new("RGBA", (W, H), (40, 70, 60, 255))

    def poser(nom, x, y, l, h, dossier=KIT):
        p = Image.open(os.path.join(dossier, nom + ".png")).convert("RGBA").resize((int(l), int(h)), Image.LANCZOS)
        im.alpha_composite(p, (int(x), int(y)))

    def ecrire(s, x, y, l, h, teinte="FFFFFF", centre=True):
        T = h * 1.30
        w0 = sum((largeurs[c] - 2 * marge + 0.025) if c in largeurs else 0.30 for c in s) + 2 * marge
        T = min(T, l / w0)
        px = x + ((l - w0 * T) / 2 if centre else 0)
        top = y + h / 2 - T / 2
        tt = np.array(hexa(teinte)) / 255
        for c in s:
            if c in largeurs:
                g = Image.open(os.path.join(LETTRES, nom_lettre(c) + ".png")).convert("RGBA")
                g = g.resize((max(1, int(largeurs[c] * T)), int(T)), Image.LANCZOS)
                a = np.asarray(g).astype(float)
                a[..., :3] *= tt[:3]
                im.alpha_composite(Image.fromarray(a.astype(np.uint8)), (int(px), int(top)))
                px += (largeurs[c] - 2 * marge + 0.025) * T
            else:
                px += 0.30 * T

    poser("Panneau", 140, 120, 820, 640)
    poser("Entete", 130, 90, 840, 120)
    poser("IconeSupplies", 150, 70, 130, 130)
    ecrire("FLIGHT OPS", 290, 110, 500, 64)
    poser("Fermer", 870, 80, 100, 100)
    lignes = (("LigneCyan", "DESTINATIONS", "BUY ROUTES AND FLY", "IconeDestinations", "BoutonVert", "OPEN"),
              ("LigneVerte", "SUPPLIES", "FOOD AND DRINKS", "IconeSupplies", "BoutonVert", "OPEN"),
              ("LigneViolette", "UPGRADES", "GROW YOUR PLANE", "IconeUpgrades", "BoutonCyan", "$20K"))
    for i, (fond, t, st, ic, bt, bx) in enumerate(lignes):
        y = 240 + i * 170
        poser(fond, 170, y, 760, 150)
        ecrire(t, 200, y + 22, 330, 50, centre=False)
        ecrire(st, 200, y + 82, 330, 30, "DFF7FF", centre=False)
        poser(ic, 520, y + 10, 130, 130)
        poser(bt, 680, y + 30, 220, 90)
        ecrire(bx, 690, y + 48, 200, 46)
    im.convert("RGB").save(os.path.join(KIT, "..", "..", "Outils", "apercu_interface_cartoon.png"))


if __name__ == "__main__":
    largeurs, marge, espace = police_cartoon()
    ecrire_verse(largeurs, marge, espace)
    kit()
    hud()
    apercu(largeurs, marge)
    print(len(largeurs), "lettres ; marge", round(marge, 4), "espace", round(espace, 4))
