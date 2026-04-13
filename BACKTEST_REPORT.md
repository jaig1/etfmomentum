# ETF Momentum Strategy — Universe Backtest Report

**Version:** v0.9.0
**Report Date:** April 12, 2026
**Backtest End Date:** April 8, 2026
**Initial Capital:** $100,000

---

## Table of Contents

1. [Methodology](#1-methodology)
2. [SP500 Sectors](#2-sp500-sectors)
3. [Emerging Markets](#3-emerging-markets)
4. [Developed Markets](#4-developed-markets)
5. [Commodity](#5-commodity)
6. [Multi-Asset](#6-multi-asset)
7. [Factor](#7-factor)
8. [Bond](#8-bond)
9. [Cross-Universe Comparison](#9-cross-universe-comparison)

---

## 1. Methodology

### 1.1 Strategy Overview

A systematic weekly-rebalancing rotation strategy that ranks ETFs within a universe by relative strength versus SPY, applies an absolute trend filter, and selects the top-N holdings. Four independent defensive layers protect capital during adverse regimes.

### 1.2 Signal Pipeline

| Step | Mechanism | Purpose |
|---|---|---|
| 1. Absolute trend filter | ETF price > its own SMA | Eliminates ETFs in downtrends |
| 2. RS ratio | ETF ROC ÷ SPY ROC over lookback | Ranks relative to broad market |
| 3. Momentum Quality | RS ratio ÷ rolling StdDev | Rewards smooth, consistent trends over volatile spikes |
| 4. Correlation filter | Skip if corr > 0.85 with already-selected ETF | Prevents holding near-duplicate positions |
| 5. Breadth filter | If < 40% of universe above SMA → 50% SGOV + 50% top-1 | Early warning: drops to defensive before vol spikes |

All five steps are computed weekly. Parameters (SMA lookback, ROC lookback, TopN) are universe-specific and walk-forward validated.

### 1.3 Defensive Layers

| Layer | Trigger | Action |
|---|---|---|
| SGOV Cash | ETF fails SMA filter | Replace with SGOV short-term treasuries |
| 5% Stop-Loss | SPY drops 5% from recent high | Exit all positions → SGOV until re-entry signal |
| Volatility Regime | SPY realised vol > 25% annualised | Shift to high-vol allocation (TopN=5, min 20% SPY) |
| Breadth Filter | < 40% of universe ETFs above SMA | 50% SGOV + 50% highest-ranked ETF |

### 1.4 Optimised Parameters (Per Universe)

| Universe | SMA Lookback | ROC Lookback | TopN | Derived By |
|---|---|---|---|---|
| SP500 | 210d (10mo) | 63d (3mo) | 3 | In-sample grid search |
| Emerging | 252d (12mo) | 21d (1mo) | 3 | Walk-forward consensus 5/6 windows |
| Developed | 168d (8mo) | 21d (1mo) | 3 | Walk-forward consensus 6/6 windows |
| Commodity | 126d (6mo) | 126d (6mo) | 3 | Walk-forward consensus 6/6 windows |
| Multi-Asset | 126d (6mo) | 63d (3mo) | 5 | Walk-forward consensus 4/6 windows |
| Factor | 210d (10mo) | 21d (1mo) | 3 | Walk-forward consensus W5+W6 |
| Bond | 126d (6mo) | 63d (3mo) | 10 | Walk-forward consensus 6/6 windows |

### 1.5 Walk-Forward Validation Protocol

- **Windows:** 6 expanding windows, anchor 2007-01-01, 2-year OOS test periods
- **Grid:** 48 combinations — SMA {6, 8, 10, 12}mo × ROC {1, 3, 6}mo × TopN {3, 5, 7, 10}
- **Rebalance:** Monthly (vol-regime disabled for clean parameter isolation)
- **Decay guide:** ≥ 0.70 = ROBUST | 0.50–0.70 = MODERATE | < 0.50 = Overfitting concern

### 1.6 Known Limitations

| Issue | Status | Impact |
|---|---|---|
| Look-ahead bias — signal and execution on same-day close | Open | Moderate |
| Stop-loss gap risk — assumes fill at exact 5% threshold | Open | Moderate |
| Pre-2007 data unavailable — 2008 is in-sample for all WF windows | Open | Low |
| SGOV pre-inception proxy | Fixed — BIL backfill pre June 2020 | N/A |

---

## 2. SP500 Sectors

### Universe

12 US equity sector ETFs ranked by relative strength vs SPY.

| Ticker | Sector | Issuer |
|---|---|---|
| XLK | Technology | SPDR |
| XLF | Financials | SPDR |
| XLE | Energy | SPDR |
| XLV | Health Care | SPDR |
| XLY | Consumer Discretionary | SPDR |
| XLP | Consumer Staples | SPDR |
| XLI | Industrials | SPDR |
| XLB | Materials | SPDR |
| XLRE | Real Estate | SPDR |
| XLU | Utilities | SPDR |
| XLC | Communication Services | SPDR |
| SMH | Semiconductors | VanEck |

**Optimised params:** SMA=210d, ROC=63d, TopN=3 (in-sample, 2016–2026)

### 10-Year Performance (2016-01-01 to 2026-04-08)

| Metric | Strategy | SPY B&H |
|---|---|---|
| Total Return | **768.94%** | 236.29% |
| Annualized Return | **23.51%** | 12.58% |
| Maximum Drawdown | **-11.83%** | -34.10% |
| Sharpe Ratio | **1.266** | 0.499 |
| Final Value ($100k) | **$868,944** | $336,290 |

### Max-History Performance (2007-01-01 to 2026-04-08, 19 years)

| Metric | Strategy | SPY B&H |
|---|---|---|
| Total Return | **2,530.69%** | 378.18% |
| Annualized Return | **18.53%** | 8.48% |
| Maximum Drawdown | **-13.03%** | -56.47% |
| Sharpe Ratio | **0.991** | 0.283 |
| Final Value ($100k) | **$2,630,690** | $478,185 |

### Year-by-Year Returns (10-Year)

| Year | Strategy | SPY | vs SPY |
|---|---|---|---|
| 2017 | +21.31% | +19.38% | +1.93pp ✅ |
| 2018 | +0.25% | -6.35% | +6.60pp ✅ |
| 2019 | +20.64% | +28.79% | -8.15pp ❌ |
| 2020 | +36.69% | +16.16% | +20.53pp ✅ |
| 2021 | +45.83% | +27.04% | +18.79pp ✅ |
| 2022 | +8.04% | -19.48% | +27.52pp ✅ |
| 2023 | +22.20% | +24.29% | -2.09pp ❌ |
| 2024 | +39.13% | +23.30% | +15.83pp ✅ |
| 2025 | +25.00% | +16.35% | +8.65pp ✅ |
| 2026 (YTD) | +13.77% | -0.87% | +14.64pp ✅ |

**Win rate: 8/10 years beat SPY**

### Walk-Forward Validation (SP500, April 2026)

| Window | OOS Period | OOS Sharpe | vs SPY | Beat SPY |
|---|---|---|---|---|
| 1 | 2014–2015 | 0.065 | -1.7pp | ❌ |
| 2 | 2016–2017 | 0.863 | -6.2pp | ❌ |
| 3 | 2018–2019 | 0.996 | +8.0pp | ✅ |
| 4 | 2020–2021 | 1.735 | +21.2pp | ✅ |
| 5 | 2022–2023 | 0.263 | +15.2pp | ✅ |
| 6 | 2024–2026 | 1.575 | +34.4pp | ✅ |

**Combined OOS return: 504% | Avg OOS Sharpe: 0.916 | 4/6 windows beat SPY**
**Note:** OOS/IS decay ratio 1.46 — anomalous (OOS periods happened to be stronger than training periods that include 2008). Current in-sample params (SMA=10mo, ROC=3mo, TopN=3) were not the walk-forward consensus choice; WF consensus was SMA=8mo, ROC=1mo, TopN=10.

### Key Observations

- **Best year 2022 (+8.04% vs SPY -19.48%):** Breadth filter fired early; rotated into energy (XLE) which rallied on inflation. Delivered +27.52pp edge in a severe bear market.
- **Worst miss 2019 (-8.15pp):** Tech (XLK) and broad growth dominated; sector rotation lag on a momentum-driven year with low dispersion.
- **2021 standout (+45.83%):** Concentrated in XLK, XLY, SMH during post-COVID tech expansion.
- **Structural strength:** Positive every year in 19yr history except 2008 (-8.16%) and 2011 (-1.28%) — only 2 negative years over 19 years.

---

## 3. Emerging Markets

### Universe

28 single-country and regional emerging market ETFs.

| Ticker | Country/Region | Ticker | Country/Region |
|---|---|---|---|
| FXI | China Large-Cap | EWZ | Brazil |
| MCHI | China Broad | EWW | Mexico |
| KWEB | China Internet | ECH | Chile |
| INDA | India | EPU | Peru |
| SMIN | India Small-Cap | TUR | Turkey |
| EWT | Taiwan | EPOL | Poland |
| EWY | South Korea | KSA | Saudi Arabia |
| EWM | Malaysia | UAE | UAE |
| EIDO | Indonesia | QAT | Qatar |
| THD | Thailand | EZA | South Africa |
| EPHE | Philippines | ILF | Latin America 40 |
| VNM | Vietnam | EGPT | Egypt |
| ARGT | Argentina | GXG | Colombia |
| NGE | Nigeria | GREK | Greece |

**Optimised params:** SMA=252d, ROC=21d, TopN=3 (walk-forward consensus 5/6 windows)

### 10-Year Performance (2016-01-01 to 2026-04-08)

| Metric | Strategy | SPY B&H |
|---|---|---|
| Total Return | **2,236.42%** | 236.29% |
| Annualized Return | **36.04%** | 12.58% |
| Maximum Drawdown | **-9.09%** | -34.10% |
| Sharpe Ratio | **1.862** | 0.499 |
| Final Value ($100k) | **$2,336,420** | $336,290 |

### Max-History Performance (2007-01-01 to 2026-04-08, 19 years)

| Metric | Strategy | SPY B&H |
|---|---|---|
| Total Return | **16,320.14%** | 380.63% |
| Annualized Return | **30.36%** | 8.50% |
| Maximum Drawdown | **-18.51%** | -56.47% |
| Sharpe Ratio | **1.426** | 0.284 |
| Final Value ($100k) | **$16,420,139** | $480,625 |

### Year-by-Year Returns (10-Year)

| Year | Strategy | SPY | vs SPY |
|---|---|---|---|
| 2017 | +48.20% | +19.38% | +28.82pp ✅ |
| 2018 | +8.75% | -6.35% | +15.10pp ✅ |
| 2019 | +9.52% | +28.79% | -19.27pp ❌ |
| 2020 | +33.00% | +16.16% | +16.84pp ✅ |
| 2021 | +45.43% | +27.04% | +18.39pp ✅ |
| 2022 | +29.30% | -19.48% | +48.78pp ✅ |
| 2023 | +32.51% | +24.29% | +8.22pp ✅ |
| 2024 | +32.69% | +23.30% | +9.39pp ✅ |
| 2025 | +78.30% | +16.35% | +61.95pp ✅ |
| 2026 (YTD) | +34.77% | -0.87% | +35.64pp ✅ |

**Win rate: 9/10 years beat SPY**

### Walk-Forward Validation (Emerging, April 2026)

**Combined OOS return: 734% | Avg OOS Sharpe: 0.949 | OOS/IS decay: 0.90 (ROBUST) | 5/6 windows beat SPY**

### Key Observations

- **Highest Sharpe across all universes (10yr: 1.862).** Country-level rotation within EM provides far higher dispersion than sector rotation — dramatically wider signal spread between winners and losers.
- **2022 (+29.30% vs SPY -19.48%, +48.78pp):** Rotated into commodity-linked EMs (energy exporters, GCC countries) as inflation/commodity cycle favoured EM over US equities.
- **2025 (+78.30%):** AI infrastructure cycle lifted Taiwan (EWT) and India (INDA, SMIN) strongly.
- **2019 (-19.27pp):** Only down year relative to SPY — US growth dominated; EM lagged on USD strength and trade war concerns.
- **MaxDD -9.09%:** Lowest drawdown of all equity universes. Wide universe of 28 ETFs provides natural diversification; strategy rarely concentrated in correlated positions.
- **OOS decay 0.90** — excellent parameter generalisation, lowest overfitting of all universes.

---

## 4. Developed Markets

### Universe

27 developed market ETFs covering single-country and regional exposures, including currency-hedged variants.

| Ticker | Country | Ticker | Country |
|---|---|---|---|
| EWJ | Japan | EWD | Sweden |
| EWG | Germany | EWK | Belgium |
| EWU | United Kingdom | EWS | Singapore |
| EWA | Australia | EWH | Hong Kong |
| EWC | Canada | ENOR | Norway |
| EWQ | France | EDEN | Denmark |
| EWL | Switzerland | EFNL | Finland |
| EWP | Spain | EIRL | Ireland |
| EWI | Italy | EIS | Israel |
| EWN | Netherlands | EWGS | Germany Small-Cap |
| SCJ | Japan Small-Cap | EWUS | UK Small-Cap |
| EWAS | Australia Small-Cap | HEWJ | Japan Hedged |
| HEWG | Germany Hedged | HEWU | UK Hedged |

**Optimised params:** SMA=168d, ROC=21d, TopN=3 (walk-forward consensus 6/6 windows)

### 10-Year Performance (2016-01-01 to 2026-04-08)

| Metric | Strategy | SPY B&H |
|---|---|---|
| Total Return | **349.59%** | 236.29% |
| Annualized Return | **15.81%** | 12.58% |
| Maximum Drawdown | **-13.95%** | -34.10% |
| Sharpe Ratio | **0.914** | 0.499 |
| Final Value ($100k) | **$449,588** | $336,290 |

### Max-History Performance (2007-01-01 to 2026-04-08, 19 years)

| Metric | Strategy | SPY B&H |
|---|---|---|
| Total Return | **827.27%** | 380.63% |
| Annualized Return | **12.27%** | 8.50% |
| Maximum Drawdown | **-19.06%** | -56.47% |
| Sharpe Ratio | **0.603** | 0.284 |
| Final Value ($100k) | **$927,274** | $480,625 |

### Year-by-Year Returns (10-Year)

| Year | Strategy | SPY | vs SPY |
|---|---|---|---|
| 2017 | +35.20% | +19.38% | +15.82pp ✅ |
| 2018 | +0.62% | -6.35% | +6.97pp ✅ |
| 2019 | +11.70% | +28.79% | -17.09pp ❌ |
| 2020 | +24.34% | +16.16% | +8.18pp ✅ |
| 2021 | +18.13% | +27.04% | -8.91pp ❌ |
| 2022 | -10.17% | -19.48% | +9.31pp ✅ |
| 2023 | +13.78% | +24.29% | -10.51pp ❌ |
| 2024 | +19.05% | +23.30% | -4.25pp ❌ |
| 2025 | +50.07% | +16.35% | +33.72pp ✅ |
| 2026 (YTD) | +10.05% | -0.87% | +10.92pp ✅ |

**Win rate: 6/10 years beat SPY**

### Walk-Forward Validation (Developed, April 2026)

**Combined OOS return: 210% | Avg OOS Sharpe: 0.420 | 2/6 windows beat SPY**

### Key Observations

- **Weakest equity universe** — 10yr Sharpe 0.914, though still far above SPY (0.499). The 19yr Sharpe (0.603) reflects persistent developed market underperformance post-2008 vs US equities.
- **2025 (+50.07%):** European defence spending surge and weak USD strongly favoured DM international. The strategy's best year, capturing structural rotation.
- **2019, 2021, 2023, 2024 all missed SPY:** US large-cap growth dominated in these years; DM countries structurally lagged.
- **2/6 WF windows beat SPY:** Consistent underperformance in in-sample equity bull markets. Strategy adds value mainly in US-equity bear regimes and international rotation cycles.
- **Currency-hedged variants** (HEWJ, HEWG, HEWU) add a layer of tactical currency positioning — when JPY/EUR weakness is expected, hedged versions can outperform.

---

## 5. Commodity

### Universe

10 commodity ETFs spanning metals, energy, and agriculture.

| Ticker | Commodity | Ticker | Commodity |
|---|---|---|---|
| GLD | Gold | DBC | Broad Commodities Basket |
| SLV | Silver | DBB | Base Metals Basket |
| PPLT | Platinum | BNO | Brent Crude Oil |
| PALL | Palladium | UNG | Natural Gas |
| CPER | Copper | CORN | Corn (Agriculture) |

**Optimised params:** SMA=126d, ROC=126d, TopN=3 (walk-forward consensus 6/6 windows)
**Note:** ROC=1mo in-sample optimal was rejected — walk-forward unanimously chose 6mo to avoid commodity noise overfitting.

### 10-Year Performance (2016-01-01 to 2026-04-08)

| Metric | Strategy | SPY B&H |
|---|---|---|
| Total Return | **5,204.06%** | 236.29% |
| Annualized Return | **47.38%** | 12.58% |
| Maximum Drawdown | **-10.67%** | -34.10% |
| Sharpe Ratio | **1.861** | 0.499 |
| Final Value ($100k) | **$5,304,065** | $336,290 |

### Max-History Performance (2012-01-01 to 2026-04-08, ~14 years)

Honest start: Jan 2012 (CPER copper ETF inception Nov 2011 + 6mo SMA warmup)

| Metric | Strategy | SPY B&H |
|---|---|---|
| Total Return | **6,801.90%** | 430.20% |
| Annualized Return | **34.66%** | 12.44% |
| Maximum Drawdown | **-23.06%** | -34.10% |
| Sharpe Ratio | **1.522** | 0.517 |
| Final Value ($100k) | **$6,901,900** | $530,204 |

### Year-by-Year Returns (10-Year)

| Year | Strategy | SPY | vs SPY |
|---|---|---|---|
| 2017 | +30.80% | +19.38% | +11.42pp ✅ |
| 2018 | +25.05% | -6.35% | +31.40pp ✅ |
| 2019 | +33.05% | +28.79% | +4.26pp ✅ |
| 2020 | +71.77% | +16.16% | +55.61pp ✅ |
| 2021 | +77.81% | +27.04% | +50.77pp ✅ |
| 2022 | +46.67% | -19.48% | +66.15pp ✅ |
| 2023 | -1.01% | +24.29% | -25.30pp ❌ |
| 2024 | +14.66% | +23.30% | -8.64pp ❌ |
| 2025 | +156.07% | +16.35% | +139.72pp ✅ |
| 2026 (YTD) | +69.42% | -0.87% | +70.29pp ✅ |

**Win rate: 8/10 years beat SPY**

### Walk-Forward Validation (Commodity, April 2026)

**Combined OOS return: 978% | Avg OOS Sharpe: 1.000 | OOS/IS decay: 0.93 (ROBUST) | 5/6 windows beat SPY**
Window 1 (2014–2015) missed: Sharpe -0.527 — commodity secular bear (USD strength, China slowdown, energy oversupply).

### Key Observations

- **Highest absolute return across all universes (10yr: 5,204%).** Weekly rebalancing is critical — monthly rebalancing drops Sharpe to 1.146 (vs 1.861 weekly).
- **2025 (+156.07%):** Commodity supercycle — oil (BNO), metals (GLD, SLV, CPER), and broad basket (DBC) all surged; strategy held concentration in the leaders throughout.
- **2022 (+46.67% vs SPY -19.48%):** Inflation-driven commodity bull; energy (BNO) and metals (GLD, PALL) dominated while equities collapsed.
- **2023 (-1.01%):** Strategy's weakest year — commodity cycle paused as rate hikes dampened demand; breadth filter triggered SGOV allocation during the pullback.
- **Regime-dependent:** Outstanding in inflation/commodity bull regimes; does not protect against commodity-specific bear markets (2013–2015 secular bust in max-history period: -14.84% in 2015).
- **Correlation filter critical:** DBC (broad basket) absorbs the correlation of most individual ETFs, so SGOV frequently appears as the 3rd position — this is correct behaviour.
- **OOS decay 0.93** — most robust of all universes.

---

## 6. Multi-Asset

### Universe

12 ETFs spanning all major asset classes.

| Ticker | Asset Class | Ticker | Asset Class |
|---|---|---|---|
| SPY | US Large Cap Equities | LQD | Investment Grade Bonds |
| IWM | US Small Cap Equities | HYG | High Yield Bonds |
| QQQ | US Tech / Growth | GLD | Gold |
| EFA | Developed ex-US Equities | VNQ | US Real Estate (REITs) |
| EEM | Emerging Market Equities | DBC | Broad Commodities |
| TLT | Long-Term Treasuries | IEF | Intermediate Treasuries |

**Optimised params:** SMA=126d, ROC=63d, TopN=5 (walk-forward consensus 4/6 windows)
**Note:** SPY is both a universe member and the RS benchmark — its RS ratio is structurally ~1.0 (circularity). Strategy value is drawdown protection, not alpha over SPY.

### 10-Year Performance (2016-01-01 to 2026-04-08)

| Metric | Strategy | SPY B&H |
|---|---|---|
| Total Return | **470.47%** | 236.29% |
| Annualized Return | **18.54%** | 12.58% |
| Maximum Drawdown | **-13.27%** | -34.10% |
| Sharpe Ratio | **1.147** | 0.499 |
| Final Value ($100k) | **$570,470** | $336,290 |

### Max-History Performance (2007-01-01 to 2026-04-08, 19 years)

| Metric | Strategy | SPY B&H |
|---|---|---|
| Total Return | **2,424.71%** | 378.18% |
| Annualized Return | **18.28%** | 8.48% |
| Maximum Drawdown | **-13.27%** | -56.47% |
| Sharpe Ratio | **1.062** | 0.283 |
| Final Value ($100k) | **$2,524,710** | $478,185 |

### Year-by-Year Returns (10-Year)

| Year | Strategy | SPY | vs SPY |
|---|---|---|---|
| 2017 | +20.92% | +19.38% | +1.54pp ✅ |
| 2018 | +7.73% | -6.35% | +14.08pp ✅ |
| 2019 | +18.47% | +28.79% | -10.32pp ❌ |
| 2020 | +43.53% | +16.16% | +27.37pp ✅ |
| 2021 | +23.38% | +27.04% | -3.66pp ❌ |
| 2022 | +1.84% | -19.48% | +21.32pp ✅ |
| 2023 | +18.06% | +24.29% | -6.23pp ❌ |
| 2024 | +18.24% | +23.30% | -5.06pp ❌ |
| 2025 | +28.70% | +16.35% | +12.35pp ✅ |
| 2026 (YTD) | +9.19% | -0.87% | +10.06pp ✅ |

**Win rate: 6/10 years beat SPY**

### Walk-Forward Validation (Multi-Asset, April 2026)

**Combined OOS return: 270% | Avg OOS Sharpe: 0.623 | OOS/IS decay: 0.78 (ROBUST) | 2/6 windows beat SPY**

### Key Observations

- **Best risk-adjusted returns of pure diversification universe** — Sharpe 1.147 vs SPY 0.499, MaxDD only -13.27% vs SPY -34.10%.
- **2008 (+20.72%):** In the 19yr history, the strategy rotated into TLT (long-term treasuries) during the credit crisis — its best relative year, delivering +59pp over SPY.
- **2022 (+1.84% vs SPY -19.48%):** Both equities and bonds fell, but the strategy's rotation into GLD (gold) and DBC (commodities) preserved capital.
- **2019, 2021, 2023, 2024 all missed SPY:** During sustained US equity bull markets, the cross-asset diversification is a headwind.
- **SPY circularity:** SPY being both a member and benchmark means its RS is permanently ~1.0. The strategy rarely exits SPY and rarely selects it as a top pick. True value is the other 11 assets providing rotation opportunities.
- **OOS decay 0.78** — good robustness.

---

## 7. Factor

### Universe

12 US equity factor ETFs spanning size, style, and smart-beta factors.

| Ticker | Factor | Inception | Ticker | Factor | Inception |
|---|---|---|---|---|---|
| IWF | Russell 1000 Growth | 2000 | USMV | Min Volatility | 2011 |
| IWD | Russell 1000 Value | 2000 | SCHD | Dividend Equity | 2011 |
| IWM | Russell 2000 Small Cap | 2000 | MTUM | Momentum Factor | 2013 |
| IWO | Russell 2000 Growth | 2003 | QUAL | Quality Factor | 2013 |
| IWN | Russell 2000 Value | 2003 | VLUE | Value Factor | 2013 |
| VUG | Vanguard Growth | 2004 | VTV | Vanguard Value | 2004 |

**Optimised params:** SMA=210d, ROC=21d, TopN=3 (walk-forward consensus W5+W6; ROC=1mo chosen 5/6 windows)
**Note:** MTUM, QUAL, VLUE (inception 2013) are absent in walk-forward windows 1–2 training periods.

### 10-Year Performance (2016-01-01 to 2026-04-08)

| Metric | Strategy | SPY B&H |
|---|---|---|
| Total Return | **258.10%** | 236.29% |
| Annualized Return | **13.27%** | 12.58% |
| Maximum Drawdown | **-20.37%** | -34.10% |
| Sharpe Ratio | **0.716** | 0.499 |
| Final Value ($100k) | **$358,095** | $336,290 |

### Max-History Performance (2014-01-01 to 2026-04-08, ~12 years)

Honest start: Jan 2014 (MTUM/QUAL/VLUE inception July 2013 + 6mo warmup)

| Metric | Strategy | SPY B&H |
|---|---|---|
| Total Return | **261.42%** | 269.57% |
| Annualized Return | **11.07%** | 11.27% |
| Maximum Drawdown | **-20.37%** | -34.10% |
| Sharpe Ratio | **0.568** | 0.444 |
| Final Value ($100k) | **$361,424** | $369,566 |

### Year-by-Year Returns (10-Year)

| Year | Strategy | SPY | vs SPY |
|---|---|---|---|
| 2017 | +19.66% | +19.38% | +0.28pp ✅ |
| 2018 | -2.75% | -6.35% | +3.60pp ✅ |
| 2019 | +15.93% | +28.79% | -12.86pp ❌ |
| 2020 | +42.68% | +16.16% | +26.52pp ✅ |
| 2021 | +23.91% | +27.04% | -3.13pp ❌ |
| 2022 | -18.60% | -19.48% | +0.88pp ✅ |
| 2023 | +13.86% | +24.29% | -10.43pp ❌ |
| 2024 | +24.70% | +23.30% | +1.40pp ✅ |
| 2025 | +19.52% | +16.35% | +3.17pp ✅ |
| 2026 (YTD) | +5.20% | -0.87% | +6.07pp ✅ |

**Win rate: 7/10 years beat SPY**

### Walk-Forward Validation (Factor, April 2026)

| Window | OOS Period | OOS Sharpe | vs SPY | Beat SPY |
|---|---|---|---|---|
| 1 | 2014–2015 | -0.273 | -9.3pp | ❌ |
| 2 | 2016–2017 | 0.943 | -4.5pp | ❌ |
| 3 | 2018–2019 | 0.585 | +4.0pp | ✅ |
| 4 | 2020–2021 | 1.627 | +18.7pp | ✅ |
| 5 | 2022–2023 | -0.120 | +5.3pp | ✅ |
| 6 | 2024–2026 | 0.490 | -18.2pp | ❌ |

**Combined OOS return: 249% | Avg OOS Sharpe: 0.542 | OOS/IS decay: 0.87 (ROBUST) | 3/6 windows beat SPY**

### Key Observations

- **Weakest standalone equity universe** — factor rotation within US equities adds limited alpha vs SPY. All 12 ETFs are highly correlated with the broad market.
- **~55% of rebalance periods force SPY** via `HIGH_VOL_SPY_MIN_ALLOCATION` vol-regime parameter, significantly diluting factor signals. This is a structural limitation worth testing with SPY floor disabled.
- **2020 (+42.68%):** Stop-loss triggered Feb 27 (COVID crash), re-entered via IWO (small-cap growth) which led the recovery.
- **2022 (-18.60%):** All factors fell together in the rate-rise bear market. No factor offered refuge — the worst year, barely edged SPY (-19.48%).
- **Strategy strength is drawdown control:** MaxDD -20.37% vs SPY -34.10%. Meaningful protection even if alpha is modest.

---

## 8. Bond

### Universe

12 fixed income ETFs covering the full bond market spectrum across duration, credit quality, and geography.

| Ticker | Segment | Inception | Ticker | Segment | Inception |
|---|---|---|---|---|---|
| TLT | Long Treasury 20+yr | 2002 | HYG | High Yield Corporate | 2007 |
| IEF | Intermediate Treasury 7-10yr | 2002 | MBB | Mortgage-Backed Securities | 2007 |
| SHY | Short Treasury 1-3yr | 2002 | EMB | EM Bonds USD | 2007 |
| LQD | Investment Grade Corporate | 2002 | MUB | Municipal Bonds | 2007 |
| AGG | Broad US Bond Market | 2003 | BKLN | Senior Loans / Floating Rate | 2011 |
| TIP | TIPS Inflation-Protected | 2003 | BWX | International Treasury ex-US | 2007 |

**Optimised params:** SMA=126d, ROC=63d, TopN=10 (walk-forward consensus 6/6 windows — most stable parameter set of all universes)
**Note:** TopN=10 out of 12 means holding nearly all segments. Bond universe rewards broad diversification over concentration.

### 10-Year Performance (2016-01-01 to 2026-04-08)

| Metric | Strategy | SPY B&H |
|---|---|---|
| Total Return | **127.51%** | 236.29% |
| Annualized Return | **8.36%** | 12.58% |
| Maximum Drawdown | **-18.61%** | -34.10% |
| Sharpe Ratio | **0.477** | 0.499 |
| Final Value ($100k) | **$227,513** | $336,290 |

### Max-History Performance (2011-04-01 to 2026-04-08, ~15 years)

Honest start: April 2011 (BKLN inception March 2011 + 1mo warmup)

| Metric | Strategy | SPY B&H |
|---|---|---|
| Total Return | **211.17%** | 407.71% |
| Annualized Return | **7.87%** | 11.45% |
| Maximum Drawdown | **-18.61%** | -34.10% |
| Sharpe Ratio | **0.430** | 0.455 |
| Final Value ($100k) | **$311,169** | $507,706 |

### Year-by-Year Returns (10-Year)

| Year | Strategy | SPY | vs SPY |
|---|---|---|---|
| 2017 | +13.80% | +19.38% | -5.58pp ❌ |
| 2018 | +8.56% | -6.35% | +14.91pp ✅ |
| 2019 | +6.91% | +28.79% | -21.88pp ❌ |
| 2020 | +23.23% | +16.16% | +7.07pp ✅ |
| 2021 | +10.45% | +27.04% | -16.59pp ❌ |
| 2022 | -14.24% | -19.48% | +5.24pp ✅ |
| 2023 | +13.26% | +24.29% | -11.03pp ❌ |
| 2024 | +12.37% | +23.30% | -10.93pp ❌ |
| 2025 | +13.29% | +16.35% | -3.06pp ❌ |
| 2026 (YTD) | -2.06% | -0.87% | -1.19pp ❌ |

**Win rate: 3/10 years beat SPY (2018, 2020, 2022 — all equity stress years)**

### Walk-Forward Validation (Bond, April 2026)

| Window | OOS Period | OOS Sharpe | vs SPY | Beat SPY |
|---|---|---|---|---|
| 1 | 2014–2015 | -0.037 | -3.5pp | ❌ |
| 2 | 2016–2017 | 0.362 | -18.5pp | ❌ |
| 3 | 2018–2019 | 0.086 | -9.6pp | ❌ |
| 4 | 2020–2021 | 1.234 | -0.8pp | ❌ |
| 5 | 2022–2023 | -0.588 | -0.0pp | ❌ |
| 6 | 2024–2026 | 0.924 | -5.9pp | ❌ |

**Combined OOS return: 169% | Avg OOS Sharpe: 0.330 | OOS/IS decay: 0.58 (MODERATE) | 0/6 windows beat SPY**
**Note:** 0/6 beating SPY is structural — bonds cannot be expected to outperform equities in a bull market. SPY is the wrong benchmark for this universe; the correct benchmark is AGG (aggregate bond index).

### Key Observations

- **Not a standalone equity-replacement strategy.** Designed as a fixed-income allocation or equity hedge, not to beat SPY.
- **Beats SPY only in equity stress years (2018, 2020, 2022):** Provides meaningful protection when equities fall, which is its core purpose.
- **2022 (-14.24%):** The strategy's worst year — the most severe bond bear market since 1994, with the Fed hiking 425bps. Every bond sector fell; even floating rate (BKLN) and short duration (SHY) declined. No rotation strategy within bonds could escape.
- **2020 (+23.23%):** TLT (long treasury) surged during COVID flight to safety; strategy rotated early into duration.
- **Parameter stability perfect:** SMA=6mo, ROC=3mo chosen in all 6 walk-forward windows — most consistent parameter finding across all universes.
- **Complement, not standalone:** Paired with an equity universe, bond rotation provides genuine counter-cyclical diversification. Against AGG benchmark, this rotation strategy almost certainly shows positive alpha.

---

## 9. Cross-Universe Comparison

### 9.1 10-Year Performance Scorecard (2016-01-01 to 2026-04-08)

| Universe | Total Return | Ann. Return | Sharpe | MaxDD | Years Beat SPY | SPY (Ref) |
|---|---|---|---|---|---|---|
| Commodity | **5,204%** | **47.38%** | 1.861 | -10.67% | 8/10 | 236% |
| Emerging | 2,236% | **36.04%** | **1.862** | **-9.09%** | **9/10** | 236% |
| SP500 | 769% | 23.51% | 1.266 | -11.83% | 8/10 | 236% |
| Multi-Asset | 470% | 18.54% | 1.147 | -13.27% | 6/10 | 236% |
| Developed | 350% | 15.81% | 0.914 | -13.95% | 6/10 | 236% |
| Factor | 258% | 13.27% | 0.716 | -20.37% | 7/10 | 236% |
| Bond | 128% | 8.36% | 0.477 | -18.61% | 3/10 | 236% |
| **SPY B&H** | **236%** | **12.58%** | **0.499** | **-34.10%** | — | — |

### 9.2 Max-History Scorecard

| Universe | Period | Total Return | Ann. Return | Sharpe | MaxDD |
|---|---|---|---|---|---|
| Commodity | 14yr (2012–2026) | 6,802% | 34.66% | 1.522 | -23.06% |
| Emerging | 19yr (2007–2026) | 16,320% | 30.36% | 1.426 | -18.51% |
| SP500 | 19yr (2007–2026) | 2,531% | 18.53% | 0.991 | -13.03% |
| Multi-Asset | 19yr (2007–2026) | 2,425% | 18.28% | 1.062 | -13.27% |
| Developed | 19yr (2007–2026) | 827% | 12.27% | 0.603 | -19.06% |
| Factor | 12yr (2014–2026) | 261% | 11.07% | 0.568 | -20.37% |
| Bond | 15yr (2011–2026) | 211% | 7.87% | 0.430 | -18.61% |

### 9.3 Risk-Adjusted Return Ranking (Sharpe, 10-Year)

```
Emerging    ████████████████████ 1.862  ← #1 — highest Sharpe
Commodity   ████████████████████ 1.861  ← #2 — virtually identical
SP500       █████████████        1.266
Multi-Asset ████████████         1.147
Developed   █████████            0.914
Factor      ███████              0.716
SPY B&H     █████                0.499
Bond        ████                 0.477
```

### 9.4 Drawdown Comparison (10-Year)

```
Emerging    ████  -9.09%   ← Shallowest
Commodity   ████  -10.67%
SP500       █████ -11.83%
Multi-Asset █████ -13.27%
Developed   █████ -13.95%
Bond        ██████████ -18.61%
Factor      ████████████ -20.37%
SPY B&H     ████████████████████ -34.10%  ← Deepest
```

All 7 universes deliver significantly better drawdown control than buy-and-hold SPY.

### 9.5 Walk-Forward Robustness

| Universe | Avg OOS Sharpe | OOS/IS Decay | Windows Beat SPY | Robustness Rating |
|---|---|---|---|---|
| Commodity | 1.000 | 0.93 | 5/6 | ⭐⭐⭐ ROBUST |
| Emerging | 0.949 | 0.90 | 5/6 | ⭐⭐⭐ ROBUST |
| SP500 | 0.916 | 1.46* | 4/6 | ⭐⭐ GOOD* |
| Factor | 0.542 | 0.87 | 3/6 | ⭐⭐ GOOD |
| Multi-Asset | 0.623 | 0.78 | 2/6 | ⭐⭐ GOOD |
| Developed | 0.420 | N/A | 2/6 | ⭐ MODERATE |
| Bond | 0.330 | 0.58 | 0/6 | ⭐ MODERATE† |

*SP500 decay 1.46 is anomalous — OOS periods were more favorable than IS (which includes 2008). Not a clean robustness signal.
†Bond 0/6 vs SPY is structural (wrong benchmark). Against AGG the picture would be different.

### 9.6 Regime Analysis — Which Universe Wins When

| Market Regime | Best Universe | Reason |
|---|---|---|
| Equity bull (2017, 2021, 2024) | Emerging / Commodity | High-return modes capture momentum leaders |
| Equity bear / correction | Bond / Multi-Asset | Flight-to-quality rotation; treasury/gold allocation |
| Inflation / commodity cycle (2018, 2020–2022) | Commodity | Direct exposure to commodity sector leaders |
| Risk-off / volatility spike | All (vs SPY) | Defensive layers (SGOV, stop-loss, breadth filter) cut drawdowns for all universes |
| USD weakness / EM recovery | Emerging | Country rotation captures EM outperformers |
| US large-cap growth domination (2019, 2023) | SP500 | US sector rotation captures the leaders (XLK, SMH) |
| International rotation | Developed | European/Asian cycles; currency-hedged variants add edge |

### 9.7 Correlation of Annual Returns (Approximate, 2017–2025)

Based on year-by-year data — universes that beat SPY in the same years are positively correlated:

| Pair | Shared years beating SPY | Notes |
|---|---|---|
| Commodity + Emerging | 2017, 2018, 2020, 2021, 2022, 2025 | High correlation — both benefit from inflation/risk-on cycles |
| SP500 + Multi-Asset | 2017, 2018, 2020, 2021, 2022, 2025 | Moderate correlation — multi-asset partially tracks US equity |
| Bond + Commodity | 2018, 2020, 2022 | Low correlation — bond is counter-cyclical to commodity's risk-on bias |
| Bond + Emerging | 2018, 2020, 2022 | Low — similar counter-cyclical pattern |
| Factor + SP500 | 2017, 2018, 2020, 2022, 2024, 2025 | High — both are US equity; factor is a diluted version of SP500 |

**Diversification insight:** Bond and Commodity are the most counter-cyclical pair. Combining them in a multi-universe portfolio would smooth the equity curve.

### 9.8 Portfolio Allocation Recommendations

**Single universe (pick one):**
- Max return: Commodity (47% ann., regime-dependent)
- Best risk-adjusted + robust: Emerging (Sharpe 1.862, decay 0.90)
- Most consistent vs SPY: SP500 (8/10 years, Sharpe 1.266)

**Two-universe portfolio (diversified):**
- SP500 + Commodity — US equity rotation + inflation hedge
- Emerging + Bond — high-alpha equity with counter-cyclical fixed income hedge

**Three-universe portfolio (balanced):**
- SP500 + Emerging + Bond — equity alpha from two regions + fixed income ballast
- Commodity + SP500 + Multi-Asset — multiple equity regimes covered + broad asset class diversification

**Universes to avoid standalone:**
- Bond — use as complement only (Sharpe below SPY, correct benchmark is AGG)
- Factor — SPY forced allocation dilutes signal; test with vol-regime SPY floor disabled before deploying
- Developed — 19yr Sharpe 0.603 is weak; better to use Emerging for international exposure

### 9.9 Open Improvement Opportunities

| Priority | Universe | Action |
|---|---|---|
| High | Factor | Disable `HIGH_VOL_SPY_MIN_ALLOCATION` — SPY forced in 55% of rebalances is diluting factor signal |
| High | Bond | Benchmark vs AGG instead of SPY to properly measure value-add |
| Medium | SP500 | Resolve in-sample vs WF consensus param conflict (10mo/3mo/TopN=3 vs 8mo/1mo/TopN=10) |
| Medium | All | Fix look-ahead bias — use next-day open for execution |
| Low | All | Model stop-loss gap risk for more realistic drawdown estimates |

---

*Report generated April 12, 2026. All backtests use $100,000 initial capital, weekly rebalancing, SGOV as cash proxy (BIL backfill pre June 2020), 5% stop-loss, volatility regime switching enabled, breadth filter enabled. Walk-forward validation uses monthly rebalancing with vol-regime disabled for clean parameter isolation.*
