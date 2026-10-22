# Icônes de l'onglet UPGRADES du PC — prompts

24 images à générer (Gemini ou autre), puis à détourer.

## Règles pour toutes les images

- **Format** : PNG carré 512 x 512, **fond transparent** (si l'outil ne sait pas, fond blanc uni, on détoure après).
- **Nom du fichier** : exactement celui indiqué (ex. `Avion_02.png`), tous dans un dossier `Ameliorations`.
- **Même style que les icônes existantes du PC** (le globe, le chariot de snacks, la clé avec la flèche verte) :
  coller ce bloc de style au début de CHAQUE prompt :

> **STYLE** : flat cartoon sticker icon, thick dark navy blue outline (#1E2A5A) around every shape,
> bright saturated flat colors with one soft lighter highlight and one soft darker shade per shape,
> clean simple shapes, slightly chunky and cute proportions, mobile game UI icon,
> centered, the object fills about 85% of the canvas, no background, transparent background,
> no shadow on the ground, no frame, no border, no text unless written below.

- Le texte écrit dans l'image (quand il y en a) : **gros, en blanc avec contour bleu nuit, 1 à 3 caractères max**.

---

## AVION (10 images) — dossier `Ameliorations`

| Fichier | Prompt (après le bloc STYLE) |
|---|---|
| `Avion_01.png` | A small white commercial airliner (A320 style) seen from a 3/4 front side view, two engines under the wings, blue windows, friendly look. |
| `Avion_02.png` | Front cross-section cut of an airplane cabin, round fuselage shape, showing three blocks of blue passenger seats side by side (2 seats, 2 seats, 2 seats) with two aisles between them, a small green "+" badge in the top right corner. |
| `Avion_03.png` | A long white airliner seen from the side, stretched longer than normal, with two big green double-headed arrows above it pointing left and right to show it got longer. |
| `Avion_04.png` | A huge wide-body jumbo jet seen from the front, very wide round fuselage, four big engines under wide wings, white and light blue. |
| `Avion_05.png` | A cartoon airplane interior staircase going up (spiral or straight stairs with a handrail), blue carpet on the steps, and a round green sign on the wall with the text "2F". |
| `Avion_06.png` | A modern elevator with sliding silver doors half open, inside an airplane (curved ceiling), and a button panel next to it with a big glowing green button showing the text "3F". |
| `Avion_07.png` | A luxury airplane lounge bar: a curved bar counter in dark wood and gold, a tall cocktail glass with a lime and a straw on top, a round airplane window behind it. |
| `Avion_08.png` | An indoor swimming pool inside an airplane: turquoise water with small waves, a pool ladder, a pink inflatable ring floating, round airplane windows on the curved wall behind. |
| `Avion_09.png` | A colossal airplane seen from the front with SIX big engines (three under each wing), very wide fuselage with many rows of windows on several floors, looks enormous and powerful. |
| `Avion_10.png` | The biggest airplane in the world, fully GOLDEN with shiny sparkles, a small golden crown on top of the fuselage, many floors of windows, six engines, epic and over the top. |

## CLASSES (4 images)

| Fichier | Prompt (après le bloc STYLE) |
|---|---|
| `Classe_Premium.png` | One comfy airplane seat in dark blue with a light blue headrest cover, extra legroom shown by a small footrest, a small green "+" badge. |
| `Classe_Business.png` | A business class lie-flat airplane seat fully reclined like a bed, grey and navy, with a small side table holding a glass of orange juice, a reading lamp. |
| `Classe_First.png` | A first class private suite in an airplane: a wide leather seat inside a box with a half-open sliding door, warm beige and gold colors, a small TV screen. |
| `Classe_Suite.png` | A royal airplane bedroom suite: a big double bed with white and gold sheets, a golden headboard with a small crown ornament, a round airplane window above the bed. |

## CONFORT (4 images)

| Fichier | Prompt (après le bloc STYLE) |
|---|---|
| `Confort_Ecrans.png` | The back of an airplane seat with a seatback touchscreen showing a cute movie play button, a pair of headphones hanging next to it. |
| `Confort_Wifi.png` | A big Wi-Fi symbol (three curved bars and a dot) in bright green, with a small white airplane flying through it. |
| `Confort_Couvertures.png` | A folded fluffy blue blanket with a white pillow on top, a small sleeping mask on the pillow. |
| `Confort_Massage.png` | A luxury massage chair in purple and gold with small motion lines showing it vibrates, and two small sparkles. |

## ÉQUIPE (4 images)

| Fichier | Prompt (après le bloc STYLE) |
|---|---|
| `Equipe_Hotesse.png` | A smiling female flight attendant bust (head and shoulders), navy uniform with a small red scarf, a small hat, friendly cartoon face. |
| `Equipe_Chef.png` | A tall white chef hat (toque) with a silver cooking pan and a wooden spatula crossed in front of it. |
| `Equipe_Hotesse2.png` | Two smiling flight attendants side by side (one female, one male), navy uniforms, with a green badge showing the text "x2". |
| `Equipe_Complete.png` | A full airplane crew group of five people (a pilot with a captain hat in the middle, flight attendants around), all smiling, navy uniforms, a small golden star above them. |

## REBIRTH (1 image)

| Fichier | Prompt (après le bloc STYLE) |
|---|---|
| `Rebirth.png` | A golden circular arrow (circle of two arrows chasing each other, like a refresh symbol) around a small white airplane in the center, purple and gold glow sparkles. |

## Bonus (1 image) : carte verrouillée "bientôt"

| Fichier | Prompt (après le bloc STYLE) |
|---|---|
| `Bientot.png` | A big silver padlock closed, with a small round clock badge in the bottom right corner. |

---

## Après la génération

1. Détourer (fond transparent) et redimensionner en 512 x 512.
2. Mettre les 24 PNG dans le dépôt : `Textures/Ameliorations/`.
3. Dans UEFN : créer le dossier **Ameliorations** dans le Tiroir à contenu et y importer les 24 images
   (les noms doivent être exactement les mêmes, le Verse les appelle `Ameliorations.Avion_02`, etc.).
