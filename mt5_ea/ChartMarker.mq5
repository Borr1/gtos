//+------------------------------------------------------------------+
//| ChartMarker.mq5 — v2.0                                            |
//| Reads agent_signals_{SYMBOL}.jsonl from the GTOS Python agent     |
//| and renders a rich, at-a-glance view of every decision +          |
//| live-trade state on the chart.                                    |
//|                                                                   |
//| Attach to each instrument chart. Polls the signal file every      |
//| PollSeconds.                                                      |
//+------------------------------------------------------------------+
#property copyright "GoldAgent"
#property version   "2.00"
#property strict

// ===================================================================
//  Signal file schema (one JSON line per event)
//  ----------------------------------------------------------------
//  Required fields (all events):
//    "time"     : ISO-8601 UTC timestamp ("2026-04-27T08:15:00")
//    "decision" : enum  (NO_TRADE | CANDIDATE | EXECUTED | REJECTED |
//                        BLOCKED_CALENDAR | LIMIT_PLACED | LIMIT_FILLED |
//                        EXECUTION_FAILED | EMERGENCY_STOP | ...)
//    "detail"   : free-text human description (≤80 chars)
//    "price"    : double (chart price at event time)
//
//  Optional fields (gracefully skipped when absent):
//    "trade_id"    : string — links open / close events of one trade
//    "direction"   : "LONG" | "SHORT"
//    "framework"   : "ob_retest" | "fvg_fill" | "breaker_re_entry"
//    "grade"       : "A+" | "A" | "B" | "C"
//    "confidence"  : int 0-100
//    "align"       : alignment-label string (M15/H1/H4/D1)
//    "kill_zone"   : "london" | "ny" | "tokyo" | ""
//    "sl"          : stop-loss price
//    "tp1"/"tp2"/"tp3" : take-profit prices
//    "lots"        : volume on EXECUTED
//    "risk_pct"    : effective risk % on EXECUTED
//    "realized_r"  : double — on close events
//    "exit_type"   : enum  — on close events
//    "mfe_r"/"mae_r" : MFE/MAE in R-units on close events
//    "hold_min"    : hold time minutes on close events
//
//  Backward compatibility: an event lacking the optional fields still
//  renders correctly (parsed direction/grade/framework fall back to
//  detail-string keyword extraction).
// ===================================================================


// ====== INPUTS =====================================================

input group           "── Display ──"
input bool   ShowInfoPanel        = true;
input bool   ShowKZRegions        = true;
input bool   ShowSLTPLines        = true;
input bool   ShowTradeLifecycle   = true;
input bool   ShowGradeLabels      = true;
input bool   ShowAlignLabels      = true;

input group           "── Markers ──"
input bool   ShowExecuted         = true;
input bool   ShowCandidate        = true;
input bool   ShowRejected         = true;
input bool   ShowNoTrade          = true;
input bool   ShowLimitPlaced      = true;
input bool   ShowBlockedCalendar  = true;
input int    MaxNoTradeAgeBars    = 200;     // purge dots older than N bars

input group           "── Layout ──"
input int    PanelCornerCode      = 1;        // 0=top-left, 1=top-right, 2=bottom-left, 3=bottom-right
input int    PanelXOffset         = 12;
input int    PanelYOffset         = 22;
input int    PanelFontSize        = 9;
input string PanelFontName        = "Consolas";
input int    PollSeconds          = 5;

input group           "── Colours ──"
input color  ColLong              = clrLime;
input color  ColShort             = clrTomato;
input color  ColCandidate         = clrDodgerBlue;
input color  ColRejected          = clrOrangeRed;
input color  ColNoTrade           = clrDimGray;
input color  ColBlocked           = clrGold;
input color  ColLimitPlaced       = clrDeepSkyBlue;
input color  ColEmergency         = clrMagenta;
input color  ColTimeStop          = clrDarkOrange;
input color  ColBE                = clrKhaki;
input color  ColTP                = clrLimeGreen;
input color  ColSL                = clrCrimson;
input color  ColPanelBg           = clrBlack;
input color  ColPanelBorder       = clrDarkSlateGray;
input color  ColPanelText         = clrWhiteSmoke;
input color  ColPanelMuted        = clrDarkGray;
input color  ColPanelGood         = clrLimeGreen;
input color  ColPanelBad          = clrTomato;
input color  ColKZLondon          = clrDarkSlateBlue;
input color  ColKZNY              = clrDarkSlateGray;
input color  ColKZTokyo           = clrDarkOliveGreen;


// ====== OBJECT-NAMING DISCIPLINE ===================================
// All chart objects this EA creates start with this prefix so we can
// purge / count / clean up without touching foreign objects.
const string OBJ_PREFIX     = "GTOS_CM_";
const string PANEL_PREFIX   = OBJ_PREFIX + "panel_";
const string KZ_PREFIX      = OBJ_PREFIX + "kz_";
const string MARKER_PREFIX  = OBJ_PREFIX + "mk_";
const string LINE_PREFIX    = OBJ_PREFIX + "ln_";
const string LIFECYCLE_PREFIX = OBJ_PREFIX + "lc_";


// ====== STATE ======================================================
int     g_lastLineCount = 0;
string  g_signalFile    = "";
string  g_chartSymbol   = "";

// Distinguish initial file replay from new live events. During replay
// we render the historical markers but DO NOT update active-trade
// state or today's stats — those are reserved for live events only,
// otherwise stats from prior days bleed into "today" and a closed-out
// historical EXECUTED bootstraps a phantom active trade.
bool    g_replayPhase   = true;
datetime g_attachTime   = 0;

// Active trade (last EXECUTED whose close hasn't been seen yet)
struct ActiveTrade
{
   string   tradeId;
   datetime entryTime;
   double   entryPrice;
   double   sl;
   double   tp1;
   double   tp2;
   double   tp3;
   double   lots;
   string   direction;
   string   framework;
   string   grade;
   double   riskPct;
   bool     tp1Hit;
   bool     bePulled;
   bool     j46j49Active;
};
ActiveTrade g_active;
bool        g_hasActive   = false;

// Today's stats
datetime g_todayUtcDay     = 0;
int      g_tradesToday     = 0;
int      g_winsToday       = 0;
int      g_lossesToday     = 0;
double   g_totalRToday     = 0.0;
int      g_candidatesToday = 0;
int      g_rejectedToday   = 0;
int      g_noTradeToday    = 0;

// Last decision summary
string   g_lastDecision    = "—";
string   g_lastDetail      = "";
datetime g_lastDecisionTs  = 0;

// File modification check
datetime g_lastFileMtime   = 0;


// ====== UTILITY: ISO PARSER ========================================
datetime ParseISO(string iso)
{
   // "2026-04-07T08:15:00"  → datetime
   if(StringLen(iso) < 19) return 0;
   string d = StringSubstr(iso, 0, 10);  // YYYY-MM-DD
   string t = StringSubstr(iso, 11, 8);  // HH:MM:SS
   StringReplace(d, "-", ".");
   return StringToTime(d + " " + t);
}


