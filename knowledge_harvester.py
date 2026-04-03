import os
import requests
from bs4 import BeautifulSoup
from database import SessionLocal, KnowledgeFact
from google import genai
from google.genai import types

def search_snippets(query: str) -> str:
    """Uses headless DDG to extract text snippets related to a query."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
    snippets = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        for div in soup.find_all('a', class_='result__snippet')[:5]:
            snippets.append(div.text)
    except Exception as e:
        print(f"Search snippet failed: {e}")
    return "\n".join(snippets)

def harvest_knowledge():
    """Runs a nightly crawl to fetch critical financial and legal constraints for contractors."""
    print("🧠 Autonomous Knowledge Harvester Activating...")
    db = SessionLocal()
    
    # 1. Clear old facts to ensure we only hold the freshest weekly data
    db.query(KnowledgeFact).delete()
    db.commit()

    questions = [
        "What is the current minimum wage per day for unskilled labor in Jammu and Kashmir PWD in 2024?",
        "What is the current GST percentage rate on government civil construction contracts in India?",
        "Is the Zojila Pass currently closed or open for vehicular movement today?"
    ]

    for question in questions:
        try:
            print(f"   [~] Researching: {question}")
            raw_evidence = search_snippets(question)
            
            if not raw_evidence.strip():
                continue
                
            prompt = (
                "You are an AI data extractor. Read the following web search snippets.\n"
                f"Question: {question}\n\nSearch Evidence:\n{raw_evidence}\n\n"
                "Extract the factual answer in exactly ONE concise sentence. If the evidence does not contain a clear answer, reply exactly with 'UNKNOWN'."
            )
            
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                )
            )
            fact_text = response.text.replace("*", "").strip()
            
            if "UNKNOWN" not in fact_text.upper():
                new_fact = KnowledgeFact(fact_text=f"Q: {question}\nA: {fact_text}")
                db.add(new_fact)
                print(f"   [+] Learned Fact: {fact_text}")
        except Exception as e:
            print(f"   [!] Failed to harvest knowledge for '{question}': {e}")

    try:
        db.commit()
        print("✅ Knowledge Harvest Complete. Facts stored in long-term memory.")
    except Exception as e:
        db.rollback()
        print(f"❌ DB Error saving facts: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    harvest_knowledge()
