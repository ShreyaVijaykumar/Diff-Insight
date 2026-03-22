"""
backend/utils/diff_sanitiser.py

Strips sensitive content from diff text BEFORE it is sent to any LLM.
Two layers of protection:

  1. FILE-LEVEL BLOCK  — entire diff hunks for sensitive file paths are
     replaced with a single redaction notice. The LLM never sees the
     filename or any of its content.

  2. LINE-LEVEL REDACT — for files that pass the path check, individual
     lines that still contain credential-shaped values are redacted in-place.
     The structure of the diff is preserved so the LLM can still reason
     about the surrounding code.

Nothing from this module is logged or stored — the sanitised string is
only held in memory for the duration of the LLM call.
"""

import re


# ─────────────────────────────────────────────────────────────────────────────
# File-level block list
# Files matching any of these patterns are completely removed from the diff
# before it reaches the LLM.
# ─────────────────────────────────────────────────────────────────────────────

BLOCKED_FILE_PATTERNS: list[re.Pattern] = [re.compile(p, re.IGNORECASE) for p in [
    # Environment / config files
    r'(^|/)\.env$',
    r'(^|/)\.env\.',
    r'(^|/)\.envrc$',
    r'(^|/)\.env\.local$',
    r'(^|/)\.env\.production$',
    r'(^|/)\.env\.staging$',

    # Key / certificate files
    r'\.pem$',
    r'\.key$',
    r'\.p12$',
    r'\.pfx$',
    r'\.crt$',
    r'\.cer$',
    r'id_rsa',
    r'id_ed25519',
    r'id_ecdsa',

    # Secret / credential source files
    r'secret[_\-]?manager',
    r'secret[_\-]?store',
    r'credential',
    r'vault[_\-]?client',
    r'auth[_\-]?config',
    r'jwt[_\-]?secret',
    r'api[_\-]?keys?\.py',
    r'api[_\-]?keys?\.js',
    r'api[_\-]?keys?\.ts',

    # Known sensitive config formats
    r'(^|/)secrets?\.(json|yaml|yml|toml)$',
    r'(^|/)config/secrets',
    r'(^|/)\.aws/credentials',
    r'(^|/)\.ssh/',
]]


# ─────────────────────────────────────────────────────────────────────────────
# Line-level redaction patterns
# Applied to lines inside files that are NOT blocked at the file level.
# ─────────────────────────────────────────────────────────────────────────────

SENSITIVE_LINE_PATTERNS: list[re.Pattern] = [re.compile(p, re.IGNORECASE) for p in [
    # Generic key=value credential assignments
    r'(password|passwd|secret|api_key|apikey|access_key|secret_key|private_key|auth_token|jwt_secret|salt|encryption_key)\s*=\s*["\']?[^\s"\']{6,}["\']?',

    # Known token formats
    r'hvs\.[a-zA-Z0-9_\-]{10,}',       # HashiCorp Vault
    r'ghp_[a-zA-Z0-9]{36}',             # GitHub PAT classic
    r'github_pat_[a-zA-Z0-9_]{80,}',    # GitHub PAT fine-grained
    r'sk-[a-zA-Z0-9]{32,}',             # OpenAI
    r'sk-ant-[a-zA-Z0-9\-]{80,}',       # Anthropic
    r'xoxb-[a-zA-Z0-9\-]+',             # Slack bot token
    r'xoxp-[a-zA-Z0-9\-]+',             # Slack user token
    r'AKIA[0-9A-Z]{16}',                # AWS access key ID
    r'[0-9a-zA-Z/+]{40}(?=[^a-zA-Z0-9/+]|$)',  # AWS secret (40-char base64)

    # Connection strings with embedded credentials
    r'(postgresql|mysql|mongodb(\+srv)?|redis|amqp)://[^:\s]+:[^@\s]+@',
    r'(jdbc:[^:]+)://[^:\s]+:[^@\s]+@',

    # Bearer / Authorization headers in code
    r'["\']?Authorization["\']?\s*:\s*["\']?Bearer\s+[a-zA-Z0-9\-_\.]{20,}',
    r'["\']?Authorization["\']?\s*:\s*["\']?Basic\s+[a-zA-Z0-9+/=]{10,}',
]]


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def sanitise_for_llm(diff_text: str) -> tuple[str, dict]:
    """
    Sanitise a diff before sending to an LLM.

    Returns
    -------
    sanitised_diff : str
        Safe version of the diff with secrets removed.
    report : dict
        Summary of what was removed, for logging/debugging (never sent to LLM).
        {
          "blocked_files":   list of filenames that were fully removed,
          "redacted_lines":  int,
          "total_lines_in":  int,
          "total_lines_out": int,
        }
    """
    if not diff_text or not diff_text.strip():
        return diff_text, _empty_report()

    lines           = diff_text.splitlines()
    sanitised       = []
    blocked_files   = []
    redacted_count  = 0
    skip_file       = False
    current_file    = ""

    for line in lines:

        # ── Detect start of a new file block ──────────────────────────────
        if line.startswith("diff --git "):
            m = re.match(r'diff --git a/(.+) b/(.+)', line)
            current_file = m.group(2) if m else line.split()[-1]

            skip_file = _is_blocked(current_file)

            if skip_file:
                blocked_files.append(current_file)
                sanitised.append(
                    f"# [FILE REDACTED — sensitive path: {_safe_label(current_file)}]"
                )
            else:
                sanitised.append(line)
            continue

        # ── Skip all lines belonging to a blocked file ────────────────────
        if skip_file:
            continue

        # ── Redact sensitive values in non-blocked lines ──────────────────
        redacted, changed = _redact_line(line)
        if changed:
            redacted_count += 1
        sanitised.append(redacted)

    out_text = "\n".join(sanitised)

    report = {
        "blocked_files":  blocked_files,
        "redacted_lines": redacted_count,
        "total_lines_in": len(lines),
        "total_lines_out": len(sanitised),
    }

    return out_text, report


def has_sensitive_content(diff_text: str) -> bool:
    """Quick check — returns True if the diff contains anything that
    would be blocked or redacted. Useful for showing a UI warning."""
    _, report = sanitise_for_llm(diff_text)
    return bool(report["blocked_files"]) or report["redacted_lines"] > 0


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _is_blocked(path: str) -> bool:
    return any(p.search(path) for p in BLOCKED_FILE_PATTERNS)


def _redact_line(line: str) -> tuple[str, bool]:
    """Replace sensitive values in a single diff line. Returns (line, changed)."""
    result  = line
    changed = False
    for pattern in SENSITIVE_LINE_PATTERNS:
        def _replace(m: re.Match) -> str:
            text = m.group(0)
            # Preserve the key name if it's a key=value pattern
            eq_pos = text.find('=')
            if eq_pos != -1:
                return text[:eq_pos + 1] + '[REDACTED]'
            return '[REDACTED]'
        new = pattern.sub(_replace, result)
        if new != result:
            changed = True
            result  = new
    return result, changed


def _safe_label(path: str) -> str:
    """Return just the filename, not full path, for the redaction notice."""
    return path.split('/')[-1] if '/' in path else path


def _empty_report() -> dict:
    return {
        "blocked_files":   [],
        "redacted_lines":  0,
        "total_lines_in":  0,
        "total_lines_out": 0,
    }