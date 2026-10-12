"""Shared Rossmann data prep + rolling-origin backtest.

Single source of truth used by scripts/rossmann_forecast.py (summer window) and
scripts/seasonal_backtest.py (Christmas peak windows).

Design contract (unchanged from Phase 3):
  * Features known in advance only (no leakage; no Customers, no Sales lags).
  * Rolling-origin folds: retrain at each origin on all history before it.
  * Baselines: seasonal-naive (date-364, closed-adjusted) and 4-week moving median.
  * Model: HistGradientBoostingRegressor on log1p(Sales).
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

RAW = Path("data/raw")
RANDOM_STATE = 42

FEATS = ["DayOfWeek", "month", "day", "weekofyear", "Promo", "state_holiday",
         "SchoolHoliday", "days_to_holiday", "store_type", "assortment",
         "log_comp_dist", "comp_dist_missing", "promo2_active",
         "store_mean_log", "store_dow_mean_log"]
CAT_FEATS = ["DayOfWeek", "month", "state_holiday", "store_type", "assortment"]
CAT_IDX = [FEATS.index(c) for c in CAT_FEATS]

STATE_MAP = {"0": 0, "a": 1, "b": 2, "c": 3}
TYPE_MAP = {"a": 0, "b": 1, "c": 2, "d": 3}
ASSORT_MAP = {"a": 0, "b": 1, "c": 2}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def wape(y, yhat):
    y, yhat = np.asarray(y, float), np.asarray(yhat, float)
    return float(np.sum(np.abs(y - yhat)) / np.sum(np.abs(y)))


def build_panel():
    """Load train+store, engineer leak-free features, return (df, closed_df)."""
    train = pd.read_csv(RAW / "train.csv", parse_dates=["Date"], low_memory=False)
    store = pd.read_csv(RAW / "store.csv", low_memory=False)
    hol_dates = np.sort(train.loc[train["StateHoliday"].astype(str) != "0", "Date"].unique())

    df = train.merge(store, on="Store", how="left")
    closed = df.loc[df["Open"] == 0, ["Store", "Date"]].copy()

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
    return df, closed


def _add_baselines(val, op):
    """Attach seasonal-naive + 4-week moving median; return (val, sn_fallback_n)."""
    val_start = val["Date"].min()
    sn = op[["Store", "Date", "Sales"]].copy()
    sn["Date"] = sn["Date"] + pd.Timedelta(days=364)
    val = val.merge(sn.rename(columns={"Sales": "sn_raw"}), on=["Store", "Date"], how="left")
    pre = op[op["Date"] < val_start]
    sd_med = pre.groupby(["Store", "DayOfWeek"])["Sales"].median().rename("sd_med")
    val = val.merge(sd_med, on=["Store", "DayOfWeek"], how="left")
    val["pred_seasonal_naive"] = val["sn_raw"].fillna(val["sd_med"]).fillna(pre["Sales"].median())
    n_fb = int(val["sn_raw"].isna().sum())

    op_sorted = op.sort_values(["Store", "DayOfWeek", "Date"])
    op_sorted = op_sorted.assign(pred_movmedian=op_sorted.groupby(["Store", "DayOfWeek"])["Sales"]
                                 .transform(lambda s: s.shift(1).rolling(4, min_periods=1).median()))
    val = val.merge(op_sorted.set_index(["Store", "Date"])["pred_movmedian"],
                    left_on=["Store", "Date"], right_index=True, how="left")
    return val, n_fb


def run_window(df, w_start, w_end, fold_days=14, verbose=True):
    """Rolling-origin backtest over [w_start, w_end]. Returns (val_df, meta)."""
    op = df[df["Open"] == 1].copy()
    val = op[(op["Date"] >= w_start) & (op["Date"] <= w_end)].copy()
    val, n_fb = _add_baselines(val, op)

    folds, pred_frames = [], []
    cur = w_start
    while cur <= w_end:
        folds.append((cur, min(cur + pd.Timedelta(days=fold_days - 1), w_end)))
        cur = cur + pd.Timedelta(days=fold_days)

    for i, (a, b) in enumerate(folds, 1):
        tr = op[op["Date"] < a].copy()
        te = op[(op["Date"] >= a) & (op["Date"] <= b)].copy()

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

        if verbose:
            print(f"    fold {i}: train {len(tr):,} rows -> predict {a:%Y-%m-%d}..{b:%Y-%m-%d}",
                  end="", flush=True)
        model = HistGradientBoostingRegressor(
            max_iter=300, learning_rate=0.06, max_leaf_nodes=63, min_samples_leaf=40,
            l2_regularization=1.0, categorical_features=CAT_IDX, random_state=RANDOM_STATE)
        model.fit(tr[FEATS], np.log1p(tr["Sales"]))

        out = te[["Store", "Date"]].copy()
        out["pred_model"] = np.expm1(model.predict(te[FEATS]))
        cf = te[FEATS].copy(); cf["Promo"] = 0
        out["pred_model_nopromo"] = np.expm1(model.predict(cf))
        pred_frames.append(out)
        if verbose:
            print(" done")

    val = val.merge(pd.concat(pred_frames, ignore_index=True), on=["Store", "Date"], how="left")
    meta = {"w_start": w_start, "w_end": w_end, "folds": folds,
            "n_rows": len(val), "sn_fallback_n": n_fb,
            "sn_fallback_share": n_fb / len(val) if len(val) else np.nan,
            "last_model": model, "last_te": te}
    return val, meta
