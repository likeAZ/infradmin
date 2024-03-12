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

    def list_running_containers(self):
        return self.o_docker.containers.list()

    def list_stopped_and_running_containers(self):
        return self.o_docker.containers.list(all=True)

    def from_id_to_name(self, s_id):
        o_container = self.o_docker.containers.get(s_id)
        s_container_name = o_container.name
        return s_container_name

    def exec_command(self, s_container_id: str, s_command: str):
        l_response = self.o_docker.containers.exec_create(container=s_container_id, cmd=s_command)
        s_output = self.o_docker.containers.exec_start(exec_id=l_response['Id'])
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