// ====== UTILITY: JSON FIELD EXTRACTOR ==============================
//
// Replaces JSON \uXXXX escape sequences with the closest ASCII char so
// MT5 chart text doesn't render literal "—". Python's json.dumps
// emits non-ASCII as \uXXXX by default; rather than write a full UTF-16
// decoder in MQL5, we map the handful of typography characters the agent
// actually uses (em-dash, en-dash, smart quotes, bullets) to ASCII.
string DecodeJsonString(string s)
{
   if(StringFind(s, "\\u") < 0) return s;
   StringReplace(s, "\\u2014", "-");   // em-dash
   StringReplace(s, "\\u2013", "-");   // en-dash
   StringReplace(s, "\\u2026", "...");  // ellipsis
   StringReplace(s, "\\u2018", "'");
   StringReplace(s, "\\u2019", "'");
   StringReplace(s, "\\u201c", "\"");
   StringReplace(s, "\\u201d", "\"");
   StringReplace(s, "\\u00b7", "*");   // middle dot
   StringReplace(s, "\\u2022", "*");   // bullet
   // Embedded newline/tab escapes (rare but cheap to handle).
   StringReplace(s, "\\n", " ");
   StringReplace(s, "\\t", " ");
   StringReplace(s, "\\\"", "\"");
   StringReplace(s, "\\\\", "\\");
   return s;
}


string ExtractField(string json, string key)
{
   string search = "\"" + key + "\":";
   int pos = StringFind(json, search);
   if(pos < 0) return "";
   pos += StringLen(search);

   while(pos < StringLen(json) && StringGetCharacter(json, pos) == ' ') pos++;
   if(pos >= StringLen(json)) return "";

   if(StringGetCharacter(json, pos) == '"')
   {
      pos++;
      // Scan to the closing unescaped quote (handle backslash-escapes).
      int end = pos;
      while(end < StringLen(json))
      {
         int ch = StringGetCharacter(json, end);
         if(ch == '\\') { end += 2; continue; }
         if(ch == '"') break;
         end++;
      }
      if(end >= StringLen(json)) return "";
      return DecodeJsonString(StringSubstr(json, pos, end - pos));
   }
   int end2 = pos;
   while(end2 < StringLen(json))
   {
      int ch = StringGetCharacter(json, end2);
      if(ch == ',' || ch == '}' || ch == ' ' || ch == '\n' || ch == '\r') break;
      end2++;
   }
   return StringSubstr(json, pos, end2 - pos);
}


double ExtractDouble(string json, string key)
{
   string s = ExtractField(json, key);
   if(StringLen(s) == 0) return 0.0;
   return StringToDouble(s);
}


// ====== UTILITY: KEYWORD-PARSE FALLBACK ============================
//
// When the Python writer hasn't yet been enhanced to emit structured
// fields, we extract the same info from the free-text `detail`. This
// keeps the EA useful TODAY against the existing 4-field payload.
// ===================================================================
string ParseDirection(string detail)
{
   if(StringFind(detail, "LONG") >= 0)  return "LONG";
   if(StringFind(detail, "SHORT") >= 0) return "SHORT";
   return "";
}


string ParseFramework(string detail)
{
   if(StringFind(detail, "ob_retest") >= 0)        return "ob_retest";
   if(StringFind(detail, "fvg_fill") >= 0)         return "fvg_fill";
   if(StringFind(detail, "breaker_re_entry") >= 0) return "breaker_re_entry";
   if(StringFind(detail, "breaker") >= 0)          return "breaker_re_entry";
   if(StringFind(detail, "fvg") >= 0)              return "fvg_fill";
   return "";
}


string ParseGrade(string detail)
{
   // Look at the start of detail for "A+ "/"A "/"B "/"C "
   int p = StringFind(detail, "A+");
   if(p == 0)  return "A+";
   if(p == 0 || (p > 0 && StringGetCharacter(detail, p-1) == ' ')) return "A+";
   if(StringFind(detail, " A ") >= 0 || (StringLen(detail) > 1 && StringSubstr(detail, 0, 2) == "A "))
      return "A";
   if(StringFind(detail, " B ") >= 0 || (StringLen(detail) > 1 && StringSubstr(detail, 0, 2) == "B "))
      return "B";
   if(StringFind(detail, " C ") >= 0 || (StringLen(detail) > 1 && StringSubstr(detail, 0, 2) == "C "))
      return "C";
   return "";
}


string ResolveDirection(string explicit_dir, string detail)
{
   if(StringLen(explicit_dir) > 0) return explicit_dir;
   return ParseDirection(detail);
}


string ResolveFramework(string explicit_fw, string detail)
{
   if(StringLen(explicit_fw) > 0) return explicit_fw;
   return ParseFramework(detail);
}


string ResolveGrade(string explicit_g, string detail)
{
   if(StringLen(explicit_g) > 0) return explicit_g;
   return ParseGrade(detail);
}


color DirectionColour(string dir)
{
   if(dir == "LONG")  return ColLong;
   if(dir == "SHORT") return ColShort;
   return ColCandidate;
}


// ====== KILL-ZONE SCHEDULE (UTC) ===================================
//
// Mirrors CLAUDE.md "KILL ZONE SCHEDULE (UTC)" so the chart shows
// shaded regions for each KZ. Times are broker-clock-INDEPENDENT; the
// EA converts to broker time on each candle.
// ===================================================================
struct KZWindow
{
   string name;
   int    sh, sm;   // start hour/minute UTC
   int    eh, em;   // end hour/minute UTC
   color  clr;
};


int  g_kzCount = 0;
KZWindow g_kz[8];

void SetKZ(int idx, string nm, int sh, int sm, int eh, int em, color c)
{
   g_kz[idx].name = nm;
   g_kz[idx].sh = sh; g_kz[idx].sm = sm;
   g_kz[idx].eh = eh; g_kz[idx].em = em;
   g_kz[idx].clr = c;
}


void BuildKZSchedule(string sym)
{
   // Map the broker symbol to a canonical key.
   string s = sym;
   StringReplace(s, ".", "");
   StringReplace(s, "_", "");
   StringToUpper(s);

   g_kzCount = 0;

   // XAGUSD mirrors XAUUSD (per FN profile + agent_config metals).
   if(StringFind(s, "XAU") == 0 || StringFind(s, "XAG") == 0)
   {
      SetKZ(g_kzCount++, "London", 7, 0, 10, 30, ColKZLondon);
      SetKZ(g_kzCount++, "NY",    13, 0, 17,  0, ColKZNY);
   }
   else if(StringFind(s, "US30") == 0 || StringFind(s, "DJ30") == 0)
   {
      SetKZ(g_kzCount++, "London", 8, 0, 10, 30, ColKZLondon);
      SetKZ(g_kzCount++, "NY",    13, 30, 16, 0, ColKZNY);
   }
   else if(StringFind(s, "NAS") == 0 || StringFind(s, "NDX") == 0)
   {
      SetKZ(g_kzCount++, "London", 8, 0, 10, 30, ColKZLondon);
      SetKZ(g_kzCount++, "NY",    13, 30, 16, 0, ColKZNY);
   }
   else if(StringFind(s, "USDJPY") == 0 || StringFind(s, "GBPJPY") == 0)
   {
      SetKZ(g_kzCount++, "Tokyo",   0, 0,  3, 0, ColKZTokyo);
      SetKZ(g_kzCount++, "London",  7, 0,  9, 30, ColKZLondon);
      SetKZ(g_kzCount++, "NY",     13, 0, 15, 30, ColKZNY);
   }
   else if(StringFind(s, "GBPUSD") == 0 || StringFind(s, "EURUSD") == 0)
   {
      SetKZ(g_kzCount++, "London",  7, 0, 12,  0, ColKZLondon);
      SetKZ(g_kzCount++, "NY",     13, 0, 15, 30, ColKZNY);
   }
   else
   {
      // Default fallback — generic London + NY
      SetKZ(g_kzCount++, "London",  7, 0, 10, 30, ColKZLondon);
      SetKZ(g_kzCount++, "NY",     13, 0, 17,  0, ColKZNY);
   }
}


