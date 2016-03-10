#!/usr/bin/python3
"""
***************************************************************************
Script:                 Nimbus Intermixed Modular Back Up Script
Module:					Config Parse class
Authors/Maintainers:    Rich Nason (rnason@clusterfrak.com)
Description:            This Module will handle the actual gitlab backup.
***************************************************************************
"""
# This module expects that your backup local directory is set to the default
# location of /var/opt/gitlab/backups.
# This setting can be found in the /etc/gitlab/gitlab.rb file
# gitlab_rails['backup_path'] = "/var/opt/gitlab/backups"

# Define all modules that this script will utilize
import os  # Imported to allow run of popen to execute the command
import shutil  # Imported to allow easy copy operation
import tarfile  # Imported to tar up the backup and move it to the local directory location.
import json  # Imported to parse module arguments array

# Define the function to pass back to the main backup module.
def gitlab_backup_job(localdir, filedate, args):
    """The module will perform the actual gitlab backup"""
    # We don't need the config in this job so remove the variable to clear pylint errors
    # del args

    # Load the module aregments and jsonify them
    args = args.replace("'", "\"")
    args = json.loads(args)

    if 'gitlab_backup_path' in args:
        gitlab_path = args['gitlab_backup_path']
    else:
        gitlab_path = '/var/opt/gitlab/backups'

    # Print a warning to the user letting them know the location of the back up file settings.
    print('--------------------------------------------------------------------------------')
    print("This job assumes that the backup location set in your /etc/gitlab/gitlab.rb file")
    print("is set to : " + gitlab_path + "\n")
    print("If you would like to change this path, please set 'gitlab_backup_path'")
    print("in the module_args section of the config")
    print('--------------------------------------------------------------------------------')

    # Set the file date (separate the timestamp and date portion)
    filedate = str(filedate).split(" ")
    timestamp = filedate[1]
    timestamp = str(timestamp).split(".")
    timestamp = str(timestamp[0]).replace(":", "-")
    filedate = filedate[0] + "_" + timestamp

    # If any files currently exist in that directory then remove them all..
    if os.path.isdir(gitlab_path):
        for file_name in os.listdir(gitlab_path):
            try:
                file_path = os.path.join(gitlab_path, file_name)
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.unlink(file_path)
                # os.remove(gitlab_path + "/" + file_name)
                # shutil.rmtree(gitlab_path)
            except OSError as err:
                print("OS error: {0}".format(err))
                raise SystemError(" ERROR: " + file_name + " could not be removed.")
    else:
        try:
            os.makedirs(gitlab_path)
            shutil.chown(gitlab_path, user='git', group='git')
            print(gitlab_path + " has been created.")
        except FileNotFoundError:
            print(gitlab_path + " could not be created.")

    print("Running backup job...\n")
    execute_backup = os.popen('/opt/gitlab/bin/gitlab-rake gitlab:backup:create')
    # execute_backup = os.popen("echo 'ran the job' > /var/opt/gitlab/backups/gitlab_backup.file")
    job_log = execute_backup.read()
    execute_backup.close()

    # Grab the gitlab settings file
    print("\n")
    print("Backing up configuration files...")
    print("---------------------------------\n")
    shutil.copyfile('/etc/gitlab/gitlab.rb', gitlab_path + "/gitlab.rb")

    # Tar up the backup and move it to the local backup directory.
    print("Creating backup archive...")
    print("--------------------------\n")
    # Create the name of the tarball
    tar_name = '/gitlab_' + str(filedate) + '.tar.gz'
    tar_path = gitlab_path + tar_name

    # Tar the files
    tar = tarfile.open(tar_path, 'w:gz')
    for file_name in os.listdir(gitlab_path):
        tar.add(gitlab_path + "/" + file_name)
    tar.close()

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
