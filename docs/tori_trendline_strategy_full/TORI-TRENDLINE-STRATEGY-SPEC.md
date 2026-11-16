# Tori Trades trendline strategy: full specification

Prepared 15 November 2026 (Africa/Johannesburg). Companion to `TORI-TRENDLINE-BUILD-ROADMAP.md`.

**Status of this document (revision 2).** It records what is publicly known about the strategy, separates what the sources say from what I had to decide in order to make it codable, and then gives a complete, deterministic specification (called `TRL_V1` below) that can be implemented and tested. `TRL_V1` is **a deterministic trendline strategy inspired by Tori Trades**, with variants identified by origin (TradeZella-style, FX Replay package, researcher-defined). It is not a reproduction of her discretionary method. Revision 2 incorporates an external review you supplied; see Appendix C.

**Nothing here shows the strategy has an edge.** The only profit claim is the author's own and is unverified. Everything below is a research specification, not a recommendation to trade. I am not a financial advisor.

---

## 0. How to read this document

Every rule carries a tag so you can tell its origin at a glance.

| Tag | Meaning |
| --- | --- |
| `[V]` | Stated in Tori's own video (read through a third-party transcript, see section 1) |
| `[TZ]` | Stated on the TradeZella "Trendline Strategy" playbook page |
| `[FXR]` | Stated on the FX Replay "Tori Trades Trend Line Strategy" page, which describes itself as her model *plus added mechanical rules* |
| `[CONV]` | A convention I chose so the rule can be coded. Not from any source. Must be frozen before any results are seen |
| `[CONV*]` | A number borrowed from one source's variant but applied beyond it (for example FX Replay's 6-candle spacing used in TradeZella-style strategies). Treated as a convention |
| `[AMBIG]` | The sources disagree or are silent. Section 6 lists each one and how `TRL_V1` resolves it |

Identifiers: parameters are `P-xx`, rules are `R-xx`, ambiguities are `A-xx`, hypotheses are `H-xx`.

---

## 1. Provenance and evidence quality

### 1.1 Sources used

| Source | What it is | What it gives | Reliability notes |
| --- | --- | --- | --- |
| Tori Trades YouTube video "This boring trading strategy made me $526,454" (June 2026) | Her own teaching video, read here via an auto-generated transcript on a summarizer site | The foundation: trendline drawing rules, top-down analysis, action line, safety line, position sizing, trailing, line maintenance | Transcript is machine-made and may contain errors. I did not watch the video. Contains promotional links (see 1.3) |
| TradeZella "Trendline Strategy" page | A trading-journal company's playbook page crediting Tori | Bounce, 2-touchpoint break, 3-touchpoint break; 4-hour timeframe; checks and invalidation rules; example trades on platinum and crude oil | Third-party write-up. Commercial page promoting a backtesting product |
| FX Replay "Tori Trades Trend Line Strategy" page | A backtesting-platform strategy library entry | The most mechanical version: 3 taps, spacing, span, slope limit, stop projection, 2R take profit, one attempt per line | Says it is her model "with some added mechanical rules", so it is not purely hers. Lists markets as indices and metals |
| Podcast and interview summaries (podwise, coconote, recapio, forex.in.rs, lilys) | AI-generated summaries of talks and reactions | Instruments she trades (platinum, previously crude oil, gold, corn), volatility-based sizing, an outside trader's reaction | Lowest reliability. Contain visible errors (one calls her by a different name, another mislabels what she does) |

### 1.2 What I could not find

- Her trade records, an audited track record, or any win rate, average R, profit factor or drawdown.
- The "playbooks" and "filters" she says exist on top of the foundation. She says there are ways to be more selective but does not detail them in the video.
- A precise definition of a "touchpoint", of a "break", or of how a line is chosen when several fit. These are the main sources of subjectivity.
- Whether her live trading matches the clean rules (she says some parts require discretion).

### 1.3 Claims and commercial context

- She says she turned a USD 5,000 account into over half a million dollars over about 11 years using the same system. This is self-reported and unverified.
- The video promotes a prop-firm evaluation (discount code) and the description reportedly links to a journal tool and a broker. This is a financial incentive to keep people trading, and it does not make the method wrong. It is a reason not to take performance claims at face value.
- The strategy is taught on futures (mainly platinum, previously crude oil). Your lab is forex. Behaviour on forex is untested.

### 1.4 Consequence for the build

Treat the public rules as a **hypothesis about a discretionary method**. A coded version is a *mechanical interpretation*. It can show whether a deterministic version of the idea has an edge; it cannot show whether Tori's discretionary version does. If the coded version fails, that is not proof the original fails, and if it succeeds, that is not proof the original works.

### 1.5 Departures from the source method

`TRL_V1` is legitimate research, but each row below is a choice that defines a *different mechanical strategy* from the one taught.

| Aspect | As taught or published | In `TRL_V1` | Reason |
| --- | --- | --- | --- |
| Drawing lines | Hand-drawn chain of connected lines, top-down, adjusted daily `[V]` | Deterministic enumeration of every eligible pivot pair with a fixed ranking; connected chains are a later variant | Needed to make it codable |
| Higher-timeframe context | Central to the method `[V][TZ]` | Baseline off; a D1 decision table as a separate strategy | Isolates the line logic; compared as a separate trial |
| Swing points | Seen by eye | Confirmed pivots, available only after 3 later bars | Causality |
| Line violations | "No poke" `[V]` | Strict penetration rule, no exceptions | One consistent policy |
| Extra filters | Not described | ATR-based tolerances, stop-distance window, spread limit | Determinism and execution realism |
| Spacing, age, slope numbers | Only FXR gives six-candle spacing, three-week formation, 45-degree angle | FXR numbers used for the FXR package; borrowed or separate numbers elsewhere | Sources disagree |
| Stop | Beyond the safety line `[V]`; projected 4 candles ahead `[FXR]` | Core: current line value plus buffer. FXR package: projected | A projected stop can sit inside the line (7.7.3) |
| Entry | Discretionary on the break `[V]`; market order after the close `[FXR]` | First eligible quote after the break bar closes; abstain if no safety line (waiting is a separate variant) | Avoids chasing and hidden discretion |
| Exits | Trail and close beyond `[V][TZ]`; fixed S/R target `[FXR]` | `E1` and `E2` as separate strategies; no trailing in `E2` is a convention | The FXR page does not mention trailing, which does not mean trailing is forbidden |
| Attempts | One per line `[FXR]` | One per line group, consumed at the trigger | Prevents retrying a line after a skip |
| Adding to winners | Allowed in a TZ example | Off | Conflicts with the lab's rules |
| Risk per trade | 1 to 2 percent suggested to beginners `[V]` | 0.25 percent (lab convention) | Conservative research setting |
| Instrument | Futures, mainly platinum and crude oil | EURUSD first | Lab scope |

---

## 2. The idea in one page

1. **Hypothesis:** price respects trendlines: it either bounces off a line or breaks through it. `[V][TZ]` A bounce or a cross does not by itself establish predictive value.
2. A line connecting rising lows is an **upward** (bullish) line. A line connecting falling highs is a **downward** (bearish) line. `[V]`
3. Analyse top-down: start at a high timeframe for context, work down to the timeframe you trade, redrawing lines at each level. `[V]`
4. Two lines run each trade. The **action line** is the one that tells you to enter. The **safety line** is the opposing line that tells you to leave. `[V][TZ]`
5. A break of an upward line means go **short**. A break of a downward line means go **long**. The direction of the break is the direction of the trade. `[V]`
6. The safety line is also the trailing stop. As price respects it, the stop moves with it. Close the trade when price violates it. `[V][TZ]`
7. Risk per trade is fixed in advance from the distance to the stop. Beginners are told 1 to 2 percent of capital. `[V]`
8. Lines are maintained every day: redraw them as new highs, lows and touches form. `[V]`
9. The sources claim the method works best on instruments that respect trendlines (metals and some commodities are named) and poorly in ranges or on instruments with frequent false breaks. `[TZ]` This is an unverified claim.

The author's own summary: **the action line gets you in, the safety line gets you out, and price tells you both.**

---

## 3. Glossary

| Term | Meaning |
| --- | --- |
| **Trendline** | A straight line through price swing points. Drawn with a ray from point A (a pivot) through point B (which fixes the angle) and extended forward. |
| **Upward line / support line** | Connects higher lows; sits below price while the uptrend holds. |
| **Downward line / resistance line** | Connects lower highs; sits above price while the downtrend holds. |
| **Touchpoint / tap** | A swing point that reaches the line and turns away. |
| **Action line** | The line whose break (or test, for a bounce) triggers entry. |
| **Safety line** | The line that protects the trade and doubles as the trailing stop. For a break trade it is a *new opposing line*. For a bounce trade it is the *same line* as the action line. |
| **Break** | Price closes beyond the action line. |
| **Bounce** | Price reaches an established line and respects it. |
| **Top-down analysis** | Drawing lines from the highest timeframe down to the trading timeframe. |
| **Chain** | A run of connected lines where each new line starts at the previous line's point B. |
| **Poke** | Price intersects the line when it should have stayed on one side. Lines are redrawn to avoid pokes. |
| **R** | The initial risk of a trade: distance from entry to stop. A "2R" target is twice that distance away. |

---

## 4. The method as Tori teaches it (video)

All items in this section are tagged `[V]` unless noted.

### 4.1 Tools and conventions

- Platform shown: TradingView, with the **ray** drawing tool (two clicks: point A is the pivot, point B sets the angle, the line then extends forward).
- Colour convention: upward lines green, downward lines red (cosmetic).
- Charts are kept naked: no indicators, no volume, no session lines.

### 4.2 Top-down analysis

Procedure shown on Bitcoin, which she says applies to any instrument:

