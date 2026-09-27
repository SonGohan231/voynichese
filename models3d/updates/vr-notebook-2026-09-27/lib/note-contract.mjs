export const ID=/^[a-f0-9-]{36}$/i;
export const MAX_AUDIO=12*1024*1024, MAX_IMAGE=2*1024*1024, MAX_META=1500000;
export function validContext(c){
 if(!c||typeof c!=='object'||Array.isArray(c))return false;
 const finite=a=>Array.isArray(a)&&a.every(Number.isFinite);
 if(c.pose&&(!finite(c.pose.position)||c.pose.position.length!==3||!finite(c.pose.quaternion)||c.pose.quaternion.length!==4))return false;
 if(!Array.isArray(c.sources)||c.sources.length>120)return false;
 if(!c.sources.every(s=>typeof s.scan==='string'&&/^s\d{4}$/.test(s.scan)&&typeof s.folio==='string'&&s.folio.length<70))return false;
 if(c.strokes&&(!Array.isArray(c.strokes)||c.strokes.length>200||!c.strokes.every(s=>Array.isArray(s.points)&&s.points.length<=6000&&s.points.every(p=>finite(p)&&p.length===3))))return false;
 return JSON.stringify(c).length<=MAX_META;
}
export const noteSchema={type:'object',additionalProperties:false,properties:{
 title:{type:'string'},summary:{type:'string'},category:{type:'string'},tags:{type:'array',items:{type:'string'}},
 observations:{type:'array',items:{type:'string'}},hypotheses:{type:'array',items:{type:'string'}},
 tests:{type:'array',items:{type:'string'}},links:{type:'array',items:{type:'object',additionalProperties:false,properties:{id:{type:'string'},reason:{type:'string'},confidence:{type:'string',enum:['low','medium','high']}},required:['id','reason','confidence']}}
},required:['title','summary','category','tags','observations','hypotheses','tests','links']};
export function validAnalysis(n,allowed){return n&&typeof n.title==='string'&&typeof n.summary==='string'&&typeof n.category==='string'&&['tags','observations','hypotheses','tests'].every(k=>Array.isArray(n[k])&&n[k].every(x=>typeof x==='string'))&&Array.isArray(n.links)&&n.links.every(x=>allowed.has(x.id)&&typeof x.reason==='string'&&['low','medium','high'].includes(x.confidence));}
export function cosine(a,b){if(!Array.isArray(a)||!Array.isArray(b)||a.length!==b.length)return 0;let dot=0,aa=0,bb=0;for(let i=0;i<a.length;i++){dot+=a[i]*b[i];aa+=a[i]**2;bb+=b[i]**2;}return aa&&bb?dot/Math.sqrt(aa*bb):0;}
export function rankNotes(rows,vector){return rows.map(n=>({...n,similarity:cosine(vector,JSON.parse(n.embedding||'[]'))})).sort((a,b)=>b.similarity-a.similarity).slice(0,24);}
