// Executes the application's actual handlers with Three.js scene math and mocked XR/DOM I/O.
// This is not a WebGL/browser/headset test.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import * as T from '../dist/vendor/three.module.js';
import * as math from '../dist/xr-math.js';
import * as meshEdit from '../dist/mesh-edit.js';
import * as catalog from '../dist/catalog.js';
const html=fs.readFileSync(new URL('../dist/quest.html',import.meta.url),'utf8');
const elements=new Map([...html.matchAll(/id="([^"]+)"/g)].map(m=>['#'+m[1],{append(){},addEventListener(){},getBoundingClientRect(){return {width:1000,height:700,left:0,top:0};}}]));
const canvas=()=>({getContext:()=>({fillRect(){},fillText(){},drawImage(){},strokeRect(){},measureText:s=>({width:s.length*16})}),addEventListener(){}});
class Renderer{constructor(){this.domElement=canvas();this.controllers=[new T.Group(),new T.Group()];this.xr={setReferenceSpaceType(){},getController:i=>this.controllers[i],isPresenting:false};}setPixelRatio(){}setSize(){}setAnimationLoop(fn){this.frame=fn;}render(s){s.updateMatrixWorld(true);}setClearColor(){}}
class Orbit{constructor(){this.target=new T.Vector3();}update(){}}
let failLoad=false;
class Loader{async loadAsync(){if(failLoad)throw Error('fixture load failure');const scene=new T.Group();for(let i=0;i<3;i++){const mesh=new T.Mesh(new T.BoxGeometry(.07,.1,.01).translate(i*.15,0,0),new T.MeshStandardMaterial());mesh.name='fragment-'+i;scene.add(mesh);}return {scene};}}
const data=JSON.parse(fs.readFileSync(new URL('../dist/assets/atlas.json',import.meta.url),'utf8'));
const storage=new Map();let uid=0;
const context=vm.createContext({console,devicePixelRatio:1,isSecureContext:true,navigator:{},crypto:{randomUUID:()=>`id-${++uid}`},ResizeObserver:class{observe(){}},document:{querySelector:s=>{assert.ok(elements.has(s),s);return elements.get(s);},createElement:s=>s==='canvas'?canvas():{}},localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)},fetch:async()=>({json:async()=>data}),setTimeout,URL,Blob});
const actual=fs.readFileSync(new URL('../dist/quest.js',import.meta.url),'utf8');
const source=actual+`\nexport {preview,filteredPages,cycleCategory,nextCard,nextPart,updatePreview,addPreview,splitSelected,changeCut,resetCut,rotateSelected,capture,restore,assemble,explode,joinSelected,detachSelected,newFreeGroup,setActive,addEntry,begin,release,assist,renderer,hands,validate,toggleLayout,toggleReadable,toggleBackplate};export const state=()=>({entries,active,selectedPiece,freeGroups,freeMembership,activeFree,layoutMode,notice,cursor,category,previewPart});`;
const modules={three:{...T,WebGLRenderer:Renderer,TextureLoader:class{async loadAsync(){return new T.Texture();}}},'./vendor/OrbitControls.js':{OrbitControls:Orbit},'./vendor/GLTFLoader.js':{GLTFLoader:Loader},'./vendor/GLTFExporter.js':{GLTFExporter:class{}},'./xr-math.js':math,'./mesh-edit.js':meshEdit,'./catalog.js':catalog};
async function link(name){if(name==='./model-preview.js'){const m=new vm.SourceTextModule(fs.readFileSync(new URL('../dist/model-preview.js',import.meta.url),'utf8'),{context});await m.link(link);return m;}const exports=modules[name==='./vendor/three.module.js'?'three':name];assert.ok(exports,name);return new vm.SyntheticModule(Object.keys(exports),function(){for(const [k,v] of Object.entries(exports))this.setExport(k,v);},{context});}
const mod=new vm.SourceTextModule(source,{context});await mod.link(link);await mod.evaluate();const a=mod.namespace;
const close=(a,b)=>assert.ok(a.every((x,i)=>Math.abs(x-b[i])<1e-6));
assert.equal(a.state().entries.length,1,'startup loaded initial model');assert.equal(a.state().layoutMode,'free');
let e=a.state().active,p=e.pieces[0];a.setActive(e,p);p.position.set(.7,.2,-.1);p.rotation.set(.2,.3,.4);p.updateWorldMatrix(true,false);const custom=p.matrixWorld.clone();a.joinSelected();p.updateWorldMatrix(true,false);close(p.matrixWorld.elements,custom.elements);assert.equal(a.state().freeGroups.length,1);
let e2=await a.addEntry(data.pages[5].id);const p2=e2.pieces[1];a.setActive(e2,p2);p2.updateWorldMatrix(true,false);const custom2=p2.matrixWorld.clone();a.joinSelected();p2.updateWorldMatrix(true,false);close(p2.matrixWorld.elements,custom2.elements);assert.equal(p.parent,p2.parent,'cross-folio pieces join one custom group');
let saved=a.capture();assert.equal(saved.version,5);assert.equal(saved.freeGroups.length,1);assert.equal(saved.entries[1].pieces[1].freeGroup,saved.freeGroups[0].id);await a.restore(saved);e=a.state().entries[0];e2=a.state().entries[1];p=e.pieces[0];p.updateWorldMatrix(true,false);close(p.matrixWorld.elements,custom.elements);assert.equal(a.state().freeMembership.size,2);
a.setActive(e,p);a.detachSelected();p.updateWorldMatrix(true,false);close(p.matrixWorld.elements,custom.elements);assert.ok(!a.state().freeMembership.has(p));
a.toggleLayout();assert.equal(a.state().layoutMode,'source');a.joinSelected();assert.ok(e.joined.has(p.name));close(p.position.toArray(),e.home.get(p.name).p);
// Hold the assembled group with one controller and a loose part from the same folio with the other.
const h0=a.hands[0],h1=a.hands[1],loose=e.pieces[2];h0.controller.attach(e.cluster);h0.held={object:e.cluster,entry:e,cluster:true,whole:false};h1.controller.attach(loose);h1.held={object:loose,entry:e,cluster:false,whole:false};
const record=a.capture();assert.equal(e.cluster.parent,h0.controller);assert.equal(loose.parent,h1.controller);assert.equal(a.assist(h1,null).includes('cm'),true);assert.ok(h1.ghost);a.release(h1,false);a.release(h0,false);assert.equal(h1.ghost,null);
await a.restore(record);assert.equal(a.state().entries[0].joined.size,1);a.setActive(a.state().entries[0]);a.assemble();assert.equal(a.state().active.joined.size,3);a.explode();assert.equal(a.state().active.joined.size,0);
// Load old projects as unjoined pieces, then handle a failed load transactionally.
const legacy=a.capture();legacy.version=1;delete legacy.freeGroups;for(const entry of legacy.entries){delete entry.cluster;for(const piece of entry.pieces){delete piece.freeGroup;delete piece.joined;}}await a.restore(legacy);assert.equal(a.state().freeGroups.length,0);
const before=a.state().entries;failLoad=true;await a.restore(a.capture());failLoad=false;assert.equal(a.state().entries,before);assert.match(a.state().notice,/poprzednia scena zachowana/);
a.setActive(a.state().entries[0],a.state().entries[0].pieces[0]);let edited=a.state().selectedPiece;const geometry=edited.geometry;a.changeCut(.05);assert.notEqual(edited.geometry,geometry);assert.equal(edited.userData.cut.xMin,.05);const cutProject=a.capture();await a.restore(cutProject);edited=a.state().entries[0].pieces[0];assert.equal(edited.userData.cut.xMin,.05);a.setActive(a.state().entries[0],edited);a.rotateSelected(2,Math.PI*2);a.resetCut();assert.equal(edited.userData.cut,undefined);assert.equal(edited.geometry.attributes.position.count,geometry.attributes.position.count);
// Independent pieces survive save/restore without duplicating the visible original.
a.setActive(a.state().entries[0],a.state().entries[0].pieces[0]);const parent=a.state().selectedPiece;const count=a.state().active.pieces.length;a.splitSelected();assert.equal(parent.visible,false);assert.equal(a.state().active.pieces.length,count+2);let split=a.capture();assert.equal(split.entries[0].pieces.filter(p=>p.sourceName).length,2);await a.restore(split);assert.equal(a.state().entries[0].pieces[0].visible,false);assert.equal(a.state().entries[0].pieces.filter(p=>p.userData.sourceName&&p.visible).length,2);
a.setActive(a.state().entries[0],a.state().entries[0].pieces.at(-1));const originalPose=a.state().selectedPiece.quaternion.clone();a.rotateSelected(1,Math.PI);assert.ok(Math.abs(a.state().selectedPiece.quaternion.angleTo(originalPose)-Math.PI)<1e-6);await a.addPreview();assert.equal(a.state().entries[0].pieces.length,count+3);
a.cycleCategory();assert.ok(a.filteredPages().every(p=>p.category===a.state().category));a.nextCard(1);assert.equal(data.pages[a.state().cursor].category,a.state().category);a.nextPart(1);await a.updatePreview();assert.ok(a.preview.stage.children.length);assert.equal(a.preview.root.parent,a.state().active.root.parent.parent);assert.equal(a.preview.stage.children[0].parent,a.preview.stage);
const previewButton=a.preview.pick({x:.15,y:1-(645/900)});assert.equal(typeof previewButton,'function');
a.toggleReadable();a.toggleBackplate();a.renderer.frame(100);assert.throws(()=>a.validate({...a.capture(),freeGroups:[{id:'bad',transform:{}}]}));
console.log('PASS: actual Quest handlers: startup, arbitrary-pose and cross-folio grouping, detach, v5 save/restore + cut restoration, v1 migration, two held objects, ghost lifecycle, source assembly, explode, failed-load rollback, 180-degree turn, independent split/duplicate roundtrip, category filtering, preview model and panel controls, display toggles, DOM IDs. XR/DOM I/O mocked; no rendered or physical-device claim.');
