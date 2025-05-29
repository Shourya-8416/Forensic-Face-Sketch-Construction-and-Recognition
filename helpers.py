# helpers.py

import uuid
import socket

def get_mac():
    """
    Returns the MAC address of this machine as a string
    in the format xx:xx:xx:xx:xx:xx.
    """
    mac = uuid.getnode()
    # format 48-bit MAC in hex
    return ':'.join(
        f"{(mac >> ele) & 0xff:02x}"
        for ele in range(40, -1, -8)
    )

def get_ip_and_adapter():
    """
    Returns a tuple (ip_address, adapter_name).
    adapter_name is just the hostname here.
    """
    hostname   = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address, hostname

