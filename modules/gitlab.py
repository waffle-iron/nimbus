#!/usr/bin/python3
"""
***************************************************************************
Script:                 Nimbus Intermixed Modular Back Up Script
Module:					Config Parse class
Authors/Maintainers:    Rich Nason (rnason@clusterfrak.com)
Description:            This Module will handle the actual gitlab backup.
***************************************************************************
"""
# This module expects that your backup local directory is set to the default location of /var/opt/gitlab/backups.
# This setting can be found in the /etc/gitlab/gitlab.rb file
# gitlab_rails['backup_path'] = "/var/opt/gitlab/backups"

# Define all modules that this script will utilize
import os  # Imported to allow run of popen to execute the command
import shutil  # Imported to allow easy copy operation
import tarfile  # Imported to tar up the backup and move it to the local directory location.

# Set the gitlab configured backup path
GITLAB_PATH = '/var/opt/gitlab/backups'

# Function to remove all files out of the backup path before/after the backup
def file_clear():
    """The purpose of this function is to clear out the local gitlab backup dir"""
    # If any files currently exist in that directory then remove them all..
    for file_name in os.listdir(GITLAB_PATH):
        try:
            # os.remove(GITLAB_PATH + "/" + file_name)
            shutil.rmtree(GITLAB_PATH)
        except OSError as err:
            print("OS error: {0}".format(err))
            raise SystemError(" ERROR: " + file_name + " could not be removed.")


# Define the function to pass back to the main backup module.
def gitlab_backup_job(localdir, filedate, config):
    """This is the function that performs the gitlab backup job"""
    # We don't need the config in this job so remove the variable to clear pylint errors
    del config

    # Print a warning to the user letting them know the location of the back up file settings.
    print('----------------------------------------------------------------------------------------------------------------')
    print("This job assumes that the backup location set in your /etc/gitlab/gitlab.rb file is set to " + GITLAB_PATH + "\n")
    print('----------------------------------------------------------------------------------------------------------------')

    # Set the file date (remove the timestamp and just keep the date portion)
    filedate = str(filedate).split(" ")
    filedate = filedate[0]

    # If any files currently exist in that directory then remove them all..
    file_clear()

    # Make a tmp directory and perform the backup, then tar up that directory.
    # Check to see if the path exists.
    if not os.path.isdir(GITLAB_PATH):
        try:
            os.makedirs(GITLAB_PATH)
            shutil.chown(GITLAB_PATH, user='git', group='git')
            print(GITLAB_PATH + " has been created.")
        except FileNotFoundError:
            print(GITLAB_PATH + " could not be created.")

    # Check to make sure that gitlab is using the most up to date pg_dump
    pg_dump = os.popen('which pg_dump')
    pg_dump_host_ver = os.popen(pg_dump + ' --version')
    pg_embedded_ver = os.popen('/opt/gitlab/embedded/bin/pg_dump --version')

    if pg_dump_host_ver != pg_embedded_ver:
        print("The version of PG_DUMP on the host is higher then the version of the embedded Gitlab PG_DUMP")
        print("In order to correct the issue, you can update the embedded version of PG_DUMP with the following")
        print("mv /opt/gitlab/embedded/bin/pg_dump /opt/gitlab/embedded/bin/pg_dump.embedded")
        print("cd /opt/gitlab/embedded/bin/; ln -s " + pg_dump + " pg_dump")

    print("Running backup job...\n")
    execute_backup = os.popen('/opt/gitlab/bin/gitlab-rake gitlab:backup:create')
    # execute_backup = os.popen("echo 'ran the job' > /var/opt/gitlab/backups/gitlab_backup.file")
    job_log = execute_backup.read()
    execute_backup.close()

    # Grab the gitlab settings file
    print("\n")
    print("Backing up configuration files...")
    print("---------------------------------\n")
    shutil.copyfile('/etc/gitlab/gitlab.rb', GITLAB_PATH + "/gitlab.rb")

    # Tar up the backup and move it to the local backup directory.
    print("Creating backup archive...")
    print("--------------------------\n")
    # Create the name of the tarball
    tar_name = '/gitlab_' + str(filedate) + '.tar.gz'
    tar_path = GITLAB_PATH + tar_name

    # Tar the files
    tar = tarfile.open(tar_path, 'w:gz')
    for file_name in os.listdir(GITLAB_PATH):
        tar.add(GITLAB_PATH + "/" + file_name)
    tar.close()

    # Remove the files that were included in the archive
    file_clear()

    # Move the backup to the local directory
    print("Moving backup archive to " + localdir + "...")
    print("--------------------------------------------\n")
    try:
        shutil.move(tar_path, localdir + "/" + tar_name)
    except OSError as err:
        print("OS error: {0}".format(err))
        raise SystemError(" ERROR: Backup could not be moved!")

    print("Job backup module completed...")
    print("-----------------------------\n")
    return tar_name, job_log
