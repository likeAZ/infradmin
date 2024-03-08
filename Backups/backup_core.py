import datetime
import yaml
import subprocess
import os
import tarfile
import common.infradmin_logs
import common.sftp


class Backup:

    def __init__(self, i_keep=90):
        #with open("/usr/src/app/infradmin/conf/containers.json", 'r') as fp:
        #    self.d_json_conf = json.load(fp)
        #fp.close()
        self.i_keep = i_keep
        self.s_conf_file = "/usr/src/app/infradmin/conf/backup/backup.yaml"
        self.s_exclude_conf = "/usr/src/app/infradmin/conf/backup/exclude.yaml"
        self.s_bck_path = "/usr/src/app/infradmin/backup/"
        self.s_source_data = "/usr/src/app/infradmin/data/"
        self.s_date_format = "%Y%m%d%H%M%S"
        self.o_now = datetime.datetime.now()
        self.o_logger = common.infradmin_logs.O_LOGGER
        self.l_files_to_backup_fp = []
        self.l_backup_name = []
        self.d_yaml = []
        self.s_backup_filename = None

    def run_command(self, command=None):
        result = subprocess.call(command, shell=False)

    def backups(self):
        self.get_info_from_conf()
        self.do_backup()
        for s_backup_name in self.l_backup_name:
            self.o_logger.info(f"For {s_backup_name}")
            s_backup_type = self.d_yaml[s_backup_name]['type']
            match s_backup_type:
                case 'local':
                    self.rotate_local(self.get_retention(s_backup_name), self.s_bck_path)
                case 'mount':
                    s_remote_backup_path = self.get_backup_path_from_file(s_backup_name)
                    self.copy_backups(s_backup_type, s_remote_backup_path)
                    self.rotate_local(self.get_retention(s_backup_name), s_remote_backup_path)
                case 'sftp':
                    s_hostname = self.d_yaml[s_backup_name]['hostname']
                    s_username = self.d_yaml[s_backup_name]['user']
                    s_password = self.d_yaml[s_backup_name]['password']
                    i_port = self.d_yaml[s_backup_name]['port']
                    i_keep = self.get_retention(s_backup_name)
                    s_remote_backup_path = os.path.join(self.get_backup_path_from_file(s_backup_name), self.s_backup_filename)
                    o_sftp = common.sftp.Sftp(s_hostname, s_username, s_password, i_port)
                    o_sftp.connect()
                    self.copy_backups(s_backup_type, s_remote_backup_path, o_sftp)
                    l_present_backup = o_sftp.listdir(self.get_backup_path_from_file(s_backup_name))
                    l_backup_to_delete = self.delta_from_list(i_keep, l_present_backup)
                    self.o_logger.info(f"deleting files older than : {str(i_keep)} days in {s_remote_backup_path}")
                    for s_backup_to_delete in l_backup_to_delete:
                        o_sftp.delete(s_remote_backup_path + s_backup_to_delete)
                    o_sftp.disconnect()



    def get_info_from_conf(self):
        self.o_logger.info(f"getting info from conf file {self.s_conf_file}")
        with open(self.s_conf_file) as o_yaml_conf_file:
            self.d_yaml = yaml.safe_load(o_yaml_conf_file)
        self.l_backup_name = list(self.d_yaml.keys())
        o_yaml_conf_file.close()

    def get_exclude_list(self):
        with open(self.s_exclude_conf) as exclude_file:
            o_exclude_file = yaml.safe_load(exclude_file)
        l_exclude = o_exclude_file.get('exclude')
        self.o_logger.info("exclude list for is :")
        for s_exclude_dir in l_exclude:
            self.o_logger.info(s_exclude_dir)
        exclude_file.close()
        return l_exclude

    def is_local(self, s_backup_name):
        b_is_local = False
        if self.d_yaml[s_backup_name]['type'] == 'local':
            b_is_local = True
        return b_is_local

    def get_retention(self, s_backup_name):
        return self.d_yaml[s_backup_name]['keep']

    def get_backup_path_from_file(self, s_backup_name):
        return self.d_yaml[s_backup_name]['backup_path']

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
        self.o_logger.info("Backup finished")


    def rotate_local(self, i_keep, s_rotate_path):
        self.o_logger.info(f"deleting backups older than : {str(i_keep)} days in {s_rotate_path}")
        for s_dir_backup in os.listdir(s_rotate_path):
            s_date_backup = s_dir_backup[:10]
            o_date_backup = datetime.datetime.strptime(s_date_backup, self.s_date_format[:8])
            i_date_delta = int((self.o_now - o_date_backup).days)
            if i_date_delta >= i_keep:
                self.o_logger.info(f"deleting {s_dir_backup}")
                os.remove(s_rotate_path + s_dir_backup)

    def delta_from_list(self, i_keep, l_backups):
        l_backups_to_delete = []
        for s_dir_backup in l_backups:
            s_date_backup = s_dir_backup[:10]
            o_date_backup = datetime.datetime.strptime(s_date_backup, self.s_date_format[:8])
            i_date_delta = int((self.o_now - o_date_backup).days)
            if i_date_delta >= i_keep:
                l_backups_to_delete.append(s_dir_backup)
        return l_backups_to_delete

    def copy_backups(self, s_type, s_remote_backup_path, o_sftp=None):
        # one rsync command per path, ignore files vanished errors
        self.o_logger.info("pushing backups...")
        s_backup_path_fp = self.s_bck_path + self.s_backup_filename
        match s_type:
            case 'mount':
                s_rsync_cmd = [
                    "/usr/bin/rsync",
                    "-av",
                    s_backup_path_fp,
                    s_remote_backup_path
                ]
                self.o_logger.info("with command : " + str(s_rsync_cmd))
                self.run_command(command=s_rsync_cmd)
            case 'sftp':
                self.o_logger.info("upload data to a sftp server")
                o_sftp.upload(s_backup_path_fp, s_remote_backup_path)
