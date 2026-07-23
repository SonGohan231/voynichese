#!/usr/bin/env python3
from __future__ import annotations
import csv, json, math, random, re, sys, urllib.request
from pathlib import Path
from collections import defaultdict

SOURCE_URL='https://www.voynich.nu/data/RF1b-er.txt'
SEED=3001425
PERMUTATIONS=100000
SIGN_PANELS={
 'Pisces':['f70v2'],
 'Aries':['f70v1','f71r'],
 'Taurus':['f71v','f72r1'],
 'Gemini':['f72r2'],
 'Cancer':['f72r3'],
 'Leo':['f72v3'],
 'Virgo':['f72v2'],
 'Libra':['f72v1'],
 'Scorpio':['f73r'],
 'Sagittarius':['f73v'],
}
CALIBRATION=['Aries','Taurus']

COMMENT_RE=re.compile(r'<!.*?>')
ALT_RE=re.compile(r'\[([^:\]]+):[^\]]+\]')
LOCUS_RE=re.compile(r'^\s*<([^>]+)>\s*(.*?)\s*$')

def normalize(raw:str)->str:
    s=COMMENT_RE.sub('',raw)
    s=ALT_RE.sub(lambda m:m.group(1),s)
    s=re.sub(r'@\d+;','',s)
    s=re.sub(r'\{[^}]*\}','',s)
    s=s.replace(',','').replace('=','').lower()
    s=re.sub(r'[^a-z?.]+','',s)
    s=s.replace('?','')
    s=re.sub(r'\.{2,}','.',s).strip('.')
    return s

def locus_key(locus:str):
    parts=locus.split(',')[0].split('.')
    page=parts[0]
    nums=[]
    for p in parts[1:]:
        m=re.search(r'\d+',p)
        nums.append(int(m.group()) if m else 0)
    return page,tuple(nums)

def parse(text:str):
    rows=[]
    for line_no,line in enumerate(text.splitlines(),1):
        m=LOCUS_RE.match(line)
        if not m: continue
        locus=m.group(1)
        if not re.search(r'[@&]Lz\b',locus): continue
        page=locus.split('.')[0]
        label=normalize(m.group(2))
        rows.append({'line_no':line_no,'locus':locus,'page':page,'label':label,'raw':m.group(2)})
    return rows

def levenshtein(a,b):
    if a==b:return 0
    if not a:return len(b)
    if not b:return len(a)
    prev=list(range(len(b)+1))
    for i,ca in enumerate(a,1):
        cur=[i]
        for j,cb in enumerate(b,1):
            cur.append(min(cur[-1]+1,prev[j]+1,prev[j-1]+(ca!=cb)))
        prev=cur
    return prev[-1]

def common_prefix(a,b):
    n=0
    for x,y in zip(a,b):
        if x!=y:break
        n+=1
    return n

def common_suffix(a,b): return common_prefix(a[::-1],b[::-1])
def bigrams(s): return [s[i:i+2] for i in range(max(0,len(s)-1))]

def dice(a,b):
    aa=bigrams(a); bb=bigrams(b)
    if not aa and not bb:return 1.0 if a==b else 0.0
    from collections import Counter
    ca,cb=Counter(aa),Counter(bb)
    inter=sum((ca & cb).values())
    return 2*inter/max(1,len(aa)+len(bb))

def similarity(a,b):
    if not a or not b:return 0.0
    den=max(len(a),len(b),1)
    vals=[1-levenshtein(a,b)/den,common_prefix(a,b)/den,common_suffix(a,b)/den,dice(a,b),1-abs(len(a)-len(b))/den]
    return sum(vals)/len(vals)

def sign_sequences(rows):
    by_page=defaultdict(list)
    for r in rows: by_page[r['page']].append(r)
    for page in by_page: by_page[page].sort(key=lambda r:locus_key(r['locus'])[1])
    return {sign:[r for page in pages for r in by_page[page]] for sign,pages in SIGN_PANELS.items()}

def shift_score(labels,refs,shift):
    n=len(labels)
    return sum((similarity(labels[(i+shift)%n],refs[0][i])+similarity(labels[(i+shift)%n],refs[1][i]))/2 for i in range(n))/n

def one_gap_score(labels,refs,gap,shift=0):
    x=labels[shift:]+labels[:shift]
    vals=[]; j=0
    for i in range(30):
        if i==gap: continue
        vals.append((similarity(x[j],refs[0][i])+similarity(x[j],refs[1][i]))/2); j+=1
    return sum(vals)/len(vals)