// Broker offset = TimeCurrent() - TimeGMT(). Positive when broker is
// ahead of UTC (e.g. UTC+3). Cached and refreshed once per poll.
int g_brokerOffsetSec = 0;


void RefreshBrokerOffset()
{
   g_brokerOffsetSec = (int)(TimeCurrent() - TimeGMT());
}


// CurrentKZName operates in REAL UTC, NOT broker time. The KZ schedule
// is anchored to UTC per CLAUDE.md. Always pass TimeGMT() in (or 0 to
// have the function pull TimeGMT() itself).
string CurrentKZName(datetime nowUtc)
{
   if(nowUtc == 0) nowUtc = TimeGMT();
   MqlDateTime mdt;
   TimeToStruct(nowUtc, mdt);
   int minute = mdt.hour * 60 + mdt.min;
   for(int i = 0; i < g_kzCount; i++)
   {
      int s = g_kz[i].sh * 60 + g_kz[i].sm;
      int e = g_kz[i].eh * 60 + g_kz[i].em;
      if(minute >= s && minute < e) return g_kz[i].name;
   }
   return "-";
}


// ====== KZ REGION DRAWING =========================================
//
// Draws KZ windows as a low-height bottom strip so they're a session-
// timing indicator without dimming the candles. Only renders for a
// small window around "now" (last 7d + next 1d) — saves chart-object
// budget and lets the user scroll back to a plain chart.
// ===================================================================
void DrawKZRegions()
{
   if(!ShowKZRegions) return;

   // Compute KZ window edges in REAL UTC (which is where the schedule
   // lives), then shift each onto the broker timeline (which is what
   // the chart x-axis uses) by adding g_brokerOffsetSec. Skipping this
   // shift draws the rectangles at the wrong x-position whenever the
   // broker is offset from UTC (redacted_account is UTC+2/+3 for example).
   datetime nowUtc = TimeGMT();
   datetime startDay = (nowUtc / 86400) * 86400 - 7 * 86400;

   double priceMax = ChartGetDouble(0, CHART_PRICE_MAX, 0);
   double priceMin = ChartGetDouble(0, CHART_PRICE_MIN, 0);
   if(priceMax <= priceMin)
   {
      priceMax = SymbolInfoDouble(_Symbol, SYMBOL_BID) * 1.005;
      priceMin = SymbolInfoDouble(_Symbol, SYMBOL_BID) * 0.995;
   }

   // Bottom strip = lowest 6% of visible price range. Tall enough to
   // see, short enough to leave the candles untouched.
   double stripTop = priceMin + (priceMax - priceMin) * 0.06;
   double stripBot = priceMin;

   for(int day = 0; day < 9; day++)
   {
      datetime dayStartUtc = startDay + day * 86400;
      for(int i = 0; i < g_kzCount; i++)
      {
         datetime kzStartUtc = dayStartUtc + g_kz[i].sh * 3600 + g_kz[i].sm * 60;
         datetime kzEndUtc   = dayStartUtc + g_kz[i].eh * 3600 + g_kz[i].em * 60;
         datetime kzStart    = kzStartUtc + g_brokerOffsetSec;
         datetime kzEnd      = kzEndUtc   + g_brokerOffsetSec;

         string objName = StringFormat("%s%s_%d_%d",
                                       KZ_PREFIX, g_kz[i].name, day, i);

         if(ObjectFind(0, objName) < 0)
            ObjectCreate(0, objName, OBJ_RECTANGLE, 0, kzStart, stripTop, kzEnd, stripBot);
         ObjectSetInteger(0, objName, OBJPROP_TIME,  0, kzStart);
         ObjectSetDouble (0, objName, OBJPROP_PRICE, 0, stripTop);
         ObjectSetInteger(0, objName, OBJPROP_TIME,  1, kzEnd);
         ObjectSetDouble (0, objName, OBJPROP_PRICE, 1, stripBot);
         ObjectSetInteger(0, objName, OBJPROP_COLOR, g_kz[i].clr);
         ObjectSetInteger(0, objName, OBJPROP_FILL, true);
         ObjectSetInteger(0, objName, OBJPROP_BACK, true);
         ObjectSetInteger(0, objName, OBJPROP_SELECTABLE, false);
         ObjectSetInteger(0, objName, OBJPROP_HIDDEN, true);
         ObjectSetString (0, objName, OBJPROP_TOOLTIP, g_kz[i].name + " KZ");
      }
   }
}


// ====== INFO PANEL =================================================
//
// One fixed-position stack of OBJ_LABEL lines, with an OBJ_RECTANGLE_LABEL
// behind them as a background. Updated on every poll.
// ===================================================================
const int    PANEL_MAX_LINES   = 14;
const int    PANEL_LINE_HEIGHT = 16;
const int    PANEL_PADDING     = 8;
const int    PANEL_WIDTH       = 360;


string g_panelLines[14];
color  g_panelColours[14];
int    g_panelLineCount = 0;


void PanelClearBuffer()
{
   for(int i = 0; i < PANEL_MAX_LINES; i++)
   {
      g_panelLines[i] = "";
      g_panelColours[i] = ColPanelText;
   }
   g_panelLineCount = 0;
}


void PanelAddLine(string text, color c)
{
   if(g_panelLineCount >= PANEL_MAX_LINES) return;
   // OBJ_LABEL falls back to the literal "Label" placeholder when its
   // OBJPROP_TEXT is the empty string. Substitute a non-breaking space
   // for visually-empty separator rows so they render as blank gaps.
   if(StringLen(text) == 0) text = " ";
   g_panelLines[g_panelLineCount] = text;
   g_panelColours[g_panelLineCount] = c;
   g_panelLineCount++;
}


// Cross-platform corner constant resolver.
ENUM_BASE_CORNER PanelCorner()
{
   switch(PanelCornerCode)
   {
      case 0: return CORNER_LEFT_UPPER;
      case 1: return CORNER_RIGHT_UPPER;
      case 2: return CORNER_LEFT_LOWER;
      case 3: return CORNER_RIGHT_LOWER;
   }
   return CORNER_RIGHT_UPPER;
}


ENUM_ANCHOR_POINT PanelAnchor()
{
   switch(PanelCornerCode)
   {
      case 0: return ANCHOR_LEFT_UPPER;
      case 1: return ANCHOR_RIGHT_UPPER;
      case 2: return ANCHOR_LEFT_LOWER;
      case 3: return ANCHOR_RIGHT_LOWER;
   }
   return ANCHOR_RIGHT_UPPER;
}


