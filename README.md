# PC-ESP32 Protobuf UART Communication System

This is a personal project demonstrating a bidirectional communication system between a PC and an ESP32 microcontroller using UART with Protocol Buffers for efficient data serialization.

It was developed as part of my embedded systems portfolio to showcase my skills in serial communication protocols, data serialization, and cross-platform system integration.

---

## 📐 System Overview

- **Microcontroller:** ESP32-S3 (or compatible ESP32 variants).
- **Communication:** UART/USB serial communication with Protocol Buffers.
- **PC Application:** Python serializer with interactive CLI interface.
- **Firmware:** C using ESP-IDF with protobuf-c library.
- **Data Format:** Binary protobuf messages with timestamped payloads.
- **Output:** JSON formatted messages on ESP32 with comprehensive logging.

---

## 🎯 Key Features

- Efficient binary serialization using Protocol Buffers.
- Bidirectional UART communication over USB/serial.
- Timestamped message transmission with Unix timestamps.
- Configurable UART parameters (port, baud rate).
- Cross-platform Python application (Windows, Linux, macOS):
```json
{
  "timestamp": 1758894299,
  "data": "Hello world!"
}
```
- Real-time message processing on ESP32.
- Interactive command-line interface for message input.
- Comprehensive error handling and logging system.
- Modular and scalable code structure:
    - Python serializer with command-line argument parsing.
    - ESP32 deserializer with FreeRTOS task management.
    - Unit testing framework with Pytest integration.

---

## 📊 System Architecture

```
┌─────────────────┐    UART/USB    ┌─────────────────┐
│   PC (Python)   │ ──────────────►│   ESP32 (C)     │
│                 │    Protobuf    │                 │
│  ┌─────────────┐│                │┌─────────────┐  │
│  │ Serializer  ││                ││Deserializer │  │
│  │   .py       ││                ││    .c       │  │
│  └─────────────┘│                │└─────────────┘  │
│                 │                │                 │
│ • User Input    │                │ • UART RX       │
│ • Timestamp     │                │ • Protobuf      │
│ • Protobuf      │                │ • JSON Output   │
│ • UART TX       │                │ • Logging       │
└─────────────────┘                └─────────────────┘
```

The system operates with:
- PC application sending protobuf-serialized messages via UART.
- ESP32 receiving binary data and deserializing to JSON format.
- Real-time logging and error handling on both ends.

---

## ⚙️ Technical Architecture

- **PC Side**: Python serializer reads user input and packages it with Unix timestamps.
- **Data Transmission**: Binary protobuf messages sent over UART/USB connection.
- **ESP32 Side**: Firmware deserializes incoming data and outputs JSON to console.
- **Protocol**: Custom protobuf schema with uint32 timestamp and string data fields.

---

## 🎨 Project Structure

```
protobuf-serialization/
├── README.md                     # This documentation
├── message.proto                 # Protobuf schema definition
├── pc/                           # Python PC application
│   ├── serializer.py             # Main Python serializer script
│   ├── message_pb2.py            # Generated Python protobuf classes
│   ├── pyproject.toml            # Python dependencies (uv package manager)
│   └── .venv/                    # Python virtual environment
└── esp32/   
    └── deserializer/             # ESP-IDF project
        ├── CMakeLists.txt        # ESP-IDF build configuration
        ├── sdkconfig             # ESP32 configuration
        ├── sdkconfig.diffbr      # ESP32 with different configuration (used for testing)
        ├── tests/
        │   ├── test_main.py      # Unit tests (using Pytest)
        │   ├── requirements.txt  # File with modules used in virtual environment
        │   └── pytest.ini        # Config file for unit tests
        └── main/
            ├── main.c            # ESP32 main application
            ├── message.pb-c.c    # Generated C protobuf code
            ├── message.pb-c.h    # Generated C protobuf headers
            └── CMakeLists.txt    # Component build config
```

---

## Quick Start Guide

### Hardware Requirements

**PC Side:**
- **Operating System**: Windows, Linux, or macOS
- **Python**: Version 3.10 or higher
- **USB Port**: For UART communication with ESP32

**ESP32 Side:**
- **ESP32 Development Board** (ESP32S3-DevKitC or similar)
- **USB Cable**: USB-A to Micro-USB or USB-C (depending on board)

### Development Environment Setup

**Required Tools:**

**For PC Development:**
- Python 3.10+
- uv package manager
- Protocol Buffers compiler (`protoc`)
- PIP package manager (for unit testing)

**For ESP32 Development:**
- ESP-IDF v4.4+ (recommended v5.0+)
- Espressif toolchain
- Protocol Buffers C compiler (`protoc-c`)
- ClangFormat (for code styling)

### Installation and Usage

**1. Download and Setup**

```powershell
git clone <repository-url>
cd protobuf-serialization
```
**2. Protobuf Schema**

The communication protocol is defined in `message.proto`:

```protobuf
syntax = "proto3";

message Payload {
  uint32 timestamp = 1;  // Unix timestamp (seconds)
  string data = 2;       // Message content
}
```

**3. PC Application Setup**

```powershell
# Navigate to PC directory
cd pc

# Install uv package manager (if not installed)
pip install uv

# Install dependencies
uv sync

# Basic usage (auto-detects first available port, 9600 baud)
uv run serializer.py

# Advanced usage with custom parameters
uv run serializer.py --port "COM8" --baudrate 115200
```

**4. ESP32 Application Setup**

```powershell
# Open ESP-IDF Terminal (wherever is located in your system)

# Navigate to ESP32 directory
cd esp32\deserializer

# Configure and build project
idf.py menuconfig
idf.py build

# Flash to ESP32 (replace COM3 with your port)
idf.py -p COM3 flash monitor
```

### UART Configuration

Default UART settings for both programs:
- **UART Port**: Port 2 (ESP32) - First available port (PC) (Configurable)
- **Baud Rate**: 9600 (configurable)
- **Data Bits**: 8
- **Parity**: None
- **Stop Bits**: 1
- **Flow Control**: None

---

## 🧪 Testing

The project includes comprehensive unit tests using Pytest:

```powershell
# Navigate to tests directory
cd esp32/deserializer/tests

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1     # Windows

# Install test dependencies
pip install -r requirements.txt

# Run tests
cd ..
pytest .\tests\test_main.py
```

---

## 🚀 Future Improvements

- **Enhanced Protocol**: Support for multiple message types and data structures.
- **Encryption**: TLS/SSL encryption for secure communication channels.
- **GUI Application**: Desktop interface for easier message management.
- **Data Logging**: Persistent storage of transmitted messages with timestamps.
- **Multi-device Support**: Simultaneous communication with multiple ESP32 devices.
- **Real-time Dashboard**: Web-based interface for monitoring communication status.
