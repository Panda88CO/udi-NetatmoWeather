
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
import json
import urllib.parse
#from udi_interface import LOGGER, Custom
#from oauth import OAuth
try:
    from udi_interface import LOGGER, Custom, OAuth
    logging = LOGGER
    Custom = Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)



# Implements the API calls to your external service
# It inherits the OAuth class
class NetatmoCloud(OAuth):
    yourApiEndpoint = 'https://api.netatmo.com/api'

    def __init__(self, polyglot):
        super().__init__(polyglot)
        logging.info('OAuth initializing')
        self.poly = polyglot
        self.scope_str = None
        self.apiEndpoint = 'https://api.netatmo.com'
        self.client_ID = None
        self.client_SECRET = None
        self.handleCustomParamsDone = False
        #self.customerDataHandlerDone = False
        self.customNsHandlerDone = False
        self.temp_unit = 'C'

        self.scopeList = ['read_station', 'read_magellan', 'write_magellan', 'read_bubendorff', 'write_bubendorff', 'read_smarther', 'write_smarther', 'read_thermostat','write_thermostat', 'read+_camera', 'write_camera', 'access_camera', 'read_boorbell', 'access_doorbell',
             'read_mx', 'write_mx', 'read_presence', 'write_presence', 'access_presence', 'read_homecoach', 'read_carbonmonoxidedetector', 'read_smokedetector', 'read_mhs1', 'write_mhs1']
        
        self.poly = polyglot
        #self.customParameters= Custom(polyglot, 'customparams')
        #self.Notices = Custom(self.poly, 'notices')

        logging.info('External service connectivity initialized...')
        #logging.debug('oauth : {}'.format(self.oauthConfig))

        time.sleep(1)
        #while not self.handleCustomParamsDone:
        #    logging.debug('Waiting for customParams to complete - getAccessToken')
        #    time.sleep(0.2)
        # self.getAccessToken()
    
    # The OAuth class needs to be hooked to these 3 handlers
    def customDataHandler(self, data):
        while not self.handleCustomParamsDone:
            logging.debug('Waiting for customDataHandler to complete')
            time.sleep(1)
        super()._customDataHandler(data)
        #self.customerDataHandlerDone = True

    def customNsHandler(self, key, data):
        while not self.handleCustomParamsDone:
            logging.debug('Waiting for customNsHandler to complete')
            time.sleep(1)
        #self.updateOauthConfig()
        super().customNsHandler(key, data)
        self.customNsHandlerDone = True

    def oauthHandler(self, token):
        while not self.handleCustomParamsDone or not self.customNsHandlerDone:
            logging.debug('Waiting for oauthHandler to complete')
            time.sleep(1)
        
        super().oauthHandler(token)

    #def refresh_token(self):
    #    logging.debug('checking token for refresh')
        

    # Your service may need to access custom params as well...
    
    def customParamsHandler(self, userParams):
        self.customParameters.load(userParams)
        logging.debug('customParamsHandler called')
        oauthSettingsUpdate = {}
        # Example for a boolean field

        if 'clientID' in userParams:
            self.client_ID = self.customParameters['clientID'] 
            oauthSettingsUpdate['client_id'] = self.customParameters['clientID']
            #self.addOauthParameter('client_id',self.client_ID )
            #self.oauthConfig['client_id'] =  self.client_ID
        else:
            self.customParameters['clientID'] = 'enter client_id'
            self.client_ID = None
            
        if 'clientSecret' in self.customParameters:
            self.client_SECRET = self.customParameters['clientSecret'] 
            oauthSettingsUpdate['client_secret'] = self.customParameters['clientSecret']
            #self.oauthConfig['client_secret'] =  self.client_SECRET
        else:
            self.customParameters['clientSecret'] = 'enter client_secret'
            self.client_SECRET = None
            
        #if 'scope' in self.customParameters:
        #    temp = self.customParameters['scope'] 
        #    temp1 = temp.split()
        #    self.scope_str = ''
        #    for net_scope in temp1:
        #        if net_scope in self.scopeList:
        #            self.scope_str = self.scope_str + ' ' + net_scope
        #        else:
        #            logging.error('Unknown scope provided: {} - removed '.format(net_scope))
        #    self.scope = self.scope_str.split()
        #else:
        #    self.customParameters['scope'] = 'enter desired scopes space separated'
        #    self.scope_str = ""

        if "TEMP_UNIT" in self.customParameters:
            self.temp_unit = self.customParameters['TEMP_UNIT'][0].upper()
        else:
            self.temp_unit = 0
            self.customParameters['TEMP_UNIT'] = 'C'

        #if 'refresh_token' in self.customParameters:
        #    if self.customParameters['refresh_token'] is not None and self.customParameters['refresh_token'] != "":
        #        self.customData.token['refresh_token'] = self.customParameters['refresh_token']
            
        self.updateOauthSettings(oauthSettingsUpdate)        
        logging.debug('Updated oAuth config: {}'.format(self.getOauthSettings()))
        self.handleCustomParamsDone = True

        #self.updateOauthConfig()
        #self.myParamBoolean = ('myParam' in self.customParametersand self.customParameters['myParam'].lower() == 'true')
        #logging.info(f"My param boolean: { self.myParamBoolean }")
    

    def add_to_parameters(self,  key, value):
        '''add_to_parameters'''
        self.customParameters[key] = value

    def check_parameters(self, key, value):
        '''check_parameters'''
        if key in self.customParameters:
            return(self.customParameters[key]  == value)
        else:
            return(False)

    def setOauthScope(self, scope):
        oauthSettingsUpdate = {}
        logging.debug('Set Scope to {}'.format(scope))
        oauthSettingsUpdate['scope'] = str(scope)
        self.updateOauthSettings(oauthSettingsUpdate)
    
    def setOauthName(self, name):
        oauthSettingsUpdate = {} 
        logging.debug('Set name to {}'.format(name))
        oauthSettingsUpdate['name'] = str(name)
        self.updateOauthSettings(oauthSettingsUpdate)
    
    '''
    def _insert_refreshToken(self, refresh_token, clientId, clientSecret):
        data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': clientId,
                'client_secret':  clientSecret
                }
        try:
            response = requests.post('https://api.netatmo.com/oauth2/token' , data=data)
            response.raise_for_status()
            token = response.json()
            logging.info('Refreshing tokens successful')
            logging.debug(f"Token refresh result [{ type(token) }]: { token }")
            self._saveToken(token)
            return('Success')
          
        except requests.exceptions.HTTPError as error:
            logging.error(f"Failed to refresh  token: { error }")
            return(None)
            # NOTE: If refresh tokens fails, we keep the existing tokens available.
    '''

    # Call your external service API
    def _callApi(self, method='GET', url=None, body=None):
        # When calling an API, get the access token (it will be refreshed if necessary)
        try:
            accessToken = self.getAccessToken()
        except ValueError as err:
            LOGGER.warning('Access token is not yet available. Please authenticate.')
            self.poly.Notices['auth'] = 'Please initiate authentication'
            return
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
    '''
    def getAllDevices(self):
        return self._callApi(url='/devices')

    def unsubscribe(self):
        return self._callApi(method='DELETE', url='/subscription')

    def getUserInfo(self):
        return self._callApi(url='/user/info')
    '''
    '''
    def updateOauthConfig(self):
        logging.debug('updateOauthConfig')
        logging.debug(' {} {} {}'.format(self.client_ID,self.client_SECRET, self.scope_str  ))
        self.addOauthParameter('client_id',self.client_ID )
        self.addOauthParameter('client_secret',self.client_SECRET )
        self.addOauthParameter('scope','read_station' )
        #self.addOauthParameter('state','dette er en test' )
        #self.addOauthParameter('redirect_uri','https://my.isy/io/api/cloudlink/redirect' )
        self.addOauthParameter('name','Netatmo Weather' )
        self.addOauthParameter('cloudlink', True )
        self.addOauthParameter('addRedirect', True )
        logging.debug('updateOauthConfig = {}'.format(self.oauthConfig))
    '''
