# 25 passagers 3D — Gemini puis Meshy (instructions pour Cowork)

Budget : **900 crédits Meshy**. Un modèle 3D avec texture coûte **30 crédits**. **25 passagers = 750 crédits** ; les **150 crédits restants (5 essais)** servent à refaire les modèles ratés. Aucun crédit n'est dépensé deux fois sans raison.
Uniquement des PASSAGERS (pas de pilote, pas d'hôtesse, pas d'équipage).

Style : celui des 2 images de référence (le gondolier au t-shirt rayé et l'homme barbu à la chemise rouille). C'est un **low-poly stylisé** : formes simples à facettes, ombrage mat comme de l'argile, couleurs unies, visage simple. Tous les personnages doivent être en **posture en T**.

---

## A. Ce que Cowork doit faire, dans l'ordre (pour CHAQUE personnage)

1. **Gemini, l'image**
   - Ouvrir Gemini (génération d'images).
   - Joindre les 2 images de référence et écrire : « Same art style as these 2 reference images ».
   - Coller le **BLOC DE STYLE** (partie B), puis la **description** du personnage (partie C).
   - Vérifier l'image avant de passer à la suite :
     - **posture en T parfaite** : les bras tendus à l'horizontale, à hauteur des épaules ;
     - le **corps entier visible**, du chapeau aux chaussures ;
     - un **fond blanc uni**, sans ombre au sol ;
     - **rien dans les mains**, aucun texte, une seule personne.
   - Si un point manque, régénérer (Gemini ne coûte pas de crédits Meshy).
   - Enregistrer l'image en PNG sous le nom indiqué, par exemple `01_HommeAffaires.png`.

2. **Meshy, la 3D**
   - Ouvrir Meshy : **Image to 3D**, puis importer le PNG.
   - Réglages :
     - **Texture : ACTIVÉE** (générer avec la texture directement) ;
     - **Symétrie : ON** ;
     - **Pose : T-pose** (si l'option existe) ;
     - **Topologie : Triangle** ;
     - **Polycount cible : 10 000**. C'est ce qui « réduit la taille » : modèle léger pour Fortnite.
   - Avant de lancer, vérifier qu'il reste au moins 30 crédits, puis lancer **une seule fois**.
   - Contrôler le résultat :
     - le visage est propre ;
     - il n'y a pas de trou ;
     - les bras sont bien en T ;
     - la texture correspond à l'image.
   - Si le résultat est mauvais, **ne pas relancer tout de suite**. Noter le problème et passer au suivant. Une fois les 25 faits, refaire les ratés avec les 150 crédits restants (5 essais maximum), en commençant par les plus ratés.

3. **Téléchargement et réduction de la taille**
   - Télécharger au format **GLB**, ou **FBX** si on veut le rig plus tard. Si Meshy propose de choisir la taille des textures, prendre **1024 × 1024**.
   - Nommer le fichier comme l'image : `01_HommeAffaires.glb`.
   - Si le fichier fait **plus de 5 Mo**, utiliser **Remesh** dans Meshy avec une cible de 6 000 à 8 000 triangles, puis retélécharger. Remesh ne doit pas refaire la texture.
   - Ranger tous les GLB dans un dossier `Personnages_Meshy`.

4. **Tenir le compte**
   - Après chaque modèle, noter dans un fichier `suivi.txt` :
     - le numéro et le nom ;
     - les crédits restants ;
     - OK ou à refaire.
   - **S'arrêter** quand il reste moins de 30 crédits.

> Optionnel, mais utile pour le jeu : dans Meshy, **Animate / Auto-rig** fonctionne parce que les personnages sont en T. Vérifier d'abord combien de crédits ça coûte, et ne le faire que si on a validé.

---

## B. BLOC DE STYLE (à coller AVANT chaque description, toujours le même)

```
Stylized low-poly 3D character render, same art style as the reference images: faceted simple
shapes, smooth matte clay-like shading, flat solid colors, simple friendly face (small dark eyes,
simple nose, small mouth), slightly elongated realistic proportions. Full body, front view,
perfectly symmetrical, standing in a strict T-pose: both arms straight out horizontally at shoulder
height, palms facing down, fingers together, legs straight, feet slightly apart. Nothing in the
hands, no bag in the hands, no props. Pure white background, soft even studio lighting, no ground
shadow, no text, no logo, centered, the whole body visible from head to shoes, one single person.
```

---

## C. Les 25 passagers (description à coller APRÈS le bloc de style)

### Les 25 passagers

**01_HommeAffaires**
```
A businessman in his forties, short brown hair, navy-blue suit, light-blue shirt, red tie, brown
leather shoes.
```

**02_FemmeAffaires**
```
A businesswoman in her thirties, shoulder-length black hair, light-grey blazer, white blouse, grey
trousers, black loafers.
```

**03_Mamie**
```
An elderly woman, grey hair in a bun, round glasses, beige knitted cardigan, purple blouse, long
navy skirt, comfortable brown shoes.
```

**04_Papy**
```
An elderly man, white hair, grey flat cap, beige sweater vest over a white shirt, brown trousers,
brown shoes.
```

**05_AdoGarcon**
```
A teenage boy, messy blond hair, oversized blue hoodie, black headphones around the neck, grey
jogging pants, white sneakers.
```

**06_AdoFille**
```
A teenage girl, high ponytail, light denim jacket over a white t-shirt, black leggings, pink
sneakers.
```

**07_EnfantGarcon**
```
A boy about 8 years old, short brown hair, green t-shirt with a small airplane print, beige shorts,
red sneakers.
```

**08_EnfantFille**
```
A girl about 8 years old, two pigtails, pink summer dress with white dots,
white socks, purple shoes.
```

**09_Touriste**
```
A cheerful tourist man, sunburnt cheeks, sunglasses pushed up on his head, colorful Hawaiian shirt
with blue and green flowers, khaki shorts, brown sandals.
```

**10_Routard**
```
A backpacker in his twenties, short beard, beanie hat, a big green backpack worn on his back,
olive hiking jacket, cargo pants, brown hiking boots.
```

**11_Millionnaire**
```
A rich VIP man, slicked hair, dark sunglasses, white luxury suit, open black shirt, thin gold
chain necklace, white shoes.
```

**12_Diva**
```
A glamorous VIP woman, wavy auburn hair, big dark sunglasses, elegant emerald-green dress to the
knees, pearl necklace, beige heels.
```

**13_Fraudeur**
```
A suspicious-looking man, fedora hat, dark sunglasses, long beige trench coat with the collar
raised, dark trousers, black shoes.
```

**14_Supporter**
```
A football fan, red and white striped scarf, red football jersey, white cap worn backwards, blue
jeans, white sneakers.
```

**15_Sportif**
```
A muscular gym guy, buzz cut, grey tank top, black jogger pants, bright blue running shoes.
```

**16_Docteur**
```
A doctor on holiday, glasses, short hair, light-blue shirt, white doctor coat worn open, dark
trousers, brown shoes.
```

**17_Rockeur**
```
A rock musician, long black hair, black leather jacket, grey band-style t-shirt without text,
ripped black jeans, black boots.
```

**18_MamieTouriste**
```
A smiling elderly tourist woman, wide straw sun hat with a blue ribbon, floral blue and white
dress, white cardigan, white sandals.
```

**19_Hipster**
```
A hipster man, big brown beard, grey beanie, red and black checked flannel shirt, dark slim jeans,
brown boots.
```

**20_Etudiante**
```
A student girl, round glasses, brown bob haircut, cozy beige sweater, plaid green skirt, black
tights, brown ankle boots.
```

**21_PereFamille**
```
A dad in his forties, short black hair, light stubble, navy polo shirt, beige chino trousers,
white sneakers.
```

**22_Influenceuse**
```
A trendy young influencer, long platinum hair, white bucket hat, cropped lilac jacket, white
t-shirt, wide light-blue jeans, chunky white sneakers.
```

**23_JeuneMaman**
```
A young mother in her late twenties, long brown hair in a loose ponytail, navy and white striped
long-sleeve top, light-blue jeans, white sneakers.
```

**24_Golfeur**
```
A retired man in his sixties, white golf cap, short grey beard, light-green polo shirt, beige
checked trousers, white shoes.
```

**25_Sportive**
```
A sporty young woman, high ponytail, light-blue zip-up sport jacket, black leggings, white and
pink running shoes.
```

---

## D. Notes

- **Pas de jaune vif.** Les couleurs du jeu sont le vert, le bleu, le blanc et l'or discret. Le paille du chapeau et le beige, c'est OK.
- **Rien dans les mains :** Meshy collerait l'objet aux doigts, et le personnage ne pourrait plus s'asseoir proprement.
- **Les vêtements doivent être près du corps** (pas de cape, pas de très longue robe), pour que le personnage puisse s'asseoir dans les sièges.
- Si Gemini met les bras **en A** (en diagonale) au lieu du T, ajouter à la fin : « ARMS MUST BE PERFECTLY HORIZONTAL, 90 DEGREES FROM THE BODY ».
