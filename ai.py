import json, re
import google.generativeai as genai

API_KEY = "AIzaSyAsFyzwaqObulwBHaE2RLU0Wru9oaeM-10"

if not API_KEY:
    raise RuntimeError("Gemini API key missing.")

genai.configure(api_key=API_KEY)
MODEL_NAME = "gemini-1.5-flash"

def _ensure_model():
    return genai.GenerativeModel(MODEL_NAME)

def generate_json(system_prompt: str, user_prompt: str):
    model = _ensure_model()
    rsp = model.generate_content([system_prompt, user_prompt])
    text = rsp.text or ""
    try:
        match = re.search(r'\{[\s\S]*\}|\[[\s\S]*\]', text)
        if match:
            return json.loads(match.group(0))
    except Exception:
        pass
    try:
        return json.loads(text)
    except Exception:
        return {"_raw": text}

def generate_text(system_prompt: str, user_prompt: str):
    model = _ensure_model()
    rsp = model.generate_content([system_prompt, user_prompt])
    return rsp.text or ""

def extract_sections(contract_text: str):
    from prompts import EXTRACTION_SYSTEM
    user = f"Contract Text:\n\n{contract_text}\n\nReturn JSON."
    return generate_json(EXTRACTION_SYSTEM, user)

def risk_flags(sections_json: dict, persona: str):
    from prompts import RISK_SYSTEM
    import json as _json
    user = f"Persona: {persona}\nSections JSON:\n{_json.dumps(sections_json, ensure_ascii=False)}"
    res = generate_json(RISK_SYSTEM, user)
    if isinstance(res, dict):
        res = res.get("flags", [])
    if not isinstance(res, list):
        res = []
    for f in res:
        sev = str(f.get("severity","low")).lower()
        if sev not in ("low","medium","high"):
            f["severity"] = "low"
    return res

def summarize(sections_json: dict, persona: str, lang: str):
    from prompts import SUMMARY_SYSTEM
    import json as _json
    sys = SUMMARY_SYSTEM.format(persona=persona, lang=lang)
    user = f"Sections JSON:\n{_json.dumps(sections_json, ensure_ascii=False)}"
    return generate_text(sys, user)

def rewrite_clause(clause_text: str, persona: str):
    from prompts import REWRITE_SYSTEM
    sys = REWRITE_SYSTEM.format(persona=persona)
    user = f"Original Clause:\n{clause_text}\n\nReturn JSON."
    return generate_json(sys, user)

def negotiation_script(persona: str, improved_clause: str):
    from prompts import NEGOTIATE_SYSTEM
    user = f"Persona: {persona}\nSafer Clause:\n{improved_clause}"
    return generate_text(NEGOTIATE_SYSTEM, user)

def graphviz_dot(sections_json: dict):
    from prompts import GRAPH_SYSTEM
    import json as _json
    user = f"Sections JSON:\n{_json.dumps(sections_json, ensure_ascii=False)}\nReturn DOT only."
    return generate_text(GRAPH_SYSTEM, user)
