/**
 * @file main.c
 * @brief ESP32 Protobuf Deserializer Application
 *
 * This application receives protobuf-serialized data via UART, deserializes it,
 * and converts it to JSON format for further processing. It implements a UART
 * communication interface with protobuf-c library integration.
 *
 * @author Juan Ignacio Giorgetti
 * @date 2025
 * @version 1.0
 */

#include <stdio.h>
#include <string.h>

#include "cJSON.h"
#include "driver/uart.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#include "message.pb-c.h"
#include "sdkconfig.h"

// UART configuration parameters from Kconfig
#define UART_NUM CONFIG_DESERIALIZER_UART_NUMBER
#define UART_TX CONFIG_DESERIALIZER_UART_TX_PIN
#define UART_RX CONFIG_DESERIALIZER_UART_RX_PIN
#define UART_BAUD_RATE CONFIG_DESERIALIZER_UART_BAUD_RATE

// Buffer and task configuration
#define BUFF_SIZE 256
#define QUEUE_SIZE 5
#define TASK_MEM 1024 * 4

// Global variables
char const* TAG = "Deserializer";
static QueueHandle_t uart_queue;

// Function prototypes
static void uart_init(void);
static void uart_task(void* arg);
static void show_payload_as_json(Payload const* payload);

/**
 * @fn void app_main(void)
 * @brief Main application entry point
 *
 * Initializes the UART interface.
 * This is the main entry point called by the ESP-IDF framework after
 * system initialization is complete.
 *
 * @return void
 */
void app_main(void) { uart_init(); }

/**
 * @fn void uart_init(void)
 * @brief Initialize UART interface for protobuf communication
 *
 * Configures and initializes the UART peripheral with the following settings:
 * - Baud rate: Configurable via Kconfig (default 9600)
 * - Data bits: 8
 * - Parity: None
 * - Stop bits: 1
 * - Flow control: None
 * - Source clock: APB clock
 *
 * If any configuration step fails, an error is logged and the function returns early.
 * A stabilization delay is included to ensure proper hardware initialization.
 * Finally, it creates the UART processing task to handle incoming data.
 *
 * @return void
 *
 * @note This function must be called before starting the UART task
 * @note The UART pins and port are configured via Kconfig parameters
 */
void uart_init(void) {
    uart_config_t uart_config = {
        .baud_rate = UART_BAUD_RATE,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_APB,
    };

    if (uart_param_config(UART_NUM, &uart_config)) {
        ESP_LOGE(TAG, "Failed to configure UART parameters");
        return;
    }

    if (uart_set_pin(UART_NUM, UART_TX, UART_RX, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE)) {
        ESP_LOGE(TAG, "Failed to set UART pins");
        return;
    }

    if (uart_driver_install(UART_NUM, BUFF_SIZE, BUFF_SIZE, QUEUE_SIZE, &uart_queue, 0)) {
        ESP_LOGE(TAG, "Failed to install UART driver");
        return;
    }

    // Small delay to allow system to stabilize
    vTaskDelay(pdMS_TO_TICKS(100));

    ESP_LOGI(TAG, "Uart initialized on port %d with TX pin %d, RX pin %d at baud rate %d", UART_NUM,
            UART_TX, UART_RX, UART_BAUD_RATE);

    xTaskCreate(uart_task, "uart_task", TASK_MEM, NULL, 5, NULL);
}

/**
 * @fn void uart_task(void *arg)
 * @brief UART data processing task for protobuf deserialization
 *
 * This FreeRTOS task continuously monitors the UART queue for incoming data
 * events and processes them accordingly. When protobuf data is received,
 * it deserializes the binary data into a Payload structure and converts
 * it to JSON format for logging and further processing.
 *
 * The task performs the following operations:
 * 1. Clears any residual data from previous operations.
 * 2. Initializes a buffer for incoming data.
 * 3. Waits for UART events from the queue.
 * 4. Reads binary data from UART buffer.
 * 5. Deserializes protobuf data.
 * 6. Converts deserialized data to JSON format.
 * 7. Logs the results, cleans up memory and flushes UART buffer.
 *
 * @param arg Pointer to task parameters (unused, set to NULL)
 *
 * @return void (task runs indefinitely)
 *
 * @note This task allocates BUFF_SIZE bytes for incoming data buffer
 * @note Task will log errors if memory allocation or deserialization fails
 * @note Task will also handle UART the unlikely events of FIFO overflow and RX buffer full
 *       logging the error and flushing the UART buffer and resetting the queue.
 */