void DrawPanel()
{
   if(!ShowInfoPanel)
   {
      // Clear if user toggled off
      ObjectsDeleteAll(0, PANEL_PREFIX);
      return;
   }

   // Background rectangle
   string bg = PANEL_PREFIX + "bg";
   if(ObjectFind(0, bg) < 0)
      ObjectCreate(0, bg, OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, bg, OBJPROP_CORNER,   PanelCorner());
   ObjectSetInteger(0, bg, OBJPROP_XDISTANCE, PanelXOffset);
   ObjectSetInteger(0, bg, OBJPROP_YDISTANCE, PanelYOffset);
   ObjectSetInteger(0, bg, OBJPROP_XSIZE,    PANEL_WIDTH);
   ObjectSetInteger(0, bg, OBJPROP_YSIZE,    PANEL_PADDING * 2 + g_panelLineCount * PANEL_LINE_HEIGHT);
   ObjectSetInteger(0, bg, OBJPROP_BGCOLOR,  ColPanelBg);
   ObjectSetInteger(0, bg, OBJPROP_BORDER_COLOR, ColPanelBorder);
   ObjectSetInteger(0, bg, OBJPROP_BORDER_TYPE,  BORDER_FLAT);
   ObjectSetInteger(0, bg, OBJPROP_BACK,     false);
   ObjectSetInteger(0, bg, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, bg, OBJPROP_HIDDEN,   true);

   // Lines
   for(int i = 0; i < PANEL_MAX_LINES; i++)
   {
      string objName = StringFormat("%sln_%02d", PANEL_PREFIX, i);
      if(i >= g_panelLineCount)
      {
         ObjectDelete(0, objName);
         continue;
      }
      if(ObjectFind(0, objName) < 0)
         ObjectCreate(0, objName, OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, objName, OBJPROP_CORNER,    PanelCorner());
      ObjectSetInteger(0, objName, OBJPROP_ANCHOR,    PanelAnchor());
      ObjectSetInteger(0, objName, OBJPROP_XDISTANCE, PanelXOffset + PANEL_PADDING);
      ObjectSetInteger(0, objName, OBJPROP_YDISTANCE, PanelYOffset + PANEL_PADDING + i * PANEL_LINE_HEIGHT);
      ObjectSetString (0, objName, OBJPROP_TEXT,      g_panelLines[i]);
      ObjectSetInteger(0, objName, OBJPROP_COLOR,     g_panelColours[i]);
      ObjectSetInteger(0, objName, OBJPROP_FONTSIZE,  PanelFontSize);
      ObjectSetString (0, objName, OBJPROP_FONT,      PanelFontName);
      ObjectSetInteger(0, objName, OBJPROP_SELECTABLE, false);
      ObjectSetInteger(0, objName, OBJPROP_HIDDEN,   true);
   }
}


// ====== INFO PANEL CONTENT =========================================
string FormatHeldMinutes(datetime entry)
{
   int sec = (int)(TimeCurrent() - entry);
   if(sec < 0) sec = 0;
   int mn = sec / 60;
   if(mn < 60) return StringFormat("%dm", mn);
   return StringFormat("%dh%02dm", mn / 60, mn % 60);
}


double CurrentPrice(string dir)
{
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   if(dir == "SHORT") return ask;       // closing a SHORT lifts the ask
   return bid;                           // closing a LONG hits the bid
}


double LiveR(const ActiveTrade &t)
{
   double dist = MathAbs(t.entryPrice - t.sl);
   if(dist <= 0) return 0;
   double now = CurrentPrice(t.direction);
   if(t.direction == "LONG")  return (now - t.entryPrice) / dist;
   return (t.entryPrice - now) / dist;
}


double TargetR(double price, const ActiveTrade &t)
{
   double dist = MathAbs(t.entryPrice - t.sl);
   if(dist <= 0) return 0;
   if(t.direction == "LONG") return (price - t.entryPrice) / dist;
   return (t.entryPrice - price) / dist;
}


void PopulatePanel()
{
   PanelClearBuffer();

   // Header
   PanelAddLine(StringFormat("=== GTOS . %s ===", _Symbol), ColPanelText);

   // Server time + KZ status. KZ status uses REAL UTC (CLAUDE.md
   // schedule); the displayed clock shows real UTC for an at-a-glance
   // sanity check, plus broker time for chart correlation.
   datetime nowUtc = TimeGMT();
   datetime nowSrv = TimeCurrent();
   string kzNow = CurrentKZName(nowUtc);
   color kzC = (kzNow == "-" ? ColPanelMuted : ColPanelGood);
   PanelAddLine(StringFormat("UTC %s . broker %s . KZ: %s",
                             TimeToString(nowUtc, TIME_MINUTES|TIME_SECONDS),
                             TimeToString(nowSrv, TIME_MINUTES),
                             kzNow),
                kzC);

   PanelAddLine("", ColPanelMuted);

   // Active trade block
   if(g_hasActive)
   {
      double liveR = LiveR(g_active);
      color rC = (liveR > 0 ? ColPanelGood : (liveR < 0 ? ColPanelBad : ColPanelMuted));
      string flags = "";
      if(g_active.j46j49Active) flags += " · J46-J49";
      if(g_active.bePulled)     flags += " · BE";
      if(g_active.tp1Hit)       flags += " · TP1✓";

      PanelAddLine(StringFormat("ACTIVE %s %.2f lots @ %s%s",
                                g_active.direction,
                                g_active.lots,
                                DoubleToString(g_active.entryPrice, _Digits),
                                flags),
                   DirectionColour(g_active.direction));

      if(g_active.sl > 0)
         PanelAddLine(StringFormat("  SL %s",
                                    DoubleToString(g_active.sl, _Digits)),
                       ColSL);

      if(g_active.tp1 > 0)
      {
         double r1 = TargetR(g_active.tp1, g_active);
         PanelAddLine(StringFormat("  TP1 %s (%+.1fR)",
                                    DoubleToString(g_active.tp1, _Digits), r1),
                       ColTP);
      }
      if(g_active.tp2 > 0)
      {
         double r2 = TargetR(g_active.tp2, g_active);
         PanelAddLine(StringFormat("  TP2 %s (%+.1fR)",
                                    DoubleToString(g_active.tp2, _Digits), r2),
                       ColTP);
      }

      PanelAddLine(StringFormat("  Live %+.2fR · held %s",
                                liveR, FormatHeldMinutes(g_active.entryTime)),
                   rC);
      if(StringLen(g_active.framework) > 0 || StringLen(g_active.grade) > 0)
         PanelAddLine(StringFormat("  %s %s%s",
                                    (StringLen(g_active.grade) > 0 ? g_active.grade : ""),
                                    (StringLen(g_active.framework) > 0 ? g_active.framework : ""),
                                    (g_active.riskPct > 0 ? StringFormat(" · risk %.2f%%", g_active.riskPct) : "")),
                       ColPanelMuted);
   }
   else
   {
      PanelAddLine("ACTIVE: none", ColPanelMuted);
   }

   PanelAddLine("", ColPanelMuted);

   // Today's stats
   string winrate = "—";
   if(g_tradesToday > 0)
      winrate = StringFormat("%d%%", (int)(100.0 * g_winsToday / g_tradesToday));
   color rTotC = (g_totalRToday > 0 ? ColPanelGood : (g_totalRToday < 0 ? ColPanelBad : ColPanelMuted));
   PanelAddLine(StringFormat("TODAY %d trades · WR %s · %+.2fR",
                             g_tradesToday, winrate, g_totalRToday),
                rTotC);
   PanelAddLine(StringFormat("  candidates %d · rejected %d · no-trade %d",
                             g_candidatesToday, g_rejectedToday, g_noTradeToday),
                ColPanelMuted);

   PanelAddLine("", ColPanelMuted);

   // Last decision
   string lastTs = (g_lastDecisionTs > 0
                     ? TimeToString(g_lastDecisionTs, TIME_MINUTES)
                     : "—");
   color lastC = ColPanelText;
   if(g_lastDecision == "EXECUTED")           lastC = ColLong;
   else if(g_lastDecision == "CANDIDATE")     lastC = ColCandidate;
   else if(StringFind(g_lastDecision, "REJECT") >= 0) lastC = ColRejected;
   else if(g_lastDecision == "BLOCKED_CALENDAR")     lastC = ColBlocked;
   else if(g_lastDecision == "EMERGENCY_STOP")       lastC = ColEmergency;
   else if(g_lastDecision == "NO_TRADE")             lastC = ColPanelMuted;

   PanelAddLine(StringFormat("LAST %s [%s]", g_lastDecision, lastTs), lastC);
   if(StringLen(g_lastDetail) > 0)
   {
      string trimmed = g_lastDetail;
      if(StringLen(trimmed) > 44) trimmed = StringSubstr(trimmed, 0, 41) + "...";
      PanelAddLine("  " + trimmed, ColPanelMuted);
   }

   DrawPanel();
}


