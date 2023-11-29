
#!/usr/bin/env python3

from NetatmoOauthDev import NetatmoCloud
from NetatmoControlHC import NetatmoControlHC
from NetatmoControlLighting import NetatmoControlLighting
from NetatmoControlPower import NetatmoControlPower
from NetatmoControlShutter import NetatmoControlShutter
from NetatmoControlVentilation import NetatmoControlVentilation


import urllib.parse

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
        self._dev_list = ['BNS', 'OTH', 'OTM', 'NRV', 'BNMH', 'BNTH', 'BNFC','BNTR', 'NLG', 
                          'NLGS', 'NLFN', 'NLL', 'NLF', 'NLFE','NLM', 'NLIS', 'NLTS', 'NLD', 'Z3L', 'BNLD','BNIL', 'BN3L' 
                          'NLG', 'NLGS', 'NLE', 'NLPS', 'NLP', 'NLPM', 'NLC', 'NLPC', 'NLPT', 'NLPO', 'NLPD', 'BNXM', 
                         'NLV', 'NLLV', 'NLIV', 'Z3V', 'NLAV', 'BNAB', 'BNAS', 'BNMS', 'NLLF'] 
        
        self.HC_dev_list = ['BNS', 'OTH', 'OTM', 'NRV', 'BNMH', 'BNTH', 'BNFC','BNTR']
        self.HC_gateway_list = ['BNS', 'OTH', 'BNMH']
        self.HC_module_list = [ 'OTM', 'NRV', 'BNTH', 'BNFC','BNTR']

        self.Light_dev_list = ['NLG', 'NLGS', 'NLFN', 'NLL', 'NLF', 'NLFE','NLM', 'NLIS', 'NLTS', 'NLD', 'Z3L', 'BNMH', 'BNLD','BNIL', 'BN3L' ]
        self.Light_gateway_list = ['NLG', 'NLGS', 'BNMH']
        self.Light_module_list = [ 'NLFN', 'NLL', 'NLF', 'NLFE','NLM', 'NLIS', 'NLTS', 'NLD', 'Z3L', 'BNLD','BNIL', 'BN3L' ]
        self.Light_dimmer_list = [ 'NLFN', 'NLF', 'NLFE',  'NLD', 'Z3L', 'BNLD','BNIL', 'BN3L' ]
        self.Light_switch_list = [ 'NLL', 'NLM', 'NLIS',  'NLD', 'Z3L', 'BNIL', 'BN3L' ]

        self.Power_dev_list = ['NLG', 'NLGS', 'NLE', 'NLPS', 'NLP', 'NLPM', 'NLC', 'NLPC', 'NLPT', 'NLPO', 'NLPD', 'BNMH', 'BNMH', 'BNXM' ]
        self.Power_gateway_list = ['NLG', 'NLGS', 'NLE', 'BNMH']
        self.Power_module_list = [ 'NLPS', 'NLP', 'NLPM', 'NLC', 'NLPC', 'NLPT', 'NLPO', 'NLPD', 'BNMH', 'BNXM' ]

        self.Shutter_dev_list = ['NLG', 'NLGS', 'NLV', 'NLLV', 'NLD', 'NLIV', 'Z3V', 'NLAV', 'BNMH', 'BNAB', 'BNAS', 'BNMS']
        self.Shutter_gateway_list = ['NLG', 'NLGS',  'BNMH']
        self.Shutter_module_list = [ 'NLV', 'NLLV', 'NLD', 'NLIV', 'Z3V', 'NLAV', 'BNAB', 'BNAS', 'BNMS']

        self.Ventilation_dev_list = ['NLG', 'NLGS', 'NLLF']
        self.Ventilation_gateway_list = ['NLG', 'NLGS']
        self.Ventilation_module_list = ['NLLF']




    def initialize(self):
        '''initialize'''
        #self.power = NetatmoControlPower()
        #self.lighting = NetatmoControlLighting()
        #self.hot_cold = NetatmoControlHC()
        #self.ventilation = NetatmoControlVentilation()
        #self.shutter = NetatmoControlShutter()

    def get_type_devices(self, home_id, dev_list):
        '''get_type_modules'''
        res_dict = {}
        home_modules = self.get_home_status(home_id)
        if 'modules' in home_modules:
            for module in home_modules['modules']:
                if home_modules[module]['type'] in dev_list:
                    res_dict[module] = home_modules[module]
        return(res_dict)



    def get_homes(self):
        '''get_homes_info'''
        tmp = self.get_homes_info()
        ctrl_in_homes = {}
        for home_id in tmp:
            found = False
            for mod_type in tmp[home_id]['module_types']:
                if mod_type in  self._dev_list:
                    found = True
            if found:
                ctrl_in_homes[home_id] = tmp[home_id]
        self.homes_list = ctrl_in_homes
        #self.initialize()
        return(ctrl_in_homes)



    def merge_data_str(self, data):
        '''merge_data_str'''
        if data == 'ts':
            data_str = 'time_stamp'
        if data == 'time_utc':
            data_str = 'time_stamp'
        elif data == 'last_seen':
            data_str = 'time_stamp'

        elif data == 'AbsolutePressure':
            data_str = 'absolute_pressure'

        elif data == 'reachable':
            data_str = 'online'

        else:
            data_str = data.lower()
        return(data_str)
    


    def get_power_gateways(self, home_id):
        '''get_power_gateways'''
        return(self._get_modules(home_id, self.Power_gateway_list)) 


    def get_power_modules(self, home_id):
        '''get_power_modules'''
        return(self._get_modules(home_id, self.Power_module_list))   

    def get_lighting_gateways(self, home_id):
        '''get_lighting_gateways'''
        return(self._get_modules(home_id, self.Light_gateway_list)) 


    def get_lighting_modules(self, home_id):
        '''get_lighting_modules'''
        return(self._get_modules(home_id, self.Light_module_list))   