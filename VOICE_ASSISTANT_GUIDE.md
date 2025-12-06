# 🤖 Voice Assistant - Full Laptop Control Guide

## Overview

Your project now includes a **full voice assistant** that can control your entire laptop, not just the browser! This is like having an "Alexa for your laptop" - you can operate almost anything by voice.

## 🚀 Quick Start

### Option 1: Standalone Script (Recommended for Testing)

```bash
cd backend/services
python run_voice_assistant.py
```

### Option 2: Via Flask API

Start the Flask server and use the new endpoint:

```bash
# Start Flask server
cd backend
python app.py

# Then call the API endpoint
POST http://localhost:5000/control/voice/assistant/start
```

### Option 3: Via Frontend

The frontend can be updated to include a toggle for "Full Assistant Mode" vs "Browser Only Mode".

## 📋 Available Commands

### 🎯 Application Launching
- **"Open [app name]"** - Launch any application
  - Examples: "Open Chrome", "Open Word", "Open Notepad", "Open Calculator"
  - Works with: Word, Excel, PowerPoint, Chrome, Edge, Notepad, Calculator, VS Code, Cursor, and more

### 📁 File System Operations
- **"Open This PC"** or **"Open File Explorer"** - Open Windows File Explorer
- **"Open Desktop"** - Navigate to Desktop folder
- **"Open Documents"** - Navigate to Documents folder
- **"Open Downloads"** - Navigate to Downloads folder
- **"Open Pictures"** - Navigate to Pictures folder
- **"Go to [folder name]"** - Navigate to any folder
- **"Search for [file name]"** - Find files on your computer
  - Example: "Search for budget.xlsx"

### 🪟 Window Management
- **"Switch to [window name]"** - Switch to a specific window
  - Example: "Switch to Chrome"
- **"List windows"** - Show all open windows
- **"Focus [window name]"** - Bring a window to front

### 💻 System Information
- **"System status"** or **"System info"** - Get CPU, memory, disk usage
- **"Battery status"** - Check battery level and charging status
- **"How is my computer"** - Get system health overview

### 🔒 System Actions
- **"Lock screen"** - Lock your computer
- **"Sleep"** - Put computer to sleep
- **"Shutdown"** - Shutdown computer (use with caution!)
- **"Restart"** - Restart computer

### 🌐 Browser Commands (All Previous Commands Still Work!)
- All browser commands from the original voice control still work:
  - "Open Chrome"
  - "Search [query]"
  - "Minimize Chrome"
  - "Maximize window"
  - "Scroll down/up"
  - "Play video" / "Pause video"
  - "What's on my screen?"
  - "Summarize document"
  - And many more!

## 🎤 How It Works

1. **Speech Recognition**: Uses Google Speech Recognition to convert your voice to text
2. **Intent Parsing**: The Intent Router analyzes your command and determines what you want to do
3. **Action Execution**: The System Controller performs the requested action
4. **Voice Feedback**: Text-to-speech confirms actions (optional)

## 🔧 Configuration

### Customizing App Mappings

Edit `backend/services/app_config.json` to add custom application paths:

```json
{
  "app_mappings": {
    "myapp": "C:\\Path\\To\\MyApp.exe",
    "custom": "C:\\Program Files\\Custom\\app.exe"
  }
}
```

The system will auto-detect applications if paths don't exist.

### Adjusting TTS Settings

In `backend/services/voice_assistant.py`, you can modify:

```python
self.tts_engine.setProperty('rate', 150)  # Speech speed (default: 150)
self.tts_engine.setProperty('volume', 0.8)  # Volume (0.0 to 1.0)
```

## 📝 Example Usage Scenarios

### Scenario 1: Morning Routine
```
You: "Open Chrome"
Assistant: "✅ Launched Chrome"

You: "Search weather today"
Assistant: [Opens Google and searches]

You: "Open This PC"
Assistant: "✅ Opened This PC"

You: "Go to Documents"
Assistant: "✅ Opened Documents"
```

### Scenario 2: File Management
```
You: "Search for report.docx"
Assistant: "✅ Found 3 file(s). Opened folder containing: report.docx"

You: "Open Desktop"
Assistant: "✅ Opened Desktop"

You: "Switch to Chrome"
Assistant: "✅ Switched to Chrome"
```

### Scenario 3: System Check
```
You: "System status"
Assistant: "💻 System Information:
   CPU Usage: 25.3%
   Memory Usage: 45.2%
   Disk Usage: 67.8%
   Battery: 85% (plugged in)"

You: "Battery status"
Assistant: "✅ Battery: 85% (plugged in)"
```

## 🛠️ Architecture

The voice assistant consists of three main components:

1. **`system_control.py`**: Handles all system operations (apps, files, windows, system info)
2. **`intent_router.py`**: Parses natural language and routes to appropriate handlers
3. **`voice_assistant.py`**: Main orchestrator that combines everything

## 🔐 Security Notes

⚠️ **Important**: Commands like "shutdown" and "restart" will actually shut down/restart your computer! Use with caution.

The system includes safeguards, but always be careful with system-level commands.

## 🐛 Troubleshooting

### "Could not find application: [app name]"
- The app might not be installed in the default location
- Add a custom mapping in `app_config.json`
- Or use the full path: "Open C:\Path\To\App.exe"

### TTS Not Working
- Install `pyttsx3`: `pip install pyttsx3`
- On Windows, ensure you have SAPI5 voices installed
- TTS is optional - commands still work without it

### Commands Not Recognized
- Speak clearly and wait for the beep
- Use the exact command phrases shown above
- Check microphone permissions

## 🚀 Future Enhancements

Potential additions:
- Custom command training
- Multi-language support
- Context-aware commands (remember previous actions)
- Integration with more system settings
- Calendar and email control
- Smart home device control

## 📚 Related Files

- `backend/services/voice_assistant.py` - Main assistant
- `backend/services/system_control.py` - System operations
- `backend/services/intent_router.py` - Command parsing
- `backend/services/voice_browser_control.py` - Browser control (integrated)
- `backend/services/app_config.json` - App configuration

---

**Enjoy your voice-controlled laptop! 🎉**

