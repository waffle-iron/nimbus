#!/usr/bin/python3
"""
***************************************************************************
Script:                 Nimbus Intermixed Modular Back Up Script
Library:				Job Selector class
Authors/Maintainers:    Rich Nason (rnason@clusterfrak.com)
Description:            This class will handle Returning an object that contains 
						information about the module to run
***************************************************************************
"""

class JobSelector(Object):
"""The purpose of this class is to select the type of job to run, and return information about that job"""
def __init__(self, backup_job):
        self.backup_job = backup_job

def module_select(self):
	"""This function will select the module name and function name from the given input"""
	if self.backup_job == 'GITLAB':
    	module_name = 'Gitlab'
    	run_module = gitlab_backup_job
	elif self.backup_job == 'POSTGRES':
    	module_name = 'PostgreSQL'
    	run_module = postgres_backup_job
	elif self.backup_job == 'MYSQL':
    	module_name = 'MySQL'
    	run_module = mysql_backup_job
	elif self.backup_job== 'JENKINS':
    	module_name = 'Jenkins'
    	run_module = jenkins_backup_job
	else:
    	raise SystemExit(" ERROR: You have identified an Undefined Backup Job.. Please try again")

    return module_name run_module