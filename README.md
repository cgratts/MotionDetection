# MotionDetection
 
Implementations/bug fixes to be added:

(Implement) - Generalize code to accept any email (Only accepts gmail accounts currently)

(Debug) - Each clip of detected movement is appended into 1 video dynamically growing in size each time motion is detected, instead of replacing the previous clip with the most recent one after it is sent in an email

(Debug) - os.remove after attachment email is sent gives the following message: The process cannot access the file because it is being used by another process: 'C:\\Users\\Charby\\PycharmProjects\\LiveWebcamFeed\\DetectedMotion.avi'

(Implement) - Send time log file as an email attachment the once above issues are debugged
