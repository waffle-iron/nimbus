#!/usr/bin/python3.4
'''
***************************************************************************
Script:                 Universal Backup Script
Module:				  	Postgres
Authors/Maintainers:    Rich Nason (rnason@getnucleus.io)
Description:            This script will perform Postgresql backup jobs.
***************************************************************************
'''

# Define all modules that this script will utilize
import os  # Imported to allow run of popen to execute the command
import shutil  # Imported to allow easy copy operation
import tarfile  # Imported to tar up the backup and move it to the local directory location.
import json  # This is loaded to parse the server_settings.ini file


# Define the function to pass back to the main backup module.
def jenkins_backup_job(localdir, filedate, config):
    """This is the actual backup action that will backup jenkins"""
    print('mysql')
