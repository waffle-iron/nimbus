#!/usr/bin/python3
"""
***************************************************************************
Script:                 Nimbus Intermixed Modular Back Up Script
Module:					MySQL Backup Module
Authors/Maintainers:    Rich Nason (rnason@clusterfrak.com)
Description:            This Module will handle the actual mysql backup.
***************************************************************************
"""

# Define all modules that this script will utilize
import os  # Imported to allow run of popen to execute the command
import shutil  # Imported to allow easy copy operation
import tarfile  # Imported to tar up the backup and move it to the local directory location.
import json  # This is loaded to parse the server_settings.ini file


# Define the function to pass back to the main backup module.
def mysql_backup_job(localdir, filedate, args):
    """The module will perform the actual mysql / backup"""
    # Get the module arguments
    # del args

    # Load the module aregments and jsonify them
    args = args.replace("'", "\"")
    args = json.loads(args)

    # Get credentials
    if 'mysql_user' in args:
        mysql_user = args['mysql_user']
    else:
        mysql_user = 'root'

    if 'mysql_password' in args:
        mysql_password = args['mysql_password']

        if mysql_password == "":
            mysql_password = "\"\""
    else:
        mysql_password = "\"\""

    # Get Host Info
    if 'mysql_host' in args:
        mysql_host = args['mysql_host']
    else:
        mysql_host = 'localhost'

    if 'mysql_port' in args:
        mysql_port = args['mysql_port']
    else:
        mysql_port = 3306

    # Get list of databases to back up.
    if 'db_list' in args:
        db_list = args['db_list']
    else:
        db_list = "mysql"

    # Set the file date (separate the timestamp and date portion)
    filedate = str(filedate).split(" ")
    timestamp = filedate[1]
    timestamp = str(timestamp).split(".")
    timestamp = str(timestamp[0]).replace(":", "-")
    filedate = filedate[0] + "_" + timestamp

    # Create a temp directory to store the backup files in
    try:
        tmp_dir = '/tmp/mysql' + filedate
        if os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir)
        os.makedirs(tmp_dir)
    except:
        raise SystemExit(" ERROR: Failed to create tmp backup folder")

    # Perform the backup of the databases
    print("Running backup job...\n")
    job_log = None
    for database in db_list:
        # print(database)
        db_dump_cmd = "mysqldump" + " -h " + mysql_host + " -P " + str(mysql_port) + " --user=" \
        + mysql_user + " --password=" + mysql_password + " " + database + " > " + tmp_dir + "/" + database \
        + "-" + filedate + ".sql"

        print(db_dump_cmd)

        # Execute the Database Backups
        # print(db_dump_cmd)
        job_log_header = "Running " + database + " backup...\n"
        execute_backup = os.popen(db_dump_cmd)
        backup_log = execute_backup.read()
        execute_backup.close()

        # Concat all of the backup files
        if job_log is None:
            job_log = job_log_header
            job_log = job_log + "\n" + backup_log
        else:
            job_log = job_log + "\n" + job_log_header + "\n" + backup_log

    # Copy the my.cnf config file
    print("\n")
    print("Backing up configuration files...")
    print("---------------------------------\n")
    try:
        if os.path.isfile("/etc/my.cnf"):
            my_cnf = "/etc/my.cnf"
        elif os.path.isfile("/etc/mysql/my.cnf"):
            my_cnf = "/etc/mysql/my.cnf"
    except FileNotFoundError:
        print("Error: File Not Found!")
        raise SystemError("ERROR: my.cnf not found, is mysql-server properly installed!")

    shutil.copyfile(my_cnf, tmp_dir + "/my.cnf")

    # Tar up the backup and move it to the local backup directory.
    print("Creating backup archive...")
    print("--------------------------\n")
    # Create the name of the tarball
    tar_name = '/mysql_' + str(filedate) + '.tar.gz'
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
        shutil.rmtree(tmp_dir)
    except OSError as err:
        print("OS error: {0}".format(err))
        raise SystemError(" ERROR: " + tmp_dir + " could not be removed.")

    print("Job backup module completed...")
    print("-----------------------------\n")
    return tar_name, job_log
