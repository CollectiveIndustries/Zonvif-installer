#!/usr/bin/python
#
# Title: probe.py
#
# Purpose: Probes network using ARP and grabs ONVIF cameras and installes them directly into Zoneminder MySQL DB.
#
# Copyright (C) Andrew Malone 2017

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
CWD = os.getcwd() # get current working directory path
COPYRIGHT_DATE = '2017'

##      # Global Variables #    ##

warnings.filterwarnings('error',category=MySQLdb.Warning)
_NTP_SERVER_ = 'time.nist.gov'


class SQLFields(object):

    ## SQL dictionary for the Zoneminder server ##
    Monitors = {"Name": "General",
                            "ServerId": 0,
                            "Device": "/dev/video0",
                            "Format": 255,
                            "V4LMultiBuffer": 0,
                            "V4LCapturesPerFrame": 1,
                            "Type": "Ffmpeg",
                            "Port": "80",
                            "Width": 1920,
                            "Height": 1080, # May need to be set up dynamically using camera specs
                            "Colours": 3,
                            "LabelSize": 1,
                            "ImageBufferCount": 50,
                            "PreEventCount": 25,
                            "PostEventCount": 25,
                            "AlarmFrameCount": 1,
                            "AnalysisFPS": 0.00,
                            "MaxFPS": 0.00,
                            "AlarmMaxFPS": 0.00,
                            "FPSReportInterval": 1000,
                            "SignalCheckColour": "#0000c0" }
# Dynamically assigned when added "Sequence": index number for camera in the list.

    Zones = {
#                               "MonitorId": 2, # Monitor ID will need to be pulled from the last commit then added here.
                            "Name": "All",
                            "Units": "Percent",
                            "NumCoords": 4,
                            "Coords": "0,0 1919,0 1919,1079 0,1079",
                            "Area": 2073600,
                            "AlarmRGB": 16711680,
                            "CheckMethod": "Blobs",
                            "MinPixelThreshold": 25,
                            "MinAlarmPixels": 62208,
                            "MaxAlarmPixels": 1555200,
                            "FilterX": 3,
                            "FilterY": 3,
                            "MinFilterPixels": 62208,
                            "MaxFilterPixels": 1555200,
                            "MinBlobPixels": 41472,
                            "MinBlobs": 1,
                            "OverloadFrames": 0,
                            "ExtendAlarmFrames": 0}


    ## Define the Camera SQL Object here
    def __init__(self, ip, user='admin', password='admin'): # Define default options for the camera object
        # https://regex101.com/r/kKnaHy/1
        ValidIP = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")
        ValidMac = re.compile("^([0-9A-F]{2}:){5}([0-9A-Z]){2}$")

        path = "rtsp://{IP}:{PORT}/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif"
        host = "http://{IP}/onvif/device_service"

        # Validate the IP/MAC for the camera so we can verify any potential issues.
        if(re.match(ValidIP, ip) is not None):
            ## rtsp://admin:admin@192.168.20.148:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif ##
            self.Monitors['Host'] = host.format(IP=ip) # IP address for the camera
            self.Monitors['Path'] = path.format(IP=ip, PORT='554' ) # "rtsp://"+user+":"+password+"@"+ip+":554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif"
        else:
            raise RuntimeError("%sIP Address %s%s%s is not valid.%s" % (color.FAIL, color.UNDERLINE, ip, color.FAIL, color.END))
        self.user = user # Username for the camera
        self.password = password # Password for the camera

    def InstallCamera(self):                ## Insert statements ##
        placeholderM = ', '.join(['%s'] * len(self.Monitors))
        insert = "INSERT INTO `{table}` ({columns}) VALUES ({values})"
        select = "SELECT `{id}` FROM `{table}` WHERE host='{host}'"
        db.communicate(insert.format(table='Monitors', columns=", ".join(self.Monitors.keys()), values=placeholderM ), self.Monitors.values())
        self.Zones['MonitorId'] = db.fetchOne(select.format(id='Id', table='Monitors', host=self.Monitors['Host'] ))[0]
        placeholderZ = ', '.join(['%s'] * len(self.Zones))

        for k, v in self.Monitors.iteritems() :
            print(k, v)

        for k, v in self.Zones.iteritems():
            print(k, v)

        db.communicate(insert.format(table='Zones', columns=", ".join(self.Zones.keys()), values=placeholderZ ), self.Zones.values())
        return True
#               self.Monitor = "INSERT INTO `Monitors` 45 VALUES "
#               self.Zone = "INSERT INTO `Zones` 45 VALUES "

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
    arp2json = [CWD+'/bash/arp2json']
    getInf = [CWD+'/bash/lsiface']

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

