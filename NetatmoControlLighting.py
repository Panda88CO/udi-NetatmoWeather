
#!/usr/bin/env python3

from  NetatmoOauthDev import NetatmoCloud 
import urllib.parse

from oauth import OAuth

try:
    from udi_interface import LOGGER, Custom, OAuth
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)
    


class NetatmoControlLighting (NetatmoCloud):
    def __init__(self):
        #super().__init__()
        self.instant_data = {}
        self.cloud_data = {}
        self.control_data = {}

        self.dev_list = ['NLG', 'NLGS', 'NLFN', 'NLL', 'NLF', 'NLFE','NLM', 'NLIS', 'NLTS', 'NLD', 'Z3L', 'BNMH', 'BNLD','BNIL', 'BN3L' ]
        self.gateway_list = ['NLG', 'NLGS', 'BNMH']
        self.module_list = [ 'NLFN', 'NLL', 'NLF', 'NLFE','NLM', 'NLIS', 'NLTS', 'NLD', 'Z3L', 'BNLD','BNIL', 'BN3L' ]
        self.dimmer_list = [ 'NLFN', 'NLF', 'NLFE',  'NLD', 'Z3L', 'BNLD','BNIL', 'BN3L' ]
        self.switch_list = [ 'NLL', 'NLM', 'NLIS',  'NLD', 'Z3L', 'BNIL', 'BN3L' ]



        

    def update_lighting_info(self, home_id):
        '''update_lighting_info'''


    def get_modules(self, home_id):
        '''get_modules'''
        return(self._get_modules(home_id, self.module_list))   

    def get_gateways(self, home_id):
        '''get_modules'''
        return(self._get_modules(home_id, self.gateway_list))  
    
    def get_dimmers (self, home_id):
        '''get_dimmers'''
        return(self._get_modules(home_id, self.dimmer_list))  

    def get_switches(self, home_id):
        '''get_switches'''
        return(self._get_modules(home_id, self.switch_list))  