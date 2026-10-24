#!/usr/bin/env python3
"""
Polyglot v3 node server Netatmo Weather Station status
This project is based on the "udi-owm-poly" code from Bob Paauwe (https://github.com/bpaauwe/udi-owm-poly/)
and uses the "lnetatmo" library from Philippe Larduinat (https://github.com/philippelt/netatmo-api-python)
Copyright (C) 2021 Daniel Caldentey
"""
import logging
import os
import sys
import json
import math
import lnetatmo

__version__ = '1.4.0'

# Fallback dummy udi_interface for standalone execution, CI, and test environments
class _FallbackLogger:
    def info(self, msg, *args, **kwargs): logging.info(str(msg), *args, **kwargs)
    def debug(self, msg, *args, **kwargs): logging.debug(str(msg), *args, **kwargs)
    def error(self, msg, *args, **kwargs): logging.error(str(msg), *args, **kwargs)
    def warning(self, msg, *args, **kwargs): logging.warning(str(msg), *args, **kwargs)

class _FallbackNode:
    def __init__(self, poly, primary, address, name):
        self.poly = poly
        self.primary = primary
        self.address = address
        self.name = name
        self.driver_values = {}
    def setDriver(self, driver, value, report=True, force=False, uom=None):
        self.driver_values[driver] = value
    def reportDrivers(self):
        pass

class _FallbackCustom(dict):
    def __init__(self, poly=None, custom=None, *args, **kwargs):
        super().__init__()
        self.poly = poly
        self.custom = custom
    def clear(self):
        super().clear()
    def load(self, data):
        self.update(data or {})

class _FallbackInterface:
    START = 'start'
    STOP = 'stop'
    CUSTOMPARAMS = 'customparams'
    POLL = 'poll'
    CONFIGDONE = 'config_done'
    DISCOVER = 'discover'

    def __init__(self, classes=None, options=None):
        self.classes = classes or []
        self.options = options or {}
        self.name = 'Netatmo'
        self.version = None
        self.callbacks = []
        self.subscribers = {}
        self.nodes = {}
        self.custom_params = {}
        self.Notices = _FallbackCustom()

    def subscribe(self, event, callback, *args):
        self.subscribers.setdefault(event, []).append(callback)

    def start(self, options=None):
        if isinstance(options, dict):
            self.version = options.get('version')
        else:
            self.version = options

    def ready(self):
        pass

    def updateProfile(self):
        return True

    def installprofile(self):
        return True

    def setCustomParams(self, params):
        self.custom_params.update(params)

    def setCustomParamsDoc(self):
        pass

    def addNode(self, node, conn_status=None, rename=False):
        self.nodes[node.address] = node
        return node

    def restart(self):
        pass

    def runForever(self):
        pass

    def onConfig(self, callback):
        self.callbacks.append(callback)

class _FallbackUDIInterface:
    LOGGER = _FallbackLogger()
    Node = _FallbackNode
    Interface = _FallbackInterface
    Custom = _FallbackCustom
    Controller = None

# Backward compatibility alias
_FallbackPolyinterface = _FallbackUDIInterface

try:
    from udi_interface import Interface, Node, LOGGER, Custom
except ImportError:
    Interface = _FallbackInterface
    Node = _FallbackNode
    LOGGER = _FallbackLogger()
    Custom = _FallbackCustom

def round_half_up(num, decimals = 0):
    temp_dec = 10 ** decimals
    result = num * temp_dec
    result = math.floor(result + 0.5)
    result = result / temp_dec
    return result

def get_temperature(temp_value):
    try:
        temp_value = temp_value / 5
        temp_value = temp_value * 9
        temp_value = temp_value + 32
        temp_value = round_half_up(temp_value,1)
        return temp_value
    except:
        LOGGER.info('Failed to convert temperature')
    return 0

def get_pressure(pressure_value):
    try:
        pressure_value = pressure_value * 0.02953
        pressure_value = round_half_up(pressure_value,2)
        return pressure_value
    except:
        LOGGER.info('Failed to convert pressure')
    return 0


