# Nivara - rural business & loan advisor (prototype)

## Run (Visual Studio / VS Code)
1. Open this folder. In a terminal: `python -m venv .venv`, then `.venv\Scripts\activate` (Windows).
2. `pip install -r requirements.txt`
3. Optional LLM chatbot - FREE key: get one at https://aistudio.google.com/apikey then run `setx GEMINI_API_KEY "your-key"` (reopen terminal). Or use `ANTHROPIC_API_KEY` (paid).
   Without a key the chatbot still works and shows the matching knowledge-base passages.
4. `streamlit run app.py`

## What is where
- `engine.py` financial structuring + feasibility (edit SCHEMES / BUSINESSES)
- `db.py` SQLite file `nivara.db`: every analysis and chat message is stored (History tab)
- `rag.py` + `kb/` the knowledge base. Add more .md/.txt files here (official scheme PDFs converted to text, Census/MSME notes). The first lines of each paragraph should say where the facts came from.
- `llm.py` the chatbot: answers only from your report + retrieved passages, otherwise says "Insufficient data"
- `app.py` Streamlit UI

## How hallucination is limited
1. Numbers come from code (engine.py), not from the LLM.
2. The LLM only sees your report and retrieved kb/ passages, with a strict prompt.
3. If retrieval finds nothing above the threshold, the bot says "Insufficient data".
4. Answers show their sources.
The starter kb/ files are general and must be replaced with official documents before real use.
