# Memo 1 — Ad Campaign Experiment Readout
**To:** Northwind Retail Co. Growth Leadership  **From:** Analytics Engagement Team  **Date:** 2026-10-11
**Decision this supports:** whether to scale (increase spend on) the ad campaign

---

### 1. Answer first (1 sentence)

> **The ad campaign reliably increases conversion — +0.77 percentage points absolute
> (+43% relative) — and this result is statistically solid and well-powered; however,
> we cannot recommend *scaling spend* yet, because the dataset has no revenue or ad
> cost, so we cannot tell whether those extra conversions are profitable.**

---

### 2. Three supporting findings

**Finding 1 — The ad arm converts materially more, with a tight confidence interval.**
Conversion was **2.55% (14,423 / 564,577 users)** in the ad arm vs **1.79% (420 / 23,524
users)** in the PSA control. Absolute lift **+0.77 pp** (95% CI **+0.60 to +0.94 pp**);
relative lift **+43%** (95% CI on the ratio **1.30× to 1.58×**, i.e. **+30% to +58%**).
*Business read: ≈ **+769 extra conversions per 100,000 users** exposed.*

**Finding 2 — The effect is statistically significant and the test was adequately powered.**
Two-proportion z-test: **z = 7.37, p = 1.7 × 10⁻¹³** (n = 588,101). Detecting an effect
this size at 80% power needs only **≈5,631 users per group**; we had **564,577 (ad)** and
**23,524 (psa)**, giving **≈100% achieved power**. The result is not a fluke of sample size.

**Finding 3 — The lift is concentrated at higher ad exposure (observational).**
Among users seeing **26–200 ads**, relative lift runs **+33% to +101%** (e.g. 51–100 ads:
**11.6% vs 5.8%**, denominators 44,149 and 1,853). But in the largest bucket — **0–25 ads
(412,634 ad / 17,388 psa users)** — the arms are statistically flat (**0.599% vs 0.610%,
−1.7%**). *This is a dose–response signal, not proof of causation (see §4).*

---

### 3. So-what recommendation

- **Do now:** Keep the campaign running. The conversion lift is real, precisely estimated,
  and the experiment had ample power — nothing here argues for pausing.
- **Decide after finance supplies two inputs:** (1) revenue/profit **per conversion**, and
  (2) ad **cost per user exposed**. "Worth it" is `lift × value_per_conversion − cost`.
  Only then can we compute break-even and recommend scaling.
- **Do not do:** Do **not** scale spend on the p-value alone, and do **not** treat the
  segment doses as causal (they are confounded).

---

### 4. Data-quality & limitations (read before trusting the conclusions)

| Issue | Evidence | Effect on credibility | Mitigation |
|-------|----------|----------------------|------------|
| **24 : 1 arm imbalance** | 564,577 ad vs 23,524 psa (96% / 4%) | **Low** — huge n, CI still tight; but control is small, so segment cuts on the control side get thin | Report control-arm n everywhere |
| **Cannot validate randomization** | Only available "covariates" (`total ads`, `most ads day/hour`) are *post-treatment exposure* variables, not pre-treatment traits | **Medium** — we assume arms were randomized; we can't prove it from this file | Treat as randomized by platform design; flag as an assumption |
| **Exposure covariates differ** | `most_ads_day` χ² p≈5×10⁻⁴⁸; `most_ads_hour` χ² p≈1×10⁻²⁸ (but `total_ads` mean identical, 24.8 vs 24.8) | **Low–Medium** — expected by design; with n=588k even trivial differences are "significant" | Judge by effect size, not p-value |
| **No duplicates / no contamination** | 0 duplicate users; 0 users in both arms | **Positive** | Clean split confirmed |
| **No revenue or spend data** | File has a binary `converted` flag only | **High for the scale decision** — blocks all ROI/profit analysis | Escalate data request to finance |
| **Segments are post-treatment** | Buckets split on ads already seen | **High for causal claims** | Label as association only |

---

### 5. Appendix pointer

- Group summary: `deliverables/outputs/ab_group_summary.csv`
- Lift, CIs, p-value, power: `deliverables/outputs/ab_lift_ci.csv`
- Data-quality audit: `deliverables/outputs/ab_audit.csv`
- Segments: `deliverables/outputs/ab_segment_totalads.csv`, `..._hour.csv`, `..._daypart.csv`, `..._dayname.csv`
- Reproducible code: `scripts/ab_experiment_readout.py`
