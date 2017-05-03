#! /usr/bin/env python
import pydbus

if __name__ == "__main__":
    bus = pydbus.SystemBus()
    help(bus.get("org.coiot", "/org/coiot/0"))
