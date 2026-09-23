import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from geometry_lib import Bar, simulate

def test_long_target_hit():
    bars=[Bar(100,100,100,100)]*1 + [Bar(100,100,100,100)] + [Bar(100,103,100,102)]
    r=simulate(bars,0,+1,stop_dist=1.0,target_dist=2.0)
    assert abs(r-2.0)<1e-9, r   # +2R target reached

def test_long_stop_hit():
    bars=[Bar(100,100,100,100),Bar(100,100,98.9,99)]
    r=simulate(bars,0,+1,stop_dist=1.0,target_dist=2.0)
    assert abs(r-(-1.0))<1e-9, r

def test_short_target_hit():
    bars=[Bar(100,100,100,100),Bar(100,100,97.9,98)]
    r=simulate(bars,0,-1,stop_dist=1.0,target_dist=2.0)
    assert abs(r-2.0)<1e-9, r   # short wins when price DROPS

def test_short_stop_hit():
    # THE bug case: short must STOP OUT when price rises
    bars=[Bar(100,100,100,100),Bar(100,101.1,100,101)]
    r=simulate(bars,0,-1,stop_dist=1.0,target_dist=2.0)
    assert abs(r-(-1.0))<1e-9, r

def test_short_same_bar_pessimistic():
    # both stop(+1) and target(-2) touchable same bar -> stop wins
    bars=[Bar(100,100,100,100),Bar(100,101.5,97.5,99)]
    r=simulate(bars,0,-1,stop_dist=1.0,target_dist=2.0)
    assert abs(r-(-1.0))<1e-9, r

def test_long_trail():
    # rise to +2R (arm at +2), pull back 1R from extreme +3 -> exit at +2
    bars=[Bar(100,100,100,100),Bar(100,103,100,103),Bar(100,103,101.9,102)]
    r=simulate(bars,0,+1,stop_dist=1.0,trail_arm=2.0,trail_gap=1.0)
    assert r>=1.9 and r<=3.0, r