class Controller(Node):
    id = 'NETATMO'
    def __init__(self, polyglot, primary='netatmo_ws', address='netatmo_ws', name='Netatmo Weather Station'):
        super(Controller, self).__init__(polyglot, primary, address, name)
        self.poly = polyglot
        self.name = name
        self.address = address
        self.primary = primary
        self.configured = False
        self.myConfig = {}
        self.clientId = ''
        self.clientSecret = ''
        self.connected = False
        self.session = None
        self.weatherStation = None
        self.lastData = None
        self.nodes = {}
        self.polyConfig = {'customParams': {}}
        self.custom_params = {}
        self.notices_removed = False
        self.version = __version__
        self._startup_completed = False

        self.Parameters = Custom(self.poly, 'customparams') if hasattr(self.poly, 'subscribe') else {}
        self.Notices = getattr(self.poly, 'Notices', None) or (Custom(self.poly, 'notices') if hasattr(self.poly, 'subscribe') else {})

        LOGGER.debug('[__init__] Subscribing to polyglot events')
        if hasattr(self.poly, 'subscribe'):
            self.poly.subscribe(getattr(self.poly, 'START', 'start'), self.start)
            self.poly.subscribe(getattr(self.poly, 'STOP', 'stop'), self.stop)
            self.poly.subscribe(getattr(self.poly, 'CUSTOMPARAMS', 'customparams'), self.process_config)
            self.poly.subscribe(getattr(self.poly, 'POLL', 'poll'), self.poll)
            if hasattr(self.poly, 'CONFIGDONE'):
                self.poly.subscribe(self.poly.CONFIGDONE, self.config_done)
            if hasattr(self.poly, 'DISCOVER'):
                self.poly.subscribe(self.poly.DISCOVER, self.discover)

        if hasattr(self.poly, 'onConfig'):
            self.poly.onConfig(self.process_config)

        if hasattr(self.poly, 'updateProfile'):
            try:
                self.poly.updateProfile()
            except Exception:
                pass

        LOGGER.info('[__init__] Registering Netatmo Controller node')
        if hasattr(self.poly, 'addNode'):
            try:
                self.poly.addNode(self, conn_status='ST')
            except TypeError:
                self.poly.addNode(self)
        self.nodes[self.address] = self

        LOGGER.info('[__init__] Signaling polyglot ready')
        if hasattr(self.poly, 'ready'):
            self.poly.ready()

    def poll(self, flag):
        if not self._startup_completed:
            self._run_startup_once('POLL')
        if flag == 'shortPoll':
            self.shortPoll()
        elif flag == 'longPoll':
            self.longPoll()

    def config_done(self, *_args, **_kwargs):
        LOGGER.debug('Configuration done event received')
        if not self._startup_completed:
            self._run_startup_once('CONFIGDONE')

    # Process changes to customParameters
    def process_config(self, config):
        if not config:
            return
        params = config.get('customParams', config) if isinstance(config, dict) else {}
        if hasattr(self, 'Parameters') and hasattr(self.Parameters, 'load'):
            self.Parameters.load(params)

        # Check if anything we care about was changed...
        if params != self.myConfig:
            changed = False

            if 'ClientID' in self.myConfig:
                if self.myConfig['ClientID'] != params.get('ClientID'):
                    changed = True
            elif 'ClientID' in params:
                if params.get('ClientID') != "":
                    changed = True

            if 'ClientSecret' in self.myConfig:
                if self.myConfig['ClientSecret'] != params.get('ClientSecret'):
                    changed = True
            elif 'ClientSecret' in params:
                if params.get('ClientSecret') != "":
                    changed = True

            self.myConfig = dict(params)
            if changed:
                self.clientId = params.get('ClientID', '')
                self.clientSecret = params.get('ClientSecret', '')
                if self.clientId and self.clientSecret:
                    self.configured = True
                else:
                    self.configured = False
                self.removeNoticesAll()
                if self.configured and self._startup_completed:
                    try:
                        self.session = lnetatmo.ClientAuth(clientId=self.clientId, clientSecret=self.clientSecret)
                    except Exception as ex:
                        LOGGER.info(f'ClientAuth failed: {ex}')
                self.discover()

    def start(self, *_args, **_kwargs):
        LOGGER.info(f'Starting Netatmo node server v{__version__}')
        self._run_startup_once('START')

    def _run_startup_once(self, source='START'):
        if self._startup_completed:
            return
        LOGGER.info(f'Running Netatmo startup via {source}')
        self.check_params()
        if self.configured and self.clientId and self.clientSecret:
            try:
                self.session = lnetatmo.ClientAuth(clientId=self.clientId, clientSecret=self.clientSecret)
                self.discover()
            except Exception as ex:
                LOGGER.error(f'Authentication or discovery failed during startup: {ex}')
        else:
            LOGGER.warning('Netatmo controller is not configured yet. Please configure ClientID and ClientSecret.')
        self._startup_completed = True
        LOGGER.info('Node server started')

    def longPoll(self):
        pass

    def shortPoll(self):
        if not self.configured:
            LOGGER.info('Skipping shortPoll because controller is not configured yet.')
            return

        try:
            self.weatherStation = lnetatmo.WeatherStationData(self.session)
        except Exception as ex:
            LOGGER.error(f'Authentication or data retrieval failed: {ex} - Restarting NodeServer')
            self.poly.restart()
            return

        if not self.weatherStation:
            LOGGER.warning('No weather station data object available')
            return

        self.lastData = self.weatherStation.lastData()
        if not self.lastData:
            LOGGER.warning('No module data available in lastData')
            return

        for node in self.nodes:
            if self.nodes[node].id != 'NETATMO':
                self.nodes[node].weatherStation = self.weatherStation
                self.nodes[node].lastData = self.lastData
                self.nodes[node].get_status(False)

    def query(self):
        LOGGER.info('QUERY Controller')
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, *args, **kwargs):
        # Discover the list of available modules and create the right node
        # for each.
        LOGGER.info("In Discovery...")
        if not self.configured:
            LOGGER.info('Skipping connection because we aren\'t configured yet.')
            return

        try:
            self.weatherStation = lnetatmo.WeatherStationData(self.session)
            self.lastData = self.weatherStation.lastData()
            LOGGER.info('Weather Station Name = ' + self.weatherStation.default_home)
            i = 0
            nodeAddress = ''
            for moduleName in sorted(self.lastData.keys()):
                LOGGER.info('Module name = ' + moduleName)
                if 'Noise' in self.lastData[moduleName]:
                    #Master Module
                    nodeAddress = 'netwsmain'
                    weatherStation_node = mainModuleNode(self.poly, self.address, nodeAddress, moduleName)
                    LOGGER.info('Master Module')
                elif 'CO2' in self.lastData[moduleName]:
                    #Indoor Module: prefer deterministic address derived from hardware ID
                    mod = None
                    if hasattr(self.weatherStation, 'moduleByName'):
                        try:
                            mod = self.weatherStation.moduleByName(moduleName)
                        except Exception:
                            mod = None
                    if mod and '_id' in mod:
                        clean_id = mod['_id'].replace(':', '').lower()
                        nodeAddress = 'nwin' + clean_id[-6:]
                    else:
                        nodeAddress = 'netwsin' + str(i)
                    weatherStation_node = indoorModuleNode(self.poly, self.address, nodeAddress, moduleName)
                    LOGGER.info(f'Indoor Module: {moduleName} -> {nodeAddress}')
                    i = i + 1
                elif 'Temperature' in self.lastData[moduleName]:
                    #Outside Module
                    nodeAddress = 'netwsout'
                    weatherStation_node = outdoorModuleNode(self.poly, self.address, nodeAddress, moduleName)
                    LOGGER.info('Outside Module')
                elif 'WindStrength' in self.lastData[moduleName]:
                    #Wind Module
                    nodeAddress = 'netwswind'
                    weatherStation_node = windModuleNode(self.poly, self.address, nodeAddress, moduleName)
                    LOGGER.info('Wind Module')
                elif 'Rain' in self.lastData[moduleName]:
                    #Rain Module
                    nodeAddress = 'netwsrain'
                    weatherStation_node = rainModuleNode(self.poly, self.address, nodeAddress, moduleName)
                    LOGGER.info('Rain Module')
                else:
                    LOGGER.info('Unidentified Module')

                weatherStation_node.lastData = self.lastData
                weatherStation_node.name = moduleName
                self.addNode(weatherStation_node)
                self.nodes[nodeAddress].get_status(True)

        except Exception as ex:
            LOGGER.error(f'Authentication failed or error during discovery: {ex}')
            

    # Delete the node server from Polyglot
    def delete(self):
        LOGGER.info('Removing node server')

    def stop(self):
        LOGGER.info('Stopping node server')
        try:
            self.session.logout()
        except:
            LOGGER.debug('session logout failed')

    def update_profile(self, command=None):
        LOGGER.info('UPDATE PROFILE Controller')
        if hasattr(self.poly, 'updateProfile'):
            return self.poly.updateProfile()
        elif hasattr(self.poly, 'installprofile'):
            return self.poly.installprofile()
        return True

    def check_params(self):
        LOGGER.info('CHECK PARAMS Controller')
        self.configured = True

        custom_params = {}
        if hasattr(self, 'Parameters') and isinstance(self.Parameters, dict) and self.Parameters:
            custom_params = dict(self.Parameters)
        elif hasattr(self, 'myConfig') and self.myConfig:
            custom_params = dict(self.myConfig)
        elif hasattr(self, 'polyConfig') and isinstance(self.polyConfig, dict) and 'customParams' in self.polyConfig:
            custom_params = self.polyConfig['customParams']
        elif hasattr(self.poly, 'config') and isinstance(self.poly.config, dict) and 'customParams' in self.poly.config:
            custom_params = self.poly.config['customParams']

        if 'ClientID' in custom_params:
            self.clientId = custom_params['ClientID']

        if 'ClientSecret' in custom_params:
            self.clientSecret = custom_params['ClientSecret']

        if hasattr(self.poly, 'setCustomParams'):
            try:
                self.poly.setCustomParams({
                    'ClientID': self.clientId,
                    'ClientSecret': self.clientSecret
                })
            except Exception:
                pass
        elif hasattr(self, 'addCustomParam'):
            try:
                self.addCustomParam({
                    'ClientID': self.clientId,
                    'ClientSecret': self.clientSecret
                })
            except Exception:
                pass

        self.custom_params = {
            'ClientID': self.clientId,
            'ClientSecret': self.clientSecret
        }

        if self.clientId == '' or self.clientSecret == '':
            self.configured = False

        self.removeNoticesAll()

    def removeNoticesAll(self):
        self.notices_removed = True
        if hasattr(self.poly, 'Notices') and hasattr(self.poly.Notices, 'clear'):
            self.poly.Notices.clear()

    def addNode(self, node):
        self.nodes[node.address] = node
        if hasattr(self.poly, 'addNode'):
            try:
                self.poly.addNode(node)
            except Exception:
                pass

    def remove_notices_all(self, command=None):
        LOGGER.info('REMOVE NOTICES Controller')
        self.removeNoticesAll()

    def query_all(self, command=None):
        LOGGER.info('Query All')
        self.shortPoll()

    commands = {
            'DISCOVER': discover,
            'UPDATE_PROFILE': update_profile,
            'REMOVE_NOTICES_ALL': remove_notices_all,
            'QUERY_ALL': query_all
            }

    drivers = [
            {'driver': 'ST', 'value': 1, 'uom': 2, 'name': 'NodeServer Online'},
            ]

