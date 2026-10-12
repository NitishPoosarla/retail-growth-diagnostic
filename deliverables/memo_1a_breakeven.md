# Memo 1a — Ad Campaign Break-Even & Scale Decision
**To:** Northwind Retail Co. Growth Leadership  **From:** Analytics Engagement Team  **Date:** 2026-10-11
**Decision this supports:** should we scale (increase spend on) the ad campaign?

---

### 1. Answer first (1 sentence)

> **On the client-supplied assumptions (€30 value per conversion, €0.05 ad cost per
> user), scaling pays off — net ≈ €18,077 per 100,000 users — and it stays positive
> even at the *bottom* of the 95% confidence interval, so the recommendation is
> SCALE; but the whole conclusion lives or dies on those two assumed numbers, which
> the data does not contain.**

---

### 2. Three supporting findings

**Finding 1 — The lift, converted into units of business value.**
Phase 2 measured **+0.769pp** lift (95% CI **+0.595 to +0.943 pp**, n = 588,101 users).
Per **100,000 users** that is **595 / 769 / 943** incremental conversions at the
low / expected / high end — every figure carrying its cohort denominator.

**Finding 2 — At the assumed inputs, the campaign clears break-even with room.**
Value per cohort (100,000 users): **€17,853 / €23,077 / €28,302** against a cost of
**€5,000** (= €0.05 × 100,000). Net: **+€12,853 / +€18,077 / +€23,302**, i.e.
**ROI 3.6× / 4.6× / 5.7×**. The *worst case* (CI low) still nets +€12,853.

**Finding 3 — The break-even is low, so the decision is robust to most inputs.**
Break-even **value per conversion = €6.50** (at €0.05/user cost); break-even **cost
per user = €0.2308** (at €30/conversion). The campaign only turns negative in the
corners of the sensitivity grid — e.g. value = €10 *and* cost = €0.10, or value = €20
*and* cost = €0.20.

---

### 3. So-what recommendation

- **Do now:** Scale if walk-forward trials confirm the assumed unit economics
  (value/conversion ≥ ~€7 and cost/user ≤ ~€0.23). The measured lift is precise
  enough that the decision is driven by *economics*, not by statistical noise.
- **Decide after finance supplies:** the **actual** value per conversion and ad cost
  per user. These are **assumptions, not measurements** — replacing them is the
  single highest-value data request in this engagement.
- **Do not do:** Do **not** treat this as a proven ROI. It is a break-even *frame*:
  it converts a statistically-significant lift into a money decision **conditional**
  on inputs the client has not yet provided.

---

### 4. Data-quality & limitations

| Issue | Evidence | Effect on credibility | Mitigation |
|-------|----------|----------------------|------------|
| **Value & cost are assumptions** | €30 and €0.05 are placeholders, not from any dataset | **High** — the verdict is only as good as these two numbers | Re-run `breakeven.py` with finance's real inputs |
| **Conversions ≠ revenue** | Data has a binary `converted` flag only | **High** — no margin, no basket size | Escalate data request |
| **CI reflects sampling only** | CI from the A/B test | **Medium** — does not cover cost/value uncertainty | Sensitivity grid spans both |
| **Lift is from one campaign window** | Phase 2 dataset | **Medium** — may not hold at 10× spend (diminishing returns) | Pilot at scale before full rollout |

---

### 5. Appendix pointer

- Scenario table: `deliverables/outputs/breakeven_scenarios.csv`
- Sensitivity grid: `deliverables/outputs/breakeven_sensitivity.csv`
- Measured lift & CI: `deliverables/outputs/ab_lift_ci.csv`
- Code: `scripts/breakeven.py` (`--value-per-conversion`, `--ad-cost-per-user`)
