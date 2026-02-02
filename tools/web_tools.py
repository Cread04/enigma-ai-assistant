import warnings

warnings.filterwarnings("ignore") 

from langchain_core.tools import tool
from ddgs import DDGS
import wikipedia


try: 
    wikipedia.set_lang("sv")
except: 
    pass

@tool
def search_web(query: str):
    """
    Söker på nätet efter information.
    Använder DuckDuckGo för snabba, uppdaterade resultat.
    """
    
    clean_query = query.strip()
    if not clean_query:
        return "Ingen sökterm angiven."

    print(f"DEBUG: Startar sökning efter '{clean_query}'...", flush=True)

    # PRIMARY: DuckDuckGo (most reliable and updated)
    try:
        print("DEBUG: Testar DuckDuckGo...", flush=True)
        ddgs = DDGS()
        results = ddgs.text(clean_query, max_results=5)
        
        if results:
            combined_results = ""
            for r in results:
                title = r.get('title', '')
                body = r.get('body', '')
                if title and body:
                    combined_results += f"Källa: {title}\nInfo: {body}\n\n"
            
            if combined_results:
                print(f"DEBUG: DDG hittade {len(results)} resultat.", flush=True)
                return combined_results
    except Exception as e:
        print(f"DEBUG: DuckDuckGo misslyckades ({e})", flush=True)

    # FALLBACK: Wikipedia
    try:
        print("DEBUG: Testar Wikipedia...", flush=True)
        wiki = wikipedia.summary(clean_query, sentences=15, auto_suggest=True)
        if wiki: 
            print("DEBUG: Wikipedia hittade info.", flush=True)
            return f"Wikipedia: {wiki}"
    except Exception as e:
        print(f"DEBUG: Wikipedia hittade inget ({e}).", flush=True)

    print("DEBUG: Inga resultat hittades.", flush=True)
    return "Kunde inte hitta information. Försök med en annan sökterm."