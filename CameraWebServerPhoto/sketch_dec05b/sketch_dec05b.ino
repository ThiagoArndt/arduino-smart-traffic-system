#include <Arduino.h>

// Define os pinos para os LEDs e botão de pedestre
const int redLedPin = 4;
const int yellowLedPin = 5;  // Alterado de 0 para 5
const int greenLedPin = 2;
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
}

void loop() {
  // Verifica se há dados disponíveis na porta serial
  if (Serial.available() > 0) {
    // Lê o comando recebido
    char command = Serial.read();

    // Desliga todos os LEDs inicialmente
    digitalWrite(redLedPin, LOW);
    digitalWrite(yellowLedPin, LOW);
    digitalWrite(greenLedPin, LOW);

    // Verifica qual comando foi recebido e acende o LED correspondente
    if (command == 'R') {
      digitalWrite(redLedPin, HIGH);     // Acende o LED vermelho
    } else if (command == 'Y') {
      digitalWrite(yellowLedPin, HIGH);  // Acende o LED amarelo
    } else if (command == 'G') {
      digitalWrite(greenLedPin, HIGH);   // Acende o LED verde
    }
  }

  // Verifica se o botão de pedestre foi pressionado
  if (digitalRead(pedestrianSwitchPin) == LOW) {
    // Envia um sinal para o Python
    Serial.println("PedestrianButtonPressed");
    // Aguarda o botão ser liberado
    while (digitalRead(pedestrianSwitchPin) == LOW) {
      delay(10);
    }
  }
}
