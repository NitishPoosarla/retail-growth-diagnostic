"""PHASE 2 — A/B experiment readout for the marketing_AB dataset.

Structure mirrors the brief:
  4a  Data-quality audit  (BEFORE any test)
  4b  Core analysis       (rates, lift, z-test, CIs, power)
  4c  Segment views       (dose-response by total ads; by hour)

Every percentage is printed with its denominator. Statistical vs practical
significance is kept visually separate.

Run:  ./venv/Scripts/python.exe scripts/ab_experiment_readout.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest, proportion_effectsize
from statsmodels.stats.power import NormalIndPower

RAW = Path("data/raw/marketing_AB.csv")
OUT = Path("deliverables/outputs")
OUT.mkdir(parents=True, exist_ok=True)
ALPHA = 0.05
Z_A2 = stats.norm.ppf(1 - ALPHA / 2)      # 1.96
Z_B = stats.norm.ppf(0.80)                # 0.84 (80% power)
pd.set_option("display.width", 200)

def rule(t=""):
    print("\n" + "=" * 78 + (f"\n{t}" if t else ""))

# ─────────────────────────────────────────────────────────────────────────
# LOAD
# ─────────────────────────────────────────────────────────────────────────
df = pd.read_csv(RAW, low_memory=False)
df = df.rename(columns={"test group": "group", "total ads": "total_ads",
                        "most ads day": "most_ads_day", "most ads hour": "most_ads_hour"})
df = df.drop(columns=[c for c in df.columns if c.startswith("Unnamed")])
df["converted"] = df["converted"].astype(bool)

rule("PHASE 2 — A/B EXPERIMENT READOUT")
print(f"Rows loaded: {len(df):,} | columns: {list(df.columns)}")
print(f"Groups present: {sorted(df['group'].unique())}")

# ─────────────────────────────────────────────────────────────────────────
# 4a  DATA-QUALITY AUDIT (before any test)
# ─────────────────────────────────────────────────────────────────────────
rule("4a  DATA-QUALITY AUDIT  (run BEFORE the test)")

n_total = len(df)
sizes = df["group"].value_counts()
n_ad, n_psa = int(sizes.get("ad", 0)), int(sizes.get("psa", 0))
imbalance = max(n_ad, n_psa) / min(n_ad, n_psa)

print(f"[1] Group sizes")
print(f"    ad  (treatment) : {n_ad:,}  ({n_ad/n_total:.2%} of {n_total:,})")
print(f"    psa (control)   : {n_psa:,}  ({n_psa/n_total:.2%} of {n_total:,})")
print(f"    imbalance ratio : {imbalance:.4f} : 1  (1.0 = perfectly balanced)")

# duplicate users / rows
dup_rows = int(df.duplicated().sum())
dup_users = int(df["user id"].duplicated().sum())
dup_user_ids = int(df.loc[df["user id"].duplicated(keep=False), "user id"].nunique())
print(f"\n[2] Duplicates")
print(f"    exact duplicate rows        : {dup_rows:,}")
print(f"    duplicate user ids          : {dup_users:,}")
print(f"    user ids appearing >1 time  : {dup_user_ids:,}")

# cross-arm contamination: any user id in both groups?
arm_counts = df.groupby("user id")["group"].nunique()
contaminated = int((arm_counts > 1).sum())
print(f"\n[3] Cross-arm contamination (users exposed to BOTH conditions)")
print(f"    users in both ad & psa : {contaminated:,}  "
      f"({'PASS — clean split' if contaminated == 0 else 'FAIL — investigate'})")

# randomization integrity on available covariates
print(f"\n[4] Randomization integrity — compare arms on available covariates")
print("    NOTE: 'total_ads' / 'most_ads_day' / 'most_ads_hour' are EXPOSURE")
print("    variables (consequences of treatment), not pre-treatment covariates.")
print("    They can reveal imbalance, but a difference here is expected by design.\n")

ta = {g: df.loc[df["group"] == g, "total_ads"] for g in ["ad", "psa"]}
t_stat, p_tt = stats.ttest_ind(ta["ad"], ta["psa"], equal_var=False)
u_stat, p_mw = stats.mannwhitneyu(ta["ad"], ta["psa"])
print(f"    total_ads  mean  ad={ta['ad'].mean():.1f} (n={len(ta['ad']):,})  "
      f"psa={ta['psa'].mean():.1f} (n={len(ta['psa']):,})")
print(f"               Welch t={t_stat:.2f}, p={p_tt:.3g} | "
      f"Mann-Whitney U p={p_mw:.3g}")

for col in ["most_ads_day", "most_ads_hour"]:
    ct = pd.crosstab(df["group"], df[col])
    chi2, p_chi, dof, _ = stats.chi2_contingency(ct)
    print(f"    {col:14s} chi2={chi2:,.1f}, dof={dof}, p={p_chi:.3g}")

# persisted audit table
audit_rows = [
    ("n_total", n_total, ""),
    ("n_ad", n_ad, "treatment"),
    ("n_psa", n_psa, "control"),
    ("imbalance_ratio_ad_over_psa", round(imbalance, 4), "1.0 = balanced"),
    ("duplicate_rows", dup_rows, ""),
    ("duplicate_user_ids", dup_users, ""),
    ("users_in_both_arms", contaminated, "should be 0"),
    ("total_ads_mean_ad", round(ta["ad"].mean(), 2), ""),
    ("total_ads_mean_psa", round(ta["psa"].mean(), 2), ""),
    ("total_ads_welch_p", float(p_tt), "exposure var — expected to differ"),
]
pd.DataFrame(audit_rows, columns=["metric", "value", "note"]).to_csv(
    OUT / "ab_audit.csv", index=False)

# ─────────────────────────────────────────────────────────────────────────
# 4b  CORE ANALYSIS
# ─────────────────────────────────────────────────────────────────────────
rule("4b  CORE ANALYSIS")

x_ad = int(df.loc[df["group"] == "ad", "converted"].sum())
x_psa = int(df.loc[df["group"] == "psa", "converted"].sum())
p_ad, p_psa = x_ad / n_ad, x_psa / n_psa

print("Conversion rate per arm (denominator in the base):")
print(f"    ad  : {x_ad:,} / {n_ad:,} = {p_ad:.4%}")
print(f"    psa : {x_psa:,} / {n_psa:,} = {p_psa:.4%}")

abs_lift = p_ad - p_psa
rel_lift = p_ad / p_psa - 1
print(f"\nAbsolute lift : {abs_lift:+.4%}  ({(abs_lift*100):+.3f} pp)")
print(f"Relative lift : {rel_lift:+.2%}  (ad vs psa)")

# two-proportion z-test (pooled SE), two-sided
z_stat, p_val = proportions_ztest(count=[x_ad, x_psa], nobs=[n_ad, n_psa],
                                  alternative="two-sided")
print(f"\nTwo-proportion z-test (two-sided):")
print(f"    z = {z_stat:.3f},  p = {p_val:.3g}   "
      f"({'significant' if p_val < ALPHA else 'NOT significant'} at alpha=0.05)")

# 95% CI on the DIFFERENCE (unpooled / Wald)
se_diff = np.sqrt(p_ad * (1 - p_ad) / n_ad + p_psa * (1 - p_psa) / n_psa)
diff_lo, diff_hi = abs_lift - Z_A2 * se_diff, abs_lift + Z_A2 * se_diff
print(f"\n95% CI on the DIFFERENCE (absolute lift):")
print(f"    [{diff_lo:+.4%}, {diff_hi:+.4%}]  i.e. [{diff_lo*100:+.3f}, {diff_hi*100:+.3f}] pp")

# 95% CI on the RATIO (relative lift) — log method
se_log_rr = np.sqrt(1 / x_ad - 1 / n_ad + 1 / x_psa - 1 / n_psa)
rr = p_ad / p_psa
ratio_lo, ratio_hi = np.exp(np.log(rr) - Z_A2 * se_log_rr), np.exp(np.log(rr) + Z_A2 * se_log_rr)
print(f"\n95% CI on the RATIO (relative lift = {rr:.4f}):")
print(f"    [{ratio_lo:.4f}, {ratio_hi:.4f}]  i.e. [{(ratio_lo-1):+.2%}, {(ratio_hi-1):+.2%}] lift")

# power / required sample size at the OBSERVED effect
es = proportion_effectsize(p_ad, p_psa)
pbar = (p_ad + p_psa) / 2
n_req = ((Z_A2 * np.sqrt(2 * pbar * (1 - pbar)) + Z_B * np.sqrt(p_ad * (1 - p_ad) + p_psa * (1 - p_psa)))
         / (p_ad - p_psa)) ** 2
n_req = int(np.ceil(n_req))
# cross-check with statsmodels
es_check = proportion_effectsize(p_ad, p_psa)
n_req_sm = NormalIndPower().solve_power(effect_size=es_check, alpha=ALPHA, power=0.80,
                                        ratio=1, alternative="two-sided")
achieved_power = NormalIndPower().power(effect_size=es_check, nobs1=n_ad,
                                        alpha=ALPHA, ratio=n_psa / n_ad,
                                        alternative="two-sided")

print(f"\nPower analysis (80% power, alpha=0.05, two-sided) at the observed effect:")
print(f"    observed effect size (Cohen's h)  : {es:.4f}")
print(f"    required n PER GROUP              : {n_req:,}  (statsmodels check: {int(np.ceil(n_req_sm)):,})")
print(f"    actual n per group                : ad={n_ad:,}, psa={n_psa:,}")
print(f"    achieved power at actual n        : {achieved_power:.4f}")
powered = min(n_ad, n_psa) >= n_req
print(f"    ADEQUATELY POWERED?               : {'YES' if powered else 'NO'}")

# business translation (per 100k, since no revenue)
per100k = abs_lift * 100_000
print(f"\nBusiness translation (no revenue data — conversions only):")
print(f"    ~{per100k:,.0f} extra conversions per 100,000 users exposed.")

core = pd.DataFrame([
    ("conversion_rate_ad", p_ad, x_ad, n_ad, "x/n"),
    ("conversion_rate_psa", p_psa, x_psa, n_psa, "x/n"),
    ("absolute_lift_pp", abs_lift * 100, "", "", "percentage points"),
    ("relative_lift_pct", rel_lift * 100, "", "", "%"),
    ("z_stat", z_stat, "", "", "pooled two-proportion"),
    ("p_value", p_val, "", "", "two-sided"),
    ("ci95_diff_pp_lo", diff_lo * 100, "", "", "Wald, unpooled"),
    ("ci95_diff_pp_hi", diff_hi * 100, "", "", "Wald, unpooled"),
    ("relative_risk", rr, "", "", "ratio of rates"),
    ("ci95_ratio_lo", ratio_lo, "", "", "log method"),
    ("ci95_ratio_hi", ratio_hi, "", "", "log method"),
    ("n_required_per_group_80pct", n_req, "", "", "at observed effect"),
    ("achieved_power", achieved_power, "", "", "at actual n"),
    ("adequately_powered", int(powered), "", "", "1=yes"),
    ("extra_conversions_per_100k", per100k, "", "", "no revenue data"),
], columns=["metric", "value", "numerator", "denominator", "note"])
core.to_csv(OUT / "ab_lift_ci.csv", index=False)

# ─────────────────────────────────────────────────────────────────────────
# 4c  SEGMENT VIEWS  (observational — NOT causal)
# ─────────────────────────────────────────────────────────────────────────
rule("4c  SEGMENT VIEWS  (observational / post-treatment splits — not causal)")

def seg_table(data, key):
    g = (data.groupby(["group", key])["converted"]
         .agg(n="size", conv="sum").reset_index())
    g["rate"] = g["conv"] / g["n"]
    wide = g.pivot(index=key, columns="group", values=["n", "rate"]).reset_index()
    wide.columns = ["_".join([str(c) for c in col if c != ""]).strip("_")
                    for col in wide.columns.values]
    wide["abs_lift_pp"] = (wide["rate_ad"] - wide["rate_psa"]) * 100
    wide["rel_lift_pct"] = (wide["rate_ad"] / wide["rate_psa"] - 1) * 100
    return wide

# dose-response by total ads seen
print("Total ads seen — distribution (all users):")
print(f"    min={df['total_ads'].min():,}  p50={df['total_ads'].median():,.0f}  "
      f"p90={df['total_ads'].quantile(.9):,.0f}  max={df['total_ads'].max():,}")
bins = [0, 25, 50, 100, 200, 500, np.inf]
labels = ["0-25", "26-50", "51-100", "101-200", "201-500", "500+"]
df["ads_bucket"] = pd.cut(df["total_ads"], bins=bins, labels=labels, right=True)
ads_seg = seg_table(df, "ads_bucket")
print("\nConversion by total-ads bucket (n shown per cell):")
print(ads_seg.to_string(index=False))
ads_seg.to_csv(OUT / "ab_segment_totalads.csv", index=False)

# by most-ads-hour (exact hour) + daypart rollup
hour_seg = seg_table(df, "most_ads_hour")
hour_seg.to_csv(OUT / "ab_segment_hour.csv", index=False)

def daypart(h):
    if h < 6:   return "00-05 night"
    if h < 12:  return "06-11 morning"
    if h < 18:  return "12-17 afternoon"
    return "18-23 evening"
df["daypart"] = df["most_ads_hour"].map(daypart)
day_seg = seg_table(df, "daypart")
day_seg.to_csv(OUT / "ab_segment_daypart.csv", index=False)
print("\nConversion by daypart:")
print(day_seg.to_string(index=False))

# by most-ads-day
dayname_seg = seg_table(df, "most_ads_day")
dayname_seg.to_csv(OUT / "ab_segment_dayname.csv", index=False)

# compact group summary for the memo
summary = pd.DataFrame([
    ("ad", n_ad, x_ad, p_ad),
    ("psa", n_psa, x_psa, p_psa),
], columns=["group", "n_users", "n_converted", "conversion_rate"])
summary.to_csv(OUT / "ab_group_summary.csv", index=False)

rule("OUTPUTS WRITTEN")
for f in sorted(OUT.glob("*.csv")):
    print(f"    {f}  ({f.stat().st_size:,} bytes)")
