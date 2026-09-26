import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=new URL('../dist/',import.meta.url).pathname;const atlas=JSON.parse(fs.readFileSync(path.join(root,'assets/atlas.json'),'utf8'));
assert.equal(atlas.pages.length,206);let parts=0;
for(const p of atlas.pages){for(const url of [p.page_model,p.art_model,...p.parts.map(q=>q.model)].filter(Boolean))assert.ok(fs.existsSync(path.join(root,url)),url);parts+=p.parts.length;}
const html=fs.readFileSync(path.join(root,'index.html'),'utf8'),app=fs.readFileSync(path.join(root,'app.js'),'utf8');
for(const m of app.matchAll(/\$\('#([A-Za-z][\w-]*)'\)/g))assert.ok(html.includes(`id="${m[1]}"`),m[1]);
for(const p of fs.readdirSync(path.join(root,'vendor'))){const src=fs.readFileSync(path.join(root,'vendor',p),'utf8').replace(/\/\*[\s\S]*?\*\//g,'');for(const m of src.matchAll(/^import\s+[\s\S]*?\sfrom\s+['"]([^'"]+)['"]/gm)){if(m[1]==='three')continue;assert.ok(fs.existsSync(path.resolve(root,'vendor',m[1])),`${p}: ${m[1]}`);}}
assert.ok(html.includes('lang="pl"'));console.log(JSON.stringify({scans:206,parts,assets:'all referenced models present',modules:'all vendor imports resolved',controls:'all static control targets present'}));

const qhtml=fs.readFileSync(path.join(root,'quest.html'),'utf8'),quest=fs.readFileSync(path.join(root,'quest.js'),'utf8');for(const m of quest.matchAll(/\$\('#([A-Za-z][\w-]*)'\)/g))assert.ok(qhtml.includes(`id="${m[1]}"`),m[1]);
let bytes=0;function walk(dir){for(const entry of fs.readdirSync(dir,{withFileTypes:true})){const file=path.join(dir,entry.name);if(entry.isDirectory())walk(file);else bytes+=fs.statSync(file).size;}}walk(root);assert.ok(bytes<256*1024*1024);console.log(JSON.stringify({questControls:'all IDs present',staticBytes:bytes,hostingLimit:256*1024*1024}));
