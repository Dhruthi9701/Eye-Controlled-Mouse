# Complete Project Functionality Summary

## Eye-Controlled Mouse with Voice Commands for Browser Automation

A comprehensive accessibility system that combines **eye tracking**, **voice commands**, and **hand gesture controls** to enable hands-free computer interaction.

---

## 🎯 Core Features Overview

### 1. **Eye Tracking System** 👁️
- **Real-time gaze tracking** using MediaPipe Face Mesh
- **Cursor control** via eye movements
- **Blink-to-click** functionality
- **Advanced calibration** with multiple mapping methods
- **Adaptive learning** for improved accuracy over time
- **Kalman filtering** for smooth cursor movement
- **Head pose compensation** for better accuracy
- **Attention score tracking** based on blink detection

### 2. **Voice Browser Control** 🎤
- **30+ voice commands** for browser automation
- **Chrome browser control** (open, close, tab management)
- **Google search** via voice commands
- **Video control** (play/pause on YouTube and HTML5)
- **Screen analysis** using Gemini AI 2.0 Flash
- **Document summarization** from web pages
- **Window management** (minimize/maximize)

### 3. **Hand Gesture Controls** ✋
- **Pinch gesture** for volume control
- **Palm gesture** for screenshot capture
- **Real-time hand tracking** using MediaPipe Hands

### 4. **Web Interface** 🌐
- **React-based frontend** for system control
- **Toggle switches** for enabling/disabling features
- **Real-time status** indicators
- **Feature flag system** for optional features

---

## 📋 Detailed Functionality

### 👁️ Eye Tracking Features

#### Core Capabilities
1. **Gaze Point Detection**
   - Detects iris position in both eyes
   - Maps gaze coordinates to screen coordinates
   - Uses calibrated transformation matrices

2. **Calibration System**
   - Multi-point calibration process
   - Saves calibration data to JSON files
   - Supports recalibration anytime
   - Multiple calibration methods (affine, perspective, polynomial)

3. **Cursor Control**
   - Smooth cursor movement following gaze
   - Adaptive smoothing for accuracy
   - Acceleration for large movements
   - Screen boundary checking

4. **Blink Detection**
   - Monitors blink ratio using eye landmarks
   - Deliberate blink recognition for clicking
   - Attention score calculation based on blink frequency

5. **Advanced Features**
   - Kalman filter for gaze prediction
   - Head pose estimation and compensation
   - Confidence scoring for measurements
   - Historical data tracking with deques

---

### 🎤 Voice Commands (30+ Commands)

#### Browser Control
1. **"Open Chrome"** - Launches Chrome browser
2. **"Close browser"** - Closes entire browser
3. **"Open another tab" / "New tab"** - Opens new tab
4. **"Close tab"** - Closes current tab
5. **"Go back" / "Back"** - Navigates to previous webpage

#### Search Commands
6. **"Search [query]"** - Searches Google with query
7. **"Search"** (two-step) - Activates search mode, then accepts query
8. **"Search for [query]"** - Alternative search command
9. **"Search meaning of [word]"** - Searches for word meaning

#### Screen Analysis (Gemini AI)
10. **"What's on my screen?" / "Analyze screen"** - Analyzes and describes current screen
11. **"Ask about [question]" / "Ask [question]"** - Answers questions about visible screen
12. **"Summarise document" / "Summarise page"** - Summarizes current webpage using Gemini AI

#### Window Management
13. **"Minimize" / "Minimise"** - Minimizes active window
14. **"Minimize Chrome" / "Minimise Chrome"** - Minimizes Chrome specifically
15. **"Minimize cursor" / "Minimise cursor"** - Minimizes window under cursor
16. **"Minimize File Explorer" / "Minimise File Explorer"** - Minimizes File Explorer
17. **"Minimize window" / "Minimise window"** - Minimizes any window except Chrome/File Explorer
18. **"Maximize" / "Maximise"** - Maximizes active window
19. **"Maximize Chrome" / "Maximise Chrome"** - Maximizes Chrome specifically
20. **"Maximize cursor" / "Maximise cursor"** - Maximizes window under cursor
21. **"Maximize File Explorer" / "Maximise File Explorer"** - Maximizes File Explorer
22. **"Maximize window" / "Maximise window"** - Maximizes any window except Chrome/File Explorer

