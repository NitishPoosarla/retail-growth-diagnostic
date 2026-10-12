# Memo 2 — Demand Forecast & Promo Lift Bridge (Rossmann panel)
**To:** Northwind Retail Co. Planning  **From:** Analytics Engagement Team  **Date:** 2026-10-11
**Decision this supports:** whether to adopt a demand-forecast model, and how much revenue promotions really add

---

### 1. Answer first (1 sentence)

> **A single gradient-boosted model trained on the whole store panel beats the
> seasonal-naive baseline in summer (WAPE 10.39% vs 12.05%) and, after extension to
> the two full Decembers, beats it at Christmas peak too (14.52% vs 17.12% in Dec
> 2014; 23.89% vs 28.50% in Dec 2013) — so it is now peak-validated — but peak error
> is roughly 1.4× the summer error, and the promo "lift" it implies is only ~28% of
> promo-day revenue and is an **association from an observational model, not a causal
> estimate**, so it must not be used as an ROI number.**

---

### 2. Supporting findings

**Finding 1 — The model beats both baselines, by a modest but real margin.**
Rolling-origin backtest over the last 6 weeks (**40,282 open store-days**, 2015-06-20 → 2015-07-31):

| Model | WAPE | vs best baseline |
|---|---:|---:|
| Seasonal-naive (baseline 1) | **12.05%** | — |
| 4-week moving median (baseline 2) | 18.12% | −6.07 pp (worse) |
| HistGradientBoosting (model) | **10.39%** | **+1.65 pp better** |

The model improves on the best baseline by **+1.65pp WAPE**, a **13.7% relative**
error reduction. Honest caveat: the margin is a real but modest gain, and the
moving-median baseline is clearly the weakest of the three.

**Finding 2 — The model wins where the money is, but loses on one small segment.**
On the **top-decile revenue days (4,029 store-days = 10.00% of the window, actual
Sales ≥ €10,753)**, mean absolute % error is **11.34% (model)** vs **12.75%
(seasonal-naive)** vs 18.13% (moving median) — the model is best exactly where
forecast error is most expensive. By store type, though, the model beats
seasonal-naive on types a, c and d but **loses on type b (11.39% vs 10.00%, n = 714
store-days)** — type b is 1.8% of the panel, so this is a small-sample result we
would not build a plan on.

**Finding 3 — Promo "lift" shrinks once you control for when promos run.**
Using the model counterfactually (same store-days, `Promo` forced to 0), the
estimated incremental revenue across the **16,701 promo store-days (41.46% of the
window)** is **€38.8m**, i.e. **28.2% of promo-day revenue**. The naive EDA
comparison suggested **+38.8%** (€8,228 vs €5,929 per store-day, over 376,896 promo
vs 467,496 non-promo open store-days). **The model says the naive number overstates
promo's contribution by ~10.6pp** — promotions cluster on high-demand days, so a raw
comparison double-counts demand that would have happened anyway.

**Finding 4 — Peak validation (extension): the model holds at Christmas, but error
roughly doubles.** Extended the backtest to the two full Decembers. Model WAPE rises
from **10.39% (summer)** to **14.52% (Dec 2014)** and **23.89% (Dec 2013)** — a penalty
of **+4.13 to +13.49 pp**, i.e. peak error is **~1.4×** summer error (expected: December
demand is far more volatile). Crucially, the model **still beats seasonal-naive in both
peaks**: Dec 2014 **14.52% vs 17.12% (+2.60 pp)**; Dec 2013 **23.89% vs 28.50% (+4.62 pp)**.
Denominators: **23,492** (Dec 2014) and **26,901** (Dec 2013) open store-days. Caveat on
Dec 2013: data begins 2013-01-01, so its seasonal-naive reference is missing for
**99.9% of rows** and degrades to a store × weekday median — that comparison is against a
*weakened* baseline, not a fair seasonal-naive.

---

### 3. So-what recommendation

- **Do now:** Adopt the gradient-boosted panel model for open-day demand forecasting.
  It is the *smallest* model that beats the naive baseline, trains on the whole
  1,115-store panel, runs the entire 3-fold backtest (train + evaluate) in about
  70 seconds, and wins on the top-decile revenue days.
- **Decide after a causal test:** Treat the **28% promo lift as an upper-bound
  association**, not ROI. Before changing promo policy, run a hold-out/geo test.
- **Do not do:** Do **not** size the promo budget on the naive **38.8%** figure, and
  do **not** deploy the model on store **type b** without more data for that segment.

---

### 4. Data-quality & limitations (read before trusting the conclusions)

| Issue | Evidence | Effect on credibility | Mitigation |
|-------|----------|----------------------|------------|
| **Sundays closed** | 97.52% of Sunday store-days closed (n = 144,730) | **Low** — expected; it's a schedule, not demand | Forecast open days; re-insert 0 for closed |
| **Closed days excluded** | 172,817 of 1,017,209 store-days (16.99%) are `Open=0`, all with Sales=0 | **Low** — including them would bias means down | Kept in `closed_store_days.csv` for re-integration as 0 |
| **Promo is not randomized** | Promos cluster on Mon/Fri/holidays | **High for causal claims** | Labelled association-only; causal test required |
| **Peak error is higher** | Model WAPE **14.52% (Dec 2014) / 23.89% (Dec 2013)** vs **10.39% summer** — now peak-tested | **Medium** — model still beats naive at peak, but absolute accuracy is ~1.4× worse | Plan peak safety stock; do not quote summer WAPE as year-round |
| **Store-level features are target encodings** | `store_mean_log`, `store_dow_mean_log` from training history only | **Low** | Recomputed at each fold origin — no leakage |
| **Type b small sample** | 714 store-days (1.8%) | **Medium for that segment** | Do not deploy on type b yet |
| **No leakage by construction** | Only pre-known features used; no `Customers`, no Sales lags | **Positive** | Design fixed before training |

---

### 5. Appendix pointer

- EDA tables: `deliverables/outputs/eda_daily_revenue.csv`, `eda_dow.csv`, `eda_promo.csv`, `eda_storetype.csv`, `eda_assortment.csv` (+ `eda_*.png` figures)
- Backtest: `deliverables/outputs/model_backtest_metrics.csv`, `..._by_storetype.csv`, `..._top_decile.csv`, `..._predictions.csv`
- Peak extension: `deliverables/outputs/seasonal_backtest.csv`
- Promo bridge: `deliverables/outputs/promo_lift_bridge.csv`
- Feature importance: `deliverables/outputs/model_feature_importance.csv`
- Code: `scripts/rossmann_eda.py`, `scripts/rossmann_forecast.py`