_FallbackPolyinterface.Controller = Controller

class mainModuleNode(Node):
    id = 'MAINNETATMO'
    name = ''
    lastData = None
    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 2, 'name': 'Connected'},
            {'driver': 'GV0', 'value': 0, 'uom': 17, 'name': 'Temperature'},
            {'driver': 'GV1', 'value': 0, 'uom': 54, 'name': 'CO2'},
            {'driver': 'GV2', 'value': 0, 'uom': 22, 'name': 'Humidity'},
            {'driver': 'GV3', 'value': 0, 'uom': 12, 'name': 'Noise'},
            {'driver': 'GV4', 'value': 0, 'uom': 23, 'name': 'Pressure'},
            {'driver': 'GV5', 'value': 0, 'uom': 23, 'name': 'Absolute Pressure'},
            {'driver': 'GV6', 'value': 0, 'uom': 17, 'name': 'Min Temperature'},
            {'driver': 'GV7', 'value': 0, 'uom': 17, 'name': 'Max Temperature'},
            {'driver': 'GV8', 'value': 0, 'uom': 25, 'name': 'Temperature Trend'},
            {'driver': 'GV9', 'value': 0, 'uom': 25, 'name': 'Pressure Trend'},
            {'driver': 'GV10', 'value': 0, 'uom': 56, 'name': 'Timestamp'},
            {'driver': 'GV11', 'value': 0, 'uom': 56, 'name': 'Wi-Fi Status'},
            ]

    def temp_trend(self, json):
        try:
            nodeStat = json['temp_trend']
            if nodeStat == 'stable':
                return 0
            elif nodeStat == 'up':
                return 1
            else:
                return 2
        except:
            LOGGER.info('Failed to parse trend status type.')
        return 99

    def pressure_trend(self, json):
        try:
            nodeStat = json['pressure_trend']
            if nodeStat == 'stable':
                return 0
            elif nodeStat == 'up':
                return 1
            else:
                return 2
        except:
            LOGGER.info('Failed to parse trend status type.')
        return 99

    def get_status(self, first):
        LOGGER.info('GET STATUS Main Module')
        try:
            LOGGER.info('Get Staus - MainModule 1')
            json = self.lastData[self.name]
            LOGGER.debug(json)

            n_tempTrend = self.temp_trend(json)
            n_pressureTrend = self.pressure_trend(json)
            n_temperature = json['Temperature']
            n_temperature = get_temperature(n_temperature)
            n_minTemp = json['min_temp']
            n_minTemp = get_temperature(n_minTemp)
            n_maxTemp = json['max_temp']
            n_maxTemp = get_temperature(n_maxTemp)
            n_pressure = json['Pressure']
            n_pressure = get_pressure(n_pressure)
            n_absolutePressure = json['AbsolutePressure']
            n_absolutePressure = get_pressure(n_absolutePressure)
            try:
                n_status = 1
                n_CO2 = json['CO2']
                n_humidity = json['Humidity']
                n_noise = json['Noise']
                n_when = json['When']
                n_when = n_when / 10
                n_wifiStatus = json['wifi_status']
                LOGGER.info('GET STATUS - TRY All')

                try:
                    LOGGER.info('Writting Drivers - START')
                    self.setDriver('ST', n_status, report=True, force=first)
                    LOGGER.info('Temperature :')
                    LOGGER.info(n_temperature)
                    self.setDriver('GV0', n_temperature, report=True, force=first)
                    self.setDriver('GV1', n_CO2, report=True, force=first)
                    self.setDriver('GV2', n_humidity, report=True, force=first)
                    self.setDriver('GV3', n_noise, report=True, force=first)
                    self.setDriver('GV4', n_pressure, report=True, force=first)
                    self.setDriver('GV5', n_absolutePressure, report=True, force=first)
                    self.setDriver('GV6', n_minTemp, report=True, force=first)
                    self.setDriver('GV7', n_maxTemp, report=True, force=first)
                    self.setDriver('GV8', n_tempTrend, report=True, force=first)
                    self.setDriver('GV9', n_pressureTrend, report=True, force=first)
                    self.setDriver('GV10', n_when, report=True, force=first)
                    self.setDriver('GV11', n_wifiStatus, report=True, force=first)
                    LOGGER.info('Writting Drivers - END')
                except:
                    LOGGER.error('Failed to update node status')
            except:
                LOGGER.error('Failed to parse Netatmo status JSON')

        except Exception as ex:
            LOGGER.info('In exception handler, no data for this node')
            LOGGER.debug('Skipping status: ' + str(ex.args[0]))
            return False
        return True

