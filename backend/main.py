from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path

from unidiff import PatchSet
import os
import re
import time

from backend.llm.analyzer import analyze_diff
from backend.llm.tech_assistant import query_tech_assistant
from backend.services.github_service import search_repositories
from backend.utils.risk import compute_risk
from backend.utils.change_intelligence import analyse_change_intelligence
from backend.utils.churn_heatmap import build_heatmap
from backend.utils.diff_sanitiser import sanitise_for_llm
from backend.security.secret_manager import SecretManager


# ─────────────────────────────────────────────────────────────────────────────
# Startup checks
# ─────────────────────────────────────────────────────────────────────────────

def check_groq() -> bool:
    """Check if GROQ_API_KEY is set and reachable."""
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        return False
    try:
        from groq import Groq
        client = Groq(api_key=key)
        # Lightweight check — list models
        client.models.list()
        return True
    except Exception:
        # Key exists but couldn't verify — treat as available
        # (avoids startup delay on Railway)
        return bool(key)


def check_github() -> bool:
    try:
        SecretManager.get_github_token()
        return True
    except Exception:
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*50)
    print("  DiffInsight — Startup Check")
    print("="*50)
    groq_ok   = check_groq()
    github_ok = check_github()
    print(f"  Groq LLM      : {'✓ ready' if groq_ok else '✗ GROQ_API_KEY missing'}")
    print(f"  GitHub token  : {'✓ found' if github_ok else '✗ not configured'}")
    print("="*50 + "\n")
    app.state.groq_ok   = groq_ok
    app.state.github_ok = github_ok
    yield


# ─────────────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

_rate_store: dict[str, list[float]] = {}
RATE_LIMIT  = 10
RATE_WINDOW = 60
MAX_DIFF_MB = 5


def _check_rate_limit(ip: str):
    now    = time.time()
    window = _rate_store.get(ip, [])
    window = [t for t in window if now - t < RATE_WINDOW]
    if len(window) >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {RATE_LIMIT} requests per {RATE_WINDOW}s."
        )
    window.append(now)
    _rate_store[ip] = window


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ─────────────────────────────────────────────────────────────────────────────
# Diff normaliser + parser
# ─────────────────────────────────────────────────────────────────────────────

def _normalise_diff(diff_text: str) -> str:
    normalised_lines = []
    for line in diff_text.splitlines():
        if line.startswith('Binary files') and 'differ' in line:
            continue
        if line.startswith('--- ') and '\t' in line:
            path = re.sub(r'^[^/]+/', '', line[4:].split('\t')[0].strip())
            normalised_lines.append(f'--- a/{path}')
            continue
        if line.startswith('+++ ') and '\t' in line:
            path = re.sub(r'^[^/]+/', '', line[4:].split('\t')[0].strip())
            normalised_lines.append(f'+++ b/{path}')
            continue
        if line.startswith('diff -') and not line.startswith('diff --git'):
            parts = line.split()
            if len(parts) >= 3:
                path = re.sub(r'^[^/]+/', '', parts[-1])
                normalised_lines.append(f'diff --git a/{path} b/{path}')
                continue
        normalised_lines.append(line)
    return '\n'.join(normalised_lines)


