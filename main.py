# coding: utf-8
import argparse
import common.infradmin_logs
from Backups import backup_core
import time
"""
Lanceur 
"""

def main():
    """    Main function   """
    parser = argparse.ArgumentParser(description='Backup and Restore Utility')
    parser.add_argument('operation', choices=['backup', 'restore'], help='Specify whether to backup or restore')
    parser.add_argument('--restore-path', help='Path to restore the backup', required=False)
    parser.add_argument('--date', help='Date of the backup to restore', required=False)
    args = parser.parse_args()
    
    common.infradmin_logs.O_LOGGER = common.infradmin_logs.init_logging('Backup', False)
    common.infradmin_logs.O_LOGGER.info('Starting operation: ' + args.operation)
    
    start_time = time.time()
    
    if args.operation == 'backup':
        o_backup = backup_core.Backup()
        o_backup.backups()
        common.infradmin_logs.O_LOGGER.info('Backup finished')
        
    elif args.operation == 'restore':
        if args.restore_path is None:
            args.restore_path = '/usr/src/app/infradmin/restore/'
        o_backup = backup_core.Backup()
        if args.date is not None:
            o_backup.restore(args.restore_path, args.date)
        else:
            common.infradmin_logs.O_LOGGER.error('Backup date is required for restore operation')
            return
        common.infradmin_logs.O_LOGGER.info('Restore finished')
    
    end_time = time.time()
    duration = end_time - start_time
    common.infradmin_logs.O_LOGGER.info(f'Operation {args.operation} took {duration} seconds')

if __name__ == "__main__":
    main()

