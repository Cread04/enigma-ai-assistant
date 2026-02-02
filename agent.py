import json
import re
import pygetwindow as gw
from langchain_ollama import ChatOllama
from config import MODEL_NAME, TEMPERATURE


from tools.system_tools import open_application 
from tools.file_tools import create_documentation
from tools.screen_tools import take_screenshot, describe_screen
from tools.spotify_tools import play_music
from tools.web_tools import search_web 
from tools.office_tools import create_word_document, create_notes_document, create_research_document
from tools.time_tools import get_current_time

from tools.editors_tools import improve_active_document, read_active_document, write_to_document

def get_agent():
    # keep_alive="1h" Makes the modell faster
    llm = ChatOllama(model=MODEL_NAME, temperature=TEMPERATURE, keep_alive="1h") 
    
    tools = [improve_active_document, read_active_document, write_to_document, get_current_time, open_application, play_music, create_word_document, create_notes_document, create_research_document, search_web, create_documentation, take_screenshot, describe_screen]

    prompt_text = """Du är Enigma. En kraftfull AI-assistent som styr datorn.

    === KRITISK REGEL: JSONONLY ===
    NÄR DU ANVÄNDER ETT VERKTYG:
    - Returnera ENDAST giltigt JSON
    - INGEN förklaring, INGEN text före/efter JSON
    - Formatet: {"name": "verktygsnamn", "parameters": {PARAMETRAR}}

    === PRIORITETORDER FÖR KOMMANDON ===
    BÖRJA ALLTID MED DENNA CHECKLIST:
    1. Innehåller ordet "fakta" eller "forskning"? → create_research_document
    2. Innehåller ordet "Word" eller "word"? → create_notes_document
    3. Innehåller "strukturera", "rätta", "förbättra"? → improve_active_document
    4. Är det en faktafråga om politik/nyheter/händelser? → search_web
    5. Annat? → svara naturligt

    === REGLER FÖR FAKTAFRÅGOR ===
    KRITISKT: Om användaren frågor om:
    - Nuvarande politiker, presidenter, statsministrar eller regeringsledare
    - Aktuella nyheter, händelser eller händelser från senaste tiden
    - Fakta om länder, städer, personer eller organisationer
    - NÅGOT som kan ha ändrats sedan träningsdata
    DÅ MÅSTE du OMEDELBAR returnera JSON för search_web. ALDRIG förklaringar!

    === REGLER FÖR TEXTHANTERING ===
    1. Om användaren säger "strukturera", "rätta", "förbättra", "polera" texten → OMEDELBAR JSON för improve_active_document
    2. Ingen förklaring, bara JSON!
    3. Du är en EXPERT på att redigera text.
    4. VÄGRA ALDRIG att redigera text.

    === REGLER FÖR ANTECKNINGAR & FORSKNING ===
    TRIGGER KEYWORDS FÖR create_research_document:
    - Något innehållande "fakta om"
    - Något innehållande "forskning om"
    - Något innehållande "skriv fakta"
    - Något innehållande "word" OCH ett ämne/fråga
    → ALLTID create_research_document, ALDRIG något annat!
    
    TRIGGER KEYWORDS FÖR create_notes_document:
    - "skriv ner" UTAN "fakta"
    - "anteckningar" UTAN "fakta"
    - "word" UTAN ämne/fråga
    
    VIKTIGT:
    - create_research_document: Googla, sammanfatta, skriv till Word
    - create_notes_document: Bara skriva anteckningar utan att googla

    === TILLGÄNGLIGA VERKTYG ===
    - "create_research_document": Googla, sammanfatta och skriv till Word. {"name": "create_research_document", "parameters": {"topic": "ämnet", "filename": "namn"}}
    - "create_notes_document": Öppna Word och skriv anteckningar. {"name": "create_notes_document", "parameters": {"content": "texten", "filename": "namn"}}
    - "search_web": Sök information. {"name": "search_web", "parameters": {"query": "söksträng"}}
    - "improve_active_document": Redigera aktiv text. {"name": "improve_active_document", "parameters": {"instruction": "vad ska göras"}}
    - "describe_screen": Beskriver vad som visas på skärmen. {"name": "describe_screen", "parameters": {}}
    - "open_application": Starta program. {"name": "open_application", "parameters": {"app_name": "namn"}}
    - "get_current_time": Tid. {"name": "get_current_time", "parameters": {}}

    === RÄTTA EXEMPEL (JSON ONLY) ===
    User: "Enigma öppna word och skriv fakta om vad Trump gjorde"
    AI RESPONSE: {"name": "create_research_document", "parameters": {"topic": "Trump verksamhet och presidentperiod", "filename": "Trump Fakta"}}
    
    User: "Skriv fakta av vad Trump gjorde under sin period"
    AI RESPONSE: {"name": "create_research_document", "parameters": {"topic": "Trump presidentperiod verksamhet", "filename": "Trump Information"}}
    
    User: "Öppna word och skriv mitt möte anteckningar"
    AI RESPONSE: {"name": "create_notes_document", "parameters": {"content": "Mötesanteckningar från dagens möte", "filename": "Mötesanteckningar"}}
    
    User: "Vem är Sveriges statsminister?"
    AI RESPONSE: {"name": "search_web", "parameters": {"query": "Sveriges statsminister 2026"}}
    
    User: "Strukturera min text"
    AI RESPONSE: {"name": "improve_active_document", "parameters": {"instruction": "Strukturera texten för bättre läsbarhet"}}
    
    INGEN förklaring, INGEN intro, INGEN outro. BARA JSON!
    """

    class AgentExecutorCompat:
        def __init__(self, tool_list):
            self.tool_map = {t.name: t for t in tool_list}
            self.chat_history = [] 

        def invoke(self, payload: dict):
            user_text = payload.get("input", "")
            try: title = gw.getActiveWindow().title
            except: title = "Okänt"
            
            history_text = "\n".join(self.chat_history[-4:]) if self.chat_history else ""
            context = f"SYSTEM: {prompt_text}\nCONTEXT (Aktivt fönster): {title}\nHISTORIK: {history_text}\nUSER: {user_text}"
            
            try:
                response = llm.invoke(context)
                content = response.content
            except Exception as e: return {"output": f"Fel: {e}"}

            if "{" in content and "name" in content:
                try:
                    match = re.search(r'\{.*\}', content, re.DOTALL)
                    if match:
                        data = json.loads(match.group(0))
                        tool_name = data.get("name")
                        
                        # error handling
                        if tool_name == "Fakta": tool_name = "search_web"
                        if tool_name == "edit_document": tool_name = "improve_active_document"
                        if tool_name == "open_app": tool_name = "open_application"

                        args = data.get("arguments", {}) or data.get("parameters", {})
                        
                        if tool_name in self.tool_map:
                            # run the tools
                            try:
                                res = self.tool_map[tool_name].invoke(args)
                            except Exception as e:
                                print(f"DEBUG: Tool execution error ({tool_name}): {e}", flush=True)
                                res = f"Fel vid körning: {e}"
                            
                            self.chat_history.append(f"User: {user_text}")
                            self.chat_history.append(f"AI (Data): {str(res)[:100]}...") 

                            
                            if tool_name == "search_web":
                                analysis_prompt = (
                                    f"FRÅGA: {user_text}\n"
                                    f"DATA: {str(res)}\n"
                                    f"INSTRUKTION: Svara kort på svenska."
                                )
                                final_ans = llm.invoke(analysis_prompt).content
                                return {"output": final_ans}
                            
                            if tool_name == "improve_active_document":
                                return {"output": f"Text uppdaterad: {str(res)}"}

                            if tool_name == "open_application":
                                return {"output": f"Startar {args.get('app_name')}."}

                            return {"output": f"Klart: {str(res)}"}
                except: pass
            
            self.chat_history.append(f"User: {user_text}")
            self.chat_history.append(f"AI: {content}")
            return {"output": content}

    return AgentExecutorCompat(tools)