"""
backend/utils/churn_heatmap.py

Builds a file-churn heatmap matrix from multiple parsed diff intelligence
results. Each diff becomes a column; each unique file becomes a row.
Cell value = churn (lines added + removed) for that file in that diff.
"""


def build_heatmap(sessions: list[dict]) -> dict:
    """
    Parameters
    ----------
    sessions : list of dicts, each with:
        - label       : str  — user-supplied name for this diff (e.g. "v1→v2")
        - intelligence: dict — output of analyse_change_intelligence()

    Returns
    -------
    {
      labels     : ["diff-1", "diff-2", ...],
      matrix     : rows sorted by total churn desc, each with file/layer/total/touches/cells
      hotspots   : top 5 files by total churn,
      max_churn  : int  — largest single-cell value (for colour scaling),
      total_diffs: int,
      summary    : str,
    }
    """

    if not sessions:
        return _empty()

    labels = [s.get("label", f"diff-{i+1}") for i, s in enumerate(sessions)]

    # Collect every unique file path + its layer
    file_meta: dict[str, str] = {}
    for s in sessions:
        for fc in s.get("intelligence", {}).get("file_changes", []):
            path = fc["path"]
            if path not in file_meta:
                file_meta[path] = fc.get("layer", "Other")

    if not file_meta:
        return _empty()

    rows = []
    for path, layer in file_meta.items():
        cells   = []
        total   = 0
        touches = 0

        for s in sessions:
            match = next(
                (fc for fc in s.get("intelligence", {}).get("file_changes", [])
                 if fc["path"] == path),
                None
            )
            if match:
                churn = match.get("churn", 0)
                cells.append({"churn": churn, "change_type": match.get("change_type")})
                total   += churn
                touches += 1
            else:
                cells.append({"churn": 0, "change_type": None})

        rows.append({
            "file":    path,
            "layer":   layer,
            "total":   total,
            "touches": touches,
            "cells":   cells,
        })

    rows.sort(key=lambda r: r["total"], reverse=True)

    max_churn = max((c["churn"] for r in rows for c in r["cells"]), default=1)

    hotspots = rows[:5]

    n_files  = len(rows)
    n_diffs  = len(sessions)
    top_file = rows[0]["file"] if rows else "—"
    summary  = (
        f"{n_files} unique file{'s' if n_files != 1 else ''} tracked across "
        f"{n_diffs} diff{'s' if n_diffs != 1 else ''}. "
        f"Hottest file: {top_file} ({rows[0]['total']} total churn lines)."
        if rows else "No data."
    )

    return {
        "labels":      labels,
        "matrix":      rows,
        "hotspots":    hotspots,
        "max_churn":   max_churn,
        "total_diffs": n_diffs,
        "summary":     summary,
    }


def _empty() -> dict:
    return {
        "labels": [], "matrix": [], "hotspots": [],
        "max_churn": 0, "total_diffs": 0, "summary": "No data.",
    }