import customtkinter as ctk
import threading
import asyncio
import speech_recognition as sr
from Voice import speak, listen, generate_speech
from agent import get_agent

# Inställningar för utseende
ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("dark-blue")

class EnigmaApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Config the main window
        self.title("PROJECT ENIGMA")
        self.geometry("600x500")
        
        
        # the brain initalization of the agent
        try:
            self.agent_executor = get_agent()
            self.agent_ready = True
        except Exception as e:
            self.agent_ready = False
            print(f"Kunde inte ladda agenten: {e}")

        
        # create the ui
        self.setup_ui()
        
        # Start the listening automatically after 1 second
        self.after(1000, self.auto_start)

    def setup_ui(self):
        # title label
        self.label_title = ctk.CTkLabel(self, text="ENIGMA AI SYSTEM", font=("Arial", 20, "bold"))
        self.label_title.pack(pady=20)

        # text area for chat log
        self.chat_display = ctk.CTkTextbox(self, width=500, height=300, font=("Consolas", 14))
        self.chat_display.pack(pady=10)
        
        
        self.chat_display.insert("1.0", "System: Startar upp sensorer...\n")
        
        self.chat_display.configure(state="disabled")

        # Status         
        self.status_label.pack(pady=5)

        # paus button
        self.btn_listen = ctk.CTkButton(
            self, 
            text="PAUSA ENIGMA", 
            command=self.toggle_listening, 
            height=50, 
            width=200,
            fg_color="red", 
            hover_color="darkred"
        )
        self.btn_listen.pack(pady=20)

    def log_message(self, sender, message):
        """Skriver till loggen"""
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"\n{sender}: {message}\n")
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")

    def auto_start(self):
        """Funktion som körs automatiskt vid start"""
        speak("Enigma är redo. Jag lyssnar.")
        self.start_listening()

    def toggle_listening(self):
        """Knappens funktion: Växla mellan PÅ och AV"""
        if getattr(self, "listening", False):
            # Stäng av
            self.listening = False
            self.status_label.configure(text="Pausad (Lyssnar ej)", text_color="orange")
            self.btn_listen.configure(text="AKTIVERA ENIGMA", fg_color="#1f538d", hover_color="#14375e")
            self.log_message("System", "Mikrofon avstängd.")
        else:
            
            self.start_listening()

    def start_listening(self):
        """Startar tråden"""
        self.listening = True
        self.btn_listen.configure(text="PAUSA ENIGMA", fg_color="red", hover_color="darkred")
        self.status_label.configure(text="Startar...", text_color="yellow")
        
        
        # start the loop in a background thread
        threading.Thread(target=self.process_voice_command_loop).start()

    def process_voice_command_loop(self):
        """Den eviga loopen som lyssnar efter 'Enigma'"""
        r = sr.Recognizer()
        r.pause_threshold = 1.0
        
        try:
            with sr.Microphone() as source:
                self.status_label.configure(text="Kalibrerar...", text_color="yellow")
                r.adjust_for_ambient_noise(source, duration=1.0)
                
                
                # here is the loop that runs as long as self.listening is True
                while self.listening:
                    self.status_label.configure(text="Väntar på 'Enigma'...", text_color="#00ff00")
                    
                   
                    # listen (without timeout, so it listens forever until sound is heard)
                    user_text = listen(recognizer=r, source=source, timeout=None)
                    
                    if user_text:
                        # WAKE WORD logic
                        text_lower = user_text.lower()
                        
                        # Check for my wake word "enigma"
                        if "enigma" in text_lower:
                            self.status_label.configure(text="Bearbetar...", text_color="cyan")
                            self.log_message("Hörde", user_text)
                            
                            # remove the wake word from the text
                            clean_text = text_lower.replace("enigma", "").strip()
                            
                            # if i only say engima take it as a hello
                            if not clean_text:
                                clean_text = "Hej, är du där?"

                            if self.agent_ready:
                                try:
                                    # send to brain
                                    response = self.agent_executor.invoke({"input": user_text}) # Skicka originaltexten för kontext
                                    ai_reply = response.get('output')

                                    if not ai_reply or not str(ai_reply).strip():
                                        ai_reply = "." # silence if no answear
                                    else:
                                        self.log_message("Enigma", ai_reply)
                                        # speak (this pauses listening temporarily which is good so it doesn't hear itself)
                                        asyncio.run(generate_speech(ai_reply))
                                    
                                except Exception as e:
                                    self.log_message("System", f"Fel: {e}")
                            
                        else:
                            # Debug: show in the terminal wwhat it ignored
                            print(f"Ignorerade: '{user_text}' (Inget vakna-ord)", flush=True)

        except Exception as e:
            print(f"Loop error: {e}")
            self.listening = False
            self.btn_listen.configure(text="Starta om (Fel)", state="normal")

if __name__ == "__main__":
    app = EnigmaApp()
    app.mainloop()

    # "E:\AI kod\.venv\Scripts\python.exe" "E:\AI kod\Ai del 2\AI-projekt\Enigma.py"