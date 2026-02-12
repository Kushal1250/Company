# VoiceMind Meeting Intelligence System

AI-powered meeting recording and analysis system with multilingual support.

## Features

- 🎙️ Real-time audio recording via ESP32 + I2S microphone
- 📡 WiFi streaming to cloud server (no SD card required)
- 🗄️ MySQL database storage with chunked audio
- 🌍 Multilingual transcription (100+ languages)
- 🤖 AI-powered Q&A using GPT
- 📊 Automatic meeting summarization
- 💬 Interactive command-line interface

## System Requirements

### Hardware
- ESP32 DevKit (with WiFi)
- INMP441 I2S MEMS Microphone
- 5V USB Power Supply
- Breadboard and jumper wires

### Software
- Python 3.8 or higher
- MySQL 8.0 or higher
- Arduino IDE (for ESP32 programming)
- OpenAI API key

## Installation

### 1. Clone Repository
```bash
git clone <reposit0ory-url>
cd VoiceMind-Meeting-System