class indoorModuleNode(Node):
    id = 'INNETATMO'
    name = ''
    lastData = None
    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 2, 'name': 'Connected'},
            {'driver': 'GV0', 'value': 0, 'uom': 17, 'name': 'Temperature'},
            {'driver': 'GV1', 'value': 0, 'uom': 54, 'name': 'CO2'},
            {'driver': 'GV2', 'value': 0, 'uom': 22, 'name': 'Humidity'},
            {'driver': 'GV3', 'value': 0, 'uom': 17, 'name': 'Min Temperature'},
            {'driver': 'GV4', 'value': 0, 'uom': 17, 'name': 'Max Temperature'},
            {'driver': 'GV5', 'value': 0, 'uom': 25, 'name': 'Temperature Trend'},
            {'driver': 'GV6', 'value': 0, 'uom': 56, 'name': 'Timestamp'},
            {'driver': 'GV7', 'value': 0, 'uom': 51, 'name': 'Battery'},
            {'driver': 'GV8', 'value': 0, 'uom': 56, 'name': 'RF Status'},
            ]

    def temp_trend(self, json):
        try:
            name = json['temp_trend']
            if name == 'stable':
                return 0
            elif name == 'up':
                return 1
            else:
                return 2
        except:
            LOGGER.info('Failed to parse trend status type.')
        return 99

    def get_status(self, first):
        LOGGER.info('GET STATUS Indoor Module')
        try:
            json = self.lastData[self.name]
            LOGGER.debug(json)

            n_tempTrend = self.temp_trend(json)
            n_temperature = json['Temperature']
            n_temperature = get_temperature(n_temperature)
            n_minTemp = json['min_temp']
            n_minTemp = get_temperature(n_minTemp)
            n_maxTemp = json['max_temp']
            n_maxTemp = get_temperature(n_maxTemp)

            try:
                n_status = 1
                n_CO2 = json['CO2']
                n_humidity = json['Humidity']
                n_when = json['When']
                n_when = n_when / 10
                n_batteryPercent = json['battery_percent']
                n_rfStatus = json['rf_status']

                try:
                    self.setDriver('ST', n_status, report=True, force=first)
                    self.setDriver('GV0', n_temperature, report=True, force=first)
                    self.setDriver('GV1', n_CO2, report=True, force=first)
                    self.setDriver('GV2', n_humidity, report=True, force=first)
                    self.setDriver('GV3', n_minTemp, report=True, force=first)
                    self.setDriver('GV4', n_maxTemp, report=True, force=first)
                    self.setDriver('GV5', n_tempTrend, report=True, force=first)
                    self.setDriver('GV6', n_when, report=True, force=first)
                    self.setDriver('GV7', n_batteryPercent, report=True, force=first)
                    self.setDriver('GV8', n_rfStatus, report=True, force=first)
                except:
                    LOGGER.error('Failed to update node status')
            except:
                LOGGER.error('Failed to parse Netatmo status JSON')

        except Exception as ex:
            LOGGER.info('In exception handler, node data not found')
            LOGGER.debug('Skipping status: ' + str(ex.args[0]))
            return False
        return True

