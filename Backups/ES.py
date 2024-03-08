from ES.tools import curl
import datetime
import json

def creationSnapshot(host, urlPath):
    date=datetime.datetime.now()
    t_check_location = curl("GET", host, urlPath)
    parser=json.loads(t_check_location)
    if parser["bck"]["settings"]["location"] == "bck":
        urlPath += urlPath+"snapshot"+date.strftime("%Y%m%d-%H%M")
        data={"accepted": true}
        curl("PUT", host, urlPath, data)
