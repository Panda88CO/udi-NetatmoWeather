#!/usr/bin/env python3

import requests
import time
import json

#from threading import Lock
#from  datetime import datetime
#try:
#    import udi_interface
#    logging = udi_interface.LOGGER
#    Custom = udi_interface.Custom
#except ImportError:
import logging
logging.basicConfig(level=logging.DEBUG)

import time
from requests_oauth2 import OAuth2BearerToken

'''
class netatmoCloudApi(object):

    def __init__(self, refreshToken):
        logging.debug('netatmoCloudApi')
        self.tokenInfo = None
        self.Rtoken = refreshToken
        self.tokenExpMargin = 600 #10min
        self.netatmo_URL = "https://api.netatmo.com"
        self.AUTHORIZE = "/oauth2/authorize?"
        self.TOKEN ="/oauth2/token"
        self.Header= {'Accept':'application/json'}

        self.cookies = None
        self.data = {}
        
        self.tokenInfo = self.netatmo_refresh_token()



    def isNodeServerUp(self):
        return( self.tokenInfo != None)


    def isConnectedToNetatmo(self):
        return( self.tokenInfo != None)     

    def netatmoCloudConnect(self ):
        logging.debug('netatmoCloudConnect')
        self.tokenInfo = self.netatmo_refresh_token( )
        return(self.tokenInfo)


    def __netatmoGetToken(self):
        if self.tokenInfo:
            dateNow = time.time()
            tokenExpires = self.tokenInfo['created_at'] + self.tokenInfo['expires_in']-self.tokenExpMargin
            if dateNow > tokenExpires:
                logging.info('Renewing token')
                self.tokenInfo = self.netatmo_refresh_token()
        else:
            logging.error('New Refresh Token required - please generate  New Token')

        return(self.tokenInfo)


    def netatmoConnect(self):
        return(self.__netatmoGetToken())


    def netatmoGetProduct(self):
        S = self.__netatmoConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])
                r = s.get(self.netatmo_URL + self.API + "/products",  headers=self.Header)
                products = r.json()
                return(products)        
            except Exception as e:
                logging.debug('Exception netatmoGetProduct: '+ str(e))
                logging.error('Error getting product info')
                return(None)


    def getRtoken(self):
        return(self.Rtoken)

    def netatmo_refresh_token(self):
        dateNow = int(time.time())
        S = {}
        if self.Rtoken:
            data = {}
            data['grant_type'] = 'refresh_token'
            data['client_id'] = 'ownerapi'
            data['client_secret'] = 'ownerapi'
            
            data['refresh_token']=self.Rtoken
            data['scope']='openid email offline_access'      
            resp = requests.post('https://auth.netatmo.com/oauth2/v3/token', headers= self.Header, data=data)
            S = json.loads(resp.text)
            S['created_at'] = dateNow
            if 'refresh_token' in S:
                self.Rtoken = S['refresh_token']
                #S['created_at'] = dateNow
                #dataFile = open('./refreshToken.txt', 'w')
                #dataFile.write( self.Rtoken)
                #dataFile.close()



            data = {}
            data['grant_type'] = 'urn:ietf:params:oauth:grant-type:jwt-bearer'
            data['client_id']=self.CLIENT_ID
            data['client_secret']=self.CLIENT_SECRET
            logging.info('netatmo_refresh_token Rtoken : {}'.format(self.Rtoken ))

            with requests.Session() as s:
                try:
                    s.auth = OAuth2BearerToken(S['access_token'])
                    r = s.post(self.netatmo_URL + '/oauth/token',data)
                    S = json.loads(r.text)
                    
                    dataFile = open('./refreshToken.txt', 'w')
                    dataFile.write( self.Rtoken)
                    dataFile.close()
                    self.tokenInfo = S

                except  Exception as e:
                    logging.error('Exception __netatmo_refersh_token: ' + str(e))
                    logging.error('New Refresh Token must be generated')
                    self.Rtoken = None
                    pass
            time.sleep(1)

        #logging.debug('netatmo_refresh_token: {}'.format(S))
        return S

'''
        
clientID = "65177da9bb1985366904e2ec"
clientSecret = "vQ5C1NyOUw26JJnXfNGWrC5SZdjz4clTBgOJZp1SxWgvt"
scopeList = ['read_station', 'read_magellan', 'write_magellan', 'read_bubendorff', 'write_bubendorff', 'read_smarther', 'write_smarther', 'read_thermostat','write_thermostat', 'read+_camera', 'write_camera', 'access_camera', 'read_boorbell', 'access_doorbell',
             'read_mx', 'write_mx', 'read_presence', 'write_presence', 'access_presence', 'read_homecoach', 'read_carbonmonoxidedetector', 'read_smokedetector', 'read_mhs1', 'write_mhs1']
scopelist1 = [ 'read_magellan', 'write_megellan']
token = '590aba75ee261c2b548bf4c0|6f86bab8767a77e853205dd74ab5a823'