void uart_task(void* arg) {
    // Clear any residual data in UART buffer before starting
    uart_flush(UART_NUM);
    xQueueReset(uart_queue);
    uart_event_t evt;
    int len;
    Payload* payload = NULL;
    uint8_t* data = (uint8_t*)malloc(BUFF_SIZE);  // Allocate buffer for incoming data
    if (data == NULL) {
        ESP_LOGE(TAG, "Error creating incoming data buffer");
        return;
    }

    ESP_LOGI(TAG, "UART task started, waiting for incoming data...");

    while (1) {
        if (xQueueReceive(uart_queue, (void*)&evt, (TickType_t)portMAX_DELAY)) {
            bzero(data, BUFF_SIZE);  // Clear buffer before reading new data
            switch (evt.type) {
            case UART_DATA:
                // Read incoming data from UART and unpack protobuf message
                len = uart_read_bytes(UART_NUM, data, evt.size, pdMS_TO_TICKS(100));
                payload = payload__unpack(NULL, len, data);
                if (payload == NULL) {
                    ESP_LOGE(TAG, "Failed to unpack payload");
                    break;
                }
                // Process the unpacked payload
                ESP_LOGI(TAG, "Received payload of length %d bytes", len);
                show_payload_as_json(payload);
                payload__free_unpacked(payload, NULL);
                uart_flush(UART_NUM);  // Clear UART RX buffer
                break;
            case UART_FIFO_OVF:
                ESP_LOGW(TAG, "UART FIFO overflow");
                uart_flush(UART_NUM);
                xQueueReset(uart_queue);
                break;
            case UART_BUFFER_FULL:
                ESP_LOGW(TAG, "UART buffer full");
                uart_flush(UART_NUM);
                xQueueReset(uart_queue);
                break;
            default:
                break;
            }
        }
    }
    // Clean up (though this point is never reached in the current design)
    free(data);
    data = NULL;
    vTaskDelete(NULL);
}

/**
 * @fn void show_payload_as_json(const Payload *payload)
 * @brief Convert protobuf Payload to JSON format and log it
 *
 * This function takes a deserialized protobuf Payload structure and converts
 * it to a JSON representation using the cJSON library. The resulting JSON
 * string is logged via ESP_LOGI and then properly cleaned up. Also logs the
 * length of the JSON string.
 *
 * The JSON structure includes:
 * - "timestamp": 32-bit unsigned integer value from payload->timestamp
 * - "data": string value from payload->data
 *
 * @param payload Pointer to the deserialized Payload structure to convert
 *                Must not be NULL and must be a valid Payload object
 *
 * @return void
 *
 * @note The function checks for NULL payload and logs an error if so.
 * @note Function handles all memory allocation and cleanup internally
 * @note Logs errors if JSON creation or string conversion fails
 * @note Uses cJSON_PrintUnformatted for compact JSON output
 * @note The input payload is not modified (const parameter)
 */
void show_payload_as_json(Payload const* payload) {
    if (payload == NULL) {
        ESP_LOGE(TAG, "Payload is NULL, cannot convert to JSON");
        return;
    }
    cJSON* json = cJSON_CreateObject();
    if (json == NULL) {
        ESP_LOGE(TAG, "Failed to create JSON object");
        return;
    }

    if (cJSON_AddNumberToObject(json, "timestamp", payload->timestamp) == NULL) {
        ESP_LOGE(TAG, "Failed to add timestamp to JSON");
        goto error;
    }

    if (cJSON_AddStringToObject(json, "data", payload->data) == NULL) {
        ESP_LOGE(TAG, "Failed to add data to JSON");
        goto error;
    }

    char* json_string = cJSON_PrintUnformatted(json);
    if (json_string == NULL) {
        ESP_LOGE(TAG, "Failed to print JSON");
        goto error;
    }

    ESP_LOGI(TAG, "JSON payload created: %s", json_string);
    ESP_LOGI(TAG, "JSON payload length: %d bytes", strlen(json_string));

    // Clean up
    free(json_string);
error:
    cJSON_Delete(json);
    return;
}