#### Scrolling
23. **"Scroll down"** - Scrolls down ~half page in active window/tab
24. **"Scroll up"** - Scrolls up ~half page in active window/tab
25. **"Scroll down more" / "Scroll more down"** - Scrolls down full visible page
26. **"Scroll up more" / "Scroll more up"** - Scrolls up full visible page

#### Mouse Control
27. **"Click"** - Clicks at current cursor position

#### Video Control
28. **"Play video" / "Play"** - Plays/resumes video (YouTube + HTML5)
29. **"Pause video" / "Pause"** - Pauses video

#### System
30. **"Stop listening" / "Exit"** - Exits the program

#### Additional Features
- Supports both **US and UK spellings** (minimize/minimise, maximize/maximise, summarize/summarise)
- **Current URL detection** from Chrome address bar
- **Webpage content fetching** for summarization
- **Active window detection** for context-aware actions

---

### ✋ Hand Gesture Controls

#### Volume Control (Pinch Gesture)
- Detects pinch gesture between thumb and index finger
- Controls system volume based on distance between fingers
- Real-time volume adjustment
- Visual feedback on camera feed

#### Screenshot Capture (Palm Gesture)
- Detects open palm gesture
- Captures screenshot when palm is shown
- Saves screenshots to designated folder
- Can work simultaneously with volume control

---

## 🏗️ System Architecture

### Backend (Flask + Python)
- **Flask REST API** for feature control
- **WebSocket support** via SocketIO (for real-time updates)
- **Feature flags** system for enabling/disabling features
- **Thread-based** service management
- **CORS enabled** for frontend communication

#### API Endpoints
- `POST /control/eye/start` - Start eye tracking
- `POST /control/eye/stop` - Stop eye tracking
- `POST /control/voice/start` - Start voice control
- `POST /control/voice/stop` - Stop voice control
- `POST /control/system/volume_start` - Start volume control
- `POST /control/system/volume_stop` - Stop volume control
- `POST /control/system/screenshot_start` - Start screenshot capture
- `POST /control/system/screenshot_stop` - Stop screenshot capture
- `POST /control/system/both_start` - Start both gestures
- `POST /control/system/both_stop` - Stop both gestures
- `GET /control/features` - Get available features

### Frontend (React)
- **React application** with modern UI components
- **Toggle switches** for feature control
- **Real-time status** updates
- **Loading states** during operations
- **Error handling** with user feedback

---

## 🔧 Technical Components

### Dependencies & Technologies

#### Python Backend
- **OpenCV** - Computer vision and camera handling
- **MediaPipe** - Face mesh, hand tracking
- **PyAutoGUI** - Mouse/keyboard automation
- **SpeechRecognition** - Voice command recognition
- **Selenium** - Browser automation (optional)
- **Flask** - Web server and API
- **Flask-SocketIO** - WebSocket support
- **Flask-CORS** - Cross-origin resource sharing
- **Google Generative AI** - Gemini API for screen analysis
- **NumPy** - Numerical computations
- **SciPy** - Scientific computing (calibration)

#### Frontend
- **React** - UI framework
- **Lucide React** - Icon library
- **Custom UI components** - Switches, buttons, etc.

---

## 🎯 Use Cases

### Primary Use Cases
1. **Accessibility Support**
   - Users with limited mobility
   - Hands-free computer interaction
   - Alternative input methods

2. **Productivity Enhancement**
   - Multitasking without using hands
   - Voice-controlled browsing
   - Quick window management

3. **Learning & Research**
   - Hands-free document reading
   - Voice-controlled web searches
   - AI-powered content summarization

4. **Media Consumption**
   - Hands-free video playback control
   - Gesture-based volume control
   - Screen capture for documentation

### Workflow Examples

#### Example 1: Web Research
1. Say **"Open Chrome"**
2. Use eyes to navigate
3. Say **"Search artificial intelligence"**
4. Use eyes to scroll and click
5. Say **"Summarise document"** on an article
6. Use eyes to navigate to another tab

#### Example 2: Video Watching
1. Say **"Open Chrome"**
2. Use eyes to navigate to YouTube
3. Say **"Play video"**
4. Use pinch gesture to adjust volume
5. Use palm gesture to capture screenshots

