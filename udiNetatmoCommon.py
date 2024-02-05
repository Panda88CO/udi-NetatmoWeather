#!/usr/bin/env python3

"""
Polyglot v3 node server
Copyright (C) 2023 Universal Devices

MIT License
"""

def node_queue(self, data):
    self.n_queue.append(data['address'])

def wait_for_node_done(self):
    while len(self.n_queue) == 0:
        time.sleep(0.1)
    self.n_queue.pop()

def getValidName(self, name):
    name = bytes(name, 'utf-8').decode('utf-8','ignore')
    return re.sub(r"[^A-Za-z0-9_ ]", "", name)

# remove all illegal characters from node address
def getValidAddress(self, name):
    name = bytes(name, 'utf-8').decode('utf-8','ignore')
    tmp = re.sub(r"[^A-Za-z0-9_]", "", name.lower())
    logging.debug('getValidAddress {}'.format(tmp))
    return tmp[:14]


def convert_temp_unit(self, tempStr):
    if tempStr.capitalize()[:1] == 'F':
        return(1)
    elif tempStr.capitalize()[:1] == 'C':
        return(0)
    
def rfstate2ISY(self, rf_state):
    if rf_state.lower() == 'full' or rf_state.lower() == 'high':
        rf = 0
    elif rf_state.lower() == 'medium':
        rf = 1
    elif rf_state.lower() == 'low':
        rf = 2
    else:
        rf= 99
        logging.error('Unsupported RF state {}'.format(rf_state))
    return(rf)


def battery2ISY(self, batlvl):
    if batlvl == 'max':
        state = 0
    elif batlvl == 'full':
        state = 1
    elif batlvl == 'high':
        state = 2
    elif batlvl == 'medium':
        state = 3
    elif batlvl == 'low':
        state = 4
    elif batlvl == 'very low':
        state = 5
    else:
        state = 99
    return(state)


def trend2ISY (self, trend):
    if trend == 'stable':
        return(0)
    elif trend == 'up':
        return(1)
    elif trend =='down':
        return(2)
    else:
        logging.error('unsupported temperature trend: {}'.format(trend))
        return(99)    