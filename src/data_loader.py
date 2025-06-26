import pandas as pd
import requests
import time
import logging
from pathlib import Path
from io import StringIO

# -------------------------
# Configuration
# -------------------------
CACHE_PATH = Path("data/raw/port_traffic_csv_cache.csv")
CACHE_TTL_SECONDS = 6 * 3600  # 6 hours
CSV_URL = (
    "https://hub.arcgis.com/api/v3/datasets/"
    "959214444157458aad969389b3ebe1a0_0/downloads/data"
    "?format=csv&spatialRefId=4326&where=1%3D1"
)

# -------------------------
# Logger Setup
# -------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("portwatch_csv_loader")


# -------------------------
# Helper: Check Cache
# -------------------------
def is_cache_fresh(path: Path, ttl: int) -> bool:
    return path.exists() and (time.time() - path.stat().st_mtime) < ttl


# -------------------------
# Fetch and Preserve All CSV Data
# -------------------------
def fetch_from_arcgis_api(
        cache: bool = True,
        return_metadata: bool = False,
        sample_fraction: float = None
) -> pd.DataFrame:
    """
    Fetches port traffic data from ArcGIS Open Data portal with optional caching and sampling.

    Args:
        cache (bool): Use local cache if available and fresh.
        return_metadata (bool): Return metadata along with DataFrame.
        sample_fraction (float): Optional fraction of rows to randomly sample (e.g., 0.15 for 15%).

    Returns:
        pd.DataFrame or (pd.DataFrame, dict): Cleaned DataFrame and optional metadata.
    """
    if cache and is_cache_fresh(CACHE_PATH, CACHE_TTL_SECONDS):
        logger.info("✅ Using cached PortWatch CSV data.")
        df = pd.read_csv(CACHE_PATH, parse_dates=["DATE"])
    else:
        logger.info("📥 Downloading CSV from ArcGIS Open Data portal...")
        try:
            response = requests.get(CSV_URL, timeout=60)
            response.raise_for_status()

            df = pd.read_csv(StringIO(response.text), encoding='utf-8-sig')
            df.columns = df.columns.str.upper()

            # Fix potential BOM header issue
            if 'Ï»¿DATE' in df.columns:
                df.rename(columns={'Ï»¿DATE': 'DATE'}, inplace=True)

            logger.info(f"📌 Loaded {len(df)} rows with columns: {list(df.columns)}")

            required_cols = {"DATE", "PORTNAME"}
            if not required_cols.issubset(df.columns):
                raise KeyError(f"❌ Missing required columns: {required_cols - set(df.columns)}")

            # Standardize and clean
            df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
            df.rename(columns={"PORTNAME": "PORT"}, inplace=True)

            # Derive TRAFFIC if not present
            if "TRAFFIC" not in df.columns:
                import_total = pd.to_numeric(df.get("IMPORT", 0), errors="coerce").fillna(0)
                export_total = pd.to_numeric(df.get("EXPORT", 0), errors="coerce").fillna(0)
                df["TRAFFIC"] = import_total + export_total
                logger.info("➕ Derived TRAFFIC from IMPORT + EXPORT.")

            # Drop rows missing core fields
            df.dropna(subset=["DATE", "PORT"], inplace=True)

            if cache:
                CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(CACHE_PATH, index=False)
                logger.info(f"💾 Cached full CSV data to {CACHE_PATH.resolve()}")

        except Exception as e:
            logger.error(f"❌ Failed to download/process CSV: {e}")
            if CACHE_PATH.exists():
                logger.warning("🔁 Falling back to last known cached version.")
                df = pd.read_csv(CACHE_PATH, parse_dates=["DATE"])
            else:
                raise RuntimeError("❌ No valid data available from URL or cache.")

    # Optional sampling
    if sample_fraction is not None:
        if 0 < sample_fraction < 1:
            df = df.sample(frac=sample_fraction, random_state=42).reset_index(drop=True)
            logger.info(f"🔍 Sampled {len(df)} rows ({sample_fraction:.0%}) from full dataset.")
        else:
            logger.warning("⚠️ Ignoring sample_fraction — must be between 0 and 1.")

    if return_metadata:
        metadata = {
            "record_count": len(df),
            "last_updated": df["DATE"].max()
        }
        return df, metadata

    return df
