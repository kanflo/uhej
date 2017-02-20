#!/usr/bin/env python

import socket
import binascii
from uhej import *
import logging

logger = logging.getLogger()

def log_init(level):
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def main():
    log_init(logging.INFO);

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
    if 0:
        try:
            host = socket.gethostbyname(socket.gethostname()+".local")
        except:
            host = socket.gethostbyname(socket.gethostname())
        logger.info("Sniffer starting on %s" % host)

        sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(host))
    sock.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(MCAST_GRP) + socket.inet_aton(ANY))

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
                hexdata = binascii.hexlify(data)
                services = ["UDP", "TCP", "Multicast"]
                if ANNOUNCE == f["frame_type"]:
                    logger.info("Announce frame")
                    print f
                elif HELLO == f["frame_type"]:
                    logger.info("Hello frame")
                    print f
                elif QUERY == f["frame_type"]:
                    logger.info("Query %s service '%s' from %s", services[f["service_type"]], f["service_name"], f["source"])
            except IllegalFrameException, e:
                print("%s:%d Illegal frame '%s'" % (addr, port, frame))

        except socket.error, e:
            print 'Expection'
            hexdata = binascii.hexlify(data)
            print 'Data = %s' % hexdata

if __name__ == '__main__':
    main()
