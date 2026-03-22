"""
backend/llm/analyzer.py

Code review analysis using Groq API (llama-3.3-70b-versatile).
Replaces the local Ollama implementation for cloud deployment.
"""

import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

REVIEWER_PROMPT = """You are a senior software engineer doing a thorough code review.
Analyse the following git diff and provide a structured review covering:

1. SUMMARY — What changed and why (2-3 sentences)
2. RISKS — Security, performance, or stability concerns (be specific)
3. CODE QUALITY — Readability, maintainability, patterns used
4. SUGGESTIONS — Concrete actionable improvements
5. VERDICT — APPROVE / REQUEST CHANGES / NEEDS DISCUSSION

Be direct, specific, and reference actual lines or patterns from the diff.
Do not pad the response — if something is fine, say so briefly and move on.
"""

JUNIOR_PROMPT = """You are a patient senior developer mentoring a junior engineer.
Analyse the following git diff and explain it clearly:

1. WHAT CHANGED — Plain English explanation of every file touched
2. WHY IT MATTERS — What problem this solves or what feature it adds
3. GOOD PRACTICES — What was done well that the junior should learn from
4. THINGS TO WATCH — Potential issues explained in simple terms
5. LEARNING POINTS — Key concepts or patterns demonstrated in this diff

Use simple language. Explain technical terms when you use them.
Be encouraging but honest.
"""


def analyze_diff(diff_text: str, risk: str = "LOW", mode: str = "reviewer") -> str:
    """
    Analyse a git diff using Groq's LLM.

    Parameters
    ----------
    diff_text : str  — sanitised diff content
    risk      : str  — pre-computed risk level (HIGH/MEDIUM/LOW)
    mode      : str  — 'reviewer' or 'junior'
    """
    if not diff_text or not diff_text.strip():
        return "No diff content to analyse."

    system_prompt = JUNIOR_PROMPT if mode == "junior" else REVIEWER_PROMPT
    user_message  = f"Risk Level (pre-computed): {risk}\n\n```diff\n{diff_text[:12000]}\n```"

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.3,
            max_tokens=1500,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return (
            f"⚠️  LLM analysis failed: {str(e)}\n\n"
            "Check your GROQ_API_KEY environment variable."
        )