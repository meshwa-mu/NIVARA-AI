"""Grounded chatbot: the LLM answers ONLY from the user's calculated report + retrieved KB chunks.

Free option : set GEMINI_API_KEY (free key from https://aistudio.google.com/apikey)
Paid option : set ANTHROPIC_API_KEY
No key / any error: falls back to showing the retrieved passages - still grounded, never invented.
"""
import json
import os
import urllib.request

GEMINI_MODEL = os.getenv("NIVARA_GEMINI_MODEL", "gemini-2.5-flash")
CLAUDE_MODEL = os.getenv("NIVARA_MODEL", "claude-sonnet-5-5")
NO_DATA = ("Insufficient data: I could not find this in the verified knowledge base or your report, "
           "so I won't guess. Please check with your bank, the District Industries Centre, or the official scheme document.")

SYSTEM = """You are Nivara, an advisor for rural micro-entrepreneurs in India.
Rules:
1. Use ONLY the facts in <report> and <context>. Never use outside knowledge for numbers, rules, rates or local facts.
2. If the answer is not in them, reply exactly: "Insufficient data" and say what to check instead. Do not guess.
3. Label statements: [Calculated] for numbers from <report> formulas, [Knowledge base: file] for context passages, [Estimate] for template estimates.
4. Reply in the same language as the user's question. Keep it short and simple. You support decisions; you never guarantee success."""


def _prompt(question, report_text, chunks):
    ctx = "\n\n".join(f"[{c['source']}] {c['text']}" for c in chunks) or "(no matching passages)"
    return f"<report>\n{report_text or '(no analysis run yet)'}\n</report>\n<context>\n{ctx}\n</context>\n\nQuestion: {question}"


def _gemini(key, prompt, history):
    contents = [{"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]}
                for m in history[-6:]]
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    body = json.dumps({"system_instruction": {"parts": [{"text": SYSTEM}]}, "contents": contents,
                       "generationConfig": {"temperature": 0.2, "maxOutputTokens": 700}}).encode()
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
        data=body, headers={"Content-Type": "application/json", "x-goog-api-key": key})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    return data["candidates"][0]["content"]["parts"][0]["text"]


def _claude(key, prompt, history):
    import anthropic
    msgs = [{"role": m["role"], "content": m["content"]} for m in history[-6:]] + [{"role": "user", "content": prompt}]
    r = anthropic.Anthropic(api_key=key).messages.create(model=CLAUDE_MODEL, max_tokens=700, system=SYSTEM, messages=msgs)
    return r.content[0].text


def answer(question, report_text, chunks, history):
    """Returns (answer_text, used_llm)."""
    if not chunks and not report_text:
        return NO_DATA, False
    prompt = _prompt(question, report_text, chunks)
    note = "(No API key set - showing the most relevant verified passages.)\n\n"
    for env, fn in (("GEMINI_API_KEY", _gemini), ("ANTHROPIC_API_KEY", _claude)):
        key = os.getenv(env)
        if key:
            try:
                return fn(key, prompt, history), True
            except Exception as e:  # network, quota, bad key...
                note = f"(LLM unavailable: {type(e).__name__}. Showing sources directly.)\n\n"
    if not chunks:
        return NO_DATA, False
    return note + "\n\n".join(f"**{c['source']}**: {c['text']}" for c in chunks), False
