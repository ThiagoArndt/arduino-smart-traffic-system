from flask import Flask, request
import cv2
import numpy as np
import requests
import time  
app = Flask(__name__)

car_cascade = cv2.CascadeClassifier('cars.xml')

def detect_cars(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    cars = car_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3)
    
    for (x, y, w, h) in cars:
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    
    timestamp = int(time.time())  
    filename = f'detected_car_image_{timestamp}.jpg'
    cv2.imwrite(filename, image)
    
    return len(cars)

def determine_red_duration(car_count):
    if car_count == 3:
        return "5 seconds red"
    elif 4 <= car_count <= 9:
        return "12 seconds red"
    elif car_count > 9:
        return "20 seconds red"
    return "No cars detected"

def send_to_arduino(message):
    arduino_url = "http://192.168.0.22/arduino-endpoint"
    requests.post(arduino_url, json={"message": message})

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image/jpeg' in request.content_type:
        image_data = np.frombuffer(request.data, np.uint8)
        img = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

        car_count = detect_cars(img)
        
        duration_msg = determine_red_duration(car_count)
        
        send_to_arduino(duration_msg)

        return duration_msg, 200

    return "Invalid content type", 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