class outdoorModuleNode(Node):
    id = 'OUTNETATMO'
    name = ''
    lastData = None
    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 2, 'name': 'Connected'},
            {'driver': 'GV0', 'value': 0, 'uom': 17, 'name': 'Temperature'},
            {'driver': 'GV1', 'value': 0, 'uom': 22, 'name': 'Humidity'},
            {'driver': 'GV2', 'value': 0, 'uom': 17, 'name': 'Min Temperature'},
            {'driver': 'GV3', 'value': 0, 'uom': 17, 'name': 'Max Temperature'},
            {'driver': 'GV4', 'value': 0, 'uom': 25, 'name': 'Temperature Trend'},
            {'driver': 'GV5', 'value': 0, 'uom': 56, 'name': 'Timestamp'},
            {'driver': 'GV6', 'value': 0, 'uom': 51, 'name': 'Battery'},
            {'driver': 'GV7', 'value': 0, 'uom': 56, 'name': 'RF Status'},
            ]

    def temp_trend(self, json):
        try:
            name = json['temp_trend']
            if name == 'stable':
                return 0
            elif name == 'up':
                return 1
            else:
                return 2
        except:
            LOGGER.info('Failed to parse trend status type.')
        return 99

    def get_status(self, first):
        LOGGER.info('GET STATUS Outdoor Module')
        try:
            json = self.lastData[self.name]
            LOGGER.debug(json)

            n_tempTrend = self.temp_trend(json)
            n_temperature = json['Temperature']
            n_temperature = get_temperature(n_temperature)
            n_minTemp = json['min_temp']
            n_minTemp = get_temperature(n_minTemp)
            n_maxTemp = json['max_temp']
            n_maxTemp = get_temperature(n_maxTemp)

            try:
                n_status = 1
                n_humidity = json['Humidity']
                n_when = json['When']
                n_when = n_when / 10
                n_batteryPercent = json['battery_percent']
                n_rfStatus = json['rf_status']

                try:
                    self.setDriver('ST', n_status, report=True, force=first)
                    self.setDriver('GV0', n_temperature, report=True, force=first)
                    self.setDriver('GV1', n_humidity, report=True, force=first)
                    self.setDriver('GV2', n_minTemp, report=True, force=first)
                    self.setDriver('GV3', n_maxTemp, report=True, force=first)
                    self.setDriver('GV4', n_tempTrend, report=True, force=first)
                    self.setDriver('GV5', n_when, report=True, force=first)
                    self.setDriver('GV6', n_batteryPercent, report=True, force=first)
                    self.setDriver('GV7', n_rfStatus, report=True, force=first)
                except:
                    LOGGER.error('Failed to update node status')
            except:
                LOGGER.error('Failed to parse Netatmo status JSON')

        except Exception as ex:
            LOGGER.info('In exception handler, node data not found')
            LOGGER.debug('Skipping status: ' + str(ex.args[0]))
            return False
        return True

