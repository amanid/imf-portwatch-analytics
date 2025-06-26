import pandas as pd
import numpy as np

def clean_and_engineer(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Normalize column names
    df.columns = [col.upper().strip() for col in df.columns]

    # Build DATE column from Y/M/D if missing
    if "DATE" not in df.columns and {"YEAR", "MONTH", "DAY"}.issubset(df.columns):
        df["DATE"] = pd.to_datetime(df[["YEAR", "MONTH", "DAY"]], errors="coerce")

    # Rename key columns
    df.rename(columns={
        "PORTNAME": "PORT",
        "COUNTRY": "COUNTRY",
        "PORTID": "PORT_ID"
    }, inplace=True)

    # Drop rows missing core fields
    df = df.dropna(subset=["DATE", "PORT"])

    # Derive synthetic TRAFFIC from PORTCALLS (including 'PORTCALLS' base column)
    portcall_cols = [col for col in df.columns if col.startswith("PORTCALLS")]
    if not portcall_cols:
        print(f"🧪 DEBUG: Columns available = {df.columns.tolist()}")
        raise ValueError("❌ No PORTCALLS columns found to compute traffic.")

    df["TRAFFIC"] = df[portcall_cols].sum(axis=1, skipna=True)

    # Compute total import/export volumes
    import_cols = [col for col in df.columns if col.startswith("IMPORT_")]
    export_cols = [col for col in df.columns if col.startswith("EXPORT_")]

    df["TOTAL_IMPORT"] = df[import_cols].sum(axis=1, skipna=True) if import_cols else 0
    df["TOTAL_EXPORT"] = df[export_cols].sum(axis=1, skipna=True) if export_cols else 0
    df["TOTAL_TRADE_VOLUME"] = df["TOTAL_IMPORT"] + df["TOTAL_EXPORT"]

    # Drop any new NA values
    df = df.dropna(subset=["TRAFFIC"])

    # Time components
    df["YEAR"] = df["DATE"].dt.year
    df["MONTH"] = df["DATE"].dt.month
    df["WEEK"] = df["DATE"].dt.isocalendar().week
    df["DAY_OF_WEEK"] = df["DATE"].dt.day_name()

    # Sort and compute rolling metrics
    df = df.sort_values(["PORT", "DATE"])

    df["ROLLING_AVG_TRAFFIC"] = df.groupby("PORT")["TRAFFIC"].transform(
        lambda x: x.rolling(7, min_periods=1).mean()
    )

    df["TRAFFIC_DELTA"] = df.groupby("PORT")["TRAFFIC"].diff()

    df["TRAFFIC_ZSCORE"] = df.groupby("PORT")["TRAFFIC"].transform(
        lambda x: (x - x.mean()) / x.std(ddof=0)
    ).clip(lower=-5, upper=5)

    return df
