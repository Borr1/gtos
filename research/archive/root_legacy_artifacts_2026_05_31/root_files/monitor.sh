#!/bin/bash
# Interactive Trading System Monitor
# Usage: bash monitor.sh

cd ~/Documents/ai-trading-agent

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

show_dashboard() {
    clear
    echo -e "${BOLD}========================================================"
    echo "          TRADING SYSTEM MONITOR"
    echo -e "========================================================${NC}"
    echo ""

    local utc=$(date -u +"%H:%M:%S")
    local kl=$(date +"%H:%M:%S")
    local day=$(date -u +"%A %Y-%m-%d")
    echo -e "  ${DIM}$day${NC}  |  KL: ${BOLD}$kl${NC}  |  UTC: $utc"
    echo ""

    local count=0
    local proclist
    proclist=$(MSYS_NO_PATHCONV=1 /c/Windows/System32/tasklist.exe 2>/dev/null)
    for lf in knowledge_base/meta/.orchestrator_*.lock; do
        [ -f "$lf" ] || continue
        local lpid=$(grep -ao '"pid": [0-9]*' "$lf" | grep -o '[0-9]*')
        if [ -n "$lpid" ] && echo "$proclist" | grep -q " ${lpid} "; then
            count=$((count + 1))
        fi
    done
    if [ "$count" -eq 7 ]; then
        echo -e "  Processes: ${GREEN}$count/7 OK${NC}"
    elif [ "$count" -eq 0 ]; then
        echo -e "  Processes: ${RED}$count/7 ALL DOWN${NC}"
    else
        echo -e "  Processes: ${YELLOW}$count/7 WARNING${NC}"
    fi
    echo ""

    # 2026-04-27 session 43: surface dormant + live_monitor data
    if [ -f pipeline_state/dormant_state.json ]; then
        local dsym=$(grep -o '"symbol": *"[^"]*"' pipeline_state/dormant_state.json | head -1 | sed 's/.*"\([^"]*\)"/\1/')
        local dreason=$(grep -o '"trigger_reason": *"[^"]*"' pipeline_state/dormant_state.json | head -1 | sed 's/.*"\([^"]*\)"/\1/')
        echo -e "  ${RED}${BOLD}!! DORMANT: $dsym ($dreason) — clear with [c]${NC}"
        echo ""
    fi

    if [ -f shadow_logs/live_monitor.jsonl ]; then
        local mon_age=$(($(date -u +%s) - $(stat -c %Y shadow_logs/live_monitor.jsonl 2>/dev/null)))
        if [ "$mon_age" -lt 1800 ]; then
            echo -e "  ${DIM}live_monitor.jsonl: ${mon_age}s old${NC}"
        else
            echo -e "  ${YELLOW}live_monitor.jsonl: ${mon_age}s old (stale)${NC}"
        fi
    fi
    if [ -f shadow_logs/live_monitor_alerts.jsonl ]; then
        local alert_count=$(wc -l < shadow_logs/live_monitor_alerts.jsonl 2>/dev/null | tr -d ' ')
        if [ "$alert_count" -gt 0 ]; then
            echo -e "  ${YELLOW}Alerts: $alert_count total — view with [a]${NC}"
        fi
    fi
    echo ""

    local i=1
    for f in logs/*.log; do
        local name=$(basename "$f" .log)
        local upper=$(echo "$name" | tr '[:lower:]' '[:upper:]')
        local last=$(grep -a "INFO" "$f" 2>/dev/null | tail -1)
        local msg=""
        local color="$NC"

        if echo "$last" | grep -q "Align score"; then
            msg=$(echo "$last" | sed 's/.*Align score/Align score/')
            color="$GREEN"
        elif echo "$last" | grep -q "Processing candle"; then
            msg=$(echo "$last" | sed 's/.*Processing/Processing/')
            color="$GREEN"
        elif echo "$last" | grep -q "Entering"; then
            msg=$(echo "$last" | sed 's/.*Entering/Entering/')
            color="$CYAN"
        elif echo "$last" | grep -q "Bootstrap complete\|New trading day"; then
            msg="Waiting for kill zone"
            color="$DIM"
        elif echo "$last" | grep -q "All kill zones complete"; then
            msg="Done for today"
            color="$DIM"
        elif echo "$last" | grep -q "CANDIDATE"; then
            msg="** CANDIDATE FOUND **"
            color="$YELLOW"
        elif echo "$last" | grep -q "trade_executed\|ENTRY"; then
            msg="** TRADE ACTIVE **"
            color="$YELLOW"
        else
            msg=$(echo "$last" | sed 's/.*\] //' | cut -c1-45)
        fi

        # Check errors
        local has_err=$(grep -a "ERROR" "$f" 2>/dev/null | tail -1)
        if [ -n "$has_err" ]; then
            local lt=$(grep -a "INFO" "$f" 2>/dev/null | tail -1 | cut -c1-19)
            local et=$(echo "$has_err" | cut -c1-19)
            if [[ "$et" > "$lt" ]] || [ -z "$lt" ]; then
                msg="!! ERROR !!"
                color="$RED"
            fi
        fi

        printf "  ${BOLD}[$i]${NC}  ${color}%-8s  %s${NC}\n" "$upper" "$msg"
        i=$((i + 1))
    done

    echo ""
    echo -e "  ---------------------------------------------------------"
    echo ""
    echo -e "  ${BOLD}[1-5]${NC}  Inspect instrument      ${BOLD}[6]${NC}  MT5 positions"
    echo -e "  ${BOLD}[7]${NC}    Errors only              ${BOLD}[8]${NC}  Trades/candidates"
    echo -e "  ${BOLD}[9]${NC}    Restart a process        ${BOLD}[0]${NC}  Kill all & exit"
    echo -e "  ${BOLD}[a]${NC}    Alerts                   ${BOLD}[c]${NC}  Clear dormant marker"
    echo -e "  ${BOLD}[r]${NC}    Refresh                  ${BOLD}[q]${NC}  Quit monitor"
    echo ""
}

show_alerts() {
    clear
    echo -e "${BOLD}=== Recent Alerts (last 20) ===${NC}"
    echo ""
    if [ ! -f shadow_logs/live_monitor_alerts.jsonl ]; then
        echo -e "  ${DIM}No alerts log found${NC}"
    else
        tail -20 shadow_logs/live_monitor_alerts.jsonl | /c/Python313/python -c "
import sys, json
for line in sys.stdin:
    line=line.strip()
    if not line: continue
    try:
        d = json.loads(line)
        sev = d.get('severity', '?')
        inst = d.get('instrument', '?')
        ts = d.get('ts_utc', '?')
        issue = d.get('issue', '?')
        interp = d.get('interpretation', '')
        print(f'[{sev}] {ts}  {inst}: {issue}')
        if interp:
            print(f'    -> {interp[:200]}')
        print()
    except Exception:
        print(f'PARSE_ERR: {line[:100]}')
" 2>/dev/null
    fi
    echo ""
    echo -e "${DIM}Press any key to return...${NC}"
    read -rsn1
}

clear_dormant() {
    clear
    echo -e "${BOLD}${RED}=== Clear Dormant Marker ===${NC}"
    echo ""
    if [ -f pipeline_state/dormant_state.json ]; then
        cat pipeline_state/dormant_state.json
        echo ""
        echo -e "${BOLD}Confirm clear? (y/n)${NC}"
        read -rsn1 key
        if [ "$key" = "y" ] || [ "$key" = "Y" ]; then
            rm pipeline_state/dormant_state.json
            echo -e "${GREEN}Cleared.${NC}"
            sleep 1
        fi
    else
        echo -e "  ${DIM}No dormant marker present${NC}"
        sleep 1
    fi
}

show_instrument() {
    local files=(logs/*.log)
    local f="${files[$1]}"
    local name=$(basename "$f" .log)
    local upper=$(echo "$name" | tr '[:lower:]' '[:upper:]')

    clear
    echo -e "${BOLD}=== $upper ===${NC}"
    echo ""

    local lines=$(wc -l < "$f" | tr -d ' ')
    echo -e "  Log: $lines lines"
    echo ""

    echo -e "${BOLD}  [1]${NC}  Last 30 lines"
    echo -e "${BOLD}  [2]${NC}  Full log"
    echo -e "${BOLD}  [3]${NC}  Errors only"
    echo -e "${BOLD}  [4]${NC}  Align scores"
    echo -e "${BOLD}  [5]${NC}  Candidates / trades"
    echo -e "${BOLD}  [6]${NC}  Live tail (Ctrl+C to stop)"
    echo -e "${BOLD}  [b]${NC}  Back"
    echo ""

    while true; do
        read -rsn1 key
        case $key in
            1)
                clear
                echo -e "${BOLD}=== $upper — Last 30 Lines ===${NC}"
                echo ""
                tail -30 "$f"
                echo ""
                echo -e "${DIM}Press any key...${NC}"
                read -rsn1
                show_instrument $1
                return
                ;;
            2)
                clear
                echo -e "${BOLD}=== $upper — Full Log ===${NC}"
                echo ""
                cat "$f"
                echo ""
                echo -e "${DIM}Press any key...${NC}"
                read -rsn1
                show_instrument $1
                return
                ;;
            3)
                clear
                echo -e "${BOLD}=== $upper — Errors ===${NC}"
                echo ""
                local errs=$(grep -ac "ERROR" "$f" 2>/dev/null)
                if [ "$errs" -gt 0 ]; then
                    grep -a "ERROR" "$f"
                else
                    echo "  No errors"
                fi
                echo ""
                echo -e "${DIM}Press any key...${NC}"
                read -rsn1
                show_instrument $1
                return
                ;;
            4)
                clear
                echo -e "${BOLD}=== $upper — Align Scores ===${NC}"
                echo ""
                local aligns=$(grep -a "Align score" "$f" 2>/dev/null)
                if [ -n "$aligns" ]; then
                    echo "$aligns"
                else
                    echo "  No align scores yet"
                fi
                echo ""
                echo -e "${DIM}Press any key...${NC}"
                read -rsn1
                show_instrument $1
                return
                ;;
            5)
                clear
                echo -e "${BOLD}=== $upper — Candidates & Trades ===${NC}"
                echo ""
                local cands=$(grep -ai "CANDIDATE\|trade_executed\|ENTRY\|open_trade\|NO_TRADE\|decision" "$f" 2>/dev/null)
                if [ -n "$cands" ]; then
                    echo "$cands"
                else
                    echo "  No candidates or trades yet"
                fi
                echo ""
                echo -e "${DIM}Press any key...${NC}"
                read -rsn1
                show_instrument $1
                return
                ;;
            6)
                clear
                echo -e "${BOLD}=== $upper — Live Tail (Ctrl+C to stop) ===${NC}"
                echo ""
                tail -f "$f"
                show_instrument $1
                return
                ;;
            b|B)
                return
                ;;
        esac
    done
}

show_mt5() {
    clear
    echo -e "${BOLD}=== MT5 Positions ===${NC}"
    echo ""
    /c/Python313/python -c "
import MetaTrader5 as mt5
mt5.initialize()
positions = mt5.positions_get()
if positions:
    for p in positions:
        print(f'  {p.symbol}  {\"BUY\" if p.type==0 else \"SELL\"}  vol={p.volume}  price={p.price_open}  SL={p.sl}  TP={p.tp}  profit={p.profit}')
else:
    print('  No open positions')
info = mt5.account_info()
print()
print(f'  Balance:  \${info.balance:,.2f}')
print(f'  Equity:   \${info.equity:,.2f}')
print(f'  Margin:   \${info.margin:,.2f}')
print(f'  Free:     \${info.margin_free:,.2f}')
mt5.shutdown()
" 2>/dev/null
    echo ""
    echo -e "${DIM}Press any key...${NC}"
    read -rsn1
}

show_errors() {
    clear
    echo -e "${BOLD}=== All Errors ===${NC}"
    echo ""
    local found=0
    for f in logs/*.log; do
        local name=$(basename "$f" .log)
        local upper=$(echo "$name" | tr '[:lower:]' '[:upper:]')
        local errs=$(grep -a "ERROR\|CRITICAL" "$f" 2>/dev/null)
        if [ -n "$errs" ]; then
            echo -e "  ${RED}--- $upper ---${NC}"
            echo "$errs"
            echo ""
            found=1
        fi
    done
    if [ "$found" -eq 0 ]; then
        echo -e "  ${GREEN}No errors across any instrument${NC}"
    fi
    echo ""
    echo -e "${DIM}Press any key...${NC}"
    read -rsn1
}

show_trades() {
    clear
    echo -e "${BOLD}=== Candidates & Trades ===${NC}"
    echo ""
    local found=0
    for f in logs/*.log; do
        local name=$(basename "$f" .log)
        local upper=$(echo "$name" | tr '[:lower:]' '[:upper:]')
        local hits=$(grep -ai "CANDIDATE\|trade_executed\|ENTRY\|open_trade" "$f" 2>/dev/null)
        if [ -n "$hits" ]; then
            echo -e "  ${YELLOW}--- $upper ---${NC}"
            echo "$hits"
            echo ""
            found=1
        fi
    done
    if [ "$found" -eq 0 ]; then
        echo "  No candidates or trades today (normal — system averages ~17/month)"
    fi
    echo ""
    echo -e "${DIM}Press any key...${NC}"
    read -rsn1
}

restart_process() {
    clear
    echo -e "${BOLD}=== Restart Process ===${NC}"
    echo ""
    local symbols=("GBPJPY" "GBPUSD" "US30_cash" "USDJPY" "XAUUSD" "XAGUSD" "NAS100")
    local lognames=("gbpjpy" "gbpusd" "us30" "usdjpy" "xauusd" "xagusd" "nas100")

    for i in 0 1 2 3 4 5 6; do
        echo -e "  ${BOLD}[$((i+1))]${NC}  ${symbols[$i]}"
    done
    echo -e "  ${BOLD}[b]${NC}  Back"
    echo ""

    read -rsn1 key
    case $key in
        [1-7])
            local idx=$((key - 1))
            local sym=${symbols[$idx]}
            local logf=${lognames[$idx]}
            echo ""
            echo "  Killing $sym..."

            # Get PID from lock file
            local pidfile="knowledge_base/meta/.orchestrator_${sym}.lock"
            if [ -f "$pidfile" ]; then
                local pid=$(grep -ao '"pid": [0-9]*' "$pidfile" | grep -o '[0-9]*')
                if [ -n "$pid" ]; then
                    MSYS_NO_PATHCONV=1 /c/Windows/System32/taskkill.exe /PID "$pid" /F >/dev/null 2>&1
                fi
            fi
            sleep 2

            echo "  Starting $sym..."
            nohup /c/Python313/python run_agent.py --symbol "$sym" --mode demo > "logs/${logf}.log" 2>&1 &
            sleep 5

            echo -e "  ${GREEN}$sym restarted${NC}"
            echo ""
            echo -e "${DIM}Press any key...${NC}"
            read -rsn1
            ;;
        b|B)
            return
            ;;
    esac
}

kill_all() {
    clear
    echo -e "${RED}${BOLD}=== KILL ALL PROCESSES ===${NC}"
    echo ""
    echo "  This will stop all 5 trading processes."
    echo ""
    echo -e "  ${BOLD}[y]${NC}  Yes, kill all"
    echo -e "  ${BOLD}[n]${NC}  No, go back"
    echo ""

    read -rsn1 key
    if [ "$key" = "y" ] || [ "$key" = "Y" ]; then
        for f in knowledge_base/meta/.orchestrator_*.lock; do
            local pid=$(grep -ao '"pid": [0-9]*' "$f" 2>/dev/null | grep -o '[0-9]*')
            if [ -n "$pid" ]; then
                MSYS_NO_PATHCONV=1 /c/Windows/System32/taskkill.exe /PID "$pid" /F >/dev/null 2>&1
                echo "  Killed PID $pid"
            fi
        done
        sleep 2
        local remaining=$(MSYS_NO_PATHCONV=1 /c/Windows/System32/tasklist.exe 2>/dev/null | grep -c python)
        echo ""
        echo "  Remaining processes: $remaining"
        echo ""
        echo -e "${DIM}Press any key to exit...${NC}"
        read -rsn1
        exit 0
    fi
}

# === Main loop ===
while true; do
    show_dashboard
    read -rsn1 key
    case $key in
        1) show_instrument 0 ;;
        2) show_instrument 1 ;;
        3) show_instrument 2 ;;
        4) show_instrument 3 ;;
        5) show_instrument 4 ;;
        6) show_mt5 ;;
        7) show_errors ;;
        8) show_trades ;;
        9) restart_process ;;
        0) kill_all ;;
        a|A) show_alerts ;;
        c|C) clear_dormant ;;
        r|R) continue ;;
        q|Q) clear; exit 0 ;;
    esac
done
