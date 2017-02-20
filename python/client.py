#!/usr/bin/env python

import logging
import time
import uhej_client
import socket
import threading
import os
import sys

logger = logging.getLogger()

def log_init(level):
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

_sock = None

def subscription_cb(service_name, host, port, is_subscribed):
    global _sock
    if is_subscribed:
        logger.info("Found service '%s' at %s:%d" % (service_name, host, port))
        _sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _sock.sendto("Hello!", (host, port))
    else:
        logger.info("Lost service '%s'" % (service_name))
        _sock.close()


log_init(logging.INFO);
logger.info("Client starting")

#os.environ['TZ'] = 'UTC'
#time.tzset()

node_id = 32768
try:
    ip = socket.gethostbyname(socket.gethostname())
except:
    ip = socket.gethostbyname(socket.gethostname()+".local")


mac = "aa:bb:cc:dd:ee:ff"
name = "Client Node"

uhej_client.init(subscription_cb, node_id, ip, mac, name)

counter = 0
while 1:
    uhej_client.subscribe_udp("test service");
    time.sleep(10)
    uhej_client.cancel_udp("test service")
    time.sleep(10)
