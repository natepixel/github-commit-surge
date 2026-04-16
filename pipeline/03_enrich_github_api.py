"""
Step 03: Enrich sampled users with GitHub profile data.

For each login in sampled_users.parquet, fetch the REST /users/{login}
endpoint to get account creation date and verify it's a real human account.

Filters applied:
  - type == 'User' (not Organization or Bot)
  - public_repos > 0

Output:
  data/raw/gh_profiles.parquet
    columns: login, created_at, account_year, followers, public_repos, location
  data/raw/confirmed_users.csv
    columns: login  (ready to upload to BigQuery as a filter table)

Uses a disk cache so reruns are free.
Supports resumable batch mode via GH_MAX_NEW_PROFILES.
"""
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))
import pipeline.config as cfg
from pipeline.utils.cache import ParquetCache
from pipeline.utils.gh_client import get_user

CACHE_PATH = cfg.DATA_RAW / "gh_profiles_cache.parquet"
PROFILES_OUT = cfg.DATA_RAW / "gh_profiles.parquet"
CONFIRMED_OUT = cfg.DATA_RAW / "confirmed_users.csv"


def fetch_and_cache(login: str, cache: ParquetCache) -> dict | None:
    if login in cache:
        return cache.get(login)
    profile = get_user(login)
    result = None
    if profile and profile.get("type") == "User":
        result = {
            "login": login,
            "created_at": profile.get("created_at", ""),
            "followers": profile.get("followers", 0),
            "public_repos": profile.get("public_repos", 0),
            "location": profile.get("location") or "",
        }
    # Cache even None results to avoid re-fetching 404s
    cache.set(login, result)
    return result


def main():
    input_path = cfg.DATA_RAW / "sampled_users.parquet"
    if not input_path.exists():
        print(f"ERROR: {input_path} not found. Run 01_sample_users.py first.")
        sys.exit(1)

    df_in = pd.read_parquet(input_path)
    logins = df_in["login"].tolist()
    print(f"Loaded {len(logins):,} candidate logins")

    cache = ParquetCache(CACHE_PATH)
    print(f"Cache has {len(cache):,} existing entries")

    uncached = [l for l in logins if l not in cache]
    max_new = max(0, cfg.GH_MAX_NEW_PROFILES)
    if max_new:
        uncached = uncached[:max_new]
        print(
            f"Batch mode enabled (GH_MAX_NEW_PROFILES={max_new:,}) — "
            f"processing {len(uncached):,} new profiles this run"
        )
    else:
        print(f"Fetching {len(uncached):,} new profiles …")

    flush_every = 500
    with ThreadPoolExecutor(max_workers=cfg.GH_API_THREADS) as pool:
        futures = {pool.submit(fetch_and_cache, login, cache): login for login in uncached}
        for i, future in enumerate(tqdm(as_completed(futures), total=len(futures))):
            future.result()
            if (i + 1) % flush_every == 0:
                cache.flush()

    cache.flush()
    print(f"Cache flushed ({len(cache):,} total entries)")

    # Pull all profiles from cache (includes previously cached entries)
    all_profiles = [cache.get(l) for l in logins if cache.get(l) is not None]
    if not all_profiles:
        df_empty = pd.DataFrame(
            columns=["login", "created_at", "account_year", "followers", "public_repos", "location"]
        )
        df_empty.to_parquet(PROFILES_OUT, index=False)
        pd.DataFrame(columns=["login"]).to_csv(CONFIRMED_OUT, index=False)
        print(f"Saved 0 confirmed profiles → {PROFILES_OUT}")
        print(f"Saved confirmed_users.csv (0 logins) → {CONFIRMED_OUT}")
        return

    df = pd.DataFrame(all_profiles)

    # Parse and filter
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce")
    df["account_year"] = df["created_at"].dt.year
    df = df.dropna(subset=["created_at"])
    df = df[df["public_repos"] > 0]
    df = df.sort_values("login")

    df.to_parquet(PROFILES_OUT, index=False)
    print(f"Saved {len(df):,} confirmed profiles → {PROFILES_OUT}")

    # Write slim CSV for BigQuery upload
    df[["login"]].to_csv(CONFIRMED_OUT, index=False)
    print(f"Saved confirmed_users.csv ({len(df):,} logins) → {CONFIRMED_OUT}")

    # Summary stats
    print("\nAccount creation year distribution:")
    print(df["account_year"].value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()
