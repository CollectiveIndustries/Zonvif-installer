#!/bin/bash

# ARP the network grab any IP address that matches the first 4 Octets E0:50:8B:59
arp-scan --localnet --interface=eth0 | grep e0:50:8b:59 | awk '{print $1}'

