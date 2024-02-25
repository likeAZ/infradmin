import datetime
import json
import yaml
import subprocess
import os
import tarfile


class Backup:

    def __init__(self, i_keep=90, s_server='192.168.1.9', s_user='hugo', s_destination_path='/'):
        #with open("/usr/src/app/infradmin/conf/containers.json", 'r') as fp:
        #    self.d_json_conf = json.load(fp)
        #fp.close()
        self.s_exclude_conf = "/usr/src/app/infradmin/conf/backup.yaml"
        self.i_keep = i_keep
        self.s_bck_path = "/usr/src/app/infradmin/backup/"
        self.s_source_data = "/usr/src/app/infradmin/data/"
        self.s_server = s_server
        self.s_user = s_user
        self.s_destination_path = s_destination_path
        self.s_date_format = "%Y%m%d%H%M%S"
        self.o_now = datetime.datetime.now()
        self.l_dirs_to_backup_fp = []
        self.l_exclude = []

    def run_command(self, command=None):
        result = subprocess.call(command, shell=False)

    def get_list_dirs_to_exclude(self):
        with open(self.s_exclude_conf) as o_yaml_conf_file:
            o_yaml = yaml.safe_load(o_yaml_conf_file)
        self.l_exclude = o_yaml['exclude']
        o_yaml_conf_file.close()

    def backup(self):
        self.get_list_dirs_to_exclude()
        for s_dir_to_backup in os.listdir(self.s_source_data):
            for s_dir_to_exclude in self.l_exclude:
                if s_dir_to_exclude not in s_dir_to_backup:
                    s_dir_to_backup_fp = self.s_source_data + s_dir_to_backup
                    self.l_dirs_to_backup_fp.append(s_dir_to_backup_fp)

        s_timestamp = self.o_now.strftime(self.s_date_format)
        s_backup_filename = s_timestamp + "-mars_backup.tar.gz"
        o_tgz_file = tarfile.open(self.s_bck_path + s_backup_filename, 'w:gz')
        for s_dir_fp in self.l_dirs_to_backup_fp:
            o_tgz_file.add(s_dir_fp)
        o_tgz_file.close()
        self.rotate()
        self.push_backups()

    def rotate(self):

        for s_dir_backup in os.listdir(self.s_bck_path):
            s_date_backup = s_dir_backup
            o_date_backup = datetime.datetime.strptime(s_date_backup, __format=self.s_date_format)
            i_date_delta = int((self.o_now - o_date_backup).days)
            if i_date_delta >= self.i_keep:
                os.remove(self.s_bck_path + s_dir_backup)

    def push_backups(self):
        # one rsync command per path, ignore files vanished errors
        for s_backup_path in os.listdir(self.s_bck_path):
            s_backup_path = s_backup_path.strip()
            s_backup_path_fp = self.s_bck_path + s_backup_path
            #s_rsync_cmd = "rsync -av " + s_backup_path_fp + self.s_user + "@" + self.s_server + "::" + self.s_destination_path
            s_rsync_cmd = "rsync -av " + s_backup_path_fp + " " + self.s_destination_path
            logging.debug(s_rsync_cmd)
            self.run_command(command=s_rsync_cmd, ignore_errors=True)