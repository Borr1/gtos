# Zeta — 20-CANDIDATE Visual MSO Audit

n=20 sampled from W pool=36 + L pool=16.
For each CAND: AI claimed OB / bias; we list the ±3h M15 window and check visual consistency.

## 1. NAS100 2026-02-06 08:15:00 london LONG → WIN (+1.50R)
- Entry 24431.05 SL 24299.45 TP 24628.4
- bias_source: H4+H1_consensus
- AI bias: bullish (high)
- AI H1 POI: OB @ 24380.25 zone=discount causing=BOS
  - Explanation: _Single unmitigated bullish H1 OB at 24431.05-24329.45 (touches=1) formed at the BOS that broke 24478.05 with displacement ratio 1.6._
- AI sweep: pdl + session_low @ 24329.45 quality=clean
```text
  high=24628.4000  low=24299.4500  span=328.9500
TTTTTTTTTTTTSTTTTTTT
                    
                    
                    
                    
           │││      
          │██░      
          ██│░  █░ █
 │       ██  ░░ █░██
░││      █│  │░░█░█│
░░█░│EEEE█EEEEE░█E││
│░█░░│   █     │   │
 ░█ ░░│ ██         │
 │   ░░██           
     │░█│           
      ││            
                    
XXXXXXXXXXXXXXXXXXXX
0   0   0   0   0   
```
**Audit:**
- Limit entry was touched in post-signal window: True
- AI POI level 24380.25 lies within SIGNAL candle [24483.85,24513.25]: False

## 2. NAS100 2026-02-24 09:30:00 london LONG → WIN (+1.50R)
- Entry 24696.83 SL 24624.13 TP 24805.88
- bias_source: H4+H1_consensus
- AI bias: bullish (high)
- AI H1 POI: OB @ 24662.93 zone=discount causing=BOS
  - Explanation: _Single unmitigated bullish H1 OB at 24696.83-24628.58 (midpoint 24662.93), created by BOS event, 1 touch — qualifies for retest entry._
- AI sweep: equal_highs @ 24834.55 quality=clean
```text
  high=24834.5500  low=24624.1300  span=210.4200
░██░        S       
░█│░        │       
TTT░░░││TT██░TTTTTTT
    │░░│█░█│░│    ││
     │░░█││ ░░░   █░
       ││     ░││ █░
              ░█░ █ 
              ░█░██ 
              ││░█  
               │ │  
                 │  
EEEEEEEEEEEEEEEEEEEE
                    
                    
                    
                    
                    
XXXXXXXXXXXXXXXXXXXX
0   0   0   0   1   
```
**Audit:**
- Limit entry was touched in post-signal window: False
- AI POI level 24662.93 lies within SIGNAL candle [24779.05,24815.95]: False

## 3. NAS100 2026-01-22 14:45:00 ny LONG → WIN (+1.50R)
- Entry 25435.05 SL 25341.05 TP 25576.05
- bias_source: H4+H1_consensus
- AI bias: bullish (high)
- AI H1 POI: OB @ 25410.4 zone=discount causing=BOS
  - Explanation: _Nearest unmitigated H1 OB at 25435.05-25385.75 (touches=2; downstream gate will evaluate) caused by BOS at 25460.55 on 2026-01-22T10:00._
- AI sweep: asian_high @ 25573.55 quality=messy
```text
  high=25597.3500  low=25341.0500  span=256.3000
            S   █░█░
│TTTT│TTTTTTTTT│█░█░
░░││││││    ││█░█│ ░
│░█░██░░││█████░█  ░
  │   │░░░█│││ │   ░
         │         ░
                   ░
                   │
                   │
                    
EEEEEEEEEEEEEEEEEEEE
                    
                    
                    
                    
                    
                    
XXXXXXXXXXXXXXXXXXXX
1   1   1   1   1   
```
**Audit:**
- Limit entry was touched in post-signal window: False
- AI POI level 25410.4 lies within SIGNAL candle [25534.25,25554.15]: False

## 4. XAUUSD 2026-04-06 10:00:00 london LONG → WIN (+1.50R)
- Entry 4658.8 SL 4643.14 TP 4682.29
- bias_source: H4+H1_consensus
- AI bias: bullish (high)
- AI H1 POI: OB @ 4664.79 zone=discount causing=BOS
  - Explanation: _Nearest unmitigated H1 bullish OB at 4678.46-4651.11 (midpoint 4664.79) caused by BOS at 2026-04-06T08:00; price is currently retesting this zone._
