import time
import cv2
import numpy as np
import os
from datetime import datetime

print(cv2.getBuildInformation())

def detect_humans_in_image_with_yolo(path):
    print(f"Begining detection (YOLO) on {path}!")
    start_time = time.time()  # Start timing

    # Load YOLO
    net = cv2.dnn.readNet("yolo/yolov4.weights", "yolo/yolov4.cfg")
    
    # Enable CUDA
    
    layer_names = net.getLayerNames()
    out_layer_indices = net.getUnconnectedOutLayers()
    output_layers = [layer_names[i - 1] for i in out_layer_indices.flatten()]  # Properly handle the indices

    # Load image
    img = cv2.imread(path)
    if img is None:
        print(f"Failed to load image at {path}")
        return
    height, width, channels = img.shape

    # Convert to blob
    blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    # Showing information on the screen and get confidence score of algorithm in detecting an object in blob
    class_ids = []
    confidences = []
    boxes = []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if class_id == 0 and confidence > 0.5:  # Class ID 0 is generally 'person' in coco.names
                # Object detected
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)

                # Rectangle coordinates
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
    print(f"Detected {len(indexes)} humans in {path}")

    # Save detected humans
    save_dir = "humans"
    os.makedirs(save_dir, exist_ok=True)
    for i in indexes:
        x, y, w, h = boxes[i]
        human_img = img[y:y+h, x:x+w]
        timestamp = datetime.now().strftime("%H_%M_%S")
        filename = f"{os.path.splitext(os.path.basename(path))[0]}_{timestamp}.jpg"
        save_path = os.path.join(save_dir, filename)
        cv2.imwrite(save_path, human_img)
        print(f"Human saved in {save_path}")

    # End timing and print the duration
    end_time = time.time()
    print(f"Total processing time: {end_time - start_time:.2f} seconds")

def detect_humans_in_image_with_hog(path):
    print(f"Begining detection (HOG) on {path}!")
    start_time = time.time()  # Start timing
    
    # Load image
    img = cv2.imread(path)
    if img is None:
        print(f"Failed to load image at {path}")
        return
    
    # Initialize HOG descriptor and SVM detector
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    
    # Detect humans in the image
    rects, _ = hog.detectMultiScale(img, winStride=(8, 8), padding=(32, 32), scale=1.2, hitThreshold=0)
    
    # Save detected humans
    save_dir = "humans"
    os.makedirs(save_dir, exist_ok=True)
    for i, (x, y, w, h) in enumerate(rects):
        human_img = img[y:y+h, x:x+w]
        timestamp = datetime.now().strftime("%H_%M_%S")
        filename = f"{os.path.splitext(os.path.basename(path))[0]}_{timestamp}_{i}.jpg"
        save_path = os.path.join(save_dir, filename)
        cv2.imwrite(save_path, human_img)
        print(f"Human saved in {save_path}")
    
    # End timing and print the duration
    end_time = time.time()
    print(f"Total processing time: {end_time - start_time:.2f} seconds")
