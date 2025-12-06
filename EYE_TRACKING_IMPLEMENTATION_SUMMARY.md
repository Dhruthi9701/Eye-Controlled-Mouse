# Eye Tracking Implementation Summary

## Overview
The eye tracking system uses **MediaPipe Face Mesh** to detect facial landmarks and track eye movements for cursor control. It implements a sophisticated pipeline that processes camera frames, extracts eye/iris positions, maps them to screen coordinates, and controls the mouse cursor with smoothing and filtering.

---

## Architecture Components

### 1. **Core Classes**

#### `AdvancedEyeTracker` (Main Class)
- **Purpose**: Orchestrates the entire eye tracking pipeline
- **Key Responsibilities**:
  - Camera capture and frame processing
  - Face landmark detection via MediaPipe
  - Gaze point calculation
  - Mouse cursor control
  - Blink detection for clicking
  - Calibration data management

#### `KalmanGazeFilter`
- **Purpose**: Smooths gaze predictions to reduce jitter
- **Implementation**: 4-state Kalman filter (x, y, velocity_x, velocity_y)
- **Benefits**: Predicts next position, filters noise, provides stable cursor movement

#### `AttentionDetector`
- **Purpose**: Analyzes gaze patterns to detect user attention/focus
- **Features**: 
  - Tracks gaze history (30-point window)
  - Calculates attention score based on gaze stability
  - Detects fixation points

#### `EyeState` (DataClass)
- **Stores**: Left iris position, right iris position, head pose (yaw/pitch/roll), blink ratio, attention score

#### `GazePoint` (DataClass)
- **Stores**: Screen coordinates (x, y), timestamp, confidence score

---

## Eye Tracking Pipeline

### **Step 1: Initialization**
```python
tracker = AdvancedEyeTracker()
```
- Loads latest calibration data (if available)
- Initializes Kalman filter and attention detector
- Sets up blink detection variables
- Configures mouse smoothing parameters

### **Step 2: Camera Capture & Face Detection**
```python
cap = cv2.VideoCapture(0)
results = face_mesh.process(rgb_frame)
```
- Captures frames from webcam (640x480)
- Converts BGR to RGB for MediaPipe
- Detects face landmarks using MediaPipe Face Mesh
- Extracts 468 facial landmarks + iris landmarks (468, 469, 470, 471, 472, 473, 474, 475, 476, 477)

### **Step 3: Landmark Processing** (`process_face_landmarks`)
For each frame:
1. **Iris Detection**:
   - Left iris: Landmark 468
   - Right iris: Landmark 473
   - Fallback: Calculates eye center from multiple eye landmarks if iris not detected

2. **Head Pose Estimation** (`_estimate_head_pose`):
   - Calculates yaw, pitch, roll from facial landmarks
   - Uses nose tip, chin, and eye positions
   - Used for head movement compensation

3. **Blink Detection** (`_calculate_blink_ratio`):
   - Calculates **Eye Aspect Ratio (EAR)** for both eyes
   - Uses 6 key points per eye (outer corner, inner corner, 2 top points, 2 bottom points)
   - Formula: `EAR = (vertical1 + vertical2) / (2.0 * horizontal)`
   - Averages both eyes for reliability
   - Threshold: < 0.22 = blinking, ≥ 0.22 = eyes open

4. **Landmark Signature Extraction**:
   - Extracts comprehensive landmark patterns for calibration matching
   - Stores iris centroids, eye regions, face structure

### **Step 4: Gaze Point Calculation** (`calculate_gaze_point`)
1. **Average Iris Position**:
   ```python
   avg_iris_x = (left_iris_x + right_iris_x) / 2
   avg_iris_y = (left_iris_y + right_iris_y) / 2
   ```

2. **Head Pose Correction** (`_apply_head_pose_correction`):
   - Adjusts iris position based on head rotation
   - Yaw correction: `iris_x + (yaw * 2.0)`
   - Pitch correction: `iris_y + (pitch * 1.5)`

3. **Screen Coordinate Mapping** (`_map_to_screen`):
   - **If Calibrated**:
     - **Landmark-based mapping** (preferred): Matches current landmark signature to stored calibration patterns
     - **Traditional mapping**: Uses polynomial transformation matrix
   - **If Not Calibrated**: Uses basic head+eye tracking (less accurate)

4. **Confidence Calculation** (`_calculate_confidence`):
   - Base confidence from attention score
   - Reduced if blinking (< 0.2)
   - Reduced if iris detection poor
   - Returns value between 0.1 and 1.0

5. **Kalman Filtering**:
   - Updates filter with new measurement
   - Predicts next position
   - Returns smoothed gaze coordinates

### **Step 5: Mouse Control** (`control_mouse`)
1. **Confidence Check**: Skips if confidence < 0.2

2. **Adaptive Smoothing**:
   - Distance-based smoothing:
     - < 20px: 0.15 × confidence (high precision)
     - < 50px: 0.25 × confidence
     - < 100px: 0.4 × confidence
     - ≥ 100px: 0.6 × confidence (quick movement)
   - Minimum smoothing: 0.1

3. **Sensitivity Adjustment**:
   - Applies `eye_sensitivity_multiplier` (default: 1.25)
   - User-configurable for fine-tuning

4. **Acceleration**:
   - For movements > 100px, applies acceleration factor
   - Speeds up large movements

5. **Mouse Movement**:
   ```python
   smooth_x = current_x + delta_x * smoothing
   smooth_y = current_y + delta_y * smoothing
   pyautogui.moveTo(int(smooth_x), int(smooth_y))
   ```

