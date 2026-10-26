# 30 personnages 3D — Gemini puis Meshy (instructions pour Cowork)

Budget : **900 crédits Meshy**. Un modèle 3D avec texture coûte **30 crédits**, donc **30 modèles au maximum**. Aucun crédit n'est dépensé deux fois.

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
   - Enregistrer l'image en PNG sous le nom indiqué, par exemple `01_Hotesse.png`.

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
   - Si le résultat est mauvais, **ne pas relancer tout de suite**. Noter le problème et passer au suivant : on décidera ensemble (chaque essai coûte 30 crédits).

3. **Téléchargement et réduction de la taille**
   - Télécharger au format **GLB**, ou **FBX** si on veut le rig plus tard. Si Meshy propose de choisir la taille des textures, prendre **1024 × 1024**.
   - Nommer le fichier comme l'image : `01_Hotesse.glb`.
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

## C. Les 30 personnages (description à coller APRÈS le bloc de style)

### L'équipe de l'avion (8)

**01_Hotesse**
```
A young female flight attendant, hair in a neat bun, small emerald-green pillbox hat, fitted
emerald-green uniform jacket with gold buttons, green pencil skirt to the knee, white silk neck
scarf with a thin gold stripe, black low heels.
```

**02_Steward**
```
A young male flight attendant, short tidy dark hair, white shirt with rolled cuffs, emerald-green
waistcoat with gold buttons, green tie, dark navy trousers, black shoes.
```

**03_Commandant**
```
An airline captain in his fifties, short grey hair, neat grey moustache, navy-blue pilot uniform
jacket with four gold stripes on the sleeves, gold wings badge, white shirt, black tie, navy pilot
cap with gold badge, black shoes.
```

**04_Copilote**
```
A female airline first officer in her thirties, long brown hair in a low ponytail, navy-blue pilot
uniform jacket with three gold stripes on the sleeves, white shirt, navy tie, navy trousers, navy
pilot cap, black shoes.
```

**05_AgentBillets**
```
A ticket agent, young man with curly hair, emerald-green blazer, white shirt, a green lanyard with
a white badge around the neck, grey trousers, white sneakers.
```

**06_Barman**
```
A barman, slicked-back black hair, small beard, crisp white shirt with sleeves rolled up, black
waistcoat, black bow tie, black trousers, black shoes.
```

**07_Chef**
```
A chef, friendly round face, white double-breasted chef jacket, tall white chef hat, black-and-white
checked trousers, long white apron, black kitchen clogs.
```

**08_AgentEntretien**
```
A cabin cleaner, middle-aged woman with short hair, grey work coveralls with emerald-green trim and
a green cap, grey sneakers.
```

### Les passagers (22)

**09_HommeAffaires**
```
A businessman in his forties, short brown hair, navy-blue suit, light-blue shirt, red tie, brown
leather shoes.
```

**10_FemmeAffaires**
```
A businesswoman in her thirties, shoulder-length black hair, light-grey blazer, white blouse, grey
trousers, black loafers.
```

**11_Mamie**
```
An elderly woman, grey hair in a bun, round glasses, beige knitted cardigan, purple blouse, long
navy skirt, comfortable brown shoes.
```

**12_Papy**
```
An elderly man, white hair, grey flat cap, beige sweater vest over a white shirt, brown trousers,
brown shoes.
```

**13_AdoGarcon**
```
A teenage boy, messy blond hair, oversized blue hoodie, black headphones around the neck, grey
jogging pants, white sneakers.
```

**14_AdoFille**
```
A teenage girl, high ponytail, light denim jacket over a white t-shirt, black leggings, pink
sneakers.
```

**15_EnfantGarcon**
```
A boy about 8 years old, short brown hair, green t-shirt with a small airplane print, beige shorts,
red sneakers.
```

**16_EnfantFille**
```
A girl about 8 years old, two pigtails, pink summer dress with white dots,
white socks, purple shoes.
```

**17_Touriste**
```
A cheerful tourist man, sunburnt cheeks, sunglasses pushed up on his head, colorful Hawaiian shirt
with blue and green flowers, khaki shorts, brown sandals.
```

**18_Routard**
```
A backpacker in his twenties, short beard, beanie hat, a big green backpack worn on his back,
olive hiking jacket, cargo pants, brown hiking boots.
```

**19_Millionnaire**
```
A rich VIP man, slicked hair, dark sunglasses, white luxury suit, open black shirt, thin gold
chain necklace, white shoes.
```

**20_Diva**
```
A glamorous VIP woman, wavy auburn hair, big dark sunglasses, elegant emerald-green dress to the
knees, pearl necklace, beige heels.
```

**21_Fraudeur**
```
A suspicious-looking man, fedora hat, dark sunglasses, long beige trench coat with the collar
raised, dark trousers, black shoes.
```

**22_Supporter**
```
A football fan, red and white striped scarf, red football jersey, white cap worn backwards, blue
jeans, white sneakers.
```

**23_Sportif**
```
A muscular gym guy, buzz cut, grey tank top, black jogger pants, bright blue running shoes.
```

**24_Docteur**
```
A doctor on holiday, glasses, short hair, light-blue shirt, white doctor coat worn open, dark
trousers, brown shoes.
```

**25_Rockeur**
```
A rock musician, long black hair, black leather jacket, grey band-style t-shirt without text,
ripped black jeans, black boots.
```

**26_MamieTouriste**
```
A smiling elderly tourist woman, wide straw sun hat with a blue ribbon, floral blue and white
dress, white cardigan, white sandals.
```

**27_Hipster**
```
A hipster man, big brown beard, grey beanie, red and black checked flannel shirt, dark slim jeans,
brown boots.
```

**28_Etudiante**
```
A student girl, round glasses, brown bob haircut, cozy beige sweater, plaid green skirt, black
tights, brown ankle boots.
```

**29_PereFamille**
```
A dad in his forties, short black hair, light stubble, navy polo shirt, beige chino trousers,
white sneakers.
```

**30_Influenceuse**
```
A trendy young influencer, long platinum hair, white bucket hat, cropped lilac jacket, white
t-shirt, wide light-blue jeans, chunky white sneakers.
```

---

## D. Notes

- **Pas de jaune vif.** Les couleurs du jeu sont le vert, le bleu, le blanc et l'or discret. Le paille du chapeau et le beige, c'est OK.
- **Rien dans les mains :** Meshy collerait l'objet aux doigts, et le personnage ne pourrait plus s'asseoir proprement.
- **Les vêtements doivent être près du corps** (pas de cape, pas de très longue robe), pour que le personnage puisse s'asseoir dans les sièges.
- Si Gemini met les bras **en A** (en diagonale) au lieu du T, ajouter à la fin : « ARMS MUST BE PERFECTLY HORIZONTAL, 90 DEGREES FROM THE BODY ».
