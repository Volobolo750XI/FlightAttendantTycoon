# Image du panneau MUSIC ON/OFF du lobby (fond transparent) : Textures/Lobby/Panneau_Music.png
# Usage (depuis la racine du depot) : python3 Outils/panneau_musique.py
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
K=2; W,H=1024*K,1024*K
POL='Outils/TitanOne-Regular.ttf'
C=(22,27,48,255)
im=Image.new('RGBA',(W,H),(0,0,0,0))
def dilate(m, r):
    b=m.filter(ImageFilter.GaussianBlur(r*0.55))
    return b.point(lambda v: 255 if v>10 else int(v*255/10))
def degrade(haut,bas):
    g=np.linspace(0,1,H)[:,None,None]
    c=np.array(haut)*(1-g)+np.array(bas)*g
    return Image.fromarray(np.repeat(c,W,1).astype(np.uint8)).convert('RGBA')
def poser(masque, haut, bas, trait, ombre=12):
    mc=dilate(masque, trait*K)
    im.paste(Image.new('RGBA',(W,H),C),(0,ombre*K),mc)
    im.paste(Image.new('RGBA',(W,H),C),(0,0),mc)
    im.paste(degrade(haut,bas),(0,0),masque)
def texte(t,xy,taille):
    m=Image.new('L',(W,H),0); ImageDraw.Draw(m).text((xy[0]*K,xy[1]*K),t,font=ImageFont.truetype(POL,taille*K),fill=255,anchor='mm'); return m
m=Image.new('L',(W,H),0)
tete=Image.new('L',(W,H),0); ImageDraw.Draw(tete).ellipse([360*K,300*K,520*K,410*K],fill=255)
tete=tete.rotate(22,center=(440*K,355*K),resample=Image.BICUBIC)
m=ImageChops.lighter(m,tete); d=ImageDraw.Draw(m)
d.rectangle([482*K,60*K,532*K,352*K],fill=255)
d.polygon([(532*K,60*K),(532*K,150*K),(640*K,225*K),(668*K,290*K),(660*K,200*K),(600*K,130*K)],fill=255)
poser(m,(78,82,100),(18,20,30),13,10)
r=Image.new('L',(W,H),0); ImageDraw.Draw(r).ellipse([385*K,312*K,450*K,340*K],fill=110); ImageDraw.Draw(r).rectangle([492*K,80*K,502*K,300*K],fill=90)
im.paste(Image.new('RGBA',(W,H),(255,255,255,255)),(0,0),ImageChops.multiply(r.filter(ImageFilter.GaussianBlur(4*K)),m))
poser(texte('MUSIC',(512,560),230),(255,255,255),(196,204,218),16)
poser(texte('ON',(262,800),190),(120,250,110),(20,170,60),16)
poser(texte('/',(445,800),190),(255,255,255),(200,206,220),16)
poser(texte('OFF',(690,800),190),(255,100,100),(215,30,45),16)
im=im.resize((1024,1024),Image.LANCZOS)
im.save('Textures/Lobby/Panneau_Music.png')
print('ok')
