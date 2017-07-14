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
import subprocess
import getpass
import ConfigParser
from module import config, function
import MySQLdb
import warnings

######## variable init #######


##	# Global Variables #	##

warnings.filterwarnings('error',category=MySQLdb.Warning)


# Regular Expression Groups #


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

subprocess.call('clear')
print "Welcome: " + getpass.getuser()
print "Zoneminder Onvif device installer. Copyright (C) 2016 Andrew Malone Collective Industries\n\n"
print os.getcwd()
db = function.MySQL_init()

cursor = db.cursor()

data = fetch("SELECT VERSION()")
print("Database version: %s" % data)
print("Database configuration settings are correct\n\n")
