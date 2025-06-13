import cv2
import time
import os
import threading
from flask import Flask, render_template, send_from_directory

def motion_detection_thread():
    # so we can access video from anywhere
    global video
    static_back = None

    # get the webcam
    video = cv2.VideoCapture(0, cv2.CAP_V4L2)

    # let the camera warm up
    print("[Motion Thread] Camera warming up...")
    time.sleep(2.0)
    print("[Motion Thread] Camera ready. Watching for motion")

    while True:
        check, frame = video.read()
        if not check:
            # try again if we can't get a frame
            time.sleep(0.5)
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if static_back is None:
            static_back = gray
            continue

        frame_delta = cv2.absdiff(static_back, gray)
        thresh = cv2.threshold(frame_delta, 15, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) < 500:
                continue
            motion_detected = True
            # don't need the green box for the web version
            # (x, y, w, h) = cv2.boundingRect(contour)
            # cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        if motion_detected:
            print("[Motion Thread] Motion Detected!")
            current_time = time.strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"motion_{current_time}.jpg"
            cv2.imwrite(filename, frame)
            print(f"[Motion Thread] Saved image as {filename}")
            static_back = gray
            # cooldown to not save too many pictures
            time.sleep(5)

        # wait for a sec so the cpu doesn't melt
        time.sleep(0.1)

app = Flask(__name__)

@app.route('/')
def index():
    # get all the .jpg files
    # newest first
    image_files = sorted([f for f in os.listdir('.') if f.endswith('.jpg')], reverse=True)
    return render_template('index.html', image_files=image_files)

@app.route('/images/<filename>')
def get_image(filename):
    # lets the html see the images
    return send_from_directory('.', filename)

# run it
if __name__ == '__main__':
    # start the motion thread
    motion_thread = threading.Thread(target=motion_detection_thread)
    # lets us exit the app easily
    motion_thread.daemon = True
    motion_thread.start()

    # start the web server on our local network
    print("[Web Server] Starting Flask server")
    app.run(host='0.0.0.0', port=5000)
