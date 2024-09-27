import cv2
import easyocr
import pandas as pd
from inference_sdk import InferenceHTTPClient

# Initialize the InferenceHTTPClient
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="fCG1GZQlr7RsoXfUl0If"
)

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'])

# Path to the video file
video_path = "C:\\Users\\ergou\\PycharmProjects\\pythonProject\\APLR\\data\\Traffic Control CCTV.mp4"

# Open the video file
cap = cv2.VideoCapture(video_path)

# Get the video's frame rate (FPS) and size
fps = cap.get(cv2.CAP_PROP_FPS)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
# example

# Calculate the number of frames to skip (3 seconds * FPS)
frames_to_skip = int(0.5 * fps)

# Initialize a list to store OCR results
ocr_results = []

# Frame counter to track which frame we're on
frame_count = 0

# Output video path
output_video_path = "processed_video_output.mp4"

# Initialize the video writer to save the output video
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

while cap.isOpened():
    ret, frame = cap.read()

    # Break the loop if no frame is captured (end of video)
    if not ret:
        break

    frame_count += 1

    # Process the frame only if it's the first frame or after skipping the defined interval
    if frame_count % frames_to_skip == 0:
        # Convert the frame to a suitable format for plate detection inference
        frame_path = f"temp_frame_{frame_count}.png"
        cv2.imwrite(frame_path, frame)

        # Perform plate detection inference
        result = CLIENT.infer(frame_path, model_id="vehicle-registration-plates-trudk/2")

        # Extract detection results from the frame
        predictions = result['predictions']

        for prediction in predictions:
            # Extract bounding box coordinates
            x = int(prediction['x'])
            y = int(prediction['y'])
            width = int(prediction['width'])
            height = int(prediction['height'])
            confidence = prediction['confidence']

            # Crop the license plate region from the frame
            start_x = max(x - width // 2, 0)
            start_y = max(y - height // 2, 0)
            end_x = min(x + width // 2, frame.shape[1])
            end_y = min(y + height // 2, frame.shape[0])

            cropped_plate = frame[start_y:end_y, start_x:end_x]

            # Apply OCR using EasyOCR
            ocr_result = reader.readtext(cropped_plate)
            if ocr_result:
                plate_text = ocr_result[0][1].strip()  # Extract the detected text
            else:
                plate_text = "No Text Detected"

            # Draw a bounding box around the detected license plate
            cv2.rectangle(frame, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)

            # Put the OCR result on the frame
            cv2.putText(frame, plate_text, (start_x, start_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

            # Store the result in a dictionary
            ocr_entry = {
                'frame': frame_count,
                'plate_text': plate_text,
                'confidence': confidence,
                'x': x,
                'y': y,
                'width': width,
                'height': height
            }

            # Append the result to the list
            ocr_results.append(ocr_entry)

        # Write the processed frame with annotations to the output video
        out.write(frame)

# Release the video capture and writer objects
cap.release()
out.release()

# Convert the OCR results to a pandas DataFrame
df = pd.DataFrame(ocr_results)

# Save the DataFrame to a CSV file
csv_path = "dataset_from_video.csv"
df.to_csv(csv_path, index=False)

print(f"OCR results saved to {csv_path}")
print(f"Processed video saved to {output_video_path}")
