"""STEP 2 — Data inspection.

Prints, for every CSV in data/raw/: file size, row count, column names, dtypes
and 5 sample rows. Beginner notes are inline.
"""
from pathlib import Path
import pandas as pd

RAW = Path("data/raw")
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 50)

files = sorted(RAW.glob("*.csv"))
if not files:
    raise SystemExit(f"No CSVs found in {RAW.resolve()}")

print(f"Found {len(files)} CSV file(s) in {RAW.resolve()}:\n")
for f in files:
    mb = f.stat().st_size / 1_048_576
    # low_memory=False avoids mixed-dtype guessing warnings on big files
    df = pd.read_csv(f, low_memory=False)
    print("=" * 78)
    print(f"FILE      : {f.name}")
    print(f"SIZE      : {mb:,.1f} MB")
    print(f"SHAPE     : {df.shape[0]:,} rows x {df.shape[1]} columns")
    print(f"DUPLICATE ROWS: {df.duplicated().sum():,}")
    print("-" * 78)
    print("COLUMNS + DTYPES:")
    for col in df.columns:
        print(f"  - {col!r:28s} {str(df[col].dtype):10s} "
              f"| nulls={df[col].isna().sum():,} "
              f"| n_unique={df[col].nunique():,}")
    print("-" * 78)
    print("FIRST 5 ROWS:")
    print(df.head(5).to_string())
    print()
