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

class CheckService:
    def mysql(self, retry=3): # Set a default retry of 3
        for i in range(retry-1):
            output = subprocess.check_output(['ps', '-A'])
            if 'mysqld' in output:
                print("MariaDB/MySQL is up and running! [ "+color.OKGREEN+"OK"+color.END+" ]")
                return True
            else:
                print("MariaDB/MySQL is "+color.FAIL+"NOT"+color.END+" running...fixing!")
                subprocess.call(['service','mysql','start'])
        return None

    def zoneminder(self, retry=3):
        for i in range(retry-1):
            output = subprocess.check_output(['ps', '-A'])
            if 'zmc' in output:
                print("Zoneminder surveillance system is up and running! [ "+color.OKGREEN+"OK"+color.END+" ]")
                return True
            else:
                print("Zoneminder surveillance system is "+color.FAIL+"NOT"+color.END+" running...fixing!")
                subprocess.call(['service','zoneminder','start'])
        return None

    def apache(self, retry=3):
        for i in range(retry-1):
            output = subprocess.check_output(['ps', '-A'])
            if 'apache2' in output:
                print("Apache2 is up and running! [ "+color.OKGREEN+"OK"+color.END+" ]")
                return True
            else:
                print("Apache2 is "+color.FAIL+"NOT"+color.END+" running...fixing!")
                subprocess.call(['service','apache2','start'])
        return None

## https://stackoverflow.com/questions/207981/how-to-enable-mysql-client-auto-re-connect-with-mysqldb
## MySQL Wrapper Class for dealing with MySQL Servers ##

class MySQL:
    conn = None

    ## MySQL init function added an error handler + a config data setting dump should be able to use this for all python database connections
    def connect(self):
        services = CheckService()
        if services.mysql(3) is None:
            print("MySQL service failed to restart correctly. Check system logs for further details.")
            exit(1)

        while True:
        ## Set up the Connection using config.d/NAME.conf returns a standard DB Object
            try:
                print("Attempting to load configuration file for login information.")
                self.conn = MySQLdb.connect(host=SQLConfig.host,user=SQLConfig.user,passwd=SQLConfig.password,db=SQLConfig.db)

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
                pass

            finally:
                # Values must be correct, if values were wrong a MySQLdb.Error would have been thrown
                # lets write out the new configuration values.
#                       config.ConfigAddSection("DB")
                config.ConfigSetValue("DB","host",SQLConfig.host)
                config.ConfigSetValue("DB","user",SQLConfig.user)
                config.ConfigSetValue("DB","password",SQLConfig.password)
                config.ConfigSetValue("DB","database",SQLConfig.db)
#                       config.ConfigSetValue("DB","port",config._IN_MYSQL_PORT_) # this setting looks to be unused at the moment however at some time in the future it should be configurable.
                config.ConfigWrite() # Write file with proper values now that weve updated everything.
                break

## push information to the server
    def communicate(self, sql, params=[]):
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
        except (AttributeError, MySQLdb.OperationalError):
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
        except Warning as w:
            print(color.WARNING+"\nWARNING: "+statement+"\n"+format(w)+color.END)
        except Exeception as e:
            print(color.FAIL+"\nERROR: "+statement+"\n"+format(e)+color.END)
        finally:
            self.conn.commit()
            return cursor

## Grab oneline from the server
    def fetchOne(self, sql, params=[]):
            cursor = self.communicate(sql, params)
            return cursor.fetchone()

### END CLASS

def ViewCamera(User, Pass, ip):
    cap = cv2.VideoCapture('rtsp://{USER}:{PASSWORD}@{IP}:{PORT}/cam/realmonitor?channel=1&subtype=1&unicast=true&proto=Onvif'.format(USER=User, PASSWORD=Pass, IP=ip, PORT='554') )
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
