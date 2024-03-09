# coding: utf-8
import common.infradmin_logs
from Backups import backup_core
import requests
from common.tools import load_yaml
"""
Lanceur 
"""

def main():
    """    Main function   """
    common.infradmin_logs.O_LOGGER = common.infradmin_logs.init_logging('Backup', False)
    common.infradmin_logs.O_LOGGER.info('Starting backup')
    d_yaml = load_yaml("/usr/src/app/infradmin/conf/config.yaml")
    if d_yaml['healthcheck']['is_active']:
        s_healthchack_url = d_yaml['healthcheck']['url']
        requests.get(s_healthchack_url + '/start')
        common.infradmin_logs.O_LOGGER.info('Making request to : ' + s_healthchack_url + '/start')
        o_backup = backup_core.Backup()
        o_backup.backups()
        requests.get(s_healthchack_url)
        common.infradmin_logs.O_LOGGER.info('Making request to : ' + s_healthchack_url)
        common.infradmin_logs.O_LOGGER.info('Backup finished')
    else:
        o_backup = backup_core.Backup()
        o_backup.backups()
        common.infradmin_logs.O_LOGGER.info('Backup finished')


if __name__ == "__main__":
    main()