- AI sweep: equal_highs / asian_high @ 4678.46 quality=clean
```text
  high=4697.9500  low=4639.7400  span=58.2100
            S    ││█
                │███
               │███ 
               ██│  
TTTTTTTTTTTTTTT█│TTT
     │         █│   
    ││         █    
    █░         █    
    █░││   │   █    
    █░░│   █░ ██    
    █ ░░█░ █░ █│    
EEE██EE░█░│█░E█EEEEE
   █   ░█│░█░│█     
  │█   ░█││ ░░█     
│ ██    │   ││      
███     │    │      
█││XXXXX│XXXXXXXXXXX
│                   
0   0   0   1   1   
```
**Audit:**
- Limit entry was touched in post-signal window: True
- AI POI level 4664.79 lies within SIGNAL candle [4647.92,4666.52]: True

## 5. EURUSD 2026-02-04 07:00:00 london LONG → WIN (+0.00R)
- Entry 1.18 SL 1.18 TP 1.18
- bias_source: H4+H1_consensus
- AI bias: bullish (high)
- AI H1 POI: OB @ 1.18 zone=discount causing=BOS
  - Explanation: _Single unmitigated H1 bullish OB at 1.18 (touches=1) formed 2026-02-04T02:00, caused by BOS at that level._
- AI sweep: PDH / session_high @ 1.18 quality=clean
```text
  high=1.1836  low=1.1800  span=0.0036
           █S│█░█░│ 
          │█░██░█░░│
│       █░│█ │ │ │░░
│      │█░░█       ░
█░│░   ██           
│░█░█░░█│           
 ││░█│░█            
   │ ││             
   │                
                    
                    
                    
                    
                    
                    
                    
                    
EEEEEEEEEEEEEEEEEEEE
0   0   0   0   0   
```
**Audit:**
- Limit entry was touched in post-signal window: False
- AI POI level 1.18 lies within SIGNAL candle [1.1833,1.18357]: False

## 6. NAS100 2026-03-11 13:30:00 ny LONG → WIN (+1.50R)
- Entry 24501.23 SL 24261.23 TP 24861.23
- bias_source: H4+H1_consensus
- AI bias: bullish (high)
- AI H1 POI: OB @ 24395.88 zone=discount causing=BOS
  - Explanation: _Nearest unmitigated H1 bullish OB at 24501.23–24290.53 (touches=1) formed prior to BOS at 24470.85; second OB at 24688.33–24552.33 has touches=2 and will be rejected downstream._
- AI sweep: asian_low @ 24873.85 quality=clean
```text
  high=25017.4500  low=24261.2300  span=756.2200
░██░░       S██░    
░█││░░░│  ███  ░░░██
││   │░░░░█      ░█│
TTTTTTTTT░█TTTTTTTTT
                    
                    
                    
                    
                    
                    
                    
EEEEEEEEEEEEEEEEEEEE
                    
                    
                    
                    
                    
XXXXXXXXXXXXXXXXXXXX
1   1   1   1   1   
```
**Audit:**
- Limit entry was touched in post-signal window: False
- AI POI level 24395.88 lies within SIGNAL candle [24944.55,24994.05]: False

## 7. EURUSD 2026-01-23 13:30:00 ny LONG → WIN (+1.50R)
- Entry 1.16 SL 1.157 TP 1.1645
- bias_source: H4+H1_consensus
- AI bias: bullish (high)
- AI H1 POI: OB @ 1.16 zone=discount causing=BOS
  - Explanation: _Nearest unmitigated H1 OB with touches=1 is the bullish OB at 1.16-1.16 formed 2026-01-16T23:00, caused by BOS._
- AI sweep: asian_low @ 1.17 quality=clean
```text
  high=1.1747  low=1.1570  span=0.0177
█░░█░░     █S██████░
█ ││ ░░█░████││     
                    
                    
                    
                    
                    
                    
                    
TTTTTTTTTTTTTTTTTTTT
                    
                    
                    
                    
EEEEEEEEEEEEEEEEEEEE
                    
                    
XXXXXXXXXXXXXXXXXXXX
1   1   1   1   1   
```
**Audit:**
- Limit entry was touched in post-signal window: False
- AI POI level 1.16 lies within SIGNAL candle [1.17357,1.17389]: False

