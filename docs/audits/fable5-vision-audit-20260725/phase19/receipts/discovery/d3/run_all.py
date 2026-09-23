import sys,time,json; sys.path.insert(0,'/tmp/d3')
import d3_walk as W, d3_tape as D, d3_tape2 as T2
syms=sorted({p.name[:-len('_M15.csv')] for p in D.M15_DIR.glob('*_M15.csv')})
tape=T2.CTape(syms); C=W.Cost()
for win,indir in D.WINDOWS.items():
    t0=time.time()
    o=W.run_window(win, indir, tape, C, f'/tmp/d3/D3_{win}.json', chunk=6000)
    print(win, o['n_rows'], 'cells', len(o['cells']), round(time.time()-t0,1),'s',flush=True)
print("ALL DONE",flush=True)
