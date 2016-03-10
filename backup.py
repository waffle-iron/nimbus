#!/usr/bin/python3
"""
***************************************************************************
Script:                 Nimbus Intermixed Modular Back Up Script
Authors/Maintainers:    Rich Nason (rnason@clusterfrak.com)
Description:            This script will perform a pluthra of various backups.
***************************************************************************
"""
# Define all modules that this script will require to function
import argparse  # Get, and parse incoming arguments from the execution of the script
import time  # Used to get the current date to apend to logs in pretty format
import datetime  # Used to do file date calculations
import os  # Used to grab the config files that will be parsed.
import shutil  # Imported to allow easy copy operation
import smtplib  # Library needed to send the email report
from email.mime.text import MIMEText  # Extra libraries to set the mimetype of the message

# Import Nimbus class libraries
from libs.parseconf import ParseConf  # Class to parse the referenced config file.
from libs.jobselect import module_select  # FN to grab information about the passed in job module.

# Import backup job modules:
from modules.gitlab import gitlab_backup_job  # This imports the gitlab backup job.
from modules.postgres import postgres_backup_job  # This imports the gitlab backup job.
from modules.mysql import mysql_backup_job  # This imports the gitlab backup job.
from modules.jenkins import jenkins_backup_job  # This imports the gitlab backup job.

'''
***************************************************************************
Define Global Functions Used for all Backup Job types.
***************************************************************************
'''


def write_log(string):
    """The purpose of this function is simply to allow an easy way to write to the logfile."""
    try:
        logfile = open(LOGFILE, 'a+')
        logfile.write(string)
        logfile.close()
    except IOError:
        raise SystemError('ERROR: ' + LOGFILE + ' does not exist!')

'''
***************************************************************************
Get Passed Arguments and Build the Help feature.
***************************************************************************
'''
# Gather Input Arugments:
BACKUP_JOB_DESC = """
The backup job module that you want to run.
Available module options currently are:
postgres, mysql, gitlab, jenkins
"""
CONFIG_FILE_DESC = """
The full path location of the config file that holds the options
for the backup job that you would like to run.
(/root/backup/mygitserver.ini)
"""

# Parse input arguments #
PARSE = argparse.ArgumentParser(description='NIMBUS is a modular backup utility \
                                designed to backup many different type of applications')
PARSE.add_argument('-b', '--backup', help=BACKUP_JOB_DESC, required=True)
PARSE.add_argument('-c', '--config', help=CONFIG_FILE_DESC, required=True)
ARGS = PARSE.parse_args()

# Show Argument Values #
print('\n')
print("Backup Job: %s" % ARGS.backup)
print("Config File: %s" % ARGS.config)
print('\n')

# Make the backup argument upper case so that we can evaluate what job we need to run.
# Take the Job named passed in via the -b statement and send it to the jobselector class.
# This will get information such as the App Name and Actual Function to run for the backup.
BACKUP_JOB = ARGS.backup.upper()
CONFIG_FILE = ARGS.config
APP, JOB = module_select(BACKUP_JOB)

'''
***************************************************************************
Set Global Variables and Parse the config file
***************************************************************************
'''

# Define Global Variables
# FILEDATE = time.strftime("%Y-%m-%d %H:%M:%S")
USER = os.getlogin()
FILEDATE = datetime.datetime.today()
print(FILEDATE)
print(datetime.datetime.now())
DISPLAYDATE = time.strftime("%a %B %d, %Y")
MAIL_SUBJECT = APP + ' Backup Report - ' + DISPLAYDATE
LOGFILEDIR = '/var/log/nimbus'
LOGFILE = LOGFILEDIR + '/' + APP.lower() + '_backup.log'
LOCALDIR = None

# Check to ensure that the config file actually exists.
if os.path.isfile(CONFIG_FILE):
    # Instanciate ParseConfig Object
    CONF = ParseConf(CONFIG_FILE)
    # OBJ = dir(CONF)
    # print(OBJ)

    # Print out the configuration
    CONF.print_header()
    CONF.print_backup_dirs()
    CONF.print_mail_sender()
    CONF.print_mail_recipients()
    CONF.print_module_args()
    CONF.print_footer()

else:
    print("Specified configuration file does not exist. Please check the path and try again!\n")
    raise SystemExit(" ERROR: Specified Configuration File Not Found")

'''
***************************************************************************
Set Local Dir Location
***************************************************************************
'''
# Make sure all of the directory locations actually exist.. If they dont' then crate them
print("Checking backup directory paths: ")
print("---------------------------------")
for directory in CONF.backup_dirs():
    dir_name = directory.get('directory')
    path = directory.get('path')
    dir_type = directory.get('type')

    # Setup the local backup directory
    if LOCALDIR is None:
        if dir_type == "local":
            LOCALDIR = path + dir_name
            print("INFO: " + LOCALDIR + " directory location set!")
        else:
            print()
            raise SystemExit("ERROR: At least one directory in the configuration \
                             must be set to type 'local'!")

