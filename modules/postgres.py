#!/usr/bin/python3
"""
***************************************************************************
Script:                 Nimbus Intermixed Modular Back Up Script
Module:					Postgres Backup Module
Authors/Maintainers:    Rich Nason (rnason@clusterfrak.com)
Description:            This Module will handle the actual postgres backup.
***************************************************************************
"""

# Define all modules that this script will utilize
import os  # Imported to allow run of popen to execute the command
import shutil  # Imported to allow easy copy operation
import tarfile  # Imported to tar up the backup and move it to the local directory location.
import json  # This is loaded to parse the server_settings.ini file


# Define the function to pass back to the main backup module.
def postgres_backup_job(localdir, filedate, args):
    """The module will perform the actual postgres backup"""
    # Get the module arguments
    # del args

    # Load the module aregments and jsonify them
    args = args.replace("'", "\"")
    args = json.loads(args)

    # Get postgres version
    if 'pg_ver' in args:
        pg_ver = args['pg_ver']
    else:
        pg_ver = "9.4"

    if 'pg_dump' in args:
        pg_dump = args['pg_dump']
    else:
        pg_dump = '/usr/pgsql-' + pg_ver + '/bin/pg_dump'

    # Get path of binaries
    if 'pg_dumpall' in args:
        pg_dumpall = args['pg_dumpall']
    else:
        pg_dumpall = '/usr/pgsql-' + pg_ver + '/bin/pg_dumpall'

    # Get credentials
    if 'pg_user' in args:
        pg_user = args['pg_user']
    else:
        pg_user = 'postgres'

    if 'pg_password' in args:
        pg_password = args['pg_password']
        
        if pg_password == "":
            pg_password = "\"\"" 
    else:
        pg_password = "\"\""

    # Get Host Info
    if 'pg_host' in args:
        pg_host = args['pg_host']
    else:
        pg_host = 'localhost'

    if 'pg_port' in args:
        pg_port = args['pg_port']
    else:
        pg_port = 5432

    # Get list of databases to back up.
    if 'db_list' in args:
        db_list = args['db_list']
    else:
        db_list = "postgres"

    # Print a warning to the user letting them know the location of the back up file settings.
    print('----------------------------------------------------------------------------')
    print("This job assumes that the the following: ")
    print("pg_dump is located in: " + pg_dump)
    print("pg_dumpall is located in: " + pg_dumpall)
    print("If you would like to change this path, please set 'pg_dump' and 'pg_dumpall'")
    print("in the module_args section of the settings file")
    print('--------------------------------------------------------------------------\n')

    # Set the file date (remove the timestamp and just keep the date portion)
    filedate = str(filedate).split(" ")
    filedate = filedate[0]

    # Create a temp directory to store the backup files in
    try:
        tmp_dir = '/tmp/postgres_' + filedate
        if os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir)
        os.makedirs(tmp_dir)
    except:
        raise SystemExit(" ERROR: Failed to create tmp backup folder")

    # Perform the backup of the databases
    print("Running backup job...\n")
    joblog = ""
    for database in db_list:
        # print(database)
        # db_dump_cmd = pg_dump + " -h " + pg_host + " -p " + str(pg_port) + " -U " + pg_user + \
        # " -w " + " " + database + " > " + tmp_dir + "/" + database + "-" + filedate + ".sql"
        db_dump_cmd = pg_dump + " --dbname=postgresql://" + pg_user + ":" + pg_password + "@" \
        + pg_host + ":" + str(pg_port) + "/" + database

        # Execute the Database Backups
        # print(db_dump_cmd)
        job_log = "Running " + database + " backup:\n"
        execute_backup = os.popen(db_dump_cmd)
        backup_log = execute_backup.read()
        execute_backup.close()

        # Concat all of the backup files
        job_log = job_log + "\n" + backup_log

    # Backup the pg_roles
    db_dumpall_cmd = pg_dumpall + " -h " + pg_host + " -p " + str(pg_port) + " -U " + pg_user + \
    " -w " + " -v --globals-only > " + tmp_dir + "/" + "pg_roles-" + filedate + ".sql"

    execute_backup_roles = os.popen(db_dumpall_cmd)
    job_log_roles = execute_backup_roles.read()
    execute_backup_roles.close()

    # Concat the logs
    job_log = job_log + "\n" + job_log_roles

    # Copy the pg_hba and postgres config files
    print("\n")
    print("Backing up configuration files...")
    print("---------------------------------\n")
    try:
        if os.path.isfile("/var/lib/pgsql/" + pg_ver + "/data/pg_hba.conf"):
            pg_hba = "/var/lib/pgsql/" + pg_ver + "/data/pg_hba.conf"
        elif os.path.isfile("/var/lib/pgsql/data/pg_hba.conf"):
            pg_hba = "/var/lib/pgsql/data/pg_hba.conf"
    except FileNotFoundError:
        print("Error: File Not Found!")
        raise SystemError(" ERROR: File not found, please ensure postgres-server is properly installed!")

    try:
        if os.path.isfile("/var/lib/pgsql/" + pg_ver + "/data/postgresql.conf"):
            pg_conf = "/var/lib/pgsql/" + pg_ver + "/data/postgresql.conf"
        elif os.path.isfile("/var/lib/pgsql/data/postgresql.conf"):
            pg_conf = "/var/lib/pgsql/data/postgresql.conf"
    except FileNotFoundError:
        print("Error: File Not Found!")
        raise SystemError(" ERROR: File not found, please ensure postgres-server is properly installed!")

    shutil.copyfile(pg_hba, tmp_dir + "/pg_hba")
    shutil.copyfile(pg_conf, tmp_dir + "/postgres.conf")

    # Tar up the backup and move it to the local backup directory.
    print("Creating backup archive...")
    print("--------------------------\n")
    # Create the name of the tarball
    tar_name = '/postgres_' + str(filedate) + '.tar.gz'
    tar_path = tmp_dir + tar_name

    # Tar the files
    tar = tarfile.open(tar_path, 'w:gz')
    for file_name in os.listdir(tmp_dir):
        tar.add(tmp_dir + "/" + file_name)
    tar.close()

    # Move the backup to the local directory
    print("Moving backup archive to " + localdir + "...")
    print("--------------------------------------------\n")
    try:
        shutil.move(tar_path, localdir + "/" + tar_name)
        # Since we move the tar and remove the tmp dir, repath the tar_path to pass back to main
        tar_path = localdir + "/" + tar_name
    except OSError as err:
        print("OS error: {0}".format(err))
        raise SystemError(" ERROR: Backup could not be moved!")

    # Remove the tmp directory.
    try:
        # os.remove(gitlab_path + "/" + file_name)
        shutil.rmtree(tmp_dir)
    except OSError as err:
        print("OS error: {0}".format(err))
        raise SystemError(" ERROR: " + tmp_dir + " could not be removed.")

    print("Job backup module completed...")
    print("-----------------------------\n")
    return tar_name, job_log
