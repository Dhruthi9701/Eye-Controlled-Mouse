from flask import Blueprint, jsonify
import threading
from services import pure_eye_calibrator
from utils.feature_flags import is_enabled
import cv2,time
from services import volume_control

bp = Blueprint("control", __name__)

controllers = {
    "voice": None,
    "eye": None,
}

eye_tracker_instance = None
eye_tracker_stop_event = None
eye_tracker_thread = None

@bp.route("/features", methods=["GET"])
def features():
    from utils.feature_flags import FEATURES
    return jsonify({"features": FEATURES})

eye_tracker_should_stop = False

def run_eye_control():
    from services import advanced_eye_tracker
    global controllers, eye_tracker_instance, eye_tracker_should_stop
    
    eye_tracker_should_stop = False
    
    try:
        if not hasattr(advanced_eye_tracker, 'should_stop'):
            advanced_eye_tracker.should_stop = False
        
        tracker = advanced_eye_tracker.create_advanced_eye_tracking_demo()
        eye_tracker_instance = tracker
        
    except KeyboardInterrupt:
        print("Eye tracking interrupted")
    except Exception as e:
        print(f"Eye tracking error: {e}")
    finally:
        controllers["eye"] = None
        eye_tracker_instance = None
        eye_tracker_should_stop = False

@bp.route("/eye/start", methods=["POST"])
def eye_start():
    global controllers, eye_tracker_instance, eye_tracker_stop_event, eye_tracker_should_stop, eye_tracker_thread
    if not is_enabled("eye_control"):
        return jsonify({"error": "Eye control disabled"}), 403
    
    if controllers["eye"] is not None or eye_tracker_instance is not None:
        eye_stop_internal()
        import time
        time.sleep(0.5)
    
    try:
        try:
            print("🔧 Running calibration before starting eye tracker...")
            calib_file = pure_eye_calibrator.run_pure_eye_calibration()
            if not calib_file:
                controllers["eye"] = None
                return jsonify({"error": "Calibration failed or cancelled"}), 400
            print(f"🔎 Calibration saved: {calib_file}")
        except Exception as e:
            controllers["eye"] = None
            return jsonify({"error": f"Calibration error: {str(e)}"}), 500

        eye_tracker_stop_event = threading.Event()
        eye_tracker_should_stop = False
        controllers["eye"] = "running"

        eye_tracker_thread = threading.Thread(target=run_eye_control, daemon=True)
        eye_tracker_thread.start()

        return jsonify({"status": "Eye control started", "eye_active": True})
    except Exception as e:
        controllers["eye"] = None
        eye_tracker_instance = None
        eye_tracker_stop_event = None
        eye_tracker_thread = None
        eye_tracker_should_stop = False
        return jsonify({"error": f"Failed to start eye control: {str(e)}"}), 500

