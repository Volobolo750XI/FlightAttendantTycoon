import sys, numpy as np, trimesh
from PIL import Image
from trimesh.ray.ray_pyembree import RayMeshIntersector
sc=trimesh.load(sys.argv[1],force='scene'); out=sys.argv[2]
cam=np.array([float(v) for v in sys.argv[3].split(',')]); cible=np.array([float(v) for v in sys.argv[4].split(',')])
ms=[]
for node in sc.graph.nodes_geometry:
    T,g=sc.graph[node]; m=sc.geometry[g].copy(); m.apply_transform(T)
    c=np.array([180,180,190.]); tex=None; mat=getattr(m.visual,'material',None)
    if mat is not None and getattr(mat,'baseColorTexture',None) is not None:
        tex=np.asarray(mat.baseColorTexture.convert('RGB')).astype(float); c=tex.reshape(-1,3).mean(0)
    elif mat is not None and getattr(mat,'baseColorFactor',None) is not None: c=np.array(mat.baseColorFactor[:3],float)
    uv=getattr(m.visual,'uv',None) if tex is not None else None
    ms.append((m,c,tex,uv))
allm=trimesh.util.concatenate([trimesh.Trimesh(m.vertices,m.faces,process=False) for m,_,_,_ in ms])
owner=np.concatenate([np.full(len(m.faces),i) for i,(m,_,_,_) in enumerate(ms)])
off=np.concatenate([[0],np.cumsum([len(m.faces) for m,_,_,_ in ms])])
W,H,fo=1000,560,500
fwd=cible-cam; fwd/=np.linalg.norm(fwd); r=np.cross(fwd,[0,1,0]); r/=np.linalg.norm(r); up=np.cross(r,fwd)
u,v=np.meshgrid(np.arange(W)-W/2,H/2-np.arange(H))
d=fwd*fo+u.reshape(-1,1)*r+v.reshape(-1,1)*up; d/=np.linalg.norm(d,axis=1,keepdims=True)
tri,ray,loc=RayMeshIntersector(allm).intersects_id(np.tile(cam,(len(d),1)),d,multiple_hits=False,return_locations=True)
img=np.zeros((len(d),3))+[255,0,255]
for k in range(len(tri)):
    t=tri[k]; i=owner[t]; m,c,tex,uv=ms[i]; f=m.faces[t-off[i]]; col=c
    if uv is not None:
        bc=trimesh.triangles.points_to_barycentric(m.vertices[f][None],loc[k][None])[0]
        q=(uv[f]*bc[:,None]).sum(0); h,w=tex.shape[:2]
        col=tex[int((1-q[1]%1)*(h-1)),int((q[0]%1)*(w-1))]
    n=allm.face_normals[t]; img[ray[k]]=col*(0.35+0.65*abs(n@d[ray[k]]))
Image.fromarray(img.reshape(H,W,3).clip(0,255).astype(np.uint8)).save(out)
