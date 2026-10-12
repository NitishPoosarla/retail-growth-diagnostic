# Retail Growth Diagnostic — Project Plan

An A/B experiment readout + demand forecasting for a (fictional) retail client.
This mimics a real consulting engagement for MBB-style recruiters, so communication
discipline matters as much as code.

**PHASE 1:** engagement setup + memo skeleton.
**PHASE 2:** A/B experiment readout.
**PHASE 3:** Rossmann EDA + forecast.
**PHASE 4:** promo lift bridge analysis.
**PHASE 5:** final executive memos + README + publish.

---

## STEP 1 — Setup

- Create a Python virtual environment.
- Install: pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, python-dotenv.
- Create `.gitignore` excluding `.env`, `data/`, `venv/`.
- Init git.

## STEP 2 — Inspect data

- List CSVs in `data/raw/`, show columns, row counts, dtypes, and 5 sample rows each.
- Explain each file in one sentence.

## STEP 3 — Engagement setup (Phase 1 deliverable)

**(a)** Write `engagement/engagement_brief.md` in pyramid-principle style:
the client question ("Should we scale the ad campaign, and are our promotions
worth it?"), the analytical approach, the deliverables list, and explicitly stated
assumptions (we have conversion data but NO revenue/spend per user — state what
that limits).

**(b)** Create a memo TEMPLATE: `deliverables/memo_template.md` — the structure
every final memo must follow:
Answer first (1 sentence) → 3 supporting findings with numbers →
So-what recommendation → Appendix pointer.

## STEP 4 — Experiment readout (Phase 2, on the marketing A/B dataset)

**(a)** Data-quality audit BEFORE any test:
- group sizes and imbalance ratio,
- control for duplicate users,
- check randomization integrity (compare the two groups on available covariates —
  total ads, most ads hour/day),
- identify any users exposed to BOTH conditions (they should not exist — report if they do).

**(b)** Analysis:
- conversion rate per group,
- absolute and relative lift,
- z-test for proportions,
- 95% confidence interval on the difference,
- p-value,
- also compute the CI on the RATIO (relative lift),
- show the required sample size per group for detecting the observed effect at 80% power —
  tell me if the test was adequately powered.

**(c)** Segment views:
- conversion lift by total-ads-seen buckets,
- and by most-ads-hour.

**(d)** Write `deliverables/memo_1_experiment.md` using the template — answer first,
evidence with numbers, honest limitations (no revenue data, observational segment caveats).

## STEP 5

- Save key outputs as CSVs in `deliverables/outputs/`.
- Git commit ONCE with a clear message.
- Show a summary.

---

## RULES

- Never present a percentage without its denominator (carries over from the last project).
- Distinguish "statistically significant" from "practically significant" — always report
  effect size in business terms, not just p-values.
- If a data-quality problem exists, report it before testing, and say what it does to the
  conclusion's credibility.
- Ask before any destructive operation. If anything fails, explain simply.
