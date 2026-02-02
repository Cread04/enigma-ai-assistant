from langchain_core.tools import tool
from PIL import ImageGrab
import time
import os
import re
import sys

try:
    import pygetwindow as gw
    PYGETWINDOW_AVAILABLE = True
except:
    PYGETWINDOW_AVAILABLE = False
    gw = None

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except:
    TESSERACT_AVAILABLE = False
    pytesseract = None

# Try to find Tesseract in common locations
def find_tesseract():
    """Find Tesseract executable in various locations."""
    possible_paths = [
        # New Tessaract folder (highest priority)
        os.path.join(os.path.dirname(__file__), '..', 'Tessaract', 'tesseract.exe'),
        # Custom installation in project folder
        os.path.join(os.path.dirname(__file__), '..', 'tesseract.exe'),
        os.path.join(os.path.dirname(__file__), '..', 'tesseract', 'tesseract.exe'),
        os.path.join(os.path.dirname(__file__), '..', 'Tesseract-OCR', 'tesseract.exe'),
        # Default Windows installation
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        # Portable or alternative installations
        os.path.join(os.path.expanduser('~'), 'Tesseract-OCR', 'tesseract.exe'),
    ]
    
    for path in possible_paths:
        expanded_path = os.path.abspath(path)
        if os.path.exists(expanded_path):
            print(f"DEBUG: Found Tesseract at: {expanded_path}", flush=True)
            return expanded_path
    
    print(f"DEBUG: Tesseract not found in common locations", flush=True)
    return None

# Set Tesseract path if found
TESSERACT_PATH = find_tesseract()
if TESSERACT_AVAILABLE and pytesseract and TESSERACT_PATH:
    pytesseract.pytesseract.pytesseract_cmd = TESSERACT_PATH
    
    # Also set tessdata directory (same folder as tesseract.exe)
    tesseract_dir = os.path.dirname(TESSERACT_PATH)
    tessdata_path = os.path.join(tesseract_dir, 'tessdata')
    
    # Add Tesseract folder to PATH so pytesseract can find it
    if tesseract_dir not in os.environ['PATH']:
        os.environ['PATH'] = tesseract_dir + os.pathsep + os.environ['PATH']
    
    if os.path.exists(tessdata_path):
        os.environ['TESSDATA_PREFIX'] = tessdata_path
    
    print(f"DEBUG: Tesseract path set to: {TESSERACT_PATH}", flush=True)
    print(f"DEBUG: Tessdata path set to: {tessdata_path}", flush=True)
    print(f"DEBUG: Added Tesseract folder to PATH", flush=True)

@tool
def take_screenshot():
    """
    Tar en skärmdump av hela skärmen, sparar filen och försöker läsa texten.
    Använd detta om användaren ber om att se skärmen.
    """
    try:
        filename = f"screenshot_{int(time.time())}.png"
        screenshot = ImageGrab.grab()
        screenshot.save(filename)
        return f"Skärmdump sparad som {filename}."
    except Exception as e:
        return f"Kunde inte ta skärmdump: {e}"

def get_active_application(debug=False):
    """
    Identifies the currently active/focused application.
    Returns: (app_name, window_title, should_analyze)
    """
    try:
        if not PYGETWINDOW_AVAILABLE:
            return ("unknown", "unknown", True)
        
        # Get the active window
        active_window = gw.getActiveWindow()
        if not active_window:
            return ("unknown", "unknown", True)
        
        window_title = active_window.title.lower()
        
        if debug:
            print(f"DEBUG: Active window: {window_title}", flush=True)
        
        # Identify browser windows
        if any(browser in window_title for browser in ['chrome', 'firefox', 'edge', 'safari', 'opera']):
            return ("browser", window_title, True)
        
        # Identify document apps
        if any(doc in window_title for doc in ['word', 'writer', 'notepad', 'notepad++', 'sublime']):
            return ("document", window_title, True)
        
        # Identify code editors/IDEs
        if any(ide in window_title for ide in ['visual studio code', 'vscode', 'pycharm', 'intellij', 'atom']):
            return ("ide", window_title, False)  # Don't analyze IDE
        
        # Identify file explorer
        if 'explorer' in window_title or 'file browser' in window_title:
            return ("file_explorer", window_title, False)  # Don't analyze desktop/files
        
        # Identify ENIGMA interface
        if 'enigma' in window_title:
            return ("enigma", window_title, False)  # Don't analyze own window
        
        # Default to analyzing
        return ("other", window_title, True)
        
    except Exception as e:
        if debug:
            print(f"DEBUG: Could not get active window: {e}", flush=True)
        return ("unknown", "unknown", True)

