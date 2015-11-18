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
import shutil  # Imported to allow easy copy operation
import smtplib  # Library needed to send the email report
from email.mime.text import MIMEText  # Extra libraries to set the mimetype of the message

# Import backup job modules:
from modules.gitlab import gitlab_backup_job  # This imports the gitlab backup job.

'''
***************************************************************************
Define Global Functions Used for all Backup Job types.
***************************************************************************
'''


def write_log(string):
    try:
        logfile = open(LOGFILE, 'a+')
        logfile.write(string)
        logfile.close()
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
    JOB = gitlab_backup_job
else:
    raise SystemExit(" ERROR: You have identified an Undefined Backup Job.. Please try again")

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
LOGFILE = '/tmp/' + APP.lower() + '_backup.log'
LOCALDIR = None

if os.path.isfile(CONFIG_FILE):
    print('========================================')
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
                print('\t\t' + 'type: ' + directory.get('type'))

        # Load mail sender
        if 'mail_sender' in BACKUP_CONFIG:
            MAIL_SENDER = BACKUP_CONFIG['mail_sender']
            print("Mail Sender: " + MAIL_SENDER)

        # Load mail recipients
        if 'mail_recipients' in BACKUP_CONFIG:
            MAIL_RECIPIENTS = BACKUP_CONFIG['mail_recipients']
            print("Mail Recipients: " + MAIL_RECIPIENTS)

    print('========================================')
    print('\n')
else:
    print("Specified configuration file does not exist. Please check the path and try again!\n")
    raise SystemExit(" ERROR: Specified Configuration File Not Found")


'''
***************************************************************************
Make sure all of the listed directories in the config file exist, or create them
***************************************************************************
'''
# Make sure all of the directory locations actually exist.. If they dont' then crate them
print("Checking backup directory paths: ")
print("---------------------------------")
for directory in DIRECTORY_LIST:
    dir_name = directory.get('directory')
    path = directory.get('path') + APP.lower()
    dir_type = directory.get('type')

    # Check to see if the path exists:
    if not os.path.isdir(path):
        try:
            os.makedirs(path)
            print("INFO: " + path + " has been created.")
        except FileNotFoundError:
            print("WARNING " + path + " could not be created.")
    print("\n")

    # Setup the local backup directory
    if LOCALDIR is None:
        if dir_type == "local":
            LOCALDIR = path
            print("INFO: " + LOCALDIR + " directory location set!")
        else:
            print()
            raise SystemExit(" ERROR: At least one directory in the configuration must be set to type 'local'!")

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
    for file_name in os.listdir(path):
        file_create_date = datetime.datetime.fromtimestamp(os.path.getmtime(path + "/" + file_name))
        file_age = FILEDATE - file_create_date

        # If the file is greater then the set retention, then remove the file.
        if file_age.days > int(retention):
            # print(path + "/" + file + " - " + str(file_age.days) + " days old - File removed!")
            write_log(path + "/" + file_name + " removed (" + str(file_age.days) + " days old)\n")
            try:
                os.remove(path + "/" + file_name)
                DELETED_FILES += 1
            except OSError as err:
                print("OS error: {0}".format(err))
                raise SystemExit(path + "/" + file_name + " could not be removed.")

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
# Write Log header
write_log("Performing backup operation:\n")
write_log("============================================================\n")

# Set the logging variable, and execute the backup job.
ARCHIVE_NAME, JOB_LOG = JOB(LOCALDIR, FILEDATE)
write_log(JOB_LOG + "\n")

write_log("============================================================\n\n")

'''
***************************************************************************
Copy the backups to the remote directories
***************************************************************************
'''
# For each of the listed directories, copy the backup file from the local directory to the backup locations.
print("Copying backup from local directory to all included remote directories...")
print("-------------------------------------------------------------------------\n")
for directory in DIRECTORY_LIST:
    dir_name = directory.get('directory')
    path = directory.get('path') + APP.lower()
    dir_type = directory.get('type')

    if dir_type != "local":
        shutil.copy2(LOCALDIR + "/" + ARCHIVE_NAME, path + "/")

'''
***************************************************************************
Print the log report
***************************************************************************
'''
# Go to All of the backup directories and list out the contents of the dirctories.
print("Print out directory content reports...")
print("--------------------------------------\n")
for directory in DIRECTORY_LIST:
    dir_name = directory.get('directory')
    path = directory.get('path') + APP.lower() + "/"
    # Write Log Header
    write_log("Files moved to " + path + " folder:\n")
    write_log("============================================================\n")
    for file_name in os.listdir(path):
        report_cmd = "ls -lah | grep " + file_name + " | awk '{print $9,\t$5,\t$6,$7,$8}'"
        print(report_cmd)
        execute_ls = os.popen(report_cmd)
        report = execute_ls.read()
        execute_ls.close()
        write_log(report)

    write_log("\n\n")
'''
***************************************************************************
Print summary and email the report.
***************************************************************************
'''
write_log("Backup Script completed at " + time.strftime("%H:%M:%S") + " on " + DISPLAYDATE + " " + " by " + USER + ".\n")
print("Backup Script completed at " + time.strftime("%H:%M:%S") + " on " + DISPLAYDATE + " by " + USER + ".\n")

'''
***************************************************************************
Send the listed administrators notification that the backup job has completed.
***************************************************************************
'''
# Open a plain text file for reading.  For this example, assume that
# the text file contains only ASCII characters.
with open(LOGFILE) as log:
    # Create a text/plain message
    MSG = MIMEText(log.read())

# me == the sender's email address
# you == the recipient's email address
MSG['Subject'] = MAIL_SUBJECT
MSG['From'] = MAIL_SENDER
MSG['To'] = MAIL_RECIPIENTS

# Send the message via our own SMTP server.
SENDMAIL = smtplib.SMTP('localhost')
SENDMAIL.send_message(MSG)
SENDMAIL.quit()
