
#!/usr/bin/env python3

### Your external service class
'''
Your external service class can be named anything you want, and the recommended location would be the lib folder.
It would look like this:

External service sample code
Copyright (C) 2023 Universal Devices

MIT License
'''
import requests
import time
#from udi_interface import LOGGER, Custom
from oauth import OAuth
try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)



# Implements the API calls to your external service
# It inherits the OAuth class
class NetatmoCloud(OAuth):
    yourApiEndpoint = 'https://api.netatmo.com/api'

    def __init__(self, polyglot):
        super().__init__(polyglot)
        self.scope_str = None
        self.apiEndpoint = 'https://api.netatmo.com'
        self.client_ID = None
        self.client_SECRET = None


        self.scopeList = ['read_station', 'read_magellan', 'write_magellan', 'read_bubendorff', 'write_bubendorff', 'read_smarther', 'write_smarther', 'read_thermostat','write_thermostat', 'read+_camera', 'write_camera', 'access_camera', 'read_boorbell', 'access_doorbell',
             'read_mx', 'write_mx', 'read_presence', 'write_presence', 'access_presence', 'read_homecoach', 'read_carbonmonoxidedetector', 'read_smokedetector', 'read_mhs1', 'write_mhs1']

        self.poly = polyglot
        self.customParams = Custom(polyglot, 'customparams')
        logging.info('External service connectivity initialized...')
        #logging.debug('oauth : {}'.format(self.oauthConfig))
        time.sleep(1)
 
    # The OAuth class needs to be hooked to these 3 handlers
    def customDataHandler(self, data):
        super()._customDataHandler(data)

    def customNsHandler(self, key, data):
        super()._customNsHandler(key, data)

    def oauthHandler(self, token):
        logging.debug('oauthHandler')
        self.updateOauthConfig()
        super()._oauthHandler(token)

    def refresh_token(self):
        logging.debug('checking token for refresh')
        

    # Your service may need to access custom params as well...
    def customParamsHandler(self, data):
        self.customParams.load(data)
        logging.debug('customParamsHandler called')
        # Example for a boolean field
        if 'clientID' in self.customParams:
            self.client_ID = self.customParams['clientID'] 
            #self.addOauthParameter('client_id',self.client_ID )
            #self.oauthConfig['client_id'] =  self.client_ID
        else:
            self.customParams['clientID'] = 'enter client_id'
            self.client_ID = None
            
        if 'clientSecret' in self.customParams:
            self.client_SECRET = self.customParams['clientSecret'] 
            #self.addOauthParameter('client_secret',self.client_SECRET )
            #self.oauthConfig['client_secret'] =  self.client_SECRET
        else:
            self.customParams['clientSecret'] = 'enter client_secret'
            self.client_SECRET = None
            
        if 'scope' in self.customParams:
            temp = self.customParams['scope'] 
            temp1 = temp.split()
            self.scope_str = ''
            for net_scope in temp1:
                if net_scope in self.scopeList:
                    self.scope_str = self.scope_str + ' ' + net_scope
                else:
                    logging.error('Unknown scope provide {} - removed '.format(net_scope))
            self.scope = self.scope_str.split()
            
            attempts = 0
            while not self.customData and attempts <3:
                attempts = attempts + 1
                time.sleep(1)

            if self.customData:
                if 'scope' in self.customData:
                    if self.scope_str != self.customData['scope']:
                       #scope changed - we need to generate a new token/refresh token
                       logging.debug('scope has changed - need to get new token')
                       self.poly.Notices['auth'] = 'Please initiate authentication - scope has changed'
                       self.customData['scope'] = self.scope_str
                else: 
                    if self.oauthConfig['client_id'] is None or self.oauthConfig['client_secret'] is None:
                        self.updateOauthConfig()    
                    
                    self.poly.Notices['auth'] = 'Please initiate authentication - scope has changed'
                    self.customData['scope'] = self.scope_str


            #self.addOauthParameter('scope',self.scope_str )
            #self.oauthConfig['scope'] = self.scope_str
            logging.debug('Following scopes are selected : {}'.format(self.scope_str))
        else:
            self.customParams['scope'] = 'enter desired scopes space separated'
            self.scope_str = ""


        if 'refresh_token' in self.customParams:
            if self.customParams['refresh_token'] is not None and self.customParams['refresh_token'] != "":
                self.customData.token['refresh_token'] = self.customParams['refresh_token']


        self.updateOauthConfig()
        #self.myParamBoolean = ('myParam' in self.customParams and self.customParams['myParam'].lower() == 'true')
        #logging.info(f"My param boolean: { self.myParamBoolean }")

    def get_home_info(self):
        logging.debug('get_home_info')
        api_str = '/homesdata'
        res = self._callApi('GET', api_str )
        logging.debug(res)

    def get_weather_info(self):
        logging.debug('get_weather_info')
        api_str = '/getstationsdata'
        res = self._callApi('GET', api_str )
        logging.debug(res)

    def get_weather_info2(self):
        logging.debug('get_weather_info')
        api_str = '/homestatus'
        res = self._callApi('GET', api_str )
        logging.debug(res)

    # Call your external service API
    def _callApi(self, method='GET', url=None, body=None):
        # When calling an API, get the access token (it will be refreshed if necessary)
        accessToken = self.getAccessToken()

        if accessToken is None:
            logging.error('Access token is not available')
            return None

        if url is None:
            logging.error('url is required')
            return None

        completeUrl = self.yourApiEndpoint + url

        headers = {
            'Authorization': f"Bearer { accessToken }"
        }

        if method in [ 'PATCH', 'POST'] and body is None:
            logging.error(f"body is required when using { method } { completeUrl }")
        logging.debug(' call info url={}, header= {}, body = {}'.format(completeUrl, headers, body))

        try:
            if method == 'GET':
                response = requests.get(completeUrl, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(completeUrl, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(completeUrl, headers=headers, json=body)
            elif method == 'POST':
                response = requests.post(completeUrl, headers=headers, json=body)
            elif method == 'PUT':
                response = requests.put(completeUrl, headers=headers)

            response.raise_for_status()
            try:
                return response.json()
            except requests.exceptions.JSONDecodeError:
                return response.text

        except requests.exceptions.HTTPError as error:
            logging.error(f"Call { method } { completeUrl } failed: { error }")
            return None

    # Then implement your service specific APIs
    def getAllDevices(self):
        return self._callApi(url='/devices')

    def unsubscribe(self):
        return self._callApi(method='DELETE', url='/subscription')

    def getUserInfo(self):
        return self._callApi(url='/user/info')


    def updateOauthConfig(self):
        self.addOauthParameter('client_id',self.client_ID )
        self.addOauthParameter('client_secret',self.client_SECRET )
        self.addOauthParameter('scope',self.scope_str )
        #self.addOauthParameter('state','dette er en test' )
        #self.addOauthParameter('redirect_uri','https://my.isy/io/api/cloudlink/redirect' )
        self.addOauthParameter('name','Netatmo Test' )
        self.addOauthParameter('cloudlink', True )
        self.addOauthParameter('addRedirect', True )
        logging.debug('updateOauthConfig = {}'.format(self.oauthConfig))

### Main node server code

