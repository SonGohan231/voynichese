import * as THREE from './vendor/three.module.js';
export function homeTransform(object){return {p:object.position.toArray(),q:object.quaternion.toArray(),s:object.scale.toArray()};}
export function applyTransform(object,t){object.position.fromArray(t.p);object.quaternion.fromArray(t.q).normalize();object.scale.fromArray(t.s);object.updateMatrixWorld(true);}
export function uniformScale(root,factor){const n=THREE.MathUtils.clamp(root.scale.x*factor,.04,3);root.scale.setScalar(n);return n;}
export function transformMatrix(t){return new THREE.Matrix4().compose(new THREE.Vector3().fromArray(t.p),new THREE.Quaternion().fromArray(t.q).normalize(),new THREE.Vector3().fromArray(t.s));}
// Compare the visible fragment's centre in world metres, even while either hand moves its parent.
export function snapMetrics(piece,home,assembly,anchor=new THREE.Vector3(),threshold=.06,angleLimit=22){
 piece.updateWorldMatrix(true,false);assembly.updateWorldMatrix(true,false);
 const target=assembly.matrixWorld.clone().multiply(transformMatrix(home));
 const currentPoint=anchor.clone().applyMatrix4(piece.matrixWorld),targetPoint=anchor.clone().applyMatrix4(target);
 const p=new THREE.Vector3(),q=new THREE.Quaternion(),s=new THREE.Vector3(),tq=new THREE.Quaternion(),ts=new THREE.Vector3();
 piece.matrixWorld.decompose(p,q,s);target.decompose(p,tq,ts);
 const distance=currentPoint.distanceTo(targetPoint),angle=THREE.MathUtils.radToDeg(q.angleTo(tq));
 const scaleError=Math.max(...s.toArray().map((v,i)=>Math.abs(v/ts.getComponent(i)-1)));
 return {distance,angle,ready:distance<threshold&&angle<angleLimit&&scaleError<.03,target,currentPoint,targetPoint};
}
export function canSnap(piece,home,assembly,threshold=.035){return snapMetrics(piece,home,assembly,new THREE.Vector3(),threshold,14).ready;}
export function canGrab(entry,object,held){return !held.some(h=>h&&(h.object===object||(h.entry===entry&&(h.object===entry.root||object===entry.root))));}
export function joinPiece(entry,piece){entry.cluster.attach(piece);applyTransform(piece,entry.home.get(piece.name));entry.joined.add(piece.name);}
export function detachPiece(entry,piece){entry.origin.attach(piece);entry.joined.delete(piece.name);}
export function pieceRecord(entry,piece){const joined=entry.joined.has(piece.name);return {name:piece.name,joined,transform:relativeTransform(piece,joined?entry.cluster:entry.origin)};}
export function restorePiece(entry,piece,record){const joined=record.joined===true;(joined?entry.cluster:entry.origin).add(piece);applyTransform(piece,record.transform);if(joined)entry.joined.add(piece.name);else entry.joined.delete(piece.name);}
export function validTransform(t){return !!(t&&[['p',3],['q',4],['s',3]].every(([k,n])=>Array.isArray(t[k])&&t[k].length===n&&t[k].every(Number.isFinite))&&Math.hypot(...t.q)>1e-8&&t.s.every(x=>x>0&&x<=100)&&Math.abs(t.s[0]-t.s[1])<1e-5&&Math.abs(t.s[1]-t.s[2])<1e-5);}
export function relativeTransform(object,parent){object.updateWorldMatrix(true,false);parent.updateWorldMatrix(true,false);const matrix=parent.matrixWorld.clone().invert().multiply(object.matrixWorld),p=new THREE.Vector3(),q=new THREE.Quaternion(),s=new THREE.Vector3();matrix.decompose(p,q,s);return {p:p.toArray(),q:q.toArray(),s:s.toArray()};}