## 8. XAUUSD 2026-03-24 13:15:00 ny LONG → WIN (+1.50R)
- Entry 4398.7 SL 4319.64 TP 4517.29
- bias_source: H4+H1_consensus
- AI bias: bullish (high)
- AI H1 POI: OB @ 4405.92 zone=discount causing=BOS
  - Explanation: _Unmitigated bullish H1 OB at 4420.74-4391.10 (midpoint 4405.92) formed at 11:00 UTC, caused by the BOS at 4433.07; price is currently retesting this zone._
- AI sweep: session_high @ 4433.07 quality=messy
```text
  high=4517.2900  low=4319.6400  span=197.6500
TTTTTTTTTTTTSTTTTTTT
                    
                    
                    
                    
                    
              █░    
░ │       █░░██░ ││ 
░ █░░ │││██│░█│░░█░█
░░█│░│█░██│    │││░█
E│EE░██░█EEEEEE│EE│E
               │    
               │    
                    
                    
                    
                    
XXXXXXXXXXXXXXXXXXXX
1   1   1   1   1   
```
**Audit:**
- Limit entry was touched in post-signal window: True
- AI POI level 4405.92 lies within SIGNAL candle [4421.24,4432.41]: False

## 9. XAUUSD 2026-01-20 16:00:00 ny LONG → WIN (+1.50R)
- Entry 4727.61 SL 4715.35 TP 4745.99
- bias_source: H4+H1_consensus
- AI bias: bullish (high)
- AI H1 POI: OB @ 4728.48 zone=premium causing=BOS
  - Explanation: _Nearest unmitigated H1 OB at 4732.98-4723.98 (midpoint 4728.48) caused by BOS at 2026-01-20T14:00; price is currently retesting this zone from above._
- AI sweep: asian_high @ 4735.18 quality=clean
```text
  high=4750.7700  low=4715.3500  span=35.4200
            S█░     
            │█░ │   
TTTTTTTTTTTT│█░T█░TT
            │█░ █░  
            ██░██░  
            █│░█│░ │
           ██ ░│ ░ █
   │       █│ ││ ░│█
  ██░      █│ ││ ░██
  █│░░    │█  │  ░█│
││█ │░│││ ██  │  ░█│
░██EE░██░│█│EEEEE░█E
││    │ ░│█      ░█ 
│       ░░█      ││ 
│        ░█         
         ░█         
         ││         
XXXXXXXXXX│XXXXXXXXX
1   1   1   1   1   
```
**Audit:**
- Limit entry was touched in post-signal window: True
- AI POI level 4728.48 lies within SIGNAL candle [4732.24,4748.42]: False

## 10. XAUUSD 2026-03-31 14:00:00 ny LONG → WIN (+1.50R)
- Entry 4551.25 SL 4524.37 TP 4591.63
- bias_source: H4+H1_consensus
- AI bias: bullish (high)
- AI H1 POI: OB @ 4543.07 zone=discount causing=BOS
  - Explanation: _Nearest unmitigated H1 bullish OB at 4561.59-4529.37 (body 4555.37-4546.77) created by BOS at 13:00, midpoint 4545.57, price currently retesting after london_low sweep at 4529.37._
- AI sweep: london_low / session_low @ 4529.37 quality=clean
```text
  high=4597.3900  low=4524.3700  span=73.0200
            S   │   
TTTTTTTTTTTTTT█░│T│T
              █░│ │ 
             │█░░│││
             │█│░█░░
│█░││        ██ ░█ ░
│█░░░░       █│  │ │
██ ││░      │█      
│   │░░││█░ │█      
      ░░██░ │█      
EEEEEE││EE░│██EEEEEE
      │   ░██│      
          ░█│       
          ░█│       
          │         
          │         
                    
XXXXXXXXXXXXXXXXXXXX
1   1   1   1   1   
```
**Audit:**
- Limit entry was touched in post-signal window: True
- AI POI level 4543.07 lies within SIGNAL candle [4540.93,4563.7]: True

