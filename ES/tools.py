import requests
import common.infradmin_logs

def curl(methode, host, urlPath, data):
    """ construction du curl """
    match methode:
        case "GET":
            o_curl = requests.get("http://"+host+":9200"+urlPath)
        case "POST":
            o_curl = requests.post("http://"+host+":9200"+urlPath, data=data)
        case "PUT":
            o_curl = requests.put("http://"+host+":9200"+urlPath, data=data)
        case "DELETE":
            o_curl = requests.delete("http://"+host+":9200"+urlPath)
    if o_curl.status_code == "200":
        common.logging.O_LOGGER.info('Demande de curl Ok '+o_curl.status_code)
        return o_curl.json
    else:
        common.logging.O_LOGGER.error('Demande de curl KO '+o_curl.status_code+' --> '+o_curl.text)
        return o_curl.text