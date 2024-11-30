from ultralytics import YOLO
from collections import deque
import json
import os

JSON_FILE = "objects.json"

def objDetection():
    model = YOLO("yolo11n.pt")  # load an official model
    results = model(source=0, stream=True)  # generator of Results objects
    
    for result in results: 
        add_json_object(result.to_json())
    

#results_pose = model_pose(source=0, stream=True)  # generator of Results objects
#model_pose = YOLO("yolo11n-pose.pt")


# for result in results_pose: 
#     boxes = result.boxes  # Boxes object for bounding box outputs
#     masks = result.masks  # Masks object for segmentation masks outputs
#     keypoints = result.keypoints  # Keypoints object for pose outputs
#     probs = result.probs  # Probs object for classification outputs
#     obb = result.obb  # Oriented boxes object for OBB outputs
#     result.save(filename="result.jpg")  # save to disk
#     print(result)
# Run inference on the source


# Function to load the JSON file
def load_json_file(filepath):
    try:
        with open(filepath, 'r') as file:
            data = json.load(file)
            return deque(data, maxlen=5)  # Convert the list to a deque with a max length of 5
    except (FileNotFoundError, json.JSONDecodeError):
        return deque(maxlen=5)  # Return an empty deque if the file doesn't exist or is invalid

# Function to save the deque back to the JSON file
def save_json_file(filepath, data):
    with open(filepath, 'w') as file:
        json.dump(list(data), file, indent=4)

# Function to add a new object to the JSON file
def add_json_object(new_object):
    data = load_json_file(JSON_FILE)  # Load existing data
    data.append(new_object)  # Add the new object, deque will handle the size limit
    save_json_file(JSON_FILE, data)  # Save updated data back to the file    