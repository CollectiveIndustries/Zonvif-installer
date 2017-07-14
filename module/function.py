#!/usr/bin/python

## Hopefully we can avoid disaster if we dont import this in a main program
try:
  config
except NameError:
  import config

import MySQLdb
import subprocess
import os, shutil
from getpass import getpass

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
			db = MySQLdb.connect(host=config._IN_MYSQL_HOST_,user=config._IN_MYSQL_USR_,passwd=config._IN_MYSQL_PASS_,db=config._IN_MYSQL_DB_)
			# Values must be correct, if values were wrong a MySQLdb.Error would have been thrown
			# lets write out the new configuration values.
#			config.ConfigAddSection("DB")
			config.ConfigSetValue("DB","host",config._IN_MYSQL_HOST_)
			config.ConfigSetValue("DB","user",config._IN_MYSQL_USR_)
			config.ConfigSetValue("DB","password",config._IN_MYSQL_PASS_)
			config.ConfigSetValue("DB","database",config._IN_MYSQL_DB_)
#			config.ConfigSetValue("DB","port",config._IN_MYSQL_PORT_) # this setting looks to be unused at the moment however at some time in the future it should be configurable.
			config.ConfigWrite() # Write file with proper values now that weve updated everything.

			return db # Return the DB connection Object

		except MySQLdb.Error:
			print "There was a problem in connecting to the database."
			print "Config DUMP:"
			print "HOST: %s\nUSER: %s\nPASS: %s\nDATABASE: %s" %(config._IN_MYSQL_HOST_,config._IN_MYSQL_USR_,config._IN_MYSQL_PASS_,config._IN_MYSQL_DB_)
			print "Please Enter the correct login credentials below.\nRequired items are marked in "+color.FAIL+"RED"+color.END+" Any default values will be marked with []\n Once correct values are configured the installer will update the configuration file: "+config.ConfigFile

			## > fix values here < ##

			config._IN_MYSQL_HOST_ = None
			config._IN_MYSQL_USR_ = None
			config._IN_MYSQL_PASS_ = None
			config._IN_MYSQL_DB_ = None

			# After restting variables to None we need to prompt the user for each one and try again.

			while ((config._IN_MYSQL_HOST_ is None) or (config._IN_MYSQL_HOST_=='')):
				config._IN_MYSQL_HOST_ = raw_input(color.FAIL+"Mysql Server Host (example.com) []: "+color.END)
			while ((config._IN_MYSQL_DB_ is None) or (config._IN_MYSQL_DB_ == '')):
				config._IN_MYSQL_DB_ = raw_input(color.FAIL+"Name of Database []: "+color.END)
			while ((config._IN_MYSQL_USR_ is None) or (config._IN_MYSQL_USR_ == '')):
				config._IN_MYSQL_USR_ = raw_input(color.FAIL+"Username []: "+color.END)
			while ((config._IN_MYSQL_PASS_ is None) or (config._IN_MYSQL_PASS_ == '')):
				config._IN_MYSQL_PASS_ = getpass(color.FAIL+"Password []: "+color.END)
			pass
		except MySQLdb.Warning: # Silently ignore Warnings
			break
