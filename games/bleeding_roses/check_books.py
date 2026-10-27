import sys,os
sys.path.insert(0,os.path.abspath("../..")); sys.path.insert(0,".")
from game_config import GameConfig
from gamestate import GameState
from src.wins.win_manager import WinManager
cfg=GameConfig()
fails=[];n=0;caps=0;capbase=0
for m in cfg.bet_modes:
    mode=m.get_name()
    crits=[d._criteria for d in m.get_distributions()]
    for crit in crits:
        reps = 60 if crit=="wincap" else 40
        for sim in range(reps):
            gs=GameState(cfg); gs.win_manager=WinManager(cfg.basegame_type,cfg.freegame_type)
            gs.library={}; gs.betmode=mode; gs.criteria=crit
            gs.run_spin(sim)
            ev=gs.book.events if hasattr(gs.book,'events') else []
            g=lambda t:[e for e in ev if e['type']==t]
            fw=g('finalWin')[-1]['amount']; n+=1
            base=0
            for e in ev:
                if e['type']=='freeSpinTrigger': break
                if e['type']=='winInfo': base+=e['totalWin']
            fe=g('freeSpinEnd'); wc=g('wincap')
            st=g('setTotalWin')
            if st and st[-1]['amount']!=fw: fails.append((mode,crit,sim,'lastTotal',st[-1]['amount'],fw))
            if round(gs.book.payout_multiplier*100)!=fw: fails.append((mode,crit,sim,'payout'))
            if fe and fe[-1]['amount']!=fw-base: fails.append((mode,crit,sim,'fsEnd',fe[-1]['amount'],fw,base))
            if wc:
                caps+=1; capbase+= base>0
                lastinfo=[e for e in ev if e['type']=='winInfo']
                tot=sum(e['totalWin'] for e in lastinfo)
                if tot!=fw: fails.append((mode,crit,sim,'winInfoSum',tot,fw))
print("books",n,"capbooks",caps,"capWithBaseWin",capbase)
from collections import Counter
print(Counter((f[0],f[1],f[3]) for f in fails))
print(fails[:8])
