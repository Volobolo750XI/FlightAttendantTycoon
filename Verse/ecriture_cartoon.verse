using { /Verse.org/Colors }
using { /Verse.org/Assets }
using { /UnrealEngine.com/Temporary/SpatialMath }
using { /UnrealEngine.com/Temporary/UI }

# Flight Attendant Tycoon - le TEXTE CARTOON de toutes les interfaces.
# FICHIER GENERE par Outils/interface_cartoon.py : ne pas modifier a la main.
#
# Chaque lettre est une image du dossier TexteCartoon (lettre blanche tres epaisse, gros contour sombre).
# Ecrire() les pose cote a cote, de la couleur voulue (teinte), centre / a gauche / a droite dans une
# boite. Si le texte est trop long pour la boite, il est reduit pour rentrer.
# Les positions sont celles d'un ecran 1920 x 1080 (X, Y = coin haut gauche de la boite).
# Dans le Tiroir a contenu : importer le dossier Textures/TexteCartoon (a la racine, comme InterfacePC).

ecriture_cartoon := class:
    Glyphes:[char]texture = map{
            'A' => TexteCartoon.L_A,
            'B' => TexteCartoon.L_B,
            'C' => TexteCartoon.L_C,
            'D' => TexteCartoon.L_D,
            'E' => TexteCartoon.L_E,
            'F' => TexteCartoon.L_F,
            'G' => TexteCartoon.L_G,
            'H' => TexteCartoon.L_H,
            'I' => TexteCartoon.L_I,
            'J' => TexteCartoon.L_J,
            'K' => TexteCartoon.L_K,
            'L' => TexteCartoon.L_L,
            'M' => TexteCartoon.L_M,
            'N' => TexteCartoon.L_N,
            'O' => TexteCartoon.L_O,
            'P' => TexteCartoon.L_P,
            'Q' => TexteCartoon.L_Q,
            'R' => TexteCartoon.L_R,
            'S' => TexteCartoon.L_S,
            'T' => TexteCartoon.L_T,
            'U' => TexteCartoon.L_U,
            'V' => TexteCartoon.L_V,
            'W' => TexteCartoon.L_W,
            'X' => TexteCartoon.L_X,
            'Y' => TexteCartoon.L_Y,
            'Z' => TexteCartoon.L_Z,
            'a' => TexteCartoon.L_a_min,
            'b' => TexteCartoon.L_b_min,
            'c' => TexteCartoon.L_c_min,
            'd' => TexteCartoon.L_d_min,
            'e' => TexteCartoon.L_e_min,
            'f' => TexteCartoon.L_f_min,
            'g' => TexteCartoon.L_g_min,
            'h' => TexteCartoon.L_h_min,
            'i' => TexteCartoon.L_i_min,
            'j' => TexteCartoon.L_j_min,
            'k' => TexteCartoon.L_k_min,
            'l' => TexteCartoon.L_l_min,
            'm' => TexteCartoon.L_m_min,
            'n' => TexteCartoon.L_n_min,
            'o' => TexteCartoon.L_o_min,
            'p' => TexteCartoon.L_p_min,
            'q' => TexteCartoon.L_q_min,
            'r' => TexteCartoon.L_r_min,
            's' => TexteCartoon.L_s_min,
            't' => TexteCartoon.L_t_min,
            'u' => TexteCartoon.L_u_min,
            'v' => TexteCartoon.L_v_min,
            'w' => TexteCartoon.L_w_min,
            'x' => TexteCartoon.L_x_min,
            'y' => TexteCartoon.L_y_min,
            'z' => TexteCartoon.L_z_min,
            '0' => TexteCartoon.L_0,
            '1' => TexteCartoon.L_1,
            '2' => TexteCartoon.L_2,
            '3' => TexteCartoon.L_3,
            '4' => TexteCartoon.L_4,
            '5' => TexteCartoon.L_5,
            '6' => TexteCartoon.L_6,
            '7' => TexteCartoon.L_7,
            '8' => TexteCartoon.L_8,
            '9' => TexteCartoon.L_9,
            '$' => TexteCartoon.L_Dollar,
            '.' => TexteCartoon.L_Point,
            ',' => TexteCartoon.L_Virgule,
            ':' => TexteCartoon.L_DeuxPoints,
            '-' => TexteCartoon.L_Tiret,
            '+' => TexteCartoon.L_Plus,
            '/' => TexteCartoon.L_Slash,
            '%' => TexteCartoon.L_Pourcent,
            '!' => TexteCartoon.L_Exclamation,
            '?' => TexteCartoon.L_Question,
            '(' => TexteCartoon.L_ParentheseG,
            ')' => TexteCartoon.L_ParentheseD,
            '|' => TexteCartoon.L_Barre,
            '#' => TexteCartoon.L_Diese,
            '<' => TexteCartoon.L_Inferieur,
            '>' => TexteCartoon.L_Superieur,
            '=' => TexteCartoon.L_Egal,
            '*' => TexteCartoon.L_Etoile}

    # largeur de chaque image de lettre, divisee par sa hauteur
    Largeurs:[char]float = map{
            'A' => 0.7500,
            'B' => 0.7266,
            'C' => 0.6875,
            'D' => 0.7500,
            'E' => 0.6562,
            'F' => 0.6406,
            'G' => 0.7031,
            'H' => 0.7422,
            'I' => 0.4766,
            'J' => 0.5156,
            'K' => 0.7266,
            'L' => 0.6094,
            'M' => 0.8516,
            'N' => 0.7500,
            'O' => 0.7656,
            'P' => 0.7266,
            'Q' => 0.7578,
            'R' => 0.7344,
            'S' => 0.6875,
            'T' => 0.6875,
            'U' => 0.7422,
            'V' => 0.7422,
            'W' => 0.9531,
            'X' => 0.7344,
            'Y' => 0.7188,
            'Z' => 0.6719,
            'a' => 0.6953,
            'b' => 0.7031,
            'c' => 0.6172,
            'd' => 0.6953,
            'e' => 0.6797,
            'f' => 0.6250,
            'g' => 0.6953,
            'h' => 0.6953,
            'i' => 0.4688,
            'j' => 0.5078,
            'k' => 0.6797,
            'l' => 0.4688,
            'm' => 0.9219,
            'n' => 0.7031,
            'o' => 0.7109,
            'p' => 0.6953,
            'q' => 0.6953,
            'r' => 0.6406,
            's' => 0.6562,
            't' => 0.5625,
            'u' => 0.7031,
            'v' => 0.7031,
            'w' => 0.9219,
            'x' => 0.7031,
            'y' => 0.6953,
            'z' => 0.6328,
            '0' => 0.7422,
            '1' => 0.5469,
            '2' => 0.6562,
            '3' => 0.6562,
            '4' => 0.6641,
            '5' => 0.6562,
            '6' => 0.6953,
            '7' => 0.6094,
            '8' => 0.6953,
            '9' => 0.6953,
            '$' => 0.6953,
            '.' => 0.4297,
            ',' => 0.4297,
            ':' => 0.4297,
            '-' => 0.6172,
            '+' => 0.6172,
            '/' => 0.5156,
            '%' => 0.9219,
            '!' => 0.4609,
            '?' => 0.6484,
            '(' => 0.5469,
            ')' => 0.5469,
            '|' => 0.4219,
            '#' => 0.8047,
            '<' => 0.4844,
            '>' => 0.4844,
            '=' => 0.6172,
            '*' => 0.6250}

    # bord transparent a gauche et a droite de chaque image (contour compris), divise par la hauteur
    Marge:float = 0.1094
    # largeur d'un espace, divisee par la hauteur
    Espace:float = 0.1617
    # hauteur de l'image d'une lettre par rapport a la hauteur de la boite
    Agrandir:float = 1.30

    # Largeur du texte pour une hauteur d'image de 1.
    Mesure(S:string):float =
        var W:float = 0.0
        for (C : S):
            if (R := Largeurs[C]):
                set W += R - 2.0 * Marge
            else:
                set W += Espace
        W + 2.0 * Marge

    Ecrire(S:string, Hex:string, J:text_justification, X:float, Y:float, L:float, H:float, Couche:type{_X:int where 0 <= _X, _X <= 2147483647}):[]canvas_slot =
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
        var Slots:[]canvas_slot = array{}
        for (C : S):
            if (Img := Glyphes[C], R := Largeurs[C]):
                set Slots += array{Lettre(Img, Teinte, PX, Haut, R * T, T, Couche)}
                set PX += (R - 2.0 * Marge) * T
            else:
                set PX += Espace * T
        Slots

    Lettre(Img:texture, Teinte:color, X:float, Y:float, L:float, H:float, Couche:type{_X:int where 0 <= _X, _X <= 2147483647}):canvas_slot =
        canvas_slot:
            Anchors := anchors{Minimum := vector2{X := 0.5, Y := 0.5}, Maximum := vector2{X := 0.5, Y := 0.5}}
            Alignment := vector2{X := 0.0, Y := 0.0}
            Offsets := margin{Left := X - 960.0, Top := Y - 540.0, Right := L, Bottom := H}
            SizeToContent := false
            ZOrder := Couche
            Widget := texture_block{DefaultImage := Img, DefaultTint := Teinte, DefaultDesiredSize := vector2{X := L, Y := H}}