def analyze_screen_for_research(debug=False):
    """
    Analyserar skärmen för att detektera research- och anteckningsaktiviteter.
    Returnerar detected activity type och relevant text.
    """
    try:
        # First check if we should analyze the current window
        app_type, window_title, should_analyze = get_active_application(debug)
        
        if not should_analyze:
            if debug:
                print(f"DEBUG: Skipping analysis for {app_type} application", flush=True)
            return {"activity": "idle", "text": "", "confidence": 0, "full_text": ""}
        
        if debug:
            print(f"DEBUG: Analyzing {app_type} application", flush=True)
        # Set up environment for Tesseract if needed
        if TESSERACT_PATH:
            tesseract_dir = os.path.dirname(TESSERACT_PATH)
            tessdata_path = os.path.join(tesseract_dir, 'tessdata')
            if os.path.exists(tessdata_path):
                os.environ['TESSDATA_PREFIX'] = tessdata_path
                if debug:
                    print(f"DEBUG: Set TESSDATA_PREFIX to: {tessdata_path}", flush=True)
        
        # Take screenshot of ACTIVE WINDOW ONLY, not entire screen
        if debug:
            print(f"DEBUG: Taking screenshot of active window...", flush=True)
        
        try:
            if PYGETWINDOW_AVAILABLE:
                active_window = gw.getActiveWindow()
                if active_window and active_window.isActive:
                    # Capture only the active window area
                    left = max(0, active_window.left)
                    top = max(0, active_window.top)
                    right = min(active_window.right, 9999)
                    bottom = min(active_window.bottom, 9999)
                    
                    if debug:
                        print(f"DEBUG: Window bounds: ({left}, {top}, {right}, {bottom})", flush=True)
                    
                    screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
                else:
                    # Fallback to full screen if window not found
                    if debug:
                        print(f"DEBUG: Active window not found, using full screen", flush=True)
                    screenshot = ImageGrab.grab()
            else:
                # Fallback to full screen if pygetwindow not available
                if debug:
                    print(f"DEBUG: pygetwindow not available, using full screen", flush=True)
                screenshot = ImageGrab.grab()
        except Exception as e:
            if debug:
                print(f"DEBUG: Window capture error: {e}, falling back to full screen", flush=True)
            screenshot = ImageGrab.grab()
        
        # Försök att läsa text från skärmen med OCR
        screen_text = ""
        if TESSERACT_AVAILABLE and pytesseract:
            try:
                if debug:
                    print(f"DEBUG: Running OCR with pytesseract...", flush=True)
                # Try Swedish first, fallback to English
                try:
                    screen_text = pytesseract.image_to_string(screenshot, lang='swe')
                except:
                    if debug:
                        print(f"DEBUG: Swedish OCR failed, trying English...", flush=True)
                    screen_text = pytesseract.image_to_string(screenshot)
                
                if debug:
                    print(f"DEBUG: OCR extracted {len(screen_text)} characters", flush=True)
            except Exception as ocr_error:
                if debug:
                    print(f"DEBUG: OCR error: {ocr_error}", flush=True)
                return {"activity": "error", "text": f"OCR error: {ocr_error}", "confidence": 0, "full_text": ""}
        else:
            if debug:
                print(f"DEBUG: Tesseract not available (TESSERACT_AVAILABLE={TESSERACT_AVAILABLE})", flush=True)
            return {"activity": "unknown", "text": "Tesseract not configured", "confidence": 0, "full_text": ""}
        
        if not screen_text or len(screen_text.strip()) < 20:
            if debug:
                print(f"DEBUG: Not enough text detected (length: {len(screen_text)})", flush=True)
            return {"activity": "idle", "text": "", "confidence": 0, "full_text": screen_text}
        
        # Analysera texten för att detektera aktiviteter
        text_lower = screen_text.lower()
        
        # Check if content is PRIMARILY code (more than 50% looks like Python/code)
        code_lines = sum(1 for line in screen_text.split('\n') if any(kw in line.lower() for kw in ['def ', 'import ', 'class ', 'return ']))
        total_lines = max(1, len(screen_text.split('\n')))
        code_ratio = code_lines / total_lines
        
        if code_ratio > 0.5:
            # This is primarily code
            if debug:
                print(f"DEBUG: Content is {code_ratio*100:.0f}% code, ignoring...", flush=True)
            return {"activity": "idle", "text": "", "confidence": 0, "full_text": screen_text}
        
        if debug:
            print(f"DEBUG: Analyzing text for keywords (code ratio: {code_ratio*100:.0f}%)...", flush=True)
        
        # Check for URLs (https://, http://) - indicator of web browsing
        has_url = 'https://' in text_lower or 'http://' in text_lower
        
        # Detektera research-indikatorer
        research_keywords = [
            'wikipedia', 'google', 'search', 'article', 'read',
            'scholar', 'research', 'study', 'learn',
            'definition', 'explanation', 'guide', 'tutorial',
            '.edu', '.org', '.com', 'university', 'college'
        ]
        
        # Detektera anteckningsaktiviteter - more specific
        note_keywords = [
            'anteckningar:', 'notes:', 'todo:', 'checklist',
            '[ ]', '[x]', '- [ ]', '- [x]',
            'deadline:', 'reminder:', 'viktigt:',
            'action item', 'follow up'
        ]
        
        # Detektera skrivande - actual writing activity
        writing_indicators = len(screen_text) > 100 and text_lower.count('\n') > 3
        
        research_score = sum(1 for kw in research_keywords if kw in text_lower)
        note_score = sum(1 for kw in note_keywords if kw in text_lower)
        
        if debug:
            print(f"DEBUG: research_score={research_score}, note_score={note_score}, has_url={has_url}", flush=True)
            print(f"DEBUG: writing_indicators={writing_indicators}, text_length={len(screen_text)}", flush=True)
            # Show first 200 chars of detected text
            preview = screen_text[:200].replace('\n', ' ')
            print(f"DEBUG: Text preview: {preview}...", flush=True)
        
        # Bestäm aktivitetstyp - improved detection
        if note_score > 0:
            # Note-taking has priority
            activity = "note_taking"
            confidence = min((note_score + 1) / (len(note_keywords) * 0.5), 1.0)
        elif has_url or research_score > 0:
            # Web browsing OR research keywords found
            activity = "research"
            # If URL found, boost confidence
            base_score = (research_score + 1) if research_score > 0 else 1
            if has_url:
                base_score += 2  # Boost for actual URL
            confidence = min(base_score / (len(research_keywords) * 0.4), 1.0)
        elif writing_indicators:
            activity = "writing"
            confidence = 0.65
        else:
            activity = "reading"
            confidence = 0.45
        
        if debug:
            print(f"DEBUG: Detected activity={activity}, confidence={confidence}", flush=True)
        
        # Extrahera relevant text (första 300 tecken)
        relevant_text = screen_text[:300].strip()
        
        return {
            "activity": activity,
            "text": relevant_text,
            "confidence": confidence,
            "full_text": screen_text
        }
        
    except Exception as e:
        print(f"DEBUG: Error analyzing screen: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return {"activity": "error", "text": str(e), "confidence": 0, "full_text": ""}

@tool
def describe_screen():
    """
    Beskriver vad som visas på skärmen. Använd när användaren frågar "vad ser du?".

    Returnerar:
    - Webbplats (om du är på en hemsida)
    - Filnamn och mappar (om filhanteraren är öppen)
    - Programnamn (om ett annat program är öppet)
    - Huvudsaklig innehål som OCR kan läsa
    """
    try:
        # Ta skärmdump
        screenshot = ImageGrab.grab()
        
        # Extrahera text
        screen_text = ""
        if TESSERACT_AVAILABLE and pytesseract and TESSERACT_PATH:
            try:
                # Set up environment
                tesseract_dir = os.path.dirname(TESSERACT_PATH)
                tessdata_path = os.path.join(tesseract_dir, 'tessdata')
                if os.path.exists(tessdata_path):
                    os.environ['TESSDATA_PREFIX'] = tessdata_path
                
                # Try to extract text
                try:
                    screen_text = pytesseract.image_to_string(screenshot, lang='swe')
                except:
                    screen_text = pytesseract.image_to_string(screenshot)
                    
            except Exception as e:
                return f"Kunde inte läsa skärmen: {e}"
        
        if not screen_text or len(screen_text.strip()) < 20:
            return "Skärmen verkar vara tom eller innehåller bara ikoner."
        
        text_lower = screen_text.lower()
        
        # Check for actual browser URLs (must have .com, .org, .se etc in URL context)
        has_http = 'http://' in text_lower or 'https://' in text_lower
        
        # Detektera webbplatser - ONLY if we see actual URLs/browser indicators
        if has_http:
            sites = []
            # Check for specific domain URLs
            if 'wikipedia.org' in text_lower or 'wikipedia.se' in text_lower:
                sites.append("Wikipedia")
            if 'google.com' in text_lower or 'google.se' in text_lower or 'search?q=' in text_lower:
                sites.append("Google")
            if '.edu' in text_lower:
                sites.append("En universitet/utbildningswebbplats")
            if 'github.com' in text_lower:
                sites.append("GitHub")
            if 'youtube' in text_lower:
                sites.append("YouTube")
            if 'twitter' in text_lower or 'x.com' in text_lower:
                sites.append("Twitter/X")
            if 'reddit' in text_lower:
                sites.append("Reddit")
            if 'stackoverflow' in text_lower:
                sites.append("Stack Overflow")
            
            if sites:
                return f"Du är på: {', '.join(sites)}"
            else:
                # URL visible but can't identify specific site
                return "Du är på en webbplats. Jag kan se en URL men kan inte identifiera vilken sajt."
        
        # Detektera Windows Explorer
        if any(pattern in text_lower for pattern in ['papperskorg', 'mina dokument', 'downloads', 'filhanterare', 'explorer']):
            # Extrahera filnamn
            words = screen_text.split()
            files = [w for w in words if '.' in w and len(w) < 50][:3]
            if files:
                return f"Du har Windows Utforskaren öppen. Jag ser filer som: {', '.join(files)}"
            return "Du har Windows Utforskaren öppen med mappar och filer."
        
        # Detektera andra program
        if 'visual studio code' in text_lower or 'enigma interface' in text_lower:
            return "Du har ENIGMA-gränssnittet eller en kodeditor öppen."
        
        if 'word' in text_lower or 'excel' in text_lower or 'powerpoint' in text_lower:
            return "Du har ett Microsoft Office-program öppet."
        
        # Generisk beskrivning
        preview = screen_text[:200].replace('\n', ' ').strip()
        if len(preview) > 150:
            preview = preview[:150] + "..."
        
        return f"Jag ser: {preview}"
        
    except Exception as e:
        return f"Kunde inte analysera skärmen: {str(e)}"