class windModuleNode(Node):
    id = 'WINDNETATMO'
    name = ''
    lastData = None
    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 2, 'name': 'Connected'},
            {'driver': 'GV0', 'value': 0, 'uom': 48, 'name': 'Wind Strength'},
            {'driver': 'GV1', 'value': 0, 'uom': 76, 'name': 'Wind Angle'},
            {'driver': 'GV2', 'value': 0, 'uom': 48, 'name': 'Gust Strength'},
            {'driver': 'GV3', 'value': 0, 'uom': 76, 'name': 'Gust Angle'},
            {'driver': 'GV4', 'value': 0, 'uom': 48, 'name': 'Max Wind Strength'},
            {'driver': 'GV5', 'value': 0, 'uom': 76, 'name': 'Max Wind Angle'},
            {'driver': 'GV6', 'value': 0, 'uom': 56, 'name': 'Timestamp'},
            {'driver': 'GV7', 'value': 0, 'uom': 51, 'name': 'Battery'},
            {'driver': 'GV8', 'value': 0, 'uom': 56, 'name': 'RF Status'},
            ]

    def get_status(self, first):
        LOGGER.info('GET STATUS Wind Module')
        try:
            json = self.lastData[self.name]
            LOGGER.debug(json)

            try:
                n_status = 1
                n_windStrength = json['WindStrength']
                n_windAngle = json['WindAngle']
                n_gustStrength = json['GustStrength']
                n_gustAngle = json['GustAngle']
                n_maxWindStrength = json['max_wind_str']
                n_maxWindAngle = json['max_wind_angle']
                n_when = json['When']
                n_when = n_when / 10
                n_batteryPercent = json['battery_percent']
                n_rfStatus = json['rf_status']

                try:
                    self.setDriver('ST', n_status, report=True, force=first)
                    self.setDriver('GV0', n_windStrength, report=True, force=first)
                    self.setDriver('GV1', n_windAngle, report=True, force=first)
                    self.setDriver('GV2', n_gustStrength, report=True, force=first)
                    self.setDriver('GV3', n_gustAngle, report=True, force=first)
                    self.setDriver('GV4', n_maxWindStrength, report=True, force=first)
                    self.setDriver('GV5', n_maxWindAngle, report=True, force=first)
                    self.setDriver('GV6', n_when, report=True, force=first)
                    self.setDriver('GV7', n_batteryPercent, report=True, force=first)
                    self.setDriver('GV8', n_rfStatus, report=True, force=first)
                except:
                    LOGGER.error('Failed to update node status')
            except:
                LOGGER.error('Failed to parse Netatmo status JSON')

        except Exception as ex:
            LOGGER.info('In exception handler, node data not found')
            LOGGER.debug('Skipping status: ' + str(ex.args[0]))
            return False
        return True

