import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "deepseek-coder:6.7b"

REVIEWER_PROMPT = """
You are a senior software engineer performing a strict code review.

Respond ONLY in the following format:

TITLE:
CHANGE_SUMMARY:
MODIFIED_FILES:
WHAT_CHANGED:
WHY_CHANGED:
RISK_LEVEL:
IMPACT:
REVIEWER_NOTES:

Rules:
- Be concise and assertive
- Call out poor practices
- Flag missing tests, edge cases, or unclear intent
- No markdown, no emojis
"""

JUNIOR_PROMPT = """
You are a helpful mentor explaining a git diff to a junior developer.

Respond ONLY in the following format:

TITLE:
CHANGE_SUMMARY:
WHAT_CHANGED:
WHY_CHANGED:
IMPACT:
LEARNING_NOTES:

Rules:
- Be friendly and explanatory
- No markdown, no emojis
- Explain clearly what each file change does and its importance
"""

def prepare_diff(diff_text, max_lines=200):
    lines = diff_text.splitlines()
    if len(lines) > max_lines:
        return "\n".join(lines[:max_lines]) + f"\n... ({len(lines) - max_lines} more lines truncated)"
    return diff_text

def analyze_diff(diff_text: str, risk: str, mode: str = "reviewer") -> str:
    system_prompt = REVIEWER_PROMPT if mode == "reviewer" else JUNIOR_PROMPT
    diff_text = prepare_diff(diff_text)

    prompt = f"""
Precomputed Risk Level: {risk}

Git Diff:
{diff_text}
"""

    payload = {
        "model": MODEL,
        "prompt": system_prompt + prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()
    resp_json = response.json()
    print("DEBUG JSON:", resp_json)

    detailed_report = resp_json.get("response", "")
    if not detailed_report.strip():
        detailed_report = "⚠️ LLM did not return a detailed analysis. Check the diff size or prompt."

    summary_intro = f"""
DIFFINSIGHT REPORT
------------------
Risk Level : {risk.upper()}

"""
    return summary_intro + detailed_report
