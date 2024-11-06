from os import environ
import docker
from common.tools import load_yaml, write_json
import common.infradmin_logs
import common.traefik_management


class Compose:
    def __init__(self):
        self.o_logger = common.infradmin_logs.O_LOGGER
        self.s_app_dir = environ["APP_DIR"]
        self.s_compose_fp = self.s_app_dir + "conf/docker/docker-compose.yml"
        self.s_json_conf_fp = self.s_app_dir + "data/containers.json"
        self.d_compose = load_yaml(self.s_compose_fp)

    def create_json_conf(self):
        d_json = []
        l_containers_name = self.get_containers_name()
        for s_container_name in l_containers_name:
            d_json[s_container_name] = {
                "l_volumes": self.get_volumes_for_container(s_container_name),
                "b_is_bdd": self.is_bdd(),
                "url": self.get_external_url(s_container_name)
                }
        write_json(self.s_json_conf_fp, d_json)

    def is_bdd(self):
        return False

    def get_external_url(self, s_container_name: str):
        o_traefik = common.traefik_management.Traefik()
        return  o_traefik.get_url(s_container_name)

    def get_containers_name(self) -> list:
        l_container_name = []
        for containers in self.d_compose.items():
            l_container_name.append(containers[0])
        return l_container_name

    def get_volumes_for_container(self, s_container_name):
        l_volumes = self.d_compose['services'][s_container_name]['volumes'].values()
        return l_volumes


class Docker:
    def __init__(self):
        self.o_logger = common.infradmin_logs.O_LOGGER
        self.o_docker = docker.from_env()

    def get_containers_name(self) -> list:
        """
        Get all containers name
        :return: list of containers name
        """
        l_containers_id = self.list_stopped_and_running_containers()
        l_containers_name = []
        for s_container_id in l_containers_id:
            s_container_name = self.from_id_to_name(s_container_id)
            l_containers_name.append(s_container_name)
        return l_containers_name
    
    def get_database_containers_name(self) -> list:
        """
        Get all containers name which are databases
        :return: list of containers name
        """
        l_containers_name = self.get_containers_name()
        l_database_containers_name = []
        for s_container_name in l_containers_name:
            if self.is_bdd(s_container_name):
                l_database_containers_name.append(s_container_name)
        return l_database_containers_name
    
    def get_database_type(self, s_container_name: str) -> str:
        """
        Get the type of the database
        :param s_container_name: container name
        :return: type of the database
        """
        l_labels = self.get_labels_from_container(s_container_name)
        if 'infradmin.database_type' in l_labels:
            return l_labels['infradmin.database_type']
        else:
            return 'unknown'
    
    def is_bdd(self, s_container_name: str) -> bool:
        """
        Check if a container is a database
        :param s_container_name: container name
        :return: True if it is a database, False otherwise
        """
        l_labels = self.get_labels_from_container(s_container_name)
        if 'infradmin.is_bdd' in l_labels and l_labels['infradmin.is_bdd'] == 'true':
            return True
        else:
            return False
        
    def is_container_exist(self, s_container_name: str) -> bool:
        """
        Check if a container exist
        :param s_container_name: container name
        :return: True if the container exist, False otherwise
        """
        l_containers_name = self.get_containers_name()
        if s_container_name in l_containers_name:
            return True
        else:
            return False
    
    def get_own_container_volume_source(self, ) -> str:
        """
        Get the path of the volume of the container
        :return: path of the volume
        """
        s_own_container_id = self.o_docker.containers.get(environ["HOSTNAME"]).id
        l_own_container_volumes = self.get_volumes_for_container(s_own_container_id)
        for s_own_container_volume in l_own_container_volumes:
            if s_own_container_volume.split(':')[1] == '/usr/src/app/infradmin/data/':
                s_own_container_volume_source = s_own_container_volume.split(':')[0]
        return s_own_container_volume_source
    
    def get_volumes_for_container(self, s_container_name: str) -> list:
        """
        Get all volumes for a container
        :param s_container_name: container name
        :return: list of volumes
        """
        l_volumes = self.o_docker.containers.get(s_container_name).attrs['HostConfig']['Binds']
        return l_volumes
    
    def list_running_containers(self):
        return self.o_docker.containers.list()

    def list_stopped_and_running_containers(self):
        return self.o_docker.containers.list(all=True)

    def from_id_to_name(self, s_id):
        o_container = self.o_docker.containers.get(s_id)
        s_container_name = o_container.name
        return s_container_name

    def from_name_to_id(self, s_name: str)-> str:
        o_container = self.o_docker.containers.get(s_name)
        s_container_id = o_container.id
        return s_container_id

    def exec_command(self, s_container_id: str, s_command: str, s_user: str = None):
        exec_create_params = {
        'container': s_container_id,
        'cmd': s_command,
        'tty': False,  # Enable TTY if you want interactive mode
        }
        if s_user is not None:
            exec_create_params['user'] = s_user

        l_response = self.o_docker.api.exec_create(**exec_create_params)
        s_output = self.o_docker.api.exec_start(exec_id=l_response['Id'])
        self.o_logger.info('command returned : ' + s_output.decode('utf-8'))

    def get_labels_from_container(self, s_container_name: str) -> list:
        o_container = self.o_docker.containers.get(s_container_name)
        l_labels = o_container.labels
        return l_labels

    def get_all_containers_labels(self):
        d_ret = {}
        o_compose = Compose()
        l_containers = o_compose.get_containers_name()
        i_nb_containers = len(l_containers)
        for i in range(i_nb_containers):
            l_labels = self.get_labels_from_container(l_containers[i])
            d_ret[i] = {
                l_containers[i]: l_labels
            }
        return d_ret

