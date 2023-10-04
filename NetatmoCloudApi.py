#!/usr/bin/env python3
import requests
import json
import time
from requests_oauth2 import OAuth2BearerToken


try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=30)


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


    '''
    def isNodeServerUp(self):
        return( self.tokenInfo != None)
    '''

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

    '''
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
    '''

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


            '''
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
            '''
        #logging.debug('netatmo_refresh_token: {}'.format(S))
        return S

