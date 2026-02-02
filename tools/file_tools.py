import os
from langchain_core.tools import tool

@tool
def create_documentation(file_path: str, content: str) -> str:
    """
    Används för att skapa en textfil.
    Kräver två inputs: 'file_path' (t.ex. rapport.txt) och 'content' (själva texten).
    """
    try:
        # secure the file extension
        if not file_path.endswith(".txt") and not file_path.endswith(".md"):
            file_path += ".txt"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"Filen '{file_path}' har skapats!"
    except Exception as e:
        return f"Ett fel uppstod vid skapandet av filen: {str(e)}"