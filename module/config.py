#!/usr/bin/python

##################################################################################################
#
# Copyright (C) Andrew Malone, Collective Industries 2016
#
# AUTHOR: Andrew Malone
#
# TITLE: config
#
# PURPOSE: Configuration file managment
#
#
##################################################################################################

import ConfigParser
import os

ConfigFile = "config.d/zm.conf"

conf = ConfigParser.ConfigParser()
conf.read(os.path.abspath(ConfigFile))
conf.sections()

## Config Parse Helper ##

def ConfigSectionMap(section):
    dict1 = {}
    options = conf.options(section)
    for option in options:
        try:
            dict1[option] = conf.get(section, option)
            if dict1[option] == -1:
                print("Skipping: %s %s" % (section,option))
        except:
            print("Exception on %s %s!" % (section,option))
            dict1[option] = None
    return dict1

## Config section writter ##
def ConfigAddSection(section):
	conf.add_section(section)

def ConfigSetValue(section,key,value):
	conf.set(section,key,value)

def ConfigWrite():
	cfgfile = open(ConfigFile, "wb")
	conf.write(cfgfile)
	cfgfile.close()

# Set up config values

# Zoneminder Settings
class SQLConfig:
		host = ConfigSectionMap("DB")['host']
		user = ConfigSectionMap("DB")['user']
		password = ConfigSectionMap("DB")['password']
		db = ConfigSectionMap("DB")['database']
		port = ConfigSectionMap("DB")['port']

# Camera Settings
class CameraConfig:
	user = ConfigSectionMap("CAM")['user']
	password = ConfigSectionMap("CAM")['pass']

# Site settings
class SiteConfig:
	ntp = ConfigSectionMap("NETWORK")['ntp']
	dns = ConfigSectionMap("NETWORK")['dns']
        dhcp = ConfigSectionMap("NETWORK")['dhcp']
	gateway = ConfigSectionMap("NETWORK")['gateway']
	iface = ConfigSectionMap("NETWORK")['iface']


# DNS Server settings for uploading HOST file
class DNSConfig:
	addy = ConfigSectionMap("DNS")['address']
	hostFile = ConfigSectionMap("DNS")['host_file_path']
	serverProto = ConfigSectionMap("DNS")['protocol']
	user = ConfigSectionMap("DNS")['user']

