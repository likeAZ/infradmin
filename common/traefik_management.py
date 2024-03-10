from common.tools import load_yaml
import os
import common.infradmin_logs


class Traefik:
    def __init__(self):
        self.o_logger = common.infradmin_logs.O_LOGGER
        self.d_dyn_conf = None
        self.d_static_conf = None

    def load_static_conf(self, s_path: str):
        self.d_static_conf = load_yaml(s_path)

    def load_dynamic_conf(self, s_dir_path: str):
        for s_dir_path, l_subdirectories, l_files in os.walk(s_dir_path):
            for s_file in l_files:
                s_dyn_file_fp = os.path.join(s_dir_path, s_file)
                self.d_dyn_conf.append(load_yaml(s_dyn_file_fp))

    def get_url(self, s_container_name):
        return s_url
