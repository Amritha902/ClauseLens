<img width="1024" height="1024" alt="ChatGPT Image Sep 3, 2025, 08_10_04 PM" src="https://github.com/user-attachments/assets/41fcf067-02da-494e-9865-7c97b4df5201" />
# ⚖️ ClauseLens — AI Legal Doc Demystifier (Dark iOS UI)

Built for Google GenAI Hackathon (Student Track). Upload a contract → get a plain-language summary, risk flags with severity, safer rewrites with inline diff, negotiation scripts, a risk radar, a contract graph, and an exportable dark report.

---

## 🚀 Quick Start
```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 🖥️ Demo Instructions (Judge-Friendly)
### Judge Demo (fast)
- Open app → **Upload / Input** tab → click **✨ Load Judge Demo**
- Switch to **Analyze** tab → summary, risk radar, graph auto-run

### Sample Contracts
- `sample_docs/rental_agreement_low.txt` → short safe case
- `sample_docs/freelance_medium.txt` → medium freelancer case
- `sample_docs/rental_agreement_spicy.txt` → spicy high-risk case

---

## ✨ Features (What judges will see)
- **Dark iOS-minimalist UI**: centered title, glass panels, pill buttons, hover delight
- **Multi-source input**: PDF / DOCX / TXT upload + paste box
- **Plain-language summary**: English, Hinglish, தமிழ், हिंदी
- **Risk flags with severity**: 🔴 High | 🟠 Medium | 🟢 Low + expandable “where/why/quote/fix”
- **Risk radar**: payment / termination / liability / dispute / other (severity-weighted)
- **Contract graph**: Graphviz DOT → compact party/obligation map
- **Clause rewrite + inline diff**: added (green) vs removed (red)
- **Negotiation script**: polite, firm, <5 lines
- **Export report**: one-click dark HTML
- **Judge Demo button**: preloads spicy text & auto-runs analysis
- **Local DB (optional)**: save analyses (SQLite), no signup or cloud needed

---

## 📊 Results (Short / Medium / Big Inputs)

### Short (~1 page)
- **Typical output**: 2–3 flags (e.g., late fee, short notice)
- **Visuals**: Payment & Termination spikes on radar; small, clean graph
- **Why it’s good**: Instant clarity without scrolling walls of text

### Medium (1–2 pages, freelancer)
- **Typical output**: 4–6 flags (e.g., net-90 payment, broad indemnity, IP grab)
- **Rewrite**: Liability/indemnity balanced; inline diff highlights improvements
- **Negotiate**: Ready-to-send script

### Big (5–10 pages)
- **Typical output**: 10+ flags; severity counters pop at the top
- **Visuals**: Clear radar clusters; compact graph shows party obligations
- **Export**: Dark HTML report for offline review

---

## 🛠️ Tech Stack
- **Frontend**: Streamlit (dark theme, minimalist)
- **Backend AI**: Google Gemini 1.5 Flash (`google-generativeai`)
- **Visuals**: Plotly (Radar), Graphviz (Contract graph)
- **Storage**: SQLite (optional local save)
- **Doc ingestion**: PyPDF / python-docx / TXT

---

## 📸 Screenshots 
#low risk contract:
<img width="1464" height="789" alt="image" src="https://github.com/user-attachments/assets/a79c31e1-e5b1-4249-b1a0-fb54de6aeeb6" />
<img width="518" height="233" alt="image" src="https://github.com/user-attachments/assets/0f373ea6-f947-4317-8108-a1189dee7cbd" />





## ⚠️ Disclaimer
ClauseLens is an educational prototype; it does **not** constitute legal advice.
