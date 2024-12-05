import os
import threading
import time
from flask import Flask, render_template_string, jsonify, request
import cv2
import numpy as np
from pyfirmata2 import Arduino
import requests

app = Flask(__name__)

# Configurações do Arduino
try:
    board = Arduino('COM8')  # Substitua pela porta correta do seu Arduino
    arduino_connected = True
    print("Arduino conectado via PyFirmata2.")
except Exception as e:
    board = None
    arduino_connected = False
    print(f"Erro ao conectar ao Arduino: {e}")

# Configurações do semáforo
car_cascade = cv2.CascadeClassifier('cars.xml')
image_dir = 'detected_images'

if not os.path.exists(image_dir):
    os.makedirs(image_dir)

image_filenames = []
semaphore_state = "Verde"
state_start_time = time.time()
durations = {'Verde': 10, 'Amarelo': 3, 'Vermelho': 5}
total_cars_detected = 0
current_car_count = 0

# Pinos do Arduino
if arduino_connected:
    red_led = board.digital[13]  # LED vermelho no pino digital 13
    yellow_led = board.digital[12]  # LED amarelo no pino digital 12
    green_led = board.digital[11]  # LED verde no pino digital 14

def set_semaphore_lights(state):
    """Define os LEDs do semáforo."""
    if not arduino_connected:
        return
    if state == "Verde":
        green_led.write(1)
        yellow_led.write(0)
        red_led.write(0)
    elif state == "Amarelo":
        green_led.write(0)
        yellow_led.write(1)
        red_led.write(0)
    elif state == "Vermelho":
        green_led.write(0)
        yellow_led.write(0)
        red_led.write(1)

def detect_cars(image):
    """Detecta carros na imagem."""
    global total_cars_detected, current_car_count, durations
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cars = car_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3)

    for (x, y, w, h) in cars:
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

    timestamp = int(time.time())
    filename = f'carro_detectado_{timestamp}.jpg'
    cv2.imwrite(os.path.join(image_dir, filename), image)

    image_filenames.append(filename)
    if len(image_filenames) > 10:
        oldest_image = image_filenames.pop(0)
        os.remove(os.path.join(image_dir, oldest_image))

    car_count = len(cars)
    total_cars_detected += car_count
    current_car_count = car_count
    calculate_durations(car_count)
    return car_count

def calculate_durations(car_count):
    """Ajusta a duração do semáforo com base no número de carros detectados."""
    global durations
    if car_count <= 3:
        durations = {'Verde': 10, 'Amarelo': 3, 'Vermelho': 5}
    elif 4 <= car_count <= 9:
        durations = {'Verde': 15, 'Amarelo': 3, 'Vermelho': 10}
    else:  # car_count > 9
        durations = {'Verde': 20, 'Amarelo': 3, 'Vermelho': 15}
    print(f"Durações ajustadas com base em {car_count} carros detectados: {durations}")

def update_semaphore_state():
    """Atualiza o estado do semáforo com base nas durações."""
    global semaphore_state, state_start_time, durations, arduino_connected
    try:
        set_semaphore_lights(semaphore_state)
        while True:
            elapsed_time = time.time() - state_start_time
            current_duration = durations[semaphore_state]

            if elapsed_time >= current_duration:
                if semaphore_state == 'Verde':
                    semaphore_state = 'Amarelo'
                elif semaphore_state == 'Amarelo':
                    semaphore_state = 'Vermelho'
                elif semaphore_state == 'Vermelho':
                    semaphore_state = 'Verde'

                set_semaphore_lights(semaphore_state)
                state_start_time = time.time()
            time.sleep(0.1)
    except Exception as e:
        print(f"Erro na thread do semáforo: {e}")

# Iniciar a thread do semáforo
threading.Thread(target=update_semaphore_state, daemon=True).start()
print("Thread do semáforo iniciada.")

@app.route('/dashboard_data')
def dashboard_data():
    """Retorna os dados do dashboard."""
    time_remaining = durations[semaphore_state] - (time.time() - state_start_time)
    if time_remaining < 0:
        time_remaining = 0
    return jsonify({
        "semaphore_state": semaphore_state,
        "state_duration": durations[semaphore_state],
        "time_remaining": int(time_remaining),
        "total_cars_detected": total_cars_detected,
        "image_filenames": image_filenames,
        "current_car_count": current_car_count,
        "arduino_connected": arduino_connected
    })