1. Start at the monthly chart, then weekly, daily, 4-hour, 1-hour, and continue down only if you trade a lower timeframe (her example: a 5-minute trader continues 1h, 30m, 15m, 10m, 5m).
2. At each timeframe draw all the upward and downward lines you can, working toward the most recent price action.
3. Moving down a timeframe, lines will be slightly off because there is more detail. Adjust them so the rules still hold.
4. Stop when no further lines can be drawn on the current timeframe; that is the signal to move down.
5. Higher timeframes give context. Lower timeframes give entries, trade management and exits.

Why: higher timeframes carry more data and show the major trends and levels.

### 4.3 Rules for drawing lines

| # | Rule |
| --- | --- |
| 1 | **First upward line:** begins at the lowest visible point on the screen and must slope upward. A horizontal line through equal lows is wrong. |
| 2 | **First downward line:** begins at the highest visible point on the screen, with the same rules mirrored. |
| 3 | **Connected:** every new line starts where the previous line's point B was (the previous B becomes the new A). |
| 4 | **Maximum touchpoints:** capture as many touches as possible. |
| 5 | **No poking:** price must not have crossed or poked through the line. The line should "hold price up". If price already crossed, the line is too steep (or wrongly placed) and must be redrawn. |

Her example's first upward line captured three touchpoints.

### 4.4 The action line

- Price breaks an **upward** line: the uptrend is violated, buyers are no longer in control, so **short**.
- Price breaks a **downward** line: sellers are no longer in control, so **go long**.
- The broken line is the action line. The direction of the break gives the direction of the trade.
- She notes there are extra layers (filters, playbooks) that make setups more selective, but the video teaches only the foundation.

### 4.5 The safety line

- It is always the **opposing** line to the action line.
- Short trade (an upward line broke): the safety line is the downward line **above** price.
- Long trade (a downward line broke): the safety line is the upward line **below** price.
- While price respects the safety line you stay in. When price violates it, you close. This is the exit rule.

### 4.6 Position size and stop loss

- Size is a personal decision based on how much you are willing to lose if price reaches the safety line.
- The hard stop order is placed **on the far side of the safety line**, so it triggers if the line is violated. It is set before entry.
- Beginner rule of thumb: risk no more than **1 to 2 percent** of capital on a single trade. Her example: on USD 10,000 that is USD 100 to 200.
- The stated reason: with small risk you can take about ten losses in a row without serious damage. Check the arithmetic: ten full losses at 1 percent of remaining equity lose about 9.6 percent, and at 2 percent about 18.3 percent, before any gap or slippage excess. Small risk limits damage; it does not remove it.

### 4.7 Trailing the stop

- The safety line is not only the initial stop. As price moves in your favour and respects the line, the stop **moves along the line**.
- This is done by hand. Safety line and trailing stop are "one and the same".

### 4.8 The five-step trade

1. Top-down analysis and marked-up chart.
2. Wait for price to break a line (action line) and enter in the direction of the break.
3. Pre-plan position size and stop placement.
4. Trail the stop along the safety line.
5. Exit when price violates the safety line.

### 4.9 Ongoing maintenance

- The chart is not a static picture. Lines are updated **daily**, on the designated timeframe.
- When price has broken through a line and you missed the trade, redraw by moving point B to the new structure so the rules hold again, in preparation for the next move.
- Use the same three rules: connected, as many touches as possible, no pokes.

### 4.10 Practice route she recommends

Paper-trade on a simulated account at a realistic size, then consider a prop-firm evaluation. This part is promotional and not part of the trading rules.

---

## 5. The three published playbooks

### 5.1 TradeZella: bounce and break (`[TZ]`)

**General:** swing trading on **stocks, futures or forex**, no indicators. Timeframe: **4-hour**, with the daily or weekly chart used to confirm the main trend direction. The 4-hour chart is used to draw lines, find touchpoints and plan entries and exits.

**Setups:** trendline bounce and trendline break.

#### Bounce

| Item | Rule |
| --- | --- |
| Entry | Price reaches or tests an existing line |
| Touches | At least two or three clear touchpoints **before** entry |
| Age | At least one week of price data between the first touchpoint and entry |
| Stop | The trendline itself. If price **closes through** it, close immediately |
| Trailing | The stop may be trailed along the line as new valid swing points form |
| Room | Do not put the stop exactly at entry; leave enough room that ordinary wicks do not stop you out |
| Where it works | Instruments that respect lines consistently (metals and trending commodities). Less reliable where false breaks are frequent |
| Risk | The page describes it as the lowest-risk setup because invalidation is immediate. This is the page's claim: a tighter stop does not by itself mean a lower probability of loss or a better expectancy, especially when every trade risks the same amount of money |

#### 2-touchpoint break

| Item | Rule |
| --- | --- |
| Action line | Two clear touchpoints before the break |
| Age | About one week between first touchpoint and break (4-hour chart) |
| Safety line | A clear opposing line must exist at the break. If none exists, wait until price forms a clear high or low so you can draw one |
| Proximity | The break must happen **close to the safety line** so risk stays tight. If it is too far, skip |
| Invalid | Price moves back and **closes beyond the safety line**: close the trade |
| Management | Safety line is the stop; move it manually as new structure forms |
| Tracking | Record 2-touchpoint breaks separately from 3-touchpoint breaks |
| Character | More trades, but bigger losses are possible if risk is poorly managed |

#### 3-touchpoint break

Same as the 2-touchpoint break but with **three or more** touchpoints and **at least** one week of data between first touchpoint and break. The page states that more touchpoints make the break more reliable. This is an unverified claim (see H-01).

#### Example trades on the page

- Platinum 4h uptrend: bounce on the third touch of an upward line. Stop trailed along the line under each new swing low. Exit when price closed below the line.
- Platinum 4h: a 2-touchpoint break of a downward line, entered long when a bar closed above it. An opposing upward line was drawn as the safety line. The page says positions can be **added** as the trend continues. Exit when price broke below the safety line.
- Crude oil 4h: a 3-touchpoint break of an upward line, entered short on a close below it, with the opposing downward line used to trail the stop and exit on a close above it.

#### Testing advice on the page

Tag every setup as bounce, 2-touch break or 3-touch break and compare them. It says 30 to 50 trades per setup type is enough to see win rate, profit factor and expectancy. Such a sample can describe observed performance and expose implementation problems, but whether it supports a claim of an edge depends on effect size, variability, dependence between trades and how many alternatives were tried (see section 11.1).

### 5.2 FX Replay: the mechanical version (`[FXR]`)

| Item | Rule |
| --- | --- |
| Style, markets, sessions | Swing; indices and metals; asia, london, new york |
| Timeframe | 4-hour |
| Line requirements | At least **3 taps**, with **6 or more candles** between taps, drawn over **3 or more weeks**, and with a slope **under 45 degrees** when you are zoomed in on three months of price action |
| Entry | After a candle **closes** past the line, enter with a **market order** |
| Stop | Where the supporting "safety" trendline would **intersect 4 candles after the break** |
| Target | The **first support or resistance level that offers 2R or more** |
| Attempts | **One attempt per trendline** |
| Futures | Be careful around contract rollover |
| Execution aid | Alerts are used to time entries |

The page does not mention trailing the stop. That does not mean trailing is forbidden; the spec's `E2` simply has none, as a `[CONV]` choice.

### 5.3 Side-by-side comparison

| Parameter | Video `[V]` | TradeZella `[TZ]` | FX Replay `[FXR]` |
| --- | --- | --- | --- |
| Timeframe traded | Any (example to 1h) | 4h | 4h |
| Context | Top-down monthly to trade TF | Daily or weekly confirms trend | Not stated |
| Minimum touches | As many as possible | 2 or 3 (bounce); 2 or 3+ (breaks) | 3 |
| Spacing between touches | Not stated | Not stated | 6+ candles |
| Minimum line age | Not stated | About 1 week (first touch to entry or break) | 3+ weeks |
| Slope limit | Must slope; not horizontal | Not stated | Under 45 degrees at a 3-month view |
| Break defined as | Price breaks the line | A bar closes beyond the line | A candle closes past the line |
| Entry order | On the break | Not specified | Market order |
| Stop | Beyond safety line | Safety line, with some room | Safety line projected 4 candles ahead |
| Exit | Price violates safety line | Close beyond safety line | TP at first S/R giving 2R or more |
| Trailing | Yes, along safety line | Yes, manual | Not mentioned |
| Adding to position | Not mentioned | Allowed ("add more positions") | Not mentioned |
| One attempt per line | Not mentioned | Not mentioned | Yes |
| Risk per trade | 1 to 2 percent (beginner) | Not stated | Not stated |

---

## 6. Where the sources conflict or are silent

Each row is something the code must decide. The resolution column is what `TRL_V1` does. These resolutions are `[CONV]` and are frozen before any results are seen. Changing one afterwards creates a new strategy version.

