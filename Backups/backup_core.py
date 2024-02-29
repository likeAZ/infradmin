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
        self.s_conf_file = "/usr/src/app/infradmin/conf/backup/backup.yaml"
        self.s_exclude_conf = "/usr/src/app/infradmin/conf/backup/exclude.yaml"
        self.i_keep = i_keep
        self.s_bck_path = "/usr/src/app/infradmin/backup/"
        self.s_source_data = "/usr/src/app/infradmin/data/"
        self.s_server = s_server
        self.s_user = s_user
        self.s_destination_path = s_destination_path
        self.s_date_format = "%Y%m%d%H%M%S"
        self.o_now = datetime.datetime.now()
        self.l_files_to_backup_fp = []
        self.l_backup_name = []
        self.d_yaml = []
        self.s_backup_filename = None
        self.o_logger = common.infradmin_logs.O_LOGGER

    def run_command(self, command=None):
        result = subprocess.call(command, shell=False)

    def backups(self):
        self.get_info_from_conf()
        self.do_backup()
        for s_backup_name in self.l_backup_name:
            if self.is_local(s_backup_name):
                self.rotate(self.get_retention(s_backup_name))
            else:
                self.rotate(self.get_retention(s_backup_name))
                self.push_backups()

    def get_info_from_conf(self):
        self.o_logger.info("getting exclude list")
        with open(self.s_conf_file) as o_yaml_conf_file:
            self.d_yaml = yaml.safe_load(o_yaml_conf_file)
        self.l_backup_name = list(self.d_yaml.keys())
        o_yaml_conf_file.close()

    def get_exclude_list(self):
        o_exclude_file = yaml.safe_load(self.s_exclude_conf)
        l_exclude = o_exclude_file['exclude']
        self.o_logger.info("exclude list for is :")
        for s_exclude_dir in l_exclude:
            self.o_logger.info(s_exclude_dir)
        return l_exclude

    def is_local(self, s_backup_name):
        b_is_local = False
        if self.d_yaml[s_backup_name]['type'] == 'local':
            b_is_local = True
        return b_is_local

    def delete_local_backup(self):
        os.remove(self.s_bck_path + self.s_backup_filename)

    def get_retention(self, s_backup_name):
        return self.d_yaml[s_backup_name]['keep']

    def do_backup(self):
        self.o_logger.info("starting backup...")
        l_files_to_backup_fp_tmp = []
        l_exclude = self.get_exclude_list()
        for s_dir_path, l_subdirectories, l_files in os.walk(self.s_source_data):
            for s_file in l_files:
                s_file_to_backup_fp = os.path.join(s_dir_path, s_file)
                l_files_to_backup_fp_tmp.append(s_file_to_backup_fp)
        for s_dir_to_exclude in l_exclude:
            self.o_logger.info("deleting " + s_dir_to_exclude + " in the backup list")
            l_files_to_backup_fp_tmp = [file_path for file_path in l_files_to_backup_fp_tmp if not file_path.startswith(s_dir_to_exclude)]
        self.l_files_to_backup_fp = l_files_to_backup_fp_tmp
        s_timestamp = self.o_now.strftime(self.s_date_format)
        self.s_backup_filename = s_timestamp + "-mars.tar.gz"
        self.o_logger.info("backup name will be : " + self.s_backup_filename)
        o_tgz_file = tarfile.open(self.s_bck_path + self.s_backup_filename, 'w:gz')
        for s_file_fp in self.l_files_to_backup_fp:
            self.o_logger.info("backuping : " + s_file_fp)
            o_tgz_file.add(s_file_fp)
        o_tgz_file.close()

    def rotate(self, i_keep):
        self.o_logger.info("deleting files older than : " + str(i_keep) + "days")
        for s_dir_backup in os.listdir(self.s_bck_path):
            s_date_backup = s_dir_backup[:8]
            o_date_backup = datetime.datetime.strptime(s_date_backup, self.s_date_format[:8])
            i_date_delta = int((self.o_now - o_date_backup).days)
            if i_date_delta >= i_keep:
                os.remove(self.s_bck_path + s_dir_backup)

    def push_backups(self):
        # one rsync command per path, ignore files vanished errors
        self.o_logger.info("pushing backups..")
        for s_backup_path in os.listdir(self.s_bck_path):
            s_backup_path = s_backup_path.strip()
            s_backup_path_fp = self.s_bck_path + s_backup_path
            self.o_logger.info("pushing : " + s_backup_path_fp + " to " + self.s_destination_path)
            #s_rsync_cmd = "rsync -av " + s_backup_path_fp + self.s_user + "@" + self.s_server + "::" + self.s_destination_path
            s_rsync_cmd = ["/usr/bin/rsync", "-av", s_backup_path_fp, self.s_destination_path]
            self.o_logger.info("with command : " + str(s_rsync_cmd))
            self.run_command(command=s_rsync_cmd)
