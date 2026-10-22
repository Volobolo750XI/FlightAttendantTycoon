# Onglet UPGRADES du PC — images

## Déjà faites (rien à générer)

23 pictogrammes blancs, dessinés par `Outils/icones_ameliorations.py` (traits blancs épais, fond transparent) :
avions (Avion_01 à Avion_08), espaces (Espace_*), classes (Classe_*), confort (Confort_*), Rebirth.

## À générer : les 6 portraits des employés (onglet STAFF)

Un portrait = un employé qu'on reconnaît **en une fraction de seconde** grâce à sa tenue et à UN objet.

**Règles pour les 6 images** (à coller au début de chaque prompt) :

> Head-and-shoulders portrait of ONE person, facing the camera, friendly smile,
> realistic photo style with soft studio light, plain background that is easy to remove
> (solid light grey), the person centered and filling most of the square image,
> the job must be obvious at a glance from the outfit and the one object,
> no text, no logo, no other people, square image 1024 x 1024.

| Fichier | Prompt (après le bloc de règles) |
|---|---|
| `Equipe_Hotesse.png` | A female flight attendant in a navy blue airline uniform with a small red neck scarf and a small navy hat. |
| `Equipe_Barman.png` | A male bartender in a white shirt, black vest and black bow tie, holding a silver cocktail shaker next to his shoulder. |
| `Equipe_Majordome.png` | An elderly male butler in a black tailcoat with white gloves, holding a small silver tray with one glass of champagne. |
| `Equipe_Chef.png` | A chef in a white chef jacket and a tall white chef hat (toque), holding a wooden spoon. |
| `Equipe_Masseur.png` | A massage therapist in a white spa tunic, with a rolled white towel on the shoulder. |
| `Equipe_MaitreNageur.png` | A lifeguard in a red lifeguard t-shirt with a whistle around the neck and a red rescue float on the shoulder. |

## Après la génération

1. Détourer le fond (fond transparent) et redimensionner en 512 x 512.
2. Mettre les 6 PNG dans le dépôt : `Textures/Ameliorations/`.
3. Dans UEFN : créer le dossier **Ameliorations** dans le Tiroir à contenu et importer les **29 images**
   (23 pictogrammes + 6 portraits). Les noms doivent être exactement les mêmes : le Verse les appelle
   `Ameliorations.Avion_02`, `Ameliorations.Equipe_Barman`, etc.