| ID | Question | What the sources say | `TRL_V1` resolution |
| --- | --- | --- | --- |
| A-01 | What counts as a touchpoint? | Never defined | A confirmed swing point of the line's kind whose extreme lies **on the correct side of the line** (no penetration) and within `TOUCH_TOL` of it, chosen chronologically with at least `MIN_TAP_SPACING` bars after the previous accepted touch (7.3.5) |
| A-02 | Can wicks poke through a valid line? | Video: no poke at all. TZ and FXR: the *close* is what breaks it | **Strict validity.** Any penetration beyond the line by more than `PEN_ALLOW` (default 0) makes the line `POKED`. There is **no touch exception**, and a later pivot confirmation never restores an earlier eligibility. A tolerant policy (non-zero `PEN_ALLOW`) is a declared later variant, not in the initial trials |
| A-03 | What is a break? | "Breaks", "closes beyond", "candle closes past" | A completed bar whose close is beyond the line value on that bar by at least `BREAK_MARGIN` |
| A-04 | Which line is *the* action line when several valid lines exist? | Not addressed (she draws a chain by eye) | Every valid line is a candidate with its own opportunity group. Simultaneous same-direction breaks collapse into one group; opposing breaks abstain. Following connected chains is a departure listed in 1.5 and a later variant |
| A-05 | How many touches? | "As many as possible"; 2 or 3; 3 | `BRK3`: 3 or more. `BRK2`: **exactly 2**, so the two groups never overlap. `BNC`: at least 2 prior touches. `FXR_M`: 3 or more |
| A-06 | How old must the line be? | None; about 1 week from first touch to entry or break; "drawn over 3+ weeks" | Two separate measures: **age** (first touch to the signal bar) used by `BRK*` and `BNC` (30 H4 bars, TZ); **formation span** (first touch to last touch) used by `FXR_M` (90 H4 bars). Both assume 6 bars per day and 5 days per week |
| A-07 | "Under 45 degrees when zoomed in on 3 months" | Depends on the chart's pixel shape and scale, which the source does not give | Two *approximate* metrics (7.3.8): a normalised-angle test with a declared aspect ratio, and an ATR-slope test. Both apply in `FXR_M`; only the ATR-slope test applies elsewhere. Neither claims to reproduce the original chart view |
| A-08 | What if no safety line exists at the break? | TZ: wait until a clear high or low forms so a line can be drawn | **Baseline abstains** (`NO_SAFETY_LINE`). Waiting is a separate, fully specified variant `DLY` (7.7.5) because waiting needs its own entry rule |
| A-09 | What makes a safety line valid? | "A clear line" | A valid opposing line with at least `SAFETY_MIN_TOUCHES` touches, not poked, on the correct side of price, built from data available at the trigger bar's close |
| A-10 | How close must the break be to the safety line? | "Close", "tight", otherwise skip | Stop distance between `MIN_STOP_ATR` and `MAX_STOP_ATR` times ATR_SMA14, and spread no more than `MAX_SPREAD_STOP_FRAC` of stop distance |
| A-11 | Stop: line value now, line value in 4 bars, or beyond the line? | Beyond the line `[V]`; projected 4 bars ahead `[FXR]`; some room `[TZ]` | **Core:** line value at the latest completed bar, pushed outward by `STOP_BUFFER` (`STOP_PROJ_BARS = 0`). **`FXR_M` only:** line value projected 4 bars ahead, then buffered. A projected stop can sit on the wrong side of the current line (7.7.3), which is why it is not the core rule |
| A-12 | Exit rule: hard stop, close beyond the line, or target? | All three appear | `E1` core: hard stop, trail along the safety line, close-beyond exit. `E2`: hard stop plus S/R target, **no trailing as a `[CONV]` choice** (the FXR page does not mention trailing, which does not mean trailing is forbidden) |
| A-13 | What is "support/resistance" for the 2R target? | Not defined | Horizontal levels from clustered confirmed pivots, with a fixed clustering procedure (7.7.6) |
| A-14 | Add to winners? | TZ example says yes | **Off** in v1 (conflicts with the lab's no-pyramiding rule). A later variant only |
| A-15 | Is top-down context a requirement? | Yes in the video, "confirm trend" in TZ, absent in FXR | Baseline: context gate **off**. Variant: the D1 decision table in 7.6. Compared as separate strategies |
| A-16 | Timeframe alignment (H4 bar boundaries) | Not stated | Declared from the data calendar, not guessed from a broker server label |
| A-17 | Does the poke check include the break bar? | Not stated | No. Poke checks cover completed bars strictly before the break bar. The break bar is judged by the break rule |
| A-18 | How is a missed break handled (price already beyond the line when a valid line first becomes valid)? | Video: redraw the line for the next move | Discard (`MISSED_BREAK`). No retrospective entry |
| A-19 | What exactly is "maintenance" in code? | "Redraw daily" | Lines are re-derived deterministically at every new confirmed pivot and on every completed bar for poke checks. Each change is a new immutable revision. Past signals are never rewritten |
| A-20 | Instrument choice | Futures, metals | `EURUSD` first (lab scope). Metals and others are separate declared instruments. Your decision (roadmap Phase 0) |
| A-21 | When is the one attempt consumed? | FXR: "one attempt per trendline" | **At the trigger** (the break event or bounce contact). From then on the line group cannot produce another signal, whatever happens next: entry, skip, expiry or no fill. This avoids hidden retries of the same line |
| A-22 | What precision can the data support? | Not discussed | Two declared data levels, Q (quote based) and B (bar based approximation), with different execution models (7.1). Level B never claims Level Q precision |
| A-23 | Where do the spacing numbers come from? | Only FXR states 6 candles | `MIN_TAP_SPACING = 6` is `[FXR]` for `FXR_M` and `[CONV*]` (borrowed) for the other strategies |
| A-24 | Is a bounce trigger a touch? | TZ: "reaches or tests" the line | No. A **bounce contact** is an ordinary completed bar that meets the conditions in 7.7.2. A **confirmed touch** is a confirmed pivot. A contact may later become a touch, but entry never waits for that |

---

## 7. Operational specification `TRL_V1`

### 7.1 Scope and data levels

- **Research and demo only.** No real-money mode, no automatic orders by default, no martingale, no averaging down, no recovery sizing.
- **Instrument (initial):** EURUSD, USD accounting. Other instruments need their own contract and data declarations.
- **Timeframes:** H4 for lines and setups, D1 for the optional context gate. H1 data are the source for aggregation.
- **Completed bars only.** A higher-timeframe bar is never used before it has completed and its data are available.

**Data qualification levels** (every output carries its level label):

| | Level Q: quote based | Level B: bar based approximation |
| --- | --- | --- |
| Input | Timestamped bid/ask quotes with ordering and clock evidence | Historical H1 bars (bid OHLC plus a spread field, or source-supplied mid candles) |
| Geometry basis | Midpoint of synchronised quotes | Source mid candles if supplied, otherwise **bid-only** candles. **Never** average bid and ask candle highs or lows: that is not the high of synchronised midpoints |
| Entry | First eligible quote after the trigger bar's close, quote age at most 2 s, spread at most 1.5 pips | Ask-equivalent (bid plus spread field) at the **open of the first H1 bar after the trigger H4 bar's close**. Quote age is not testable and is not claimed |
| Stops and targets | Observed executable bid/ask | H1 bid high/low (long exits) and bid plus spread (short exits); intrabar order unknown |
| Same-bar stop and target | Resolved from finer observations if available, else adverse | Always adverse |
| Claims allowed | Execution research | Strategy-behaviour research only. Cannot satisfy the broker-performance or demo gate |

The manifest records the geometry basis (`mid_sync`, `mid_candles_source`, `bid_only`) and the level.

### 7.2 Parameter table (frozen before results)

| ID | Parameter | Default | Source | Notes |
| --- | --- | --- | --- | --- |
| P-01 | `TF_SETUP` | H4 | `[TZ][FXR]` | |
| P-02 | `TF_CONTEXT` | D1 | `[TZ]` | W1 and MN only as later declared variants |
| P-03 | `PIV_RADIUS` | 3 | `[CONV]` | Strict centred extremum over `2r+1` completed bars. Equal extrema do not confirm |
| P-04 | `MIN_TAP_SPACING` | 6 bars | `[FXR]` for `FXR_M`; `[CONV*]` elsewhere | Between consecutive accepted touches |
| P-05 | Touch requirement | `BRK3`: 3 or more; `BRK2`: exactly 2; `BNC`: 2 or more prior; `FXR_M`: 3 or more | `[TZ][FXR]` | Counts include A and B |
| P-06 | `AGE_MIN_BARS` | 30 (first touch to signal bar) | `[TZ]` | `BRK*` and `BNC` |
| P-06b | `FORMATION_MIN_BARS` | 90 (first touch to last touch) | `[FXR]` | `FXR_M` only |
| P-07 | `TOUCH_TOL` | 0.25 x ATR_SMA14, measured at the touch pivot's confirmation bar | `[CONV]` | Fixed once the pivot is confirmed |
| P-08 | `PEN_ALLOW` | 0 | `[V]` strict | Penetration beyond this poked the line. No touch exception |
| P-09 | `MAX_ANGLE_DEG` | 45 | `[FXR]` | Approximate test (7.3.8) |
| P-10 | `ANGLE_WINDOW_BARS` | 390 | `[CONV]` | About 3 months of H4 forex bars (6 x 5 x 13) |
| P-11 | `CHART_ASPECT` | 0.5 | `[CONV]` | Assumed chart height to width |
| P-12 | `MAX_SLOPE_ATR_PER_BAR` | 0.5 | `[CONV]` | Alternative slope test |
| P-13 | `BREAK_MARGIN` | 1 tick | `[CONV]` | |
| P-14 | `SAFETY_MIN_TOUCHES` | 2 | `[CONV]` | |
| P-15 | `STOP_PROJ_BARS` | core: 0; `FXR_M`: 4 | `[CONV]`; `[FXR]` | Core stop sits at the current line value plus buffer |
| P-16 | `STOP_BUFFER` | max(1 tick, 0.10 x ATR_SMA14) | `[CONV]` borrowed from the lab plan | Pushes the stop away from price |
| P-17 | `MIN_STOP_ATR` / `MAX_STOP_ATR` | 0.5 / 2.5 | `[CONV]` | Stop distance in ATR_SMA14 |
| P-18 | `MAX_SPREAD_STOP_FRAC` | 0.10 | `[CONV]` | Effective entry spread divided by stop distance |
| P-19 | Quote eligibility window | Until the next H4 bar closes | `[CONV]` | Miss it and the setup abstains |
| P-20 | `TP_R_MIN` | 2.0 | `[FXR]` | `E2` only |
| P-21 | `RISK_FRAC` | 0.0025 of executable equity | Lab convention (video says 1 to 2 percent) | Sizing is not a pure scale factor (see 7.9) |
| P-22 | `DAILY_LOSS_PAUSE` | 1 percent of day-reference equity | Lab convention | Entry pause latch |
| P-23 | `MAX_CONCURRENT` | 1 per account | Lab convention | Each independent simulation is its own account |
| P-24 | Attempt consumption | At the trigger | `[CONV]` | A-21 |
| P-25 | `CONTEXT_GATE` | off (baseline) | `[CONV]` | Decision table in 7.6 |
| P-26 | Level Q execution limits | Quote age 2 s, spread 1.5 pips | Lab convention | Frozen research assumptions |
| P-27 | `MAX_HOLD` | none (dataset boundary only) | `[V]` | Report holds over 30 days as a diagnostic |
| P-28 | `LINE_LOOKBACK_BARS` | 600 H4 bars | `[CONV]` | Only pivots inside this window are eligible (about 20 weeks) |
| P-29 | `PIVOT_CAP` | 256 per kind | `[CONV]` | Safety bound applied after the window, so it cannot block forever |
| P-30 | `RETIRE_AFTER_BARS` | 500 | `[CONV]` | Valid but untriggered lines retire |
| P-31 | `CONTEXT_MAX_ATR` | 3 x ATR_SMA14(D1) | `[CONV]` | D1 lines further than this are ignored by the gate |
| P-32 | `MAX_CHASE_ATR` | 1.0 | `[CONV]` | `DLY` variant only |
| P-33 | `SETUP_EXPIRY_BARS` | 10 | `[CONV]` | `DLY` variant only |

### 7.3 Definitions

7.3.1 **Bars.** Completed, qualified H4 bars aggregated from the admitted source. The bar calendar, DST handling and weekend gaps are declared with the data manifest. Unknown clock offsets stay unknown.

7.3.2 **`ATR_SMA14`.** The **simple** arithmetic mean of the last 14 true ranges (true range uses the preceding close), on completed bars only. This is *not* TradingView's default ATR, which smooths with an RMA. Compare implementation output with charts only after accounting for this difference.

7.3.3 **Confirmed pivot.** Bar `i` is a pivot high if its high is strictly greater than the highs of the `P-03` bars on each side; pivot low is the mirror. It is *available* only when bar `i + r` has completed. Occurrence and confirmation are stored separately. A bar that is both a high and a low pivot is unresolved and not used.

7.3.4 **Line.** A pair of confirmed pivots `(A, B)` of the same kind with `B` later than `A`, `B.index - A.index >= MIN_TAP_SPACING`.

- **Support line** (upward): pivot lows with strictly rising prices.
- **Resistance line** (downward): pivot highs with strictly falling prices.

Horizontal and wrong-direction lines are not lines in `TRL_V1`. The line value at bar `k` is the linear interpolation or extrapolation in bar-index space, in exact arithmetic.

7.3.5 **Touch (confirmed).** Pivots of the line's kind are processed **chronologically** from `A`. A pivot is accepted as a touch if (a) its extreme is on the correct side of the line (for a support line, the pivot low is at or above the line value at its bar) or exactly on it, (b) the price distance to the line is at most `TOUCH_TOL`, and (c) it is at least `MIN_TAP_SPACING` bars after the previously accepted touch. A pivot that fails (c) is skipped (earliest wins). `A` and `B` are accepted by construction.

7.3.6 **Poke (strict).** A completed bar strictly before the evaluated bar whose low (support) or high (resistance) penetrates the line value on that bar by more than `PEN_ALLOW`. A poked line is `POKED` and cannot generate a break or bounce. There is no exemption for contacts that later turn out to be pivots: validity is decided with the information available at each bar, and **a later confirmation never restores an earlier eligibility**.

7.3.7 **Age and formation span.** *Age* is the number of bars from the first touch to the signal bar. *Formation span* is the number of bars from the first touch to the last touch.

7.3.8 **Slope tests (approximate).**

- *ATR-slope test:* `abs(slope_price_per_bar) / ATR_SMA14 <= MAX_SLOPE_ATR_PER_BAR`, with ATR at the evaluation bar.
- *Normalised-angle test:* take the last `ANGLE_WINDOW_BARS` bars, let `range` be their high minus low. Then `angle = atan( (abs(slope_price_per_bar) * ANGLE_WINDOW_BARS / range) * CHART_ASPECT )` in degrees; the test is `angle <= MAX_ANGLE_DEG`. With `CHART_ASPECT = 0.5`, a line that rises the full 3-month range over 3 months is near 27 degrees, so 45 degrees is a very steep limit. This approximates the FXR wording without the original chart's scale and dimensions, so it is not a reproduction of it. Neither test by itself demonstrates robustness.

7.3.9 **Valid line.** Not `POKED`; touch count as required by the strategy; age or formation span as required; slope tests pass; confirmed using only data available at the evaluation time.

7.3.10 **Prices and ticks.** Stops are rounded away from price to an allowed tick before sizing (a wider stop). Targets are rounded toward the entry. Buy orders trade at the ask and sell orders at the bid. A long stop triggers when the executable bid is at or below the stop; a short stop when the ask is at or above it. A long target needs the bid at or above the target; a short target needs the ask at or below it.

### 7.4 Line construction (deterministic)

At every completed H4 bar, using pivots inside the last `LINE_LOOKBACK_BARS` bars and at most `PIVOT_CAP` per kind (exceeding the cap records `search_incomplete` and blocks new entries for that snapshot only):

1. Enumerate every pair `(A, B)` of same-kind pivots with the right slope sign and `B.index - A.index >= MIN_TAP_SPACING`.
2. For each pair compute touches (7.3.5), poke status (7.3.6), age or span, and slope tests.
3. Keep the valid lines.
4. **Deduplicate by touch set.** Several pairs can produce the same accepted touch set because of the tolerance. Keep the line through the **earliest and latest touch of that set**; if more than one pair qualifies, keep the one with the smallest sum of absolute touch distances (exact arithmetic), then the smallest canonical id. A touch set that is a strict subset of another line's set is dropped.
5. Rank with a frozen lexicographic order: more touches, longer age, more recent last touch, earlier first-touch id. The canonical line id breaks only display ties and never chooses a trade.
6. Persist an immutable revision for every change (new line, line poked, line retired). Never rewrite earlier revisions.

Complexity is quadratic in the number of pivots, which the window and cap keep small.

### 7.5 Line and group lifecycle

**Line states:** `CANDIDATE` -> `VALID` -> (`TRIGGERED` | `POKED` | `RETIRED`).

- `VALID` lines extend forward each bar and are poke-checked every bar.
- A poke moves a line to `POKED`. A replacement may arise at a later pivot confirmation as a *new* line with a new id and its own group. This is what "adjust the line" means in code.
- A line retires when valid for more than `RETIRE_AFTER_BARS` bars without a trigger, or when a newer line with a strict superset of its touches replaces it.
- A break or bounce contact moves the line to `TRIGGERED`.

**Opportunity group states:** `OPEN` -> `CONSUMED`. The group is consumed **at the trigger** (A-21). Once consumed it cannot produce another signal, whether the setup then enters, skips, abstains, expires or fails to fill. A genuinely new confirmed pivot that creates a new line is a new group.

### 7.6 D1 context gate (decision table)

The baseline ignores context. The variant applies this table. Terms:

- **`trade_direction`:** `LONG` or `SHORT`, the direction the setup would trade. A break of a falling resistance line is `LONG`; a break of a rising support line is `SHORT`; a bounce off support is `LONG`; a bounce off resistance is `SHORT`. (The direction of the *broken line* is the opposite of the trade for breaks, so the gate uses trade direction only.)
- **`S_below`:** the nearest valid, unpoked D1 support line below price within `CONTEXT_MAX_ATR` x ATR_SMA14(D1), if any.
- **`R_above`:** the nearest valid, unpoked D1 resistance line above price within the same distance, if any.
- **`D1_bias`:**

| `S_below` | `R_above` | `D1_bias` |
| --- | --- | --- |
| exists | none | `BULLISH` |
| none | exists | `BEARISH` |
| exists | exists | `NEUTRAL` (inside a channel or wedge) |
| none | none | `UNAVAILABLE` |
| D1 data incomplete or unfinished bar involved | | `UNAVAILABLE` |

| `trade_direction` | `D1_bias` | Outcome |
| --- | --- | --- |
| LONG | BULLISH | allow |
| LONG | BEARISH | block (`CONTEXT_CONFLICT`) |
| LONG | NEUTRAL | abstain (`CONTEXT_NEUTRAL`) |
| LONG | UNAVAILABLE | abstain (`CONTEXT_UNAVAILABLE`) |
| SHORT | BEARISH | allow |
| SHORT | BULLISH | block (`CONTEXT_CONFLICT`) |
| SHORT | NEUTRAL | abstain (`CONTEXT_NEUTRAL`) |
| SHORT | UNAVAILABLE | abstain (`CONTEXT_UNAVAILABLE`) |

D1 lines use the same engine on D1 bars with `AGE_MIN_BARS` scaled to 15 D1 bars. Weekly and monthly layers and the full chain are later declared extensions.

### 7.7 Setups

All setups evaluate on completed H4 bars. Entry follows the data-level rules in 7.1.

#### 7.7.1 `BRK3`, `BRK2` (breaks)

- **Formation:** a valid resistance line (long) or support line (short) with the touch requirement for the strategy.
- **Trigger:** a bar closes beyond the line by `BREAK_MARGIN`, with the previous close on the other side or on the line. Formation and trigger cannot be the same bar. **The group is consumed here.**
- **Missed break:** if the line first becomes valid when price has already closed beyond it, discard (`MISSED_BREAK`).
- **Safety line:** the best valid opposing line (long: a support line below price; short: a resistance line above price), ranked by proximity to price, then touches. It must exist **at the trigger bar's close**. If none exists the setup abstains (`NO_SAFETY_LINE`).
- **Stop (core):** safety-line value at the trigger bar, pushed away from price by `STOP_BUFFER`, rounded outward to a tick. Check the stop window and spread (P-17, P-18).
- **Stop already crossed:** if the executable exit-side quote at the moment of entry is already at or beyond the stop (long: bid at or below the stop), skip (`STOP_ALREADY_CROSSED`).
- **Entry:** first eligible quote after the trigger bar's close (Level Q) or the next H1 open (Level B). Missing the eligibility window abstains.

#### 7.7.2 `BNC` (bounce)

- **Formation:** a valid support line (long) or resistance line (short) with at least 2 prior confirmed touches and age of at least `AGE_MIN_BARS`.
- **Bounce contact** (not a confirmed touch): a completed bar that (a) has its extreme within `TOUCH_TOL` of the line on the correct side without penetrating, (b) closes on the correct side, and (c) is at least `MIN_TAP_SPACING` bars after the last accepted touch **and** after any earlier contact. A contact is the trigger; **the group is consumed here.** It need not be a pivot, and entry never waits for pivot confirmation.
- A bar that penetrates the line is a poke (the line becomes `POKED`) and is never a contact.
- **Stop:** line value at the contact bar, pushed away by `STOP_BUFFER` (never exactly at entry, per `[TZ]`). Same stop window, spread and `STOP_ALREADY_CROSSED` checks.
- **Entry:** first eligible quote after the contact bar's close.
- An immediate-touch limit-order variant is a later declared strategy.

#### 7.7.3 `FXR_M` (mechanical FX Replay version)

`BRK3` with touches of 3 or more, spacing 6 `[FXR]`, **formation span** 90 `[FXR]`, both slope tests, market-style entry after the break bar's close, **stop projected 4 bars ahead** `[FXR]` then buffered, and exit `E2`.

Warning on the projected stop. For a long trade with a safety-line slope `m > 0` per bar and buffer `b`, the stop is `L(t) + 4m - b`. Whenever `4m > b` this sits **above the current safety-line value**, so price can stop the trade out while still respecting the line. That differs from wording elsewhere that places the stop beyond the line, and it is the reason the projection is applied to `FXR_M` only and not to the core strategies.

#### 7.7.4 Exit models

- **`E1` (core):** a hard stop order at the stop level. Each completed bar: (a) if the bar closes beyond the safety line value on that bar, exit on the next executable quote; (b) the stop is moved to the line value at that bar minus (plus) the buffer **only in the favourable direction**, never loosened. The safety line is frozen to the id used at entry. A replacement line replaces it only if it is formed after entry and gives a more protective stop; until then the old line, even if poked, still defines the close-beyond exit and the hard stop stays where it is.
- **`E2` (FXR):** hard stop at the initial level and a take-profit at the first S/R level at least `TP_R_MIN` x R away. No trailing and no close-beyond exit (`[CONV]`, because the source does not mention trailing).
- A trade holds until the stop, target, close-beyond exit or the dataset boundary. No time exit.

#### 7.7.5 `DLY` (delayed-safety variant, declared but not in the initial trials)

Used only if Phase 10 shows `NO_SAFETY_LINE` abstentions are common. After a break whose safety line does not yet exist:

- The setup enters `AWAITING_SAFETY` for at most `SETUP_EXPIRY_BARS` (10) H4 bars. The group is already consumed at the trigger.
- **Invalidated** if any completed bar closes back across the action line (failed break); if a bar closes more than `MAX_CHASE_ATR` x ATR_SMA14 beyond the trigger bar's close in the trade direction (no chasing); at expiry; or if the context gate (when enabled) fails.
- A valid safety line is accepted the first time one exists at a bar's close; that bar is the **decision bar**. No retest or extra confirmation is required (a declared simplification).
- **Stop:** safety-line value at the decision bar, buffered, as in the core rule. The projection starts at the decision bar, never at the original break.
- Entry on the first eligible quote after the decision bar's close, with the usual checks.

#### 7.7.6 Support and resistance for `E2`

Levels are recomputed each bar over the last 500 H4 bars. Method:

1. Collect confirmed pivots of the same kind from H4 and from D1. A D1 pivot and an H4 pivot with the same kind and the same extreme price (to the tick) are **one observation**.
2. Sort by price. Start a cluster at the lowest unassigned price; add each following price while `price - cluster_lowest <= TOUCH_TOL` (ATR_SMA14 of H4 at the evaluation bar).
3. A cluster needs at least 2 observations. Its representative price is the **median** of its prices.
4. Resistance levels come from pivot-high clusters and support levels from pivot-low clusters. The target is the nearest level on the profit side at least `TP_R_MIN` x R from entry. If there is none, skip (default). A fixed 2R target is a declared alternative.

### 7.8 Event order and causality

1. Process events in observed order. Bounded timestamp uncertainty must fit the bar and freshness requirements. If ordering stays material and unresolved, reject the decision.
2. A pivot confirmed at bar `i + r` cannot be used before then and cannot backdate an entry to bar `i`.
3. Lines, touches and pokes use only data available at the decision time. A line drawn today does not exist in yesterday's evaluation.
4. **A stop cannot execute before the position exists.** The position starts at the entry fill. Price movement inside the trigger bar, or before the fill, cannot create a loss. After the fill, if one bar's range contains both the stop and the target and the order cannot be resolved from finer observations, take the adverse outcome. Never assume a win.
5. Mutating or appending future data must leave every earlier published line, decision, fill and equity point unchanged (a required test).

### 7.9 Risk and sizing

1. Risk budget: `RISK_FRAC` x positive executable equity.
2. Per-lot loss to the stop includes spread and commission. Divide, then floor to the lot step. Skip if below the minimum lot. Never round up.
3. Also constrain by free margin, lot limits and headroom above the daily pause floor (EURUSD hypothetical profile: 100,000 units per lot, 0.01 step, 1 lot cap, 30:1 leverage).
4. **One reservation per account.** Each independent strategy simulation (7.12, experiment A) is its own account. A combined portfolio (experiment C) and the demo adapter share one reservation, so only one strategy should be enabled at a time in a demo. Opposing simultaneous setups abstain. Same-side groups reuse the ranking from 7.4 with no display tie-break; an unresolved tie abstains.
5. Daily reference equity is frozen at the UTC-day boundary. Equity at or below 99 percent latches an entry pause for that day, including floating losses. Held positions continue to be managed.
6. **Risk fraction is not a pure scale factor.** Lot floors, minimum lots, margin limits and the daily pause change which trades occur, so results at different risk fractions are not simply rescaled versions of each other. R-multiple statistics are comparable only when the same trades occur.
7. Stops and pauses are not guaranteed loss caps. Gaps, slippage and financing can exceed them, and every exceedance is reported.

### 7.10 Costs

Spreads come from the recorded bid/ask (Level Q) or the bar spread field (Level B). Hypothetical profiles carried from the lab: base and adverse commission USD 7 and 10 per round-turn lot, slippage 0.2 and 0.5 pip per fill, adverse spread floor 1.2 pips, financing per lot per rollover as declared. Embedded spread and slippage are counted once. **Swing holds make financing material**: a trade held over a Wednesday rollover (typically triple swap) is charged accordingly. These are hypotheses, not verified broker charges.

### 7.11 Group identity

Each line has a canonical id. Lines that share the same terminal touches or are aliases at different revisions belong to one opportunity group. Group merges keep the union of consumed state. Consumption (at the trigger) survives restarts. A new confirmed pivot that produces a new line is a new group.

### 7.12 Strategy IDs and experiment types

**Strategy IDs** (initial list):

| ID | Setup | Touches | Stop | Exit | Context gate |
| --- | --- | --- | --- | --- | --- |
| `TRL_BRK3_E1` | `BRK3` | 3 or more | core | `E1` | off |
| `TRL_BRK2_E1` | `BRK2` | exactly 2 | core | `E1` | off |
| `TRL_BNC_E1` | `BNC` | 2 or more prior | core | `E1` | off |
| `TRL_FXR_M` | `FXR_M` | 3 or more, FXR package | projected 4 | `E2` | off |
| `TRL_BRK3_E1_D1` | `BRK3` | 3 or more | core | `E1` | D1 table |

`TRL_FXR_M` is a **package** (formation, slope tests, stop and exit all differ from `TRL_BRK3_E1`). Differences between them cannot be attributed to any single rule.

**Experiment types** (declared per analysis):

| Experiment | What it is | Used for |
| --- | --- | --- |
| **A. Independent simulations** (default) | Each strategy runs on its own fresh account with its own reservation | Comparing strategies without competition for capital |
| **B. Paired exit comparison** | Take the entry events of `TRL_BRK3_E1` and apply `E1` and `E2` to the **same entries with the same initial stop and sizing** (entries with no valid 2R target are reported separately) | Hypotheses about exits (H-04, H-05) |
| **C. Combined portfolio** | Several strategies share one account and one reservation | Later, only to see how they interact. Results reflect competition for capital as well as rules |

Overlap note: `BRK2` (exactly 2 touches) and `BRK3` (3 or more) never share a break. A "minimum two touches" policy is the union of the two groups and is reported descriptively, not as a separate trial.

No parameter grid, no best-month selection, no per-setup dropping after seeing results. A revision is a new trial and cannot reuse a holdout as if it were untouched. Every strategy, variant and parameter set tried during development counts toward the trial total.

### 7.13 Journal fields per setup

Strategy id, data level and geometry basis, line id and revision, kind, touches and their times, age and formation span, slope metrics, trigger bar, safety line id and revision, stop distance in pips and ATR, spread, planned size, entry quote or bar, exit reason, R multiple, financing, days held, D1 bias and outcome, and a reason code for every abstention.

### 7.14 Partition boundaries and open positions

Each cell starts with its own fresh account and no incoming position. Prior bars may warm up indicators. At the end of a partition, an open position is closed at the first eligible executable quote inside the partition. If there is none, the position is reported as `OPEN_AT_BOUNDARY` and unavailable: it is **excluded from closed-trade statistics** (and listed separately), while equity is marked at the last executable bid or ask and the gap is disclosed. A development trade is never closed by a quote from the held-out period.

---

## 8. Known weaknesses and failure modes

| # | Failure mode | Why it matters | What the spec does about it |
| --- | --- | --- | --- |
| 1 | **Hindsight line drawing** | A line drawn after the fact always fits. This is the biggest trap in manual replay and chart-based backtests | Lines are derived only from data available at the decision time; strict poke rule with no retroactive restoration; every revision is immutable |
| 2 | **Degrees of freedom in line choice** | Which two points, how many touches, what tolerance. Many lines fit; picking the one that worked is overfitting | Fixed enumeration, fixed ranking, frozen parameters, no grid, every attempted variant counted |
| 3 | **False breaks** | The sources say fake-outs are part of the system, and some instruments produce many | Close-based break, safety line required, proximity limit, one attempt per line |
| 4 | **Ranging markets** | The source says ranges provide few valid setups | Report results by regime; the spec does not try to fix this |
| 5 | **Few trades** | Swing setups can take days or weeks. 50 closed trades may need many years or many instruments | Phase 10 counts signals before any outcome is looked at |
| 6 | **Financing and gaps** | Multi-day holds across rollovers; weekend gaps through stops | Swap modelled; gap fills at the first breached quote with adverse slippage; exceedances reported (example 9.6) |
| 7 | **Metals and futures behave differently from EURUSD** | The sources use platinum and crude oil and say instrument choice matters | Instrument declared up front; metals only as a declared second instrument |
| 8 | **Trailing makes results path-dependent** | Small differences in how the safety line is revised change exits | Revisions are deterministic and logged; the stop never loosens |
| 9 | **Slope rule depends on chart shape** | The "45 degrees" rule is visual | Two explicit, approximate metrics and a flagged assumption (A-07) |
| 10 | **Selection risk across many tests** | Testing several strategies, instruments and revisions makes a lucky result more likely, even with frozen parameters | Every strategy, variant and parameter set tried is counted; inference only with a frozen method that accounts for the count |
| 11 | **Bar-data precision** | H1 bars cannot show quote age, first executable quote or intrabar order | Data levels Q and B; Level B makes no execution-precision claims |
| 12 | **Projected stops can sit on the wrong side of the line** | A stop above a rising safety line can be hit while price still respects the line | Core strategies use the current line value; projection only in the `FXR_M` package |

---

## 9. Worked examples (illustrative numbers, not real market data)

All examples use EURUSD, H4 bars (6 per day), tick 0.00001, USD 10,000 account, 0.25 percent risk, 1 pip = 0.0001 = USD 10 per standard lot, `STOP_BUFFER = max(1 tick, 0.10 x ATR_SMA14)`.

### 9.1 A long break (`TRL_BRK3_E1`, core stop)

ATR_SMA14 = 0.00180 (18 pips).

- **Action line (resistance, falling):** confirmed pivot highs at bar 0 (1.0990), bar 22 (1.0960) and bar 47 (1.0935). Slope = (1.0935 - 1.0990) / 47 = -0.000117 per bar. Spacing between touches is at least 6 bars; age at bar 80 is 80 bars (at least 30). Slope relative to ATR is 0.065, under the 0.5 limit. No bar penetrated the line. Line value at bar 80 is about 1.08964.
- **Trigger:** bar 80 closes at 1.0905, more than a tick above the line, and bar 79 closed below it. The group is consumed here.
- **Safety line (support, rising):** confirmed pivot lows at bar 30 (1.0840) and bar 66 (1.0862). Slope = 0.0022 / 36 = 0.00006111 per bar. Two touches (the minimum), not poked, below price.
  - Line value at bar 80 = 1.0862 + 14 x 0.00006111 = **1.087056**.
- **Stop (core):** buffer = max(1 tick, 0.10 x 0.00180) = 0.00018. Stop = 1.087056 - 0.00018 = 1.086876, rounded outward to **1.08687**.
- **Entry:** first eligible quote after bar 80's close, ask 1.09070 and bid 1.09064. The bid is above the stop, so the stop is not already crossed.
- **Stop distance:** 1.09070 - 1.08687 = 0.00383 = 38.3 pips = **2.13 x ATR**. Inside 0.5 to 2.5. Spread 0.6 pip is 1.6 percent of the stop distance, under 10 percent.
- **Size:** risk = 0.25 percent of 10,000 = USD 25. Loss per lot to the stop is about 38.3 x USD 10 = USD 383, plus about USD 7 commission and USD 4 slippage = USD 394. Lots = 25 / 394 = 0.063, floored to **0.06 lots**.
- **Management (`E1`):** each new bar the stop moves up with the line value (never down). If a bar closes below the safety line, exit on the next executable quote.

**The same trade with the `FXR_M` projected stop (comparison):** the line projected to bar 84 is 1.0862 + 18 x 0.00006111 = **1.08730**. Stop = 1.08730 - 0.00018 = **1.08712**. Distance from the entry = 1.09070 - 1.08712 = 35.8 pips = **1.99 x ATR**. This stop is **about 0.64 pip above the current line value (1.087056)**, so a small dip that still respects the line could stop the trade. That is why the projection is not the core rule. (An earlier draft of this document used 1.08720, which was an arithmetic slip.)

### 9.2 A short break (`TRL_BRK3_E1`)

ATR_SMA14 = 0.00160.

- **Action line (support, rising):** pivot lows at bar 5 (1.1000), bar 40 (1.1035) and bar 70 (1.1066). Slope = 0.0035 / 35 = 0.0001 per bar; line value at bar 70 is 1.1065, so the third low sits 1 pip above the line, on the correct side and within `TOUCH_TOL` = 0.25 x 0.0016 = 4 pips. Age at bar 100 is 95 bars.
- **Trigger:** bar 99 closed at 1.1101 (line value 1.1094, above it). Bar 100's line value is 1.1095 and it closes at 1.1088, more than a tick below. Short signal; group consumed.
- **Safety line (resistance, falling):** pivot highs at bar 60 (1.1150) and bar 90 (1.1130); slope = -0.0020 / 30 = -0.00006667. Value at bar 100 = 1.1130 - 10 x 0.00006667 = 1.112333.
- **Stop:** buffer = 0.10 x 0.0016 = 0.00016. Stop = 1.112333 + 0.00016 = 1.112493, rounded outward (up) to **1.11250**.
- **Entry:** bid 1.10880, ask 1.10886. The ask is below the stop, so not already crossed.
- **Stop distance:** 1.11250 - 1.10880 = 37.0 pips = **2.31 x ATR** (inside 2.5). Spread 1.6 percent of distance.
- **Size:** about USD 25 / (37.0 x 10 + 11) = 0.066, floored to **0.06 lots**.
- **Trailing:** at bar 110 the line value is 1.1130 - 20 x 0.00006667 = 1.111667, so the stop tightens to 1.111827 (buffer 0.00016), about 6.7 pips lower than at entry.

### 9.3 A rejected wick penetration (strict validity)

ATR_SMA14 = 0.0016. Resistance line through pivot highs at bar 10 (1.2000) and bar 40 (1.1970): slope -0.0001 per bar.

- At bar 52 the line value is 1.1958. The bar's high is 1.1960, which **penetrates by 2 pips** (`PEN_ALLOW = 0`), and it closes at 1.1949, back inside.
- Under strict validity the line is `POKED` at bar 52. There is no exception even though that wick might later be confirmed as a pivot at bar 55: the engine could not know at bar 52, and a later confirmation never restores eligibility.
- At bar 70 a bar closes above the old line (value 1.1940). **No signal**, reason code `POKED`. The group of the old line is not consumed by a trigger, but the line is dead.
- A replacement line can form through the bar 40 pivot and the (now confirmed) bar 52 pivot: slope = (1.1960 - 1.1970) / 12 = -0.0000833. It has 2 touches, a new id and its own group. It qualifies for `BRK2` (exactly 2) but not `BRK3`.

### 9.4 Delayed safety line (`DLY` variant, not in the initial trials)

ATR_SMA14 = 0.0020. A resistance line is broken at bar 200: the bar closes at 1.2510, above the line value 1.2505. The group is consumed. No valid support line exists at that close, so the baseline strategy abstains (`NO_SAFETY_LINE`).

In `DLY`: the setup waits. At bar 202 a pivot low forms at 1.2475 (confirmed at bar 205's close), which together with the earlier low at bar 180 (1.2420) gives a support line with slope (1.2475 - 1.2420) / 22 = 0.00025 per bar.

- Decision bar = bar 205. The bar closes at 1.2525, which is 0.0015 = **0.75 ATR** beyond the trigger close, so within `MAX_CHASE_ATR` = 1.0. No bar closed back below 1.2505.
- Line value at bar 205 = 1.2475 + 3 x 0.00025 = 1.24825. Stop = 1.24825 - 0.0002 = **1.24805** (the projection starts at the decision bar, not the break).
- Entry ask 1.25260: stop distance 45.5 pips = 2.28 x ATR, valid.
- Had bar 205 closed at 1.2535 instead (0.0025 = 1.25 ATR beyond the trigger close), the setup would be **invalidated for chasing**. Had any bar from 201 to 205 closed below 1.2505, it would be invalidated as a failed break. After bar 210 with no valid line, it expires.

### 9.5 Simultaneous signals

On bar 300: (a) a 3-touch falling resistance line closes broken (long signal, group G1) and (b) a 3-touch rising support line closes broken (short signal, group G2). Both signals are on the same bar and opposite: **both abstain** (`OPPOSING_SIGNAL`). Both groups are **consumed** at the trigger, so neither can signal again.

If instead two falling resistance lines (L1 with 3 touches and L2 with 4 touches) break on the same bar and are not aliases, both groups are consumed and both are long. The frozen ranking (touches, then age, then last-touch recency) picks L2 for the trade. An exact tie on every criterion would abstain, and the display id never decides.

### 9.6 A gap through the stop

The 9.1 long (0.06 lots, entry 1.09070, stop 1.08687, planned loss at the stop about USD 24 including costs) is held over a weekend. The Friday close bid is 1.0900. The Sunday open bid is 1.0850, a gap of 50 pips below the stop.

- The stop fills at the **first observed breached executable quote**, 1.0850, with adverse slippage of 0.5 pip: **1.08495**.
- Realised loss in price = 1.09070 - 1.08495 = 57.5 pips = **1.50 R** (R = 38.3 pips). In money: about 0.06 x 57.5 x USD 10 = USD 34.5 plus costs, roughly **USD 35, about 1.4 times the planned USD 25 risk**.
- Reported as an entry-risk exceedance. The daily pause check uses the new equity; if equity is at or below 99 percent of the day reference, new entries pause for that day.

### 9.7 Why a tiny account breaks the rules

On USD 20, a 0.25 percent budget is USD 0.05, far below the loss of the smallest lot to a 38-pip stop. The engine would skip every trade (`BELOW_MIN_LOT`). It reports this and does not raise risk to force trades.

---

## 10. Hypotheses the sources imply (testable)

Each result is classified as **supported**, **not supported** (the estimate and its uncertainty rule out the claimed benefit), or **inconclusive** (too few trades, or intervals too wide). Too few trades is inconclusive, never a falsification, and no benefit found is not proof that no benefit exists.

| ID | Claim in sources | How to test | What would count against it |
| --- | --- | --- | --- |
| H-01 | 3-touch breaks are more reliable than 2-touch breaks `[TZ]`, an unverified claim | `TRL_BRK3_E1` against `TRL_BRK2_E1` (exactly 2 touches), independent accounts | No difference or the reverse, with adequately narrow intervals |
| H-02 | Breaks close to the safety line carry tighter risk and are better `[TZ]` | R-distribution and expectancy by stop-distance bucket (descriptive only) | No relationship |
| H-03 | Bounces are the lowest-risk setup because invalidation is immediate `[TZ]` | Compare loss size, loss frequency and expectancy of `TRL_BNC_E1` with the breaks. A tighter stop does not by itself mean a lower probability of loss or better expectancy, particularly when each trade risks the same money | Larger or more frequent losses, or worse expectancy |
| H-04 | A 2R target at S/R is available often enough to matter `[FXR]` | Experiment B (paired exits on identical entries): share of entries with a valid S/R at 2R or more, and results of `E2` against `E1` on those entries | Rare, or `E2` underperforms |
| H-05 | Trailing the safety line captures more profit than a fixed target `[V]` | Experiment B, same entries, same initial stop | `E2` equal or better |
| H-05b | The FXR package performs differently from the core | `TRL_FXR_M` against `TRL_BRK3_E1` as a whole. **Cannot be attributed to any single rule** (formation, slope tests, stop and exit all differ) | n/a (descriptive) |
| H-06 | Higher-timeframe context improves selection `[V][TZ]` | `TRL_BRK3_E1_D1` against `TRL_BRK3_E1`. The gate removes many trades, so sample size may be the limiting factor | No improvement with adequate samples |
| H-07 | Instruments that respect lines (metals) work better than others `[TZ]` | A declared second instrument | No difference |
| H-08 | Few setups appear in ranging markets `[TZ]` | Setup count by regime | Setups appear equally |

The premise that price "respects" trendlines is the strategy's **hypothesis**. A bounce or a cross does not by itself establish predictive value.

Descriptive breakdowns are not permission to drop the losing setup after the fact.

---

## 11. Metrics and screens

Report: gross and net P&L, expectancy in R and in currency, wins and losses, payoff, profit factor, costs, financing, observed executable drawdown, exposure time, turnover, monthly and quarterly results, largest loss, entry-risk exceedances, unavailable intervals, no-trade reason counts, days held distribution, and setups by line kind, touch count and stop-distance bucket.

### 11.1 The 50-trade screen, described honestly

Reuse the lab's descriptive screen: positive net profit and net expectancy under both validation cost profiles, observed drawdown at most 5 percent, at least 50 closed validation trades and 24 monthly marks. `INSUFFICIENT` means too few trades, `FAIL` means failing economically, `UNAVAILABLE` means missing qualification.

What 50 trades can and cannot do:

- They can reveal implementation problems and describe observed performance.
- Whether they support an **edge claim** depends on effect size, variability, dependence between trades and the number of alternatives tested.
- Illustration: 30 wins from 50 trades is a 60 percent observed win rate, but the Wilson 95 percent interval is about **46 to 72 percent**, assuming independent outcomes with a common win probability. That says nothing about profitability, which also depends on payoff sizes.
- Overlapping, correlated trades (for example several instruments in the same market move) are not independent, so the real uncertainty is wider.

A pass earns further research review, not a profitability claim. Before any inferential claim, freeze (a) the exact development and test dates, (b) the treatment of positions crossing partition boundaries (7.14), and (c) the uncertainty method, accounting for the number of attempted alternatives. Research on backtest overfitting stresses that the count of tried strategies and settings must be reported.

### 11.2 Position-sizing arithmetic worth knowing

- Ten consecutive full losses at 1 percent of remaining equity lose about 9.6 percent (1 - 0.99^10); at 2 percent, about 18.3 percent (1 - 0.98^10), before any gap or slippage excess. "Small risk" limits damage but does not remove it.

---

## 12. Relationship to your Elliott wave work

You noticed similarities. They are real, and they are the reason this project can reuse most of the lab.

| Concept | Elliott plan (144) | Trendline strategy |
| --- | --- | --- |
| Raw structure | Confirmed swing pivots at three radii | Confirmed swing pivots; touches are pivots |
| Causality | A pivot is available only after the bars that confirm it | Same. A touch exists only once confirmed; validity is decided with data available at each bar |
| Invalidation | Correction extreme plus buffer (wave 2 or 4 low) | Safety line value plus buffer |
| Trigger | H1 close beyond the prior wave extreme | H4 close beyond the action line |
| Context | D1 and H4 must agree, else abstain | Optional D1 table, else abstain |
| Ambiguity policy | Competing counts, abstain if conflicting | Competing lines, abstain on opposing or tied groups |
| One attempt | Consumed at the first eligible quote | **Consumed at the trigger** (a deliberate difference, A-21) |
| Missed trigger | Discard, never chase | Discard, never chase (the `DLY` variant has an explicit chase limit) |
| Costs, ledger, risk, daily pause, restart, checkpoints | Specified in 144 | Reused unchanged |
| Replay viewer with a time cursor | Planned | Same viewer, with line layers |
| Geometry | Channel guideline: parallel lines through wave anchors | Trendline geometry is the same mathematics |

Differences that matter:

- Elliott needs a large pattern grammar. The trendline strategy has a **small** rule set, so the implementation is smaller.
- The trendline strategy's weakness is **line-selection subjectivity**, where Elliott's is count ambiguity. Both are handled the same way: deterministic enumeration, frozen ranking, abstain on a tie.
- The trendline strategy's timeframe is H4 with multi-day holds, so financing and gaps matter more than in the H1 Elliott design.
- The Elliott plan is **paused, not cancelled**. Nothing in it changes. Shared modules are used through stable interfaces, not edited in place (roadmap section 3).

---

## 13. What transfers to binary options and what does not

Your binary trading uses 1-minute charts with 1 to 5 minute expiries and an 85 percent payout.

- **Product-specific limits.** In the fixed-expiry, fixed-payout format you trade on IQ Option, my understanding is that you hold to expiry, so there is no stop, trailing exit or target (check your platform, because I have not verified this for it). That is a property of the product, not of binary options in general: Nadex, a US-regulated exchange, documents that its binary contracts can be closed before expiry, while many offshore brokers do not allow it.
- **Transfers as an idea only:** a well-tested trendline with several touches that breaks on a close, on a 5- or 15-minute chart, might predict direction over the next few candles. That is a different, unverified hypothesis. If you want to test it, add a "D Trendline break" strategy to your signal log, with fixed written rules for touches and breaks, and judge it separately.
- **Break-even maths:** with a win paying 0.85 times the stake, a loss losing the stake, no fees and no special tie rules, the break-even win rate is 1 / 1.85 = **54.05 percent**. This strategy's published rules say nothing about win rate.

---

## 14. Manual checklist (for hand-practice on a demo chart)

Use it to build intuition and golden examples before coding. Do not treat results as evidence: manual replay is open to hindsight.

1. Open H4. Confirm higher-timeframe direction on D1 (and W1 if you like).
2. Mark the confirmed swing highs and lows (use a fixed rule, for example 3 candles each side).
3. Draw upward lines through rising lows and downward lines through falling highs. Lines must slope, must **not be penetrated** by any candle wick, and should be at least a week old by the signal.
4. Count touches (only pivots on the correct side of the line, spaced at least 6 candles apart). Require the touches for the setup you are tracking (exactly 2, 3 or more, or 2 prior for a bounce).
5. Mark the opposing line (the safety line). If there is none at the close of the break candle, you have no trade (log it as a skip).
6. Wait for an H4 candle to **close** beyond the action line.
7. Place the stop just beyond the **current** value of the safety line (not a projected value), with a small buffer. Check that it is not already crossed and that the distance is neither tiny nor too wide (about 0.5 to 2.5 times ATR).
8. Compute size from the stop distance and your risk percent. Skip if the minimum lot already exceeds your risk.
9. Enter on the next quote. One attempt per line, even if you skip.
10. Each new bar, tighten the stop along the safety line. Never loosen it.
11. Exit when a bar closes beyond the safety line, or at the stop, or at the target if you use one.
12. Log it with the fields in 7.13, including trades you skipped and why.

---

## 15. Open questions

1. What are Tori's actual "playbooks" and filters? Her video says they exist and does not describe them.
2. How does she decide which of several fitting lines to use? The video shows one line per step.
3. Does she enter on the close of the break candle or earlier in live trading?
4. How often do trades exit by the stop, by the safety line, or by a target? No data found.
5. Does the method transfer from platinum and crude oil to EURUSD? Unknown.
6. Her own live records, if any are public, would turn this specification from hypothesis into something checkable. None were found.

To close gaps 1 to 3, watch her original videos (including the trade breakdowns she mentions on a live account) and write down, per trade, the lines she used and the exact entry candle. Any such observations become *development evidence* only, not an untouched test.

---

## 16. Source list

- Tori Trades (YouTube), "This boring trading strategy made me $526,454", June 2026. Read through an auto-generated transcript on a summarizer site: https://lilys.ai/ko/notes/trading-strategy-20261012/simple-strategy-half-million-profit and a highlights page https://videohighlight.com/v/PnIkSLm2yRk
- TradeZella, "Trendline Strategy" playbook: https://www.tradezella.com/strategies/trendline-strategy
- FX Replay, "Tori Trades Trend Line Strategy": https://fxreplay.com/strategies/tori-trades-trendlines-strategy
- Podcast and interview summaries (lower reliability): https://podwise.ai/episodes/8438124 , https://coconote.app/notes/6bf665f6-d390-41a0-bb88-1ceb75e1689c , https://recapio.com/digest/trendline-trading-expert-mastering-her-uncles-old-school-strategy-tori-trades-by-titans-of-tomorrow , https://recapio.com/digest/lance-breitstein-reacts-to-tori-trades-trendline-trading-strategy-by-theonelanceb , https://www.forex.in.rs/miami-trader-strategy-2 , https://www.forex.in.rs/tori-swing-strategy
- Nadex, binary options pages (early closing of binary contracts): https://nadex.com/learning/how-to-trade-binary-options and https://nadex.com/pricing
- External review of revision 1 (supplied by you), whose points are listed in Appendix C.

---

## Appendix A. One-page cheat sheet

```
SETUP TF      H4 (lines, setups)         CONTEXT    D1 (optional gate, decision table 7.6)
LINES         support = rising lows      resistance = falling highs
VALID LINE    NOT PENETRATED by any wick (strict), touches per strategy,
              spacing >= 6 bars, age >= 30 (TZ-style) or formation span >= 90 (FXR_M),
              slope tests pass (approximate)
TOUCH         confirmed pivot on the correct side, within 0.25 ATR_SMA14, chronological
BREAK         completed H4 bar closes beyond line by >= 1 tick  -> group CONSUMED here
SAFETY LINE   best valid opposing line, must exist at the trigger close, else abstain
STOP (core)   safety line value at the latest bar, pushed out by max(1 tick, 0.1 ATR)
STOP (FXR_M)  safety line value projected 4 bars ahead, then buffered (can sit inside the line)
FILTERS       stop 0.5 to 2.5 ATR; spread <= 10% of stop; stop not already crossed
ENTRY         first eligible quote after the trigger close (Level Q) / next H1 open (Level B)
EXIT E1       hard stop; close beyond safety line; stop trails line, never loosens
EXIT E2       hard stop; TP at first S/R >= 2R; no trailing (convention)
RISK          0.25% per trade (lab); one reservation per account; 1% daily pause; no adds
NEVER         martingale, averaging down, chasing a missed break, widening a stop,
              fitting lines after the fact, picking a strategy after seeing results
```

## Appendix B. Declarative config (starting point)

```yaml
version: TRL_V1
instrument: EURUSD
data_level: Q            # or B (approximate); output labels follow this
geometry_basis: mid_sync # mid_sync | mid_candles_source | bid_only
timeframes: {setup: H4, context: D1}
atr: {name: ATR_SMA14, period: 14, smoothing: simple}
pivot: {radius: 3, lookback_bars: 600, cap_per_kind: 256}
lines:
  min_tap_spacing_bars: 6
  touch_tol_atr: 0.25            # ATR_SMA14 at the touch pivot's confirmation bar
  pen_allow_ticks: 0             # strict validity, no touch exception
  max_angle_deg: 45
  angle_window_bars: 390
  chart_aspect: 0.5
  max_slope_atr_per_bar: 0.5
  retire_after_bars: 500
break: {margin_ticks: 1}
consume_attempt_at: trigger
safety: {min_touches: 2, buffer: {ticks: 1, atr_frac: 0.10}}
stop_filters: {min_stop_atr: 0.5, max_stop_atr: 2.5, max_spread_stop_frac: 0.10, reject_if_already_crossed: true}
target: {r_min: 2.0, sr_lookback_bars: 500}
risk: {fraction: 0.0025, daily_pause: 0.01, max_concurrent_per_account: 1, pyramiding: false}
context_gate: {max_distance_atr_d1: 3.0, table: "spec 7.6"}
strategies:
  TRL_BRK3_E1:    {setup: BRK3, touches: {min: 3}, age_min_bars: 30, stop_proj_bars: 0, exit: E1, context: off}
  TRL_BRK2_E1:    {setup: BRK2, touches: {exactly: 2}, age_min_bars: 30, stop_proj_bars: 0, exit: E1, context: off}
  TRL_BNC_E1:     {setup: BNC,  touches: {min: 2, prior: true}, age_min_bars: 30, stop_proj_bars: 0, exit: E1, context: off}
  TRL_FXR_M:      {setup: FXR_M, touches: {min: 3}, formation_min_bars: 90, stop_proj_bars: 4, exit: E2, context: off, angle_tests: both}
  TRL_BRK3_E1_D1: {setup: BRK3, touches: {min: 3}, age_min_bars: 30, stop_proj_bars: 0, exit: E1, context: D1}
declared_not_run:
  TRL_BRK3_DLY_E1: {setup: BRK3, delayed_safety: {expiry_bars: 10, max_chase_atr: 1.0}, exit: E1}
experiments: {A: independent, B: paired_exit_on_BRK3_entries, C: combined_portfolio_later}
```

## Appendix C. Revision log

**Revision 2 (15 November 2026): changes made after an external review you supplied.** The review's main points were checked, and I agreed with the substance of all of them. The decisions I made where the review left a choice open are marked.

| Review point | What changed |
| --- | --- |
| 1. Present `TRL_V1` as an adaptation; add a departures table; label "E2 has no trailing" as a convention | Added section 1.5, the `[CONV*]` tag and the `[CONV]` label on `E2`. Strategies are now identified by origin (TZ-style, FXR package, researcher-defined) |
| 2. Fix the touch, poke and pivot-confirmation contradiction | **Chose strict validity** (no touch exception, no retroactive restoration). Tolerant validity is a declared later variant. Added the **bounce contact** versus **confirmed touch** distinction (A-24) |
| 3. Separate the projected stop from the safety-line exit; correct the example | **Core stop now uses the current line value plus buffer**; the 4-bar projection is only in `FXR_M`. The example arithmetic was corrected (1.08730, 1.08712, 35.8 pips, 1.99 ATR). Added `STOP_ALREADY_CROSSED` |
| 4. Waiting for a safety line conflicts with "never chase"; define attempt consumption once | **Baseline abstains when no safety line exists.** Waiting is the separate `DLY` variant with invalidation, a chase limit and decision-bar stop projection. **Attempts are consumed at the trigger** everywhere |
| 5. `BRK2` and `BRK3` overlap; shared reservation confounds comparisons; H-04 and H-05 are not clean | **`BRK2` is now exactly 2 touches.** Added experiment types A, B and C, a paired exit comparison, and marked `TRL_FXR_M` as a package whose differences cannot be attributed |
| 6. D1 gate needs an explicit decision table | Rewritten as 7.6 with trade direction, D1 bias, a bias table and an outcome table |
| 7. Match execution claims to the data; midpoint construction; stop before position exists | Added data levels Q and B, geometry-basis labels (never average bid and ask candle extremes), a Level B execution model, and clarified that a stop cannot fire before the position exists (7.8.4) |
| 8. Determinism gaps | Named `ATR_SMA14`; fixed ATR timing for tolerance; chronological touch selection; canonical geometry on deduplication; S/R clustering; age versus formation span; lookback window before the pivot cap; safety-line replacement; tick rounding and trigger sides; boundary handling (7.14). "Faithful" angle wording removed |
| 9. Describe the 50-trade screen correctly; inconclusive is not falsification; count attempted alternatives | Rewrote 11.1 and section 10; Wilson interval example (about 46 to 72 percent) added; trial counting made explicit |
| Wording fixes | "Price respects trendlines" now stated as a hypothesis; "more touches more reliable" marked as unverified source claim; "lowest risk" for bounces qualified; ten-loss arithmetic (9.6 percent and 18.3 percent); risk fraction not a pure scale factor; the binary early-exit statement made product-specific (Nadex); break-even stated as 54.05 percent with its assumptions |
| Suggested worked examples | Added a short trade, a rejected wick penetration, delayed safety formation, simultaneous signals and a gap through a stop (9.2 to 9.6) |
