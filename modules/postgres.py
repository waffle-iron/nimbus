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
def postgres_backup_job(localdir, filedate, config):
	# Print a warning to the user letting them know the location of the back up file settings.
	print('----------------------------------------------------------------------------------------------------------------')
	print("This job assumes that the the following: ")
	print("pg_dump is located in: /usr/pgsql-9.4/bin/pg_dump")
	print("pg_dumpll is located in /usr/pgsql-9.4/bin/pg_dumpall")
	print('----------------------------------------------------------------------------------------------------------------\n')

	# Set params for PG_DUMP and PG_DUMPALL
	pg_dump = '/usr/pgsql-9.4/bin/pg_dump'
	pg_dumpall = '/usr/pgsql-9.4/bin/pg_dumpall'

	# Set the file date (remove the timestamp and just keep the date portion)
	filedate = str(filedate).split(" ")
	filedate = filedate[0]

	# Digest the config file and pull out the postgres options.
	with open(config, encoding='utf-8') as config_file:
		backup_config = json.loads(config_file.read())

		# Load configured credentials.
		if 'credentials' in backup_config:
			pgsql_creds = backup_config['credentials']

		# Get list of databases to backup.
		if 'backup_list' in backup_config:
			pgsql_dbs = backup_config['backup_list']
	config_file.close()

	# Create a temp directory to store the backup files in
	try:
		tmp_dir = '/tmp/postgres_' + filedate
		os.makedirs(tmp_dir)
	except:
		raise SystemExit(" ERROR: Failed to create tmp backup folder")

	# Perform the backup of the databases
	for database in pgsql_dbs:
		pg_dump + "-h" + pgsql_creds['pg_host'] + "-p" + pgsql_creds['pg_port'] + "-U" \
			+ pgsql_creds['pg_user'] + database + " > " + tmp_dir + "/" + database + "-" + filedate + ".sql"

	# Backup the pg_roles
		pg_dumpall + "-h" + pgsql_creds['pg_host'] + "-p" + pgsql_creds['pg_port'] + "-U" \
			+ pgsql_creds['pg_user'] + "-v --globals-only > " + tmp_dir + "/" + "pg_roles-" + filedate + ".sql"

	# Copy the pg_hba and postgres config files


	# Tar everything up and move it to the LOCALDIR

	# Remove the tmp file.
