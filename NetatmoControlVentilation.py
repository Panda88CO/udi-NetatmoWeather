
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
    


class NetatmoControlVentilation (NetatmoControlCommon):
    def __init__(self):
        super().__init__()
        self.instant_data = {}
        self.cloud_data = {}
        self.control_data = {}

        self.dev_list = ['NLG', 'NLGS', 'NLLF']
        self.gateway_list = ['NLG', 'NLGS']
        self.module_list = ['NLLF']




    def update_ventilation_info(self, home_id):
        '''update_ventilation_info'''



        