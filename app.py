"""Nivara - business & loan advisor (prototype). Run:  streamlit run app.py"""
import os
import uuid

import streamlit as st
import db
from engine import BUSINESSES, COMPETITION, analyze
from llm import answer
from rag import KnowledgeBase

LANG = {
    "English": dict(tag="Business & loan advisor for rural micro-entrepreneurs", vil="Village", dist="District",
        cap="Your own capital (Rs)", biz="Business", comp="Similar businesses within 5-10 km (your estimate)",
        go="Analyze", fin="Financial structuring", cash="Monthly cash-flow estimate", risk="Local risks to watch",
        rec="Recommended", cau="Proceed with caution", no="Not recommended", ask="Ask Nivara a question"),
    "हिन्दी": dict(tag="ग्रामीण उद्यमियों के लिए व्यवसाय व ऋण सलाहकार", vil="गाँव", dist="ज़िला",
        cap="आपकी अपनी पूँजी (₹)", biz="व्यवसाय", comp="5-10 किमी में समान व्यवसाय (आपका अनुमान)",
        go="विश्लेषण करें", fin="वित्तीय संरचना", cash="मासिक नकदी प्रवाह अनुमान", risk="स्थानीय जोखिम",
        rec="अनुशंसित", cau="सावधानी से आगे बढ़ें", no="अनुशंसित नहीं", ask="Nivara से पूछें"),
    "ગુજરાતી": dict(tag="ગ્રામીણ ઉદ્યમીઓ માટે બિઝનેસ અને લોન સલાહકાર", vil="ગામ", dist="જિલ્લો",
        cap="તમારી પોતાની મૂડી (₹)", biz="વ્યવસાય", comp="5-10 કિમીમાં સમાન વ્યવસાય (તમારો અંદાજ)",
        go="વિશ્લેષણ કરો", fin="નાણાકીય માળખું", cash="માસિક રોકડ પ્રવાહ અંદાજ", risk="સ્થાનિક જોખમો",
        rec="ભલામણ", cau="સાવધાની સાથે આગળ વધો", no="ભલામણ નથી", ask="Nivara ને પૂછો"),
}
inr = lambda n: f"₹{n:,.0f}"


def report_text(r, village, district):
    if not r or not r.scheme:
        return ""
    return (f"[Calculated] Location {village}, {district}. Business {r.business}. Own capital {inr(r.capital)}, "
            f"project cost {inr(r.project_cost)}, loan {inr(r.loan)}. Scheme {r.scheme}, {r.rate}% for {r.years} years, "
            f"moratorium {r.moratorium} months, EMI {inr(r.emi)}. "
            f"[Estimate] revenue {inr(r.revenue)}/month, costs {inr(r.costs)}, surplus {inr(r.surplus)}, "
            f"EMI coverage {r.coverage:.1f}x, verdict {r.verdict}.")


@st.cache_resource
def get_kb():
    db.init()
    return KnowledgeBase()


# Streamlit Cloud keeps keys in "Secrets"; expose them to llm.py as environment variables
try:
    for _k in ("GEMINI_API_KEY", "ANTHROPIC_API_KEY"):
        if _k in st.secrets:
            os.environ.setdefault(_k, str(st.secrets[_k]))
except Exception:
    pass

SID = st.session_state.setdefault("sid", uuid.uuid4().hex)  # each visitor sees only their own history
kb = get_kb()
st.set_page_config(page_title="Nivara", page_icon="🌱")
lang = st.sidebar.radio("Language / भाषा / ભાષા", list(LANG))
t = LANG[lang]
st.title("🌱 Nivara")
st.caption(t["tag"])
tab_an, tab_chat, tab_hist = st.tabs(["Analyzer", t["ask"], "History"])

with tab_an:
    c1, c2 = st.columns(2)
    village = c1.text_input(t["vil"], "Gondal")
    district = c2.text_input(t["dist"], "Rajkot")
    c3, c4 = st.columns(2)
    capital = c3.number_input(t["cap"], min_value=1000, value=100000, step=1000)
    business = c4.selectbox(t["biz"], list(BUSINESSES))
    competition = st.selectbox(t["comp"], list(COMPETITION), index=1)

    if st.button(t["go"], type="primary", use_container_width=True):
        r = analyze(capital, business, competition)
        st.session_state.update(report=r, village=village, district=district, chat=[])
        st.session_state["entry_id"] = db.save_entry(r, village, district, competition, SID)

    r = st.session_state.get("report")
    if r:
        label = {"green": t["rec"], "yellow": t["cau"], "red": t["no"]}[r.verdict]
        {"green": st.success, "yellow": st.warning, "red": st.error}[r.verdict](
            f"**{label}** - {r.business}, {st.session_state['village']}, {st.session_state['district']}\n\n{r.reason}")
        st.subheader(t["fin"])
        a, b, c = st.columns(3)
        a.metric("Your contribution (10%)", inr(r.capital)); b.metric("Project cost", inr(r.project_cost)); c.metric("Loan (90%)", inr(r.loan))
        if r.scheme:
            a, b, c = st.columns(3)
            a.metric("Scheme", r.scheme); b.metric("Interest / Tenure", f"{r.rate}% / {r.years} yrs"); c.metric("Moratorium", f"{r.moratorium} months")
            a, b = st.columns(2)
            a.metric("Monthly EMI", inr(r.emi)); b.metric("Total interest", inr(r.total_interest))
            st.caption(f"EMI assumes repayment over {r.months} months after the moratorium, no interest added during it. Confirm in official rules.")
            st.subheader(t["cash"])
            a, b, c = st.columns(3)
            a.metric("Revenue (est.)", inr(r.revenue)); b.metric("Costs (est.)", inr(r.costs)); c.metric("Surplus (est.)", inr(r.surplus))
            a, b = st.columns(2)
            a.metric("Left after EMI (est.)", inr(r.left_after_emi)); b.metric("EMI coverage", f"{r.coverage:.1f}x")
            d = BUSINESSES[r.business]
            st.subheader("SWOT (template estimate)")
            s1, s2 = st.columns(2)
            for col, title, key in ((s1, "Strengths", "strengths"), (s2, "Weaknesses", "weaknesses"),
                                    (s1, "Opportunities", "opportunities"), (s2, "Threats", "threats")):
                col.markdown(f"**{title}**\n" + "\n".join(f"- {x}" for x in d[key]))
            st.subheader(t["risk"])
            st.markdown("\n".join(f"- {x}" for x in r.risks))

with tab_chat:
    st.caption("Answers come only from your report and the knowledge base in the kb/ folder. If it is not there, Nivara says so.")
    hist = st.session_state.setdefault("chat", [])
    for m in hist:
        st.chat_message(m["role"]).markdown(m["content"])
    q = st.chat_input(t["ask"])
    if q:
        st.chat_message("user").markdown(q)
        chunks = kb.retrieve(q)
        rt = report_text(st.session_state.get("report"), st.session_state.get("village"), st.session_state.get("district"))
        text, used_llm = answer(q, rt, chunks, hist)
        src = ", ".join(sorted({c["source"] for c in chunks}))
        with st.chat_message("assistant"):
            st.markdown(text)
            st.caption(("Sources: " + src) if src else "No knowledge-base source matched")
        hist += [{"role": "user", "content": q}, {"role": "assistant", "content": text}]
        eid = st.session_state.get("entry_id")
        db.save_chat(eid, "user", q); db.save_chat(eid, "assistant", text, src)

with tab_hist:
    rows = db.list_entries(SID)
    st.dataframe(rows, use_container_width=True) if rows else st.info("No analyses saved yet.")
