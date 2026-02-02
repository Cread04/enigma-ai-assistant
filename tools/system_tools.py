from langchain_core.tools import tool
import os
import subprocess

@tool
def open_application(app_name: str):
    """
    Öppnar ett program på datorn.
    Exempel: "chrome", "spotify", "notepad", "calculator".
    """
    app_map = {
        "kalkylator": "calc",
        "miniräknare": "calc",
        "anteckningar": "notepad",
        "utforskaren": "explorer",
        "chrome": "chrome",
        "spotify": "spotify",
        "word": "winword",
        "excel": "excel",
        "powerpoint": "powerpnt"
    }
    
    target = app_map.get(app_name.lower(), app_name)
    
    try:
        print(f"DEBUG: Försöker starta {target}...", flush=True)
        os.system(f"start {target}")
        return f"Öppnar {target}..."
    except Exception as e:
        return f"Kunde inte öppna {app_name}. Fel: {e}"