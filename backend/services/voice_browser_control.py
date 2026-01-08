import speech_recognition as sr
import pyautogui
import subprocess
import time
import re
import webbrowser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, NoSuchElementException
import threading
import queue
import os
import win32gui
import win32con
import win32process
import psutil
import base64
from io import BytesIO
from PIL import Image
import ctypes
from ctypes import wintypes
import shutil

try:
    from dotenv import load_dotenv
    load_dotenv()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    services_env = os.path.join(current_dir, '.env')
    if os.path.exists(services_env):
        load_dotenv(services_env)
        print(f"✅ Loaded .env from services folder: {services_env}")
    parent_env = os.path.join(os.path.dirname(current_dir), '.env')
    if os.path.exists(parent_env):
        load_dotenv(parent_env)
except ImportError:
    print("⚠️ python-dotenv not installed. Install with: pip install python-dotenv")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    print("⚠️ google-generativeai not installed. Install with: pip install google-generativeai")
    GEMINI_AVAILABLE = False

class VoiceBrowserController:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        try:
            self.microphone = sr.Microphone()
        except Exception as e:
            print(f"⚠️ Failed to initialize microphone: {e}")
            print("💡 Microphone unavailable — voice input will be disabled.")
            self.microphone = None
        self.driver = None
        self.listening = False
        self.command_queue = queue.Queue()
       
        
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 1.2
        self.search_mode = False
        self.find_mode = False
        
        self.chrome_path = self._find_chrome_path()
        
        self.gemini_model = None
        self._initialize_gemini()
        
        print("🎤 Voice Browser Controller initialized!")
        print("📋 Available commands:")
        print("   • 'Open Chrome' - Launch Chrome browser")
        print("   • 'Search [your query]' - Search on Google")
        print("   • 'Search' (then say query) - Two-step search")
        print("   • 'Search meaning of [word]' - Search word meaning")
        print("   • 'What's on my screen?' or 'Analyze screen' - Analyze current screen")
        print("   • 'Summarise document' or 'Summarise page' - Summarise current webpage")
        print("   • 'Click' - Click at current cursor position")
        print("   • 'Open another tab' - Open new tab")
        print("   • 'Close tab' - Close current tab")
        print("   • 'Go back' - Navigate to previous webpage")
        print("   • 'Minimize' / 'Minimize Chrome' / 'Minimize cursor' / 'Minimize File Explorer' / 'Minimize window' - Minimize windows")
        print("   • 'Maximize' / 'Maximize Chrome' / 'Maximize cursor' / 'Maximize File Explorer' / 'Maximize window' - Maximize windows")
        print("   • 'Scroll down' - Scroll down in Chrome or current window")
        print("   • 'Scroll up' - Scroll up in Chrome or current window")
        print("   • 'Scroll down more' - Scroll down a full visible page")
        print("   • 'Scroll up more' - Scroll up a full visible page")
        print("   • 'Close browser' - Close entire browser")
        print("   • 'Play video' - Play/resume video")
        print("   • 'Pause video' - Pause video")
        print("   • 'Stop listening' - Exit the program")
    
    def _initialize_gemini(self):
        if not GEMINI_AVAILABLE:
            print("⚠️ Gemini API not available. Install google-generativeai package.")
            return
        
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                print("⚠️ GEMINI_API_KEY not found in .env file. Screen analysis features will be disabled.")
                print("💡 Create a .env file in the project root with: GEMINI_API_KEY=your_api_key")
                print("💡 Note: Word meaning searches work without Gemini API (they use Google search)")
                return
            
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
            print("✅ Gemini API initialized successfully with gemini-2.0-flash!")
            print("💡 Gemini is used for screen analysis features (not word meanings)")
        except Exception as e:
            print(f"⚠️ Failed to initialize Gemini API: {e}")
            print("💡 Screen analysis features will be disabled.")
            print("💡 Note: Word meaning searches still work (they use Google search)")
    
    
    def _find_chrome_path(self):
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"),
        ]
        
        for path in possible_paths:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                print(f"✅ Found Chrome at: {expanded_path}")
                return expanded_path
        
        print("⚠️ Chrome not found in default locations")
        print("💡 Trying to use system default browser instead...")
        return None
    
    def find_chrome_window(self):
        """Find Chrome window handle"""
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                if "Google Chrome" in window_text or "chrome" in window_text.lower():
                    windows.append(hwnd)
            return True
        
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        return windows[0] if windows else None
    
    def focus_chrome_window(self):
        """Focus Chrome window using multiple reliable methods"""
        try:
            print("🎯 Focusing Chrome window...")
            
            chrome_hwnd = self.find_chrome_window()
            if chrome_hwnd:
                try:
                    win32gui.ShowWindow(chrome_hwnd, win32con.SW_RESTORE)
                    win32gui.ShowWindow(chrome_hwnd, win32con.SW_SHOW)
                    win32gui.SetForegroundWindow(chrome_hwnd)
                    time.sleep(1.0)
                    print("✅ Chrome focused using window handle")
                    return True
                except Exception as e:
                    print(f"Window API failed: {e}")
            
            print("🔄 Using Alt+Tab method...")
            for i in range(3):
                pyautogui.hotkey('alt', 'tab')
                time.sleep(0.8)
                
                try:
                    pyautogui.hotkey('ctrl', 'l')
                    time.sleep(0.3)
                    pyautogui.press('escape')
                    print("✅ Chrome focused via Alt+Tab!")
                    return True
                except:
                    continue
            
            print("🖱️ Trying taskbar click...")
            screen_width, screen_height = pyautogui.size()
            taskbar_y = screen_height - 40
            
            for x in range(200, 800, 100):
                pyautogui.click(x, taskbar_y)
                time.sleep(0.5)
                
                try:
                    pyautogui.hotkey('ctrl', 'l')
                    time.sleep(0.3)
                    pyautogui.press('escape')
                    print("✅ Chrome focused via taskbar click!")
                    return True
                except:
                    continue
            
            print("⚠️ Could not focus Chrome window")
            return False
            
        except Exception as e:
            print(f"⚠️ Focus method failed: {e}")
            return False
    
    def setup_selenium_driver(self):
        """Setup Selenium WebDriver for Chrome"""
        try:
            chrome_options = Options()
            chrome_options.add_experimental_option("detach", True)
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            print("✅ Selenium WebDriver initialized")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup Selenium: {e}")
            print("📝 Using PyAutoGUI fallback for browser control")
            return False
    
    def listen_for_commands(self):
        """Listen for voice commands continuously"""
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

                    if self.search_mode:
                        print("\n🔍 Listening for search query...")
                        audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=10)
                    elif self.find_mode:
                        print("\n🔎 Listening for find query (will search inside the active window)...")
                        audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=8)
                    else:
                        print("\n👂 Listening...")
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)

                if not self.listening:
                    break 

                print("🔄 Processing speech...")
                command = self.recognizer.recognize_google(audio).lower()
                print(f"🗣️ Heard: '{command}'")
                self.process_command(command)

            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                print("❓ Could not understand the command")
            except sr.RequestError as e:
                print(f"❌ Speech recognition error: {e}")
            except Exception as e:
                print(f"❌ Unexpected error: {e}")

        print("🛑 Voice listening stopped gracefully.")

    
    def process_command(self, command):
        """Process recognized voice command"""
        command = command.strip().lower()
        
        try:
            if self.search_mode:
                print(f"🔍 Search query captured: '{command}'")
                self.search_query(command)
                self.search_mode = False
                return
            if self.find_mode:
                print(f"🔎 Find query captured: '{command}'")
                self.find_in_active(command)
                self.find_mode = False
                return
            
            m_drive = (re.search(r'open\s+(?:the\s+)?([a-z])\s*drive', command) or
                       re.search(r'open\s+(?:the\s+)?drive\s+([a-z])', command) or
                       re.search(r'open\s+(?:the\s+)?([a-z]):', command) or
                       re.search(r'open\s+(?:the\s+)?([a-z])\b', command))

            if m_drive and 'open' in command:
                drive_letter = m_drive.group(1).upper()
                print(f"🔎 Detected drive open command for: {drive_letter}:")
                self.open_drive(drive_letter)
                return

            if "open chrome" in command:
                self.open_chrome()

            if "open vs code" in command or "open vscode" in command or "open visual studio code" in command:
                self.open_vs_code()

            if ("maximize" in command or "maximise" in command) and ("vs code" in command or "vscode" in command or "visual studio code" in command):
                self.maximize_vscode()
                return

            if ("minimize" in command or "minimise" in command) and ("vs code" in command or "vscode" in command or "visual studio code" in command):
                self.minimize_vscode()
                return

            if command.startswith('mini '):
                q = command.replace('mini ', '', 1).strip()
                if q:
                    self.find_in_active(q)
                    return

            if command.startswith('find '):
                query = command.replace('find ', '', 1).strip()
                if query:
                    self.find_in_active(query)
                    return

            if any(phr in command for phr in ['find in active', 'search in active', 'search in active tab', 'find in active tab', 'find this page', 'search this page', 'find in tab', 'search in tab']):
                m_find = re.search(r'(?:find|search).*?(?:in (?:the )?(?:active|this|current)(?: tab| page)?)[\s:\-]*(.*)', command)
                if m_find and m_find.group(1).strip():
                    self.find_in_active(m_find.group(1).strip())
                    return
                else:
                    print("🎤 Find mode activated! Say the text to find in the active window...")
                    self.find_mode = True
                    return

            if command == 'find':
                print("🎤 Find mode activated! Say the text to find in the active window...")
                self.find_mode = True
                return
            
            elif "search" in command and len(command.split()) == 1:
                print("🎤 Search mode activated! Say your search query now...")
                self.search_mode = True
                return
            
            elif command.startswith("search ") or "search for" in command:
                if command.startswith("search for "):
                    query = command.replace("search for ", "", 1)
                else:
                    query = command.replace("search ", "", 1)
                
                if query.strip():  
                    self.search_query(query)
                else:
                    print("❓ No search query provided. Try: 'Search cats' or just say 'Search' first")
            
            elif 'click' in command:
                try:
                    if 'double' in command:
                        m_coord = re.search(r'click(?: at)?\s*(\d+)\s*[ ,]\s*(\d+)', command)
                        if m_coord:
                            x = int(m_coord.group(1)); y = int(m_coord.group(2))
                            print(f"🖱️ Double-clicking at ({x},{y})")
                            pyautogui.doubleClick(x=x, y=y)
                        else:
                            print("🖱️ Double-clicking at current cursor position")
                            pyautogui.doubleClick()
                        return

                    if 'right' in command or 'right-click' in command or 'right click' in command:
                        m_coord = re.search(r'click(?: at)?\s*(\d+)\s*[ ,]\s*(\d+)', command)
                        if m_coord:
                            x = int(m_coord.group(1)); y = int(m_coord.group(2))
                            print(f"🖱️ Right-clicking at ({x},{y})")
                            pyautogui.click(x=x, y=y, button='right')
                        else:
                            print("🖱️ Right-clicking at current cursor position")
                            pyautogui.click(button='right')
                        return

                    if 'middle' in command or 'middle-click' in command:
                        print("🖱️ Middle-clicking at current cursor position")
                        pyautogui.click(button='middle')
                        return

                    m_coord = re.search(r'click(?: at)?\s*(\d+)\s*[ ,]\s*(\d+)', command)
                    if m_coord:
                        x = int(m_coord.group(1)); y = int(m_coord.group(2))
                        print(f"🖱️ Clicking at ({x},{y})")
                        pyautogui.click(x=x, y=y)
                        return

                    print("🖱️ Clicking at current cursor position (default)")
                    self.click_at_cursor()
                except pyautogui.FailSafeException as fe:
                    print(f"❌ PyAutoGUI failsafe triggered: {fe}")
                except Exception as e:
                    print(f"❌ Click command failed: {e}")
            
            elif "open another tab" in command or "new tab" in command:
                self.open_new_tab()
            
            elif "close tab" in command:
                self.close_tab()
            
            elif "go back" in command or "back" in command:
                self.go_back()
            
            elif "minimize" in command or "minimise" in command:
                if "chrome" in command:
                    self.minimize_window("chrome")
                elif "cursor" in command:
                    self.minimize_window("cursor")
                elif "file explorer" in command or "explorer" in command:
                    self.minimize_window("explorer")
                elif "window" in command:
                    self.minimize_window("other")
                else:
                    self.minimize_window("active")
            
            elif "maximize" in command or "maximise" in command:
                if "chrome" in command:
                    self.maximize_window("chrome")
                elif "cursor" in command:
                    self.maximize_window("cursor")
                elif "file explorer" in command or "explorer" in command:
                    self.maximize_window("explorer")
                elif "window" in command:
                    self.maximize_window("other")
                else:
                    self.maximize_window("active")
            
            elif "scroll down more" in command or "scroll more down" in command:
                self.scroll_down_more()
            
            elif "scroll up more" in command or "scroll more up" in command:
                self.scroll_up_more()
            
            elif "scroll down" in command:
                self.scroll_down()
            
            elif "scroll up" in command:
                self.scroll_up()
            
            elif "close browser" in command:
                self.close_browser()
            
            elif "play video" in command or "play" in command:
                self.play_video()
            
            elif "pause video" in command or "pause" in command:
                self.pause_video()
            
            elif "stop listening" in command or "exit" in command:
                self.stop_listening()
            
            elif "search meaning" in command or "meaning of" in command:
                word_match = re.search(r'(?:meaning of|meaning)\s+(.+)', command, re.IGNORECASE)
                if word_match:
                    word = word_match.group(1).strip()
                    word = re.sub(r'[^\w\s]+$', '', word)
                    self.search_word_meaning(word)
                else:
                    print("❓ Please specify a word. Example: 'Search meaning of artificial intelligence'")
            
            elif "what's on my screen" in command or "analyze screen" in command or "what is on my screen" in command:
                self.analyze_screen()
            
            elif "summarize" in command or "summarise" in command:
                self.summarize_current_page()
            
            elif command.startswith("ask") or "ask about" in command:
                question_match = re.search(r'ask\s+(?:about\s+)?(.+)', command, re.IGNORECASE)
                if question_match:
                    question = question_match.group(1).strip()
                    self.ask_about_screen(question)
                else:
                    print("❓ Please provide a question about your screen. Example: 'Ask what is this document about'")
            
            else:
                print(f"❓ Unknown command: '{command}'")
                print("💡 Try: 'Open Chrome', 'Search cats', 'What's on my screen?', etc.")
                
        except Exception as e:
            print(f"❌ Error executing command '{command}': {e}")
    
    def open_chrome(self):
        """Open Chrome browser with just one tab"""
        try:
            print("🌐 Opening Chrome...")
            
            if self.chrome_path and os.path.exists(self.chrome_path):
                print(f"🚀 Starting Chrome from: {self.chrome_path}")
                subprocess.Popen([
                    self.chrome_path, 
                    "--new-window", 
                    "--start-maximized",
                    "https://www.google.com"
                ])
            else:
                print("⚠️ Chrome path not found, using default browser...")
                webbrowser.open('https://www.google.com')
                print("✅ Opened Google in default browser!")
                return
            
            print("⏰ Waiting for Chrome to load...")
            time.sleep(4)
            
            self.focus_chrome_window()
            
            print("✅ Chrome opened with Google homepage!")
            
        except FileNotFoundError as e:
            print(f"❌ Chrome executable not found: {e}")
            print("💡 Opening in default browser instead...")
            try:
                webbrowser.open('https://www.google.com')
                print("✅ Opened Google in default browser!")
            except Exception as fallback_error:
                print(f"❌ Failed to open browser: {fallback_error}")

    def open_vs_code(self):
        """Open Visual Studio Code using common locations or 'code' in PATH"""
        try:
            print("🧑‍💻 Opening VS Code...")
            code_cmd = shutil.which('code')
            if code_cmd:
                subprocess.Popen([code_cmd])
                print("✅ VS Code opened using 'code' from PATH")
                return

            possible = [
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
                os.path.expandvars(r"%PROGRAMFILES%\Microsoft VS Code\Code.exe"),
                os.path.expandvars(r"%PROGRAMFILES(x86)%\Microsoft VS Code\Code.exe"),
            ]

            for p in possible:
                if p and os.path.exists(p):
                    subprocess.Popen([p])
                    print(f"✅ VS Code opened from: {p}")
                    return

            try:
                os.startfile('code')
                print("✅ Attempted to open VS Code via os.startfile('code')")
                return
            except Exception:
                pass

            print("❌ Could not find VS Code executable. Make sure VS Code is installed and 'code' is in PATH.")
        except Exception as e:
            print(f"❌ Failed to open VS Code: {e}")

    def open_drive(self, drive_letter):
        """Open a Windows drive in File Explorer (e.g., D, E)

        drive_letter: single uppercase letter (A-Z)
        """
        try:
            if not drive_letter or len(drive_letter) != 1 or not drive_letter.isalpha():
                print(f"❌ Invalid drive letter: {drive_letter}")
                return

            path = f"{drive_letter}:/"
            explorer_path = f"{drive_letter}:\\"

            if os.path.exists(path) or os.path.exists(explorer_path):
                try:
                    subprocess.Popen(['explorer', f'{drive_letter}:\\'])
                    print(f"✅ Opened drive {drive_letter}:\\ in File Explorer")
                except Exception as e:
                    try:
                        os.startfile(f"{drive_letter}:/")
                        print(f"✅ Opened drive {drive_letter}:/ via os.startfile")
                    except Exception as e2:
                        print(f"❌ Failed to open drive {drive_letter}: {e} / {e2}")
            else:
                print(f"❌ Drive {drive_letter}: not found or not accessible")
        except Exception as e:
            print(f"❌ Error opening drive {drive_letter}: {e}")
            print("💡 Trying default browser...")
            try:
                webbrowser.open('https://www.google.com')
                print("✅ Opened Google in default browser!")
            except Exception as fallback_error:
                print(f"❌ Failed to open browser: {fallback_error}")
    
    def manual_chrome_focus_helper(self):
        """Helper method to manually ensure Chrome focus"""
        print("\n🎯 CHROME FOCUS HELPER:")
        print("1. Click on Chrome window manually")
        print("2. Make sure Chrome is visible on screen")
        print("3. Press any key when Chrome is focused...")
        try:
            input("Press Enter when Chrome is focused and ready...")
        except (OSError, EOFError) as e:
            print(f"⚠️ No console input available: {e}")
            print("💡 Continuing without manual confirmation.")
        
        try:
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.3)
            pyautogui.press('escape')
            print("✅ Chrome focus confirmed!")
            return True
        except:
            print("❌ Chrome still not focused")
            return False
    
    def search_query(self, query):
        """Search for a query on Google in the current tab"""
        try:
            print(f"🔍 Searching for: '{query}'")
            
            print("🎯 Attempting automatic Chrome focus...")
            focused = False
            for attempt in range(2):
                if self.focus_chrome_window():
                    focused = True
                    break
                time.sleep(1)
            
            if not focused:
                print("⚠️ Automatic Chrome focus failed!")
                try:
                    response = input("Try manual focus? (y/n): ").lower()
                except (OSError, EOFError) as e:
                    print(f"⚠️ No console input available: {e}")
                    response = 'n'

                if response == 'y':
                    focused = self.manual_chrome_focus_helper()
            
            if focused:
                self._search_with_pyautogui(query)
            else:
                print("❌ Cannot search - Chrome not focused!")
                print("💡 Make sure Chrome window is open and visible")
                
        except Exception as e:
            print(f"❌ Failed to search: {e}")
    
    def _search_with_pyautogui(self, query):
        """Search using PyAutoGUI - SIMPLIFIED AND RELIABLE VERSION"""
        try:
            print(f"� Searching for: '{query}'")
            
            print("📍 Focusing Chrome...")
            focused = False
            for attempt in range(3):
                if self.focus_chrome_window():
                    focused = True
                    break
                print(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(1)
            
            if not focused:
                print("❌ Could not focus Chrome! Make sure Chrome is open.")
                return
            
            time.sleep(1.5)
            
            print("📍 Focusing address bar...")
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(1.0)
            
            print("📍 Clearing address bar...")
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            
            print(f"📍 Typing: '{query}'")
            for char in query:
                pyautogui.typewrite(char)
                time.sleep(0.08) 
            
            time.sleep(1.0)
            
            print("📍 Pressing Enter...")
            pyautogui.press('enter')
            
            print("✅ Search completed!")
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
    
    def open_search_result(self, result_number):
        """Open a specific search result by number (1-5)"""
        try:
            print(f"🔗 Opening search result #{result_number}...")
            
            if self.driver:
                try:
                    time.sleep(2)
                    
                    selectors = [
                        f"#search .g:nth-child({result_number}) h3 a",  
                        f"#rso .g:nth-child({result_number}) h3 a",   
                        f".g:nth-child({result_number}) a[href]:first-of-type", 
                        f".yuRUbf:nth-child({result_number}) a",      
                    ]
                    
                    link_clicked = False
                    for selector in selectors:
                        try:
                            links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if links and len(links) >= 1:
                                if result_number <= len(links):
                                    link = links[0] if result_number == 1 else links[result_number - 1]
                                    self.driver.execute_script("arguments[0].click();", link)
                                    print(f"✅ Opened search result #{result_number} with Selenium!")
                                    link_clicked = True
                                    break
                        except:
                            continue
                    
                    if not link_clicked:
                        try:
                            all_links = self.driver.find_elements(By.CSS_SELECTOR, "#search .g h3 a, #rso .g h3 a")
                            if all_links and result_number <= len(all_links):
                                link = all_links[result_number - 1]
                                self.driver.execute_script("arguments[0].click();", link)
                                print(f"✅ Opened search result #{result_number} (fallback method)!")
                                link_clicked = True
                        except:
                            pass
                    
                    if not link_clicked:
                        print(f"❌ Could not find search result #{result_number}")
                        return
                        
                except Exception as selenium_error:
                    print(f"⚠️ Selenium method failed: {selenium_error}")
                    self._open_result_with_pyautogui(result_number)
            else:
                self._open_result_with_pyautogui(result_number)
                
        except Exception as e:
            print(f"❌ Failed to open search result: {e}")
    
    def _open_result_with_pyautogui(self, result_number):
        """Fallback method to open search results using PyAutoGUI"""
        try:
            print(f"🖱️ Using PyAutoGUI to open result #{result_number}...")
            
            pyautogui.press('home')
            time.sleep(1)
            
            tab_count = 7 + (result_number - 1) * 3
            
            for i in range(tab_count):
                pyautogui.press('tab')
                time.sleep(0.1)
            
            pyautogui.press('enter')
            print(f"✅ Opened search result #{result_number} with PyAutoGUI!")
            
        except Exception as e:
            print(f"❌ PyAutoGUI fallback failed: {e}")
    
    def click_at_cursor(self):
        """Click at the current cursor position or specified coordinates.

        Optional parameters are passed via attributes on the instance prior to calling
        or by calling helper methods. For normal use just call without args.
        """
        try:
            print("🖱️ Clicking at current cursor position...")

            current_x, current_y = pyautogui.position()
            print(f"📍 Cursor position: ({current_x}, {current_y})")

            pyautogui.click(current_x, current_y)
            print("✅ Clicked successfully!")

        except pyautogui.FailSafeException as fe:
            print(f"❌ PyAutoGUI failsafe triggered during click: {fe}")
        except Exception as e:
            print(f"❌ Failed to click: {e}")
    
    def open_new_tab(self):
        """Open a new tab"""
        try:
            print("📂 Opening new tab...")
            
            if self.driver:
                self.driver.execute_script("window.open('');")
                self.driver.switch_to.window(self.driver.window_handles[-1])
            else:
                pyautogui.hotkey('ctrl', 't')
            
            print("✅ New tab opened!")
            
        except Exception as e:
            print(f"❌ Failed to open new tab: {e}")
    
    def close_tab(self):
        """Close current tab"""
        try:
            print("❌ Closing current tab...")
            
            if self.driver and len(self.driver.window_handles) > 1:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[-1])
            else:
                pyautogui.hotkey('ctrl', 'w')
            
            print("✅ Tab closed!")
            
        except Exception as e:
            print(f"❌ Failed to close tab: {e}")
    
    def go_back(self):
        """Navigate back to previous webpage in Chrome"""
        try:
            print("⬅️ Going back to previous page...")
            
            if self.driver:
                self.driver.back()
                print("✅ Navigated back!")
            else:
                if self.focus_chrome_window():
                    time.sleep(0.5)
                    pyautogui.hotkey('alt', 'left')
                    print("✅ Navigated back!")
                else:
                    print("❌ Could not focus Chrome. Please ensure Chrome is open.")
            
        except Exception as e:
            print(f"❌ Failed to go back: {e}")
    
    def find_window_under_cursor(self):
        """Find the window handle under the current cursor position"""
        try:
            cursor_x, cursor_y = pyautogui.position()
            
            try:
                point = wintypes.POINT(cursor_x, cursor_y)
                hwnd = ctypes.windll.user32.WindowFromPoint(point)
                
                hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2)
                
                if hwnd and win32gui.IsWindowVisible(hwnd):
                    return hwnd
            except Exception as e:
                pass
            
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    try:
                        rect = win32gui.GetWindowRect(hwnd)
                        left, top, right, bottom = rect
                        if left <= cursor_x <= right and top <= cursor_y <= bottom:
                            windows.append((hwnd, win32gui.GetWindowText(hwnd)))
                    except:
                        pass
                return True
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            if windows:
                return windows[0][0]
            return None
        except Exception as e:
            print(f"⚠️ Error finding window under cursor: {e}")
            return None
    
    def find_file_explorer_window(self):
        """Find File Explorer window handle"""
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                if "explorer" in window_text.lower() or "CabinetWClass" in class_name or "ExploreWClass" in class_name:
                    windows.append(hwnd)
            return True
        
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        return windows[0] if windows else None

    def find_vscode_window(self):
        """Find a Visual Studio Code window handle by title or class name"""
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    window_text = win32gui.GetWindowText(hwnd)
                    if not window_text:
                        return True
                    lower = window_text.lower()
                    if 'visual studio code' in lower or 'vscode' in lower or ' - code' in lower:
                        windows.append(hwnd)
                        return True
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        proc = psutil.Process(pid)
                        pname = proc.name().lower()
                        if 'code.exe' in pname or pname.startswith('code'):
                            windows.append(hwnd)
                    except Exception:
                        pass
                except:
                    pass
            return True

        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        return windows[0] if windows else None

    def maximize_vscode(self):
        """Maximize the Visual Studio Code window if found"""
        try:
            print("📈 Maximizing VS Code...")
            hwnd = self.find_vscode_window()
            if not hwnd:
                print("❌ VS Code window not found")
                return

            try:
                win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.2)
                title = win32gui.GetWindowText(hwnd)
                print(f"✅ VS Code maximized: {title}")
            except Exception as e:
                print(f"❌ Failed to maximize VS Code: {e}")

        except Exception as e:
            print(f"❌ Error maximizing VS Code: {e}")
    
    def minimize_vscode(self):
        """Minimize the Visual Studio Code window if found"""
        try:
            print("📉 Minimizing VS Code...")
            hwnd = self.find_vscode_window()
            if not hwnd:
                print("❌ VS Code window not found")
                return

            try:
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                time.sleep(0.15)
                title = win32gui.GetWindowText(hwnd)
                print(f"✅ VS Code minimized: {title}")
            except Exception as e:
                print(f"❌ Failed to minimize VS Code: {e}")

        except Exception as e:
            print(f"❌ Error minimizing VS Code: {e}")
    
    def get_active_window(self):
        """Get the currently active (focused) window handle"""
        try:
            return win32gui.GetForegroundWindow()
        except:
            return None
    
    def find_other_window(self):
        """Find any window that is not Chrome or File Explorer"""
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    window_text = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    
                    if "chrome" in window_text.lower() or "Google Chrome" in window_text:
                        return True
                    
                    if "explorer" in window_text.lower() or "CabinetWClass" in class_name or "ExploreWClass" in class_name:
                        return True
                    
                    if window_text == "" or "Desktop" in window_text:
                        return True
                    
                    windows.append((hwnd, window_text))
                except:
                    pass
            return True
        
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        
        active_hwnd = self.get_active_window()
        if active_hwnd:
            active_text = win32gui.GetWindowText(active_hwnd)
            active_class = win32gui.GetClassName(active_hwnd)
            
            if (active_hwnd not in [w[0] for w in windows] and 
                "chrome" not in active_text.lower() and 
                "Google Chrome" not in active_text and
                "explorer" not in active_text.lower() and
                "CabinetWClass" not in active_class and
                "ExploreWClass" not in active_class and
                active_text != ""):
                return active_hwnd
        
        return windows[0][0] if windows else None
    
    def minimize_window(self, target="active"):
        """Minimize a window based on target type"""
        try:
            hwnd = None
            
            if target == "chrome":
                print("📉 Minimizing Chrome...")
                hwnd = self.find_chrome_window()
                if not hwnd:
                    print("❌ Chrome window not found")
                    return
            elif target == "cursor":
                print("📉 Minimizing window under cursor...")
                hwnd = self.find_window_under_cursor()
                if not hwnd:
                    print("❌ No window found under cursor")
                    return
            elif target == "explorer":
                print("📉 Minimizing File Explorer...")
                hwnd = self.find_file_explorer_window()
                if not hwnd:
                    print("❌ File Explorer window not found")
                    return
            elif target == "other":
                print("📉 Minimizing other window (not Chrome/File Explorer)...")
                hwnd = self.find_other_window()
                if not hwnd:
                    print("❌ No other window found (excluding Chrome and File Explorer)")
                    return
            else:  
                print("📉 Minimizing active window...")
                hwnd = self.get_active_window()
                if not hwnd:
                    print("❌ Could not get active window")
                    return
            
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                window_title = win32gui.GetWindowText(hwnd)
                print(f"✅ Window minimized: {window_title}")
            
        except Exception as e:
            print(f"❌ Failed to minimize window: {e}")
    
    def maximize_window(self, target="active"):
        """Maximize a window based on target type"""
        try:
            hwnd = None
            
            if target == "chrome":
                print("📈 Maximizing Chrome...")
                hwnd = self.find_chrome_window()
                if not hwnd:
                    print("❌ Chrome window not found")
                    return
            elif target == "cursor":
                print("📈 Maximizing window under cursor...")
                hwnd = self.find_window_under_cursor()
                if not hwnd:
                    print("❌ No window found under cursor")
                    return
            elif target == "explorer":
                print("📈 Maximizing File Explorer...")
                hwnd = self.find_file_explorer_window()
                if not hwnd:
                    print("❌ File Explorer window not found")
                    return
            elif target == "other":
                print("📈 Maximizing other window (not Chrome/File Explorer)...")
                hwnd = self.find_other_window()
                if not hwnd:
                    print("❌ No other window found (excluding Chrome and File Explorer)")
                    return
            else:  
                print("📈 Maximizing active window...")
                hwnd = self.get_active_window()
                if not hwnd:
                    print("❌ Could not get active window")
                    return
            
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                window_title = win32gui.GetWindowText(hwnd)
                print(f"✅ Window maximized: {window_title}")
            
        except Exception as e:
            print(f"❌ Failed to maximize window: {e}")
    
    def scroll_down(self):
        """Scroll down on the currently active window/tab - scrolls at least half a page"""
        try:
            print("⬇️ Scrolling down...")
            
            active_hwnd = self.get_active_window()
            
            if active_hwnd:
                window_text = win32gui.GetWindowText(active_hwnd)
                is_chrome = "chrome" in window_text.lower() or "Google Chrome" in window_text
                
                if is_chrome:
                    for _ in range(3):
                        pyautogui.press('pagedown')
                        time.sleep(0.08)
                    print("✅ Scrolled down in active window!")
                else:
                    cursor_x, cursor_y = pyautogui.position()
                    for _ in range(15):
                        pyautogui.scroll(-5, x=cursor_x, y=cursor_y)
                        time.sleep(0.015)
                    print("✅ Scrolled down in active window!")
            else:
                cursor_x, cursor_y = pyautogui.position()
                for _ in range(15):
                    pyautogui.scroll(-5, x=cursor_x, y=cursor_y)
                    time.sleep(0.015)
                print("✅ Scrolled down!")
                
        except Exception as e:
            print(f"❌ Failed to scroll down: {e}")
    
    def scroll_up(self):
        """Scroll up on the currently active window/tab - scrolls at least half a page"""
        try:
            print("⬆️ Scrolling up...")
            
            active_hwnd = self.get_active_window()
            
            if active_hwnd:
                window_text = win32gui.GetWindowText(active_hwnd)
                is_chrome = "chrome" in window_text.lower() or "Google Chrome" in window_text
                
                if is_chrome:
                    for _ in range(3):
                        pyautogui.press('pageup')
                        time.sleep(0.08)
                    print("✅ Scrolled up in active window!")
                else:
                    cursor_x, cursor_y = pyautogui.position()
                    for _ in range(15):
                        pyautogui.scroll(5, x=cursor_x, y=cursor_y)
                        time.sleep(0.015)
                    print("✅ Scrolled up in active window!")
            else:
                cursor_x, cursor_y = pyautogui.position()
                for _ in range(15):
                    pyautogui.scroll(5, x=cursor_x, y=cursor_y)
                    time.sleep(0.015)
                print("✅ Scrolled up!")
                
        except Exception as e:
            print(f"❌ Failed to scroll up: {e}")
    
    def scroll_down_more(self):
        """Scroll down a full visible page on the currently active window/tab"""
        try:
            print("⬇️ Scrolling down more (full page)...")
            
            active_hwnd = self.get_active_window()
            
            if active_hwnd:
                window_text = win32gui.GetWindowText(active_hwnd)
                is_chrome = "chrome" in window_text.lower() or "Google Chrome" in window_text
                
                if is_chrome:
                    for _ in range(6):
                        pyautogui.press('pagedown')
                        time.sleep(0.08)
                    print("✅ Scrolled down full page in active window!")
                else:
                    cursor_x, cursor_y = pyautogui.position()
                    for _ in range(30):
                        pyautogui.scroll(-8, x=cursor_x, y=cursor_y)
                        time.sleep(0.01)
                    print("✅ Scrolled down full page in active window!")
            else:
                cursor_x, cursor_y = pyautogui.position()
                for _ in range(30):
                    pyautogui.scroll(-8, x=cursor_x, y=cursor_y)
                    time.sleep(0.01)
                print("✅ Scrolled down full page!")
                
        except Exception as e:
            print(f"❌ Failed to scroll down more: {e}")
    
    def scroll_up_more(self):
        """Scroll up a full visible page on the currently active window/tab"""
        try:
            print("⬆️ Scrolling up more (full page)...")
            
            active_hwnd = self.get_active_window()
            
            if active_hwnd:
                window_text = win32gui.GetWindowText(active_hwnd)
                is_chrome = "chrome" in window_text.lower() or "Google Chrome" in window_text
                
                if is_chrome:
                    for _ in range(6):
                        pyautogui.press('pageup')
                        time.sleep(0.08)
                    print("✅ Scrolled up full page in active window!")
                else:
                    cursor_x, cursor_y = pyautogui.position()
                    for _ in range(30):
                        pyautogui.scroll(8, x=cursor_x, y=cursor_y)
                        time.sleep(0.01)
                    print("✅ Scrolled up full page in active window!")
            else:
                cursor_x, cursor_y = pyautogui.position()
                for _ in range(30):
                    pyautogui.scroll(8, x=cursor_x, y=cursor_y)
                    time.sleep(0.01)
                print("✅ Scrolled up full page!")
                
        except Exception as e:
            print(f"❌ Failed to scroll up more: {e}")
    
    def close_browser(self):
        """Close entire browser"""
        try:
            print("🚪 Closing browser...")
            
            if self.driver:
                self.driver.quit()
                self.driver = None
            else:
                pyautogui.hotkey('alt', 'f4')
            
            print("✅ Browser closed!")
            
        except Exception as e:
            print(f"❌ Failed to close browser: {e}")
    
    def play_video(self):
        """Play/resume video (works on YouTube and most video sites)"""
        try:
            print("▶️ Playing video...")
            
            if self.driver:
                try:
                    play_button = self.driver.find_element(By.CSS_SELECTOR, ".ytp-play-button")
                    if "paused" in play_button.get_attribute("class"):
                        play_button.click()
                        print("✅ YouTube video played!")
                        return
                except NoSuchElementException:
                    pass
                
                try:
                    video = self.driver.find_element(By.TAG_NAME, "video")
                    self.driver.execute_script("arguments[0].play();", video)
                    print("✅ HTML5 video played!")
                    return
                except NoSuchElementException:
                    pass
            
            pyautogui.press('space')
            print("✅ Video play command sent (spacebar)!")
            
        except Exception as e:
            print(f"❌ Failed to play video: {e}")

    
    
    def pause_video(self):
        """Pause video (works on YouTube and most video sites)"""
        try:
            print("⏸️ Pausing video...")
            
            if self.driver:
                try:
                    play_button = self.driver.find_element(By.CSS_SELECTOR, ".ytp-play-button")
                    if "paused" not in play_button.get_attribute("class"):
                        play_button.click()
                        print("✅ YouTube video paused!")
                        return
                except NoSuchElementException:
                    pass
                
                try:
                    video = self.driver.find_element(By.TAG_NAME, "video")
                    self.driver.execute_script("arguments[0].pause();", video)
                    print("✅ HTML5 video paused!")
                    return
                except NoSuchElementException:
                    pass
            
            pyautogui.press('space')
            print("✅ Video pause command sent (spacebar)!")
            
        except Exception as e:
            print(f"❌ Failed to pause video: {e}")
    
    def capture_screen(self):
        """Capture screenshot of current screen"""
        try:
            screenshot = pyautogui.screenshot()
            return screenshot
        except Exception as e:
            print(f"❌ Failed to capture screen: {e}")
            return None

    def find_in_active(self, query):
        """Perform an in-window search (Ctrl+F or F3 for Explorer) in the currently active window."""
        try:
            print(f"🔎 Performing find in active window for: '{query}'")

            active_hwnd = self.get_active_window()
            window_text = ""
            class_name = ""
            try:
                window_text = win32gui.GetWindowText(active_hwnd) or ""
                class_name = win32gui.GetClassName(active_hwnd) or ""
            except Exception:
                pass

            is_explorer = False
            try:
                if 'explorer' in window_text.lower() or 'cabinetwclass' in class_name.lower() or 'explorewclass' in class_name.lower():
                    is_explorer = True
            except Exception:
                is_explorer = False

            time.sleep(0.2)

            if is_explorer:
                pyautogui.press('f3')
            else:
                pyautogui.hotkey('ctrl', 'f')

            time.sleep(0.2)

            for ch in query:
                pyautogui.typewrite(ch)
                time.sleep(0.01)

            time.sleep(0.1)
            pyautogui.press('enter')

            print("✅ Find completed in active window.")
        except Exception as e:
            print(f"❌ Failed to perform in-window find: {e}")
    
    def analyze_screen(self):
        """Analyze current screen using Gemini API and provide description"""
        if not self.gemini_model:
            print("❌ Gemini API not available. Please set GEMINI_API_KEY in .env file.")
            return
        
        try:
            print("📸 Capturing screen...")
            screenshot = self.capture_screen()
            if not screenshot:
                print("❌ Failed to capture screen")
                return
            
            print("🔍 Analyzing screen with Gemini AI...")
            
            img_bytes = BytesIO()
            screenshot.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            prompt = "Analyze this screenshot and describe what's visible on the screen in detail. Include information about windows, applications, text content, and any important elements."
            
            response = self.gemini_model.generate_content([prompt, screenshot])
            
            print("📋 Screen Analysis:")
            print("-" * 60)
            print(response.text)
            print("-" * 60)
            
        except Exception as e:
            print(f"❌ Failed to analyze screen: {e}")
            import traceback
            traceback.print_exc()
    
    def ask_about_screen(self, question):
        """Ask a specific question about the current screen"""
        if not self.gemini_model:
            print("❌ Gemini API not available. Please set GEMINI_API_KEY in .env file.")
            return
        
        try:
            print(f"📸 Capturing screen for question: '{question}'")
            screenshot = self.capture_screen()
            if not screenshot:
                print("❌ Failed to capture screen")
                return
            
            print("🔍 Analyzing screen with Gemini AI...")
            
            prompt = f"Answer this question about the screenshot: {question}. Be specific and accurate based on what you can see in the image."
            
            response = self.gemini_model.generate_content([prompt, screenshot])
            
            print("💡 Answer:")
            print("-" * 60)
            print(response.text)
            print("-" * 60)
            
        except Exception as e:
            print(f"❌ Failed to answer question: {e}")
            import traceback
            traceback.print_exc()
    
    def get_current_chrome_url(self):
        """Get the current URL from Chrome browser"""
        try:
            if self.driver:
                try:
                    url = self.driver.current_url
                    print(f"📍 Current URL (Selenium): {url}")
                    return url
                except:
                    pass
            
            print("📍 Getting URL from Chrome address bar...")
            if not self.focus_chrome_window():
                print("❌ Could not focus Chrome window")
                return None
            
            time.sleep(0.5)
            
            pyautogui.hotkey('ctrl', 'l') 
            time.sleep(0.3)
            pyautogui.hotkey('ctrl', 'a')  
            time.sleep(0.2)
            pyautogui.hotkey('ctrl', 'c') 
            time.sleep(0.3)
            pyautogui.press('escape') 
            
            try:
                import win32clipboard
                win32clipboard.OpenClipboard()
                url = win32clipboard.GetClipboardData()
                win32clipboard.CloseClipboard()
                print(f"📍 Current URL: {url}")
                return url
            except ImportError:
                print("⚠️ win32clipboard not available. Install pywin32 for clipboard access.")
                return None
            except Exception as e:
                print(f"❌ Failed to get URL from clipboard: {e}")
                return None
                
        except Exception as e:
            print(f"❌ Failed to get Chrome URL: {e}")
            return None
    
    def summarize_current_page(self):
        """Summarize the current webpage using Gemini API"""
        if not self.gemini_model:
            print("❌ Gemini API not available. Please set GEMINI_API_KEY in .env file.")
            return
        
        try:
            print("🔍 Getting current webpage URL...")
            url = self.get_current_chrome_url()
            
            if not url:
                print("❌ Could not get current URL. Make sure Chrome is open with a webpage loaded.")
                return
            
            if url.startswith('chrome://') or url.startswith('about:') or url == 'chrome://newtab/':
                print("⚠️ Cannot summarize Chrome internal pages. Please navigate to a regular webpage.")
                return
            
            print(f"📄 Summarizing webpage: {url}")
            print("⏳ This may take a moment...")
            
            try:
                import requests
                from bs4 import BeautifulSoup
                
                print("📥 Fetching webpage content...")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                    script.decompose()
                
                text_content = soup.get_text()
                lines = (line.strip() for line in text_content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text_content = ' '.join(chunk for chunk in chunks if chunk)
                
                if len(text_content) > 50000:
                    text_content = text_content[:50000] + "... [content truncated]"
                
                print(f"✅ Fetched {len(text_content)} characters of content")
                
                prompt = f"""Please analyze and summarize the following webpage content from {url}:

{text_content}

Provide a comprehensive summary including:
- Main topic and purpose
- Key points and important information
- Any notable details or insights
- Overall conclusion or takeaways

Be thorough and accurate in your summary."""
                
                gemini_response = self.gemini_model.generate_content(prompt)
                summary_text = gemini_response.text
                
            except ImportError:
                print("⚠️ requests/BeautifulSoup not available. Trying direct URL...")
                prompt = f"""Please fetch and analyze the content from this URL: {url}

Then provide a comprehensive summary of the document/page including:
- Main topic and purpose
- Key points and important information
- Any notable details or insights
- Overall conclusion or takeaways

Be thorough and accurate in your summary."""
                
                gemini_response = self.gemini_model.generate_content(prompt)
                summary_text = gemini_response.text
                
            except Exception as fetch_error:
                print(f"⚠️ Could not fetch webpage content: {fetch_error}")
                print("💡 Trying to summarize using URL directly...")
                
                prompt = f"""Please fetch and analyze the content from this URL: {url}

Then provide a comprehensive summary of the document/page including:
- Main topic and purpose
- Key points and important information
- Any notable details or insights
- Overall conclusion or takeaways

Be thorough and accurate in your summary."""
                
                gemini_response = self.gemini_model.generate_content(prompt)
                summary_text = gemini_response.text
            
            response_text = summary_text
            
            print("\n📋 Document Summary:")
            print("=" * 60)
            print(f"🌐 URL: {url}")
            print("-" * 60)
            print(response_text)
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Failed to summarize page: {e}")
            import traceback
            traceback.print_exc()
            print("\n💡 Tip: Make sure the webpage is publicly accessible and not behind a login.")
    
    def search_word_meaning(self, word):
        """Search for the meaning of a word in Chrome"""
        try:
            print(f"📚 Searching meaning of: '{word}'")
            
            if not self.find_chrome_window():
                print("🌐 Opening Chrome...")
                self.open_chrome()
                time.sleep(3)
            
            if not self.focus_chrome_window():
                print("⚠️ Could not focus Chrome. Please ensure Chrome is open.")
                return
            
            search_query = f"meaning of {word}"
            
            self._search_with_pyautogui(search_query)
            
            print(f"✅ Search completed for meaning of '{word}'")
            
        except Exception as e:
            print(f"❌ Failed to search word meaning: {e}")
    
    def stop_listening(self):
        """Stop the voice command listener"""
        print("🛑 Stopping voice command listener...")
        self.listening = False
        
        if self.driver:
            self.driver.quit()
        
        print("👋 Voice Browser Controller stopped!")
    
    def run(self):
        print("\n🚀 Starting Voice Browser Controller...")
        self.active = True
        self.listening = True   
        try:
            self.listen_for_commands()
        except Exception as e:
            print(f"❌ Fatal error: {e}")
        finally:
            self.active = False
            print("🧩 Voice controller stopped gracefully.")

    def stop(self):
        """🛑 Gracefully stop voice recognition and browser control"""
        print("🧹 Stopping VoiceBrowserController...")
        self.listening = False 

        try:
            if hasattr(self, "stop_listening_fn") and self.stop_listening_fn:
                    self.stop_listening_fn(wait_for_stop=False)
                    print("🎙️ Microphone listener stopped")

            if self.driver:
                self.driver.quit()
                self.driver = None
                print("✅ Browser closed cleanly")
        except Exception as e:
            print(f"⚠️ Error during stop: {e}")

        print("🔇 Voice recognition stopped.")



def main():
    """Main function to run the voice browser controller"""
    print("=" * 60)
    print("🎤 VOICE-CONTROLLED BROWSER AUTOMATION")
    print("=" * 60)
    
    print("🔧 Checking dependencies...")
    
    try:
        import speech_recognition
        print("✅ SpeechRecognition available")
    except ImportError:
        print("❌ SpeechRecognition not found. Install with: pip install SpeechRecognition")
        return
    
    try:
        import pyautogui
        print("✅ PyAutoGUI available")
    except ImportError:
        print("❌ PyAutoGUI not found. Install with: pip install PyAutoGUI")
        return
    
    try:
        import selenium
        print("✅ Selenium available")
    except ImportError:
        print("⚠️ Selenium not found. Install with: pip install selenium")
        print("📝 Will use PyAutoGUI fallback for browser control")
    
    controller = VoiceBrowserController()
    controller.run()

if __name__ == "__main__":
    main()