class rainModuleNode(Node):
    id = 'RAINNETATMO'
    name = ''
    lastData = None
    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 2, 'name': 'Connected'},
            {'driver': 'GV0', 'value': 0, 'uom': 23, 'name': 'Rain'},
            {'driver': 'GV1', 'value': 0, 'uom': 23, 'name': 'Sum Rain 1h'},
            {'driver': 'GV2', 'value': 0, 'uom': 23, 'name': 'Sum Rain 24h'},
            {'driver': 'GV3', 'value': 0, 'uom': 56, 'name': 'Timestamp'},
            {'driver': 'GV4', 'value': 0, 'uom': 51, 'name': 'Battery'},
            {'driver': 'GV5', 'value': 0, 'uom': 56, 'name': 'RF Status'},
            ]

    def get_status(self, first):
        LOGGER.info('GET STATUS Rain Module')
        try:
            json = self.lastData[self.name]
            LOGGER.debug(json)

            try:
                n_status = 1
                n_rain = json['Rain']
                n_rain1h = json['sum_rain_1']
                n_rain24h = json['sum_rain_24']
                n_when = json['When']
                n_when = n_when / 10
                n_batteryPercent = json['battery_percent']
                n_rfStatus = json['rf_status']

                try:
                    self.setDriver('ST', n_status, report=True, force=first)
                    self.setDriver('GV0', n_rain, report=True, force=first)
                    self.setDriver('GV1', n_rain1h, report=True, force=first)
                    self.setDriver('GV2', n_rain24h, report=True, force=first)
                    self.setDriver('GV3', n_when, report=True, force=first)
                    self.setDriver('GV4', n_batteryPercent, report=True, force=first)
                    self.setDriver('GV5', n_rfStatus, report=True, force=first)
                except:
                    LOGGER.error('Failed to update node status')
            except:
                LOGGER.error('Failed to parse Netatmo status JSON')

        except Exception as ex:
            LOGGER.info('In exception handler, node data not found')
            LOGGER.debug('Skipping status: ' + str(ex.args[0]))
            return False
        return True