# Wrapper functions
def CameraSettings(x,User='admin',Pass='admin'):
    # fork the subprocess here
    r, w = os.pipe() # these are file descriptors, not file objects

    pid = os.fork()
    if pid:
        # we are the parent
        os.close(w) # use os.close() to close a file descriptor
        try:
            print("%s%s - %s - %s - %s - %s - %s - %s%s" %(color.OKGREEN, x['ip'], x['mac'], x['vendor'], x['onvif'], x['clock'], x['timezone'], x['dhcp'],color.END))
        except:
            print("Error forking.")

        os.waitpid(pid, 0) # make sure the child process gets cleaned up
    else:
        # we are the child
        function.ViewCamera(User,Pass,x['ip'])
        os.close(r)
        exit(0)

# Resets the camera to factory defaults everything except the Hostname will be reset to there factory shipped values.
def ResetCamera(ip,user='admin',password='admin'):
    try:
        cam = ONVIFCamera(ip,80,user,password,'/etc/onvif/wsdl')
        params = cam.devicemgmt.create_type('SetSystemFactoryDefault')
        params.FactoryDefault = "Hard"
        cam.devicemgmt.SetSystemFactoryDefault(params)
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
    arp = Popen(prog.arp2json+[inet_dev, CWD], stdout=PIPE, stderr=PIPE)
    out, err = arp.communicate()
    print('%s%s%s' % (color.WARNING,err,color.END))
# Display Onvif Devices and other information
    try:
        decoded = json.loads(out.decode("utf-8"))

    except Exception as e:
        print("%sThere was a problem decoding the returned JSON output from arp2json.%s" % (color.FAIL,color.END))
        print(e)
        exit(1)

    finally:
#        print("%sIP - MAC - Vendor - ONVIF Hostname - Configured Using - Time Zone - Local Time - Configured using DHCP?%s" % (color.HEADER,color.END))
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

#                print("%s%s - %s - %s - %s - %s - %s - %s/%s/%s %s:%s:%s - %s%s" %(color.OKGREEN, x['ip'], x['mac'], x['vendor'], x['onvif'], x['clock'], x['timezone'], Month, Day, Year,  Hour, Minute,Second,x['dhcp'],color.END))
#                ResetCamera(x['ip'],user,password)
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
        user = raw_input('Username: (%s%s%s) ' % (color.HEADER,config.CameraConfig.user,color.END))
        password = raw_input('Password: (%s%s%s) ' % (color.HEADER,config.CameraConfig.password,color.END))
        if user == '':
            user = config.CameraConfig.user
        if password == '':
            password = config.CameraConfig.password

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
                    print("%sIP - MAC - Vendor - ONVIF Hostname - Configured Using - Time Zone - Configured using DHCP?%s" % (color.HEADER,color.END))

                    SubnetInfo = GetONVIFSubnetInfo(value['iface'],user, password)
                    for x in SubnetInfo:
                        if x['onvif'] is not None:
                            # Loop through the list and pull an image from the device.
                            try:
                                CameraSettings(x,user,password)
                                SQLFields(x['ip'],user,password).InstallCamera()
                            except ONVIFError as e:
                                print("%sIP Address %s failed when trying to obtain ONVIF information with error: %s%s" % (color.FAIL,x['ip'],e,color.END) )

                    return
                if case('reset'): pass
                if case('r'): pass
                if case('R'):
                    print("%sFeature Not implimented yet%s" % (color.FAIL,color.END))
                    continue
        print("%sERROR: interface not found.%s\n%sPlease choose a valid interface from the shown options.%s" % (color.FAIL,color.END,color.WARNING,color.END))

# Precompile all the RegEx
#desc = re.compile(DESC)

### Main Script ###

call('clear')
print("Welcome: %s%s%s" %(color.OKGREEN,getpass.getuser(),color.END))
print("Current Working Directory: %s%s%s" % (color.HEADER,CWD,color.END))
print("Zoneminder Onvif device installer. Copyright (C) %s Andrew Malone Collective Industries\n\n" % (COPYRIGHT_DATE))
# Grab first time stamp from time.nist.gov so we can avoide anything too dangerous before we configure options
print("Local Server Time (from %s): %s%s%s" % (_NTP_SERVER_, color.OKBLUE, function.ntpGet(_NTP_SERVER_)[0], color.END))

#print(os.getcwd())
db = function.MySQL()
db.connect()
data = db.fetchOne("SELECT VERSION()")
print("Database version: %s" % data)
print("Database configuration settings are correct\n\n")
print("All option defaults will be marked as (%sdefault%s)" % (color.HEADER,color.END))

ScanNetwork()


#print(SQLFields('192.168.20.212','admin','admin').InstallCamera())

#pprint(SubnetInfo)
