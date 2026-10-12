# Final Memo — Retail Growth Diagnostic
*Engagement sandbox: public data (Rossmann Kaggle panel; public marketing A/B
dataset) with a fictional client used only to frame the decision.*
**To:** Northwind Retail Co. Executive Committee  **From:** Nitish Poosarla — Analytics  **Date:** 2026-10-11
**Decision this supports:** (a) whether to scale the ad campaign, and (b) whether promotions are worth it

---

### 1. Answer first (1 sentence)

> **Scale the ad campaign — the conversion lift is real, precisely measured, and
> clears break-even on plausible unit economics (+€18,077 per 100,000 users at €30
> per conversion and €0.05 ad cost per user) — but treat promotions as a
> *directionally positive, unproven* spend: our best estimate is that they add ~28%
> to promo-day revenue, and that number is an association, not a causal result.**

---

### 2. The two client questions

**(a) Should we scale the ad campaign? — Yes, conditional on two assumed numbers.**
The A/B test (**n = 588,101 users**) shows conversion of **2.55% (14,423 / 564,577)**
in the ad arm vs **1.79% (420 / 23,524)** in the PSA control: **+0.77pp absolute,
+43% relative** (95% CI on the ratio **1.30×–1.58×**), **z = 7.37, p = 1.7×10⁻¹³**,
and **~100% powered**. Converting that lift using **client assumptions** (€30 value
per conversion, €0.05 ad cost per user) gives **595–943 incremental conversions per
100,000 users** and **net +€12,853 to +€23,302 per cohort** — positive even at the
*bottom* of the confidence interval. Break-even sits at **€6.50 per conversion**, so
the decision is driven by economics, not statistical noise. *These two inputs are
assumptions, not measurements — they are the crux of the recommendation.*

**(b) Are promotions worth it? — Probably, but we cannot yet prove it.**
Using the demand model counterfactually (same store-days, promo forced off),
promotions add an estimated **€38.8m ≈ 28.2% of promo-day revenue** across **16,701
promo store-days** (41.46% of the validated window). The naive comparison suggested
**+38.8%** (376,896 promo vs 467,496 non-promo open store-days), so controlling for
*when* promos run cuts the apparent benefit by **~10.6pp**. Because promo timing is
targeted rather than randomised, **28% is an upper-bound association, not a causal
ROI.** Treat it as a reason to keep promoting — not as a number to budget against.

---

### 3. Forecast reliability statement

The demand model is trustworthy enough to plan against: it beats the seasonal-naive
baseline in **every** window tested and is most accurate where revenue is concentrated.

| Window (open store-days) | Seasonal-naive WAPE | Model WAPE | Model margin |
|---|---:|---:|---:|
| Summer 2015 (40,282) | 12.05% | **10.39%** | +1.65 pp |
| Dec 2014 peak (23,492) | 17.12% | **14.52%** | +2.60 pp |
| Dec 2013 peak (26,901) | 28.50%* | **23.89%** | +4.62 pp |

**But peak error is ~1.4× the summer error** — do not quote the 10.39% figure as
year-round accuracy; December forecasts carry materially more uncertainty.
\* Dec 2013's seasonal-naive reference is missing for 99.9% of rows (data starts
2013-01-01), so that baseline is really a store × weekday median.

---

### 4. What data would make this answer definitive

1. **Revenue and ad spend per user** — turns the ad recommendation from
   "conditional on assumptions" into a measured ROI, and removes the largest single
   caveat in this engagement. *Highest priority.*
2. **A randomised promotion test** (geo or time holdout) — replaces the 28%
   association with a causal promo lift.
3. **Christmas coverage in the test data** — our A/B uplift is from one campaign
   window; there is no evidence yet on whether the lift holds at peak volumes.

---

### 5. Appendix pointer

- A/B readout: `deliverables/memo_1_experiment.md` · lift/CI: `deliverables/outputs/ab_lift_ci.csv`
- Break-even: `deliverables/memo_1a_breakeven.md` · scenarios: `deliverables/outputs/breakeven_scenarios.csv`
- Forecast: `deliverables/memo_2_forecast.md` · peak test: `deliverables/outputs/seasonal_backtest.csv`
- Engagement brief: `engagement/engagement_brief.md`
