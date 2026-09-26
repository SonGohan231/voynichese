import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as T from '../dist/vendor/three.module.js';
import {catalogCategories,filterCatalog,splitRanges} from '../dist/catalog.js';
import {FULL_CUT,cropGeometry} from '../dist/mesh-edit.js';
const pages=JSON.parse(fs.readFileSync(new URL('../dist/assets/atlas.json',import.meta.url),'utf8')).pages;
assert.equal(catalogCategories(pages).length,7);assert.equal(filterCatalog(pages,'Rośliny').length,125);assert.equal(filterCatalog(pages,'all','category').length,206);for(const category of catalogCategories(pages))assert.ok(filterCatalog(pages,category).every(p=>p.category===category));assert.equal(filterCatalog(pages,'Nieistniejąca').length,0);
const area=g=>{const p=g.attributes.position;let sum=0;for(let i=0;i<p.count;i+=3){const a=new T.Vector3().fromBufferAttribute(p,i),b=new T.Vector3().fromBufferAttribute(p,i+1),c=new T.Vector3().fromBufferAttribute(p,i+2);sum+=b.sub(a).cross(c.sub(a)).length()/2;}return sum;};
for(const axis of ['x','y'])for(const count of [2,3,4]){const ranges=splitRanges(FULL_CUT,axis,count);assert.equal(ranges.length,count);assert.equal(ranges[0][axis+'Min'],0);assert.equal(ranges.at(-1)[axis+'Max'],1);for(let i=1;i<count;i++)assert.equal(ranges[i-1][axis+'Max'],ranges[i][axis+'Min']);let total=0;for(const r of ranges){const min=new T.Vector3(r.xMin*2-1,r.yMin*2-1,-1),max=new T.Vector3(r.xMax*2-1,r.yMax*2-1,1),g=cropGeometry(new T.PlaneGeometry(2,2),new T.Box3(min,max));total+=area(g);}assert.ok(Math.abs(total-4)<1e-6,'split keeps the complete surface without duplicated area');}
assert.throws(()=>splitRanges({...FULL_CUT,xMax:.03},'x',4));
console.log('PASS: seven source categories, full 206-scan coverage, 125 plant scans, stable filters, 2/3/4-way split boundaries and surface-area conservation.');
