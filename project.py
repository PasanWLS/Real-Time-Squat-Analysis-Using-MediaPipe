# Import Libraries
import cv2
import mediapipe as mp
import numpy as np
import csv
import time

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

# Function to calculate the angle between three points
def calculate_angle(a, b, c):
    a = np.array(a)  # First point
    b = np.array(b)  # Second point (vertex)
    c = np.array(c)  # Third point

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle

    return angle

## Thresholds Value
# Thresholds
KNEE_ANGLE_THRESHOLD = (90, 160)  # Correct squat "down" position
HIP_ANGLE_THRESHOLD = (140, 180)  # Standing "up" position
 
## Collect Personal Info
sm_name = input("Enter SportsmSaman's name: ")
sm_age = input("Enter Sportsman's age: ")

## Initialize variables
# Feedback variables
correct_count = 0
incorrect_count = 0
down_position = False
# Count Squat
squat_count = 0
squat_stage = None
# Time
start_time = None  # Time when squat starts
squat_duration = None  # Duration of the squat

## Data Collect
# To store data for CSV
data_rows = [] 
# Create CSV file and write header
with open('squat_data.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Sportman Name","Sportman Age", "Squat Number", "Knee Angle", "Hip Angle", "Ankle Angle", "Shoulder Angle",  "Squat Time (seconds)", "feedback", "status"])

# Open a video file or webcam
cap = cv2.VideoCapture('squat2.mp4') 

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Unable to fetch frame from camera.")
        break

    # Convert frame to RGB
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image.flags.writeable = False
    # Process the image
    results = pose.process(image)
    # Convert back to BGR for rendering
    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    try:
        # Extract landmarks
        landmarks = results.pose_landmarks.landmark

        # Get coordinates for key points
        hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x, 
               landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
        knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x, 
                landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
        ankle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x, 
                 landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]
        shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, 
                    landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
        foot = [landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value].x, 
                    landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value].y]
        elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x, 
                    landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]

        # Calculate angles
        knee_angle = calculate_angle(ankle, knee, hip)
        hip_angle = calculate_angle(knee, hip, shoulder)
        #ankle_angle = calculate_angle(knee, ankle, shoulder)
        ankle_angle = calculate_angle(hip, ankle, knee)
        shoulder_angle = calculate_angle(hip, shoulder, elbow)

        # Display angles
        cv2.putText(image, f"Knee: {int(knee_angle)}", 
                    tuple(np.multiply(knee, [frame.shape[1], frame.shape[0]]).astype(int)),
                    cv2.FONT_HERSHEY_SIMPLEX, .75, (255, 255, 255), 2, cv2.LINE_AA)
        
        cv2.putText(image, f"Hip: {int(hip_angle)}",
                    tuple(np.multiply(hip, [frame.shape[1], frame.shape[0]]).astype(int)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
        cv2.putText(image, f"Ankle: {int(ankle_angle)}",
                    tuple(np.multiply(ankle, [frame.shape[1], frame.shape[0]]).astype(int)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
        cv2.putText(image, f"Shoulder: {int(shoulder_angle)}",
                    tuple(np.multiply(shoulder, [frame.shape[1], frame.shape[0]]).astype(int)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
        
        ## Squat
        # Squat logic
        if KNEE_ANGLE_THRESHOLD[0] <= knee_angle <= KNEE_ANGLE_THRESHOLD[1]:
            down_position = True
        elif down_position and hip_angle >= HIP_ANGLE_THRESHOLD[0]:
            correct_count += 1
            down_position = False
        else:
            if down_position:  
                incorrect_count += 1
                down_position = False  


        # Squat Position analysis
        if knee_angle > 160:
            status = "Stand"
        elif knee_angle < 90:
            status = "Squat"
        else:
            status = "Half-Squat"
            
            
        # Provide feedback on squat depth
        if knee_angle > 160:
            feedback = "Too High"
            color = (0, 0, 255)  # Red
        elif knee_angle < 90:
            feedback = "Too Low"
            color = (0, 0, 255)  # Red
        else:
            feedback = "Good"
            color = (0, 255, 0)  # Green
            
        # # Squat Count
        # if shoulder_angle < 10:
        #     squat_stage = "up"
        # elif shoulder_angle > 50 and squat_stage == "up":
        #     squat_stage = "down"
        #     squat_count += 1
        
        # Squat Count and Time
        if shoulder_angle < 10:  # Transition to "up"
            squat_stage = "up"
            if start_time:  # If a squat just finished
                squat_duration = time.time() - start_time  # Calculate squat duration
                squat_count += 1   
                start_time = None  # Reset start time
        elif shoulder_angle > 20 and squat_stage == "up":  # Transition to "down"
            squat_stage = "down"
            start_time = time.time()  # Record the start time
        

            # Save data to CSV
            with open('squat_data.csv', 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([sm_name, sm_age, squat_count, knee_angle, hip_angle, ankle_angle, shoulder_angle,  round(squat_duration, 2), feedback, status])

        
        

        # Display feedback with black background rectangles
        rect_height = 40  
        rect_padding = 10 
        cv2.rectangle(image, (50 - rect_padding, 50 - rect_padding), 
                    (400, 10 + rect_height), (0, 0, 0), -1)  
        cv2.rectangle(image, (50 - rect_padding, 50 - rect_padding), 
                    (400, 60 + rect_height), (0, 0, 0), -1)  
        cv2.putText(image, f"  Number of Squats: {squat_count}", (50, 50 + rect_padding), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2, cv2.LINE_AA)

        cv2.rectangle(image, (50 - rect_padding, 150 - rect_padding), 
                    (400, 150 + rect_height), (0, 0, 0), -1)  # Black rectangle for second text line
        cv2.putText(image, f"  Correct Squat: {correct_count}", (50, 150 + rect_padding), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2, cv2.LINE_AA)

        cv2.rectangle(image, (50 - rect_padding, 200 - rect_padding), 
                    (400, 200 + rect_height), (0, 0, 0), -1)  # Black rectangle for third text line
        cv2.putText(image, f"  Incorrect Squat: {incorrect_count}", (50, 200 + rect_padding), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2, cv2.LINE_AA)

        cv2.rectangle(image, (50 - rect_padding, 300 - rect_padding), 
                    (400, 300 + rect_height), (0, 0, 0), -1)  # Black rectangle for fourth text line
        cv2.putText(image, f"  Squat Depth: {feedback}", (50, 300 + rect_padding), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2, cv2.LINE_AA)

        cv2.rectangle(image, (50 - rect_padding, 250 - rect_padding), 
                    (400, 250 + rect_height), (0, 0, 0), -1)  # Black rectangle for fifth text line
        cv2.putText(image, f"  Position: {status}", (50, 250 + rect_padding), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2, cv2.LINE_AA)

        cv2.rectangle(image, (50 - rect_padding, 100 - rect_padding), 
                    (400, 100 + rect_height), (0, 0, 0), -1)  # Black rectangle for sixth text line
        cv2.putText(image, f"  Squat Time: {round(squat_duration, 2)} sec", (50, 100 + rect_padding), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 255), 2, cv2.LINE_AA)


        #  # Display feedback
        # cv2.putText(image, f"Number of Squats: {squat_count}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        # cv2.putText(image, f"Correct Squat: {correct_count}", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        # cv2.putText(image, f"Incorrect Squat: {incorrect_count}", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        # cv2.putText(image, feedback, (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)
        # cv2.putText(image, status, (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        # cv2.putText(image, f"Squat Time: {round(squat_duration, 2)} sec", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)
        
        
    except Exception as e:
        pass

    # Draw landmarks
    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                               mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                               mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2))

    
    
    # Display the output
    cv2.imshow('Squat Analysis', image)

    # Break loop on 'q' key press
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
