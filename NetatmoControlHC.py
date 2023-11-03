
#!/usr/bin/env python3

from  NetatmoControlCommon import NetatmoControlCommon
import urllib.parse

from oauth import OAuth

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)
    


class NetatmoControlHC (NetatmoControlCommon):
    def __init__(self):
        super().__init__()
        self.instant_data = {}
        self.cloud_data = {}
        self.control_data = {}



        self.dev_list = ['BNS', 'OTH', 'OTM', 'NRV', 'BNMH', 'BNTH', 'BNFC','BNTR']
        self.gateway_list = ['BNS', 'OTH', 'BNMH']
        self.module_list = [ 'OTM', 'NRV', 'BNTH', 'BNFC','BNTR']


        



    def update_HC_info(self, home_id):
        '''update_HC_info'''        

