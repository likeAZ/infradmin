# coding: utf-8
import common.logging
from Backups import backup_core
"""
Lanceur 
"""

def main():
    """    Main function   """
    common.logging.O_LOGGER = common.logging.init_logging('Backup', False)
    common.logging.O_LOGGER.info('Lancement du backup')
    backup_core.Backup(90, s_destination_path="/mnt/nas")


if __name__ == "__main__":
    main()

