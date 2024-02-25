import json
import yaml
import os
import docker


class Compose:
    def __init__(self):
        self.s_app_dir = os.environ["APP_DIR"]
        self.s_compose_fp = self.s_app_dir + "conf/docker/docker-compose.yml"
        self.s_json_conf_fp = self.s_app_dir + "conf/containers.json"
        with open(self.s_compose_fp, 'r') as compose_file:
            self.d_compose = yaml.safe_load(compose_file)
        compose_file.close()

    def create_json_conf(self):
        d_json = []
        l_containers_name = self.get_containers_name()
        for s_container_name in l_containers_name:
            d_json[s_container_name] = {
                "l_volumes": self.get_volumes_for_container(s_container_name),
                "b_is_bdd": "False"
                }
        with open(self.s_json_conf_fp, 'w') as json_file:
            json.dump(d_json, json_file)
        json_file.close()

    def is_bdd(self):
        #//TODO

    def get_containers_name(self):
        l_container_name = []
        for containers in self.d_compose.items():
            l_container_name.append(containers[0])
        return l_container_name

    def get_volumes_for_container(self, s_container_name):
        l_volumes = self.d_compose['services'][s_container_name]['volumes'].values()
        return l_volumes


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
