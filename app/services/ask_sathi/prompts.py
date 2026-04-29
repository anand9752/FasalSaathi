import json

def build_language_prompt(query: str) -> str:
    return f"""
You are a language processing assistant for a farmer support chatbot.

Task:
1. Detect whether the user's query is in Hindi or English.
2. Translate the query into simple English for internal processing.
3. Preserve the agricultural meaning exactly.
4. Return JSON only.

Allowed languages: hindi, english

JSON format:
{{
  "normalizedText": "simple English translation",
  "originalLanguage": "hindi | english"
}}

User query:
{query}
""".strip()

def build_query_parser_prompt(query: str, language: str) -> str:
    return f"""
You structure farmer questions for an agricultural retrieval system.

Extract only what is clearly present in the text. Do not infer missing facts.
Return JSON only with these keys:
{{
  "crop": "",
  "issue": "",
  "symptoms": "",
  "intent": "",
  "language": "{language}"
}}

Field rules:
- crop: crop or plant name if explicitly mentioned
- issue: disease, pest, deficiency, or main problem
- symptoms: visible signs or farmer observations
- intent: what the farmer wants, such as diagnosis, treatment, prevention

Query:
{query}
""".strip()

def format_history(history: list) -> str:
    formatted = []
    for i, item in enumerate(history):
        role = item.get("role", "user").upper()
        content = item.get("content", "")
        formatted.append(f"{i + 1}. {role}: {content}")
    return "\n".join(formatted)

def build_standalone_query_prompt(history: list, query: str) -> str:
    return f"""
You resolve follow-up farmer messages into standalone queries for a retrieval system.

Conversation history:
{format_history(history)}

Latest user message:
{query}

Instructions:
- Rewrite the latest user message into a standalone farmer question
- Preserve crop, issue, timing, and symptom details from the history when needed
- Do not add facts that are not present
- Keep the result concise
- Return JSON only

JSON format:
{{
  "standaloneQuery": "..."
}}
""".strip()

def build_answer_prompt(context: str, question: str, language: str) -> str:
    return f"""
You are an agricultural expert helping farmers.

Context:
{context}

Question:
{question}

Instructions:
- First use the retrieved context wherever it is relevant
- If the context is incomplete, still provide short, safe, general advice based on the farmer's question
- Keep the answer practical and step-by-step
- Use simple language
- Do not invent exact chemical names, doses, or guaranteed diagnoses unless they are clearly supported
- If specific treatment is uncertain, say that field inspection or local expert confirmation is needed
- Respond in {language}
""".strip()

def build_general_advice_prompt(crop: str, issue: str, question: str, language: str) -> str:
    return f"""
You are an agricultural expert helping farmers.

Farmer question:
{question}

Detected crop:
{crop or "unknown"}

Detected issue:
{issue or "unknown"}

Instructions:
- Provide a short, practical answer for the farmer even when retrieved documents are weak or missing
- Give only safe, general first-step advice
- Prefer inspection, isolation, sanitation, irrigation, and local agriculture officer guidance over specific pesticide recommendations
- Do not invent exact chemical names, brand names, dosages, or guaranteed diagnoses
- Keep it concise, useful, and farmer-friendly
- Respond in {language}
""".strip()
