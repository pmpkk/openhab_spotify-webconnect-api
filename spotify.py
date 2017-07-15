#
# Use the Spotify Web Connect API using credentials auth code and tokens.
#

import json
import requests
import time
import urlparse
import sys
from myopenhab import openhab
from myopenhab import mapValues
from myopenhab import getJSONValue


#   API Gateway
ACCOUNT_URL = 'https://accounts.spotify.com/api/token'
API_ROOT_URL = 'https://api.spotify.com/v1/me/player/'
REDIRECT_URI = 'http://openhabianpi.local:8080/static/spotify-auth.html'

class spotify(object):
    """
    
    A wrapper for the Spotify Web Connect API

    https://developer.spotify.com/web-api/web-api-connect-endpoint-reference/

    """
    def __init__(self):

        self.debug = False 
        self.oh = openhab()

        self.client_id = self.oh.getState('spotify_client_id')
        self.client_secret = self.oh.getState('spotify_client_secret')

        self.access_token = self.oh.getState('spotify_access_token')
        self.refresh_token = self.oh.getState('spotify_refresh_token')
        self.token_issued = self.oh.getState('spotify_token_issued')
        self.token_expiry = self.oh.getState('spotify_token_expiry')

        if(self.token_expiry == "NULL"):
            self.refreshCredentials()
        if (self.access_token == "NULL"):
            self.generateCredentials()
        else:
            if (time.time() > float(self.token_expiry)):
                self.refreshCredentials()
      
    def generateCredentials(self):
        """
        Generate auth and refresh token for the very first time.
        """

        #   Send OAuth payload to get access_token
        payload = { 'code':self.oh.getState('spotify_auth_code'), 'client_id':self.client_id, 'client_secret':self.client_secret, 'redirect_uri':REDIRECT_URI, 'grant_type':'authorization_code' }
        
        print "-- Calling Token Service for the first time"

        try:
            r = requests.post(ACCOUNT_URL, data=payload, allow_redirects=False)

            if (self.debug): print r.headers
            if (self.debug): print r.json()
            if (self.debug): resp = r.json()

            if(r.status_code == 200):
                access_token = resp['access_token']
                refresh_token = resp['refresh_token']
                expires_in = resp['expires_in']

                #   Set and Save the access token
                self.access_token = access_token
                self.refresh_token = refresh_token
                self.token_expiry = time.time() + float(expires_in)
                self.token_issued = time.strftime("%Y-%m-%dT%H:%M:%S")
                self.saveCredentials()

        except:
            print " -> Error getting token:" + str(sys.exc_info()[1])

    def refreshCredentials(self):
        """
        If previous auth token expired, get a new one with refresh token.
        """

        #   Send OAuth payload to get access_token
        payload = { 'refresh_token':self.refresh_token, 'client_id':self.client_id, 'client_secret':self.client_secret, 'redirect_uri':REDIRECT_URI, 'grant_type':'refresh_token' }
        
        print "-- Calling Token Refresh Service"

        try:
            r = requests.post(ACCOUNT_URL, data=payload, allow_redirects=False)

            if (self.debug): print r.headers
            if (self.debug): print r.json()
            resp = r.json()

            if(r.status_code == 200):
                access_token = resp['access_token']
                expires_in = resp['expires_in']
                if('refresh_token' in resp): 
                    refresh_token = resp['refresh_token']
                    self.refresh_token = refresh_token

                #   Set and Save the access token
                self.access_token = access_token
                self.token_expiry = time.time() + float(expires_in)
                self.token_issued = time.strftime("%Y-%m-%dT%H:%M:%S")
                self.saveCredentials()

        except:
            print " -> Error refreshing token:" + str(sys.exc_info()[1])

    def saveCredentials(self):
        """
        Save current tokens to the openhab.
        """

        self.oh.sendCommand('spotify_access_token',self.access_token)
        self.oh.sendCommand('spotify_refresh_token',self.refresh_token)
        self.oh.sendCommand('spotify_token_expiry',self.token_expiry)
        self.oh.sendCommand('spotify_token_issued',self.token_issued)

    def call(self, path, mode=None, payload=None):
        """
        Call the API at the given path.
        """
        
        if (time.time() > self.token_expiry):
            self.refreshCredentials()
        headers = {"Authorization": "Bearer " + self.access_token}
        if mode == "POST":
            r = requests.post(API_ROOT_URL + path,  headers=headers, data=payload)
            return r.status_code
        elif mode == "PUT":
            r = requests.put(API_ROOT_URL + path,  headers=headers, data=payload)
            return r.status_code
        else:
            r = requests.get(API_ROOT_URL + path,  headers=headers)
            return r.json()

    def update(self):
        """
        Get a current player state.
        """
        print "-- Calling Service: Update"
        try:
            resp = self.call("")
            if (self.debug): print resp
            if ('item' in resp):

                self.oh.sendCommand('spotify_current_track', getJSONValue(resp, ['item','name']))
                self.oh.sendCommand('spotify_current_artist', getJSONValue(resp, ['item', 'artists', 0, 'name']))
                self.oh.sendCommand('spotify_current_cover', getJSONValue(resp, ['item', 'album', 'images', 1, 'url']))
                self.oh.sendCommand('spotify_current_duration', getJSONValue(resp, ['item', 'duration_ms']))
                self.oh.sendCommand('spotify_current_progress', getJSONValue(resp, ['progress_ms']))
                self.oh.sendCommand('spotify_current_progress', getJSONValue(resp, ['progress_ms']))
                self.oh.sendCommand('spotify_current_playing', mapValues(getJSONValue(resp, ['is_playing']), { 'True': 'ON', 'False': 'OFF' }))
                self.oh.sendCommand('spotify_current_device', getJSONValue(resp, ['device', 'name']))
                self.oh.sendCommand('spotify_current_volume', getJSONValue(resp, ['device', 'volume_percent']))
                self.oh.sendCommand('spotify_current_device_id', getJSONValue(resp, ['device', 'id']))

                print " -> Success"
            else:
                print " -> Item node missing from response :("
        except:
            print " -> Failure: ", sys.exc_info()[0]
            resp = ""

        return resp

    def volumeUp(self):
        """
        Volume up by 10%
        """
        print "-- Calling Service: Volume Up"
        try:
            vol = int(self.oh.getState('spotify_current_volume'))
            vol = int(round(vol/10)*10 + 10)
            if(vol>100): 
                vol = 100
            print " -> Volume To:" + str(vol)
            resp = self.call("volume?volume_percent=" + str(vol),"PUT" )
            self.oh.sendCommand('spotify_current_volume',vol)
            if (self.debug): print resp
        except:
            print " -> VolumeUp Failure: ", sys.exc_info()[0]
            resp = ""

        return resp

    def volumeDown(self):
        """
        Volume down by 10%
        """
        print "-- Calling Service: Volume Down"
        try:
            vol = int(self.oh.getState('spotify_current_volume'))
            vol = int(round(vol/10)*10 - 10)
            if(vol<0): 
                vol = 0
            print "Volume To:" + str(vol)
            resp = self.call("volume?volume_percent=" + str(vol),"PUT" )
            self.oh.sendCommand('spotify_current_volume',vol)
            if (self.debug): print resp
        except:
            print " -> VolumeDown Failure: ", sys.exc_info()[0]
            resp = ""

        return resp

    def pause(self):
        """
        Pause player
        """
        print "-- Calling Service: Pause"
        try:
            resp = self.call("pause","PUT")
            self.oh.sendCommand('spotify_current_playing',"OFF")
            if (self.debug): print resp
        except:
            print " -> Pause Failure: ", sys.exc_info()[0]
            resp = ""

        return resp    

    def play(self):
        """
        Resume player
        """
        print "-- Calling Service: Play"
        try:
            resp = self.call("play","PUT")
            self.oh.sendCommand('spotify_current_playing',"ON")
            if (self.debug): print resp
        except:
            print " -> Play Failure: ", sys.exc_info()[0]
            resp = ""

        return resp        

    def previous(self):
        """
        Skip to previous track
        """
        print "-- Calling Service: Previous"
        try:
            resp = self.call("previous","POST")
            if (self.debug): print resp
            self.refresh()  
        except:
            print " -> Previous Failure: ", sys.exc_info()[0]
            resp = ""

        return resp        

    def next(self):
        """
        Skip to next track
        """
        print "-- Calling Service: Next"
        try:
            resp = self.call("next","POST")
            if (self.debug): print resp
            self.refresh()
        except:
            print " -> Next Failure: ", sys.exc_info()[0]
            resp = ""

        return resp

    def updateConnectionDateTime(self):
        self.oh.sendCommand('spotify_lastConnectionDateTime',time.strftime("%Y-%m-%dT%H:%M:%S+0000",time.gmtime(time.time())))     

def main():

    t1 = time.time()

    c = spotify()

    args = sys.argv
    
    if(len(args) == 1):
        c.update()
    else:

        if(args[1] == "volume_up"):
            c.volumeUp()
        if(args[1] == "volume_down"):
            c.volumeDown()
        if(args[1] == "play"):
            c.play()
        if(args[1] == "pause"):
            c.pause()
        if(args[1] == "previous"):
            c.previous()
        if(args[1] == "next"):
            c.next()

    c.updateConnectionDateTime()

    t2 = time.time()
    print "Done in " + str(t2-t1) + " seconds"

if __name__ == '__main__':
    main()
