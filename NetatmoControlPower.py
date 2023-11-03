
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
    


class NetatmoControlPower (NetatmoControlCommon):
    def __init__(self):
        super().__init__()
        self.instant_data = {}
        self.cloud_data = {}
        self.control_data = {}

        self.dev_list = ['NLG', 'NLGS', 'NLE', 'NLPS', 'NLP', 'NLPM', 'NLC', 'NLPC', 'NLPT', 'NLPO', 'NLPD', 'BNMH', 'BNMH', 'BNXM' ]
        self.gateways_list = ['NLG', 'NLGS', 'NLE', 'BNMH']
        self.modules_list = [ 'NLPS', 'NLP', 'NLPM', 'NLC', 'NLPC', 'NLPT', 'NLPO', 'NLPD', 'BNMH', 'BNXM' ]

   



    def update_power_info(self, home_id):
        '''update_power_info'''    

