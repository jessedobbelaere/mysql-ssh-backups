import paramiko
import json
import time
import os

# SSH function to get the output from the server when the command is executed
def ssh(cmd):
    out = []
    msg = [stdin, stdout, stderr] = client.exec_command(cmd)
    for item in msg:
        try:
            for line in item:
                out.append(line.strip('\n'))
        except Exception, e:
            pass

    return list(out)


# Get current script directory
script_dir_path = os.path.dirname(os.path.realpath(__file__))

# Loading the configuration file
config_file = open(script_dir_path + "/config/config.json", "r")
config_file = json.load(config_file)
backup_folder = script_dir_path + '/' + config_file['settings']['backup_folder']

# Loop every website to backup
for website in config_file['websites']:
    
    # Open SSH connection
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.load_system_host_keys()
    client.connect(config_file['websites'][website]['config']['host'], username=config_file['websites'][website]['config']['username'])

    # Open SFTP connection
    sftp_client = client.open_sftp()

    # Create backup folder (if not existing)
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    # Loop the databases
    for database in config_file['websites'][website]['databases']:
        if not os.path.exists(backup_folder + website + '/' + database):
            os.makedirs(backup_folder + website + '/' + database)

        # Create backup file
        ssh('mysqldump -u' + config_file['websites'][website]['databases'][database]['mysql_user'] + ' -p' + config_file['websites'][website]['databases'][database]['mysql_pwd'] + ' -h' + config_file['websites'][website]['databases'][database]['mysql_host'] + ' ' + database + ' --lock-tables=false | bzip2 - - > db-backup-tmp.sql.bz2')
        
        # Open SFTP connection & download the backup file to the backup dir
        remote_file = sftp_client.get("db-backup-tmp.sql.bz2", backup_folder + website + '/' + database + "/backup-" + time.strftime("%Y-%m-%d-%H%M%S") + ".sql.bz2")
        
        # Remove the tmp sql file from the server
        ssh('rm db-backup-tmp.sql.bz2')

    # Close the connection
    client.close()