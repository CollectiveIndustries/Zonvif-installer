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
from pprint import pprint

######## variable init #######


##      # Global Variables #    ##

warnings.filterwarnings('error',category=MySQLdb.Warning)
_NTP_SERVER_ = '192.168.20.2'

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
    arp2json = ['./bash/arp2json']
    getInf = ['./bash/lsiface']


# This class provides the functionality we want. You only need to look at
# this if you want to know how this works. It only needs to be defined
# once, no need to muck around with its internals.
# Located at http://code.activestate.com/recipes/410692/
class switch(object):
    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        """Return the match method once, then stop"""
        yield self.match
        raise StopIteration

    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True
        elif self.value in args:
            self.fall = True
            return True
        else:
            return False


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

# ONVIF Functions by name (https://www.onvif.org/onvif/ver20/util/operationIndex.html)

def GetHostname(ip,user='admin',password='admin'):
    try:
        cam = ONVIFCamera(ip, 80, user, password, '/etc/onvif/wsdl/')
        return cam.devicemgmt.GetHostname().Name
    except ONVIFError as e:
        return None

def GetNetworkInterfaces(ip,user='admin',password='admin'):
    try:
        cam = ONVIFCamera(ip, 80, user, password, '/etc/onvif/wsdl')
        return cam.devicemgmt.GetNetworkInterfaces()
    except ONVIFError as e:
        return None

def GetDeviceInformation(ip,user='admin',password='admin'):
    try:
        cam = ONVIFCamera(ip, 80, user, password, '/etc/onvif/wsdl/')
        return cam.devicemgmt.GetDeviceInformation()
    except ONVIFError as e:
#        print("%s%s%s" % (color.FAIL,e,color.END))
        return None

def GetSystemDateAndTime(ip,user='admin',password='admin'):
    try:
        cam = ONVIFCamera(ip, 80, user, password, '/etc/onvif/wsdl')
        return cam.devicemgmt.GetSystemDateAndTime()
    except ONVIFError as e:
        return None

def ResetNetworkInterfaces(ip,user='admin',password='admin'):
    try:
        cam = ONVIFCamera(ip,80,user,password,'/etc/onvif/wsdl')
        params = cam.devicemgmt.create_type('SetNetworkInterfaces')
        params.IPv4.Config.DHCP = "True"
        cam.devicemgmt.SetNetworkInterfaces(params)
        return True
    except Exception as e:
        print(e)
        return False

def GetInf():
    ifaces = Popen(prog.getInf, stdout=PIPE, stderr=PIPE)
    out, error = ifaces.communicate()
    print("Interfaces found for scanning:")

    try:
        decoded = json.loads(out.decode("utf-8"))
#        for x in decoded:
#            print("%s%s%s" % (color.WARNING,x['iface'],color.END))
    except Exception as e:
        print("There was a problem scanning for interfaces.")
        print(e)
    finally:
        return decoded


## GetONVIFSubnetInfo()
# grab a list of network devices with arp returning in JSON format for parsing.
# Loop through each Device and a) devices is not onvif set structure to None. b) Device returns hostname so lets grab all the other information and add it to the data structure.
def GetONVIFSubnetInfo(inet_dev='eth0',user='admin',password='admin'):
    arp = Popen(prog.arp2json+[inet_dev], stdout=PIPE, stderr=PIPE)
    out, err = arp.communicate()
    print(err)
# Display Onvif Devices and other information
    try:
        decoded = json.loads(out.decode("utf-8"))
        print("%sIP - MAC - Vendor - ONVIF Hostname - Configured Using - Time Zone - Local Time - Configured using DHCP?%s" % (color.HEADER,color.END))
        for x in decoded:
            x['onvif'] = GetHostname(x['ip'],user,password)
            if x['onvif'] is not None: # print out only ONVIF devices
                # clock: NTP, dhcp: False, timezone: GMT-07:00, NewIP: 0.0.0.0
                NetConf = GetNetworkInterfaces(x['ip'],user,password)
                DateTime = GetSystemDateAndTime(x['ip'],user,password)
                x['timezone'] = DateTime.TimeZone.TZ
                x['clock'] = DateTime.DateTimeType

                ## Grab Local time from the Camera
                Hour = DateTime.LocalDateTime.Time.Hour
                Minute = DateTime.LocalDateTime.Time.Minute
                Second = DateTime.LocalDateTime.Time.Second
                Year = DateTime.LocalDateTime.Date.Year
                Month = DateTime.LocalDateTime.Date.Month
                Day = DateTime.LocalDateTime.Date.Day

                ## Process the NetConf here to get values
                for y in NetConf:
                    x['dhcp'] = y.IPv4.Config.DHCP

                print("%s%s - %s - %s - %s - %s - %s - %s/%s/%s %s:%s:%s - %s%s" %(color.OKGREEN, x['ip'], x['mac'], x['vendor'], x['onvif'], x['clock'], x['timezone'], Month, Day, Year,  Hour, Minute,Second,x['dhcp'],color.END))

    except Exception as e:
        print("There was a problem scanning the network.")
        print(e)
        exit(1)

    finally:
        return decoded

