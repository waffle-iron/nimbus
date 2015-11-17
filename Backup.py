#!/usr/bin/python3.4
'''
***************************************************************************
Script:                 Universal Backup Script
Authors/Maintainers:    Rich Nason (rnason@getnucleus.io)
Description:            This script will perform a pluthra of various backups.
***************************************************************************
'''
# Define all modules that this script will utilize
import argparse  # Get, and parse incoming arguments from the execution of the script
import time  # Used to get the current date to apend to logs in pretty format
import datetime  # Used to do file date calculations
import os  # Used to grab the config files that will be parsed.
import json  # This is loaded to parse the server_settings.ini file

'''
***************************************************************************
Define Global Functions Used for all Backup Job types.
***************************************************************************
'''


def write_log(string):
    try:
        log = open(LOGFILE, 'a+')
        log.write(string)
        log.close()
    except IOError:
        print('ERROR: ' + LOGFILE + ' does not exist!')


'''
***************************************************************************
Get Passed Arguments and Build the Help feature.
***************************************************************************
'''
# Gather Input Arugments:
BACKUP_JOB_DESC = """
The backup job type that you want to run.
Available Options are:
gitlab, jenkins, mysql, postgres'
"""
CONFIG_FILE_DESC = """
The full path location of the config file that holds the options
for the backup job that you would like to run.
(/root/backup/mygitserver.ini)
"""

# Parse input arguments #
PARSE = argparse.ArgumentParser(description='Universal Backup Script.')
PARSE.add_argument('-b', '--backup', help=BACKUP_JOB_DESC, required=True)
PARSE.add_argument('-c', '--config', help=CONFIG_FILE_DESC, required=True)
ARGS = PARSE.parse_args()

# Show Argument Values #
print('\n')
print("Backup Job: %s" % ARGS.backup)
print("Config File: %s" % ARGS.config)
print('\n')

# Make the backup argument upper case so that we can evaluate what job we need to run.
BACKUP_JOB = ARGS.backup.upper()
CONFIG_FILE = ARGS.config

if BACKUP_JOB == 'GITLAB':
    APP = 'Gitlab'
else:
    raise SystemExit(" You have identified an Undefined Backup Job.. Please try again")

'''
***************************************************************************
Set Global Variables and Parese the config file
***************************************************************************
'''

# Define Global Variables
# FILEDATE = time.strftime("%Y-%m-%d %H:%M:%S")
USER = os.getlogin()
FILEDATE = datetime.datetime.today()
DISPLAYDATE = time.strftime("%a %B %d, %Y")
MAIL_SUBJECT = APP + ' Backup Report - ' + DISPLAYDATE
LOGFILE = '/tmp/' + APP + '_backup.log'

if os.path.isfile(CONFIG_FILE):
    print('===================================')
    print('Backup Settings: File Succesfully Loaded')
    print(CONFIG_FILE + ' succesfully loaded!')
    print('-----------------------------------')

    with open(CONFIG_FILE, encoding='utf-8') as config_file:
        BACKUP_CONFIG = json.loads(config_file.read())

        # Load configured directories.
        if 'backup_directories' in BACKUP_CONFIG:
            DIRECTORY_LIST = BACKUP_CONFIG['backup_directories']
            print('Backup Directories:')
            for directory in DIRECTORY_LIST:
                print('\t' + directory.get('directory') + ': ')
                print('\t\t' + 'path: ' + directory.get('path') + APP)
                print('\t\t' + 'retention(days): ' + directory.get('retention_days'))
            print('\n')

        # Load mail recipients
        if 'mail_recipients' in BACKUP_CONFIG:
            MAIL_RECIPIENTS = BACKUP_CONFIG['mail_recipients']
            print("Mail Recipients: " + MAIL_RECIPIENTS)

    print('===================================')
    print('\n')


'''
***************************************************************************
Make sure all of the listed directories in the config file exist, or create them
***************************************************************************
'''
# Make sure all of the directory locations actually exist.. If they dont' then crate them
for directory in DIRECTORY_LIST:
    dir_name = directory.get('directory')
    path = directory.get('path') + APP.lower()

    # Check to see if the path exists:
    if not os.path.isdir(path):
        try:
            os.makedirs(path)
            print(path + " has been created.")
        except FileNotFoundError:
            print(path + " could not be created.")

'''
***************************************************************************
Instansiate the Logfile
***************************************************************************
'''

# Start the log file, clearing the contents in the event that the file already exists
open(LOGFILE, 'w').close()

# Print the subject Line
write_log('Subject: ' + MAIL_SUBJECT + '\n\n\n')

'''
***************************************************************************
Perform a clean up on the directories according to your the parsed retention policy
***************************************************************************
'''
# Write Log header
write_log("Cleaning files accourding to set retention:\n")
write_log("============================================================\n")

# Keep a counter and print the number of files removed vs number of files deleted
DELETED_FILES = 0
KEPT_FILES = 0

# Cycle through each directory in the list
for directory in DIRECTORY_LIST:
    dir_name = directory.get('directory')
    path = directory.get('path') + APP.lower()
    retention = directory.get('retention_days')

    # For each file in each directory, run a time date check and remove any files older then the retention period.
    for file in os.listdir(path):
        file_create_date = datetime.datetime.fromtimestamp(os.path.getmtime(path + "/" + file))
        file_age = FILEDATE - file_create_date

        # If the file is greater then the set retention, then remove the file.
        if file_age.days > int(retention):
            # print(path + "/" + file + " - " + str(file_age.days) + " days old - File removed!")
            write_log(path + "/" + file + " removed (" + str(file_age.days) + " days old)\n")
            try:
                os.remove(path + "/" + file)
                DELETED_FILES += 1
            except OSError as err:
                print(file + "could not be removed. - ")
                print("OS error: {0}".format(err))
        else:
            KEPT_FILES += 1
            # print(path + "/" + file + " - " + str(file_age.days) + " days old - File saved!")
write_log("============================================================\n\n")
write_log(str(DELETED_FILES) + " files exceeded the retention period and have been removed.\n")
write_log(str(KEPT_FILES) + " files are within the retention period and have been saved.\n\n\n")

'''
***************************************************************************
Run the backup job
***************************************************************************
'''

'''
***************************************************************************
Copy the backups to the remote directories
***************************************************************************
'''

'''
***************************************************************************
Print the log report
***************************************************************************
'''

'''
***************************************************************************
Print summary and email the report.
***************************************************************************
'''
write_log("Backup Script completed at " + time.strftime("%H:%M:%S") + " on " + DISPLAYDATE + " " + " by " + USER + ".\n")
print("Backup Script completed at " + time.strftime("%H:%M:%S") + " on " + DISPLAYDATE + " by " + USER + ".\n")
