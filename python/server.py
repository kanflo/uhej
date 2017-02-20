#!/usr/bin/env python

import logging
import time
import uhej_server
import socket
import threading
import os

logger = logging.getLogger()

PORT = 5000
sock = None

def log_init(level):
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def open_socket(port):
    s = None
    while s == None:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind(("", port))
        except socket.error, e:
            logger.info("Socket in use")
    return s

def service_thread():
    global sock
    while 1:
        if sock == None:
            time.sleep(1)
        else:
            try:
                data, addr = sock.recvfrom(1024)
                port = addr[1]
                addr = addr[0]
                logger.info("Got message: '%s' from %s" % (data, addr))
            except socket.error, e:
                print "sock error", e


thread = threading.Thread(target = service_thread)
thread.daemon = True
thread.start()


log_init(logging.INFO);
logger.info("Server starting")

#os.environ['TZ'] = 'UTC'
#time.tzset()

uhej_server.init()

if 1:
    logger.info("Service on %s:%d" % (uhej_server.get_local_ip(), PORT))
    sock = open_socket(PORT)
    uhej_server.announce_udp("test service", PORT)
    uhej_server.announce_udp("tftp", 69)
    while 1:
        time.sleep(10)
else:
    counter = 0
    while 1:
        logger.info("Service on %s:%d" % (uhej_server.get_local_ip(), PORT))
        sock = open_socket(PORT)
        uhej_server.announce_udp("test service", PORT)
        time.sleep(10)
        sock.close()
        sock = None
        uhej_server.cancel("test service")
        time.sleep(10)
