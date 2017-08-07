#!/usr/bin/python
#
# Title: parse.py
#
# Purpose: Takes text documents from doc folder and parses them for upload to the correct classes DB.
#
# Copyright (C) Andrew Malone 2016

# Imports for commonly used function

import glob
import re
import os
import getpass
import ConfigParser
import MySQLdb
import warnings
import json
from onvif import ONVIFCamera, ONVIFError
from module import config, function
from subprocess import *

######## variable init #######


##      # Global Variables #    ##

warnings.filterwarnings('error',category=MySQLdb.Warning)


# Regular Expression Groups #
class IsValid:
    # https://regex101.com/r/kKnaHy/1
    IP = "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"
    MAC = "^([0-9A-F]{2}:){5}([0-9A-Z]){2}$"

# SQL section #


# Text output color definitions
class color:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Helper Applications
class prog:
    arp2json = ['./arp2json']

## Function Delerations ##

    ## run a Commit ##
def sql(statement):
    try:
        num_rows = cursor.execute(statement)
    except Warning as w:
        print(color.WARNING+"\nWARNING: "+statement+"\n"+format(w)+color.END)
    except Exception as e:
        print(color.FAIL+"\nERROR: "+statement+"\n"+format(e)+color.END)
        exit(1)
    db.commit()

    ## Run a Fetch ##
def fetch(statement):
    try:
        num_rows = cursor.execute(statement)
    except Warning as w:
        print(color.WARNING+"\nWARNING: "+statement+"\n"+format(w)+color.END)
    except Exeception as e:
        print(color.FAIL+"\nERROR: "+statement+"\n"+format(e)+color.END)
    db.commit()
    return cursor.fetchone()


# Precompile all the RegEx
#desc = re.compile(DESC)

### Main Script ###

call('clear')
print("Welcome: " + getpass.getuser())
print("Zoneminder Onvif device installer. Copyright (C) 2016 Andrew Malone Collective Industries\n\n")
print(os.getcwd())
db = function.MySQL_init()

cursor = db.cursor()

data = fetch("SELECT VERSION()")
print("Database version: %s" % data)
print("Database configuration settings are correct\n\n")

# Grab ARP table
inet_dev = raw_input('Which interface should be scanned for ONVIF Cameras? (eth0) ')
if inet_dev == '':
    inet_dev = 'eth0'

arp = Popen(prog.arp2json+[inet_dev], stdout=PIPE, stderr=PIPE)
out, err = arp.communicate()

try:
    decoded = json.loads(out.decode("utf-8"))
except:
    print("There was a problem decoding the returned Json File")

# Loop through each entry and identify ONVIF Devices.

try:
    mycam = ONVIFCamera('192.168.20.22', 80, 'admin', 'admin', '/etc/onvif/wsdl/')
    # Get Hostname

    resp = mycam.devicemgmt.GetHostname()
    print('Camera`s hostname: ' + str(resp.Name))
    function.ViewCamera('admin','admin','192.168.20.22')
except ONVIFError as e:
    print("%sIP Address %s failed when trying to obtain ONVIF information with error: %s%s" % (color.FAIL,'123',e,color.END) )

print('Attempting connection to NTP Server......%s' % (config.SiteConfig.ntp))

print(function.ntpGet(config.SiteConfig.ntp))