### **Step 6: Double Blink Click Detection** (`detect_blink_click`)
1. **Blink State Tracking**:
   - Maintains history of last 10 blink states
   - Each state: `{is_blinking: bool, time: float, blink_ratio: float}`

2. **Double Blink Pattern**:
   - Looks for pattern: **blink → open → blink** within 600ms
   - Checks last 5 states for flexibility
   - Requires at least 2 frames between blinks (to distinguish from long single blink)

3. **Cooldown**:
   - 300ms cooldown after click to prevent multiple clicks

4. **Click Execution**:
   - When double blink detected, clicks at current cursor position
   - Shows "CLICK!" visual feedback

---

## Calibration System

### **Calibration Process** (`pure_eye_calibrator.py`)
1. **25-Point Grid**: User looks at 25 calibration points on screen
2. **Data Collection**: 
   - Collects eye positions for 1.5 seconds per point (45 frames)
   - Tracks head movement (resets if head moves)
   - Stores landmark signatures for each point

3. **Transformation Calculation**:
   - **Landmark-based**: Maps landmark patterns to screen coordinates
   - **Traditional**: Polynomial regression (2nd or 3rd degree)

4. **Calibration Quality**:
   - Excellent: < 5% error
   - Good: 5-10% error
   - Fair: 10-20% error
   - Poor: > 20% error

5. **Saving**: Saves to JSON file (`landmark_eye_calibration_*.json` or `pure_eye_calibration_*.json`)

### **Calibration Loading** (`load_latest_calibration`)
- Searches for latest calibration file
- Loads landmark mappings or transformation matrix
- Sets `is_calibrated` flag
- Falls back to basic mapping if no calibration found

---

## Key Algorithms

### **1. Eye Aspect Ratio (EAR)**
```
EAR = (vertical1 + vertical2) / (2.0 * horizontal)
```
- **Vertical1**: Distance between top point 1 and bottom point 1
- **Vertical2**: Distance between top point 2 and bottom point 2
- **Horizontal**: Distance between outer and inner eye corners
- **Normal**: ~0.25-0.35 (eyes open)
- **Blinking**: < 0.22 (eyes closed)

### **2. Kalman Filter**
- **State**: [x, y, velocity_x, velocity_y]
- **Process Noise**: Models eye movement uncertainty
- **Measurement Noise**: Adjusted by confidence
- **Prediction**: Estimates next gaze position
- **Update**: Incorporates new measurements

### **3. Landmark-Based Mapping**
- Extracts landmark signature (iris centroids, eye regions, face structure)
- Compares with stored calibration patterns
- Finds best match using similarity scoring
- Applies fine adjustment based on current vs. stored patterns

---

## Visual Feedback

### **Camera Feed Display**:
- Iris connections (yellow lines)
- Eye outlines (magenta polygons)
- Iris landmarks (yellow dots)
- Gaze point indicator (yellow circle with white center)
- Status text:
  - Gaze coordinates
  - Confidence score
  - Blink status (EAR value)
  - Calibration quality
  - Mouse control status

---

## Performance Optimizations

1. **Frame Rate**: ~30 FPS (33ms per frame)
2. **Smoothing**: Adaptive based on distance and confidence
3. **Confidence Filtering**: Skips low-confidence gaze points
4. **Boundary Checking**: Validates coordinates are within screen bounds
5. **Error Handling**: Graceful fallbacks if detection fails

---

## Configuration Parameters

- **Blink Threshold**: 0.22 (EAR)
- **Double Blink Window**: 600ms
- **Blink Cooldown**: 300ms
- **Mouse Smoothing**: 0.4 (calibrated) / 0.3 (uncalibrated)
- **Sensitivity Multiplier**: 1.25 (user-adjustable)
- **Confidence Threshold**: 0.2 (minimum for mouse control)
- **Screen Boundary Margin**: 15% (allows slight overshoot)

---

## Data Flow Summary

```
Camera Frame
    ↓
MediaPipe Face Detection
    ↓
Extract Landmarks (468 points + iris)
    ↓
Process Face Landmarks:
  - Get iris positions
  - Calculate head pose
  - Calculate blink ratio
  - Extract landmark signature
    ↓
Calculate Gaze Point:
  - Average iris positions
  - Apply head pose correction
  - Map to screen coordinates
  - Calculate confidence
  - Apply Kalman filtering
    ↓
Control Mouse:
  - Check confidence
  - Calculate adaptive smoothing
  - Apply sensitivity multiplier
  - Move cursor smoothly
    ↓
Detect Double Blink:
  - Track blink history
  - Detect double blink pattern
  - Trigger click if detected
```

---

## Error Handling & Fallbacks

1. **No Face Detected**: Shows "No face detected" message, continues
2. **Poor Iris Detection**: Falls back to eye center calculation
3. **No Calibration**: Uses basic head+eye tracking
4. **Low Confidence**: Skips mouse movement for that frame
5. **Invalid Coordinates**: Clamps to screen bounds
6. **Camera Failure**: Graceful shutdown with error message

---

## Threading & Integration

- Runs in separate thread to avoid blocking main application
- Can run simultaneously with voice control
- Uses global `should_stop` flag for clean shutdown
- Integrates with Flask API for start/stop control

---

This implementation provides a robust, accurate eye tracking system with multiple fallback mechanisms and user-friendly features like double-blink clicking and adaptive smoothing.

