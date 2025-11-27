# ===================== search_ai.py (FINAL + SECURE) =====================
import os
import json
import requests
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERPER_KEY = os.getenv("SERPER_KEY")

if not GEMINI_API_KEY or not SERPER_KEY:
    raise Exception("❌ API Keys missing — Set GEMINI_API_KEY & SERPER_KEY in .env")

genai.configure(api_key=GEMINI_API_KEY)


def ai_web_search(query):
    """Google Search → Gemini Answer Engine (Strongly Improved Accuracy)"""

    try:
        response = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": SERPER_KEY, "Content-Type": "application/json"},
            json={"q": query}
        )
        data = response.json()

        print("\n🔍 SEARCH RAW:\n", json.dumps(data, indent=2), "\n")

        results = []

        # Organic search results
        for item in data.get("organic", [])[:6]:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            results.append(f"{title}: {snippet}")

        # AnswerBox / Knowledge Graph extraction (HIGH PRIORITY)
        if "answerBox" in data and "answer" in data["answerBox"]:
            results.insert(0, "ANSWER: " + data["answerBox"]["answer"])
        
        if "knowledgeGraph" in data and "title" in data["knowledgeGraph"]:
            kg = data["knowledgeGraph"]
            results.insert(0, f"{kg.get('title','')} — {kg.get('description','')}")

        info = "\n".join(results).strip()

        if len(info) < 25:
            return "No clear answer found. Try rephrasing."

        prompt = f"""
        You must return answer EXACTLY in this format:

        🟢 Answer: <one line direct answer>
        📄 Summary: 3–5 lines explanation

        USER QUESTION → {query}

        Web Data:
        {info}
        """

        model = genai.GenerativeModel("models/gemini-2.5-flash")
        output = model.generate_content(prompt)

        return output.text.strip()

    except Exception as e:
        return f"❌ Web Search Failed → {e}"
