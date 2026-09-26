import * as THREE from './vendor/three.module.js';
export const FULL_CUT={xMin:0,xMax:1,yMin:0,yMax:1,zMin:0,zMax:1};
export function validCut(c){return c==null||Object.keys(FULL_CUT).every(k=>Number.isFinite(c[k])&&c[k]>=0&&c[k]<=1)&&['x','y','z'].every(a=>c[a+'Max']-c[a+'Min']>=.019);}
export function rotateAroundAnchor(object,axis,angle,anchor){object.updateMatrix();const before=anchor.clone().applyMatrix4(object.matrix);object.rotateOnAxis(new THREE.Vector3().setComponent(axis,1),angle);object.updateMatrix();const after=anchor.clone().applyMatrix4(object.matrix);object.position.add(before.sub(after));object.updateMatrixWorld(true);}
// Clip each triangle against six planes, interpolating source UVs, normals and other attributes.
// Cut faces are open; this is a reversible surface crop, not a watertight Boolean solid operation.
export function cropGeometry(source,box){
 const names=Object.keys(source.attributes),attributes=source.attributes,values=Object.fromEntries(names.map(n=>[n,[]]));
 const pos=attributes.position,index=source.index,count=index?index.count:pos.count;
 const planes=[];for(let axis=0;axis<3;axis++){planes.push({axis,limit:box.min.getComponent(axis),sign:1},{axis,limit:box.max.getComponent(axis),sign:-1});}
 const vertex=i=>Object.fromEntries(names.map(n=>{const a=attributes[n];return [n,Array.from({length:a.itemSize},(_,j)=>a.getComponent(i,j))];}));
 const interpolate=(a,b,t)=>Object.fromEntries(names.map(n=>[n,a[n].map((v,i)=>v+(b[n][i]-v)*t)]));
 const out=new THREE.BufferGeometry();let lastMaterial=-1,groupStart=0,vertices=0;
 for(let i=0;i<count;i+=3){let polygon=[0,1,2].map(k=>vertex(index?index.getX(i+k):i+k));
  for(const plane of planes){const next=[];for(let j=0;j<polygon.length;j++){const a=polygon[j],b=polygon[(j+1)%polygon.length],da=plane.sign*(a.position[plane.axis]-plane.limit),db=plane.sign*(b.position[plane.axis]-plane.limit);if(da>=-1e-9)next.push(a);if((da>=0)!==(db>=0))next.push(interpolate(a,b,da/(da-db)));}polygon=next;if(polygon.length<3)break;}
  if(polygon.length<3)continue;const material=source.groups.find(g=>i>=g.start&&i<g.start+g.count)?.materialIndex||0;
  if(material!==lastMaterial){if(vertices>groupStart)out.addGroup(groupStart,vertices-groupStart,lastMaterial);groupStart=vertices;lastMaterial=material;}
  for(let j=1;j<polygon.length-1;j++)for(const v of [polygon[0],polygon[j],polygon[j+1]]){for(const n of names)values[n].push(...v[n]);vertices++;}
 }
 if(vertices>groupStart)out.addGroup(groupStart,vertices-groupStart,lastMaterial);
 for(const n of names)out.setAttribute(n,new THREE.Float32BufferAttribute(values[n],attributes[n].itemSize));
 out.computeBoundingBox();out.computeBoundingSphere();return out;
}
