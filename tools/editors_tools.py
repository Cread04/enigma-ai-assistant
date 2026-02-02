from langchain_core.tools import tool
import pyautogui
import time
import pyperclip
from langchain_ollama import ChatOllama
from config import MODEL_NAME

@tool
def improve_active_document(instruction: str):
    """
    Läser text från aktiva fönstret, förbättrar enligt instruktion, och klistrar in igen.
    """
    try:
        print(f"DEBUG: improve_active_document startar med instruktion: {instruction}", flush=True)
        
        # Mark everything
        pyautogui.hotkey('ctrl', 'a') 
        time.sleep(0.15)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.15)
        
        # Get the text from clipboard
        original_text = pyperclip.paste()
        print(f"DEBUG: Läste text ({len(original_text)} tecken)", flush=True)
        
        if not original_text or not original_text.strip():
            print("DEBUG: Ingen text hittades", flush=True)
            return "Kunde inte hitta text i det aktiva fönstret."

        # Improve with AI
        llm = ChatOllama(model=MODEL_NAME, temperature=0.1)
        
        prompt = f"""Du är en expertkorrekturläsare som förbättrar text.

INSTRUKTION FRÅN ANVÄNDAREN: {instruction}

KRITISKA REGLER:
1. Förbättra texten enligt instruktionen
2. Behåll ALLT innehåll - ta aldrig bort meningar
3. Behåll författarens röst och ton
4. Rätta stavfel, grammatik och struktur
5. Gör texten lättare att läsa
6. Returnera ENDAST den förbättrade texten. INGENTING ANNAT.

ORIGINALTEXT:
{original_text}

FÖRBÄTTRAD TEXT:"""
        
        response = llm.invoke(prompt)
        fixed_text = response.content.strip()
        
        print(f"DEBUG: LLM returnerade {len(fixed_text)} tecken", flush=True)
        
        if not fixed_text:
            return "AI kunde inte bearbeta texten."

        # Paste the new text
        pyperclip.copy(fixed_text)
        time.sleep(0.15)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.15)
        
        print(f"DEBUG: Texten uppdaterades framgångsrikt", flush=True)
        return f"Texten uppdaterades ({len(fixed_text)} tecken)"
        
    except Exception as e:
        print(f"DEBUG: Fel i improve_active_document: {e}", flush=True)
        return f"Fel: {str(e)}"

# Placeholder-funktions
@tool
def read_active_document(): 
    """Läser texten i det aktiva fönstret."""
    return "Funktion ej klar ännu."

@tool
def write_to_document(text: str): 
    """Skriver text till det aktiva fönstret."""
    return "Funktion ej klar ännu."