import os, io, json, time, difflib
from html import escape
import streamlit as st
import plotly.graph_objects as go

from utils import extract_text_from_file, chunk_text, compute_risk_axes, highlight_terms, file_signature
from ai import extract_sections, risk_flags, summarize, rewrite_clause, negotiation_script, graphviz_dot
from db import init_db, save_analysis, clear_all, list_recent

st.set_page_config(page_title="ClauseLens — Legal Doc Demystifier", page_icon="⚖️", layout="wide")

with open("styles.css","r",encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="header">
  <img class="logo" src="assets/logo.svg" />
  <h1>ClauseLens</h1>
</div>
<div class="subcap">Built for Google hackathons · iOS‑minimalist dark UI</div>
""", unsafe_allow_html=True)

st.markdown("<div class='panel'>Upload a contract to get a plain-language summary, risk flags with severity, safer rewrites + negotiation scripts, a risk radar, a contract graph, and an exportable dark report.</div>", unsafe_allow_html=True)
st.markdown("<hr/>", unsafe_allow_html=True)

with st.sidebar:
    st.image("assets/logo.svg", width=40)
    st.caption("Dark minimalist legal document assistant.\n\n*Informational only, not legal advice.*")
    with st.expander("Settings", expanded=True):
        persona = st.selectbox("Persona", ["Student Tenant","Freelancer","Small Business Owner"], index=0)
        lang = st.selectbox("Language", ["English","Hinglish","தமிழ்","हिंदी"], index=0)
        street_mode = st.toggle("Street Lawyer Mode (casual tone)", value=False)
        save_to_db = st.toggle("Save analysis to local DB", value=False)
    with st.expander("Admin"):
        if st.button("Clear All Saved Analyses"):
            try:
                clear_all()
                st.toast("Cleared.", icon="✅")
            except Exception as e:
                st.warning(f"Couldn't clear DB: {e}")
        try:
            recent = list_recent(10)
            if recent:
                st.write("Recent analyses:")
                for r in recent:
                    st.caption(f"• {r[2]} — {time.strftime('%Y-%m-%d %H:%M', time.localtime(r[1]))} — {r[3]} / {r[4]}")
        except Exception:
            pass

SPICY_SAMPLE = (
    "Rent must be paid on the 1st of each month. If late, a penalty of ₹1,000 per day applies.\n"
    "Tenant is responsible for ALL repairs, including structural issues.\n"
    "Landlord may terminate the agreement at any time for any reason with 3 days’ notice.\n"
    "Security deposit is non-refundable at landlord’s sole discretion.\n"
    "Any disputes will be resolved only by arbitration in a city chosen by the landlord."
)

def inline_diff(old: str, new: str) -> str:
    old_words = old.split()
    new_words = new.split()
    sm = difflib.SequenceMatcher(None, old_words, new_words)
    html = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            html.append(" ".join(escape(w) for w in new_words[j1:j2]))
        elif tag == "insert":
            html.append("<ins>" + " ".join(escape(w) for w in new_words[j1:j2]) + "</ins>")
        elif tag == "delete":
            html.append("<del>" + " ".join(escape(w) for w in old_words[i1:i2]) + "</del>")
        elif tag == "replace":
            html.append("<del>" + " ".join(escape(w) for w in old_words[i1:i2]) + "</del>")
            html.append(" ")
            html.append("<ins>" + " ".join(escape(w) for w in new_words[j1:j2]) + "</ins>")
        html.append(" ")
    return "".join(html).strip()

tab_upload, tab_analyze, tab_rewrite, tab_export = st.tabs(["Upload / Input", "Analyze", "Rewrite / Negotiate", "Export"])

with tab_upload:
    st.markdown("### 1) Upload file or paste text")
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    uploaded = st.file_uploader("PDF / DOCX / TXT", type=["pdf","docx","txt"])
    pasted = st.text_area("...or Paste Contract Text", height=200, placeholder="Paste the contract text here")
    st.markdown("</div>", unsafe_allow_html=True)

    col_demo1, col_demo2 = st.columns([1,3])
    with col_demo1:
        if st.button("✨ Load Judge Demo"):
            st.session_state["contract_text"] = SPICY_SAMPLE
            st.session_state["file_name"] = "judge_demo_spicy.txt"
            st.session_state["doc_sig"] = "judge-demo"
            st.session_state["auto_run"] = True
            st.success("Loaded spicy demo text. Switch to Analyze tab!")

    text, src, file_name, sig = "", "", "", ""
    if uploaded:
        file_bytes = uploaded.read()
        text, src = extract_text_from_file(uploaded.name, file_bytes)
        file_name = uploaded.name
        sig = hashlib(file_bytes)
        if src == "image-unsupported":
            st.warning("Image uploads need OCR, which is disabled in this build. Please upload PDF/DOCX/TXT.")
        else:
            st.success(f"Loaded from {src.upper()} ({len(text)} chars).")
    elif pasted.strip():
        text = pasted.strip()
        file_name = "pasted_text.txt"
        import hashlib as _h; sig = _h.sha256(text.encode("utf-8")).hexdigest()[:16]
        st.success(f"Loaded pasted text ({len(text)} chars).")

    if text:
        st.session_state["contract_text"] = text
        st.session_state["doc_sig"] = sig
        st.session_state["file_name"] = file_name

with tab_analyze:
    st.markdown("### 2) Analyze")
    ct = st.session_state.get("contract_text","")
    if not ct:
        st.info("Upload or paste contract text in the first tab, or click ✨ Load Judge Demo.")
    else:
        col1, col2 = st.columns([2,1], gap="large")
        with col1:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.markdown("**Original Text (searchable)**")
            q = st.text_input("Search term (highlights):", "")
            highlighted = highlight_terms(ct, q)
            st.markdown(f"<div class='codebox'>{highlighted}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            run_clicked = st.button("Run AI Analysis — Summary · Flags · Graph · Radar")
            st.markdown("</div>", unsafe_allow_html=True)

            auto = st.session_state.get("auto_run", False)
            do_run = run_clicked or auto

            if do_run:
                st.session_state["auto_run"] = False
                with st.spinner("Analyzing with Gemini..."):
                    try:
                        sections = extract_sections(ct)
                        flags = risk_flags(sections, persona)
                        lang_mode = lang if lang != "Hinglish" else "Hinglish"
                        tone = " (casual)" if street_mode else ""
                        summary_text = summarize(sections, persona + tone, lang_mode)
                        dot = graphviz_dot(sections)
                    except Exception as e:
                        st.error(f"AI error: {e}")
                        sections, flags, summary_text, dot = {}, [], "", ""

                st.session_state["sections"] = sections
                st.session_state["flags"] = flags
                st.session_state["summary"] = summary_text
                st.session_state["dot"] = dot

        sections = st.session_state.get("sections")
        flags = st.session_state.get("flags", [])
        summary_text = st.session_state.get("summary","")
        dot = st.session_state.get("dot","")

        if flags:
            hi = sum(1 for f in flags if str(f.get("severity","")).lower()=="high")
            md = sum(1 for f in flags if str(f.get("severity","")).lower()=="medium")
            lo = sum(1 for f in flags if str(f.get("severity","")).lower()=="low")
            st.markdown(
                f"<div class='badges'>"
                f"<span class='badge high'>🔴 High: {hi}</span>"
                f"<span class='badge medium'>🟠 Med: {md}</span>"
                f"<span class='badge low'>🟢 Low: {lo}</span>"
                f"</div>",
                unsafe_allow_html=True
            )

        if sections:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.markdown("#### Extracted Sections")
            st.json(sections, expanded=False)
            st.markdown("</div>", unsafe_allow_html=True)

        if flags:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.markdown("#### Risk Flags")
            chip_map = {"high":"chip high","medium":"chip medium","low":"chip low"}
            chips_html = ""
            for f in flags:
                sev = f.get("severity","low").lower()
                cls = chip_map.get(sev,"chip")
                chips_html += f"<span class='{cls}'> {f.get('flag','')} • {sev} </span>"
            st.markdown(chips_html, unsafe_allow_html=True)
            for f in flags:
                with st.expander(f"🔎 {f.get('flag','(flag)')} — {f.get('severity','low').upper()}"):
                    st.write(f"**Where:** {f.get('where','')}")
                    st.write(f"**Why:** {f.get('why','')}")
                    if f.get('quote'): 
                        st.markdown(f"**Quote:**\n\n<div class='codebox'>{f['quote']}</div>", unsafe_allow_html=True)
                    if f.get('suggested_fix'):
                        st.write(f"**Suggested Fix:** {f['suggested_fix']}")
            st.markdown("</div>", unsafe_allow_html=True)

        if summary_text:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.markdown("#### Plain-Language Summary")
            st.markdown(summary_text)
            st.markdown("</div>", unsafe_allow_html=True)

        if dot:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.markdown("#### Contract Graph (DOT)")
            try:
                st.graphviz_chart(dot)
            except Exception as e:
                st.code(dot, language="dot")
            st.markdown("</div>", unsafe_allow_html=True)

        if flags:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.markdown("#### Risk Radar")
            axes = compute_risk_axes(flags)
            cats = list(axes.keys())
            vals = list(axes.values())
            fig = go.Figure(data=go.Scatterpolar(r=vals+vals[:1], theta=cats+cats[:1], fill='toself'))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=False,
                              paper_bgcolor="#000000", plot_bgcolor="#000000", font_color="#FFFFFF")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

with tab_rewrite:
    st.markdown("### 3) Rewrite / Negotiate")
    ct = st.session_state.get("contract_text","")
    if not ct:
        st.info("Upload or paste contract text in the first tab.")
    else:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        clause = st.text_area("Paste a clause to rewrite", "", height=160, placeholder="Paste a risky clause here...")
        click = st.button("Rewrite Clause")
        st.markdown("</div>", unsafe_allow_html=True)

        if click:
            if clause.strip():
                with st.spinner("Rewriting with Gemini..."):
                    rw = rewrite_clause(clause.strip(), persona)
                if isinstance(rw, dict):
                    st.markdown("<div class='panel'>", unsafe_allow_html=True)
                    st.markdown("**Improved Clause**")
                    improved = rw.get("improved_clause","")
                    st.markdown(f"<div class='codebox'>{improved}</div>", unsafe_allow_html=True)
                    st.markdown("**Why this is safer**")
                    st.write(rw.get("one_line_rationale",""))
                    try:
                        old_words = clause.strip()
                        new_words = improved
                        sm = difflib.SequenceMatcher(None, old_words.split(), new_words.split())
                        html = []
                        for tag,i1,i2,j1,j2 in sm.get_opcodes():
                            if tag=="equal": html.append(" ".join(escape(w) for w in new_words.split()[j1:j2]))
                            elif tag=="insert": html.append("<ins>"+" ".join(escape(w) for w in new_words.split()[j1:j2])+"</ins>")
                            elif tag=="delete": html.append("<del>"+" ".join(escape(w) for w in old_words.split()[i1:i2])+"</del>")
                            elif tag=="replace":
                                html.append("<del>"+" ".join(escape(w) for w in old_words.split()[i1:i2])+"</del>")
                                html.append(" ")
                                html.append("<ins>"+" ".join(escape(w) for w in new_words.split()[j1:j2])+"</ins>")
                            html.append(" ")
                        diff_html = "".join(html).strip()
                        st.markdown("**Inline Diff (added = green, removed = red)**")
                        st.markdown(f"<div class='codebox'>{diff_html}</div>", unsafe_allow_html=True)
                    except Exception:
                        pass
                    scr = negotiation_script(persona, improved)
                    st.markdown("**Negotiation Script**")
                    st.markdown(f"<div class='codebox'>{scr}</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.warning("Please paste a clause to rewrite.")

with tab_export:
    st.markdown("### 4) Export Report")
    sections = st.session_state.get("sections")
    flags = st.session_state.get("flags", [])
    summary_text = st.session_state.get("summary","")
    file_name = st.session_state.get("file_name", "contract")

    if not sections and not summary_text:
        st.info("Run analysis first.")
    else:
        html = io.StringIO()
        html.write("<html><head><meta charset='utf-8'><style>body{background:#000;color:#fff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;padding:20px} .codebox{background:#0b0b0b;border:1px solid rgba(255,255,255,0.08);padding:12px;border-radius:14px} .chip{display:inline-block;margin:4px 6px;padding:4px 8px;border-radius:999px;border:1px solid rgba(255,255,255,0.12)} .badges{display:flex;gap:.5rem;flex-wrap:wrap;margin:.25rem 0 1rem}.badge{border:1px solid rgba(255,255,255,.12);border-radius:999px;padding:.35rem .7rem;background:#0c0c0c;font-weight:600}</style></head><body>")
        html.write(f"<h1>ClauseLens Report — {file_name}</h1>")

        if flags:
            hi = sum(1 for f in flags if str(f.get('severity','')).lower()=='high')
            md = sum(1 for f in flags if str(f.get('severity','')).lower()=='medium')
            lo = sum(1 for f in flags if str(f.get('severity','')).lower()=='low')
            html.write(f"<div class='badges'><span class='badge'>High: {hi}</span><span class='badge'>Med: {md}</span><span class='badge'>Low: {lo}</span></div>")

        if summary_text:
            html.write("<h2>Plain-Language Summary</h2>")
            html.write(f"<div class='codebox'>{summary_text}</div>")
        if flags:
            html.write("<h2>Risk Flags</h2><div>")
            for f in flags:
                html.write(f"<div class='chip'>{f.get('flag','')} — {f.get('severity','low')}</div>")
            html.write("</div>")
            for f in flags:
                html.write("<hr/>")
                html.write(f"<h3>{f.get('flag','(flag)')}</h3>")
                html.write(f"<p><b>Where:</b> {f.get('where','')}</p>")
                html.write(f"<p><b>Why:</b> {f.get('why','')}</p>")
                if f.get('quote'):
                    html.write(f"<div class='codebox'>{f['quote']}</div>")
                if f.get('suggested_fix'):
                    html.write(f"<p><b>Suggested Fix:</b> {f['suggested_fix']}</p>")
        if sections:
            html.write("<h2>Extracted Sections (JSON)</h2>")
            from html import escape as _esc
            html.write(f"<div class='codebox'><pre>{_esc(json.dumps(sections, indent=2, ensure_ascii=False))}</pre></div>")
        html.write("<p style='color:#a1a1a1'>Generated by ClauseLens. Informational only, not legal advice.</p>")
        html.write("</body></html>")
        data = html.getvalue().encode("utf-8")

        st.download_button("Download HTML Report", data=data, file_name=f"{file_name}_clauselens_report.html", mime="text/html")
