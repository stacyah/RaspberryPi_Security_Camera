import cv2
import time
import os
import threading
import logging
import configparser
import subprocess
from flask import Flask, render_template, send_from_directory
# pre-trained human detector model
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

def send_alert(image_path):
    # securely read credentials
    config = configparser.ConfigParser()
    config.read('/home/pi/security_camera_project/.email_credentials')

    email = config['email']['address']
    pwd = config['email']['password']
    recipient = config['email']['recipient']

    # build email with image attached
    cmd = f"""
    curl -s --ssl-reqd \
      --url 'smtps://smtp.gmail.com:465' \
      --user '{email}:{pwd}' \
      --mail-from '{email}' \
      --mail-rcpt '{recipient}' \
      --upload-file - <<EOF
    From: "Pi Security" <{email}>
    To: "You" <{recipient}>
    Subject: SECURITY ALERT! Human detected
    Date: $(date -R)
    Content-Type: multipart/mixed; boundary="BOUNDARY"

    --BOUNDARY
    Content-Type: text/plain

    Human detected at $(date)!
    check the attached image

    --BOUNDARY
    Content-Type: image/jpeg
    Content-Disposition: attachment; filename="detection.jpg"

    $(base64 {image_path})
    --BOUNDARY--
    EOF
    """
    subprocess.run(cmd, shell=True, check=True)

# set up logging
# create a file named app.log
log_file = os.path.join(os.path.dirname(__file__), 'app.log')
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s event="%(message)s"',
    datefmt='%Y-%m-%d %H:%M:%S'
)

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
    logging.info('camera_startup_success')

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
        human_detected = False # flag if a human is found
        motion_areas = [] # store where motion happened

        for contour in contours:
            if cv2.contourArea(contour) < 1000:
                continue

            # if we found a significant motion area
            motion_detected_significant = True
            (x, y, w, h) = cv2.boundingRect(contour)
            # draw a green box around general motion
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # only run human detection if there was significant motion
        if motion_detected_significant:
            # run human detector on the whole frame
            (rects, weights) = hog.detectMultiScale(frame, winStride=(8, 8), padding=(8, 8), scale=1.05)

            for (x, y, w, h) in rects:
                # draw a blue box if human found
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                human_detected = True
                break

        # save and log based on human detection
        if human_detected and (time.time() - last_human_alert > 30):
            filename = f"human_{time.strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
            cv2.imwrite(filename, frame)
            logging.info(f'human_detected file="{filename}"')
            send_alert(filename)  # sends the email
            last_human_alert = time.time()
            time.sleep(30)  # extended cooldown

        elif motion_detected_significant: # if significant motion but no human
            print("[Motion Thread] Motion Detected: No human, adapting background")
            static_back = gray # update background
            time.sleep(1) # shorter cooldown

app = Flask(__name__)

@app.route('/')
def index():
    # get all the .jpg files
    # newest first
    image_files = sorted([f for f in os.listdir('.') if f.endswith('.jpg')], reverse=True)
    return render_template('index.html', image_files=image_files)

@app.route('/images/<filename>')
def get_image(filename):
    # lets html see the images
    return send_from_directory('.', filename)

# run it
if __name__ == '__main__':
    # start the motion thread
    motion_thread = threading.Thread(target=motion_detection_thread)
    motion_thread.daemon = True
    motion_thread.start()

    # monitor new log file
    log_monitor_command = f"sudo /opt/splunkforwarder/bin/splunk add monitor {log_file}"
    print(f"[Main Thread] Adding log file to Splunk monitor, you may need to enter your password")
    os.system(log_monitor_command)

    print("[Web Server] Starting Flask server")
    app.run(host='0.0.0.0', port=5000)
