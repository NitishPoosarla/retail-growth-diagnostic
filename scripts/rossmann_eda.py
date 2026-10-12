"""PHASE 3 — STEP 1: Rossmann EDA with a consulting lens.

Answers the questions a client actually asks, each with its denominator:
  - What does daily revenue look like over time?
  - Day-of-week pattern — and is Sunday really closed?
  - Do promo days sell more per store-day?
  - Do store types / assortments differ?
  - How much of the panel is closed days (excluded from sales analysis)?

Outputs -> deliverables/outputs/  (CSV tables + PNG figures)
Run:  ./venv/Scripts/python.exe scripts/rossmann_eda.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAW = Path("data/raw")
OUT = Path("deliverables/outputs")
OUT.mkdir(parents=True, exist_ok=True)
pd.set_option("display.width", 200)

def rule(t=""):
    print("\n" + "=" * 78 + (f"\n{t}" if t else ""))

# ── load ────────────────────────────────────────────────────────────────
train = pd.read_csv(RAW / "train.csv", parse_dates=["Date"], low_memory=False)
store = pd.read_csv(RAW / "store.csv", low_memory=False)
DOW = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}

rule("ROSSMANN EDA")
print(f"train.csv : {len(train):,} store-day rows | "
      f"{train['Store'].nunique():,} stores | "
      f"{train['Date'].min():%Y-%m-%d} -> {train['Date'].max():%Y-%m-%d}")
print(f"store.csv : {len(store):,} stores")
print(f"Stores in train but not store.csv: "
      f"{len(set(train['Store']) - set(store['Store'])):,}")

# ── the closed-day question (asked FIRST — it frames everything) ─────────
rule("Open vs closed (frames every sales number below)")
n = len(train)
n_closed = int((train["Open"] == 0).sum())
print(f"Closed store-days (Open=0): {n_closed:,} of {n:,} = {n_closed/n:.2%}")
print(f"Sales on closed days: sum={train.loc[train['Open']==0,'Sales'].sum():,}, "
      f"max={train.loc[train['Open']==0,'Sales'].max():,}")
print("-> We EXCLUDE Open=0 rows from all sales averages; they are not 'zero revenue,'")
print("   they are 'not open' and would bias every mean downward.")

dow_open = (train.assign(dow=train["DayOfWeek"].map(DOW))
            .groupby("dow")["Open"]
            .agg(n_store_days="size", n_open="sum"))
dow_open["share_closed"] = 1 - dow_open["n_open"] / dow_open["n_store_days"]
dow_open = dow_open.reindex(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
print("\nOpen share by day-of-week (denominator = store-days that weekday):")
print(dow_open.to_string())
sunday_closed = dow_open.loc["Sun", "share_closed"]
print(f"\nVERDICT — Sundays closed: {sunday_closed:.2%} of Sunday store-days "
      f"(n={dow_open.loc['Sun','n_store_days']:,}).")
print("   Meaning for forecasting: a 'Sunday' prediction is not a demand problem,")
print("   it is a schedule problem — forecast open days only, re-insert 0 for closed.")

# ── daily revenue trend ─────────────────────────────────────────────────
rule("Daily revenue trend")
open_df = train[train["Open"] == 1].copy()
daily = (open_df.groupby("Date")
         .agg(total_sales=("Sales", "sum"),
              n_stores_open=("Store", "size"))
         .reset_index())
daily["sales_per_open_store"] = daily["total_sales"] / daily["n_stores_open"]
daily.to_csv(OUT / "eda_daily_revenue.csv", index=False)
print(f"Days covered: {len(daily):,} | total revenue: {daily['total_sales'].sum():,}")
print(f"Mean daily revenue: {daily['total_sales'].mean():,.0f} "
      f"(over {daily['n_stores_open'].mean():,.0f} open stores/day avg)")
print(f"Peak day: {daily.loc[daily['total_sales'].idxmax(),'Date']:%Y-%m-%d} "
      f"(€{daily['total_sales'].max():,})")
print(f"Trough day: {daily.loc[daily['total_sales'].idxmin(),'Date']:%Y-%m-%d} "
      f"(€{daily['total_sales'].min():,})")

fig, ax = plt.subplots(figsize=(11, 4))
ax.plot(daily["Date"], daily["total_sales"] / 1e6, lw=0.7)
ax.set_title("Daily total revenue (open stores)")
ax.set_ylabel("Revenue (€m)")
fig.tight_layout(); fig.savefig(OUT / "eda_daily_revenue.png", dpi=110); plt.close(fig)

# ── day-of-week pattern ─────────────────────────────────────────────────
rule("Day-of-week pattern (open store-days only)")
dow = (open_df.assign(dow=open_df["DayOfWeek"].map(DOW))
       .groupby("dow")["Sales"]
       .agg(n_store_days="size", mean_sales="mean", median_sales="median"))
dow["share_of_store_days"] = dow["n_store_days"] / dow["n_store_days"].sum()
dow = dow.reindex(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
dow.to_csv(OUT / "eda_dow.csv")
print(dow.to_string())
# Sunday's 3,593 open store-days are special openings (e.g. Christmas) — a biased
# sliver, so rank only the normally-trading days and call Sunday out separately.
reg = dow.drop(index="Sun")
peak_d, weak_d = reg["mean_sales"].idxmax(), reg["mean_sales"].idxmin()
print(f"\nReading: denomination = store-days. Among normally-trading days, strongest "
      f"= {peak_d} (€{reg.loc[peak_d,'mean_sales']:,.0f}/store-day), weakest = "
      f"{weak_d} (€{reg.loc[weak_d,'mean_sales']:,.0f}).")
print(f"   Sunday is excluded from ranking: its {dow.loc['Sun','n_store_days']:,} open "
      f"store-days are {dow.loc['Sun','share_of_store_days']:.2%} of open days (holiday "
      f"openings) and are not representative.")

# ── promo vs non-promo ──────────────────────────────────────────────────
rule("Promo vs non-promo (open store-days only)")
promo = (open_df.groupby("Promo")["Sales"]
         .agg(n_store_days="size", mean_sales="mean", median_sales="median"))
promo["share_of_store_days"] = promo["n_store_days"] / promo["n_store_days"].sum()
promo.to_csv(OUT / "eda_promo.csv")
print(promo.to_string())
pm, nm = promo.loc[1, "mean_sales"], promo.loc[0, "mean_sales"]
print(f"\nLift on promo days: {pm:,.0f} vs {nm:,.0f} per store-day "
      f"= {pm/nm - 1:+.1%} (association, NOT yet causal).")
print(f"Denominators: {promo.loc[1,'n_store_days']:,} promo store-days vs "
      f"{promo.loc[0,'n_store_days']:,} non-promo store-days.")

# ── store type & assortment (join store.csv) ────────────────────────────
rule("Store type & assortment (join store.csv, open store-days only)")
j = open_df.merge(store[["Store", "StoreType", "Assortment", "CompetitionDistance"]],
                  on="Store", how="left")
for key in ["StoreType", "Assortment"]:
    t = (j.groupby(key)["Sales"]
         .agg(n_store_days="size", mean_sales="mean", median_sales="median"))
    t["share_of_store_days"] = t["n_store_days"] / t["n_store_days"].sum()
    t.to_csv(OUT / f"eda_{key.lower()}.csv")
    print(f"\n{key}:")
    print(t.to_string())

print(f"\nCompetitionDistance: {j['CompetitionDistance'].isna().sum():,} missing "
      f"of {len(j):,} ({j['CompetitionDistance'].isna().mean():.2%})")

# ── figures: dow + promo ────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
dow["mean_sales"].plot(kind="bar", ax=axes[0], color="#4c72b0")
axes[0].set_title("Mean sales per store-day by weekday"); axes[0].set_ylabel("Sales")
promo["mean_sales"].plot(kind="bar", ax=axes[1], color="#55a868")
axes[1].set_title("Mean sales per store-day: promo vs not")
axes[1].set_xticklabels(["No promo", "Promo"], rotation=0)
fig.tight_layout(); fig.savefig(OUT / "eda_dow_promo.png", dpi=110); plt.close(fig)

rule("EDA OUTPUTS")
for f in sorted(OUT.glob("eda_*")):
    print(f"    {f.name}")