// ====== MARKER DRAWERS ============================================
void DrawArrow(string name, datetime t, double price, int code,
               color c, int width, string tooltip)
{
   if(ObjectFind(0, name) < 0)
      ObjectCreate(0, name, OBJ_ARROW, 0, t, price);
   ObjectSetInteger(0, name, OBJPROP_TIME, t);
   ObjectSetDouble (0, name, OBJPROP_PRICE, price);
   ObjectSetInteger(0, name, OBJPROP_ARROWCODE, code);
   ObjectSetInteger(0, name, OBJPROP_COLOR, c);
   ObjectSetInteger(0, name, OBJPROP_WIDTH, width);
   ObjectSetString (0, name, OBJPROP_TOOLTIP, tooltip);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, name, OBJPROP_HIDDEN, false);
}


void DrawSmallText(string name, datetime t, double price,
                   string text, color c, int fontsize)
{
   if(ObjectFind(0, name) < 0)
      ObjectCreate(0, name, OBJ_TEXT, 0, t, price);
   ObjectSetInteger(0, name, OBJPROP_TIME,  t);
   ObjectSetDouble (0, name, OBJPROP_PRICE, price);
   ObjectSetString (0, name, OBJPROP_TEXT,  text);
   ObjectSetInteger(0, name, OBJPROP_COLOR, c);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, fontsize);
   ObjectSetInteger(0, name, OBJPROP_ANCHOR,   ANCHOR_LEFT);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, name, OBJPROP_HIDDEN,   true);
}


void DrawHLine(string name, double price, color c, int style, int width,
               string tooltip)
{
   if(ObjectFind(0, name) < 0)
      ObjectCreate(0, name, OBJ_HLINE, 0, 0, price);
   ObjectSetDouble (0, name, OBJPROP_PRICE, 0, price);
   ObjectSetInteger(0, name, OBJPROP_COLOR, c);
   ObjectSetInteger(0, name, OBJPROP_STYLE, style);
   ObjectSetInteger(0, name, OBJPROP_WIDTH, width);
   ObjectSetString (0, name, OBJPROP_TOOLTIP, tooltip);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, name, OBJPROP_BACK, true);
   ObjectSetInteger(0, name, OBJPROP_HIDDEN, true);
}


void DrawTrendline(string name, datetime t1, double p1,
                   datetime t2, double p2, color c, int style, int width,
                   string tooltip)
{
   if(ObjectFind(0, name) < 0)
      ObjectCreate(0, name, OBJ_TREND, 0, t1, p1, t2, p2);
   ObjectSetInteger(0, name, OBJPROP_TIME,  0, t1);
   ObjectSetDouble (0, name, OBJPROP_PRICE, 0, p1);
   ObjectSetInteger(0, name, OBJPROP_TIME,  1, t2);
   ObjectSetDouble (0, name, OBJPROP_PRICE, 1, p2);
   ObjectSetInteger(0, name, OBJPROP_COLOR, c);
   ObjectSetInteger(0, name, OBJPROP_STYLE, style);
   ObjectSetInteger(0, name, OBJPROP_WIDTH, width);
   ObjectSetInteger(0, name, OBJPROP_RAY_RIGHT, false);
   ObjectSetInteger(0, name, OBJPROP_BACK, true);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
   ObjectSetString (0, name, OBJPROP_TOOLTIP, tooltip);
   ObjectSetInteger(0, name, OBJPROP_HIDDEN, true);
}


// ===================================================================
//                  BUILD A RICH HOVER TOOLTIP
// ===================================================================
string BuildTooltip(string decision, string detail,
                    string dir, string fw, string grade, string conf,
                    string align, string kz,
                    double sl, double tp1, double tp2, double tp3,
                    double lots, double riskPct,
                    double rR, string exitType, double mfe, double mae,
                    string tradeId,
                    datetime t)
{
   string out = StringFormat("[%s] %s",
                             TimeToString(t, TIME_MINUTES),
                             decision);
   if(StringLen(detail) > 0) out += "\n" + detail;
   if(StringLen(dir) > 0)    out += "\nDir: " + dir;
   if(StringLen(fw) > 0)     out += " · FW: " + fw;
   if(StringLen(grade) > 0)  out += " · Grade: " + grade;
   if(StringLen(conf) > 0)   out += "\nConfidence: " + conf;
   if(StringLen(align) > 0)  out += " · Align: " + align;
   if(StringLen(kz) > 0)     out += " · KZ: " + kz;
   if(sl > 0)                out += "\nSL: " + DoubleToString(sl, _Digits);
   if(tp1 > 0)               out += " · TP1: " + DoubleToString(tp1, _Digits);
   if(tp2 > 0)               out += " · TP2: " + DoubleToString(tp2, _Digits);
   if(tp3 > 0)               out += " · TP3: " + DoubleToString(tp3, _Digits);
   if(lots > 0)              out += "\nLots: " + DoubleToString(lots, 2);
   if(riskPct > 0)           out += " · Risk: " + DoubleToString(riskPct, 2) + "%";
   if(StringLen(exitType) > 0) out += "\nExit: " + exitType;
   if(rR != 0)               out += " · R: " + StringFormat("%+.2f", rR);
   if(mfe > 0)               out += "\nMFE: " + StringFormat("%+.2fR", mfe);
   if(mae < 0)               out += " · MAE: " + StringFormat("%+.2fR", mae);
   if(StringLen(tradeId) > 0) out += "\nID: " + tradeId;
   return out;
}


