# coding: utf-8
import common.logging
"""
Lanceur 
"""

def main():
    """    Main function   """
    # comment il definie le logger :
    common.logging.O_LOGGER = common.logging.init_logging('testlogin', False)
    common.logging.O_LOGGER.info('Lancement du script test')
    

if __name__ == "__main__":
    main()

