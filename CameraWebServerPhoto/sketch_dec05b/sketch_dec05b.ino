#include <Arduino.h>

// Define os pinos para os LEDs
const int redLedPin = 13;
const int yellowLedPin = 12;
const int greenLedPin = 14;

// Duração de cada estado do semáforo em milissegundos
const int redDuration = 5000;    // 5 segundos para o vermelho
const int yellowDuration = 2000; // 2 segundos para o amarelo
const int greenDuration = 5000;  // 5 segundos para o verde

// Pino para o botão de pedestre
const int pedestrianSwitchPin = 23;

void setup() {
  // Inicializa os pinos dos LEDs como saída
  pinMode(redLedPin, OUTPUT);
  pinMode(yellowLedPin, OUTPUT);
  pinMode(greenLedPin, OUTPUT);

  // Inicializa o pino do botão de pedestre como entrada com pull-up interno
  pinMode(pedestrianSwitchPin, INPUT_PULLUP);

  // Inicia a comunicação serial
  Serial.begin(9600);
  Serial.println("Semáforo iniciado.");
}

void loop() {
  // Loop infinito para alternar as cores do semáforo

  // Estado: Vermelho
  Serial.println("Estado: Vermelho");
  digitalWrite(redLedPin, HIGH);
  digitalWrite(yellowLedPin, LOW);
  digitalWrite(greenLedPin, LOW);
  delay(redDuration);

  // Estado: Verde
  Serial.println("Estado: Verde");
  digitalWrite(redLedPin, LOW);
  digitalWrite(yellowLedPin, LOW);
  digitalWrite(greenLedPin, HIGH);
  delay(greenDuration);

  // Estado: Amarelo
  Serial.println("Estado: Amarelo");
  digitalWrite(redLedPin, LOW);
  digitalWrite(yellowLedPin, HIGH);
  digitalWrite(greenLedPin, LOW);
  delay(yellowDuration);

  // Verifica se o botão de pedestre foi pressionado
  if (digitalRead(pedestrianSwitchPin) == LOW) {
    Serial.println("Botão de pedestre pressionado. Voltando ao estado vermelho.");
    digitalWrite(redLedPin, HIGH);
    digitalWrite(yellowLedPin, LOW);
    digitalWrite(greenLedPin, LOW);

    // Aguarda o botão ser liberado
    while (digitalRead(pedestrianSwitchPin) == LOW) {
      delay(10);
    }

    // Permanece no estado vermelho por mais tempo para os pedestres
    delay(5000);
  }
}