'''
***************************************************************************
Instansiate the Logfile
***************************************************************************
'''

# Start the log file, clearing the contents in the event that the file already exists
# Check to ensure that the path exists
if not os.path.isdir(LOGFILEDIR):
    try:
        os.makedirs(LOGFILEDIR)
    except (FileNotFoundError, PermissionError) as error:
        raise SystemError("WARNING: " + LOGFILEDIR + " could not be created")

try:
    open(LOGFILE, 'w').close()
except (FileNotFoundError, PermissionError) as error:
    raise SystemError("WARNING: " + LOGFILEDIR + " not found!")

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
for directory in CONF.backup_dirs():
    dir_name = directory.get('directory')
    path = directory.get('path')
    retention = directory.get('retention_days')
    filepath = path + dir_name + "/"

    # For each file in each directory, run a time date check and remove any files
    # that are older then the retention period.
    for file_name in os.listdir(filepath):
        file_create_date = datetime.datetime.fromtimestamp(os.path.getmtime(filepath + file_name))
        file_age = FILEDATE - file_create_date

        # If the file is greater then the set retention, then remove the file.
        if file_age.days > int(retention):
            # print(path + file + " - " + str(file_age.days) + " days old - File removed!")
            write_log(filepath + file_name + " removed (" + str(file_age.days) + " days old)\n")
            try:
                os.remove(filepath + file_name)
                DELETED_FILES += 1
            except OSError as err:
                print("OS error: {0}".format(err))
                raise SystemExit(filepath + file_name + " could not be removed.")

        else:
            KEPT_FILES += 1
            # print("File Saved!: ")
            # print(path + dir_name + "/" + file_name + " - " + str(file_age.days) + " days old")
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
ARCHIVE_NAME, JOB_LOG = JOB(LOCALDIR, FILEDATE, CONF.module_args())
write_log(JOB_LOG + "\n")

write_log("============================================================\n\n")

'''
***************************************************************************
Copy the backups to the remote directories
***************************************************************************
'''
# For each of the listed directories, copy the backup file from the local directory
# to each of the backup locations.
print("Copying backup from local directory to all included remote directories...")
print("-------------------------------------------------------------------------\n")
for directory in CONF.backup_dirs():
    dir_name = directory.get('directory')
    path = directory.get('path')
    dir_type = directory.get('type')

    if dir_type != "local":
        shutil.copy2(LOCALDIR + "/" + ARCHIVE_NAME, path + dir_name + "/")

'''
***************************************************************************
Print the log report
***************************************************************************
'''
# Go to All of the backup directories and list out the contents of the dirctories.
print("Print out directory content reports...")
print("--------------------------------------\n")
for directory in CONF.backup_dirs():
    dir_name = directory.get('directory')
    path = directory.get('path')
    # Write Log Header
    write_log("Files inventory of " + path + dir_name + " folder:\n")
    write_log("============================================================\n")
    for file_name in os.listdir(path + dir_name):
        report_cmd = "ls -lah " + path + dir_name + "| grep " + file_name + \
        " | awk '{print $9,\t$5,\t$6,$7,$8}'"

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
write_log("Backup Script completed at " + time.strftime("%H:%M:%S") + \
          " on " + DISPLAYDATE + " " + " by " + USER + ".\n")
print("Backup Script completed at " + time.strftime("%H:%M:%S") + \
      " on " + DISPLAYDATE + " by " + USER + ".\n")

'''
***************************************************************************
Send the listed administrators notification that the backup job has completed.
***************************************************************************
'''
# Open a plain text file for reading.  For this example, assume that
# the text file contains only ASCII characters.
with open(LOGFILE) as log:
    # Create a text/plain message to send and to append to the json payload
    MSG = MIMEText(log.read())
    LOG_CONTENT = log.read()
    log.close()

# me == the sender's email address
# you == the recipient's email address
MSG['Subject'] = MAIL_SUBJECT
MSG['From'] = CONF.mail_sender()
MSG['To'] = CONF.mail_recipients()

# Send the message via our own SMTP server.
SENDMAIL = smtplib.SMTP('localhost')
SENDMAIL.send_message(MSG)
SENDMAIL.quit()

'''
***************************************************************************
Create a JSON payload to send to the Sybok Service if configured.
***************************************************************************
'''

# Define dict for payload and for size.
BACKUP_SIZE = []
PAYLOAD = []

# Get the size of the backup files
for directory in CONF.backup_dirs():
    dir_name = directory.get('directory')
    path = directory.get('path') + dir_name + ARCHIVE_NAME
    size = os.path.getsize(path)
    BACKUP_SIZE.append({'file_path': path, 'file_size': size})


PAYLOAD.append({"user": USER, "last_run": FILEDATE, "backup_size": BACKUP_SIZE, \
                "backup_log": LOG_CONTENT})
# print(PAYLOAD)
