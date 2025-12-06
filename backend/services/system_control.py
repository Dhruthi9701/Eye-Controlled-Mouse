"""
System Control Module - Handles system-wide operations like file management,
application launching, system information, and Windows-specific operations.
"""

import os
import subprocess
import win32gui
import win32con
import pyautogui
import time
import psutil
import shutil
from pathlib import Path
import json

class SystemController:
    """Main system controller for laptop-wide operations"""
    
    def __init__(self):
        """Initialize system controller"""
        self.app_mappings = self._load_app_mappings()
        self.special_paths = self._get_special_paths()
        print("✅ System Controller initialized")
    
    def _load_app_mappings(self):
        """Load application name mappings to executable paths"""
        # Try to load from config file first
        config_path = os.path.join(os.path.dirname(__file__), "app_config.json")
        mappings = {}
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    if "app_mappings" in config:
                        mappings.update(config["app_mappings"])
                        print(f"✅ Loaded {len(mappings)} app mappings from config")
            except Exception as e:
                print(f"⚠️ Could not load app_config.json: {e}")
        
        # Common Windows applications (fallback/defaults)
        default_mappings = {
            # Microsoft Office
            "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
            "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
            "powerpoint": r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
            "outlook": r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
            
            # Browsers
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
            
            # Development Tools
            "notepad": "notepad.exe",
            "notepad++": r"C:\Program Files\Notepad++\notepad++.exe",
            "vscode": r"C:\Users\{}\AppData\Local\Programs\Microsoft VS Code\Code.exe".format(os.getenv('USERNAME', '')),
            "cursor": r"C:\Users\{}\AppData\Local\Programs\cursor\Cursor.exe".format(os.getenv('USERNAME', '')),
            
            # System Tools
            "calculator": "calc.exe",
            "task manager": "taskmgr.exe",
            "control panel": "control.exe",
            "settings": "ms-settings:",
            "file explorer": "explorer.exe",
            "this pc": "explorer.exe",
            "command prompt": "cmd.exe",
            "powershell": "powershell.exe",
            
            # Media
            "spotify": r"C:\Users\{}\AppData\Roaming\Spotify\Spotify.exe".format(os.getenv('USERNAME', '')),
            "vlc": r"C:\Program Files\VideoLAN\VLC\vlc.exe",
            
            # Communication
            "teams": r"C:\Users\{}\AppData\Local\Microsoft\Teams\current\Teams.exe".format(os.getenv('USERNAME', '')),
            "discord": r"C:\Users\{}\AppData\Local\Discord\app-*\Discord.exe".format(os.getenv('USERNAME', '')),
            "zoom": r"C:\Users\{}\AppData\Roaming\Zoom\bin\Zoom.exe".format(os.getenv('USERNAME', '')),
        }
        
        # Merge defaults with config (config takes precedence)
        for key, value in default_mappings.items():
            if key not in mappings:
                mappings[key] = value
        
        # Try to find actual paths and update mappings
        for app_name, path_template in list(mappings.items()):
            if "{}" in path_template:
                try:
                    actual_path = path_template.format(os.getenv('USERNAME', ''))
                    if os.path.exists(actual_path):
                        mappings[app_name] = actual_path
                    else:
                        # Try to find in common locations
                        found = self._find_app_path(app_name)
                        if found:
                            mappings[app_name] = found
                except:
                    pass
            elif not os.path.exists(path_template) and not path_template.endswith('.exe'):
                # Try to find the app
                found = self._find_app_path(app_name)
                if found:
                    mappings[app_name] = found
        
        return mappings
    
    def _find_app_path(self, app_name):
        """Try to find application path in common locations"""
        common_paths = [
            r"C:\Program Files",
            r"C:\Program Files (x86)",
            r"C:\Users\{}\AppData\Local\Programs".format(os.getenv('USERNAME', '')),
            r"C:\Users\{}\AppData\Roaming".format(os.getenv('USERNAME', '')),
        ]
        
        for base_path in common_paths:
            if not os.path.exists(base_path):
                continue
            for root, dirs, files in os.walk(base_path):
                for file in files:
                    if app_name.lower() in file.lower() and file.endswith('.exe'):
                        full_path = os.path.join(root, file)
                        if os.path.exists(full_path):
                            return full_path
        return None
    
    def _get_special_paths(self):
        """Get Windows special folder paths"""
        return {
            "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
            "documents": os.path.join(os.path.expanduser("~"), "Documents"),
            "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
            "pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
            "videos": os.path.join(os.path.expanduser("~"), "Videos"),
            "music": os.path.join(os.path.expanduser("~"), "Music"),
            "this pc": "::{20D04FE0-3AEA-1069-A2D8-08002B30309D}",
            "my computer": "::{20D04FE0-3AEA-1069-A2D8-08002B30309D}",
            "recycle bin": "::{645FF040-5081-101B-9F08-00AA002F954E}",
            "control panel": "::{21EC2020-3AEA-1069-A2DD-08002B30309D}",
        }
    
    # ==================== APPLICATION LAUNCHING ====================
    
    def launch_app(self, app_name):
        """Launch an application by name"""
        try:
            app_name_lower = app_name.lower().strip()
            
            # Check direct mappings
            if app_name_lower in self.app_mappings:
                path = self.app_mappings[app_name_lower]
                if path.startswith("ms-settings:"):
                    # Windows Settings app
                    subprocess.Popen(["start", path], shell=True)
                elif os.path.exists(path) or path.endswith('.exe'):
                    subprocess.Popen([path])
                    return f"✅ Launched {app_name}"
                else:
                    # Try as command
                    subprocess.Popen([path], shell=True)
                    return f"✅ Launched {app_name}"
            
            # Try to find and launch
            found_path = self._find_app_path(app_name_lower)
            if found_path:
                subprocess.Popen([found_path])
                return f"✅ Launched {app_name}"
            
            # Try as direct command
            try:
                subprocess.Popen([app_name_lower], shell=True)
                return f"✅ Launched {app_name}"
            except:
                return f"❌ Could not find application: {app_name}"
                
        except Exception as e:
            return f"❌ Failed to launch {app_name}: {e}"
    
    # ==================== FILE SYSTEM OPERATIONS ====================
    
    def open_file_explorer(self, path_name=None):
        """Open File Explorer to a specific location"""
        try:
            if path_name:
                path_name_lower = path_name.lower().strip()
                
                # Check special paths
                if path_name_lower in self.special_paths:
                    target = self.special_paths[path_name_lower]
                    if target.startswith("::"):
                        # Special Windows folder (CLSID)
                        subprocess.Popen(["explorer.exe", target])
                    else:
                        subprocess.Popen(["explorer.exe", target])
                    return f"✅ Opened {path_name}"
                
                # Try as direct path
                if os.path.exists(path_name):
                    subprocess.Popen(["explorer.exe", path_name])
                    return f"✅ Opened {path_name}"
                
                # Try to find folder
                found = self._find_folder(path_name_lower)
                if found:
                    subprocess.Popen(["explorer.exe", found])
                    return f"✅ Opened {path_name}"
                
                return f"❌ Could not find location: {path_name}"
            else:
                # Open This PC
                subprocess.Popen(["explorer.exe", self.special_paths["this pc"]])
                return "✅ Opened This PC"
                
        except Exception as e:
            return f"❌ Failed to open file explorer: {e}"
    
    def _find_folder(self, folder_name):
        """Find a folder by name in common locations"""
        search_locations = [
            os.path.expanduser("~"),
            "C:\\",
        ]
        
        folder_name_lower = folder_name.lower()
        
        for location in search_locations:
            if not os.path.exists(location):
                continue
            try:
                for root, dirs, files in os.walk(location):
                    for dir_name in dirs:
                        if folder_name_lower in dir_name.lower():
                            full_path = os.path.join(root, dir_name)
                            if os.path.isdir(full_path):
                                return full_path
                    # Limit depth to avoid long searches
                    if root.count(os.sep) > 3:
                        dirs[:] = []  # Don't go deeper
            except PermissionError:
                continue
        
        return None
    
    def search_files(self, query, location=None):
        """Search for files by name"""
        try:
            search_path = location if location and os.path.exists(location) else os.path.expanduser("~")
            
            results = []
            query_lower = query.lower()
            
            # Search in the specified location
            try:
                for root, dirs, files in os.walk(search_path):
                    # Search in filenames
                    for file in files:
                        if query_lower in file.lower():
                            results.append(os.path.join(root, file))
                            if len(results) >= 10:  # Limit results
                                break
                    
                    if len(results) >= 10:
                        break
                    
                    # Limit depth
                    if root.count(os.sep) > 5:
                        dirs[:] = []
            except PermissionError:
                pass
            
            if results:
                # Open first result's folder
                first_result = results[0]
                folder_path = os.path.dirname(first_result)
                subprocess.Popen(["explorer.exe", folder_path])
                return f"✅ Found {len(results)} file(s). Opened folder containing: {os.path.basename(first_result)}"
            else:
                return f"❌ No files found matching: {query}"
                
        except Exception as e:
            return f"❌ Failed to search files: {e}"
    
    def open_file(self, file_path):
        """Open a file with its default application"""
        try:
            if os.path.exists(file_path):
                os.startfile(file_path)
                return f"✅ Opened {os.path.basename(file_path)}"
            else:
                return f"❌ File not found: {file_path}"
        except Exception as e:
            return f"❌ Failed to open file: {e}"
    
    # ==================== SYSTEM INFORMATION ====================
    
    def get_system_info(self):
        """Get system information"""
        try:
            info = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('C:\\').percent,
                "battery": None,
            }
            
            # Battery info (if available)
            try:
                battery = psutil.sensors_battery()
                if battery:
                    info["battery"] = {
                        "percent": battery.percent,
                        "plugged": battery.power_plugged,
                    }
            except:
                pass
            
            return info
        except Exception as e:
            return {"error": str(e)}
    
    def get_system_info_text(self):
        """Get system information as readable text"""
        try:
            info = self.get_system_info()
            if "error" in info:
                return f"❌ Error getting system info: {info['error']}"
            
            text = f"💻 System Information:\n"
            text += f"   CPU Usage: {info['cpu_percent']:.1f}%\n"
            text += f"   Memory Usage: {info['memory_percent']:.1f}%\n"
            text += f"   Disk Usage: {info['disk_usage']:.1f}%"
            
            if info.get("battery"):
                battery = info["battery"]
                status = "plugged in" if battery["plugged"] else "on battery"
                text += f"\n   Battery: {battery['percent']:.0f}% ({status})"
            
            return text
        except Exception as e:
            return f"❌ Failed to get system info: {e}"
    
    # ==================== WINDOW MANAGEMENT ====================
    
    def get_all_windows(self):
        """Get list of all open windows"""
        windows = []
        
        def enum_windows_callback(hwnd, window_list):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    title = win32gui.GetWindowText(hwnd)
                    if title:
                        window_list.append((hwnd, title))
                except:
                    pass
            return True
        
        win32gui.EnumWindows(enum_windows_callback, windows)
        return windows
    
    def switch_to_window(self, window_name):
        """Switch to a window by name"""
        try:
            windows = self.get_all_windows()
            window_name_lower = window_name.lower()
            
            for hwnd, title in windows:
                if window_name_lower in title.lower():
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.SetForegroundWindow(hwnd)
                    return f"✅ Switched to {title}"
            
            return f"❌ Window not found: {window_name}"
        except Exception as e:
            return f"❌ Failed to switch window: {e}"
    
    def list_open_windows(self):
        """List all open windows"""
        try:
            windows = self.get_all_windows()
            if windows:
                window_list = "\n".join([f"   • {title}" for hwnd, title in windows[:10]])
                return f"📋 Open Windows:\n{window_list}"
            else:
                return "❌ No open windows found"
        except Exception as e:
            return f"❌ Failed to list windows: {e}"
    
    # ==================== SYSTEM ACTIONS ====================
    
    def lock_screen(self):
        """Lock the Windows screen"""
        try:
            subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
            return "✅ Screen locked"
        except Exception as e:
            return f"❌ Failed to lock screen: {e}"
    
    def sleep_system(self):
        """Put system to sleep"""
        try:
            subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
            return "✅ System going to sleep"
        except Exception as e:
            return f"❌ Failed to sleep system: {e}"
    
    def shutdown_system(self, delay=0):
        """Shutdown system (with optional delay in seconds)"""
        try:
            if delay > 0:
                subprocess.Popen(["shutdown", "/s", "/t", str(delay)])
                return f"✅ System will shutdown in {delay} seconds"
            else:
                subprocess.Popen(["shutdown", "/s", "/t", "0"])
                return "✅ System shutting down"
        except Exception as e:
            return f"❌ Failed to shutdown: {e}"
    
    def restart_system(self, delay=0):
        """Restart system (with optional delay in seconds)"""
        try:
            if delay > 0:
                subprocess.Popen(["shutdown", "/r", "/t", str(delay)])
                return f"✅ System will restart in {delay} seconds"
            else:
                subprocess.Popen(["shutdown", "/r", "/t", "0"])
                return "✅ System restarting"
        except Exception as e:
            return f"❌ Failed to restart: {e}"
    
    # ==================== DESKTOP INTERACTIONS ====================
    
    def show_desktop(self):
        """Show desktop (minimize all windows)"""
        try:
            pyautogui.hotkey('win', 'd')
            return "✅ Showing desktop"
        except Exception as e:
            return f"❌ Failed to show desktop: {e}"
    
    def right_click_at_cursor(self):
        """Right-click at current cursor position"""
        try:
            current_x, current_y = pyautogui.position()
            pyautogui.rightClick(current_x, current_y)
            return "✅ Right-clicked at cursor position"
        except Exception as e:
            return f"❌ Failed to right-click: {e}"
    
    def double_click_at_cursor(self):
        """Double-click at current cursor position"""
        try:
            current_x, current_y = pyautogui.position()
            pyautogui.doubleClick(current_x, current_y)
            return "✅ Double-clicked at cursor position"
        except Exception as e:
            return f"❌ Failed to double-click: {e}"
    
    def open_desktop_icon(self, icon_name):
        """Open a desktop icon by name"""
        try:
            # First, show desktop
            pyautogui.hotkey('win', 'd')
            time.sleep(0.5)
            
            # Try to find and click the icon
            # This is a simplified approach - searches for icon by typing name
            # Note: This works best if desktop icons are arranged in a grid
            
            # Use Windows search to find and open
            pyautogui.hotkey('win')
            time.sleep(0.3)
            pyautogui.typewrite(icon_name, interval=0.1)
            time.sleep(0.5)
            pyautogui.press('enter')
            
            return f"✅ Opened {icon_name}"
        except Exception as e:
            return f"❌ Failed to open desktop icon: {e}"
    
    def refresh_desktop(self):
        """Refresh desktop (F5)"""
        try:
            # Show desktop first
            pyautogui.hotkey('win', 'd')
            time.sleep(0.3)
            # Press F5 to refresh
            pyautogui.press('f5')
            return "✅ Desktop refreshed"
        except Exception as e:
            return f"❌ Failed to refresh desktop: {e}"

