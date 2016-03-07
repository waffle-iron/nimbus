#!/usr/bin/python3
"""
***************************************************************************
Script:                 Nimbus Intermixed Modular Back Up Script
Library:				Config Parse class
Authors/Maintainers:    Rich Nason (rnason@clusterfrak.com)
Description:            This class will handle parsing the included configuration file and returning a config object.
***************************************************************************
"""


class ParseConf(object):
    json = __import__('json')  # Used to parse the json config file
    pyos = __import__('os')  # Used to check the physical settings file location
    sys = __import__('sys')  # Used to system exit functions on error

    def __init__(self, config):
        self.configfile = config
        self.server_config = None

        if self.pyos.path.isfile(self.configfile):
            with open(self.configfile, encoding='utf-8') as self.config_file:
                self.server_config = self.json.loads(self.config_file.read())
                self.config_file.close()
        else:
            print("Specified configuration file does not exist. Please check the path and try again!\n")
            raise SystemExit(" ERROR: Specified Configuration File Not Found")

    def print_header(self):
        print('\n')
        print('===================================')
        print('Backup Settings:')
        print(self.configfile + ' Succesfully Loaded')
        print('-----------------------------------')

    def backup_dirs(self):
        # Load list of backup directories
        if 'backup_directories' in self.server_config:
            directory_list = self.server_config['backup_directories']
            # Verify that the directories exist, and if not...create them
            for directory in directory_list:
                # Make sure that all of the required keys exist in the passed dictionary object.
                if 'directory' in directory.keys():
                    dir_name = directory.get('directory')
                    dir_name = str(dir_name)
                else:
                    directory['directory'] = None

                if 'path' in directory.keys():
                    path = directory.get('path')

                    if not path.endswith('/'):
                        path = path + "/"
                        directory['path'] = path

                    # if dir_name is not None and dir_name != "":
                    #     path = path + dir_name + "/"
                    #     directory['path'] = path

                if 'label' in directory.keys():
                    label = directory.get('label')
                    label = str(label)
                else:
                    directory['label'] = None

                if 'retention_days' in directory.keys():
                    retention_days = directory.get('retention_days')
                    retention_days = int(retention_days)
                else:
                    directory['retention_days'] = 3

                if 'type' in directory.keys():
                    dir_type = directory.get('type')
                    dir_type = str(dir_type)
                else:
                    directory['retention_days'] = 'filesystem'

                # Check to ensure that the path exists
                if not self.pyos.path.isdir(path + dir_name):
                    try:
                        self.pyos.makedirs(path + dir_name)
                    except FileNotFoundError:
                        print("WARNING: " + path + dir_name + "could not be created")
        else:
            directory_list = '[{directory: "Not Defined, "path": "Not Defined", "retention_days": "Not Defined", "type": "Not Defined"}]'
        return directory_list

    def print_backup_dirs(self):
        # Print the list of backup directories defined in the global variable DIRECTORY_LIST
        print('Backup Directories:')
        directory_list = self.backup_dirs()
        for directory in directory_list:
            print('\t' + directory.get('label') + ': ')
            print('\t\t' + 'directory: ' + directory.get('directory'))
            print('\t\t' + 'path: ' + directory.get('path'))
            print('\t\t' + 'retention(days): ' + directory.get('retention_days'))
            print('\t\t' + 'type: ' + directory.get('type'))

    def module_args(self):
        # Load the binary executable location
        if 'module_args' in self.server_config:
            module_arg_list = self.json.load(self.server_config['module_args'])
        else:
            module_arg_list = None
        return module_arg_list

    def print_module_args(self):
        # Print mail sender config
        module_arg_list = self.module_args()
        for arg, value in module_arg_list.iteritems():
            print('\t' + arg + ': ' + value)

    def mail_sender(self):
        # Load mail sender config
        if 'mail_sender' in self.server_config:
            mail_sender = self.server_config['mail_sender']
        else:
            mail_sender = 'root'
        return mail_sender

    def print_mail_sender(self):
        # Print mail sender config
        mail_sender = self.mail_sender()
        print("Using Mail Sender: " + str(mail_sender))

    def mail_recipients(self):
        # Load mail recipients config
        if 'mail_recipients' in self.server_config:
            mail_recipients = self.server_config['mail_recipients']
        else:
            mail_recipients = 'root'
        return mail_recipients

    def print_mail_recipients(self):
        # Print mail recipients config
        mail_recipients = self.mail_recipients()
        print("Using Mail Recipients: " + str(mail_recipients))

    def print_footer(self):
        print('===================================')
        print('\n')
