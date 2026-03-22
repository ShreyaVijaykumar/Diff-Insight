"""
backend/utils/change_intelligence.py

Analyses a unified git diff and returns structured intelligence about
what changed, which layers were touched, conflict risk per file,
and a team-friendly breakdown — works on any language diff.
"""

import re
from collections import Counter


# ─────────────────────────────────────────────────────────────────────────────
# Layer classifier
# ─────────────────────────────────────────────────────────────────────────────

def _classify_layer(path: str) -> str:
    p = path.lower()
    if "test" in p or "spec" in p:                          return "Tests"
    if p.startswith("backend/llm"):                          return "LLM / AI"
    if p.startswith("backend/security"):                     return "Security"
    if p.startswith("backend/services"):                     return "Services"
    if p.startswith("backend/utils"):                        return "Utilities"
    if p.startswith("backend"):                              return "Backend"
    if p.startswith("frontend/static"):                      return "Frontend JS/CSS"
    if p.startswith("frontend/templates"):                   return "Frontend HTML"
    if p.startswith("frontend"):                             return "Frontend"
    if p.endswith((".yml", ".yaml", ".toml", ".env", ".cfg", ".ini")):
                                                             return "Config / Infra"
    if p.endswith((".md", ".rst", ".txt")):                  return "Docs"
    if "migration" in p or "migrate" in p or p.endswith(".sql"):
                                                             return "Database"
    return "Other"


def _change_type(path: str, added: int, removed: int) -> str:
    if added > 0 and removed == 0:  return "new"
    if added == 0 and removed > 0:  return "deleted"
    if removed > added * 0.7:       return "refactored"
    if added > removed * 3:         return "expanded"
    return "modified"


def _conflict_risk(added: int, removed: int, churn: int) -> str:
    if churn == 0:
        return "Low"
    deletion_ratio = removed / churn
    if deletion_ratio > 0.5 and churn > 8:   return "High"
    if churn > 20 or (deletion_ratio > 0.3 and churn > 5): return "Medium"
    return "Low"


# ─────────────────────────────────────────────────────────────────────────────
# Main analyser
# ─────────────────────────────────────────────────────────────────────────────

def analyse_change_intelligence(diff_text: str) -> dict:
    """
    Parse a unified diff and return:
      file_changes   — per-file breakdown list
      layer_summary  — which architectural layers were touched
      ext_breakdown  — file extension counts
      hotspots       — files with highest churn
      at_risk_files  — merge conflict candidates
      overall_type   — additive / refactor / mixed / destructive
      summary_line   — one human-readable sentence
    """
    if not diff_text or not diff_text.strip():
        return _empty()

    file_changes: list[dict] = []
    current: dict | None     = None
    added_count              = 0
    removed_count            = 0

    for line in diff_text.splitlines():

        # New file block
        if line.startswith("diff --git "):
            if current is not None:
                _finalise(current, added_count, removed_count, file_changes)
            m    = re.match(r'diff --git a/(.+) b/(.+)', line)
            path = m.group(2) if m else line.split()[-1]
            current       = {"path": path, "change_type": "modified"}
            added_count   = 0
            removed_count = 0
            continue

        # Plain diff -ruN header (no "diff --git")
        if line.startswith("+++ ") and current is None:
            path          = line[4:].split('\t')[0].strip().lstrip('b/')
            current       = {"path": path, "change_type": "modified"}
            added_count   = 0
            removed_count = 0
            continue

        if current is None:
            continue

        if line.startswith("--- /dev/null"):
            current["change_type"] = "new"
        elif line.startswith("+++ /dev/null"):
            current["change_type"] = "deleted"
        elif line.startswith("+") and not line.startswith("+++"):
            added_count += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed_count += 1

    if current is not None:
        _finalise(current, added_count, removed_count, file_changes)

    if not file_changes:
        return _empty()

    # Aggregates
    layer_counts: Counter = Counter()
    ext_counts:   Counter = Counter()
    total_added   = 0
    total_removed = 0

    for fc in file_changes:
        layer_counts[fc["layer"]] += 1
        ext = fc["path"].rsplit(".", 1)[-1] if "." in fc["path"] else "no ext"
        ext_counts[ext] += 1
        total_added   += fc["added"]
        total_removed += fc["removed"]

    total_churn = total_added + total_removed

    hotspots = sorted(file_changes, key=lambda f: f["churn"], reverse=True)[:3]

    if total_removed == 0:                      overall_type = "additive"
    elif total_added == 0:                      overall_type = "destructive"
    elif total_removed > total_added * 0.6:     overall_type = "refactor"
    else:                                        overall_type = "mixed"

    n_files   = len(file_changes)
    n_layers  = len(layer_counts)
    layer_str = ", ".join(k for k, _ in layer_counts.most_common(3))
    summary_line = (
        f"{n_files} file{'s' if n_files != 1 else ''} changed across "
        f"{n_layers} layer{'s' if n_layers != 1 else ''} "
        f"({layer_str}) — "
        f"+{total_added} / -{total_removed} lines — "
        f"{overall_type} change."
    )

    at_risk = [
        fc for fc in file_changes
        if fc["conflict_risk"] in ("High", "Medium")
    ]

    return {
        "file_changes":   file_changes,
        "layer_summary":  dict(layer_counts.most_common()),
        "ext_breakdown":  dict(ext_counts.most_common()),
        "hotspots":       hotspots,
        "at_risk_files":  at_risk,
        "overall_type":   overall_type,
        "summary_line":   summary_line,
        "total_added":    total_added,
        "total_removed":  total_removed,
        "total_churn":    total_churn,
    }


def _finalise(current: dict, added: int, removed: int, file_changes: list):
    churn = added + removed
    ctype = current.get("change_type", "modified")
    if ctype == "modified":
        ctype = _change_type(current["path"], added, removed)
    file_changes.append({
        "path":          current["path"],
        "layer":         _classify_layer(current["path"]),
        "change_type":   ctype,
        "added":         added,
        "removed":       removed,
        "churn":         churn,
        "conflict_risk": _conflict_risk(added, removed, churn),
    })


def _empty() -> dict:
    return {
        "file_changes":  [],
        "layer_summary": {},
        "ext_breakdown": {},
        "hotspots":      [],
        "at_risk_files": [],
        "overall_type":  "unknown",
        "summary_line":  "No changes detected.",
        "total_added":   0,
        "total_removed": 0,
        "total_churn":   0,
    }