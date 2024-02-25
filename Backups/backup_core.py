import datetime
import yaml
import subprocess
import os
import tarfile
import common.infradmin_logs


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
        self.l_files_to_backup_fp = []
        self.l_exclude = []
        self.o_logger = common.infradmin_logs.O_LOGGER

    def run_command(self, command=None):
        result = subprocess.call(command, shell=False)

    def get_list_dirs_to_exclude(self):
        self.o_logger.info("getting exclude list")
        with open(self.s_exclude_conf) as o_yaml_conf_file:
            o_yaml = yaml.safe_load(o_yaml_conf_file)
        self.l_exclude = o_yaml['exclude']
        o_yaml_conf_file.close()
        self.o_logger.info("exclude list is :")
        for s_exclude_dir in self.l_exclude:
            self.o_logger.info(s_exclude_dir)

    def backup(self):
        self.o_logger.info("starting backup...")
        self.get_list_dirs_to_exclude()
        for s_dir_path, l_subdirectories, l_files in os.walk(self.s_source_data):
            for s_file in l_files:
                s_file_to_backup_fp = os.path.join(s_dir_path, s_file)
                self.o_logger.info("adding " + s_file_to_backup_fp + " in the backup list")
                self.l_files_to_backup_fp.append(s_file_to_backup_fp)
        for s_dir_to_exclude in self.l_exclude:
            for s_file_to_backup in self.l_files_to_backup_fp:
                if s_dir_to_exclude in s_file_to_backup:
                    self.o_logger.info("deleting " + s_file_to_backup + " in the backup list")
                    self.l_files_to_backup_fp.remove(s_file_to_backup)

        s_timestamp = self.o_now.strftime(self.s_date_format)
        s_backup_filename = s_timestamp + "-mars_backup.tar.gz"
        self.o_logger.info("backup name will be : " + s_backup_filename)
        o_tgz_file = tarfile.open(self.s_bck_path + s_backup_filename, 'w:gz')
        for s_file_fp in self.l_files_to_backup_fp:
            self.o_logger.info("backuping : " + s_file_fp)
            o_tgz_file.add(s_file_fp)
        o_tgz_file.close()
        self.rotate()
        self.push_backups()

    def rotate(self):
        self.o_logger.info("deleting files older than : " + str(self.i_keep))
        for s_dir_backup in os.listdir(self.s_bck_path):
            s_date_backup = s_dir_backup
            o_date_backup = datetime.datetime.strptime(s_date_backup, __format=self.s_date_format)
            i_date_delta = int((self.o_now - o_date_backup).days)
            if i_date_delta >= self.i_keep:
                os.remove(self.s_bck_path + s_dir_backup)

    def push_backups(self):
        # one rsync command per path, ignore files vanished errors
        self.o_logger.info("pushing backups..")
        for s_backup_path in os.listdir(self.s_bck_path):
            s_backup_path = s_backup_path.strip()
            s_backup_path_fp = self.s_bck_path + s_backup_path
            self.o_logger.info("pushing : " + s_backup_path_fp + " to " + self.s_destination_path)
            #s_rsync_cmd = "rsync -av " + s_backup_path_fp + self.s_user + "@" + self.s_server + "::" + self.s_destination_path
            s_rsync_cmd = "rsync -av " + s_backup_path_fp + " " + self.s_destination_path
            self.o_logger.info("with command : " + s_rsync_cmd)
            self.run_command(command=s_rsync_cmd)