def eye_stop_internal():
    global controllers, eye_tracker_instance, eye_tracker_stop_event, eye_tracker_should_stop, eye_tracker_thread
    
    print("🛑 Attempting to stop eye tracker...")
    
    print("🛑 Setting stop flag to stop eye tracker...")
    
    eye_tracker_should_stop = True
    
    if eye_tracker_stop_event:
        eye_tracker_stop_event.set()
        print("🛑 Eye tracker stop event set")
    
    try:
        from services import advanced_eye_tracker
        advanced_eye_tracker.should_stop = True
        print("🛑 Set service.should_stop = True")
        
        if hasattr(advanced_eye_tracker, 'cap') and advanced_eye_tracker.cap:
            try:
                advanced_eye_tracker.cap.release()
                print("🛑 Released camera via service.cap.release()")
            except:
                pass
        if hasattr(advanced_eye_tracker, "running"):
            advanced_eye_tracker.running = False
            print("🛑 Set service.running = False")
        if hasattr(advanced_eye_tracker, "stop_all"):
            advanced_eye_tracker.stop_all()
            print("🛑 Called service.stop_all()")
        if hasattr(advanced_eye_tracker, "stop_eye_tracking"):
            advanced_eye_tracker.stop_eye_tracking()
            print("🛑 Called service.stop_eye_tracking()")
        if hasattr(advanced_eye_tracker, "cap") and advanced_eye_tracker.cap:
            try:
                advanced_eye_tracker.cap.release()
                print("🛑 Released camera via service.cap.release()")
            except:
                pass
        if hasattr(advanced_eye_tracker, "camera") and advanced_eye_tracker.camera:
            try:
                advanced_eye_tracker.camera.release()
                print("🛑 Released camera via service.camera.release()")
            except:
                pass
    except Exception as e:
        print(f"Error calling service stop methods: {e}")
    
    if eye_tracker_instance is not None:
        try:
            if hasattr(eye_tracker_instance, "stop"):
                eye_tracker_instance.stop()
                print("🛑 Called tracker.stop()")
            if hasattr(eye_tracker_instance, "stop_eye_tracking"):
                eye_tracker_instance.stop_eye_tracking()
                print("🛑 Called tracker.stop_eye_tracking()")
            if hasattr(eye_tracker_instance, "cleanup"):
                eye_tracker_instance.cleanup()
                print("🛑 Called tracker.cleanup()")
            if hasattr(eye_tracker_instance, "release"):
                eye_tracker_instance.release()
                print("🛑 Called tracker.release()")
            if hasattr(eye_tracker_instance, "close"):
                eye_tracker_instance.close()
                print("🛑 Called tracker.close()")
            if hasattr(eye_tracker_instance, "cap"):
                try:
                    eye_tracker_instance.cap.release()
                    print("🛑 Released camera via tracker.cap.release()")
                except:
                    pass
        except Exception as e:
            print(f"Error stopping eye tracker instance: {e}")
    
    try:
        import cv2
        print("🛑 Attempted to access OpenCV directly")
    except:
        pass
    
    controllers["eye"] = None
    eye_tracker_instance = None
    if eye_tracker_stop_event:
        eye_tracker_stop_event.clear()
    eye_tracker_stop_event = None
    eye_tracker_thread = None
    eye_tracker_should_stop = False
    print("🛑 Cleared all eye tracker references")

@bp.route("/eye/stop", methods=["POST"])
def eye_stop():
    try:
        eye_stop_internal()
        print("✅ Eye control stopped successfully")
        return jsonify({"status": "Eye control stopped", "eye_active": False})
    except Exception as e:
        print(f"Error in eye_stop: {e}")
        controllers["eye"] = None
        eye_tracker_instance = None
        eye_tracker_stop_event = None
        return jsonify({"status": "Eye control stopped", "eye_active": False})

@bp.route("/eye/calibrate", methods=["POST"])
def eye_calibrate():
    if not is_enabled("eye_control"):
        return jsonify({"error": "Eye control disabled"}), 403
    threading.Thread(target=pure_eye_calibrator.run_pure_eye_calibration, daemon=True).start()
    return jsonify({"status": "Eye calibration started"})

def run_volume_control():
    from services import volume_screenshot_core
    print("🎥 Starting volume control (pinch gesture) - camera should initialize...")
    try:
        volume_screenshot_core.volume_screenshot_core_loop(True, False)
    except Exception as e:
        print(f"❌ Volume control error: {e}")
        import traceback
        traceback.print_exc()

screenshot_running = True
cap = None
hands = None

def run_screenshot_control():
    global screenshot_running
    last_time = 0
    cooldown = 2
    while screenshot_running:
        success, img = cap.read()
        if not success:
            break

        img = cv2.flip(img, 1)
        results = hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                lm_list = [[i, int(lm.x*640), int(lm.y*480)]
                           for i, lm in enumerate(hand_landmarks.landmark)]
                if len(lm_list) == 21:
                    fingers = fingers_up(lm_list)
                    if sum(fingers) == 5 and time.time() - last_time > cooldown:
                        take_screenshot()
                        last_time = time.time()
        time.sleep(0.01)

    cap.release()
    cv2.destroyAllWindows()
    print("✓ Screenshot control stopped")

gesture_threads = {
    "volume": None,
    "screenshot": None,
}

@bp.route("/volume/control/start", methods=["POST"])
def volume_start():
    global gesture_threads

    if gesture_threads["volume"] and gesture_threads["volume"].is_alive():
        volume_stop()
        time.sleep(0.1)

    gesture_threads["volume"] = threading.Thread(target=volume_control.start_volume_control, daemon=True)
    gesture_threads["volume"].start()
    return jsonify({"status": "Volume control started - camera initializing"})

@bp.route("/volume/control/stop", methods=["POST"])
def volume_stop():
    global gesture_threads

    volume_control.stop_volume_control()

    time.sleep(0.1)
    gesture_threads["volume"] = None
    return jsonify({"status": "Volume control stopped"})

