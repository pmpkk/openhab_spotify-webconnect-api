

import sys
import json
import requests
import time
import urlparse
import sys


def batteryLevel( level ):
    "This returns a string value for a battery level"
    l = 'empty'

    try:
        v = float(level)
    except:
        v = 0

    if (v < 5):
        l = 'empty'
    elif (v < 20):
        l = 'low'
    elif (v < 90):
        l = 'medium'
    elif (v < 100):
        l = 'high'
    else:
        l = 'full'

    return l


def mapValues(k, map):
    v = "unkown"
    if(str(k) in map):
        v = map[str(k)]
    return v


def getJSONValue(obj, path):
	pathOK = True
	subObj = obj
	v = ""
	try:
		for k in path:
			if(isinstance(k, basestring)):
				if(str(k) in subObj):
					subObj = subObj[k]
					v = subObj
				else:
					pathOK = False
					break
			else:
				subObj = subObj[k]
				v = subObj
	except:
		pathOK = False

	if (pathOK):
		return v
	else:
		return None


class openhab(object):
    """
    A wrapper for the OpenHab REST API.

    """

    def __init__(self):

    	self.openhab_ip = "127.0.0.1:8080"
      
    def sendCommand(self, item, state):
        """
        Update State from Item
        """

        try:
            if (isinstance(state, basestring)):
                s = state.encode('utf-8')
            elif (state is None):
                s = "NULL"
            else:
                s = str(state)
            r = requests.put('http://' + str(self.openhab_ip) + '/rest/items/' + item + '/state', s)        	    	
            if(r.status_code == 202):
                print "Successfully posted state to OpenHab: \033[0;37m" + str(item) + " \033[0m= \033[0;36m" + s + "\033[0m"
            elif(r.status_code == 400):
                print "Error posting state to OpenHab: \033[0;31m" + str(item) + " (HTTP Response " + str(r.json()['error']['message']) + ")\033[0m"
            else:
                print "Error posting state to OpenHab: \033[0;31m" + str(item) + " (HTTP Response " + str(r.status_code) + ")\033[0m"
        except:
            print "OpenHab: \033[0;31mError posting state:" + str(sys.exc_info()[1]) + "\033[0m"


    def getState(self, item):
        """
        Get State for Item
        """

        try:
            r = requests.get('http://' + str(self.openhab_ip) + '/rest/items/' + item + '/state')
            if(r.status_code == 200):
                print "Successfully got state from OpenHab: \033[0;37m" + str(item) + "\033[0m"
                state = str(r.content)
                if (state == ""): 
                    state = "NULL"
                return state
            elif(r.status_code == 400):
                print "Error posting state to OpenHab: \033[0;31m" + str(item) + " (HTTP Response " + str(r.json()['error']['message']) + ")\033[0m"
            else:
                print "Error getting state from OpenHab: \033[0;31m" + str(item) + " (HTTP Response " + str(r.status_code) + ")\033[0m"
            return ""
        except:
            print "OpenHab: \033[0;31mError getting state:" + str(sys.exc_info()[1]) + "\033[0m"