## 11. EURUSD 2026-01-30 13:00:00 ny LONG → WIN (+1.67R)
- Entry 1.19 SL 1.1897 TP 1.1905
- bias_source: H4+H1_consensus
- AI bias: bullish (high)
- AI H1 POI: OB @ 1.19 zone=discount causing=BOS
  - Explanation: _Nearest unmitigated H1 bullish OB at 1.19-1.19 with touches=1 (2026-01-27T10:00), caused by bullish BOS; preferred over the touches=2 OB at 2026-01-30T11:00._
- AI sweep: pdl / session_low @ 1.19 quality=clean
```text
  high=1.1955  low=1.1897  span=0.0058
            S   █░  
               ██░  
               █│░  
││             █ ░░ 
█░  │         │█  ░ 
█░│││        ███  ░ 
 ░░█░       ███│  ░ 
  ││░│      █│    ░ 
  │ ░░│    │█│    ░░
  │  ░│    ██      ░
     ░░  █░█│      ░
      ░░██░█       │
       ░█           
       ░█           
TTTTTTT││TTTTTTTTTTT
       │            
EEEEEEE│EEEEEEEEEEEE
XXXXXXXXXXXXXXXXXXXX
1   1   1   1   1   
```
**Audit:**
- Limit entry was touched in post-signal window: False
- AI POI level 1.19 lies within SIGNAL candle [1.1920600000000001,1.19343]: False

## 12. NAS100 2026-02-10 08:00:00 london LONG → WIN (+1.50R)
- Entry 25069.95 SL 24958.85 TP 25236.6
- bias_source: H4+H1_consensus
- AI bias: bullish (high)
- AI H1 POI: OB @ 25029.4 zone=discount causing=BOS
  - Explanation: _Nearest unmitigated H1 bullish OB at 25069.95-24988.85 (touches=2) caused by BOS at 2026-02-09T15:00; preferred lowest-touch OB is the 25069.95-24988.85 zone._
- AI sweep: session_low / london_low @ 25204.65 quality=clean
```text
  high=25270.8500  low=24958.8500  span=312.0000
       █░ │█S     │█
TTTTT│██░░██░░│T████
░│││███  ░█  ░░██│  
░████         ░█    
││                  
                    
                    
                    
                    
                    
EEEEEEEEEEEEEEEEEEEE
                    
                    
                    
                    
                    
                    
XXXXXXXXXXXXXXXXXXXX
0   0   0   0   0   
```
**Audit:**
- Limit entry was touched in post-signal window: False
- AI POI level 25029.4 lies within SIGNAL candle [25239.15,25266.63]: False

## 13. XAUUSD 2026-01-21 15:00:00 ny LONG → LOSS (-1.00R)
- Entry 4869.07 SL 4855.09 TP 4890.04
- bias_source: H4+H1_consensus
- AI bias: bullish (high)
- AI H1 POI: OB @ 4863.18 zone=discount causing=BOS
  - Explanation: _Nearest unmitigated H1 OB at 4870.77-4855.59 (midpoint 4863.18) caused by BOS at 2026-01-21T14:00 with displaced ratio 1.5._
- AI sweep: asian_high @ 4871.33 quality=clean
```text
  high=4890.0400  low=4839.4900  span=50.5500
TTTTTTTTTTTTSTTTTTTT
                    
                    
              │█░   
              ██░   
              █│░ │ 
     │    │ ││█│░ │ 
│EE│E█░█░E││█░█E░E│E
█░█░██░█░██░█│  ░││ 
█░█░█ ░█░█ │││  ░██░
█││    │ │ ││   ░█│░
XXXXXXX│X│X│XXXX░█│░
                ░█│░
                ░█││
                ░█ │
                ░█  
                ││  
                │   
1   1   1   1   1   
```
**Audit:**
- Limit entry was touched in post-signal window: True
- AI POI level 4863.18 lies within SIGNAL candle [4857.75,4871.33]: True

## 14. NAS100 2026-03-18 13:30:00 ny LONG → LOSS (-1.00R)
- Entry 24795.35 SL 24754.35 TP 24856.85
- bias_source: H4+H1_consensus
- AI bias: bullish (high)
- AI H1 POI: OB @ 24781.05 zone=discount causing=BOS
  - Explanation: _Nearest unmitigated H1 bullish OB at 24795.35–24766.75 (touches=1), caused by BOS at 2026-03-18T02:00; midpoint 24781.05 sits below current price in discount relative to recent impulse._
