import requests
import common.logging

def curl(methode, host, path, data):
    """ construction du curl """
    match methode:
        case "GET":
            o_curl = requests.get("http://"+host+":9200"+path)
        case "POST":
            o_curl = requests.post("http://"+host+":9200"+path, data=data)
        case "PUT":
            o_curl = requests.put("http://"+host+":9200"+path, data=data)
        case "DELETE":
            o_curl = requests.delete("http://"+host+":9200"+path)
    if o_curl.status_code == "200":
        common.logging.O_LOGGER.info('Demande de curl Ok '+o_curl.status_code)
        return True
    else:
        common.logging.O_LOGGER.error('Demande de curl KO '+o_curl.status_code+' --> '+o_curl.text)
        return False