from os import environ
import docker
import common.infradmin_logs
import common.traefik_management

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
        for o_container in l_containers_id:
            l_containers_name.append(o_container.name)
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
        o_own_container = self.o_docker.containers.get(environ["HOSTNAME"])
        l_own_container_volumes = self.get_volumes_for_container(o_own_container.name)
        self.o_logger.info(f'volumes for {o_own_container.name} are : {l_own_container_volumes}')
        s_own_container_volume_source = None
        for s_own_container_volume in l_own_container_volumes:
            if s_own_container_volume.split(':')[1] == '/usr/src/app/infradmin/data':
                s_own_container_volume_source = s_own_container_volume.split(':')[0]
                break
        if s_own_container_volume_source is None:
            self.o_logger.error("Volume source for /usr/src/app/infradmin/data/ not found")
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

        self.o_logger.info(f'executing command : {s_command} on container {self.from_id_to_name(s_container_id)}')
        self.o_logger.info(f'exec_create_params : {exec_create_params}')
        l_response = self.o_docker.api.exec_create(**exec_create_params)
        s_output = self.o_docker.api.exec_start(exec_id=l_response['Id'])
        self.o_logger.info('command returned : ' + s_output.decode('utf-8'))

    def get_labels_from_container(self, s_container_name: str) -> list:
        o_container = self.o_docker.containers.get(s_container_name)
        l_labels = o_container.labels
        return l_labels