- AI sweep: asian_high @ 24961.35 quality=messy
```text
  high=24969.0500  low=24754.3500  span=214.7000
  │    │█░ █S       
█░█░│││██░██░░ │    
│░█░██░█ ░█  ░█░    
 ││ │ ░█     ││░│   
              │░█░  
               ░█░  
               ░█░░ 
               ░█ ░ 
TTTTTTTTTTTTTTTTTT░T
                  ░ 
                  ░ 
                  ░░
                  │░
EEEEEEEEEEEEEEEEEE│░
                   │
                   │
                    
XXXXXXXXXXXXXXXXXXXX
1   1   1   1   1   
```
**Audit:**
- Limit entry was touched in post-signal window: True
- AI POI level 24781.05 lies within SIGNAL candle [24947.05,24967.35]: False

## 15. NAS100 2026-01-20 09:45:00 london LONG → LOSS (-1.00R)
- Entry 25258.75 SL 25073.65 TP 25536.25
- bias_source: H4+H1_consensus
- AI bias: bullish (high)
- AI H1 POI: OB @ 25236.1 zone=premium causing=CHoCH
  - Explanation: _Nearest unmitigated H1 bearish OB at 25258.75-25213.45 (touches=1), formed on the CHoCH at 2026-01-20T07:00; price has pulled back into this zone after the sweep series._
- AI sweep: asian_low @ 25103.65 quality=clean
```text
  high=25536.2500  low=24947.1500  span=589.1000
TTTTTTTTTTTTSTTTTTTT
                    
                    
                    
                    
                    
                    
                    
░██░░░EEEEEEEEEEEEEE
│││  ░░             
      ░│█░          
      ░░█░█░█░      
       ││ │ █░░     
XXXXXXXXXXXXX│░░││XX
               ░█░░ 
               │ │░░
                  │░
                   │
0   0   0   0   1   
```
**Audit:**
- Limit entry was touched in post-signal window: False
- AI POI level 25236.1 lies within SIGNAL candle [25104.35,25140.85]: False

## 16. XAUUSD 2026-01-15 13:15:00 ny LONG → LOSS (-1.00R)
- Entry 4618.93 SL 4597.79 TP 4650.62
- bias_source: H4+H1_consensus
- AI bias: bullish (high)
- AI H1 POI: OB @ 4606.33 zone=discount causing=BOS
  - Explanation: _Nearest unmitigated H1 bullish OB at 4613.48-4599.17 (midpoint 4606.33) caused by BOS at 2026-01-15T09:00; price is currently retesting this zone from above._
- AI sweep: session_high @ 4621.45 quality=clean
```text
  high=4650.6200  low=4597.7900  span=52.8300
TTTTTTTTTTTTSTTTTTTT
                    
                    
                    
                    
                    
                    
                    
             │      
          █░││││    
EEEEEEEEE██░█░█░██░E
       ││█    │░█│░░
     │█░░█        │░
     ██│           │
│█░░██              
░█│░█│              
││ │                
XXXXXXXXXXXXXXXXXXXX
1   1   1   1   1   
```
**Audit:**
- Limit entry was touched in post-signal window: True
- AI POI level 4606.33 lies within SIGNAL candle [4617.21,4620.44]: False

## 17. XAUUSD 2026-03-10 16:00:00 ny LONG → LOSS (-1.00R)
- Entry 5200.47 SL 5162.26 TP 5257.78
- bias_source: D1
- AI bias: bullish (high)
- AI H1 POI: OB @ 5183.45 zone=premium causing=BOS
  - Explanation: _Nearest unmitigated H1 OB at 5171.67-5191.67 (mid 5183.45) caused by BOS at 2026-03-10T14:00; price currently retesting this zone from above._
