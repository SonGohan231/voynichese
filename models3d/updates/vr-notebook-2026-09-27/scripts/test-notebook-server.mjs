// Real handler + real SQLite SQL. R2, Cloudflare env and OpenAI are isolated fixtures.
import assert from 'node:assert/strict';import fs from 'node:fs/promises';import {build} from 'esbuild';import {DatabaseSync} from 'node:sqlite';import {ID,validContext,validAnalysis,rankNotes} from '../lib/note-contract.mjs';
const dir=new URL('../.sites-runtime/notebook-test/',import.meta.url);await fs.mkdir(dir,{recursive:true});const db=new DatabaseSync(':memory:');db.exec(await fs.readFile(new URL('../drizzle/0000_abnormal_paladin.sql',import.meta.url),'utf8'));
const objects=new Map();
const env={
 DB:{prepare(sql){return {bind(...values){const st=db.prepare(sql);return {
  async first(){return st.get(...values)||null;},
  async all(){return {results:st.all(...values)};},
  async run(){const r=st.run(...values);return {meta:{changes:Number(r.changes)}};}
 };}};}},
 BUCKET:{
  async put(key,data,meta){objects.set(key,{bytes:await new Response(data).arrayBuffer(),httpMetadata:meta.httpMetadata});},
  async get(key){const o=objects.get(key);return o?{httpMetadata:o.httpMetadata,body:o.bytes,arrayBuffer:async()=>o.bytes}:null;}
 }
};globalThis.__noteEnv=env;
const shim=new URL('env.mjs',dir);await fs.writeFile(shim,'export const env=globalThis.__noteEnv;');const mock=new URL('openai.mjs',dir);await fs.writeFile(mock,`export default class OpenAI{constructor(){this.audio={transcriptions:{create:async()=>({text:'Widzę trzy liście i podobny układ promieni.'})}};this.embeddings={create:async()=>({data:[{embedding:[1,0,0]}]})};this.responses={create:async input=>{globalThis.__lastAI=input;return{output_text:JSON.stringify({title:'Promienie',summary:'Obserwacja użytkownika.',category:'Rośliny',tags:['liście'],observations:['Trzy liście'],hypotheses:['Podobieństwo układu'],tests:['Porównaj folio'],links:[]})}}};}}`);
await build({entryPoints:[new URL('../lib/notebook-server.ts',import.meta.url).pathname],outfile:new URL('handler.mjs',dir).pathname,bundle:true,platform:'node',format:'esm',alias:{'cloudflare:workers':shim.pathname,openai:mock.pathname},logLevel:'silent'});const {handleNotes}=await import(new URL('handler.mjs',dir));
const origin='https://example.test',id=crypto.randomUUID(),ctx={sources:[{scan:'s0014',folio:'6v'}],pose:{position:[0,1.7,0],quaternion:[0,0,0,1]},strokes:[]};assert.ok(validContext(ctx));assert.ok(!validContext({...ctx,pose:{position:[NaN],quaternion:[]}}));assert.ok(!validAnalysis({title:'x'},new Set()));
const call=(path,method='GET',body,owner='alice',requestOrigin=origin)=>handleNotes(new Request(origin+'/api/notes/'+path.join('/'),{method,headers:{...(owner?{'oai-authenticated-user-id':owner}:{}),...(method!=='GET'?{Origin:requestOrigin}:{})},body}),path);
assert.equal((await call(['status'],'GET',null,'')).status,401);assert.equal((await call(['status'])).status,200);
const form=()=>{const f=new FormData();f.set('context',JSON.stringify(ctx));f.set('audio',new Blob(['test audio'],{type:'audio/webm'}),'test.webm');f.set('image',new Blob([new Uint8Array([255,216,255,217])],{type:'image/jpeg'}),'view.jpg');return f;};
assert.equal((await call([id],'PUT',form(),'alice','https://other.test')).status,403);assert.equal((await call([id],'PUT',form())).status,201);assert.equal(objects.size,2);assert.equal((await call([id],'GET',null,'bob')).status,404);assert.equal((await call([id,'media','audio'],'GET',null,'bob')).status,404);assert.equal((await call([id,'media','audio'])).status,200);assert.equal((await call([id],'PUT',form())).status,200);assert.equal(objects.size,2);
assert.equal((await call([id,'process'],'POST')).status,503);let n=await(await call([id])).json();assert.equal(n.status,'saved');env.OPENAI_API_KEY='mock-only-no-live-request';let processed=await call([id,'process'],'POST');assert.equal(processed.status,200);n=await processed.json();assert.equal(n.status,'ready');assert.match(n.transcript,/trzy liście/);assert.equal(JSON.parse(n.analysis).category,'Rośliny');assert.equal(globalThis.__lastAI.store,false);assert.equal(globalThis.__lastAI.input[0].content[1].type,'input_image');assert.equal((await call([id,'process'],'POST')).status,200);
assert.equal(rankNotes([{id:'a',embedding:'[0,1]'}, {id:'b',embedding:'[1,0]'}],[1,0])[0].id,'b');
const list=await(await call([])).json();assert.equal(list.notes.length,1);console.log('PASS real handler and SQL: authenticated/owner-scoped reads, CSRF check, audio/image storage, idempotent upload, API-key missing state preserves original, mocked transcription + vision + structured note persisted, duplicate processing short-circuits, similarity ranking. No live OpenAI call.');db.close();
