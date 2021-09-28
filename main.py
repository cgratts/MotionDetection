import cv2
import smtplib
import pandas
import os.path
import tkinter as tk
from threading import Thread
from tkinter import simpledialog
from datetime import datetime
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase


# Setup thread to send alert email in real-time
class EmailThread(Thread):
    def __init__(self, email_to):
        self.email_to = email_to
        Thread.__init__(self)

    def run(self):
        auto_email = 'test@exmaple.com'
        body = "MOVEMENT DETECTED"
        message = MIMEMultipart()
        message["Subject"] = "!!! SECURITY BREACH !!!"
        message["From"] = "your@email.com"
        message["To"] = user_email
        message.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user_email, user_pw)
        server.sendmail(auto_email, user_email, message.as_string())
        server.quit()


# Setup thread to send attachment email in real-time
class AttachmentThread(Thread):
    def __init__(self, email_to):
        self.email_to = email_to
        Thread.__init__(self)

    def run(self):
        auto_email = 'test@exmaple.com'
        body = "Attached below is a video of the detected motion"
        message = MIMEMultipart()
        message["Subject"] = "Video Surveillance"
        message["From"] = "your@email.com"
        message["To"] = user_email
        message.attach(MIMEText(body, 'plain'))

        # Setup file attachment, bind to MIMEMultipart object, and send email
        file_path = 'C:\\Users\\Charby\\PycharmProjects\\LiveWebcamFeed\\DetectedMotion.avi'
        file_name = os.path.basename(file_path)
        attachment = open(file_path, "rb")
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % file_name)
        message.attach(part)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user_email, user_pw)
        server.sendmail(auto_email, user_email, message.as_string())
        server.quit()
        attachment.close()
        # file_path = 'C:\\Users\\Charby\\PycharmProjects\\LiveWebcamFeed\\Test.avi'
        # os.remove(file_path)


# Get user credentials for email alerts
root = tk.Tk()
root.withdraw()
user_email, user_pw = simpledialog.askstring(title="Credentials",
                                                prompt="Enter your email address followed"
                                                " by a space, and then your password").split(' ')
root.destroy()

# Define the codec and create VideoWriter object for motion recording
fourcc = cv2.VideoWriter_fourcc(*'XVID')
output = cv2.VideoWriter('DetectedMotion.avi', fourcc, 30.0, (640, 480))
# Static background
static_bg = None
# Detected motion frames
motion_list = [None, None]
# Time(s) of motion detection
time_list = []
# DataFrame initialization
df = pandas.DataFrame(columns=["Start", "End"])
# Capture webcam feed (CAP_DSHOW removes 'terminating async callback' runtime warning)
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

# Process live webcam feed
while cap.isOpened():
    # Get frame from feed
    check, frame = cap.read()
    # No motion
    motion = 0
    # Convert color image to grayscale image
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Convert gray scale image to GaussianBlur for easy identification of change
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # Assign static background value to first frame
    if static_bg is None:
        static_bg = gray
        continue

    # Find difference between static background and current frame
    frame_diff = cv2.absdiff(static_bg, gray)
    # If intensity difference of a pixel > 30, pixel = white; If intensity difference of a pixel < 30, pixel = black
    # This is how the program will identify motion between different pixels
    frame_thresh = cv2.threshold(frame_diff, 30, 255, cv2.THRESH_BINARY)[1]
    frame_thresh = cv2.dilate(frame_thresh, None, iterations=2)
    contours, _ = cv2.findContours(frame_thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # If the area of a contour < 10000, do nothing; Else draw a green rectangle around object in motion
    for contour in contours:
        if cv2.contourArea(contour) < 10000:
            continue
        # Record detected movement for future playback (in same directory as main.py)
        output.write(frame)
        motion = 1
        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1)

    # Display live timestamp on the window
    cv2.putText(frame, datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 1)

    # Add motion status to list
    motion_list.append(motion)
    motion_list = motion_list[-2:]
    # Add start time of motion to list and email recipient an alert of movement detection (in real-time)
    if motion_list[-1] == 1 and motion_list[-2] == 0:
        time_list.append(datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"))
        # Set thread as daemon thread so it gets killed when main terminates
        EmailThread.daemon = True
        EmailThread(user_email).start()

    # Add end time of motion to list and email recipient an attachment of recorded movement (in real-time)
    if motion_list[-1] == 0 and motion_list[-2] == 1:
        time_list.append(datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"))
        # Set thread as daemon thread so it gets killed when main terminates
        AttachmentThread.daemon = True
        AttachmentThread(user_email).start()

    # Display live webcam feed
    cv2.imshow("Live Webcam Feed", frame)

    # 'Esc' key pressed
    if cv2.waitKey(1) == 27:
        # If movement is detected, update end time of motion and exit live feed loop
        if motion == 1:
            time_list.append(datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"))
        break

# Add time of motion to DataFrame
for i in range(0, len(time_list), 2):
    df = df.append({"Start": time_list[i], "End": time_list[i + 1]}, ignore_index=True)

# Generate CSV file (in same directory as main.py) of time log
df.to_csv("MotionTimeLog.csv")

# Close webcam capture, output stream, and stream window
cap.release()
output.release()
cv2.destroyAllWindows()
