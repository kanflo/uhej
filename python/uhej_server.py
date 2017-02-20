"""
 The MIT License (MIT)
 
 Copyright (c) 2017 Johan Kanflo (github.com/kanflo)
 
 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:
 
 The above copyright notice and this permission notice shall be included in
 all copies or substantial portions of the Software.
 
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 THE SOFTWARE.
"""

import time
import threading
import socket
import binascii
import Queue
from uhej import *
import logging

rx_timeout_s = 1

logger = logging.getLogger(__name__)

# Array of dictionaries
# 'name' : string   name of service
# 'type' : int8     type of service (uhej_protocol.UDP, uhej_protocol.TCP, uhej_protocol.MCAST)
# 'port' : int16    port where service is located
# 'ip'   : int32    ip (for multicast services)
# 'subscribers'   : array   array of ip addresses subscribing to this service
service_list = []


def init():
    _sock_init()
    _queue_init()
    _thread_init()

def announce_udp(service_name, port):
    logger.info("Advertising UDP '%s' on port %d" % (service_name, port))
    service_list.append({'type':UDP, 'name':service_name, 'port':port, 'subscribers':[]})

def announce_tcp(service_name, port):
    logger.info("Advertising TCP service '%s' on port %d" % (service_name, port))
    service_list.append({'type':TCP, 'name':service_name, 'port':port, 'subscribers':[]})

def announce_mcast(service_name, ip, port):
    logger.info("Advertising multicast service '%s' on %s:%d" % (service_name, ip, port))
    service_list.append({'type':MCAST, 'name':service_name, 'port':port, 'ip':ip, 'subscribers':[]})

def cancel_udp(name):
    _cancel(name, UDP)

def cancel_tcp(name):
    _cancel(name, TCP)

def cancel_mcast(name):
    _cancel(name, MCAST)



### Private functions below ###

def _cancel(name, type):
    for service in service_list:
        if service["name"] == name and service["type"] == type:
            logger.info("Cancelling '%s' [%s]" % (name, type))
            service_list.remove(service)

def _janitor():
    global tx_sock

#   TODO, someday when I introduct beacons between a client and the service it subscribes to
#    for service in service_list:
#        for client in service["subscribers"]:
#            f = beacon()
#            logger.info("Beacon to %s" % client)
#            tx_sock.sendto(f, (client, MCAST_PORT))

def _comms_thread():
    global rx_sock
    global q
    logger.info("uHej server thread")
    while 1:
        try:
            data, addr = rx_sock.recvfrom(1024)
            q.put((addr, data))
        except Exception, e:
            logger.error("Exception")
            raise e

def _check_query(frame):
    services = ["UDP", "TCP", "Multicast"]
    if frame["service_name"] == "*":
        logger.info("Answering service wildcard")
        a = announce(service_list)
        try:
            tx_sock.sendto(a, (frame["source"], MCAST_PORT))
        except IOError, e:
            logger.warn("Got IOError ", e)
            raise e
    else:
        for service in service_list:
            if service["name"] == frame["service_name"] and service["type"] == frame["service_type"]:
                logger.info("Answering %s service '%s'" % (services[frame["service_type"]], frame["service_name"]))
                a = announce([service])
                service["subscribers"].append(frame["source"])
                try:
                    tx_sock.sendto(a, (frame["source"], MCAST_PORT))
                except IOError, e:
                    logger.warn("Got IOError ", e)
                    raise e

def _worker_thread():
    global q
    logger.info("uHej worker thread")
    while 1:
        data = addr = None
        try:
            addr, data = q.get(timeout = rx_timeout_s)
        except Queue.Empty:
            _janitor()
        if data != None and addr != None:
            port = addr[1]
            addr = addr[0]
            frame = bytearray(data)
            try:
                services = ["UDP", "TCP", "Multicast"]
                f = decode_frame(frame)
                f["source"] = addr
                f["port"] = port
                hexdata = binascii.hexlify(data)
                if QUERY == f["frame_type"]:
                    logger.info("Query %s service '%s' from %s", services[f["service_type"]], f["service_name"], f["source"])
                    _check_query(f)
                elif HELLO == f["frame_type"]:
                    logger.info("Hello from %s (%s)" % (f["source"], f["name"]))
                else:
                    logger.info("Unhandled frame type %d" % (f["frame_type"]))
                    print f

            except IllegalFrameException, e:
                logger.info("%s:%d Illegal frame '%s'" % (addr, port, frame))

def _start_thread(thread):
    thread = threading.Thread(target = thread)
    thread.daemon = True
    thread.start()

def _thread_init():
    _start_thread(_comms_thread)
    _start_thread(_worker_thread)

def _queue_init():
    global q
    q = Queue.Queue()

def _sock_init():
    global rx_sock
    global tx_sock
    ANY = "0.0.0.0"
    rx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    try:
        rx_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except AttributeError:
        pass
    rx_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32) 
    rx_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
#    rx_sock.bind((ANY, MCAST_PORT))
    rx_sock.bind((MCAST_GRP, MCAST_PORT))
    try:
        host = socket.gethostbyname(socket.gethostname()+".local")
    except:
        host = socket.gethostbyname(socket.gethostname())
    rx_sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(host))
    rx_sock.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(MCAST_GRP) + socket.inet_aton(host))

    tx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    tx_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
