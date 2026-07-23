#!/usr/bin/env python3
from __future__ import annotations
import csv, json, math, sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import swisseph as swe

CAL=swe.JUL_CAL
FLAGS=swe.FLG_MOSEPH|swe.FLG_SPEED
PLANETS={'Sun':swe.SUN,'Moon':swe.MOON,'Mercury':swe.MERCURY,'Venus':swe.VENUS,'Mars':swe.MARS,'Jupiter':swe.JUPITER,'Saturn':swe.SATURN}
VISIBLE=['Mercury','Venus','Mars','Jupiter','Saturn']
LOCATIONS={'Paris':(2.35,48.86,35),'Milan':(9.19,45.46,120),'Prague':(14.42,50.08,200),'Vienna':(16.37,48.21,170)}

def jd(y,m,d,h=0): return swe.julday(y,m,d,h,CAL)
def rev(x): return swe.revjul(x,CAL)
def calc(name,t): return swe.calc_ut(t,PLANETS[name],FLAGS)[0]
def lon(name,t): return calc(name,t)[0]%360
def adiff(a,b): return abs((a-b+180)%360-180)
def date_string(t):
    y,m,d,h=rev(t); hh=int(h); mm=int(round((h-hh)*60))
    if mm==60: hh+=1; mm=0
    return f'{y:04d}-{m:02d}-{d:02d} {hh:02d}:{mm:02d} UT (Julian)'
def ecl_type(flags,lunar=False):
    if flags&swe.ECL_TOTAL:return 'total'
    if flags&swe.ECL_ANNULAR:return 'annular'
    if flags&swe.ECL_PARTIAL:return 'partial'
    if lunar and flags&swe.ECL_PENUMBRAL:return 'penumbral'
    return 'unknown'
def refine_min(a,b,t0):
    xs=np.arange(t0-1.0,t0+1.0001,1/96);vals=np.array([adiff(lon(a,x),lon(b,x)) for x in xs]);k=int(vals.argmin())
    xs2=np.arange(xs[k]-1/96,xs[k]+1/96+1e-9,1/1440);vals2=np.array([adiff(lon(a,x),lon(b,x)) for x in xs2]);q=int(vals2.argmin())
    return float(xs2[q]),float(vals2[q])
def conjunctions(start,end):
    out=[];grid=np.arange(start,end,0.25)
    for i,a in enumerate(VISIBLE):
        for b in VISIBLE[i+1:]:
            ds=np.array([adiff(lon(a,t),lon(b,t)) for t in grid]);cand=[]
            for k in range(1,len(grid)-1):
                if ds[k]<=ds[k-1] and ds[k]<ds[k+1] and ds[k]<1.0:
                    t,sep=refine_min(a,b,float(grid[k]))
                    if not cand or t-cand[-1][0]>3:cand.append((t,sep))
                    elif sep<cand[-1][1]:cand[-1]=(t,sep)
            for t,sep in cand:
                l=(lon(a,t)+((lon(b,t)-lon(a,t)+180)%360-180)/2)%360;elong=adiff(l,lon('Sun',t))
                out.append({'body_a':a,'body_b':b,'date':date_string(t),'jd_ut':t,'separation_deg':sep,'ecliptic_longitude_deg':l,'solar_elongation_deg':elong,'event_class':'great_conjunction' if {a,b}=={'Jupiter','Saturn'} else 'close_conjunction'})
    return sorted(out,key=lambda r:r['jd_ut'])
def solar_eclipses(start,end):
    rows=[]
    for name,geo in LOCATIONS.items():
        t=start-5
        while True:
            flags,tret,attr=swe.sol_eclipse_when_loc(t,geo,swe.FLG_MOSEPH);mx=tret[0]
            if mx>=end:break
            rows.append({'location':name,'date':date_string(mx),'jd_ut':mx,'type':ecl_type(flags),'magnitude':attr[0],'obscuration':attr[2],'sun_altitude_deg':attr[6]});t=mx+10
    return sorted(rows,key=lambda r:(r['jd_ut'],r['location']))
def lunar_eclipses(start,end):
    rows=[]
    for name,geo in LOCATIONS.items():
        t=start-5
        while True:
            flags,tret,attr=swe.lun_eclipse_when_loc(t,geo,swe.FLG_MOSEPH);mx=tret[0]
            if mx>=end:break
            rows.append({'location':name,'date':date_string(mx),'jd_ut':mx,'type':ecl_type(flags,True),'umbral_magnitude':attr[0],'penumbral_magnitude':attr[1],'moon_altitude_deg':attr[6]});t=mx+10
    return sorted(rows,key=lambda r:(r['jd_ut'],r['location']))
