"""PHASE 3 EXTENSION — Christmas-peak backtest.

Re-runs the rolling-origin backtest over the two full Decembers (Dec 2013,
Dec 2014) and the summer window, to test whether the model holds up in the
highest-revenue period of the year.

Caveat built in: the data starts 2013-01-01, so Dec 2013 has NO year-earlier
reference and the seasonal-naive baseline degrades to a store x weekday median
there. We report that fallback share per window so the comparison is honest.

Run:  ./venv/Scripts/python.exe scripts/seasonal_backtest.py
"""
from pathlib import Path
import pandas as pd
from rossmann_lib import build_panel, run_window, wape

OUT = Path("deliverables/outputs")
OUT.mkdir(parents=True, exist_ok=True)
pd.set_option("display.width", 220)

WINDOWS = [
    ("Dec 2013 peak", "2013-12-01", "2013-12-31"),
    ("Dec 2014 peak", "2014-12-01", "2014-12-31"),
    ("Summer 2015", "2015-06-20", "2015-07-31"),
]

print("=" * 78)
print("CHRISTMAS-PEAK BACKTEST")
print("=" * 78)
df, _ = build_panel()

rows = []
for name, s, e in WINDOWS:
    print(f"\n{name}: {s} -> {e}")
    val, meta = run_window(df, pd.Timestamp(s), pd.Timestamp(e), fold_days=14)
    rows.append({
        "window": name,
        "start": s,
        "end": e,
        "n_open_store_days": len(val),
        "wape_seasonal_naive": wape(val["Sales"], val["pred_seasonal_naive"]),
        "wape_moving_median": wape(val["Sales"], val["pred_movmedian"]),
        "wape_model": wape(val["Sales"], val["pred_model"]),
        "sn_fallback_share": meta["sn_fallback_share"],
    })

res = pd.DataFrame(rows)
res["model_margin_vs_sn_pp"] = (res["wape_seasonal_naive"] - res["wape_model"]) * 100
res["model_margin_vs_sn_pct"] = (res["wape_seasonal_naive"] - res["wape_model"]) / res["wape_seasonal_naive"] * 100

print("\n" + "=" * 78)
print("COMPARISON: peak windows vs summer")
print("=" * 78)
show = res[["window", "n_open_store_days", "wape_seasonal_naive", "wape_moving_median",
            "wape_model", "model_margin_vs_sn_pp", "sn_fallback_share"]].copy()
for c in ["wape_seasonal_naive", "wape_moving_median", "wape_model"]:
    show[c] = (show[c] * 100).round(2).astype(str) + "%"
show["model_margin_vs_sn_pp"] = show["model_margin_vs_sn_pp"].round(2)
show["sn_fallback_share"] = (show["sn_fallback_share"] * 100).round(1).astype(str) + "%"
print(show.to_string(index=False))

res.to_csv(OUT / "seasonal_backtest.csv", index=False)

summer = res.loc[res.window == "Summer 2015", "wape_model"].iloc[0]
peak = res.loc[res.window.str.contains("Dec"), "wape_model"]
print("\nVERDICT")
print(f"  Model WAPE — summer: {summer:.2%} | peak windows: "
      f"{peak.min():.2%}-{peak.max():.2%}")
print(f"  Peak penalty vs summer: +{(peak.max()-summer)*100:.2f} to "
      f"+{(peak.min()-summer)*100:.2f} pp (higher = worse, and expected: December")
print("  demand is far more volatile).")
for _, r in res[res.window.str.contains("Dec")].iterrows():
    tag = "BEATS" if r["wape_model"] < r["wape_seasonal_naive"] else "LOSES TO"
    print(f"  {r['window']}: model {tag} seasonal-naive "
          f"({r['wape_model']:.2%} vs {r['wape_seasonal_naive']:.2%}, "
          f"margin {r['model_margin_vs_sn_pp']:+.2f} pp)")
print(f"\n  NOTE: Dec 2013 seasonal-naive fallback share = "
      f"{res.loc[res.window=='Dec 2013 peak','sn_fallback_share'].iloc[0]:.1%} "
      f"(no 2012 data), so that baseline is really a store x weekday median.")
