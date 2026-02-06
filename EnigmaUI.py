import customtkinter as ctk
import threading
import math
import time
from PIL import Image, ImageTk
from agent import get_agent
from Voice import listen, speak

# The look
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class EnigmaUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # New window
        self.title("ENIGMA INTERFACE")
        self.geometry("500x750")
        self.resizable(False, False)
        
        # Varibles
        self.agent = None
        self.is_processing = False
        self.stop_listening = False
        self.screen_monitoring = False
        self.circle_radius = 60
        self.angle = 0
        self.wake_word = "enigma" #this is the word its listening for
        self.last_activity = None
        self.last_help_offered = None  # Track when we last offered help
        self.activity_check_interval = 15  # seconds
        self.help_offer_cooldown = 60  # Don't repeat same help within 60 seconds

        # --- LAYOUT ---
        
        # Title Header
        self.header = ctk.CTkLabel(self, text="SYSTEM INITIALIZED", font=("Consolas", 18, "bold"), text_color="#00FFFF")
        self.header.pack(pady=(30, 10))

        # Reaktor 
        self.canvas_size = 250
        self.canvas = ctk.CTkCanvas(self, width=self.canvas_size, height=self.canvas_size, bg="#1a1a1a", highlightthickness=0)
        self.canvas.pack(pady=10)

        # Terminal window
        self.chat_display = ctk.CTkTextbox(self, width=450, height=300, font=("Consolas", 12), text_color="#DDDDDD", fg_color="#0f0f0f")
        self.chat_display.pack(pady=10)
        self.chat_display.configure(state="disabled")

       
        # Input frame
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.pack(fill="x", padx=20, pady=10)

        self.entry = ctk.CTkEntry(self.input_frame, placeholder_text="Skriv manuellt kommando...", font=("Consolas", 14), height=40, border_color="#00FFFF")
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry.bind("<Return>", self.on_enter_pressed)

        self.send_btn = ctk.CTkButton(self.input_frame, text="EXECUTE", command=self.send_text, width=80, fg_color="#006688", hover_color="#0088AA")
        self.send_btn.pack(side="right")

        # Screen monitoring button
        self.monitor_btn = ctk.CTkButton(self, text="ENABLE SCREEN MONITOR", command=self.toggle_screen_monitoring, height=35, fg_color="#1f538d", hover_color="#0d1f2d")
        self.monitor_btn.pack(pady=10)

        # Start the system
        self.animate_circle() 
        threading.Thread(target=self.system_boot, daemon=True).start()

    def system_boot(self):
        """Simulerar uppstart"""
        steps = [
            "Loading Core Modules...",
            "Connecting to Neural Network (Llama 3.1)...",
            "Initializing Audio Sensors...",
            f"Waiting for Wake Word: '{self.wake_word.upper()}'...",
            "System Online."
        ]
        
        for step in steps:
            time.sleep(0.5)
            self.log_to_chat("SYSTEM", step)
        
        self.agent = get_agent()
        self.log_to_chat("SYSTEM", "Ready.")
        
        threading.Thread(target=self.listen_loop, daemon=True).start()

    def animate_circle(self):
        """reaktor-effekt"""
        try:
            self.canvas.delete("all")
            center = self.canvas_size / 2
            
            pulse = math.sin(self.angle) * 10 
            r = self.circle_radius + pulse
            
            if self.is_processing:
                core_color = "#FF3300" 
                glow_color = "#882200"
            else:
                core_color = "#00FFFF" 
                glow_color = "#004466"

            self.canvas.create_oval(center-r-15, center-r-15, center+r+15, center+r+15, outline=glow_color, width=2)
            self.canvas.create_oval(center-r, center-r, center+r, center+r, fill=core_color, outline="#FFFFFF", width=2)
            
            self.angle += 0.1
            self.after(30, self.animate_circle)
        except: pass

    def log_to_chat(self, sender, message):
        """Skriver till terminalen"""
        self.chat_display.configure(state="normal")
        if sender == "SYSTEM":
            self.chat_display.insert("end", f"> {message}\n")
        elif sender == "ENIGMA":
            self.chat_display.insert("end", f"\n[ENIGMA]: {message}\n")
        elif sender == "IGNORED": # To show that the microphone heard but ignored
            self.chat_display.insert("end", f"> (Hörde men ignorerade): {message}\n")
        else:
            self.chat_display.insert("end", f"\n[USER]: {message}\n")
            
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")

    def process_ai(self, user_text):
        if not self.agent: return

        self.is_processing = True
        self.header.configure(text="PROCESSING DATA...", text_color="#FF3300")
        
        try:
            response = self.agent.invoke({"input": user_text})
            ai_text = response.get("output", "Error.")
            
            self.log_to_chat("ENIGMA", ai_text)
            self.header.configure(text="SYSTEM ONLINE", text_color="#00FFFF")
            
            threading.Thread(target=speak, args=(ai_text,), daemon=True).start()
            
        except Exception as e:
            self.log_to_chat("SYSTEM", f"Critical Failure: {e}")
        
        self.is_processing = False

    def on_enter_pressed(self, event):
        self.send_text()

    def send_text(self):
        text = self.entry.get()
        if not text: return
        self.entry.delete(0, "end")
        
        # IF your using the write function you dont need to write engima 
        self.log_to_chat("USER", text)
        threading.Thread(target=self.process_ai, args=(text,), daemon=True).start()

    def listen_loop(self):
        """Lyssnar alltid men reagerar BARA på 'Enigma'"""
        while not self.stop_listening:
            if not self.is_processing and self.agent:
                try:
                    text = listen()
                    if text:
                        
                        if self.wake_word in text.lower():
                            self.log_to_chat("USER", f"(Röst) {text}")
                            self.process_ai(text)
                        else:
                            pass
                except: pass
            time.sleep(0.5)

    def toggle_screen_monitoring(self):
        """Toggle screen monitoring on/off"""
        self.screen_monitoring = not self.screen_monitoring
        if self.screen_monitoring:
            self.monitor_btn.configure(text="DISABLE SCREEN MONITOR", fg_color="#8B0000", hover_color="#5C0000")
            self.log_to_chat("SYSTEM", "Screen monitoring ACTIVE.")
            threading.Thread(target=self.screen_monitor_loop, daemon=True).start()
        else:
            self.monitor_btn.configure(text="ENABLE SCREEN MONITOR", fg_color="#1f538d", hover_color="#0d1f2d")
            self.log_to_chat("SYSTEM", "Screen monitoring stopped.")

    def screen_monitor_loop(self):
        """Background loop that monitors screen for research/note-taking"""
        from tools.screen_tools import analyze_screen_for_research
        
        print("DEBUG: Screen monitoring loop started", flush=True)
        check_count = 0
        
        while self.screen_monitoring:
            if not self.is_processing and self.agent:
                try:
                    check_count += 1
                    # Only debug every 5th check to reduce spam
                    debug_mode = (check_count % 5 == 0)
                    
                    if debug_mode:
                        print(f"\nDEBUG: Screen check #{check_count}...", flush=True)
                    
                    result = analyze_screen_for_research(debug=debug_mode)
                    
                    confidence = result.get("confidence", 0)
                    activity = result.get("activity", "unknown")
                    
                    if debug_mode:
                        print(f"DEBUG: Result - activity={activity}, confidence={confidence:.2f}", flush=True)
                    
                    # Higher threshold (0.65) to avoid false positives
                    if confidence > 0.65:
                        current_time = time.time()
                        
                        # Only offer help if:
                        # 1. Activity changed, OR
                        # 2. Enough time passed since last help offer
                        if (activity != self.last_activity or 
                            self.last_help_offered is None or 
                            (current_time - self.last_help_offered) > self.help_offer_cooldown):
                            
                            # Give help based on detected activity
                            if activity == "research":
                                message = "Jag ser att du forskar på en hemsida. Vill du att jag skriver ner eller organiserar information om det du läser?"
                                self.log_to_chat("ENIGMA", message)
                                threading.Thread(target=speak, args=(message,), daemon=True).start()
                            elif activity == "note_taking":
                                message = "Jag ser att du skriver anteckningar. Kan jag organisera eller förbättra dem?"
                                self.log_to_chat("ENIGMA", message)
                                threading.Thread(target=speak, args=(message,), daemon=True).start()
                            elif activity == "writing":
                                message = "Du skriver något. Behöver du hjälp med stavning, struktur eller innehållet?"
                                self.log_to_chat("ENIGMA", message)
                                threading.Thread(target=speak, args=(message,), daemon=True).start()
                            
                            # Logg detected words (first 100 characters)
                            text_preview = result.get("text", "")[:100]
                            if text_preview:
                                print(f"DEBUG: Detected {activity}: {text_preview}...", flush=True)
                            
                            self.last_activity = activity
                            self.last_help_offered = current_time
                        
                        time.sleep(self.activity_check_interval)
                    else:
                        if debug_mode:
                            print(f"DEBUG: Confidence {confidence:.2f} below threshold (0.65), skipping...", flush=True)
                        time.sleep(3)  # Check every 3 seconds when no activity
                        
                except Exception as e:
                    print(f"DEBUG: Screen monitoring error: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
                    time.sleep(5)
            else:
                time.sleep(1)  # Reduced from 2 to be more responsive

if __name__ == "__main__":
    app = EnigmaUI()
    app.mainloop()

    # "E:\AI kod\.venv\Scripts\python.exe" "E:\AI kod\Ai del 2\AI-projekt\EnigmaUI.py"