def write_csv(path,rows):
    if not rows:return
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
def main(outdir):
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True);start,end=jd(1404,1,1),jd(1431,1,1)
    con=conjunctions(start,end);sol=solar_eclipses(start,end);lun=lunar_eclipses(start,end)
    write_csv(outdir/'planetary_conjunctions_under_1deg.csv',con);write_csv(outdir/'solar_eclipses_reference_locations.csv',sol);write_csv(outdir/'lunar_eclipses_reference_locations.csv',lun)
    great=[r for r in con if r['event_class']=='great_conjunction'];write_csv(outdir/'jupiter_saturn_conjunctions.csv',great)
    monthly=[]
    for y in range(1404,1431):
        for m in range(1,13):
            t=jd(y,m,15,12)
            for p in VISIBLE:monthly.append({'year':y,'month':m,'decimal_year':y+(m-0.5)/12,'body':p,'longitude_deg':lon(p,t)})
    write_csv(outdir/'visible_planet_longitudes_monthly.csv',monthly)
    daily=[]
    for day in np.arange(jd(1425,1,1),jd(1426,1,1),1):
        y,m,d,h=rev(float(day));daily.append({'date':f'{y:04d}-{m:02d}-{d:02d}','jd_ut':float(day),'Sun':lon('Sun',day),'Moon':lon('Moon',day),'Jupiter':lon('Jupiter',day),'Saturn':lon('Saturn',day),'Jupiter_Saturn_sep':adiff(lon('Jupiter',day),lon('Saturn',day))})
    write_csv(outdir/'daily_sun_moon_jupiter_saturn_1425.csv',daily)
    fig,ax=plt.subplots(figsize=(12,6))
    for p in VISIBLE:
        rr=[r for r in monthly if r['body']==p];ax.plot([r['decimal_year'] for r in rr],[r['longitude_deg'] for r in rr],label=p,linewidth=0.8)
    ax.set(xlabel='Year (Julian calendar)',ylabel='Geocentric tropical ecliptic longitude (deg)',title='Visible planets, monthly positions 1404–1430');ax.set_ylim(0,360);ax.legend(ncol=5,fontsize=8);fig.tight_layout();fig.savefig(outdir/'visible_planet_longitudes_1404_1430.svg');plt.close(fig)
    fig,ax=plt.subplots(figsize=(12,5));x=np.arange(len(daily));ax.plot(x,[r['Sun'] for r in daily],label='Sun');ax.plot(x,[r['Moon'] for r in daily],label='Moon',linewidth=.8);ax.set(xlabel='Day of 1425',ylabel='Ecliptic longitude (deg)',title='Sun and Moon through 1425');ax.set_ylim(0,360);ax.legend();fig.tight_layout();fig.savefig(outdir/'sun_moon_path_1425.svg');plt.close(fig)
    fig,ax=plt.subplots(figsize=(12,5));ax.plot(x,[r['Jupiter'] for r in daily],label='Jupiter');ax.plot(x,[r['Saturn'] for r in daily],label='Saturn');ax.set(xlabel='Day of 1425',ylabel='Ecliptic longitude (deg)',title='Triple Jupiter–Saturn conjunction in Scorpio, 1425');ax.legend();fig.tight_layout();fig.savefig(outdir/'jupiter_saturn_triple_1425.svg');plt.close(fig)
    major_solar=[];bydate={}
    for r in sol:bydate.setdefault(r['date'].split(' ')[0],[]).append(r)
    for date,rs in bydate.items():
        mx=max(rs,key=lambda z:z['magnitude'])
        if mx['magnitude']>=0.85:major_solar.append((date,mx['location'],mx['type'],mx['magnitude']))
    total_lunar=[];seen=set()
    for r in lun:
        key=r['date'].split(' ')[0]
        if r['type']=='total' and key not in seen:seen.add(key);total_lunar.append((key,r['umbral_magnitude']))
    summary={'method':{'calendar':'Julian','ephemeris':'Swiss Ephemeris / Moshier','range':'1404-01-01 through 1430-12-31','reference_locations':LOCATIONS},'great_conjunctions':great,'major_solar_eclipses_reference_belt':major_solar,'total_lunar_eclipses_visible_reference_belt':total_lunar,'precession_across_26_years_deg':26*50.29/3600}
    (outdir/'ASTRONOMY_RESULT.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    lines=['# Astronomy 1404–1430: computed findings','','Calculations use the Julian calendar and Swiss Ephemeris/Moshier. Reference locations are sampling points, not a provenance claim.','','## Jupiter–Saturn','']
    for r in great:lines.append(f"- {r['date']}: separation {r['separation_deg']:.4f}°, longitude {r['ecliptic_longitude_deg']:.2f}°, solar elongation {r['solar_elongation_deg']:.1f}°.")
    lines+=['','The 1425 event is a triple conjunction in tropical Scorpio and is the strongest historically specific candidate in the manuscript date window. The 1405 conjunction was only about 18° from the Sun and was much less observable.','','## Major solar eclipses in the European reference belt','']
    for d,l,t,m in major_solar:lines.append(f'- {d}: maximum sampled at {l}, {t}, magnitude {m:.3f}.')
    lines+=['','## Fixed stars','',f"Across 26 years general precession is only about {summary['precession_across_26_years_deg']:.3f}°. Fixed-star patterns therefore do not create a unique year-specific map. The informative phenomena are conjunctions, occultations, eclipses and the changing positions of planets against the fixed-star background.",'','## Interpretation boundary','','A temporal match does not identify the manuscript date. A viable manuscript model must predict a page-specific feature—especially on Scorpio f73r—without choosing the feature after seeing the 1425 sky.']
    (outdir/'ASTRONOMY_FINDINGS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'great_conjunctions':len(great),'solar_rows':len(sol),'lunar_rows':len(lun)},indent=2))
if __name__=='__main__':main(sys.argv[1] if len(sys.argv)>1 else 'research/zodiac30_ordinal_sky/astronomy')
