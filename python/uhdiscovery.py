#!/usr/bin/env python
#
# Query local network for uHej services
#

import socket
import threading
import sys
from uhej import *


def worker_thread():
    global discovery_list
    global sock
    while 1:
        try:
            data, addr = sock.recvfrom(1024)
            port = addr[1]
            addr = addr[0]
            frame = bytearray(data)
            try:
                f = decode_frame(frame)
                f["source"] = addr
                f["port"] = port
                types = ["UDP", "TCP", "mcast"]
                if ANNOUNCE == f["frame_type"]:
                    for s in f["services"]:
                        key = "%s:%s:%s" % (f["source"], s["port"], s["type"])
                        if not key in discovery_list:
                            print("%16s:%-5d  %-8s %s" % (f["source"], s["port"], types[s["type"]], s["service_name"]))
                            discovery_list[key] = True # Keep track of which hosts we have seen
            except IllegalFrameException, e:
                pass
        except socket.error, e:
            print 'Expection', e


def main():
    global discovery_list
    global sock
    discovery_list = {}

    ANY = "0.0.0.0"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except AttributeError:
        pass
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
    sock.bind((ANY, MCAST_PORT))
#    sock.bind((MCAST_GRP, MCAST_PORT))

    thread = threading.Thread(target = worker_thread)
    thread.daemon = True
    thread.start()

    if 0:
        try:
            host = socket.gethostbyname(socket.gethostname()+".local")
        except:
            host = socket.gethostbyname(socket.gethostname())
        sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(host))
    sock.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(MCAST_GRP) + socket.inet_aton(ANY))

    run_time_s = 10 # Run query for this many seconds
    query_interval_s = 2 # Send query this often
    last_query = 0
    start_time = time.time()

    while time.time() - start_time < run_time_s:
        if time.time() - last_query > query_interval_s:
            f = query(UDP, "*")
            sock.sendto(f, (MCAST_GRP, MCAST_PORT))
            last_query = time.time()
        time.sleep(1)

    num_found = len(discovery_list)
    if num_found == 0:
        print("No services found")
    elif num_found == 1:
        print("1 service found")
    else:
        print("%d services found" % (num_found))
    sys.exit(0)

if __name__ == '__main__':
    main()
