# Prompt pour Claude Cowork : les prix de toutes les dalles

Copier tout ce qui est dans le bloc ci-dessous et le donner à Claude Cowork.

---

```
Tu es game designer économie pour mon jeu Fortnite (UEFN) "Flight Attendant Tycoon".
Je veux la LISTE COMPLÈTE DES PRIX de tout ce qui s'achète, avec un équilibrage réfléchi.
Livrable : un fichier Excel (.xlsx) + un résumé court en français.

=== LE JEU ===
Je suis hôtesse / steward et propriétaire d'un avion (tycoon). Je fais embarquer des passagers,
je décolle, je sers les commandes (boissons, repas) avec un chariot, j'atterris. Je gagne de l'argent
et je l'investis pour agrandir l'avion. C'est un tycoon classique : je marche sur des DALLES posées
dans l'avion, je paie, et ça fait apparaître des choses (sièges, toilettes...). Quand une dalle est
achetée, la ou les dalles suivantes apparaissent.

=== CE QUI S'ACHÈTE AVEC DES DALLES (presque tout) ===
1. Rangées de sièges : une dalle = une rangée.
2. Toilettes : une dalle = un cabinet de toilettes.
3. "Agrandir l'avion" : une dalle spéciale. Quand on l'achète, on est téléporté dans un avion plus grand,
   et on garde ce qu'on avait (les rangées et toilettes achetées sont déjà là dans le nouvel avion).
4. Plus tard (à prévoir dans le tableau, en fin de chaque avion) : espaces (bar, salon, restaurant,
   cinéma, duty free) et zones de classes (Premium, Business, First, Suites). À toi de les placer.

RÈGLE D'ENCHAÎNEMENT (exemple au début du jeu) :
- Rangée 1 (gratuite) -> fait apparaître la dalle Toilettes 1.
- Toilettes 1 -> fait apparaître la dalle Rangée 2.
- Rangée 2 -> Toilettes 2 -> Rangée 3 -> ... et ainsi de suite.
- Quand l'avion est plein (toutes ses rangées / toilettes) -> dalle "Agrandir l'avion".
Tu peux proposer de mieux répartir les toilettes (ex. 1 toilette toutes les 3 rangées) si c'est plus logique,
mais garde l'idée : on alterne pour que le joueur ait toujours une prochaine dalle pas trop chère.

=== LES AVIONS (on élargit d'abord, puis on monte en étages ; la largeur ne change plus après le 3) ===
Avion 1 : petit A320, 1 siège | allée | 1 siège = 2 sièges par rangée.
Avion 2 : plus large, 2 | 2 = 4 sièges par rangée.
Avion 3 : gros-porteur, 3 | 3 | 3 = 9 sièges par rangée.
Avion 4 : + 2e étage (même largeur 3|3|3 sur les 2 étages).
Avion 5 : + 3e étage.
Avion 6 : + 4e étage.
Avion 7 : le "géant doré" (fin du jeu).
Longueur de la cabine : environ 10 à 12 rangées par étage (tu choisis un nombre et tu l'écris).
Toilettes : 2 dans l'avion 1, puis à toi de proposer combien par avion / par étage.

=== CE QUI RESTE SUR LE PC (pas des dalles, à chiffrer aussi) ===
- Employés (ils font une partie du travail à ma place) : contrôleur de billets (vérifie les billets
  à l'embarquement), agent des coffres (ferme les coffres à bagages), steward du galley (sert avec moi),
  plus tard barman (demande le bar) et chef (demande le restaurant).
- Capacité du galley (stock max de produits).
- Vitesse de déplacement du joueur (plusieurs paliers).
- Rebirth : quand on a le géant doré, on recommence à l'avion 1 avec un multiplicateur permanent
  (x2, puis x3...). Propose la formule.

=== CE QUE LE JEU RAPPORTE (chiffres réels du code) ===
Lignes aériennes (on les achète sur le PC, 8 niveaux de ligne) :
  Niveau de ligne :          1      2      3       4        5         6          7           8
  Prix de la ligne :      2 000  5 000  50 000  400 000  3 000 000  25 000 000  200 000 000  1 500 000 000
  "Valeur" d'un vol V :   1 000  8 000  60 000  500 000  4 000 000  30 000 000  250 000 000  2 000 000 000
  Durée du vol (min) :      5      6      7       8        9         11         13          15
  Multiplicateur service:   1      2      4       8       16         32         64         128

Gains pendant un vol :
  - Chaque passager assis rapporte 0,05 x V sur le vol (ex : ligne 1, 20 passagers = 20 x 50 = 1 000).
  - Missions de la feuille de vol : 0,10 x V chacune (environ 3 à 5 par vol),
    fraudeur attrapé : 0,12 x V, vol parfait : 0,10 x V.
  - Service au chariot : prix d'une unité du produit x 3 x multiplicateur de service x bonus de rapidité
    (x1,5 si servi vite, x1 normal, x0,5 lent). Environ 1 commande pour 5 passagers, jusqu'à 3 commandes par passager.
Produits (boutique SUPPLIES du PC) : lot / prix du lot / prix de déblocage
  Eau 20 / 20 / gratuit ; Soda 20 / 300 / 750 ; Croissant 10 / 1 000 / 6 000 ; Sandwich 10 / 8 000 / 50 000 ;
  Café 10 / 60 000 / 750 000 ; Burger 5 / 250 000 / 8 000 000 ; Homard 2 / 10 000 000 / 1 000 000 000 ;
  Caviar 1 / 60 000 000 / 15 000 000 000.
Un cycle complet (embarquement + vol + atterrissage) dure à peu près la durée du vol + 1 à 2 minutes.
Argent : entier 64 bits, donc AUCUN prix ne doit dépasser 9 000 000 000 000 000 000 (9 Qi).
Abréviations affichées en jeu : K, M, B, T, Qa (10^15), Qi (10^18).

=== CE QUE JE VEUX ===
1. Un tableau ligne par ligne, DANS L'ORDRE où le joueur les achète, avec les colonnes :
   N° | Avion | Type (rangée / toilettes / agrandir / espace / classe) | Nom affiché sur le panneau (anglais, court,
   ex "SEAT ROW 2", "TOILET 1", "BIGGER PLANE") | Prérequis (quelle dalle avant) | Prix (nombre entier) |
   Prix affiché (ex "1.5K") | Sièges total après achat | Gain estimé par vol après achat | Nombre de vols
   pour se le payer | Temps de jeu cumulé estimé.
2. Un 2e onglet pour le PC : employés, capacité du galley, vitesse de déplacement, rebirth.
3. Un 3e onglet "courbe" : temps de jeu cumulé par avion (graphique bienvenu).
4. Objectifs d'équilibrage :
   - Le début doit être rapide et satisfaisant : la 1re rangée gratuite, les premières dalles en 1 à 2 vols.
   - Chaque dalle coûte en général 1 à 4 vols au rythme du joueur à ce moment-là.
   - "Agrandir l'avion" est un gros cap (environ 8 à 15 vols).
   - Les prix doivent rester cohérents avec les lignes aériennes : on doit avoir besoin d'acheter de meilleures
     lignes pour avancer (indique à quel niveau de ligne le joueur devrait être pour chaque avion).
   - Durée visée pour finir le jeu une première fois (avion 7) : environ 15 à 25 heures. Ensuite le rebirth.
   - Prix "ronds" et lisibles (1 500, 25K, 3M...).
5. Écris en français, explique tes hypothèses en quelques lignes au début.
```
