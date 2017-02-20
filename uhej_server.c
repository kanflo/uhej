/* 
 * The MIT License (MIT)
 * 
 * Copyright (c) 2017 Johan Kanflo (github.com/kanflo)
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

#include <esp8266.h>
#include <espressif/esp_common.h>
#include <stdint.h>
#include <sys/types.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <esp8266.h>
#include <esp/uart.h>
#include <stdio.h>
#include <FreeRTOS.h>
#include <semphr.h>
#include <task.h>
#include <timers.h>
#include <queue.h>
#include <ota-tftp.h>
#include <rboot-api.h>
#include <lwip/pbuf.h>
#include <lwip/udp.h>
#include <lwip/tcp.h>
#include <lwip/ip_addr.h>
#include <lwip/api.h>
#include <lwip/netbuf.h>
#include <lwip/igmp.h>
#include <ssid_config.h>
#include <espressif/esp_wifi.h>

#include "lwipopts.h"
#include "uhej.h"

/** User friendly FreeRTOS delay macro */
#define delay_ms(ms) vTaskDelay(ms / portTICK_PERIOD_MS)

/** Semaphore to signal wifi availability */
static SemaphoreHandle_t wifi_alive;

/**
  * @brief This is the multicast task
  * @param arg user supplied argument from xTaskCreate
  * @retval None
  */
static void mcast_task(void *arg)
{
    xSemaphoreTake(wifi_alive, portMAX_DELAY);
    xSemaphoreGive(wifi_alive);

    (void) uhej_server_init();
    (void) uhej_announce_udp("tftp", 69);
    (void) uhej_announce_udp("test service", 5000); /** @todo: create UDP service */
    while(1) {
        delay_ms(2000);
    }
}

/**
  * @brief This is the wifi connection task
  * @param arg user supplied argument from xTaskCreate
  * @retval None
  */
static void wifi_task(void *pvParameters)
{
    uint8_t status = 0;
    uint8_t retries = 30;
    struct sdk_station_config config = {
        .ssid = WIFI_SSID,
        .password = WIFI_PASS,
    };

    xSemaphoreTake(wifi_alive, portMAX_DELAY);
    printf("WiFi: connecting to WiFi\n");
    sdk_wifi_set_opmode(STATION_MODE);
    sdk_wifi_station_set_config(&config);

    while(1) {
        while (status != STATION_GOT_IP && retries) {
            status = sdk_wifi_station_get_connect_status();
            if(status == STATION_WRONG_PASSWORD) {
                printf("WiFi: wrong password\n");
                break;
            } else if(status == STATION_NO_AP_FOUND) {
                printf("WiFi: AP not found\n");
                break;
            } else if(status == STATION_CONNECT_FAIL) {
                printf("WiFi: connection failed\n");
                break;
            }
            delay_ms(1000);
            retries--;
        }
        if (status == STATION_GOT_IP) {
            printf("WiFi: connected\n");
            xSemaphoreGive(wifi_alive);
            taskYIELD();
        }

        while ((status = sdk_wifi_station_get_connect_status()) == STATION_GOT_IP) {
            xSemaphoreGive(wifi_alive);
            taskYIELD();
        }
        printf("WiFi: disconnected\n");
        sdk_wifi_station_disconnect();
        delay_ms(1000);
    }
}

void user_init(void)
{
    uart_set_baud(0, 115200);
    vSemaphoreCreateBinary(wifi_alive);
    ota_tftp_init_server(TFTP_PORT);
    xTaskCreate(&wifi_task, "wifi_task",  256, NULL, 2, NULL);
    delay_ms(250);
    xTaskCreate(&mcast_task, "mcast_task", 1024, NULL, 4, NULL);
}
