import logging
import logging.handlers
import sys
import os


O_LOGGER = None
B_ACTIVATE_DEBUG = False

def get_log_file_fp(s_suffixe='.log', s_file='other'):
    s_ret = "/var/log/app"
    s_ret += "/" + s_file
    s_ret += s_suffixe
    return s_ret

def create_log_directory_fp():
    try: 
        os.makedirs("/var/log/app", exist_ok = True) 
        print("Directory '%s' created successfully") 
    except OSError as error: 
        print("Directory '%s' can not be created") 

def init_logging(s_conf_file_name='other', b_debug=False):
    """
    Init log files, streams ..... and format
    """
    global B_ACTIVATE_DEBUG
    B_ACTIVATE_DEBUG = b_debug
    # Logging config
    print("####################################################################")
    print("####################################################################")
    print("#                                                                  #")
    print("#                            INFRADMIN                             #")
    print("#                                                                  #")
    print("#                INITIALISATION LOGGING DU SCRIPT                  #")
    print("#                                                                  #")
    if b_debug:
        print("#                         DEBUG ACTIVE                             #")
    else:
        print("#                       DEBUG NON ACTIVE                           #")
    # endif
    print("#                                                                  #")
    print("####################################################################")

    o_logger = logging.getLogger(s_conf_file_name)
    o_logger.setLevel(logging.DEBUG)
    #
    formatter_info = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
    formatter_debug = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
    #
    create_log_directory_fp()
    #
    s_fp_log_error = get_log_file_fp('.error.log', s_conf_file_name)
    print("#  error log : " + s_fp_log_error)
    file_handler_error = logging.handlers.RotatingFileHandler(s_fp_log_error, mode="a", maxBytes=100*1024*1024, backupCount=3, encoding="utf-8")
    file_handler_error.setLevel(logging.WARNING)
    file_handler_error.setFormatter(formatter_info)
    o_logger.addHandler(file_handler_error)
    #
    s_fp_log_info = get_log_file_fp('.info.log', s_conf_file_name)
    print("#  info log : " + s_fp_log_info)
    file_handler_info = logging.handlers.RotatingFileHandler(s_fp_log_info, mode="a", maxBytes=100*1024*1024, backupCount=3, encoding="utf-8")
    file_handler_info.setLevel(logging.INFO)
    file_handler_info.setFormatter(formatter_info)
    o_logger.addHandler(file_handler_info)
    #
    if b_debug:
        s_fp_log_debug = get_log_file_fp('.debug.log', s_conf_file_name)
        print("#  debug log : " + s_fp_log_debug)
        file_handler_debug = logging.handlers.RotatingFileHandler(s_fp_log_debug, mode="a", maxBytes=100*1024*1024, backupCount=3, encoding="utf-8")
        file_handler_debug.setLevel(logging.DEBUG)
        file_handler_debug.setFormatter(formatter_debug)
        o_logger.addHandler(file_handler_debug)
    # endif
    print("#                                                                  #")
    print("####################################################################")
    print("####################################################################")
    #
    stream_handler_stdout = logging.StreamHandler(sys.stdout)
    stream_handler_stdout.setLevel(logging.INFO)
    stream_handler_stdout.setFormatter(formatter_info)
    o_logger.addHandler(stream_handler_stdout)
    #
    o_logger.info("INITIALISATION D'UNE SESSION DE LOGGING ( LANCEMENT D'UN PROCESS ) s_logger=" + s_conf_file_name)
    #
    return o_logger
