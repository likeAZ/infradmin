# Local lib
from common.tools import load_yaml
from common.containers import Docker
import common.infradmin_logs
# Python lib
import datetime
import time
import os


class DatabaseBackup:

    def __init__(self):
        """
        Init DatabaseBackup class
        """
        self.o_docker = Docker()
        # Init path
        self.s_databases_conf = "/usr/src/app/infradmin/conf/backup/databases.yaml"
        self.s_date_format = "%Y%m%d%H%M%S"

        # Init functions
        self.o_now = datetime.datetime.now()
        self.o_logger = common.infradmin_logs.O_LOGGER

        # Init vars
        self.d_yaml_databases = []


    def get_databases_conf_from_file(self):
        """
        Load yaml file : /usr/src/app/infradmin/conf/backup/databases.yaml
        """
        self.o_logger.info(f"getting info from conf file {self.s_databases_conf}")
        self.d_yaml_databases = load_yaml(self.s_databases_conf)
       

    def map_volume_path(self, s_volume_to_map: str) -> str:
        """
        Map a volume path to the host path.
        
        :param volume_to_map: Volume path to map.
        :return: Mapped volume path.
        """
        return s_volume_to_map.replace(self.o_docker.get_own_container_volume_source(), '/usr/src/app/infradmin/data/')

    def backup_databases(self):
        """
        Backup all configured databases
        """
        self.o_logger.info("backuping databases ...")
        self.get_databases_conf_from_file()
        l_databases_container_name = self.o_docker.get_database_containers_name()
        for s_database_container_name in l_databases_container_name:
            s_database_backup_volume = self.d_yaml_databases[s_database_container_name]['backup_volume']
            s_backup_path_container_side = s_database_backup_volume.split(":")[1]
            s_backup_path_host_side = s_database_backup_volume.split(":")[0]
            
            if os.path.exists(self.map_volume_path(s_backup_path_host_side)):
                if os.listdir(self.map_volume_path(s_backup_path_host_side)):
                    self.o_logger.info("Deleting old database dumps")
                    for s_file in os.listdir(self.map_volume_path(s_backup_path_host_side)):
                        self.o_logger.info(f"Deleting {s_file}")
                        os.remove(os.path.join(self.map_volume_path(s_backup_path_host_side), s_file))
                else:
                    self.o_logger.info("No old database dumps to delete")
            else:
                self.o_logger.info(f"Directory {self.map_volume_path(s_backup_path_host_side)} does not exist")
            
            app_entry = self.d_yaml_databases.get(s_database_container_name, {}).get('app')
            
            # Ensure app_entry is a list, even if it's a single string
            app_names = app_entry if isinstance(app_entry, list) else [app_entry]

            previous_states = {}

            for app_name in app_names:
                if not app_name:
                    continue  # skip None or empty values
                
                # Stopping App before backuping databases
                if self.o_docker.is_container_exist(app_name):
                    if app_name == 'nextcloud':
                        self.o_logger.info(f"Putting {app_name} in maintenance mode")
                        self.o_docker.exec_command(self.o_docker.from_name_to_id(app_name), "php occ maintenance:mode --on", "www-data")
                    else:
                        state = self.o_docker.get_current_container_state(app_name)
                        previous_states[app_name] = state
                        if state == 'running':
                            self.o_logger.info(f"Stopping app container: {app_name}")
                            self.o_docker.stop_container(app_name)


            
            s_type = self.o_docker.get_database_type(s_database_container_name)
            self.o_logger.info(f"Backing up {s_database_container_name} of type {s_type}")
            
            self._backup_database_by_type(s_database_container_name, s_type, s_backup_path_container_side, s_backup_path_host_side)

            for app_name in app_names:
                if not app_name:
                    continue  # skip None or empty values

                if self.o_docker.is_container_exist(app_name):
                    previous_state = previous_states.get(app_name)

                    if app_name == 'nextcloud':
                        self.o_logger.info(f"Disabling maintenance mode for {app_name}")
                        self.o_docker.exec_command(self.o_docker.from_name_to_id(app_name), "php occ maintenance:mode --off", "www-data")
                    else:
                        if previous_state == 'running':
                            self.o_logger.info(f"Starting back app container: {app_name}")
                            self.o_docker.start_container(app_name)


    def _backup_database_by_type(self, s_database_container_name: str, s_type: str, s_backup_path_container_side: str, s_backup_path_host_side: str):
        """
        Backup a database based on its type
        
        :param s_database_container_name: Name of the database container
        :param s_type: Type of the database (mariadb, postgresql, unknown)
        :param s_backup_path_container_side: Backup path inside the container
        :param s_backup_path_host_side: Backup path on the host
        """
        match s_type:
            case 'mariadb':
                self._backup_mariadb(s_database_container_name, s_backup_path_container_side, s_backup_path_host_side)
                        
            case 'postgresql':
                self._backup_postgresql(s_database_container_name, s_backup_path_container_side, s_backup_path_host_side)
                        
            case 'unknown':
                self.o_logger.info(f"{s_type} is not supported skipping")

    def _backup_mariadb(self, s_database_container_name: str, s_backup_path_container_side: str, s_backup_path_host_side: str):
        """
        Backup a MariaDB database
        
        :param s_database_container_name: Name of the database container
        :param s_backup_path_container_side: Backup path inside the container
        :param s_backup_path_host_side: Backup path on the host
        """
        s_previous_backup_state = self.o_docker.get_current_container_state(s_database_container_name)
        if not s_previous_backup_state == 'running':
            self.o_docker.start_container(s_database_container_name)
            self.o_logger.info(f"Wainting for {s_database_container_name} to be started")
            time.sleep(10)
        
        s_backup_cmd = f"/bin/sh -c 'exec /usr/bin/mariadb-dump -u root -p$MARIADB_ROOT_PASSWORD --all-databases > {s_backup_path_container_side}{datetime.datetime.now().strftime(self.s_date_format)}-backup.sql'"
        self.o_docker.exec_command(self.o_docker.from_name_to_id(s_database_container_name), s_backup_cmd)

        self.o_logger.info(f"{s_database_container_name} backuped in {self.map_volume_path(s_backup_path_host_side)}")

        if s_previous_backup_state == 'exited':
            self.o_logger.info(f"Returning {s_database_container_name} to previous state")
            self.o_docker.stop_container(s_database_container_name)

    def _backup_postgresql(self, s_database_container_name: str, s_backup_path_container_side: str, s_backup_path_host_side: str):
        """
        Backup a PostgreSQL database
        
        :param s_database_container_name: Name of the database container
        :param s_backup_path_container_side: Backup path inside the container
        :param s_backup_path_host_side: Backup path on the host
        """
        s_previous_backup_state = self.o_docker.get_current_container_state(s_database_container_name)
        if not s_previous_backup_state == 'running':
            self.o_docker.start_container(s_database_container_name)
            self.o_logger.info(f"Wainting for {s_database_container_name} to be started")
            time.sleep(10)
        
        container = self.o_docker.get_a_container(s_database_container_name)
        env_vars = container.attrs['Config']['Env']
        postgres_user_exists = any(env_var.startswith("POSTGRES_USER=") for env_var in env_vars)

        if postgres_user_exists:
            s_backup_cmd = f"/bin/sh -c '/usr/local/bin/pg_dumpall -U $POSTGRES_USER > {s_backup_path_container_side}{datetime.datetime.now().strftime(self.s_date_format)}-backup.sql'"
            self.o_docker.exec_command(self.o_docker.from_name_to_id(s_database_container_name), s_backup_cmd)
        else:
            s_backup_cmd = f"/bin/sh -c '/usr/local/bin/pg_dumpall -U postgres > {s_backup_path_container_side}{datetime.datetime.now().strftime(self.s_date_format)}-backup.sql'"
            self.o_docker.exec_command(self.o_docker.from_name_to_id(s_database_container_name), s_backup_cmd)

        self.o_logger.info(f"{s_database_container_name} backuped in {self.map_volume_path(s_backup_path_host_side)}")
        
        if s_previous_backup_state == 'exited':
            self.o_logger.info(f"Returning {s_database_container_name} to previous state")
            self.o_docker.stop_container(s_database_container_name)