def analyze_diff_content(diff_text: str) -> dict:
    if not diff_text or not diff_text.strip():
        raise ValueError("Diff text is empty.")
    normalised = _normalise_diff(diff_text)
    try:
        patch = PatchSet(normalised)
    except Exception as e:
        raise ValueError(f"Could not parse diff: {e}")

    files_changed     = len(patch)
    functions_changed = 0
    added_lines       = []
    removed_lines     = []
    FUNC_PATTERN      = re.compile(r'(def |function |class |async def )')

    for patched_file in patch:
        for hunk in patched_file:
            for line in hunk:
                text = line.value.rstrip('\n')
                if line.is_added:
                    added_lines.append(text)
                    if FUNC_PATTERN.search(text):
                        functions_changed += 1
                elif line.is_removed:
                    removed_lines.append(text)

    return {
        "files_changed":     files_changed,
        "lines_added":       len(added_lines),
        "lines_removed":     len(removed_lines),
        "functions_changed": functions_changed,
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /analyze
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/analyze")
async def analyze_diff_endpoint(
    request: Request,
    file: UploadFile = File(None),
    mode: str = Form("reviewer")
):
    _check_rate_limit(request.client.host)

    diff_text  = ""
    final_mode = "reviewer"

    if file and file.filename:
        suffix = Path(file.filename).suffix.lower()
        if suffix not in {".diff", ".patch", ".txt"}:
            raise HTTPException(status_code=400, detail=f"Invalid file type '{suffix}'.")
        raw = await file.read()
        if len(raw) > MAX_DIFF_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"File too large. Max {MAX_DIFF_MB}MB.")
        diff_text  = raw.decode("utf-8", errors="replace")
        final_mode = mode if mode in {"reviewer", "junior"} else "reviewer"
    else:
        try:
            body       = await request.json()
            diff_text  = body.get("diff", "")
            final_mode = body.get("mode", "reviewer")
            if final_mode not in {"reviewer", "junior"}:
                final_mode = "reviewer"
        except Exception:
            pass

    if not diff_text or not diff_text.strip():
        raise HTTPException(status_code=400, detail="No diff content provided.")

    # Metrics from raw diff (no LLM)
    try:
        metrics = analyze_diff_content(diff_text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    risk = compute_risk(diff_text)

    # Sanitise before LLM sees anything
    sanitised_diff, sanitise_report = sanitise_for_llm(diff_text)

    if sanitise_report["blocked_files"] or sanitise_report["redacted_lines"] > 0:
        print(f"[SANITISER] Blocked: {sanitise_report['blocked_files']}")
        print(f"[SANITISER] Redacted lines: {sanitise_report['redacted_lines']}")

    # LLM — Groq
    if not app.state.groq_ok:
        report = (
            "⚠️  Groq API key not configured.\n\n"
            "Add GROQ_API_KEY to your Railway environment variables.\n"
            "Get a free key at: console.groq.com"
        )
    else:
        report = analyze_diff(sanitised_diff, risk=risk, mode=final_mode)

    intelligence = analyse_change_intelligence(sanitised_diff)

    sanitise_warning = None
    if sanitise_report["blocked_files"]:
        names = ", ".join(f.split("/")[-1] for f in sanitise_report["blocked_files"])
        sanitise_warning = (
            f"⚠️  {len(sanitise_report['blocked_files'])} sensitive file(s) hidden "
            f"from LLM: {names}"
        )
    elif sanitise_report["redacted_lines"] > 0:
        sanitise_warning = (
            f"⚠️  {sanitise_report['redacted_lines']} line(s) with credential-shaped "
            f"values were redacted before analysis."
        )

    return {
        "report":           report,
        "mode":             final_mode,
        "risk_level":       risk,
        "sanitise_warning": sanitise_warning,
        "stats": {
            "files":     metrics["files_changed"],
            "added":     metrics["lines_added"],
            "removed":   metrics["lines_removed"],
            "functions": metrics["functions_changed"],
        },
        "intelligence": intelligence,
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /ask
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/ask")
async def ask_tech_assistant(request: Request, data: dict):
    _check_rate_limit(request.client.host)
    question = data.get("question", "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")
    if not app.state.groq_ok:
        raise HTTPException(
            status_code=503,
            detail="Groq API key not configured. Add GROQ_API_KEY to Railway env vars."
        )
    return query_tech_assistant(question)


# ─────────────────────────────────────────────────────────────────────────────
# GET /repos/{topic}
# ─────────────────────────────────────────────────────────────────────────────

VALID_SORT_OPTIONS = {"stars", "forks", "updated", "issues", "watchers"}

@app.get("/repos/{topic}")
async def github_repos(
    request: Request,
    topic: str,
    sort: str = "stars",
    language: str = None
):
    _check_rate_limit(request.client.host)
    if sort not in VALID_SORT_OPTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid sort '{sort}'.")
    if not app.state.github_ok:
        raise HTTPException(
            status_code=503,
            detail="GitHub token not configured. Add GITHUB_TOKEN to Railway env vars."
        )
    try:
        return search_repositories(query=topic, sort=sort, language=language or None)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"GitHub API error: {exc}")


@app.get("/repos")
async def github_repos_empty():
    return []


# ─────────────────────────────────────────────────────────────────────────────
# POST /heatmap
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/heatmap")
async def heatmap_endpoint(request: Request, data: dict):
    _check_rate_limit(request.client.host)
    sessions_raw = data.get("sessions", [])
    if not sessions_raw:
        raise HTTPException(status_code=400, detail="No sessions provided.")
    if len(sessions_raw) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 diffs per heatmap.")

    parsed_sessions = []
    for i, s in enumerate(sessions_raw):
        label     = s.get("label", f"diff-{i+1}").strip() or f"diff-{i+1}"
        diff_text = s.get("diff", "").strip()
        if not diff_text:
            continue
        sanitised_diff, _ = sanitise_for_llm(diff_text)
        intelligence = analyse_change_intelligence(sanitised_diff)
        parsed_sessions.append({"label": label, "intelligence": intelligence})

    if not parsed_sessions:
        raise HTTPException(status_code=400, detail="No valid diffs found.")

    return build_heatmap(parsed_sessions)


# ─────────────────────────────────────────────────────────────────────────────
# GET /health
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "groq":   app.state.groq_ok,
        "github": app.state.github_ok,
    }