class NetatmoCloudAccess(object):
    def __init__(self, client_ID, client_SECRET, scope, token ):
       
        netatmo_URL = 'https://api.netatmo.com'
        tokenURL = '/oauth2/token'
        authorizeURL = '/oauth2/authorize?'

        self.tokenURL =   netatmo_URL + tokenURL
        self.authorizeURL =   netatmo_URL + authorizeURL
        
        self.client_ID = client_ID
        self.client_secret = client_SECRET
        self.Rtoken = token
        self.tokenInfo = None
        self.state_str = 'random_str'
        self.code = None
        self.scope_str = ''
        for str in scope:
            self.scope_str = self.scope_str + ' ' + str

        #self.scope = scope.split()
        self.redirectURL = 'https://example.com/callback-url'


        self.tokenExpTime = 0
        self.timeExpMarging = 600 # 10min 
        self.lastTransferTime = time.time()
        self.token = None

            
        while not self.request_new_token( ):
            time.sleep(60)
            logging.info('Waiting to acquire access token')





    #####################################


    def request_new_token(self):
        try:
            now = int(time.time())
            
            #response = requests.post( self.tokenURL,
            #        data={"grant_type": "client_credentials",
            #            "client_id" : self.uaID,
            #            "client_secret" : self.secID },
            #    )
            
            data = {}
            data['client_id'] = self.client_ID
            #data['client_id'] = 'Netatmo ISY nodeserver'
            data['client_secret'] = self.client_secret
            data['scope'] = self.scope_str
            data['state'] = self.state_str
            #data['redirect_uri'] = self.redirectURL 
            headers1 = {}
            headers1['Content-type'] = 'application/json'
            headers1 = {'Accept':'application/json'}
            response = requests.post( self.authorizeURL, data=json.dumps(data), headers=headers1)


            temp = response.json()
            self.token = temp
            #self.token['expirationTime'] = int(self.token['expires_in'] + now )
            return(True)

        except Exception as e:
            logging.debug('Exeption occcured during request_new_token : {}'.format(e))
            return(False)


    def netatmo_refresh_token(self):
        dateNow = int(time.time())
        S = {}
        if self.Rtoken:
            data = {}
            data['grant_type'] = 'refresh_token'
            data['client_id'] = self.client_ID
            data['client_secret'] = self.client_secret
            
            data['refresh_token']=self.Rtoken
            headers1 = {}
            headers1['Content-type'] = 'application/x-www-form-urlencoded;charset=UTF-8'
            #data['scope']='openid email offline_access'      
            resp = requests.post(self.tokenURL , headers= headers1, data=data)
            S = json.loads(resp.text)
            S['created_at'] = dateNow
            if 'refresh_token' in S:
                self.Rtoken = S['refresh_token']
                #S['created_at'] = dateNow
                #dataFile = open('./refreshToken.txt', 'w')
                #dataFile.write( self.Rtoken)
                #dataFile.close()

            dataFile = open('./refreshToken.txt', 'w')
            dataFile.write( self.Rtoken)
            dataFile.close()
            self.tokenInfo = S
       
            time.sleep(1)

        #logging.debug('netatmo_refresh_token: {}'.format(S))
        return S













    def refresh_token(self):
        try:
            logging.info('Refreshing Token ')
            now = int(time.time())

            response = requests.post( self.tokenURL,
                data={"grant_type": "refresh_token",
                    "client_id" :  self.client_ID,
                    "refresh_token":self.token['refresh_token'],
                    }
            )
            temp =  response.json()
            if temp['access_token'] != self.token['access_token'] :
                self.token = temp
                #self.client.username_pw_set(username=self.token['access_token'], password=None)
                #need to check if device tokens change with new access token
            self.token['expirationTime'] = int(self.token['expires_in'] + now )
            return(True)

        except Exception as e:
            logging.debug('Exeption occcured during refresh_token : {}'.format(e))
            return(self.request_new_token())

    def get_access_token(self):
        #self.tokenLock.acquire()
        now = int(time.time())
        if self.token == None:
            self.request_new_token()
        if now > self.token['expirationTime']  - self.timeExpMarging :
            self.refresh_token()
        #    if now > self.token['expirationTime']: #we lost the token
        #        self.request_new_token()
        #    else:
        #self.tokenLock.release() 

                
    def is_token_expired (self, accessToken):
        return(accessToken == self.token['access_token'])
        
    '''
    def retrieve_device_list(self):
        try:
            data= {}
            data['method'] = 'Home.getDeviceList'
            data['time'] = str(int(time.time_ns()//1e6))
            headers1 = {}
            headers1['Content-type'] = 'application/json'
            headers1['Authorization'] = 'Bearer '+ self.token['access_token']
            r = requests.post(self.apiv2URL, data=json.dumps(data), headers=headers1) 
            info = r.json()
            self.deviceList = info['data']['devices']
            self.HubList = []
            for devNbr in range(0,len(self.deviceList)):
                if self.deviceList[devNbr]['type'] == 'Hub':
                    self.HubList.append(self.deviceList[devNbr])
        except Exception as e:
            logging.error('Exception  -  retrieve_device_list : {}'.format(e))             


    def retrieve_homeID(self):
        try:
            data= {}
            data['method'] = 'Home.getGeneralInfo'
            data['time'] = str(int(time.time_ns()//1e6))
            headers1 = {}
            headers1['Content-type'] = 'application/json'
            headers1['Authorization'] = 'Bearer '+ self.token['access_token']

            r = requests.post(self.apiv2URL, data=json.dumps(data), headers=headers1) 
            homeId = r.json()
            self.homeID = homeId['data']['id']

        except Exception as e:
            logging.error('Exception  - retrieve_homeID: {}'.format(e))            

    def getDeviceList (self):
        return(self.deviceList)

    '''

test = NetatmoCloudAccess(clientID, clientSecret, scopelist1, token)
        
test.netatmo_refresh_token()
