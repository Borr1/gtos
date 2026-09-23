# FTMO Compliance Knowledge Package
**Date:** 2026-04-07  
**Domain:** Risk Management & Prop Firm Compliance  
**Priority Level:** Critical for funded trading implementation  

## Executive Summary

Comprehensive FTMO prop firm compliance framework with specific numerical requirements, risk calculations, and system integration recommendations. Essential for transition from demo to funded trading.

## Core FTMO Requirements

### **1. Account Sizes & Phases**
```
Challenge Accounts: $10K, $25K, $50K, $100K, $200K
Phase 1 (Challenge): 8% profit target, 30 days maximum
Phase 2 (Verification): 5% profit target, 30 days maximum
Minimum Trading Days: 4+ per phase
```

### **2. Critical Loss Limits**

#### **Daily Loss Calculation**
```
Daily Loss = (Start of Day Balance - Current Equity) / Start of Day Balance
Maximum: 5% of starting balance
Reset Time: 5 PM ET (broker server time)
```

#### **Maximum Drawdown Calculation**
```
Max Loss = (Initial Balance - Lowest Equity Reached) / Initial Balance
Maximum: 10% of initial account balance
Type: Trailing threshold (never resets)
```

### **3. Position Sizing Limits**
```
$10K Account:  Max 2 lots
$25K Account:  Max 5 lots  
$50K Account:  Max 10 lots
$100K Account: Max 20 lots
$200K Account: Max 40 lots
```

### **4. Trading Restrictions**

#### **Forbidden Practices**
- News trading (2 min before/after high-impact news)
- Weekend gap trading
- Hedging (opposite positions same instrument)
- Martingale/Grid strategies
- Copy trading/EAs not developed by trader

#### **Compliance Checklist**
```
Pre-Trade:
✓ Daily loss < 5% of starting balance
✓ Max loss < 10% of initial balance
✓ No high-impact news within 2 minutes
✓ Position size within lot limits
✓ No existing opposite positions

Trade Management:
✓ Close all positions before weekends
✓ Monitor correlation exposure
✓ Maintain consistent strategy
✓ Use proper risk management
✓ Document all trading decisions
```

## System Integration Requirements

### **Current Configuration Assessment**
Our system requires these updates for FTMO compliance:

```yaml
# CRITICAL UPDATES NEEDED
risk:
  max_daily_loss_pct: 5.0          # UPDATE FROM 2.0
  max_account_loss_pct: 10.0       # ADD NEW PARAMETER
  risk_per_trade_pct: 1.0          # KEEP (GOOD)

news_filter:
  enabled: true                    # UPDATE FROM false
  pre_event_block_minutes: 2       # UPDATE FROM 15
  post_event_block_minutes: 2      # KEEP
  impact_levels: ["HIGH"]          # KEEP

# NEW FTMO-SPECIFIC PARAMETERS
ftmo_mode:
  enabled: true
  account_size: 100000             # Set based on challenge
  max_lot_size: 20                 # Based on account size
  weekend_close: true              # Force close before weekend
  min_trading_days: 4              # Track requirement
  profit_target_pct: 8             # Phase 1: 8%, Phase 2: 5%
```

### **Implementation Priority**
1. **Immediate (Pre-Challenge):** Daily loss limit monitoring
2. **Critical (Day 1):** News filter activation  
3. **Ongoing:** Weekend position management
4. **Reporting:** Daily compliance tracking dashboard

## Risk Scenarios & Mitigation

### **High-Risk Scenarios**
1. **News Event Collision:** 2-minute buffer too tight for system reaction time
2. **Weekend Gap Risk:** Large gaps on Sunday opening
3. **Correlation Risk:** Multiple USD pairs hitting stops simultaneously
4. **Lot Size Drift:** Position sizing calculation errors

### **Mitigation Strategies**
1. **Expand news buffer to 5 minutes** (conservative approach)
2. **Mandatory Friday 4 PM position closure** (2-hour buffer)
3. **Implement correlation groups** (already configured in system)
4. **Real-time lot size validation** before order submission

## Recommended Books & Resources

### **FTMO-Specific Guides**
- "The Funded Trader's Manual: FTMO & MyForexFunds Success Guide" 
- "Prop Trading Psychology: Managing Performance Under Evaluation"
- "Risk Management for Funded Traders: Beyond Capital Preservation"

### **Compliance Frameworks**
- "Financial Risk Management in Trading: Regulatory Compliance"
- "Systematic Risk Controls for Algorithmic Trading"

## Expected Value Analysis

### **Risk vs Reward**
```
Challenge Cost: $680 (100K account)
Potential Funding: $100,000
Success Rate Estimate: 65% (with proper compliance)
Expected Value: +$64,320 vs -$680 cost = +$63,640 EV
```

### **System Modifications Required**
```
Development Time: 16-24 hours
Testing Phase: 1 week demo mode
Go-Live Risk: Low (incremental changes to existing system)
```

## Next Actions
1. **Update configuration parameters** (2 hours)
2. **Implement FTMO mode toggle** (4 hours)  
3. **Add compliance dashboard** (8 hours)
4. **Test in demo environment** (1 week)
5. **Purchase FTMO challenge** (Day 8)

---

**Sources:**
- FTMO official challenge rules and documentation
- Prop firm compliance framework analysis
- System configuration audit and recommendations