- AI sweep: asian_high @ 5202.32 quality=clean
```text
  high=5257.7800  low=5156.3500  span=101.4300
TTTTTTTTTTTTSTTTTTTT
                    
                    
                    
             │      
             ││     
             █░     
             █░│ │││
             █░░░█░█
EEEEEEEEEEEE██E│░█│E
            █  │░█  
    █░     ██   │   
░░  █░░  │██│   │   
│░│██│░█░██         
 ░░█  ░█░█          
  │     ││          
XX│XXXXX│XXXXXXXXXXX
  │                 
1   1   1   1   1   
```
**Audit:**
- Limit entry was touched in post-signal window: True
- AI POI level 5183.45 lies within SIGNAL candle [5185.89,5202.32]: False

## 18. NAS100 2026-03-23 09:30:00 london SHORT → LOSS (-1.00R)
- Entry 23734.25 SL 23821.75 TP 23603.0
- bias_source: H4_primary
- AI bias: bearish (medium)
- AI H1 POI: OB @ 23763.2 zone=premium causing=CHoCH
  - Explanation: _Nearest unmitigated H1 bearish OB at 23792.15-23734.25 (touches=2) caused by CHoCH at 2026-03-23T07:00; price currently retesting this zone from below._
- AI sweep: asian_low / PDL @ 23660.05 quality=clean
```text
  high=23821.7500  low=23561.8500  span=259.9000
XXXXXX││XXXXSXXXXXXX
    ││█░            
░│ █░██░│           
░░ █░█ ░░█░         
 ░██    ░█░         
E░█EEEEE││░│EEEEEEEE
        ││░░░      │
          ││░ │   █░
            ░ ││  █░
            ░│█░  █│
            ░░█░ │█ 
             ░█░ │█ 
             ││░███ 
             ││░█│  
TTTTTTTTTTTTTTT░█TTT
               ░█   
               │    
               │    
0   0   0   0   1   
```
**Audit:**
- Limit entry was touched in post-signal window: False
- AI POI level 23763.2 lies within SIGNAL candle [23660.05,23716.85]: False

## 19. XAUUSD 2026-02-20 15:00:00 ny LONG → LOSS (-1.00R)
- Entry 5042.42 SL 5007.0 TP 5095.49
- bias_source: H4+H1_consensus
- AI bias: bullish (high)
- AI H1 POI: OB @ 5025.13 zone=discount causing=BOS
  - Explanation: _Nearest unmitigated H1 OB at 5034.75-5015.50 (body 5034.58-5017.33) caused by bullish BOS at 2026-02-20T13:00; midpoint 5025.13 sits below current price after the 15:00 BOS displacement._
- AI sweep: asian_high @ 5036.95 quality=clean
```text
  high=5095.4900  low=5007.0000  span=88.4900
TTTTTTTTTTTTSTTTTTTT
                    
                    
                    
                    
                    
                   │
                  │█
                  ██
               │░│█│
EE│EEEEEEEEEEEE█░░█E
  ██░ │        █│ │ 
││█│░░░│    │███    
░██│ │░░││█░██│     
│     │░█░█│  │     
       ░█░█         
         ░│         
XXXXXXXXXX│XXXXXXXXX
1   1   1   1   1   
```
**Audit:**
- Limit entry was touched in post-signal window: True
- AI POI level 5025.13 lies within SIGNAL candle [5023.59,5028.64]: True

## 20. NAS100 2026-04-10 15:00:00 ny LONG → LOSS (-1.00R)
- Entry 25135.55 SL 25037.85 TP 25282.4
- bias_source: H4+H1_consensus
- AI bias: bullish (high)
- AI H1 POI: OB @ 25115.95 zone=premium causing=BOS
  - Explanation: _Nearest unmitigated H1 OB at 25135.55-25096.35 (touches=1) created by BOS at 2026-04-10T14:00; entry at ob_high=25135.55._
- AI sweep: PDH @ 25096.25 quality=clean
```text
  high=25282.4000  low=25037.8500  span=244.5500
TTTTTTTTTTTTSTTTTTTT
                    
                    
                    
                    
              │   │ 
              │   ││
              │   ││
             ││││░█░
             █░░█░█│
EEEEEEEE│█░EE█│░││││
     │ │██░░██      
 │ ││█░██  ░█│      
 │ █░█│             
 █░█░█              
│█│                 
██                  
XXXXXXXXXXXXXXXXXXXX
1   1   1   1   1   
```
**Audit:**
- Limit entry was touched in post-signal window: True
- AI POI level 25115.95 lies within SIGNAL candle [25098.15,25117.35]: True
