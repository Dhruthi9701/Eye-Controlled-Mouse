# 📖 **USER HANDBOOK**
## **Eye and Voice Integration with HCI - Quick Start Guide**

---

## 🎯 **GETTING STARTED**

### **System Requirements:**
- ✅ Webcam (for eye tracking & gestures)
- ✅ Microphone (for voice commands)
- ✅ Good lighting conditions
- ✅ Chrome browser installed

### **Launch the System:**
1. Open the React dashboard (http://localhost:3000)
2. Toggle ON the features you want to use
3. Wait for "Active" status before using

---

## 👁️ **EYE TRACKING MODULE**

### **How to Use:**
1. **Toggle ON** "Eye Control" in the dashboard
2. **Calibration Process:**
   - Look at the yellow crosshair in the camera window
   - **Option 1 - New Calibration:**
     - Press **'SPACE'** to start collecting data for each point
     - Follow the 25 calibration points on screen
     - Look directly at each point when it appears
     - Keep your head still during calibration
     - Calibration saves automatically
   - **Option 2 - Skip Calibration (Use Previous):**
     - Press **'S'** key to skip calibration
     - System will automatically load your previous calibration file
     - Useful when you haven't changed position
   - **Cancel:** Press **'ESC'** to cancel

3. **Control the Cursor:**
   - **Move cursor:** Look around the screen naturally
   - **Click:** Blink deliberately twice (double-blink within 600ms)
   - **Recalibrate:** Press **'C'** anytime if accuracy drops
   - **Exit:** Press **'Q'** or **'ESC'**

### **Tips for Best Performance:**
- ✅ Sit 50-70cm from the screen
- ✅ Ensure face is fully visible in camera
- ✅ Use good lighting (avoid backlighting)
- ✅ Keep head relatively still
- ✅ Recalibrate if you change position
- ✅ Use 'S' to skip calibration if you're in the same position

---

## 🎤 **VOICE CONTROL MODULE**

### **How to Use:**
1. **Toggle ON** "Voice Control" in the dashboard
2. **Speak clearly** after you hear the system listening
3. **Wait** for command confirmation

### **Voice Commands (30+ Available):**

#### **Browser Control:**
- "Open Chrome" - Launch browser
- "Close browser" - Close Chrome
- "Open another tab" / "New tab" - New browser tab
- "Close tab" - Close current tab
- "Go back" / "Back" - Previous page

#### **Search Commands:**
- "Search [your query]" - Google search
- "Search for [query]" - Alternative search
- "Search meaning of [word]" - Word definition

#### **AI-Powered Features:**
- "What's on my screen?" - Analyze screen content
- "Analyze screen" - Describe visible content
- "Ask about [question]" - Ask about screen
- "Summarise document" - Summarize webpage
- "Summarise page" - Summarize current page

#### **Window Management:**
- "Minimize" - Minimize active window
- "Minimize Chrome" - Minimize browser
- "Minimize cursor" - Minimize window under cursor
- "Maximize" - Maximize active window
- "Maximize Chrome" - Maximize browser
- "Maximize cursor" - Maximize window under cursor

#### **Scrolling:**
- "Scroll down" - Scroll half page down
- "Scroll up" - Scroll half page up
- "Scroll down more" - Scroll full page down
- "Scroll up more" - Scroll full page up

#### **Video Control:**
- "Play video" / "Play" - Play/resume video
- "Pause video" / "Pause" - Pause video

#### **Mouse Control:**
- "Click" - Click at cursor position

#### **System:**
- "Stop listening" / "Exit" - Stop voice control

### **Voice Tips:**
- ✅ Speak clearly and naturally
- ✅ Wait for listening indicator
- ✅ Use exact command phrases
- ✅ Minimize background noise
- ✅ Adjust microphone volume if needed

---

## ✋ **GESTURE CONTROL MODULE**

### **Volume Control (Pinch Gesture):**
1. **Toggle ON** "Volume Control" in dashboard
2. **Show your hand** to the camera
3. **Pinch gesture:** Bring thumb and index finger together
4. **Adjust volume:** 
   - Fingers close together = Low volume
   - Fingers far apart = High volume
5. **Exit:** Press **'ESC'** key

### **Screenshot Capture (Hand Gestures):**
1. **Toggle ON** "Screenshot Control" in dashboard
2. **Show your hand** to the camera
3. **Use any of these gestures:**
   - **Open Palm** (all 5 fingers up) → Take screenshot
   - **Closed Fist** (no fingers up) → Take screenshot
   - **Peace Sign** (index + middle fingers up) → Take screenshot
4. **Cooldown:** 2 seconds between screenshots
5. **Screenshots saved to:** `backend/screenshots_captured/`
6. **Exit:** Press **'ESC'** key

### **Gesture Tips:**
- ✅ Keep hand clearly visible
- ✅ Use good lighting
- ✅ Hold gesture for 1 second
- ✅ One hand at a time
- ✅ Wait for cooldown between actions

---

## 🎛️ **DASHBOARD CONTROLS**

### **Toggle Switches:**
- **Eye Control** (Yellow) - Enable/disable eye tracking
- **Voice Control** (Pink) - Enable/disable voice commands
- **Volume Control** (Blue) - Enable/disable pinch volume
- **Screenshot Control** (Blue) - Enable/disable gesture screenshots

### **Status Indicators:**
- **Active** (Green) - Feature is running
- **Inactive** (Gray) - Feature is stopped
- **Loading...** - Feature is starting

### **Important Notes:**
- ⚠️ Only one camera-based feature at a time (Eye OR Gestures)
- ⚠️ Voice control can run simultaneously with camera features
- ⚠️ Toggle OFF before switching camera features

---

## 🔧 **TROUBLESHOOTING**

### **Eye Tracking Issues:**
- **Cursor not moving:** Recalibrate (press 'C') or skip to use previous calibration (press 'S')
- **Inaccurate tracking:** Check lighting and face visibility
- **Clicks not working:** Blink more deliberately (double-blink)
- **No previous calibration found:** Complete calibration at least once before using skip

### **Voice Control Issues:**
- **Commands not recognized:** Speak louder and clearer
- **No response:** Check microphone permissions
- **Wrong actions:** Use exact command phrases

### **Gesture Issues:**
- **Gestures not detected:** Improve lighting
- **Volume not changing:** Show full hand clearly
- **Screenshots not saving:** Check folder permissions

### **General Issues:**
- **Camera not working:** Close other apps using camera
- **Features won't start:** Refresh dashboard and retry
- **System slow:** Close unnecessary programs

---

## 📊 **PERFORMANCE TIPS**

### **For Best Experience:**
1. **Lighting:** Use bright, even lighting (avoid shadows)
2. **Position:** Sit centered, 50-70cm from screen
3. **Background:** Use plain background for better detection
4. **Calibration:** Recalibrate eye tracking every 30 minutes OR use skip if position unchanged
5. **Resources:** Close unnecessary programs for better FPS

### **Optimal Settings:**
- **Eye Tracking:** Calibrate in your normal sitting position, or skip if unchanged
- **Voice Control:** Adjust microphone 15-20cm from mouth
- **Gestures:** Position hand 30-50cm from camera

---

## 🆘 **QUICK REFERENCE**

| Feature | Action | Command/Gesture |
|---------|--------|-----------------|
| **Eye** | Move cursor | Look around |
| **Eye** | Click | Double-blink |
| **Eye** | New Calibration | Press 'SPACE' |
| **Eye** | Skip Calibration | Press 'S' |
| **Eye** | Recalibrate | Press 'C' |
| **Voice** | Search | "Search [query]" |
| **Voice** | Browser | "Open Chrome" |
| **Voice** | AI Help | "What's on my screen?" |
| **Gesture** | Volume | Pinch fingers |
| **Gesture** | Screenshot | Open palm / Fist / Peace |

---

## 📞 **SUPPORT**

**For issues or questions:**
- Check terminal/console for error messages
- Verify all dependencies are installed
- Ensure camera/microphone permissions granted
- Restart the system if features become unresponsive
- Complete calibration at least once before using skip feature

---

**Version:** 1.1 | **Last Updated:** December 2024 | **New Feature:** Skip Calibration

---
