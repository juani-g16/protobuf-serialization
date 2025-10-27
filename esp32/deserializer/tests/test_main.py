import sys
import os
import time
import pytest
import serial

# Add the path to generated protobuf files
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "pc"))
import message_pb2  # pyright: ignore[reportMissingImports]


# Test to check if the UART is configured correctly based on the build configuration
@pytest.mark.parametrize(
    "config, build_dir",
    [
        ("defaults", "build"),
        ("diffbr", "build_diffbr"),
    ],
)
def test_uart_config(dut, config):
    if config == "defaults":
        dut.expect(
            "Uart initialized on port 2 with TX pin 42, RX pin 41 at baud rate 9600",
            timeout=5,
        )
    elif config == "diffbr":
        dut.expect(
            "Uart initialized on port 2 with TX pin 21, RX pin 20 at baud rate 115200",
            timeout=5,
        )


# Fixture to initialize default UART connection for the user (test script)
@pytest.fixture(scope="session")
def user_uart():
    ser = serial.Serial(
        "COM8",
        baudrate=9600,
        timeout=1,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
    )
    yield ser
    ser.close()


# Helper function to create protobuf message
def create_protobuf_payload(timestamp: int, data: str):
    payload = message_pb2.Payload()
    payload.timestamp = timestamp
    payload.data = data
    return payload.SerializeToString()


# Test to verify the correct number of bytes are processed and logged
def test_right_amount_of_bytes(dut, user_uart: serial.Serial):
    # Create and send message
    serialized_msg = create_protobuf_payload(1727185234, "Hello, world!")

    time.sleep(1)  # Wait before sending
    user_uart.write(serialized_msg)
    user_uart.flush()
    time.sleep(1)  # Wait after sending

    # Expects 13 bytes of data (length of "Hello, world!") + 8 bytes of timestamp
    # and protobuf overhead (should be 21 bytes total)
    dut.expect(
        "Received payload of length 21 bytes",
        timeout=5,
    )
    # Expects JSON payload length of 47 bytes (data: 21 bytes and JSON overhead: 26 bytes)
    dut.expect(
        "JSON payload length: 47 bytes",
        timeout=5,
    )


# Test to verify handling of various valid message sizes
@pytest.mark.parametrize(
    "timestamp,test_string",
    [
        (1727185234, "short"),
        (1727185235, "medium length message"),
        (1727185236, "A" * 100),
        (1727185237, "@#$%^&()"),
        (1727185238, ""),
    ],
    ids=[
        "short_string",
        "medium_string",
        "long_string",
        "special_chars",
        "empty_string",
    ],
)
def test_protobuf_various_valid_sizes(
    dut, user_uart: serial.Serial, timestamp, test_string
):
    # Create and send message
    serialized_msg = create_protobuf_payload(timestamp, test_string)

    time.sleep(1)  # Wait before sending
    user_uart.write(serialized_msg)
    user_uart.flush()
    time.sleep(1)  # Wait after sending

    # For special characters, avoid regex issues by using expect_exact
    if test_string == "@#$%^&()":
        dut.expect_exact(
            f'JSON payload created: {{"timestamp":{timestamp},"data":"{test_string}"}}',
            timeout=5,
        )
    else:
        # Expect successful processing for normal strings
        dut.expect(
            f'JSON payload created: {{"timestamp":{timestamp},"data":"{test_string}"}}',
            timeout=5,
        )


# Test to verify handling of maximum size message (112 bytes of data)
def test_protobuf_max_size_message(dut, user_uart):
    # Create a protobuf message with maximum allowed size (112 bytes of data)
    serialized_msg = create_protobuf_payload(1727185234, "A" * 112)

    time.sleep(1)  # Wait before sending
    user_uart.write(serialized_msg)
    user_uart.flush()
    time.sleep(1)  # Wait after sending

    # Expect successful processing
    dut.expect(
        f'JSON payload created: {{"timestamp":1727185234,"data":"{"A"*112}"}}',
        timeout=5,
    )


# Test to verify handling of over-maximum size message (113 bytes of data or more)
def test_protobuf_over_max_size_message(dut, user_uart: serial.Serial):
    # Create and send a 200-byte message (should fail to unpack)
    serialized_msg = create_protobuf_payload(1727185234, "A" * 113)

    time.sleep(1)  # Wait before sending
    user_uart.write(serialized_msg)
    user_uart.flush()
    time.sleep(1)  # Wait after sending

    # Expect failure message
    dut.expect("Failed to unpack payload", timeout=5)