// ====== TRADE LIFECYCLE OVERLAY ====================================
//
// Draws SL/TP horizontal lines for the active trade, a vertical
// entry guide, and (after close) a connecting line entry → exit.
// ===================================================================
void DrawActiveTradeLines()
{
   if(!ShowSLTPLines || !g_hasActive) return;
   if(g_active.entryPrice <= 0) return;

   color dirC = DirectionColour(g_active.direction);

   // Entry vertical line
   string entryLn = LIFECYCLE_PREFIX + "entry_" + g_active.tradeId;
   if(ObjectFind(0, entryLn) < 0)
      ObjectCreate(0, entryLn, OBJ_VLINE, 0, g_active.entryTime, 0);
   ObjectSetInteger(0, entryLn, OBJPROP_TIME,  g_active.entryTime);
   ObjectSetInteger(0, entryLn, OBJPROP_COLOR, dirC);
   ObjectSetInteger(0, entryLn, OBJPROP_STYLE, STYLE_DOT);
   ObjectSetInteger(0, entryLn, OBJPROP_WIDTH, 1);
   ObjectSetInteger(0, entryLn, OBJPROP_BACK,  true);
   ObjectSetInteger(0, entryLn, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, entryLn, OBJPROP_HIDDEN, true);
   ObjectSetString (0, entryLn, OBJPROP_TOOLTIP,
                    StringFormat("Entry %s @ %s",
                                  g_active.direction,
                                  DoubleToString(g_active.entryPrice, _Digits)));

   // Entry horizontal line
   string entryHL = LIFECYCLE_PREFIX + "entryH_" + g_active.tradeId;
   DrawHLine(entryHL, g_active.entryPrice, dirC, STYLE_DASHDOT, 1,
             StringFormat("Entry %s", DoubleToString(g_active.entryPrice, _Digits)));

   // SL line (or BE line if pulled)
   if(g_active.sl > 0)
   {
      string slLn = LIFECYCLE_PREFIX + "sl_" + g_active.tradeId;
      color slC = (g_active.bePulled ? ColBE : ColSL);
      string slTip = (g_active.bePulled ? "BE pulled" : "SL");
      DrawHLine(slLn, g_active.sl, slC, STYLE_DASH, 1,
                StringFormat("%s %s", slTip,
                              DoubleToString(g_active.sl, _Digits)));
   }
   if(g_active.tp1 > 0)
   {
      string tp1Ln = LIFECYCLE_PREFIX + "tp1_" + g_active.tradeId;
      double r1 = TargetR(g_active.tp1, g_active);
      DrawHLine(tp1Ln, g_active.tp1, ColTP, STYLE_DASH, 1,
                StringFormat("TP1 %s (%+.1fR)",
                              DoubleToString(g_active.tp1, _Digits), r1));
   }
   if(g_active.tp2 > 0)
   {
      string tp2Ln = LIFECYCLE_PREFIX + "tp2_" + g_active.tradeId;
      double r2 = TargetR(g_active.tp2, g_active);
      DrawHLine(tp2Ln, g_active.tp2, ColTP, STYLE_DOT, 1,
                StringFormat("TP2 %s (%+.1fR)%s",
                              DoubleToString(g_active.tp2, _Digits), r2,
                              (g_active.j46j49Active ? " · J46-J49 higher" : "")));
   }
   if(g_active.tp3 > 0)
   {
      string tp3Ln = LIFECYCLE_PREFIX + "tp3_" + g_active.tradeId;
      double r3 = TargetR(g_active.tp3, g_active);
      DrawHLine(tp3Ln, g_active.tp3, ColTP, STYLE_DOT, 1,
                StringFormat("TP3 %s (%+.1fR)",
                              DoubleToString(g_active.tp3, _Digits), r3));
   }
}


void ClearActiveTradeLines()
{
   ObjectsDeleteAll(0, LIFECYCLE_PREFIX);
}


void FreezeLifecycleLine(string tradeId, datetime exitTime, double exitPrice,
                         double realizedR)
{
   // After a trade closes, leave only the entry/exit connector + final
   // R label so history is preserved.
   string conn = LIFECYCLE_PREFIX + "exit_" + tradeId;
   color c = (realizedR > 0 ? ColPanelGood : (realizedR < 0 ? ColPanelBad : ColPanelMuted));
   DrawTrendline(conn,
                 g_active.entryTime, g_active.entryPrice,
                 exitTime, exitPrice,
                 c, STYLE_SOLID, 1,
                 StringFormat("%s %s · %+.2fR",
                               g_active.direction,
                               g_active.tradeId,
                               realizedR));

   // Exit-price label
   string lbl = LIFECYCLE_PREFIX + "rlbl_" + tradeId;
   DrawSmallText(lbl, exitTime, exitPrice,
                 StringFormat(" %+.2fR", realizedR),
                 c, 8);

   // Drop the live SL/TP lines now that the trade is done.
   ObjectDelete(0, LIFECYCLE_PREFIX + "sl_"  + tradeId);
   ObjectDelete(0, LIFECYCLE_PREFIX + "tp1_" + tradeId);
   ObjectDelete(0, LIFECYCLE_PREFIX + "tp2_" + tradeId);
   ObjectDelete(0, LIFECYCLE_PREFIX + "tp3_" + tradeId);
   ObjectDelete(0, LIFECYCLE_PREFIX + "entryH_" + tradeId);
}


// ====== EVENT HANDLERS ============================================
// Helper: is event timestamp from today's UTC date? Stats counters
// + live active-trade state should ONLY update for today's events.
bool IsToday(datetime t)
{
   datetime today = (TimeCurrent() / 86400) * 86400;
   return t >= today;
}


// Helper: only treat an EXECUTED event as the LIVE active trade if
// (a) we're past the initial-attach replay phase, (b) the event has
// a real entry price (price > 0), and (c) the entry timestamp is
// from today. Otherwise it's a historical fill bleeding into the
// EA from the file replay.
bool IsLiveExecution(datetime t, double price)
{
   if(g_replayPhase) return false;
   if(price <= 0) return false;
   if(!IsToday(t)) return false;
   return true;
}


void HandleExecuted(int lineNum, datetime t, double price, string detail,
                    string dir, string fw, string grade, string conf,
                    string tradeId,
                    double sl, double tp1, double tp2, double tp3,
                    double lots, double riskPct, bool j46j49,
                    string tooltip)
{
   if(!ShowExecuted) return;
   color c = DirectionColour(dir);
   int code = (dir == "SHORT") ? 234 : 233;  // down arrow vs up arrow
   string nm = StringFormat("%sex_%d", MARKER_PREFIX, lineNum);
   DrawArrow(nm, t, price, code, c, 3, tooltip);

   // Update LIVE state only for today's real events; otherwise this is
   // a historical replay marker (still drawn for context but does NOT
   // hijack the active-trade panel).
   if(!IsLiveExecution(t, price)) return;

   g_tradesToday++;

   g_active.tradeId      = (StringLen(tradeId) > 0 ? tradeId
                                                   : StringFormat("ex_%d", lineNum));
   g_active.entryTime    = t;
   g_active.entryPrice   = price;
   g_active.direction    = dir;
   g_active.framework    = fw;
   g_active.grade        = grade;
   g_active.sl           = sl;
   g_active.tp1          = tp1;
   g_active.tp2          = tp2;
   g_active.tp3          = tp3;
   g_active.lots         = (lots > 0 ? lots : 1.0);
   g_active.riskPct      = riskPct;
   g_active.j46j49Active = j46j49;
   g_active.tp1Hit       = false;
   g_active.bePulled     = false;
   g_hasActive = true;

   DrawActiveTradeLines();
}