def main(outdir:Path):
    outdir.mkdir(parents=True,exist_ok=True)
    req=urllib.request.Request(SOURCE_URL,headers={'User-Agent':'VoynichOrdinalTest/1.0'})
    with urllib.request.urlopen(req,timeout=120) as r: data=r.read()
    text=data.decode('utf-8-sig',errors='replace')
    (outdir/'RF1b-er.source.txt').write_text(text,encoding='utf-8')
    rows=parse(text)
    if len(rows)!=299: raise RuntimeError(f'Expected 299 Lz loci, got {len(rows)}')
    seq=sign_sequences(rows)
    counts={k:len(v) for k,v in seq.items()}
    thirty=[s for s,c in counts.items() if c==30]
    twenty_nine=[s for s,c in counts.items() if c==29]
    if counts['Aries']!=30 or counts['Taurus']!=30: raise RuntimeError(f'Calibration counts invalid: {counts}')
    if len(twenty_nine)!=1 or len(thirty)!=9: raise RuntimeError(f'Unexpected sign counts: {counts}')
    held=[s for s in thirty if s not in CALIBRATION]
    refs=([x['label'] for x in seq['Aries']],[x['label'] for x in seq['Taurus']])
    score_by_sign={}; shift_scores={}
    for s in held:
        labs=[x['label'] for x in seq[s]]
        vals=[shift_score(labs,refs,k) for k in range(30)]
        shift_scores[s]=vals
        mean_all=sum(vals)/30
        score_by_sign[s]={'observed':vals[0],'null_mean_all_shifts':mean_all,'effect':vals[0]-mean_all,'best_shift':max(range(30),key=lambda k:vals[k]),'best_score':max(vals)}
    observed=sum(score_by_sign[s]['observed'] for s in held)/len(held)
    rng=random.Random(SEED); null=[]
    for _ in range(PERMUTATIONS): null.append(sum(shift_scores[s][rng.randrange(30)] for s in held)/len(held))
    null_mean=sum(null)/len(null)
    p=(1+sum(v>=observed for v in null))/(1+len(null))
    effect=observed-null_mean
    sd=(sum((v-null_mean)**2 for v in null)/(len(null)-1))**0.5
    z=effect/sd if sd else 0.0
    concordant=sum(score_by_sign[s]['effect']>0 for s in held)
    if p<=0.01 and effect>=0.02 and concordant>=5: verdict='PASS_POSITIONAL_TRANSFER'
    elif p>0.05 or effect<=0 or concordant<=3: verdict='FAIL_EXACT_REFERENCE_LOCUS_ORDER_MODEL'
    else: verdict='INCONCLUSIVE'
    missing=twenty_nine[0]
    labs=[x['label'] for x in seq[missing]]
    gap_scores={(gap,sh):one_gap_score(labs,refs,gap,sh) for gap in range(30) for sh in range(29)}
    best_pair=max(gap_scores,key=gap_scores.get); best=gap_scores[best_pair]
    null_gap=[max(gap_scores[(g,sh)] for g in range(30)) for sh in range(29)]
    gap_p=(1+sum(v>=best for v in null_gap))/(1+len(null_gap))
    with (outdir/'zodiac_labels_parsed.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f); w.writerow(['sign','ordinal_source','page','locus','label','raw'])
        for s in SIGN_PANELS:
            for i,r in enumerate(seq[s],1): w.writerow([s,i,r['page'],r['locus'],r['label'],r['raw']])
    result={'experiment_id':'ZODIAC-30-ORDINAL-LABEL-TRANSFER-01','source_url':SOURCE_URL,'source_bytes':len(data),'total_Lz_loci':len(rows),'counts_by_sign':counts,'calibration':CALIBRATION,'heldout':held,'missing_label_sign':missing,'primary':{'observed':observed,'null_mean':null_mean,'effect':effect,'null_sd':sd,'z':z,'p_perm':p,'permutations':PERMUTATIONS,'seed':SEED,'concordant_signs':concordant,'heldout_n':len(held),'verdict':verdict},'per_sign':score_by_sign,'one_gap_stress':{'sign':missing,'best_gap_1_based':best_pair[0]+1,'best_shift':best_pair[1],'best_score':best,'exact_shift_null_p':gap_p,'note':'exploratory stress test; maximization over all 30 gaps is included in null'},'interpretation_limit':'Tests RF1b locus order as ordinal proxy; does not certify physical zodiac-degree order.'}
    (outdir/'RESULT.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    md=['# Result: ZODIAC-30-ORDINAL-LABEL-TRANSFER-01','',f"**Verdict:** `{verdict}`",'',f"Lz loci: **{len(rows)}**. Counts: `{counts}`.",'',f"Observed similarity: `{observed:.6f}`; null mean: `{null_mean:.6f}`; effect: `{effect:.6f}`; permutation p: `{p:.6g}`; concordant held-out signs: `{concordant}/{len(held)}`.",'',f"One-gap stress sign: **{missing}**; best candidate gap: **{best_pair[0]+1}**; corrected exact p over circular shifts: `{gap_p:.6g}`.",'','## Scope','','The result applies only to the frozen RF1b locus order. It does not establish or refute a visually certified 1–30 degree ordering.']
    (outdir/'RESULT.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    print(json.dumps(result['primary'],indent=2))

if __name__=='__main__': main(Path(sys.argv[1] if len(sys.argv)>1 else 'research/zodiac30_ordinal_sky/results'))