@bp.route("/screenshot/control/start", methods=["POST"])
def screenshot_start():
    global gesture_threads
    import time
    from services.screenshot_control import run_screenshot_control

    if gesture_threads["volume"] and gesture_threads["volume"].is_alive():
        from services.volume_control import stop_volume_control
        stop_volume_control()
        time.sleep(0.2)

    if gesture_threads["screenshot"] and gesture_threads["screenshot"].is_alive():
        screenshot_stop()
        time.sleep(0.2)

    print("🖐️ Starting palm gesture (screenshot) control...")
    gesture_threads["screenshot"] = threading.Thread(target=run_screenshot_control, daemon=True)
    gesture_threads["screenshot"].start()
    return jsonify({"status": "Screenshot control started - camera initializing"})

@bp.route("/screenshot/control/stop", methods=["POST"])
def screenshot_stop():
    global gesture_threads
    from services.screenshot_control import stop_screenshot_control

    try:
        stop_screenshot_control()
        print("🛑 Screenshot control stopped")
    except Exception as e:
        print(f"Error stopping screenshot: {e}")

    gesture_threads["screenshot"] = None
    return jsonify({"status": "Screenshot control stopped"})

def run_voice_controller(voice_controller):
    print(">>> Voice controller thread started")
    try:
        voice_controller.run()
    except Exception as e:
        print(f"Voice controller error: {e}")
    finally:
        print(">>> Voice controller thread ended")
        global controllers
        controllers["voice"] = None

@bp.route("/voice/start", methods=["POST"])
def voice_start():
    from services.voice_assistant import VoiceAssistant
    global controllers

    if controllers["voice"] is not None:
        voice_stop_internal()
        import time
        time.sleep(0.3)

    try:
        assistant = VoiceAssistant(silent_mode=True)
        controllers["voice"] = assistant

        threading.Thread(target=run_voice_controller, args=(assistant,), daemon=True).start()
        return jsonify({
            "status": "Voice control started (full assistant mode)", 
            "voice_active": True,
            "mode": "full_assistant",
            "features": "Browser control + System-wide control (apps, files, windows, system info)"
        })
    except Exception as e:
        controllers["voice"] = None
        return jsonify({"error": f"Failed to start voice control: {str(e)}"}), 500

@bp.route("/voice/assistant/start", methods=["POST"])
def voice_assistant_start():
    return voice_start()

def voice_stop_internal():
    global controllers
    vc = controllers.get("voice")
    
    print("🛑 Attempting to stop voice controller...")
    
    if vc is None:
        controllers["voice"] = None
        return
    
    try:
        if hasattr(vc, "stop_all"):
            vc.stop_all()
            print("🛑 Called vc.stop_all()")
        if hasattr(vc, "stop"):
            vc.stop()
            print("🛑 Called vc.stop()")
        if hasattr(vc, "stop_listening"):
            vc.stop_listening()
            print("🛑 Called vc.stop_listening()")
        if hasattr(vc, "cleanup"):
            vc.cleanup()
            print("🛑 Called vc.cleanup()")
        if hasattr(vc, "close"):
            vc.close()
            print("🛑 Called vc.close()")
    except Exception as e:
        print(f"Error stopping voice controller methods: {e}")
    
    try:
        if hasattr(vc, "should_stop"):
            vc.should_stop = True
            print("🛑 Set vc.should_stop = True")
        if hasattr(vc, "running"):
            vc.running = False
            print("🛑 Set vc.running = False")
        if hasattr(vc, "is_listening"):
            vc.is_listening = False
            print("🛑 Set vc.is_listening = False")
    except Exception as e:
        print(f"Error setting voice controller flags: {e}")
    
    controllers["voice"] = None
    print("✅ Voice controller reference cleared")

@bp.route("/voice/stop", methods=["POST"])
def voice_stop():
    try:
        voice_stop_internal()
        import time
        time.sleep(0.2)
        print("✅ Voice control stopped successfully")
        return jsonify({"status": "Voice control stopped", "voice_active": False})
    except Exception as e:
        print(f"Error in voice_stop: {e}")
        controllers["voice"] = None
        return jsonify({"status": "Voice control stopped", "voice_active": False})

@bp.route("/start_screenshot_control", methods=["POST"])
def legacy_start_screenshot_control():
    return screenshot_start()

@bp.route("/stop_volume_screenshot", methods=["POST"])
def legacy_stop_volume_screenshot():
    return both_stop()

@bp.route("/eye/move", methods=["POST"])
def eye_move():
    return jsonify({"status": "Eye movement tracking not yet implemented"}), 200