#### Example 3: Document Analysis
1. Say **"What's on my screen?"** for overview
2. Say **"Ask what is this document about?"** for details
3. Say **"Scroll down more"** to read more
4. Use eyes to highlight important sections

---

## 🔐 Configuration & Setup

### Environment Variables
- `GEMINI_API_KEY` - For Gemini AI features (screen analysis, summarization)
- Stored in `.env` file in `backend/services/` folder

### Feature Flags
- `eye_control` - Enable/disable eye tracking
- `voice_control` - Enable/disable voice commands
- Configurable in `backend/utils/feature_flags.py`

### Calibration Files
- Stored as JSON files with timestamp
- Format: `landmark_eye_calibration_YYYYMMDD_HHMMSS.json`
- Contains mapping matrices and calibration points

---

## 📊 Performance Features

### Eye Tracking
- **Real-time processing** at ~30 FPS
- **Low latency** cursor movement
- **Adaptive smoothing** for accuracy
- **Confidence-based** filtering

### Voice Control
- **Continuous listening** mode
- **Phrase time limits** for responsiveness
- **Ambient noise adjustment**
- **Timeout handling** for better UX

### Hand Gestures
- **Real-time tracking** at video frame rate
- **Gesture recognition** with confidence thresholds
- **Multi-hand support** (configurable)

---

## 🎨 User Interface

### Main Dashboard
- **Feature toggles** for each system
- **Status indicators** (active/inactive)
- **Loading states** during operations
- **Back navigation** to home

### Visual Feedback
- **Color-coded sections** (Eye=Yellow, Voice=Pink, Gestures=Blue)
- **Loading animations** during processing
- **Success/error messages** for user feedback

---

## 🔄 Integration Points

### System Integration
1. **Windows API** - Window management (minimize/maximize)
2. **Clipboard API** - URL copying
3. **Audio API** - Volume control
4. **Screen capture** - Screenshot functionality

### External Services
1. **Google Speech Recognition** - Voice-to-text
2. **Gemini AI API** - Screen analysis and summarization
3. **Chrome Browser** - Web automation
4. **MediaPipe** - Computer vision models

---

## 🛠️ Maintenance & Extensibility

### Easy to Extend
- **Modular design** with separate service files
- **Feature flag system** for experimental features
- **API-based architecture** for easy integration
- **Well-documented** code structure

### Error Handling
- **Graceful degradation** if services unavailable
- **User-friendly error messages**
- **Fallback mechanisms** (e.g., PyAutoGUI if Selenium fails)
- **Automatic cleanup** on errors

---

## 📈 Future Enhancement Possibilities

### Potential Additions
1. **More voice commands** for system control
2. **Additional gesture types** (swipe, point)
3. **Eye typing** system using on-screen keyboard
4. **Multi-language** voice support
5. **Custom command** creation
6. **Profile system** for user-specific calibrations
7. **Machine learning** improvements for accuracy
8. **Mobile app** companion
9. **Cloud sync** for calibration data
10. **Advanced analytics** and usage tracking

---

## 🎓 Key Technologies Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Eye Tracking | MediaPipe Face Mesh | Facial landmark detection |
| Voice Recognition | Google Speech Recognition | Voice-to-text conversion |
| Browser Automation | Selenium + PyAutoGUI | Web browser control |
| AI Analysis | Gemini 2.0 Flash | Screen understanding |
| Hand Tracking | MediaPipe Hands | Gesture recognition |
| Web Server | Flask + SocketIO | API and real-time updates |
| Frontend | React | User interface |
| Computer Vision | OpenCV | Image processing |
| Mouse Control | PyAutoGUI | Cursor automation |

---

## 📝 Summary

This project provides a **complete hands-free computing solution** combining:
- 👁️ **Eye tracking** for cursor control and clicking
- 🎤 **Voice commands** for 30+ browser and system actions
- ✋ **Hand gestures** for volume and screenshots
- 🤖 **AI-powered** screen analysis and document summarization
- 🌐 **Web interface** for easy feature management

The system is designed for **accessibility**, **productivity**, and **hands-free interaction**, making it suitable for users with mobility limitations or anyone wanting to interact with their computer in new ways.

