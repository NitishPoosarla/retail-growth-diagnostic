"""PHASE 3 — STEPS 2-5: prep, rolling-origin backtest, evaluation, promo bridge.

Design (fixed BEFORE training):
  * Only features known in advance (no leakage; no Customers, no lags of Sales).
  * Rolling-origin backtest: last 6 weeks split into 3 folds of 14 days; the
    model is retrained at each origin on all history up to that origin.
  * Baseline 1: seasonal-naive (same store, date - 364d), closed-day adjusted.
  * Baseline 2: 4-week moving median by store & day-of-week.
  * Model      : HistGradientBoostingRegressor on log1p(Sales).
  * Metric     : WAPE overall, WAPE by store type, and relative error on the
    top-decile revenue days (the business metric).

STEP 5: promo lift bridge = model prediction with Promo=1 vs Promo=0,
counterfactual on the same store-days. Labelled association-based, not causal.

Run:  ./venv/Scripts/python.exe scripts/rossmann_forecast.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance

RAW = Path("data/raw")
OUT = Path("deliverables/outputs")
OUT.mkdir(parents=True, exist_ok=True)
pd.set_option("display.width", 220)
RANDOM_STATE = 42

def rule(t=""):
    print("\n" + "=" * 78 + (f"\n{t}" if t else ""))
def wape(y, yhat):
    y, yhat = np.asarray(y, float), np.asarray(yhat, float)
    return np.sum(np.abs(y - yhat)) / np.sum(np.abs(y))

# ─────────────────────────────────────────────────────────────────────────
# STEP 2 — build modelling data (leak-free)
# ─────────────────────────────────────────────────────────────────────────
rule("STEP 2  MODELLING DATA")

train = pd.read_csv(RAW / "train.csv", parse_dates=["Date"], low_memory=False)
store = pd.read_csv(RAW / "store.csv", low_memory=False)

# holiday calendar: dates flagged by ANY store (known in advance) -> days-to-holiday
hol_dates = np.sort(train.loc[train["StateHoliday"].astype(str) != "0", "Date"].unique())

df = train.merge(store, on="Store", how="left")

# keep a record of closed days so they can be re-integrated (predicted as 0)
df.loc[df["Open"] == 0, ["Store", "Date"]].to_csv(
    OUT / "closed_store_days.csv", index=False)

STATE_MAP, TYPE_MAP, ASSORT_MAP = {"0": 0, "a": 1, "b": 2, "c": 3}, {"a": 0, "b": 1, "c": 2, "d": 3}, {"a": 0, "b": 1, "c": 2}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

df["month"] = df["Date"].dt.month.astype("int16")
df["day"] = df["Date"].dt.day.astype("int16")
df["weekofyear"] = df["Date"].dt.isocalendar().week.astype("int16")
df["state_holiday"] = df["StateHoliday"].astype(str).map(STATE_MAP).astype("int16")
df["store_type"] = df["StoreType"].map(TYPE_MAP).astype("int16")
df["assortment"] = df["Assortment"].map(ASSORT_MAP).astype("int16")
df["comp_dist_missing"] = df["CompetitionDistance"].isna().astype("int16")
df["log_comp_dist"] = np.log1p(df["CompetitionDistance"].fillna(df["CompetitionDistance"].median()))
month_abbr = df["Date"].dt.month.map(lambda m: MONTHS[m - 1])
df["promo2_active"] = ((df["Promo2"] == 1) & np.array(
    [m in s for m, s in zip(month_abbr, df["PromoInterval"].fillna(""))])).astype("int16")

d = df["Date"].values.astype("datetime64[D]").astype("int64")
hd = hol_dates.astype("datetime64[D]").astype("int64")
idx = np.searchsorted(hd, d)
prev = np.where(idx > 0, hd[np.clip(idx - 1, 0, len(hd) - 1)], np.iinfo("int64").min)
nxt = np.where(idx < len(hd), hd[np.clip(idx, 0, len(hd) - 1)], np.iinfo("int64").max)
df["days_to_holiday"] = np.where(np.abs(d - prev) <= np.abs(nxt - d), d - prev, d - nxt).astype("int32")

# 'store_mean_log' / 'store_dow_mean_log' are added per-fold from training history only
FEATS = ["DayOfWeek", "month", "day", "weekofyear", "Promo", "state_holiday",
         "SchoolHoliday", "days_to_holiday", "store_type", "assortment",
         "log_comp_dist", "comp_dist_missing", "promo2_active",
         "store_mean_log", "store_dow_mean_log"]
CAT_FEATS = ["DayOfWeek", "month", "state_holiday", "store_type", "assortment"]
CAT_IDX = [FEATS.index(c) for c in CAT_FEATS]

op = df[df["Open"] == 1].copy()
print(f"Rows: {len(df):,} | open: {len(op):,} | closed: {(df['Open']==0).sum():,}")
print(f"Holiday dates in calendar: {len(hol_dates)} | features ({len(FEATS)}): {FEATS}")

# ─────────────────────────────────────────────────────────────────────────
# STEP 3 — backtest design + baselines
# ─────────────────────────────────────────────────────────────────────────
rule("STEP 3  BACKTEST DESIGN")
val_end = op["Date"].max()
val_start = val_end - pd.Timedelta(days=41)                 # 42 days = 6 weeks
folds = [(val_start + pd.Timedelta(days=14 * i), val_start + pd.Timedelta(days=14 * i + 13))
         for i in range(3)]
print(f"Validation window: {val_start:%Y-%m-%d} -> {val_end:%Y-%m-%d} (42 days)")
for i, (a, b) in enumerate(folds, 1):
    print(f"  fold {i}: train < {a:%Y-%m-%d}, predict {a:%Y-%m-%d} -> {b:%Y-%m-%d}")

val = op[(op["Date"] >= val_start) & (op["Date"] <= val_end)].copy()

# Baseline 1 — seasonal-naive: same store, date - 364d (day-of-week aligned)
sn = op[["Store", "Date", "Sales"]].copy()
sn["Date"] = sn["Date"] + pd.Timedelta(days=364)
val = val.merge(sn.rename(columns={"Sales": "sn_raw"}), on=["Store", "Date"], how="left")
pre = op[op["Date"] < val_start]
sd_med = pre.groupby(["Store", "DayOfWeek"])["Sales"].median().rename("sd_med")
val = val.merge(sd_med, on=["Store", "DayOfWeek"], how="left")
val["pred_seasonal_naive"] = val["sn_raw"].fillna(val["sd_med"]).fillna(pre["Sales"].median())
n_fb = int(val["sn_raw"].isna().sum())
print(f"\nSeasonal-naive: {n_fb:,}/{len(val):,} rows ({n_fb/len(val):.2%}) had no open "
      f"same-day-last-year reference -> store x weekday median fallback.")

# Baseline 2 — 4-week moving median by store & day-of-week (past only)
op_sorted = op.sort_values(["Store", "DayOfWeek", "Date"])
op_sorted["pred_movmedian"] = (op_sorted.groupby(["Store", "DayOfWeek"])["Sales"]
                               .transform(lambda s: s.shift(1).rolling(4, min_periods=1).median()))
val = val.merge(op_sorted.set_index(["Store", "Date"])["pred_movmedian"],
                left_on=["Store", "Date"], right_index=True, how="left")

# ─────────────────────────────────────────────────────────────────────────
# STEP 4 — rolling-origin model backtest
# ─────────────────────────────────────────────────────────────────────────
rule("STEP 4  MODEL BACKTEST (rolling origin)")
pred_frames = []
for i, (a, b) in enumerate(folds, 1):
    tr = op[op["Date"] < a].copy()
    te = op[(op["Date"] >= a) & (op["Date"] <= b)].copy()

    # leak-free store-level target encodings from training history only
    smean = tr.groupby("Store")["Sales"].apply(lambda s: np.log1p(s).mean()).rename("store_mean_log")
    sdow = (tr.groupby(["Store", "DayOfWeek"])["Sales"].apply(lambda s: np.log1p(s).mean())
            .rename("store_dow_mean_log").reset_index())
    gmean = np.log1p(tr["Sales"]).mean()
    tr = tr.merge(smean, on="Store", how="left").merge(sdow, on=["Store", "DayOfWeek"], how="left")
    tr["store_mean_log"] = tr["store_mean_log"].fillna(gmean)
    tr["store_dow_mean_log"] = tr["store_dow_mean_log"].fillna(tr["store_mean_log"])

    te = te.merge(smean, on="Store", how="left").merge(sdow, on=["Store", "DayOfWeek"], how="left")
    te["store_mean_log"] = te["store_mean_log"].fillna(gmean)
    te["store_dow_mean_log"] = te["store_dow_mean_log"].fillna(te["store_mean_log"])

    print(f"  fold {i}: training on {len(tr):,} rows ...", end="", flush=True)
    model = HistGradientBoostingRegressor(
        max_iter=300, learning_rate=0.06, max_leaf_nodes=63, min_samples_leaf=40,
        l2_regularization=1.0, categorical_features=CAT_IDX, random_state=RANDOM_STATE)
    model.fit(tr[FEATS], np.log1p(tr["Sales"]))

    out = te[["Store", "Date"]].copy()
    out["pred_model"] = np.expm1(model.predict(te[FEATS]))
    cf = te[FEATS].copy(); cf["Promo"] = 0            # counterfactual: no promo
    out["pred_model_nopromo"] = np.expm1(model.predict(cf))
    pred_frames.append(out)
    print(" done")

val = val.merge(pd.concat(pred_frames, ignore_index=True), on=["Store", "Date"], how="left")

# ── metrics ──
rule("BACKTEST RESULTS")
overall = pd.DataFrame({
    "model": ["Seasonal-naive (baseline 1)", "4-week moving median (baseline 2)",
              "HistGradientBoosting (model)"],
    "WAPE": [wape(val["Sales"], val["pred_seasonal_naive"]),
             wape(val["Sales"], val["pred_movmedian"]),
             wape(val["Sales"], val["pred_model"])]})
best_base = overall.loc[:1, "WAPE"].min()
overall["margin_vs_best_baseline_pp"] = (best_base - overall["WAPE"]) * 100
print(f"\nOverall WAPE (validation n={len(val):,} open store-days):")
print(overall.to_string(index=False))

thr = val["Sales"].quantile(0.90)
top = val[val["Sales"] >= thr]
top_tbl = pd.DataFrame({
    "model": ["Seasonal-naive", "4-week moving median", "HGBR model"],
    "mean_abs_pct_err_top_decile": [
        np.mean(np.abs(top["Sales"] - top["pred_seasonal_naive"]) / top["Sales"]),
        np.mean(np.abs(top["Sales"] - top["pred_movmedian"]) / top["Sales"]),
        np.mean(np.abs(top["Sales"] - top["pred_model"]) / top["Sales"])]})
print(f"\nBusiness metric — top-decile revenue days: {len(top):,} store-days "
      f"({len(top)/len(val):.2%}) with actual Sales >= {thr:,.0f}")
print(top_tbl.to_string(index=False))

by_type = (val.groupby("StoreType")
           .apply(lambda g: pd.Series({
               "n_store_days": len(g),
               "wape_model": wape(g["Sales"], g["pred_model"]),
               "wape_sn": wape(g["Sales"], g["pred_seasonal_naive"]),
               "wape_mm": wape(g["Sales"], g["pred_movmedian"])}), include_groups=False)
           .reset_index())
print("\nWAPE by store type (denominator = open store-days of that type):")
print(by_type.to_string(index=False))

overall.to_csv(OUT / "model_backtest_metrics.csv", index=False)
top_tbl.to_csv(OUT / "model_backtest_top_decile.csv", index=False)
by_type.to_csv(OUT / "model_backtest_by_storetype.csv", index=False)
val[["Store", "Date", "StoreType", "Sales", "Promo", "pred_seasonal_naive",
     "pred_movmedian", "pred_model", "pred_model_nopromo"]].to_csv(
    OUT / "model_backtest_predictions.csv", index=False)

# permutation importance on a sample of the last fold (HGBR has no built-in).
# Use `te` from the final fold: it still carries the per-fold encoding columns.
samp = te.sample(min(20000, len(te)), random_state=RANDOM_STATE)
pi = permutation_importance(model, samp[FEATS], np.log1p(samp["Sales"]),
                            n_repeats=3, random_state=RANDOM_STATE, n_jobs=-1)
imp = pd.Series(pi.importances_mean, index=FEATS).sort_values(ascending=False)
imp.rename("perm_importance").to_csv(OUT / "model_feature_importance.csv")
print("\nTop permutation importances (log scale, sampled):")
print(imp.head(8).to_string())

# ─────────────────────────────────────────────────────────────────────────
# STEP 5 — promo lift bridge (association-based, NOT causal)
# ─────────────────────────────────────────────────────────────────────────
rule("STEP 5  PROMO LIFT BRIDGE  (association-based — NOT causal)")
pv = val[val["Promo"] == 1]
incr = pv["pred_model"] - pv["pred_model_nopromo"]
bridge = pd.DataFrame({
    "metric": ["promo_store_days", "sum_pred_with_promo", "sum_pred_without_promo",
               "incremental_revenue_estimate", "avg_increment_per_store_day",
               "pct_of_promo_revenue", "naive_eda_lift_pct"],
    "value": [len(pv), pv["pred_model"].sum(), pv["pred_model_nopromo"].sum(),
              incr.sum(), incr.mean(), incr.sum() / pv["pred_model"].sum() * 100, 38.8]})
print(bridge.to_string(index=False))
bridge.to_csv(OUT / "promo_lift_bridge.csv", index=False)
print(f"\nDenominators: {len(pv):,} promo store-days of {len(val):,} validation open "
      f"store-days ({len(pv)/len(val):.2%}).")
print("CAVEAT: promo timing may be targeted at expected high-demand days; this is an")
print("association from an observational model, not a causal effect.")
