#!/usr/bin/python

## Hopefully we can avoid disaster if we dont import this in a main program
try:
  config
except NameError:
  import config
  from config import SQLConfig

import MySQLdb
import subprocess
import os, shutil
from getpass import getpass
import cv2
import numpy as np

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

## MySQL init function added an error handler + a config data setting dump should be able to use this for all python database connections
def MySQL_init():
	output = subprocess.check_output(['ps', '-A'])
	if 'mysqld' in output:
    		print("MariaDB/MySQL is up and running! [ "+color.OKGREEN+"OK"+color.END+" ]")
	else:
		print("MariaDB/MySQL is "+color.FAIL+"NOT"+color.END+" running...fixing!")
		subprocess.call(['service','mysql','start'])

	while True:

    ## Set up the Connection using config.d/NAME.conf returns a standard DB Object
		try:
			db = MySQLdb.connect(host=SQLConfig.host,user=SQLConfig.user,passwd=SQLConfig.password,db=SQLConfig.db)
			# Values must be correct, if values were wrong a MySQLdb.Error would have been thrown
			# lets write out the new configuration values.
#			config.ConfigAddSection("DB")
			config.ConfigSetValue("DB","host",SQLConfig.host)
			config.ConfigSetValue("DB","user",SQLConfig.user)
			config.ConfigSetValue("DB","password",SQLConfig.password)
			config.ConfigSetValue("DB","database",SQLConfig.db)
#			config.ConfigSetValue("DB","port",config._IN_MYSQL_PORT_) # this setting looks to be unused at the moment however at some time in the future it should be configurable.
			config.ConfigWrite() # Write file with proper values now that weve updated everything.

			return db # Return the DB connection Object

		except MySQLdb.Error:
			print "There was a problem in connecting to the database."
			print "Config DUMP:"
			print "HOST: %s\nUSER: %s\nPASS: %s\nDATABASE: %s" %(SQLConfig.host,SQLConfig.user,SQLConfig.password,SQLConfig.db)
			print "Please Enter the correct login credentials below.\nRequired items are marked in "+color.FAIL+"RED"+color.END+" Any default values will be marked with []\n Once correct values are configured the installer will update the configuration file: "+config.ConfigFile

			## > fix values here < ##

			SQLConfig.host = None
			SQLConfig.user = None
			SQLConfig.password = None
			SQLConfig.db = None

			# After restting variables to None we need to prompt the user for each one and try again.

			while ((SQLConfig.host is None) or (SQLConfig.host=='')):
				SQLConfig.host = raw_input(color.FAIL+"Mysql Server Host (example.com) []: "+color.END)
			while ((SQLConfig.db is None) or (SQLConfig.db == '')):
				SQLConfig.db = raw_input(color.FAIL+"Name of Database []: "+color.END)
			while ((SQLConfig.user is None) or (SQLConfig.user == '')):
				SQLConfig.user = raw_input(color.FAIL+"Username []: "+color.END)
			while ((SQLConfig.password is None) or (SQLConfig.password == '')):
				SQLConfig.password = getpass(color.FAIL+"Password []: "+color.END)
			pass
		except MySQLdb.Warning: # Silently ignore Warnings
			break


def ViewCamera(User, Pass, IP):
	cap = cv2.VideoCapture('rtsp://%s:%s@%s:554/cam/realmonitor?channel=1&subtype=1&unicast=true&proto=Onvif' % (User,Pass,IP) )
	ret, frame = cap.read()
	cv2.imshow('Snapshot', frame)
	cv2.waitKey(0)
	cv2.destroyAllWindows()

# Get time from NTP Server defualts to 'time.nist.gov' if nothing is provided.
def ntpGet(addr='time.nist.gov'):
    # http://code.activestate.com/recipes/117211-simple-very-sntp-client/
    import socket
    import struct
    import sys
    import time

    TIME1970 = 2208988800L      # Thanks to F.Lundh
    client = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
    data = '\x1b' + 47 * '\0'
    client.sendto( data, (addr, 123))
    try:
        client.settimeout(20)
        data, address = client.recvfrom( 1024 )
    except socket.error:
         errno,errstr = sys.exc_info()[:2]
         if errno == socket.timeout:
             print('%sFailed to get Time from %s reason: Socket timed out%s' % (color.FAIL,addr,color.END))
         else:
             print('%sFailed to get Time from %s error: %s%s' % (color.FAIL,addr, errstr,color.END))

    if data:
        t = struct.unpack( '!12I', data )[10]
        t -= TIME1970
        return time.ctime(t),t

def formatTime(timestamp,format="%a %b %d %X %Z %Y"):
    import time
    return time.strftime(format, time.gmtime(timestamp/1000.))
