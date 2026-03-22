"""
backend/services/github_service.py

Searches GitHub repositories, fetches as many results as the API allows
(up to 10 pages × 100 = 1000 items), then sorts entirely client-side so
every sort option (stars, forks, updated, issues, watchers) operates over
the full result set rather than whatever page-1 happens to return.

GitHub's Search API caps at 1000 results per query. For very broad queries
that would return millions of repos, we apply a MIN_STARS quality floor
inside the query so the 1000 slots are filled with quality projects.
"""

import time
import requests
from backend.security.secret_manager import SecretManager


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
PER_PAGE          = 100          # GitHub maximum per page
MAX_PAGES         = 10           # Hard ceiling — 10 × 100 = 1000 (API limit)
MIN_STARS         = 50           # Quality floor injected into query
TOP_N             = 20           # How many results to return to the UI
REQUEST_TIMEOUT   = 10           # Seconds per HTTP request
INTER_PAGE_DELAY  = 0.25         # Seconds between paginated requests (rate-limit courtesy)


# ─────────────────────────────────────────────────────────────────────────────
# Sort key registry
# ─────────────────────────────────────────────────────────────────────────────

# Maps sort name → (key_fn, reverse)
# All sorts are client-side over the full fetched set.
SORT_KEYS: dict[str, tuple] = {
    "stars":    (lambda r: r["stargazers_count"],  True),
    "forks":    (lambda r: r["forks_count"],       True),
    "updated":  (lambda r: r["updated_at"],        True),  # ISO string — lexicographic = chronological
    "issues":   (lambda r: r["open_issues_count"], True),
    "watchers": (lambda r: r["watchers_count"],    True),
}


# ─────────────────────────────────────────────────────────────────────────────
# Main function
# ─────────────────────────────────────────────────────────────────────────────

def search_repositories(
    query:    str,
    sort:     str  = "stars",
    language: str | None = None,
    top_n:    int  = TOP_N,
) -> list[dict]:
    """
    Fetch as many matching GitHub repositories as the API allows,
    sort the full set by `sort`, and return the top `top_n`.
    """

    if sort not in SORT_KEYS:
        raise ValueError(f"Unknown sort '{sort}'. Valid options: {list(SORT_KEYS)}")

    token   = _get_token()
    headers = _build_headers(token)
    q       = _build_query(query, language)

    # GitHub-native sort for first-pass ordering (helps fill pages with quality)
    gh_sort, gh_order = _github_native_sort(sort)

    all_items: list[dict] = []

    for page in range(1, MAX_PAGES + 1):
        params = {
            "q":        q,
            "sort":     gh_sort,
            "order":    gh_order,
            "per_page": PER_PAGE,
            "page":     page,
        }

        try:
            resp = requests.get(
                GITHUB_SEARCH_URL,
                headers=headers,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            raise RuntimeError(f"GitHub request failed on page {page}: {exc}") from exc

        if resp.status_code == 422:
            # Out of range page
            break

        if resp.status_code == 403:
            _handle_rate_limit(resp)
            continue

        if not resp.ok:
            raise RuntimeError(
                f"GitHub API returned {resp.status_code}: {resp.text[:200]}"
            )

        data  = resp.json()
        items = data.get("items", [])
        total = data.get("total_count", 0)

        all_items.extend(items)

        # Stop early if we have everything
        if len(all_items) >= total or len(items) < PER_PAGE:
            break

        # Stop early if native sort matches desired sort and we have plenty
        if gh_sort == sort and len(all_items) >= top_n * 3:
            break

        if page < MAX_PAGES:
            time.sleep(INTER_PAGE_DELAY)

    # ── Full client-side sort over every fetched item ─────────────────────────
    key_fn, reverse = SORT_KEYS[sort]
    all_items.sort(key=key_fn, reverse=reverse)

    return [_shape(r) for r in all_items[:top_n]]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_token() -> str:
    try:
        return SecretManager.get_github_token()
    except Exception as exc:
        raise RuntimeError(
            "GitHub token unavailable. Set VAULT_TOKEN + VAULT_ADDR, "
            "or export GITHUB_TOKEN as an environment variable."
        ) from exc


def _build_headers(token: str) -> dict:
    return {
        "Authorization": f"token {token}",
        "Accept":        "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _build_query(topic: str, language: str | None) -> str:
    q = f"{topic} stars:>={MIN_STARS}"
    if language:
        q += f" language:{language.strip().lower()}"
    return q


def _github_native_sort(sort: str) -> tuple[str, str]:
    """
    Map our sort names to GitHub API sort params.
    GitHub natively supports: stars, forks, updated.
    issues and watchers fall back to stars so pages are filled with quality.
    """
    mapping = {
        "stars":    ("stars",   "desc"),
        "forks":    ("forks",   "desc"),
        "updated":  ("updated", "desc"),
        "issues":   ("stars",   "desc"),
        "watchers": ("stars",   "desc"),
    }
    return mapping.get(sort, ("stars", "desc"))


def _handle_rate_limit(resp: requests.Response):
    reset_ts = int(resp.headers.get("X-RateLimit-Reset", 0))
    wait     = max(0, reset_ts - int(time.time()))
    if wait > 60:
        raise RuntimeError(
            f"GitHub rate limit exceeded. Resets in {wait}s. Try again later."
        )
    time.sleep(wait + 1)


def _shape(repo: dict) -> dict:
    return {
        "name":        repo.get("full_name", repo.get("name", "")),
        "description": repo.get("description") or "No description provided.",
        "stars":       repo.get("stargazers_count", 0),
        "forks":       repo.get("forks_count", 0),
        "issues":      repo.get("open_issues_count", 0),
        "watchers":    repo.get("watchers_count", 0),
        "updated":     repo.get("updated_at", ""),
        "url":         repo.get("html_url", ""),
        "language":    repo.get("language") or "Unknown",
    }