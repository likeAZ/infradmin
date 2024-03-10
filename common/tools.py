import yaml
import json
import common.infradmin_logs


def load_yaml(s_yaml_path):
    try:
        with open(s_yaml_path) as o_yaml_conf_file:
            d_yaml = yaml.safe_load(o_yaml_conf_file)
    except:
        common.infradmin_logs.O_LOGGER.warn('no file found')
    return d_yaml

def load_json(s_json_path):
    try:
        with open(s_json_path) as o_json_file:
            d_json = json.load(o_json_file)
    except:
        common.infradmin_logs.O_LOGGER.warn('no file found')
    return d_json

def write_json(s_json_path: str, d_data):
    try:
        with open(s_json_path, 'w') as json_file:
            json.dump(d_data, json_file)
        json_file.close()
    except:
        common.infradmin_logs.O_LOGGER.warn('no file wrote')
