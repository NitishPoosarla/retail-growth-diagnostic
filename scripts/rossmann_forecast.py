"""PHASE 3 — STEPS 2-5: prep, rolling-origin backtest, evaluation, promo bridge.

Summer (default) window. Shared logic lives in scripts/rossmann_lib.py, which is
also used by scripts/seasonal_backtest.py (Christmas peak windows).

Run:  ./venv/Scripts/python.exe scripts/rossmann_forecast.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from rossmann_lib import build_panel, run_window, wape, FEATS, RANDOM_STATE

OUT = Path("deliverables/outputs")
OUT.mkdir(parents=True, exist_ok=True)
pd.set_option("display.width", 220)

def rule(t=""):
    print("\n" + "=" * 78 + (f"\n{t}" if t else ""))

rule("STEP 2  MODELLING DATA")
df, closed = build_panel()
closed.to_csv(OUT / "closed_store_days.csv", index=False)
op = df[df["Open"] == 1]
print(f"Rows: {len(df):,} | open: {len(op):,} | closed: {len(closed):,}")
print(f"Features ({len(FEATS)}): {FEATS}")

rule("STEP 3/4  ROLLING-ORIGIN BACKTEST (summer window)")
val_end = op["Date"].max()
val_start = val_end - pd.Timedelta(days=41)
print(f"Validation window: {val_start:%Y-%m-%d} -> {val_end:%Y-%m-%d} (42 days)")
val, meta = run_window(df, val_start, val_end, fold_days=14)
print(f"\nSeasonal-naive: {meta['sn_fallback_n']:,}/{meta['n_rows']:,} rows "
      f"({meta['sn_fallback_share']:.2%}) had no open same-day-last-year reference "
      f"-> store x weekday median fallback.")

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

# permutation importance on the last fold (HGBR has no built-in importances)
te, model = meta["last_te"], meta["last_model"]
samp = te.sample(min(20000, len(te)), random_state=RANDOM_STATE)
pi = permutation_importance(model, samp[FEATS], np.log1p(samp["Sales"]),
                            n_repeats=3, random_state=RANDOM_STATE, n_jobs=-1)
imp = pd.Series(pi.importances_mean, index=FEATS).sort_values(ascending=False)
imp.rename("perm_importance").to_csv(OUT / "model_feature_importance.csv")
print("\nTop permutation importances (log scale, sampled):")
print(imp.head(8).to_string())

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
