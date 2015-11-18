#!/usr/bin/python3.4
'''
***************************************************************************
Script:                 Universal Backup Script
Module:				  	AWS Mount Script
Authors/Maintainers:    Rich Nason (rnason@getnucleus.io) / Walter Wernau (wallybenz@gmail.com)
Description:            This module will handle the connection to your AWS Bucket.
***************************************************************************
'''
# Import required modules
import os  # Imported to allow run of popen to execute the command


# Create function to check to see if Fuse is installed. If it is then return true, if not try and install it
def fuse_check():
	print('Checking to see if Fuse is properly installed...\n')
	fuse_installed = False

	# Define the Nucleus Repository
	repo = """
	[getnucleus_base]
	name=GetNucleus_CentOS-7 - Base
	baseurl=http://yum.getnucleus.io/centos/staging/7/base/x86_64/
	gpgcheck=1
	gpgkey=file:///etc/pki/rpm-gpg/NUCLEUS-GPG-KEY.public

	[getnucleus_custom]
	name=GetNucleus_CentOS-7 - Custom
	baseurl=http://yum.getnucleus.io/centos/staging/7/custom/x86_64/
	gpgcheck=1
	gpgkey=file:///etc/pki/rpm-gpg/NUCLEUS-GPG-KEY.public
	 """

	# First up, we need to check to see if Fuse is installed.
	fuse = os.popen('which s3fs')

	# If fuse is not installed try and install it if the box is a RHEL/CentOS box.
	if fuse == "" or fuse is None:
		if os.path.isfile('/etc/redhat-release'):
			try:
				# Install the Nuclues GPG KEY, and REPO, and then Install Fuse/Fuse-S3FS
				os.popen('rpm --import http://yum.getnucleus.io/centos/NUCLEUS-GPG-KEY.public')

				with open('/etc/yum.repos.d/nucleus.repo', 'w+') as repo_file:
					repo_file.write(repo)
				repo_file.close()

				os.system('yum clean all')
				os.system('yum install fuse fuse-s3fs')

				# Recheck to see if fuse is installed
				fuse = os.popen('which s3fs')
			except:
				raise SystemError(" FUSE could not be installed, Please install fuse and fuse-s3fs manually and then retry running the job.")
		else:
			raise SystemError(" This does not appear to be a RHEL/CentOS server, Please install fuse and fuse-s3fs manually and then retry running the job.")

	# Do a final check and return True or false
	if fuse is not None:
		fuse_installed = True

	return fuse_installed


def mount_aws():
	print('Mounting AWS Bucket...\n')
	# This function will mount the AWS Storage
	# First check to see if the password file exists
	key_check = os.path.isfile('/root/.passwd-s3fs')

	if not key_check:
		aws_id = raw_input("AWS Access Key Id: ")
		aws_secret = raw_input("AWS Secret Access Key Id: ")
		aws_bucket = raw_input("AWS Bucket to mount: ")
		aws_dir = raw_input("Local Directory to mount aws_bucket to: ")

		if aws_id != "" and aws_secret != "":
			try:
				# Write the id/secret file
				with open("/root/.passwd-s3fs", "a+") as aws_file:
					aws_file.write(aws_id + ":" + aws_secret)
				aws_file.close()

				# Set permissions
				os.chmod('~/.passwd-s3fs', 0o600)

				# Make the temp directory
				os.mkdir('/tmp/cache', 0o777)

				# Mount the storage
				mount_cmd = 's3fs -o use_cache=/tmp/cache ' + aws_bucket + " " + aws_dir
				os.system(mount_cmd)

				# Print results
				print("Your AWS Bucket " + aws_bucket + " is now mounted to " + aws_dir)

			except OSError as err:
				print("OS error: {0}".format(err))
				raise SystemError(" ERROR: " + aws_bucket + "could not be mounted, please try again.")
		else:
			raise SystemError(" You Must enter a valid Access Key Id and Secret Access Key!")

	# Print out the fstab statement
	print("Please ensure that you add the following to your /etc/fstab in order to mount your storage on boot:")
	print("s3fs#" + aws_bucket + aws_dir + "\t\tfuse _netdev,allow_other 0 0\n")


# Run the check, then run the mount
fuse_check()
mount_aws()
