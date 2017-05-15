**uHej**
==========

I needed a way to query the network for firmware upgradeable ESP8266 nodes and this is the outcome. It is basically a service advertisement protocol in a few hundred lines of C code. A python implementation is also available.

### Usage

Include "uhej.h" and call the following to have your ESP8266 node advertise its services:

```
    if (uhej_server_init() &&
   	    uhej_announce_udp("tftp", 69) &&
	    uhej_announce_udp("test service", 5000))
    {
       ...
    }

```

Next, run ```uhdiscovery.py```:

```
% ./python/uhdiscovery.py
    172.16.3.154:5000   UDP      test service
    172.16.3.154:69     UDP      tftp
    172.16.3.203:69     UDP      tftp
3 services found
```

Of course, you can have anything advertise a service. A python script:

```
% ./python/server.py
2017-02-20 23:46:02,350 - root - INFO - Server starting
2017-02-20 23:46:07,604 - uhej_server - INFO - uHej server thread
2017-02-20 23:46:07,605 - uhej_server - INFO - uHej worker thread
2017-02-20 23:46:07,605 - root - INFO - Service on 172.16.3.154:5000
2017-02-20 23:46:07,605 - uhej_server - INFO - Advertising UDP 'test service' on port 5000
```

### But why?
There are several UPnP protocols in the world already. Why another one? Weeell, I had some time over and wanted to play with multicast in [EOR](https://github.com/SuperHouse/esp-open-rtos) and Python. This thing sort of came along. But don't deploy it, lest you will create a DDOS amplifier. Will fix that someday...

And uHej? That is 'u' as in 'micro' and 'hej' as in Swedish for 'hi'.
