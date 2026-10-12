# Engagement Brief — Retail Growth Diagnostic

**Client:** Northwind Retail Co. (fictional)
**Engagement lead:** [Analyst]
**Date:** 2026-10-11
**Version:** 1.0

---

## 0. How to read this brief (pyramid principle)

We lead with the **governing thought** (our recommended answer), then the MECE
arguments that support it. A busy executive should be able to read only the bolded
lines and still get the story. Detail lives below and in the appendix.

---

## 1. The client question

**Should we scale the ad campaign, and are our promotions worth it?**

This breaks into two decision-relevant sub-questions:

1. **Ads:** Does showing more ads *cause* more conversions, and by how much? Is the
   measured effect big enough to justify scaling spend?
2. **Promotions:** Do promo days lift store sales beyond normal days, and can we
   attribute the lift to the promo itself (vs. seasonality, day-of-week, store mix)?

---

## 2. Our answer (the governing thought)

> **We can answer the *direction and statistical reliability* of the ad effect with
> high confidence, but we cannot yet answer the *profitability* question — because the
> data contains conversions but no revenue or ad spend per user.**

Consequence: this engagement will deliver a **decision-grade readout of lift and
statistical significance**, explicitly flagged as **incomplete for ROI decisions**
until finance supplies revenue/spend. For promotions, we deliver a **lift bridge**
that decomposes promo-day growth into baseline, day-of-week, seasonality and promo
effects.

---

## 3. Analytical approach (MECE)

**A. Experiment readout (ad campaign)** — the core of Phase 2
- Data-quality audit *before* any test (group balance, duplicates, randomization
  integrity, cross-arm contamination).
- Conversion rate per arm; absolute & relative lift.
- Two-proportion z-test; 95% CI on the *difference* and on the *ratio*.
- Power analysis: sample size needed to detect the observed effect at 80% power.
- Segment views (dose–response by ads seen; by hour) — **observational, not causal**.

**B. Demand forecasting (Rossmann)** — Phase 3
- EDA of store/day sales; seasonality, promo and holiday effects.
- Baseline forecast (e.g. time-aware model on store-level sales).

**C. Promo lift bridge** — Phase 4
- Decompose promo-day sales into baseline → seasonality → promo lift.
- Quantify "is the promo worth it" in the same business terms as the ad work.

---

## 4. Deliverables

| # | Deliverable | File | Phase |
|---|-------------|------|-------|
| 1 | Engagement brief (this doc) | `engagement/engagement_brief.md` | 1 |
| 2 | Reusable memo template | `deliverables/memo_template.md` | 1 |
| 3 | Experiment readout memo | `deliverables/memo_1_experiment.md` | 2 |
| 4 | Key output tables | `deliverables/outputs/*.csv` | 2+ |
| 5 | Forecast memo | `deliverables/memo_2_forecast.md` | 3 |
| 6 | Promo lift bridge memo | `deliverables/memo_3_promo.md` | 4 |
| 7 | Final executive memo + README | `deliverables/memo_final.md`, `README.md` | 5 |

---

## 5. Stated assumptions & data limitations (read before trusting any number)

1. **No revenue or spend per user.** We observe *conversions* (a yes/no flag) but not
   order value, margin, or ad cost. Therefore we **cannot compute ROI, profit, or
   break-even**. Any "should we scale" answer is limited to **conversion lift**, not
   **value lift**.
2. **Selection, not just treatment.** Users were assigned by the platform; we must
   verify the arms are comparable *before* trusting the lift (Phase 2 audit).
3. **Segment analyses are observational.** Bucketing users by "total ads seen" splits
   on a *post-treatment* variable — the buckets are not randomized, so segment
   differences are associations, not causal effects.
4. **Promotions are not randomly assigned** across stores/days; the Phase 4 bridge
   must control for day-of-week and seasonality to avoid over-attributing lift.
5. **Rossmann data is a public proxy**, not Northwind's own stores; treated as a
   methodological stand-in for the forecasting method.

---

## 6. Success criteria

- Every percentage reported with its **denominator** and **n**.
- **Statistical** significance and **practical/business** significance reported
  separately.
- Any data-quality issue surfaced **before** testing, with an explicit statement of
  how it affects the conclusion's credibility.
- Each memo readable in under 2 minutes: answer first, evidence second, so-what last.

---

## Appendix

- Data inventory & dtypes: see `scripts/inspect_data.py` output.
- Full definition of metrics used: see `deliverables/memo_template.md` and per-memo appendices.
