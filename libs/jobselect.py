#!/usr/bin/python3
"""
***************************************************************************
Script:                 Nimbus Intermixed Modular Back Up Script
Library:				Job Selector class
Authors/Maintainers:    Rich Nason (rnason@clusterfrak.com)
Description:            This function will handle Returning an object that contains
                        information about the module to run
***************************************************************************
"""

# Import backup job modules:
from modules.gitlab import gitlab_backup_job  # This imports the gitlab backup job.
from modules.postgres import postgres_backup_job  # This imports the gitlab backup job.
from modules.mysql import mysql_backup_job  # This imports the gitlab backup job.
from modules.jenkins import jenkins_backup_job  # This imports the gitlab backup job.

def module_select(backup_job):
    """This function will select the module name and function name from the given input"""
    if backup_job == 'GITLAB':
        module_name = 'Gitlab'
        run_module = gitlab_backup_job
    elif backup_job == 'POSTGRES':
        module_name = 'PostgreSQL'
        run_module = postgres_backup_job
    elif backup_job == 'MYSQL' or backup_job == 'MARIADB':
        module_name = 'MySQL'
        run_module = mysql_backup_job
    elif backup_job == 'JENKINS':
        module_name = 'Jenkins'
        run_module = jenkins_backup_job
    else:
        raise SystemExit(" ERROR: You have identified an Undefined Backup Job.. Please try again")

    return (module_name, run_module)
