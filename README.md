# DiffInsight 🔍

> **AI-powered Git diff analysis tool** — transform any git diff into structured code review reports, team-aware change breakdowns, and churn heatmaps. Built for developers, team leads, and anyone who reviews code.

🌐 **Live Demo**: [diff-insight-production.up.railway.app](https://diff-insight-production.up.railway.app/)

---

## What is DiffInsight?

DiffInsight takes a raw git diff and turns it into something actually useful — a structured review report, a breakdown of which parts of your codebase changed, merge conflict warnings, and a timeline showing which files keep getting touched across multiple versions.

It runs entirely in the browser, connects to Groq's free LLM API for AI analysis, and works on diffs from any language or framework.

---

## ✨ Features

### 🧠 AI-Powered Diff Analyzer

Upload a `.diff`, `.patch`, or `.txt` file — or paste a diff directly — and get a structured LLM-generated report in seconds.

- **Senior Reviewer mode** — concise, critical analysis focused on risks and actionable suggestions
- **Junior Mentor mode** — plain-English explanations, learning points, and encouragement for newer developers
- Supports standard git diff, `diff -ruN`, and most unified diff variants
- Files containing secrets (`.env`, private keys, vault configs) are automatically stripped before reaching the LLM

### 🗺️ Change Intelligence Panel

A team-aware breakdown of every file in the diff — works on any language, no AST parsing required.

- **Layers Touched** — instantly see which architectural layers were affected: Backend, Frontend, LLM/AI, Security, Tests, Config/Infra, Database, and more
- **Change Type Classification** — every file labelled as NEW, MODIFIED, EXPANDED, REFACTORED, or DELETED
- **Merge Conflict Candidates** — files flagged High/Medium/Low risk based on deletion ratio and churn volume
- **Churn Bar** — proportional visualisation of how much each file changed relative to the total
- **File Type Breakdown** — quick read on whether it was a backend-only, full-stack, or config change

### 📊 Diff Timeline & Churn Heatmap

Compare multiple versions of the same project to see which files keep getting touched.

- Add up to 20 diffs with custom labels (e.g. `v1→v2`, `sprint-3`, `hotfix-auth`)
- **Hotspot Leaderboard** — top 5 files ranked by total churn across all diffs with medal rankings
- **Heatmap Grid** — files × diffs matrix with colour-intensity cells (purple = low churn → orange = high churn)
- Hover tooltips showing exact churn count and change type per cell
- Churn bar and touches column showing cross-diff coverage at a glance

### 💬 Tech Assistant

Ask any technical question and get a structured answer from the LLM.

- Auto-detects topic from your question (40+ keywords: FastAPI, Docker, PostgreSQL, Redis, Terraform, AWS, PyTorch, RAG, JWT, and more)
- Structured answers covering: explanation, real example, industry use case, and common mistake
- Powered by Groq's `llama-3.3-70b-versatile` model

### 🔭 GitHub Explorer

Search GitHub repositories without leaving the app.

- Search by topic and filter by language
- Sort by ⭐ Stars, 🍴 Forks, 🕒 Recently Updated, 🐛 Most Issues, 👁️ Most Watchers
- Fetches up to 1000 results and sorts the full set client-side — every sort option operates over all results, not just the first page
- Results show all 5 metrics plus last updated date and a direct link

### 🔒 Security & Privacy

- **Two-layer diff sanitiser** — sensitive file paths (`.env`, `.pem`, `secret_manager`, `id_rsa`) are completely blocked before the LLM sees them; individual lines with credential-shaped values are redacted in-place
- GitHub token stored via HashiCorp Vault locally, or plain environment variable on cloud
- Rate limiting — 10 requests per 60 seconds per IP
- Sanitisation warning banner in the UI if any content was stripped

---

## 🚀 Live Deployment

**[diff-insight-production.up.railway.app](https://diff-insight-production.up.railway.app)**

Deployed on Railway with:
- **Groq API** (`llama-3.3-70b-versatile`) for LLM analysis — free tier, no GPU needed
- **FastAPI** backend with uvicorn
- **GitHub token** via Railway environment variables

---

## 📄 How to Generate a Git Diff File

A git diff is a text file showing exactly what changed between two versions of your code — which lines were added, removed, or modified. DiffInsight reads this file and analyses it.

### Understanding the diff format
```diff
diff --git a/backend/main.py b/backend/main.py
--- a/backend/main.py        ← original file
+++ b/backend/main.py        ← updated file
@@ -10,6 +10,8 @@           ← hunk header: line numbers affected
 def home():                  ← unchanged context line (space prefix)
-    return "hello"           ← line that was REMOVED (minus prefix)
+    return "hello world"     ← line that was ADDED (plus prefix)
+    # updated greeting       ← another added line
```

| Symbol | Meaning |
|--------|---------|
| `---` | Original (old) version of the file |
| `+++` | Updated (new) version of the file |
| `@@` | Hunk header showing which line numbers changed |
| `-` | Line that was removed |
| `+` | Line that was added |
| ` ` (space) | Unchanged context line |

---

### Method 1 — Compare two commits

Find your commit hashes with `git log`, then diff them.
```bash
# See your recent commits
git log --oneline

# Output example:
# a1b2c3d Add login feature
# e4f5g6h Fix bug in auth
# i7j8k9l Initial commit

# Compare any two commits (older → newer)
git diff i7j8k9l a1b2c3d > my_diff.txt
```

---

### Method 2 — Compare two branches

Use this when reviewing a feature branch before merging into main.
```bash
# Compare feature branch against main
git diff main feature-branch > branch_diff.txt

# Compare your current branch against main
git diff main > current_vs_main.txt
```

---

### Method 3 — See uncommitted changes

Use this to review what you have changed before committing.
```bash
# All unstaged changes (files edited but not staged yet)
git diff > unstaged.txt

# All staged changes (files you ran git add on)
git diff --staged > staged.txt

# Everything changed since last commit (staged + unstaged)
git diff HEAD > all_changes.txt
```

---

### Method 4 — Compare two tags or releases

Use this to see everything that changed between two versions of your project.
```bash
# Compare release tags
git diff v1.0 v2.0 > release_diff.txt

# Compare a tag against current state
git diff v1.0 HEAD > since_v1.txt
```

---

### Method 5 — Compare a specific file only

Use this when you only care about one file's history.
```bash
# See how one file changed between two commits
git diff e4f5g6h a1b2c3d -- backend/main.py > main_py_diff.txt

# See all changes to one file since last commit
git diff HEAD -- backend/main.py > main_changes.txt
```

---

### Method 6 — Compare two separate folders or zip files

Use this when you have two versions of a project as separate folders with no shared git history.
```bash
# Unzip your versions
unzip project-v1.zip -d v1
unzip project-v2.zip -d v2

# Generate the diff recursively across all files
diff -ru v1/ v2/ > v1_to_v2.txt

# If the zip extracts into a subfolder, go one level deeper
diff -ru v1/project-main/ v2/project-main/ > v1_to_v2.txt
```

The `-r` flag means recursive (goes through all subfolders) and `-u` gives unified format which DiffInsight can read.

---

### Method 7 — Using the Churn Heatmap with multiple diffs

If you have three versions of a project (v1, v2, v3), generate all combinations and load them into the Churn Heatmap to see which files changed the most across the entire history.
```bash
# Generate all three diffs
diff -ru v1/ v2/ > v1_to_v2.txt
diff -ru v2/ v3/ > v2_to_v3.txt
diff -ru v1/ v3/ > v1_to_v3.txt
```

Then in DiffInsight → **Churn Heatmap**:
1. Paste `v1_to_v2.txt` → label `v1→v2` → click **Add Diff**
2. Paste `v2_to_v3.txt` → label `v2→v3` → click **Add Diff**
3. Paste `v1_to_v3.txt` → label `v1→v3` → click **Add Diff**
4. Click **Generate Heatmap**

You will see exactly which files were touched in every version and which ones are hotspots.

---

### Tips

- Always save with `>` to write the output to a file — without it the diff just prints to the terminal and disappears
- Use `.txt` extension — DiffInsight accepts `.diff`, `.patch`, and `.txt`
- If your diff file is empty, the two versions are probably identical, or the folders extracted with a nested subfolder — try going one level deeper
- Large diffs (thousands of lines) work fine — DiffInsight handles up to 5MB

---

## 🛠️ Run Locally

### Prerequisites

- Python 3.10+
- A free [Groq API key](https://console.groq.com)
- A [GitHub Personal Access Token](https://github.com/settings/tokens) (for GitHub Explorer)

### 1. Clone the repository
```bash
git clone https://github.com/ShreyaVijaykumar/Diff-Insight.git
cd Diff-Insight/diffinsight
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set environment variables

Create a `.env` file — it is already in `.gitignore` so it will never be committed:
```
GROQ_API_KEY=gsk_your_key_here
GITHUB_TOKEN=ghp_your_token_here
```

Get your free Groq API key at [console.groq.com](https://console.groq.com)

Get your GitHub token at [github.com/settings/tokens](https://github.com/settings/tokens) — tick the `public_repo` scope.

### 4. Start the server
```bash
uvicorn backend.main:app --reload
```

### 5. Open in browser
```
http://127.0.0.1:8000
```

---

## 🗂️ Project Structure
```
diffinsight/
├── backend/
│   ├── main.py                      # FastAPI app, all endpoints, rate limiting
│   ├── llm/
│   │   ├── analyzer.py              # Groq-powered diff analysis
│   │   └── tech_assistant.py        # Groq-powered Q&A with topic detection
│   ├── security/
│   │   └── secret_manager.py        # Vault + env var fallback for tokens
│   ├── services/
│   │   └── github_service.py        # GitHub search with full result set sorting
│   └── utils/
│       ├── change_intelligence.py   # Team-aware diff breakdown (any language)
│       ├── churn_heatmap.py         # Multi-diff heatmap matrix builder
│       ├── diff_sanitiser.py        # Two-layer secret stripping before LLM
│       └── risk.py                  # Risk level computation
├── frontend/
│   ├── templates/
│   │   └── index.html               # Single-page app
│   └── static/
│       ├── script.js                # All frontend logic
│       └── style.css                # Dark glass UI with purple/orange gradients
├── railway.toml                     # Railway deployment config
├── requirements.txt
└── .env.example                     # Template for environment variables
```

---

## 🖥️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, Python 3.11 |
| LLM | Groq API — `llama-3.3-70b-versatile` |
| Diff Parsing | unidiff |
| Frontend | Vanilla JS, CSS (glass morphism) |
| Fonts | Syne + JetBrains Mono |
| Secrets | HashiCorp Vault (local) / env vars (cloud) |
| Deployment | Railway |

---

## 🔒 Security Notes

- Sensitive files (`.env`, private keys, vault configs, credential files) are **completely removed** from the diff before the LLM sees anything
- Hardcoded secrets in non-sensitive files (tokens, passwords, connection strings) are **redacted in-place** — the diff structure is preserved but values are replaced with `[REDACTED]`
- The UI shows a warning banner if any content was stripped, so you always know what the LLM saw
- GitHub tokens never appear in code — retrieved from Vault or environment variables only
- Rate limiting prevents abuse — 10 requests per 60 seconds per IP address

---

## 📈 Roadmap

- [ ] PR description auto-writer from diff
- [ ] Reviewer assignment suggester based on layers touched
- [ ] Commit message quality scorer
- [ ] Diff history and session comparison
- [ ] Export report as markdown / PDF
- [ ] JavaScript/TypeScript dependency graph support

---

## 👩‍💻 Author

**Shreya Vijaykumar**
[github.com/ShreyaVijaykumar](https://github.com/ShreyaVijaykumar)

---
