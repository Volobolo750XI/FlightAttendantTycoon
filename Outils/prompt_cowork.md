Tu travailles pour mon jeu Fortnite (UEFN) "Flight Attendant Tycoon". J'ai besoin de 20 images de villes pour les fiches de destinations.

Dans le dossier que je t'ai donné, il y a le fichier "prompts_gemini.md". Il contient 20 consignes : une par ville, chacune sous un titre comme "## 1. Paris.png".

Ce que tu dois faire :

1. Avec Claude in Chrome, ouvre gemini.google.com (je suis déjà connecté à mon compte Google). Utilise la création d'images.
2. Pour chaque ville du fichier, une à la fois :
   - ouvre une nouvelle discussion Gemini ;
   - colle la consigne de la ville telle quelle et demande un format paysage (16:9 si Gemini propose un choix) ;
   - télécharge l'image générée.
3. Note chaque image de 1 à 10, en étant exigeant, selon ces critères :
   - rendu 3D réaliste, comme un jeu vidéo moderne (Unreal Engine 5) : ni une photo, ni un dessin ;
   - monument de la ville bien reconnaissable et bien placé au centre ;
   - lumière et couleurs belles ;
   - aucun texte, aucune lettre, aucun logo, aucun filigrane ;
   - aucun défaut visible : bâtiments déformés, objets fondus, doublons bizarres.
   Si la note ne dépasse pas 9,5, recommence la génération. Corrige la consigne si besoin, par exemple en ajoutant "no text" ou "landmark more visible". Continue jusqu'à dépasser 9,5, avec au maximum 5 essais par ville. Après 5 essais, garde la meilleure image.
4. Recadre chaque image gardée au format 2:1, puis redimensionne-la en 1024 x 512 pixels :
   - si l'image est trop haute, coupe surtout le ciel en haut ;
   - le monument doit rester entier.
5. Enregistre les images en PNG dans un dossier "Villes", avec exactement ces noms :
   Paris, London, Rome, Madrid, Istanbul, Cairo, NewYork, Dubai, Rio, MexicoCity, LosAngeles, Delhi, Singapore, Tokyo, Sydney, BoraBora, Bangkok, HongKong, Seoul, Vancouver (.png)
6. À la fin :
   - fais une planche d'aperçu "apercu_villes.png" avec les 20 images en petit, chacune avec son nom ;
   - donne-moi un tableau avec chaque ville, sa note finale et le nombre d'essais.

Important : ne change rien d'autre dans mon dossier. Si Gemini bloque (limite atteinte, connexion demandée), arrête-toi et dis-moi exactement où tu en es.
