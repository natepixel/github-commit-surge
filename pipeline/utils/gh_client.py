"""Rate-limited GitHub REST + GraphQL client with retry and caching."""
from __future__ import annotations

import time
import threading
from typing import Any, Optional

import requests
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

import pipeline.config as cfg

_session_local = threading.local()
_rate_lock = threading.Lock()
_rate_remaining = 5000
_rate_reset_at = 0.0


def _session() -> requests.Session:
    if not hasattr(_session_local, "s"):
        s = requests.Session()
        s.headers.update({
            "Authorization": f"token {cfg.GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        _session_local.s = s
    return _session_local.s


def _update_rate_state(headers: dict) -> None:
    global _rate_remaining, _rate_reset_at
    with _rate_lock:
        _rate_remaining = int(headers.get("X-RateLimit-Remaining", _rate_remaining))
        _rate_reset_at = float(headers.get("X-RateLimit-Reset", _rate_reset_at))


def _wait_if_needed() -> None:
    with _rate_lock:
        remaining = _rate_remaining
        reset_at = _rate_reset_at
    if remaining < 50:
        wait = max(0, reset_at - time.time()) + 2
        print(f"[GH] Rate limit low ({remaining} remaining) — sleeping {wait:.0f}s")
        time.sleep(wait)


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(requests.HTTPError),
)
def get_user(login: str) -> Optional[dict]:
    """Fetch a user's public profile. Returns None if user not found."""
    _wait_if_needed()
    r = _session().get(f"https://api.github.com/users/{login}")
    _update_rate_state(r.headers)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# GraphQL: contributions per year (used for validation/enrichment only)
# ---------------------------------------------------------------------------

_GQL_CONTRIBUTIONS_FRAGMENT = """
  fragment YearContribs on User {{
    {aliases}
  }}
"""

_GQL_YEAR_ALIAS = """
  y{year}: contributionsCollection(
    from: "{year}-01-01T00:00:00Z"
    to:   "{year}-12-31T23:59:59Z"
  ) {{
    totalCommitContributions
    restrictedContributionsCount
  }}
"""


def _build_contributions_query(login: str, years: list[int]) -> str:
    aliases = "\n".join(_GQL_YEAR_ALIAS.format(year=y) for y in years)
    return f"""
    query {{
      user(login: "{login}") {{
        {aliases}
      }}
    }}
    """


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(requests.HTTPError),
)
def get_contributions_by_year(login: str, years: list[int]) -> dict[int, int]:
    """Return {{year: total_commit_contributions}} for the given user and years.

    Includes both public commits and (anonymized count of) private commits.
    """
    _wait_if_needed()
    query = _build_contributions_query(login, years)
    r = _session().post(
        "https://api.github.com/graphql",
        json={"query": query},
    )
    _update_rate_state(r.headers)
    r.raise_for_status()
    data = r.json()

    if "errors" in data or data.get("data", {}).get("user") is None:
        return {}

    user_data = data["data"]["user"]
    result = {}
    for year in years:
        key = f"y{year}"
        if key in user_data and user_data[key]:
            result[year] = (
                user_data[key]["totalCommitContributions"]
                + user_data[key]["restrictedContributionsCount"]
            )
        else:
            result[year] = 0
    return result
