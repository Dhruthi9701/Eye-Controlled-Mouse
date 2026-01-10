"""
Parses natural language commands and routes them to appropriate handlers.
This enables natural language understanding for system-wide voice commands.
"""

import re
from typing import Dict, Tuple, Optional

class IntentRouter:
    """Routes voice commands to appropriate system actions"""
    
    def __init__(self):
        """Initialize intent router with command patterns"""
        self.patterns = self._initialize_patterns()
    
    def _initialize_patterns(self):
        """Initialize command patterns for intent recognition"""
        return {
        
            "launch_app": [
                r"open\s+(.+)",
                r"launch\s+(.+)",
                r"start\s+(.+)",
                r"run\s+(.+)",
            ],
      
            "open_location": [
                r"open\s+(?:file\s+)?explorer",
                r"open\s+this\s+pc",
                r"open\s+my\s+computer",
                r"show\s+me\s+(?:the\s+)?(desktop|documents|downloads|pictures|videos|music)",
                r"go\s+to\s+(desktop|documents|downloads|pictures|videos|music)",
                r"open\s+(desktop|documents|downloads|pictures|videos|music)",
                r"navigate\s+to\s+(.+)",
                r"go\s+to\s+(.+)",
            ],
            
            "search_files": [
                r"search\s+for\s+(?:file\s+)?(.+)",
                r"find\s+(?:file\s+)?(.+)",
                r"look\s+for\s+(?:file\s+)?(.+)",
                r"where\s+is\s+(.+)",
            ],
     
            "switch_window": [
                r"switch\s+to\s+(.+)",
                r"go\s+to\s+(.+)",
                r"focus\s+(.+)",
                r"bring\s+(.+)",
            ],
            "list_windows": [
                r"list\s+(?:open\s+)?windows",
                r"show\s+(?:me\s+)?(?:open\s+)?windows",
                r"what\s+windows\s+are\s+open",
            ],
           
            "system_info": [
                r"(?:what\s+is\s+)?(?:the\s+)?system\s+(?:status|info|information)",
                r"how\s+is\s+(?:the\s+)?(?:system|computer|pc|laptop)",
                r"system\s+health",
                r"computer\s+status",
                r"show\s+me\s+(?:the\s+)?(?:system|computer)\s+(?:status|info)",
            ],
            "battery_status": [
                r"(?:what\s+is\s+)?(?:the\s+)?battery\s+(?:level|status|percent)",
                r"how\s+much\s+battery",
                r"battery\s+info",
            ],
            
       
            "lock_screen": [
                r"lock\s+(?:the\s+)?(?:screen|computer|pc|laptop)",
                r"lock\s+system",
            ],
            "sleep": [
                r"sleep",
                r"put\s+(?:the\s+)?(?:computer|pc|laptop|system)\s+to\s+sleep",
                r"sleep\s+(?:the\s+)?(?:computer|pc|laptop|system)",
            ],
            "shutdown": [
                r"shutdown",
                r"shut\s+down",
                r"turn\s+off\s+(?:the\s+)?(?:computer|pc|laptop)",
                r"power\s+off",
            ],
            "restart": [
                r"restart",
                r"reboot",
                r"restart\s+(?:the\s+)?(?:computer|pc|laptop)",
            ],
         
            "show_desktop": [
                r"show\s+desktop",
                r"show\s+me\s+the\s+desktop",
                r"minimize\s+all",
                r"hide\s+all\s+windows",
            ],
            "right_click": [
                r"right\s+click",
                r"right\s+click\s+here",
            ],
            "double_click": [
                r"double\s+click",
                r"double\s+click\s+here",
            ],
            "open_desktop_icon": [
                r"open\s+desktop\s+icon\s+(.+)",
                r"open\s+(.+)\s+on\s+desktop",
                r"launch\s+desktop\s+(.+)",
            ],
            "refresh_desktop": [
                r"refresh\s+desktop",
                r"refresh",
            ],
        }
    
    def parse_intent(self, command: str) -> Tuple[Optional[str], Dict]:
        """
        Parse a voice command and return intent type and extracted parameters
        
        Returns:
            Tuple of (intent_type, parameters_dict)
        """
        command = command.strip().lower()
     
        for intent_type, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    params = self._extract_parameters(intent_type, match, command)
                    return intent_type, params
        
        return None, {}
    
    def _extract_parameters(self, intent_type: str, match: re.Match, full_command: str) -> Dict:
        """Extract parameters from matched pattern"""
        params = {}
        
        if intent_type == "launch_app":
   
            if match.groups():
                app_name = match.group(1).strip()
    
                app_name = re.sub(r"^(?:the\s+)?(?:application\s+)?", "", app_name, flags=re.IGNORECASE)
                params["app_name"] = app_name
        
        elif intent_type == "open_location":
        
            if match.groups():
                location = match.group(1).strip() if len(match.groups()) > 0 else None
                if location:
                    params["location"] = location
            else:
         
                if "this pc" in full_command or "my computer" in full_command:
                    params["location"] = "this pc"
                elif "file explorer" in full_command or "explorer" in full_command:
                    params["location"] = None 
        
        elif intent_type == "search_files":
            if match.groups():
                query = match.group(1).strip()
                params["query"] = query
        
        elif intent_type == "switch_window":
            if match.groups():
                window_name = match.group(1).strip()
                params["window_name"] = window_name
        
        elif intent_type in ["shutdown", "restart"]:
    
            delay_match = re.search(r"(\d+)\s*(?:seconds?|secs?|minutes?|mins?)", full_command)
            if delay_match:
                delay = int(delay_match.group(1))
          
                if "minute" in delay_match.group(0) or "min" in delay_match.group(0):
                    delay *= 60
                params["delay"] = delay
        
        elif intent_type == "open_desktop_icon":
            if match.groups():
                icon_name = match.group(1).strip()
                params["icon_name"] = icon_name
        
        return params
    
    def get_intent_description(self, intent_type: str) -> str:
        """Get human-readable description of an intent"""
        descriptions = {
            "launch_app": "Launch an application",
            "open_location": "Open a file location",
            "search_files": "Search for files",
            "switch_window": "Switch to a window",
            "list_windows": "List open windows",
            "system_info": "Get system information",
            "battery_status": "Get battery status",
            "lock_screen": "Lock the screen",
            "sleep": "Put system to sleep",
            "shutdown": "Shutdown system",
            "restart": "Restart system",
            "show_desktop": "Show desktop",
            "right_click": "Right-click at cursor",
            "double_click": "Double-click at cursor",
            "open_desktop_icon": "Open desktop icon",
            "refresh_desktop": "Refresh desktop",
        }
        return descriptions.get(intent_type, "Unknown intent")