#def SetNtp(ip,user='admin',password='admin'):
#    try:
#        cam = ONVIFCamera(ip, 80, user, password, '/etc/onvif/wsdl')

def ScanNetwork():
    # Get local interfaces list from the system directory.
    # ifaces[0]['iface'] is the first listed interface name and is automatically set as the default option
    while True:
        InterfaceList = GetInf()
        for index, value in enumerate(InterfaceList):
            print("%s%s) %s%s" % (color.WARNING,index,value['iface'],color.END))
        print("\n%s%s%s" % (color.FAIL,'R) Reset [Resets all DHCP Settings on every compatible device on the network]',color.END))

        prompt = raw_input('Which interface should be scanned for ONVIF Cameras? (%s%s%s) ' % (color.HEADER,InterfaceList[0]['iface'],color.END))
        user = raw_input('Username: (%s%s%s) ' % (color.HEADER,'admin',color.END))
        password = raw_input('Password: (%s%s%s) ' % (color.HEADER,'admin',color.END))
        if user == '':
            user = 'admin'
        if password == '':
            password = 'admin'

        for index, value in enumerate(InterfaceList):
            for case in switch(prompt):
                if case(''): pass # Default option
                if case('0'): pass # First listed option
                if case(InterfaceList[0]['iface']): # user gave the name of the interface of option 0
                    SubnetInfo = GetONVIFSubnetInfo(value['iface'],user, password)
                    return
                if case(str(index)): pass # Check all interfaces in the list
                if case(value['iface']): # aswell as there name
                    print("Scanning network using interface: %s%s) %s%s" % (color.OKBLUE,index,value['iface'],color.END))
                    SubnetInfo = GetONVIFSubnetInfo(value['iface'],user, password)
                    return
                if case('reset'): pass
                if case('r'): pass
                if case('R'):
                    SubnetInfo = GetONVIFSubnetInfo(value['iface'],user, password) # print it out
                    SubnetReset(value['iface'], user, password) # reset
                    SubnetInfo = GetONVIFSubnetInfo(value['iface'],user, password) # print it out again
                    return
        print("%sERROR: interface not found.%s\n%sPlease choose a valid interface from the shown options.%s" % (color.FAIL,color.END,color.WARNING,color.END))

# Precompile all the RegEx
#desc = re.compile(DESC)

### Main Script ###

call('clear')
print("Welcome: " + getpass.getuser())
print("Zoneminder Onvif device installer. Copyright (C) 2017 Andrew Malone Collective Industries\n\n")
# Grab first time stamp from time.nist.gov so we can avoide anything too dangerous before we configure options
print("Local Server Time (from %s): %s%s%s" % (_NTP_SERVER_, color.OKBLUE,function.ntpGet(_NTP_SERVER_)[0], color.END))

#print(os.getcwd())
db = function.MySQL_init()

cursor = db.cursor()

data = fetch("SELECT VERSION()")
print("Database version: %s" % data)
print("Database configuration settings are correct\n\n")
print("All option defaults will be marked as (%sdefault%s)" % (color.HEADER,color.END))

ScanNetwork()

#pprint(SubnetInfo)



# Loop through the list and pull an image from the device.
#for x in decoded:
#    if x['onvif'] is not None:
#        try:
#            function.ViewCamera('admin','admin',x['ip'])
#        except ONVIFError as e:
#            print("%sIP Address %s failed when trying to obtain ONVIF information with error: %s%s" % (color.FAIL,x['ip'],e,color.END) )
