"""
@file serializer.py
@brief UART Communication Module for Embedded Systems
@details This module provides functionality for establishing UART connections and
         transmitting protobuf-encoded messages to embedded devices such as ESP32.
         Features include automatic port detection, configurable baud rates, and
         timestamped message transmission with binary protobuf serialization.

@author Juan Ignacio Giorgetti
@date 2025
@version 1.0

@dependencies
- pyserial: Serial port communication library
- protobuf: Protocol buffer serialization
- argparse: Command line argument parsing
- datetime: Timestamp generation

@usage
Command line execution:
    uv run serializer.py [--port PORT] [--baudrate RATE]

Examples:
    uv run serializer.py --port COM3 --baudrate 115200
    uv run serializer.py --port /dev/ttyUSB0
    uv run serializer.py --baudrate 300

@note Requires message_pb2.py generated from message.proto protobuf schema
@warning Ensure target device matches the configured baud rate for proper communication
"""

from time import timezone
import serial
import serial.tools.list_ports
import argparse
from datetime import datetime, timezone

import message_pb2  # Generated protobuf classes

TIMEOUT = 1  #!< Timeout in seconds for serial read/write operations


def setup_uart(port: str, baud_rate: int) -> serial.Serial | None:
    """
    @fn setup_uart
    @brief Initialize UART connection with the specified port and baud rate
    @details Creates a serial connection using the pyserial library with standard
             8N1 configuration (8 data bits, no parity, 1 stop bit). The function
             handles connection errors gracefully and returns None on failure.
    @param port String containing the serial port name (e.g., "COM3", "/dev/ttyUSB0")
    @param baud_rate Integer specifying the communication baud rate (e.g., 9600, 115200)
    @return Serial object if connection successful, None if connection fails
    @exception serial.SerialException Raised when port cannot be opened or configured
    @note Uses global TIMEOUT constant for read/write timeout configuration
    @warning Ensure the specified port exists and is not already in use by another application
    """
    try:
        ser = serial.Serial(
            port=port,
            baudrate=baud_rate,
            timeout=TIMEOUT,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
        )
        print(f"UART connection established on {port} at {baud_rate} baud")
        return ser
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        return None


def send_message(ser: serial.Serial, message: str, ts: int) -> None:
    """
    @fn send_message
    @brief Send a protobuf-encoded message over UART connection
    @details Creates a protobuf Payload object containing the message and timestamp,
             serializes it to binary format, and transmits it over the UART connection.
             The function validates the serial connection status before attempting transmission.
    @param ser Active serial.Serial object representing the UART connection
    @param message String containing the user message/data to be transmitted
    @param ts Integer Unix timestamp (seconds since epoch) to be included with the message
    @return None
    @exception Exception Generic exception handling for serialization or transmission errors
    @note Requires message_pb2.Payload protobuf class to be available
    @warning Function assumes the serial connection is valid and open
    """
    if ser and ser.is_open:
        try:
            # Convert message to protobuf and sends it over UART
            payload = message_pb2.Payload()
            payload.timestamp = ts
            payload.data = message
            message_bytes = payload.SerializeToString()
            print(f"Sending message: {ts}, {message}")
            ser.write(message_bytes)

        except Exception as e:
            print(f"Error sending message: {e}")
    else:
        print("UART connection not available")


def main():
    """
    @fn main
    @brief Main application entry point for the UART message sender
    @details Parses command line arguments for port and baud rate configuration,
             establishes UART connection, and runs the interactive message sending loop.
             Handles user input, timestamp generation, and graceful shutdown on interrupt.
    @return None
    @exception KeyboardInterrupt Handles Ctrl+C user interruption for clean shutdown
    @exception SystemExit Called when UART connection fails during initialization
    @note Defaults to first available serial port if --port not specified
    @note Defaults to 9600 baud if --baudrate not specified
    @note Uses UTC timezone for timestamp generation
    @warning Exits with code 1 if no serial connection can be established
    """
    parser = argparse.ArgumentParser(description="Select port and baudrate")
    parser.add_argument("--port", required=False, type=str)
    parser.add_argument("--baudrate", required=False, type=int)
    args = parser.parse_args()
    if args.port is None:
        args.port = sorted(serial.tools.list_ports.comports())[0][
            0
        ]  # First available port
    if args.baudrate is None:
        args.baudrate = 9600

    # Initialize UART connection with selected port
    ser = setup_uart(args.port, args.baudrate)

    if ser is None:
        print("Failed to establish UART connection. Exiting...")
        exit(1)

    try:
        print("\n=== UART Message Sender ===")
        print(f"Connected to port: {args.port} at {args.baudrate} baud \n")

        while True:
            msg = input("Enter a message or hit Ctrl+C to finish program: ")
            if len(msg) >= 113:
                print("Message too long, please limit to less than 113 characters.")
                continue
            ts = int(
                datetime.now(tz=timezone.utc).timestamp()
            )  # Convert to integer seconds
            send_message(ser, msg, ts)

    except KeyboardInterrupt:
        if ser and ser.is_open:
            ser.close()
            print("\nUART connection closed")
        print("\nProgram stopped by user")


if __name__ == "__main__":
    main()
