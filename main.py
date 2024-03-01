# coding: utf-8
import common.infradmin_logs
from Backups import backup_core
"""
Lanceur 
"""

def main():
    """    Main function   """
    common.infradmin_logs.O_LOGGER = common.infradmin_logs.init_logging('Backup', False)
    common.infradmin_logs.O_LOGGER.info('Lancement du backup')
    o_backup = backup_core.Backup(90)
    o_backup.backups()


if __name__ == "__main__":
    main()