void HandleCloseEvent(int lineNum, datetime t, double price, string detail,
                      string decision, string tradeId,
                      double realizedR, string exitType,
                      string tooltip)
{
   // Render an exit marker and freeze the lifecycle line.
   string nm = StringFormat("%sclose_%d", MARKER_PREFIX, lineNum);
   color c = (realizedR > 0 ? ColPanelGood : (realizedR < 0 ? ColPanelBad : ColPanelMuted));
   int  code = (realizedR > 0 ? 217 : (realizedR < 0 ? 218 : 159));
   DrawArrow(nm, t, price, code, c, 2, tooltip);

   // Stats only update for today's events; historical closes drawn for
   // context but excluded from "today's" tallies.
   if(g_replayPhase || !IsToday(t)) return;

   if(realizedR > 0.05) g_winsToday++;
   else if(realizedR < -0.05) g_lossesToday++;
   g_totalRToday += realizedR;

   if(g_hasActive)
   {
      FreezeLifecycleLine(g_active.tradeId, t, price, realizedR);
      g_hasActive = false;
   }
}


void HandleCandidate(int lineNum, datetime t, double price, string detail,
                     string dir, string fw, string grade, string conf,
                     string align, string tooltip)
{
   if(!ShowCandidate) return;
   color c = (StringLen(dir) > 0 ? DirectionColour(dir) : ColCandidate);
   string nm = StringFormat("%scand_%d", MARKER_PREFIX, lineNum);
   DrawArrow(nm, t, price, 159, c, 3, tooltip);

   if(!g_replayPhase && IsToday(t)) g_candidatesToday++;

   if(ShowGradeLabels && StringLen(grade) > 0)
   {
      string lbl = StringFormat("%scgrade_%d", MARKER_PREFIX, lineNum);
      DrawSmallText(lbl, t, price, " " + grade, c, 8);
   }
   if(ShowAlignLabels && StringLen(align) > 0)
   {
      string lbl = StringFormat("%scalign_%d", MARKER_PREFIX, lineNum);
      DrawSmallText(lbl, t, price, " A" + align, ColPanelMuted, 7);
   }
}


void HandleRejected(int lineNum, datetime t, double price, string decision,
                    string detail, string tooltip)
{
   if(!ShowRejected) return;
   string nm = StringFormat("%srej_%d", MARKER_PREFIX, lineNum);
   DrawArrow(nm, t, price, 251, ColRejected, 1, tooltip);
   if(!g_replayPhase && IsToday(t)) g_rejectedToday++;
}


void HandleNoTrade(int lineNum, datetime t, double price, string detail,
                   string tooltip)
{
   if(!ShowNoTrade) return;
   string nm = StringFormat("%snt_%d", MARKER_PREFIX, lineNum);
   DrawArrow(nm, t, price, 159, ColNoTrade, 1, tooltip);
   if(!g_replayPhase && IsToday(t)) g_noTradeToday++;
}


void HandleBlocked(int lineNum, datetime t, double price, string detail,
                   string decision, string tooltip)
{
   if(!ShowBlockedCalendar) return;
   string nm = StringFormat("%sblk_%d", MARKER_PREFIX, lineNum);
   DrawArrow(nm, t, price, 78, ColBlocked, 2, tooltip);
}


void HandleEmergency(int lineNum, datetime t, double price, string detail,
                     string decision, string tooltip)
{
   string nm = StringFormat("%semerg_%d", MARKER_PREFIX, lineNum);
   DrawArrow(nm, t, price, 251, ColEmergency, 3,
              "EMERGENCY STOP: " + tooltip);
}


void HandleLimitPlaced(int lineNum, datetime t, double price, string detail,
                       string dir, string tooltip)
{
   if(!ShowLimitPlaced) return;
   color c = (StringLen(dir) > 0 ? DirectionColour(dir) : ColLimitPlaced);
   string nm = StringFormat("%slim_%d", MARKER_PREFIX, lineNum);
   // Hollow square to distinguish from market candidate
   DrawArrow(nm, t, price, 168, c, 2, "LIMIT PLACED: " + tooltip);
}


void HandleExecutionFailed(int lineNum, datetime t, double price, string detail,
                           string tooltip)
{
   string nm = StringFormat("%sfail_%d", MARKER_PREFIX, lineNum);
   DrawArrow(nm, t, price, 251, clrRed, 3, "EXEC FAIL: " + tooltip);
}


// ====== STATS DAY-ROLLOVER ========================================
void MaybeRollDay()
{
   datetime now = TimeCurrent();
   datetime today = (now / 86400) * 86400;
   if(g_todayUtcDay != today)
   {
      g_todayUtcDay = today;
      g_tradesToday = 0;
      g_winsToday = 0;
      g_lossesToday = 0;
      g_totalRToday = 0.0;
      g_candidatesToday = 0;
      g_rejectedToday = 0;
      g_noTradeToday = 0;
   }
}


