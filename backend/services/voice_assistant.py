import speech_recognition as sr
import pyttsx3
import threading
import queue
import time
from typing import Optional

try:
    from .system_control import SystemController
    from .intent_router import IntentRouter
    from .voice_browser_control import VoiceBrowserController
except ImportError:
    
    from system_control import SystemController
    from intent_router import IntentRouter
    from voice_browser_control import VoiceBrowserController

class VoiceAssistant:
    
    
    def __init__(self, silent_mode=False):
        
        self.silent_mode = silent_mode
        
        
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)  
            self.tts_engine.setProperty('volume', 0.8)  
            self.tts_enabled = True
        except Exception as e:
            if not silent_mode:
                print(f"⚠️ TTS not available: {e}")
            self.tts_enabled = False
        
        
        self.system_controller = SystemController()
        self.intent_router = IntentRouter()
        self.browser_controller = VoiceBrowserController()
        
        
        self.listening = False
        self.command_queue = queue.Queue()
        
        
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 1.2
        
        if not silent_mode:
            print("🤖 Voice Assistant initialized!")
            print("📋 Available commands:")
            print("   • 'Open [app name]' - Launch any application")
            print("   • 'Open This PC' / 'Open File Explorer' - Open file manager")
            print("   • 'Go to Desktop/Documents/Downloads' - Navigate to folders")
            print("   • 'Search for [file name]' - Find files")
            print("   • 'Switch to [window name]' - Switch windows")
            print("   • 'List windows' - Show open windows")
            print("   • 'System status' / 'System info' - Get system information")
            print("   • 'Battery status' - Check battery level")
            print("   • 'Lock screen' - Lock the computer")
            print("   • All browser commands from voice_browser_control")
            print("   • 'Stop listening' - Exit")
    
    def speak(self, text: str, force_speak=False):
        
        if self.silent_mode and not force_speak:
            
            print(f"🔊 {text}")
            return
        
        if self.tts_enabled:
            try:
                
                def speak_thread():
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                
                thread = threading.Thread(target=speak_thread, daemon=True)
                thread.start()
            except Exception as e:
                print(f"⚠️ TTS error: {e}")
        
        
        print(f"🔊 {text}")
    
    def listen_for_commands(self):
        
        print("\n🎤 Listening for voice commands...")
        print("💡 Speak clearly and wait for the beep!")
        
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("🔧 Adjusted for ambient noise")
        
        self.listening = True
        
        while self.listening:
            try:
                with self.microphone as source:
                    if not self.listening:
                        break
                    
                    print("\n👂 Listening...")
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=8)
                
                if not self.listening:
                    break
                
                print("🔄 Processing speech...")
                command = self.recognizer.recognize_google(audio).lower()
                print(f"🗣️ Heard: '{command}'")
                
                
                response = self.process_command(command)
                
                
                if response and isinstance(response, str) and len(response) > 0:
                    
                    if response.startswith("✅") or response.startswith("❌"):
                        self.speak(response)
            
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                print("❓ Could not understand the command")
            except sr.RequestError as e:
                print(f"❌ Speech recognition error: {e}")
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
        
        print("🛑 Voice listening stopped gracefully.")
    
    def process_command(self, command: str) -> Optional[str]:
        
        command = command.strip().lower()
        
        
        if "stop listening" in command or command in ["exit", "stop", "quit", "close"]:
            print("🛑 Stop command received - shutting down voice assistant...")
            self.stop_listening()
            return "✅ Voice assistant stopped"
        
        
        
        browser_keywords = ["chrome", "browser", "search", "google", "youtube", "video", 
                           "tab", "scroll", "minimize chrome", "maximize chrome",
                           "what's on my screen", "analyze screen", "summarise", "summarize"]
        
        if any(keyword in command for keyword in browser_keywords):
            try:
                self.browser_controller.process_command(command)
                return None  
            except Exception as e:
                print(f"Browser command error: {e}")
                
        
        
        intent_type, params = self.intent_router.parse_intent(command)
        
        if intent_type:
            return self._handle_system_intent(intent_type, params)
        
        
        try:
            self.browser_controller.process_command(command)
            return None  
        except:
            pass
        
        
        self.speak("I didn't understand that command. Please try again.")
        return "❓ Unknown command"
    
    def _handle_system_intent(self, intent_type: str, params: dict) -> str:
        
        try:
            if intent_type == "launch_app":
                app_name = params.get("app_name", "")
                if app_name:
                    result = self.system_controller.launch_app(app_name)
                    return result
                else:
                    return "❌ Please specify an application name"
            
            elif intent_type == "open_location":
                location = params.get("location")
                result = self.system_controller.open_file_explorer(location)
                return result
            
            elif intent_type == "search_files":
                query = params.get("query", "")
                if query:
                    result = self.system_controller.search_files(query)
                    return result
                else:
                    return "❌ Please specify what to search for"
            
            elif intent_type == "switch_window":
                window_name = params.get("window_name", "")
                if window_name:
                    result = self.system_controller.switch_to_window(window_name)
                    return result
                else:
                    return "❌ Please specify a window name"
            
            elif intent_type == "list_windows":
                result = self.system_controller.list_open_windows()
                return result
            
            elif intent_type == "system_info":
                result = self.system_controller.get_system_info_text()
                return result
            
            elif intent_type == "battery_status":
                info = self.system_controller.get_system_info()
                if info.get("battery"):
                    battery = info["battery"]
                    status = "plugged in" if battery["plugged"] else "on battery"
                    result = f"✅ Battery: {battery['percent']:.0f}% ({status})"
                else:
                    result = "❌ Battery information not available"
                return result
            
            elif intent_type == "lock_screen":
                result = self.system_controller.lock_screen()
                return result
            
            elif intent_type == "sleep":
                result = self.system_controller.sleep_system()
                return result
            
            elif intent_type == "shutdown":
                delay = params.get("delay", 0)
                result = self.system_controller.shutdown_system(delay)
                return result
            
            elif intent_type == "restart":
                delay = params.get("delay", 0)
                result = self.system_controller.restart_system(delay)
                return result
            
            elif intent_type == "show_desktop":
                result = self.system_controller.show_desktop()
                return result
            
            elif intent_type == "right_click":
                result = self.system_controller.right_click_at_cursor()
                return result
            
            elif intent_type == "double_click":
                result = self.system_controller.double_click_at_cursor()
                return result
            
            elif intent_type == "open_desktop_icon":
                icon_name = params.get("icon_name", "")
                if icon_name:
                    result = self.system_controller.open_desktop_icon(icon_name)
                    return result
                else:
                    return "❌ Please specify a desktop icon name"
            
            elif intent_type == "refresh_desktop":
                result = self.system_controller.refresh_desktop()
                return result
            
            else:
                return f"❌ Unhandled intent: {intent_type}"
        
        except Exception as e:
            return f"❌ Error executing command: {e}"
    
    def stop_listening(self):
        
        print("🛑 Stopping voice assistant...")
        self.listening = False
        
        
        try:
            self.browser_controller.stop_listening()
        except:
            pass
        
        print("👋 Voice Assistant stopped!")
    
    def run(self):
        
        if not self.silent_mode:
            print("\n🚀 Starting Voice Assistant...")
        self.listening = True
        
        try:
            
            if not self.silent_mode:
                self.speak("Voice assistant ready. How can I help you?")
            else:
                print("🎤 Voice assistant listening...")
            self.listen_for_commands()
        except KeyboardInterrupt:
            if not self.silent_mode:
                print("\n⚠️ Interrupted by user")
        except Exception as e:
            print(f"❌ Fatal error: {e}")
        finally:
            self.listening = False
            if not self.silent_mode:
                print("🧩 Voice assistant stopped gracefully.")
    
    def stop(self):
        
        self.stop_listening()


def main():
    
    print("=" * 60)
    print("🤖 VOICE ASSISTANT - LAPTOP CONTROL")
    print("=" * 60)
    
    assistant = VoiceAssistant()
    assistant.run()


if __name__ == "__main__":
    main()
