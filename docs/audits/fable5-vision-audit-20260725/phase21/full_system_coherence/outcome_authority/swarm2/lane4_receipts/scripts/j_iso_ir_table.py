"""LANE 4: the iso-IR table. n_required = k*(sigma/mu)^2, k = (z_.975 + z_.80)^2 = 7.8489.
Produces J_ISO_IR_TABLE_V1.json."""
import json, numpy as np
from scipy import stats
K=(stats.norm.ppf(0.975)+stats.norm.ppf(0.80))**2
def cell(mu,sd,bpm,label,src):
    ir_bet=mu/sd; ir_ann=ir_bet*np.sqrt(bpm*12); yrs=K/ir_ann**2
    return {'label':label,'src':src,'mu_per_bet':mu,'sd_per_bet':sd,'bets_per_month':bpm,
            'IC_per_bet_mu_over_sd':round(ir_bet,4),'effective_bets_per_year':round(bpm*12,1),
            'IR_annualised':round(ir_ann,4),'years_to_answer':round(yrs,3),'months_to_answer':round(yrs*12,2),
            'breadth_multiple_for_6_week_answer':round((np.sqrt(K/0.125)/ir_ann)**2,2)}
T={
 'armed3_live_FTMO_bookday':cell(0.3298,1.1785,3.833,'armed 3, FTMO CURRENT_SURFACE, R/book-day','THREE_SLEEVE_BOOK_RESTATEMENT §3.2'),
 'armed3_live_FN_bookday':cell(0.4026,1.0071,2.938,'armed 3, redacted_account FN_TRADEABLE','THREE_SLEEVE_BOOK_RESTATEMENT §3.2'),
 'armed3_archive_pertrade':cell(1.02672,2.20513,4.637,'armed 3, r1 archive fwd, capped','LANE4 C'),
 'outofselection_basket_c0p05_pertrade':cell(0.17786-0.05,1.4813,65.83,'9-sleeve out-of-selection basket net 0.05R','LANE4 I'),
 'outofselection_basket_c0p05_dayportfolio':cell(0.10985-0.05,0.99146,22.65,'same basket, one unit of risk per DAY','LANE4 I'),
 'all29_daylevel':cell(-0.027726*7.7457,1.4158*np.sqrt(5.692),9.192,'all 29 sleeves, day level','LANE4 C'),
 'funnel_at_required_edge':cell(0.09,1.1388,1847.4,'funnel IF it had the break-even edge','LANE_I §7.1 + LANE4 B'),
 'funnel_measured_edge':cell(0.00298,1.1388,1847.4,'funnel, measured within-window edge','LANE_I §3.1'),
 'required_for_6_week_answer':{'target_years':0.125,'IR_annualised_required':round(float(np.sqrt(K/0.125)),3),'k_z2':round(float(K),4)}}
print(json.dumps(T,indent=1,default=str))
