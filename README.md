**uHej**
==========

I needed a way to query the network for firmware upgradeable ESP8266 nodes and this is the outcome. It is basically a service advertisement protocol in a few hundred lines of C code. A python implementation is also available.

### Usage

Add this git as well as the [python counterpart](https://github.com/kanflo/uhej-python) as submodules to your project. For ESP Open RTOS projects, add the following lines to your makefile:

```
PROGRAM_INC_DIR = . uhej
PROGRAM_SRC_DIR = . uhej
```

Copy "lwipopts.h" to your source directory, include "uhej.h" and call the following to have your ESP8266 node advertise its services:

```
    if (!(uhej_server_init() &&
   	    uhej_announce_udp("tftp", 69) &&
	    uhej_announce_udp("test service", 5000)))
    {
       printf("uHej registration failed\n");
    }

```

Next, run ```uhdiscovery.py```:

```
% ./uhdiscovery.py
    172.16.3.154:5000   UDP      test service
    172.16.3.154:69     UDP      tftp
    172.16.3.203:69     UDP      tftp
3 services found
```

Of course, you can have anything advertise a service. A python script:

```
% ./server.py
2017-02-20 23:46:02,350 - root - INFO - Server starting
2017-02-20 23:46:07,604 - uhej_server - INFO - uHej server thread
2017-02-20 23:46:07,605 - uhej_server - INFO - uHej worker thread
2017-02-20 23:46:07,605 - root - INFO - Service on 172.16.3.154:5000
2017-02-20 23:46:07,605 - uhej_server - INFO - Advertising UDP 'test service' on port 5000
```

Check [the example](https://github.com/kanflo/uhej-example) for more details.

If you get ```Error, netif is null``` and ```uHej registration failed``` chances are you called ```uhej_server_init``` "too soon". It seems ```sdk_system_get_netif``` returns NULL if called to soon, eg. from ```user_init```. Add the call to the first task you create, see the uHej example.

### But why?
There are several UPnP protocols in the world already. Why another one? Weeell, I had some time over and wanted to play with multicast in [EOR](https://github.com/SuperHouse/esp-open-rtos) and Python. This thing sort of came along. But don't deploy it, lest you will create a DDOS amplifier. Will fix that someday...

And uHej? That is 'u' as in 'micro' and 'hej' as in Swedish for 'hi'.
