# coding: utf-8
import argparse
import common.infradmin_logs
from Backups import backup_core
from Backups.backup_databases import DatabaseBackup
import time
import datetime
"""
Lanceur 
"""

def main():
    """    Main function   """
    parser = argparse.ArgumentParser(description='Backup and Restore Utility')
    parser.add_argument('operation', choices=['backup-databases'], help='Specify to backup databases')
    args = parser.parse_args()
    
    start_time = time.time()
    
    s_log_file_name = datetime.datetime.now().strftime('%Y-%m-%d') + '_backup'
    common.infradmin_logs.O_LOGGER = common.infradmin_logs.init_logging('Backup', False)
    common.infradmin_logs.O_LOGGER.info('Starting operation: ' + args.operation)
    
    if args.operation == 'backup-databases':
        o_database_backup = DatabaseBackup()
        o_database_backup.backup_databases()
        common.infradmin_logs.O_LOGGER.info('Database backup finished')
        
    # if args.operation == 'backup':
    #     o_backup = backup_core.Backup()
    #     o_backup.backups()
    #     common.infradmin_logs.O_LOGGER.info('Backup finished')
        
    # elif args.operation == 'restore':
    #     if args.restore_path is None:
    #         args.restore_path = '/usr/src/app/infradmin/restore/'
    #     o_backup = backup_core.Backup()
    #     if args.date is not None:
    #         o_backup.restore(args.restore_path, args.date)
    #     else:
    #         common.infradmin_logs.O_LOGGER.error('Backup date is required for restore operation')
    #         return
    #     common.infradmin_logs.O_LOGGER.info('Restore finished')
    
    end_time = time.time()
    s_duration = end_time - start_time
    
    s_hours, s_remainder = divmod(s_duration, 3600)
    s_minutes, s_seconds = divmod(s_remainder, 60)
    
    common.infradmin_logs.O_LOGGER.info(f'Operation {args.operation} took {s_hours} hours {s_minutes} minutes {s_seconds} seconds')

if __name__ == "__main__":
    main()