@app.route('/upload', methods=['POST'])
def upload_image():
    """Recebe imagens para detecção de carros."""
    if 'image/jpeg' in request.content_type:
        image_data = np.frombuffer(request.data, np.uint8)
        img = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

        car_count = detect_cars(img)
        duration_msg = determine_red_duration(car_count)

        send_to_arduino(duration_msg)
        return duration_msg, 200

    return "Invalid content type", 400

def determine_red_duration(car_count):
    """Define a duração do sinal vermelho com base nos carros detectados."""
    if car_count == 3:
        return "5 seconds red"
    elif 4 <= car_count <= 9:
        return "12 seconds red"
    elif car_count > 9:
        return "20 seconds red"
    return "No cars detected"

def send_to_arduino(message):
    """Envia uma mensagem ao Arduino via HTTP."""
    arduino_url = "http://192.168.220.81"  # Substitua pelo URL correto do Arduino
    try:
        response = requests.post(arduino_url, json={"message": message})
        print("Message sent to Arduino:", message)
        print("Response:", response.text)
    except Exception as e:
        print("Error sending message to Arduino:", e)

@app.route('/')
def dashboard():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard de Tráfego Inteligente</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {
                background-color: #2c2f33;
                color: #ffffff;
                font-family: 'Arial', sans-serif;
            }
            .glass-card {
                background: rgba(255, 255, 255, 0.2);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 10px;
                padding: 20px;
                margin: 10px 0;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .semaforo {
                width: 120px;
                height: 120px;
                margin: 20px auto;
                border-radius: 50%;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
            }
            .connected {
                color: #28a745;
            }
            .disconnected {
                color: #dc3545;
            }
        </style>
    </head>
    <body>
        <div class="container py-5">
            <h1 class="text-center mb-4">Dashboard de Tráfego Inteligente</h1>
            <div class="row">
                <div class="col-md-6 offset-md-3">
                    <div class="glass-card text-center">
                        <h2>Estado do Semáforo</h2>
                        <div id="traffic-light" class="semaforo bg-success"></div>
                        <p class="h5 mt-3">Estado: <strong id="semaphore-state">Verde</strong></p>
                        <p class="h5">Tempo Restante: <strong id="time-remaining">0</strong> segundos</p>
                        <p class="h5">Arduino: <strong id="arduino-status" class="connected">Conectado</strong></p>
                    </div>
                </div>
            </div>
            <div class="row mt-4">
                <div class="col-md-6 offset-md-3">
                    <div class="glass-card">
                        <h3>Total de Carros Detectados: <span id="total-cars-detected">0</span></h3>
                        <h4>Carros na Última Detecção: <span id="current-car-count">0</span></h4>
                        <p>Últimas 10 imagens detectadas:</p>
                        <ul id="image-list" class="list-group">
                            <!-- Lista de imagens será atualizada dinamicamente -->
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        <script>
            function updateDashboard() {
                fetch('/dashboard_data')
                    .then(response => response.json())
                    .then(data => {
                        const trafficLight = document.getElementById('traffic-light');
                        const semaphoreState = document.getElementById('semaphore-state');
                        const timeRemaining = document.getElementById('time-remaining');
                        const arduinoStatus = document.getElementById('arduino-status');

                        semaphoreState.textContent = data.semaphore_state;
                        timeRemaining.textContent = data.time_remaining;

                        trafficLight.className = 'semaforo';
                        if (data.semaphore_state == "Vermelho") {
                            trafficLight.classList.add('bg-danger');
                        } else if (data.semaphore_state == "Verde") {
                            trafficLight.classList.add('bg-success');
                        } else if (data.semaphore_state == "Amarelo") {
                            trafficLight.classList.add('bg-warning');
                        }

                        document.getElementById('total-cars-detected').textContent = data.total_cars_detected;
                        document.getElementById('current-car-count').textContent = data.current_car_count;

                        if (data.arduino_connected) {
                            arduinoStatus.textContent = "Conectado";
                            arduinoStatus.className = "connected";
                        } else {
                            arduinoStatus.textContent = "Desconectado";
                            arduinoStatus.className = "disconnected";
                        }

                        const imageList = document.getElementById('image-list');
                        imageList.innerHTML = '';
                        data.image_filenames.forEach(filename => {
                            const li = document.createElement('li');
                            li.className = 'list-group-item glass-card';
                            li.textContent = filename;
                            imageList.appendChild(li);
                        });
                    });
            }

            setInterval(updateDashboard, 1000);
        </script>
    </body>
    </html>
    """)
 

if __name__ == "__main__":
    try:
        print("Iniciando o servidor Flask...")
        app.run(host='0.0.0.0', port=5000)
    finally:
        if arduino_connected:
            board.exit()
            print("Conexão com o Arduino encerrada.")