### Main node server code

    #def set_temp_unit(self, value):
    #    self.temp_unit = value

    
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

    def process_homes_data(self, net_system):
        homes_list = {}
        for home in range(0, len(net_system['homes'])):
            tmp = net_system['homes'][home]
            homes_list[tmp['id']]= {}
            homes_list[tmp['id']]['name']= tmp['name']
            homes_list[tmp['id']]['modules'] = {}
            homes_list[tmp['id']]['module_types'] = []
            if 'modules' in tmp:
                for mod in range(0,len(tmp['modules'])):
                    homes_list[tmp['id']]['modules'][tmp['modules'][mod]['id']] = tmp['modules'][mod]
                    homes_list[tmp['id']]['module_types'].append( tmp['modules'][mod]['type'] )
        return(homes_list)



    def get_homes_info(self):
        logging.debug('get_home_info')
        api_str = '/homesdata'
        temp = self._callApi('GET', api_str )
        self.netatmo_systems = temp['body']
        logging.debug(self.netatmo_systems)
        self.homes_list = self.process_homes_data(self.netatmo_systems)
        return(self.homes_list)


    def get_home_status(self, home_id):
        status = {}
        logging.debug('get_home_status')
        try:
            if home_id:
                home_id_str = urllib.parse.quote_plus(home_id )
                api_str = '/homestatus?home_id='+str(home_id_str)


            tmp = self._callApi('GET', api_str)
            if tmp:
                tmp = tmp['body']
                if 'errors' not in tmp:
                    tmp = tmp['home']
                    status[home_id] = home_id #tmp['body']['body']['home']
                    if 'modules' in tmp:
                        status['modules'] = {}
                        status['module_types'] = []
                        for mod in range(0,len(tmp['modules'])):
                            status['modules'][tmp['modules'][mod]['id']]= tmp['modules'][mod]
                            status['module_types'].append(tmp['modules'][mod]['type'])
                    logging.debug(status)
                else:
                    status['error'] = tmp['error']

                return(status)
        except Exception as e:
            logging.error('Error get hiome status : {}'.format(e))

    def get_modules(self, home_id):
        '''get_modules'''
        logging.debug('get_modules')
        if home_id in self.homes_list:
            # Find relevan modules
            return(self.homes_list[home_id]['modules'])
        
    def get_module_types(self, home_id):
        '''get_module_types'''
        if home_id in self.homes_list:
            return(self.homes_list[home_id]['module_types'])

    def get_home_name(self, home_id):
        '''get_home_name'''
        if home_id in self.homes_list:
            return(self.homes_list[home_id]['name'])

    def get_modules_present(self, home_id):
        '''get_modules_present'''
        logging.debug('get_modules_present')
        modules = {}
        if home_id in self.homes_list:
            for tmp in range(0,len(self.homes_list[home_id]['modules'])):
                modules[tmp[id]] = tmp
        return(modules)
    
    def get_sub_modules(self, home_id, main_module_id):
        '''get_sub_modules'''
        logging.debug('get_sub_modules')
        if home_id in  self.homes_list:
            if main_module_id in self.homes_list[home_id]['modules']:
                if 'modules_bridged' in self.homes_list[home_id]['modules'][main_module_id]:
                    return(self.homes_list[home_id]['modules'][main_module_id]['modules_bridged'])

    def get_module_info(self, home_id, module_id):
        '''get_module_info'''
        logging.debug('get_module_info')
        if home_id in  self.homes_list:
            if module_id in self.homes_list[home_id]['modules']:
                return(self.homes_list[home_id]['modules'][module_id])


    def _get_modules(self, home_id, mod_type_lst):
        '''get list of weather modules of type attached to house_id'''
        try:
            mod_dict = {}
            if home_id in self.homes_list:
               for module in self.homes_list[home_id]['modules']:
                    if self.homes_list[home_id]['modules'][module]['type'] in mod_type_lst:
                        mod_dict[module] = {}
                        if 'name' in  self.homes_list[home_id]['modules'][module]:
                            mod_dict[module]['name'] = self.homes_list[home_id]['modules'][module]['name']
                        else:
                            mod_dict[module]['name'] = self.homes_list[home_id]['modules'][module]['id']
                    


                    
            else:
                logging.error('No data found for {} {}'.format(home_id, mod_type_lst))
            return(mod_dict)
    
        except Exception as e:
            logging.error('Exception : {}'.format(e))
            return(None)