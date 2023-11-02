
#!/usr/bin/env python3

from  NetatmoOauthDev import NetatmoCloud
import urllib.parse

from oauth import OAuth

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)



class NetatmoControl (NetatmoCloud):
    def __init__(self):
        super().__init__()
        self.instant_data = {}
        self.cloud_data = {}
        self.control_data = {}

        self.ligthning_dev = ['NLG', 'NLGS', 'NLFN', 'NLL', 'NLF', 'NLFE','NLM', 'NLIS', 'NLTS', 'NLD', 'Z3L', 'BNMH', 'BNLD','BNIL', 'BN3L' ]
        self.ligthning_gateway = ['NLG', 'NLGS', 'BNMH']
        self.ligthning_module = [ 'NLFN', 'NLL', 'NLF', 'NLFE','NLM', 'NLIS', 'NLTS', 'NLD', 'Z3L', 'BNLD','BNIL', 'BN3L' ]
        self.lighting_dimmer = [ 'NLFN', 'NLF', 'NLFE',  'NLD', 'Z3L', 'BNLD','BNIL', 'BN3L' ]
    

        self.ventilation_dev = ['NLG', 'NLGS', 'NLLF']
        self.ventilation_gateway = ['NLG', 'NLGS']
        self.ventilation_module = ['NLLF']

        self.power_dev = ['NLG', 'NLGS', 'NLE', 'NLPS', 'NLP', 'NLPM', 'NLC', 'NLPC', 'NLPT', 'NLPO', 'NLPD', 'BNMH', 'BNMH', 'BNXM' ]
        self.power_gateway = ['NLG', 'NLGS', 'NLE', 'BNMH']
        self.power_module = [ 'NLPS', 'NLP', 'NLPM', 'NLC', 'NLPC', 'NLPT', 'NLPO', 'NLPD', 'BNMH', 'BNXM' ]

        self.HC_dev = ['BNS', 'OTH', 'OTM', 'NRV', 'BNMH', 'BNTH', 'BNFC','BNTR']
        self.HC_gateways = ['BNS', 'OTH', 'BNMH']
        self.HC_modules = [ 'OTM', 'NRV', 'BNTH', 'BNFC','BNTR']

        self.Roller_shutter_dev = ['NLG', 'NLGS', 'NLV', 'NLLV', 'NLD', 'NLIV', 'Z3V', 'NLAV', 'BNMH', 'BNAB', 'BNAS', 'BNMS']

        

    def update_lighting_info(self, home_id):
        '''update_lighting_info'''


    def update_ventilation_info(self, home_id):
        '''update_ventilation_info'''


    def update_power_info(self, home_id):
        '''update_power_info'''    

    def update_HC_info(self, home_id):
        '''update_HC_info'''        

    def update_Roller_shutter_info(self, home_id):
        '''update_HC_info'''        
        