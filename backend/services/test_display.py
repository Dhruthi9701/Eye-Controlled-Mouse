import cv2
import numpy as np

print("Testing basic OpenCV window creation...")

analysis_w, analysis_h = 1000, 700
screen = np.zeros((analysis_h, analysis_w, 3), dtype=np.uint8)

cv2.circle(screen, (500, 350), 20, (0, 0, 255), -1)
cv2.circle(screen, (500, 350), 25, (255, 255, 255), 2)

cv2.putText(screen, "Test Screen - Press ESC to exit", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

cv2.namedWindow('Test Window', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Test Window', analysis_w, analysis_h)

print("Black screen with red ball should appear. Press ESC to exit.")

while True:
    cv2.imshow('Test Window', screen)
    
    key = cv2.waitKey(1) & 0xFF
    if key == 27:
        break
    elif key == ord(' '):
        print("Space pressed - ball position will move")
        x = np.random.randint(50, analysis_w - 50)
        y = np.random.randint(50, analysis_h - 50)
        screen = np.zeros((analysis_h, analysis_w, 3), dtype=np.uint8)
        cv2.circle(screen, (x, y), 20, (0, 0, 255), -1)
        cv2.circle(screen, (x, y), 25, (255, 255, 255), 2)
        cv2.putText(screen, "Test Screen - Press ESC to exit", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(screen, "Press SPACE for new position", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

cv2.destroyAllWindows()
print("Test completed.")
