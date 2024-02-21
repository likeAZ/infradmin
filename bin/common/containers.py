import yaml
import os
import docker


class Compose:
    def __init__(self):
        self.s_app_dir = os.environ["APP_DIR"]
        self.s_compose_fp = self.s_app_dir + "conf/docker/docker-compose.yml"
        with open(self.s_compose_fp, 'r') as compose_file:
            self.d_compose = yaml.safe_load(compose_file)

    def get_containers_name(self):
        l_container_name = []
        for containers in self.d_compose.items():
            l_container_name.append(containers[0])
        return l_container_name

    def get_volumes_for_container(self, s_container_name):
        return self.d_compose['services'][s_container_name]['volumes'].values()


class Docker:
    def __init__(self):
        self.o_docker = docker.from_env()

    def list_running_containers(self):
        return self.o_docker.containers.list()

    def list_stopped_and_running_containers(self):
        return self.o_docker.containers.list(all=True)

    def from_id_to_name(self, s_id):
        o_container = self.o_docker.containers.get(s_id)
        s_container_name = o_container.name
        return s_container_name
