"""Tiny dependency-free RAG: chunk the files in kb/, rank with BM25.

If nothing in the knowledge base matches well, retrieve() returns [] and the
chatbot must say "insufficient data" instead of guessing.
"""
import math
import re
from collections import Counter
from pathlib import Path

KB_DIR = Path(__file__).parent / "kb"
STOP = set("a an the is are was were of to in on for and or with what how do does can i my me it this that "
           "be as at by from your you should which will if".split())
MIN_SCORE = 1.2  # below this we treat the knowledge base as having no answer


def _tok(text):
    return [w for w in re.findall(r"[a-z0-9\u0900-\u097f\u0a80-\u0aff%.]+", text.lower()) if w not in STOP]


class KnowledgeBase:
    def __init__(self, kb_dir=KB_DIR):
        self.chunks = []  # dicts: source, text, tokens
        for f in sorted(Path(kb_dir).glob("*.md")) + sorted(Path(kb_dir).glob("*.txt")):
            for para in re.split(r"\n\s*\n", f.read_text(encoding="utf-8")):
                para = para.strip()
                if len(para) > 40 and not para.startswith("---"):
                    self.chunks.append({"source": f.name, "text": para, "tokens": _tok(para)})
        n = max(len(self.chunks), 1)
        df = Counter(t for c in self.chunks for t in set(c["tokens"]))
        self.idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}
        self.avg = sum(len(c["tokens"]) for c in self.chunks) / n

    def retrieve(self, query, k=3):
        q = _tok(query)
        scored = []
        for c in self.chunks:
            tf, L = Counter(c["tokens"]), len(c["tokens"])
            s = sum(self.idf.get(t, 0) * tf[t] * 2.2 / (tf[t] + 1.2 * (0.25 + 0.75 * L / self.avg))
                    for t in q if t in tf)
            if s >= MIN_SCORE:
                scored.append((s, c))
        scored.sort(key=lambda x: -x[0])
        return [{"source": c["source"], "text": c["text"], "score": round(s, 2)} for s, c in scored[:k]]