if __name__ == "__main__":
    try:
        LOGGER.info("=" * 80)
        LOGGER.info(f"Starting Netatmo PG3 Node Server v{__version__}")
        LOGGER.info("=" * 80)

        # In PG3 environment, PG3INIT is passed via os.environ.
        # If running outside PG3 (e.g. standalone test in dev terminal),
        # use the fallback interface instead of crashing on base64 decode of PG3INIT.
        if 'PG3INIT' not in os.environ:
            LOGGER.warning("PG3INIT environment variable is not set.")
            LOGGER.warning("Node server was started outside of Polyglot (PG3) environment.")
            if Interface is not _FallbackInterface:
                LOGGER.info("Using fallback interface for standalone execution.")
                Interface_Cls = _FallbackInterface
            else:
                Interface_Cls = Interface
        else:
            Interface_Cls = Interface

        LOGGER.info("Creating polyglot interface")
        polyglot = Interface_Cls([])

        LOGGER.info("Starting polyglot interface")
        polyglot.start({'version': __version__, 'requestId': True})
        LOGGER.info("Polyglot interface started")

        if hasattr(polyglot, 'setCustomParamsDoc'):
            LOGGER.info("Setting custom params documentation")
            polyglot.setCustomParamsDoc()

        LOGGER.info("Constructing Netatmo Controller node")
        control = Controller(polyglot, 'netatmo_ws', 'netatmo_ws', 'Netatmo Weather Station')
        LOGGER.info("Netatmo Controller constructed successfully")

        if 'PG3INIT' not in os.environ and hasattr(control, 'start'):
            LOGGER.info("Executing standalone startup")
            control.start()

        LOGGER.info("Entering polyglot runForever() loop")
        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        LOGGER.info("Shutdown signal received")
        sys.exit(0)
    except Exception as err:
        LOGGER.error(f"Fatal error in Netatmo node server: {err}", exc_info=True)
        sys.exit(1)
        