// ====== POLL + DISPATCH ===========================================
void ProcessLine(int lineNum, string line)
{
   if(StringLen(line) < 5) return;

   string decision = ExtractField(line, "decision");
   if(StringLen(decision) == 0) return;

   string detail   = ExtractField(line, "detail");
   string time_str = ExtractField(line, "time");
   double price    = ExtractDouble(line, "price");
   string align    = ExtractField(line, "align");
   string conf     = ExtractField(line, "confidence");
   string kz       = ExtractField(line, "kill_zone");
   string tradeId  = ExtractField(line, "trade_id");

   // Direction / framework / grade — explicit field FIRST, fall back
   // to keyword-extraction from `detail` (works against current
   // 4-field schema; auto-upgrades when the Python writer adds the
   // structured fields).
   string dir   = ResolveDirection(ExtractField(line, "direction"), detail);
   string fw    = ResolveFramework(ExtractField(line, "framework"), detail);
   string grade = ResolveGrade(ExtractField(line, "grade"), detail);

   double sl    = ExtractDouble(line, "sl");
   double tp1   = ExtractDouble(line, "tp1");
   double tp2   = ExtractDouble(line, "tp2");
   double tp3   = ExtractDouble(line, "tp3");
   double lots  = ExtractDouble(line, "lots");
   double riskP = ExtractDouble(line, "risk_pct");
   bool   j46   = (ExtractField(line, "j46_j49_active") == "true");

   double realR = ExtractDouble(line, "realized_r");
   string exitType = ExtractField(line, "exit_type");
   double mfe   = ExtractDouble(line, "mfe_r");
   double mae   = ExtractDouble(line, "mae_r");

   datetime t = ParseISO(time_str);
   if(t == 0) t = TimeCurrent();

   string tooltip = BuildTooltip(decision, detail,
                                 dir, fw, grade, conf, align, kz,
                                 sl, tp1, tp2, tp3,
                                 lots, riskP,
                                 realR, exitType, mfe, mae,
                                 tradeId, t);

   // Update last-decision fields BEFORE dispatch so panel reflects current.
   g_lastDecision   = decision;
   g_lastDetail     = detail;
   g_lastDecisionTs = t;

   // Dispatch
   if(decision == "EXECUTED")
   {
      HandleExecuted(lineNum, t, price, detail, dir, fw, grade, conf, tradeId,
                     sl, tp1, tp2, tp3, lots, riskP, j46, tooltip);
   }
   else if(decision == "CANDIDATE")
   {
      HandleCandidate(lineNum, t, price, detail, dir, fw, grade, conf,
                      align, tooltip);
   }
   else if(decision == "LIMIT_PLACED" || decision == "LIMIT_INTENT_PLACED")
   {
      HandleLimitPlaced(lineNum, t, price, detail, dir, tooltip);
   }
   else if(decision == "LIMIT_FILLED")
   {
      HandleExecuted(lineNum, t, price, detail, dir, fw, grade, conf, tradeId,
                     sl, tp1, tp2, tp3, lots, riskP, j46,
                     "LIMIT FILLED · " + tooltip);
   }
   else if(decision == "TP1_HIT" || decision == "TP1_BE_ONLY_J46_J49"
           || decision == "tp1_be_only_j46_j49"
           || decision == "tp1_partial")
   {
      // Mark BE pull on the active trade
      if(g_hasActive) { g_active.tp1Hit = true; g_active.bePulled = true; }
      string nm = StringFormat("%stp1_%d", MARKER_PREFIX, lineNum);
      DrawArrow(nm, t, price, 217, ColBE, 2, "TP1 HIT · " + tooltip);
      DrawActiveTradeLines();
   }
   else if(decision == "TP2_HIT" || decision == "TP2_HIGHER_TARGET_J46_J49"
           || decision == "tp2_higher_target_j46_j49"
           || decision == "tp2_partial" || decision == "tp1_full_close"
           || decision == "tp2_full_close")
   {
      HandleCloseEvent(lineNum, t, price, detail, decision, tradeId,
                       (realR != 0 ? realR : 6.0), exitType, tooltip);
   }
   else if(decision == "TIME_STOP" || decision == "j46_j49_time_stop")
   {
      string nm = StringFormat("%sts_%d", MARKER_PREFIX, lineNum);
      DrawArrow(nm, t, price, 165, ColTimeStop, 2,
                "TIME STOP (J48 12-bar): " + tooltip);
      HandleCloseEvent(lineNum, t, price, detail, decision, tradeId,
                       realR, exitType, tooltip);
   }
   else if(decision == "BE_PULLED" || decision == "be_pulled")
   {
      if(g_hasActive) { g_active.bePulled = true; }
      string nm = StringFormat("%sbe_%d", MARKER_PREFIX, lineNum);
      DrawArrow(nm, t, price, 78, ColBE, 1, "BE PULL: " + tooltip);
      DrawActiveTradeLines();
   }
   else if(decision == "SL_HIT" || decision == "stop_loss"
           || decision == "broker_closed")
   {
      HandleCloseEvent(lineNum, t, price, detail, decision, tradeId,
                       (realR != 0 ? realR : -1.0), exitType, tooltip);
   }
   else if(decision == "REJECTED" || StringFind(decision, "REJECT") >= 0
           || decision == "SKIPPED_CORRELATION")
   {
      HandleRejected(lineNum, t, price, decision, detail, tooltip);
   }
   else if(decision == "BLOCKED_CALENDAR" || decision == "SKIP_NEWS_EVENT"
           || decision == "SKIP_NY_OPEN_CANDLE")
   {
      HandleBlocked(lineNum, t, price, detail, decision, tooltip);
   }
   else if(decision == "EMERGENCY_STOP" || decision == "CANARY_BLOCKED")
   {
      HandleEmergency(lineNum, t, price, detail, decision, tooltip);
   }
   else if(decision == "EXECUTION_FAILED" || decision == "LIMIT_INTENT_FAILED")
   {
      HandleExecutionFailed(lineNum, t, price, detail, tooltip);
   }
   else if(decision == "NO_TRADE")
   {
      HandleNoTrade(lineNum, t, price, detail, tooltip);
   }
   else if(decision == "ERROR")
   {
      HandleEmergency(lineNum, t, price, detail, decision, "ERROR: " + tooltip);
   }
   else
   {
      // Unknown decision — render as a small grey dot so we don't lose it.
      string nm = StringFormat("%sunk_%d", MARKER_PREFIX, lineNum);
      DrawArrow(nm, t, price, 159, ColPanelMuted, 1,
                StringFormat("(%s) %s", decision, tooltip));
   }
}


// ====== MAIN POLL =================================================
void PollFile()
{
   if(!FileIsExist(g_signalFile, FILE_COMMON | FILE_TXT))
   {
      // Try the local terminal Files dir if the COMMON path doesn't exist.
      if(!FileIsExist(g_signalFile))
         return;
   }

   int handle = FileOpen(g_signalFile,
                         FILE_READ | FILE_TXT | FILE_ANSI | FILE_SHARE_READ);
   if(handle == INVALID_HANDLE) return;

   int lineNum = 0;
   while(!FileIsEnding(handle))
   {
      string line = FileReadString(handle);
      lineNum++;
      if(lineNum <= g_lastLineCount) continue;
      ProcessLine(lineNum, line);
   }
   g_lastLineCount = lineNum;
   FileClose(handle);
}


void PurgeOldNoTradeMarkers()
{
   if(MaxNoTradeAgeBars <= 0) return;
   datetime cutoff = iTime(_Symbol, PERIOD_CURRENT, MaxNoTradeAgeBars);
   if(cutoff == 0) return;

   int total = ObjectsTotal(0);
   for(int i = total - 1; i >= 0; i--)
   {
      string nm = ObjectName(0, i);
      if(StringFind(nm, MARKER_PREFIX + "nt_") != 0) continue;
      datetime objTime = (datetime)ObjectGetInteger(0, nm, OBJPROP_TIME);
      if(objTime > 0 && objTime < cutoff) ObjectDelete(0, nm);
   }
}


// ====== EVENT FUNCTIONS ===========================================
int OnInit()
{
   g_chartSymbol = _Symbol;
   string sym = _Symbol;
   StringReplace(sym, ".", "_");
   g_signalFile = "agent_signals_" + sym + ".jsonl";

   g_attachTime = TimeCurrent();
   g_replayPhase = true;

   BuildKZSchedule(g_chartSymbol);
   DrawKZRegions();
   PanelClearBuffer();
   PopulatePanel();

   EventSetTimer(PollSeconds);

   PrintFormat("ChartMarker v2.0 attached: symbol=%s, file=%s, kz_count=%d, panel=%s",
               g_chartSymbol, g_signalFile, g_kzCount,
               (ShowInfoPanel ? "ON" : "OFF"));
   return INIT_SUCCEEDED;
}


void OnDeinit(const int reason)
{
   EventKillTimer();
   ObjectsDeleteAll(0, OBJ_PREFIX);
   ChartRedraw(0);
}


void OnTimer()
{
   RefreshBrokerOffset();
   MaybeRollDay();
   PollFile();
   // First poll consumes the historical file backlog; subsequent polls
   // see only fresh events. After replay completes we flip the flag
   // so HandleExecuted / Candidate / Close update live state + stats.
   if(g_replayPhase) g_replayPhase = false;
   PurgeOldNoTradeMarkers();
   PopulatePanel();
   ChartRedraw(0);
}


void OnChartEvent(const int id, const long &lparam, const double &dparam,
                  const string &sparam)
{
   // Re-anchor KZ rectangles when the chart range changes so the
   // shaded regions stay full-height even after zoom/scroll.
   if(id == CHARTEVENT_CHART_CHANGE)
   {
      DrawKZRegions();
      ChartRedraw(0);
   }
}
//+------------------------------------------------------------------+
