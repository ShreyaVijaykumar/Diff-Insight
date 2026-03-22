"""
backend/llm/tech_assistant.py

Technical Q&A using Groq API.
Replaces the local Ollama implementation for cloud deployment.
"""

import os
import re
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Topic keyword map — longest match wins
TOPIC_KEYWORDS = {
    "fastapi":        "FastAPI", "django":         "Django",
    "flask":          "Flask",   "sqlalchemy":     "SQLAlchemy",
    "postgresql":     "PostgreSQL", "postgres":    "PostgreSQL",
    "redis":          "Redis",   "docker":         "Docker",
    "kubernetes":     "Kubernetes", "k8s":         "Kubernetes",
    "terraform":      "Terraform", "aws":          "AWS",
    "gcp":            "GCP",     "azure":          "Azure",
    "git":            "Git",     "github":         "GitHub",
    "react":          "React",   "typescript":     "TypeScript",
    "javascript":     "JavaScript", "python":      "Python",
    "rust":           "Rust",    "golang":         "Go",
    "pytorch":        "PyTorch", "tensorflow":     "TensorFlow",
    "transformer":    "Transformers", "rag":       "RAG",
    "llm":            "LLMs",    "embeddings":     "Embeddings",
    "api":            "REST APIs", "graphql":      "GraphQL",
    "websocket":      "WebSockets", "async":       "Async Python",
    "microservice":   "Microservices", "ci":       "CI/CD",
    "jwt":            "JWT",     "oauth":          "OAuth",
    "encryption":     "Encryption", "hash":        "Hashing",
    "mongodb":        "MongoDB", "mysql":          "MySQL",
    "celery":         "Celery",  "kafka":          "Kafka",
    "nginx":          "Nginx",   "linux":          "Linux",
}

SYSTEM_PROMPT = """You are a knowledgeable and concise technical assistant for software developers.
When answering questions:

1. EXPLANATION — Clear, simple explanation of the concept
2. REAL EXAMPLE — A concrete, practical code or real-world example
3. WHEN TO USE — Industry use cases and when it applies
4. COMMON MISTAKE — The most common misconception or pitfall

Keep answers focused and practical. No fluff.
"""


def extract_topic(question: str) -> str:
    q = question.lower()
    q = re.sub(r'\b(what|is|are|how|does|do|explain|tell|me|about|the|a|an)\b', '', q)
    q = q.strip()

    # Longest match first
    for keyword in sorted(TOPIC_KEYWORDS, key=len, reverse=True):
        if keyword in q:
            return TOPIC_KEYWORDS[keyword]

    # Fallback: first meaningful word
    words = [w for w in q.split() if len(w) > 3]
    return words[0].title() if words else "this topic"


def query_tech_assistant(question: str) -> dict:
    """
    Answer a technical question using Groq.

    Returns
    -------
    { "answer": str, "topic": str }
    """
    if not question or not question.strip():
        return {"answer": "Please ask a question.", "topic": "unknown"}

    topic = extract_topic(question)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": question},
            ],
            temperature=0.4,
            max_tokens=800,
        )
        answer = response.choices[0].message.content.strip()
        return {"answer": answer, "topic": topic}

    except Exception as e:
        return {
            "answer": f"⚠️  Assistant failed: {str(e)}\n\nCheck your GROQ_API_KEY.",
            "topic":  topic,
        }