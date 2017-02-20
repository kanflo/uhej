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
beacon_timeout_s = 5
query_time_s = 2

logger = logging.getLogger(__name__)

# Array of services we subscribe to, each item being a dictionary with the items:
# "name"       : string     - name of service
# "type"       : int        - type of service (uhej.UDP, uhej.TCP, uhej.MCAST)
# "subscribed" : bool       - True if we are subscribed to a service
# "timestamp"  : integer    - Unix timestamp of last beacon
# "addr"       : ip address - IP address of server where we found the subscription
# "port"       : integer    - port of server where we found the subscription
service_list = [] # Array of service dictionaties


def init(callback, node_id, ip, mac, name):
    global _callback
    _callback = callback
    print("uHej client '%s on %s:%d" % (name, MCAST_GRP, MCAST_PORT))
    _sock_init()
    _queue_init()
    _thread_init()
    f = hello(node_id, ip, mac, name)
    tx_sock.sendto(f, (MCAST_GRP, MCAST_PORT))

def subscribe_udp(service_name):
    logger.info("Subscribing to UDP service '%s'" % (service_name))
    service_list.append({'type':UDP, 'name':service_name, 'subscribed':False, 'timestamp':0, 'addr':None, 'port':None})

def cancel_udp(service_name):
    for service in service_list:
        if service["name"] == service_name:
            logger.info("Cancelling UDP service '%s'" % (service_name))
            service_list.remove(service)

def find_service(name, type):
    for service in service_list:
        if service["name"] == name and service["type"] == type:
            return service
    return None

### Private functions below ###

def _check_service_announcement(frame):
    global _callback
    addr = frame["source"]
    services = ["UDP", "TCP", "Multicast"]
    for ann_service in frame["services"]:
        name = ann_service["service_name"]
        type = ann_service["type"]
        port = ann_service["port"]
        service = find_service(name, type)
        if None != service:
            if not service["subscribed"]:
                logger.info("Found %s service '%s' at %s:%d" % (services[type], name, addr, port))
                _callback(name, addr, port, True)
            service["subscribed"] = True
            service["timestamp"] = time.time()
            service["addr"] = addr
            service["port"] = port

def _check_beacon(frame):
    global _callback
    match = False
    addr = frame["source"]
    for service in service_list:
        if service["addr"] == addr:
            if service["subscribed"]:
                logger.info("Beacon from %s service '%s'" % (addr, service["name"]))
                service["timestamp"] = time.time()
                match = True
            else:
                logger.warning("Beacon from %s for unsubscribed service '%s'" % (addr, service["name"]))
    if not match:
        logger.warning("Unknown beacon from %s" % (addr))

def _janitor():
    global _callback
    global tx_sock
    services = ["UDP", "TCP", "Multicast"]
    for service in service_list:
        if not service["subscribed"] and time.time() - service["timestamp"] > query_time_s:
            logger.info("Querying %s service '%s'" % (services[service["type"]], service["name"]))
            f = query(service["type"], service["name"])
            tx_sock.sendto(f, (MCAST_GRP, MCAST_PORT))

#   TODO, someday when I introduct beacons between a client and the service it subscribes to

#        elif service["subscribed"]:
#            if time.time() - service["timestamp"] > 2*beacon_timeout_s:
#                logger.info("Lost '%s'" % (service["name"]))
#                _callback(service["name"], None, None, False)
#                service["subscribed"] = False
#            elif time.time() - service["timestamp"] > beacon_timeout_s:
#                service["timestamp"] = time.time()
#                logger.info("Beacon to %s:%d" % (service["addr"], MCAST_PORT))
#                f = beacon()
#                tx_sock.sendto(f, (service["addr"], MCAST_PORT))



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
                f = decode_frame(frame)
                f["source"] = addr
                f["port"] = port
                if ANNOUNCE == f["frame_type"]:
                    logger.info("Announce frame from %s:%d" % (f["source"], f["port"]))
                    _check_service_announcement(f)
                elif HELLO == f["frame_type"]:
                    logger.info("Hello frame")
                elif BEACON == f["frame_type"]:
                    logger.info("Beacon frame")
                    _check_beacon(f)

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

    rx_sock.bind((ANY, MCAST_PORT))
    try:
        host = socket.gethostbyname(socket.gethostname())
    except:
        host = socket.gethostbyname(socket.gethostname()+".local")
    rx_sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(host))
    rx_sock.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(MCAST_GRP) + socket.inet_aton(ANY))

    tx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    tx_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
