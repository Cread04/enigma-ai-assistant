#!/usr/bin/env python
"""
Screen Monitoring Diagnostic Script
Tests if Tesseract is found and if screen analysis works
"""

import sys
import os
import time

print("\n" + "="*60)
print("ENIGMA SCREEN MONITORING DIAGNOSTIC")
print("="*60 + "\n")

# Check Tesseract
print("1. CHECKING TESSERACT OCR")
print("-" * 60)

try:
    import pytesseract
    print("✓ pytesseract imported successfully")
except ImportError as e:
    print(f"✗ pytesseract import failed: {e}")
    sys.exit(1)

# Try to find Tesseract
possible_paths = [
    os.path.join(os.path.dirname(__file__), 'tesseract', 'tesseract.exe'),
    os.path.join(os.path.dirname(__file__), 'Tesseract-OCR', 'tesseract.exe'),
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    os.path.join(os.path.expanduser('~'), 'Tesseract-OCR', 'tesseract.exe'),
]

tesseract_found = False
for path in possible_paths:
    if os.path.exists(path):
        print(f"✓ Tesseract found at: {path}")
        pytesseract.pytesseract.pytesseract_cmd = path
        tesseract_found = True
        break

if not tesseract_found:
    print(f"✗ Tesseract not found in:")
    for path in possible_paths:
        print(f"  - {path}")
    print("\n  Install from: https://github.com/UB-Mannheim/tesseract/wiki")

print("\n2. TESTING TESSERACT")
print("-" * 60)

try:
    version = pytesseract.get_tesseract_version()
    print(f"✓ Tesseract version: {version}")
except Exception as e:
    print(f"✗ Tesseract test failed: {e}")
    print("  Make sure Tesseract is installed and accessible")

print("\n3. TESTING SCREEN ANALYSIS")
print("-" * 60)

try:
    from tools.screen_tools import analyze_screen_for_research
    print("✓ Screen analysis module loaded")
    
    print("\nTesting screen capture and OCR (this takes 5-10 seconds)...")
    print("Make sure you have text visible on your screen!")
    print("(If your screen is blank, OCR won't detect anything)\n")
    
    time.sleep(2)
    result = analyze_screen_for_research(debug=True)
    
    print("\n" + "-" * 60)
    print("RESULTS:")
    print(f"  Activity: {result['activity']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Text length: {len(result['full_text'])} characters")
    print(f"  Text preview: {result['text'][:100]}...")
    print("-" * 60)
    
    if result['activity'] == 'unknown':
        print("\n⚠️  NO ACTIVITY DETECTED")
        print("   Make sure you have text on your screen!")
        print("   Try: Open a document with text and run again")
    elif result['activity'] == 'error':
        print(f"\n✗ ERROR: {result['text']}")
    else:
        print(f"\n✓ DETECTED: {result['activity']} (confidence: {result['confidence']:.0%})")

except Exception as e:
    print(f"✗ Screen analysis test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n4. SYSTEM INFO")
print("-" * 60)
print(f"Python: {sys.version}")
print(f"Platform: {sys.platform}")
print(f"Working directory: {os.getcwd()}")

print("\n" + "="*60)
print("DIAGNOSTIC COMPLETE")
print("="*60 + "\n")

print("NEXT STEPS:")
if not tesseract_found:
    print("1. Install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki")
    print("2. Run this diagnostic again")
else:
    print("1. Open EnigmaUI.py")
    print("2. Enable screen monitoring")
    print("3. Open a document with text (or your notes)")
    print("4. Enigma should detect your activity within 15 seconds")

print("\nIf still not working:")
print("- Check the debug output above")
print("- Make sure Tesseract is installed correctly")
print("- Ensure you have readable text on your screen")
print("- Try running this diagnostic again with text visible\n")
