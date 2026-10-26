# Put Nivara online (works on any Android phone via a link)

1. Create a free GitHub account and a new PUBLIC repository named nivara.
2. Upload every file in this folder (Add file > Upload files). Do NOT upload .venv, nivara.db or any real API key.
3. Go to share.streamlit.io, sign in with GitHub, click New app.
4. Pick your repo, branch main, main file app.py. Under Advanced settings choose Python 3.11 and paste into Secrets:
   GEMINI_API_KEY = "your-free-key"
5. Click Deploy. You get a link like https://your-name-nivara.streamlit.app
6. On Android: open the link in Chrome > menu (three dots) > Add to Home screen (or Install app).

Notes: free hosting may reset the nivara.db file when the app restarts, so saved history is temporary.
Each visitor only sees their own history. Use a hosted database before collecting real farmer data.
