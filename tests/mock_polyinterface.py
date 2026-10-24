"""Mock implementation of the polyinterface library for unit testing."""
import sys
import types

class MockLogger:
    def __init__(self):
        self.logs = []

    def clear(self):
        self.logs.clear()

    def info(self, msg, *args):
        self.logs.append(('INFO', str(msg)))

    def debug(self, msg, *args):
        self.logs.append(('DEBUG', str(msg)))

    def error(self, msg, *args):
        self.logs.append(('ERROR', str(msg)))

    def warning(self, msg, *args):
        self.logs.append(('WARNING', str(msg)))


class MockNotices(dict):
    def clear(self):
        super().clear()

    def load(self, data):
        self.update(data or {})


class MockInterface:
    START = 'start'
    STOP = 'stop'
    CUSTOMPARAMS = 'customparams'
    POLL = 'poll'
    CONFIGDONE = 'config_done'
    DISCOVER = 'discover'

    def __init__(self, classes=None, options=None):
        self.classes = classes or []
        self.options = options or {}
        self.name = 'MockNetatmo'
        self.version = None
        self.callbacks = []
        self.subscribers = {}
        self.restarted = False
        self.profile_installed = False
        self.nodes = {}
        self.custom_params = {}
        self.Notices = MockNotices()

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
        self.profile_installed = True
        return True

    def installprofile(self):
        self.profile_installed = True
        return True

    def setCustomParamsDoc(self):
        pass

    def setCustomParams(self, params):
        self.custom_params.update(params)

    def addNode(self, node, conn_status=None, rename=False):
        self.nodes[node.address] = node
        return node

    def restart(self):
        self.restarted = True

    def runForever(self):
        pass

    def onConfig(self, callback):
        self.callbacks.append(callback)


class MockController:
    def __init__(self, polyglot):
        self.poly = polyglot
        self.nodes = {}
        self.polyConfig = {'customParams': {}}
        self.custom_params = {}
        self.notices_removed = False

    def addNode(self, node):
        self.nodes[node.address] = node

    def addCustomParam(self, params):
        self.custom_params.update(params)

    def removeNoticesAll(self):
        self.notices_removed = True

    def runForever(self):
        pass


class MockNode:
    def __init__(self, poly, primary, address, name):
        self.poly = poly
        self.controller = poly
        self.primary = primary
        self.address = address
        self.name = name
        self.driver_values = {}
        self.driver_reports = []
        self.report_drivers_called = False

    def setDriver(self, driver, value, report=True, force=False, uom=None):
        self.driver_values[driver] = value
        self.driver_reports.append({
            'driver': driver,
            'value': value,
            'report': report,
            'force': force,
            'uom': uom
        })

    def reportDrivers(self):
        self.report_drivers_called = True


class MockCustom(dict):
    def __init__(self, poly=None, custom="customparams"):
        super().__init__()
        self.poly = poly
        self.custom = custom

    def load(self, data):
        self.update(data or {})


def install_mock():
    """Install mock polyinterface and udi_interface into sys.modules if not present."""
    logger = MockLogger()
    if 'polyinterface' not in sys.modules:
        mod_p = types.ModuleType('polyinterface')
        mod_p.LOGGER = logger
        mod_p.Interface = MockInterface
        mod_p.Controller = MockController
        mod_p.Node = MockNode
        sys.modules['polyinterface'] = mod_p

    if 'udi_interface' not in sys.modules:
        mod_u = types.ModuleType('udi_interface')
        mod_u.LOGGER = logger
        mod_u.Interface = MockInterface
        mod_u.Node = MockNode
        mod_u.Custom = MockCustom
        sys.modules['udi_interface'] = mod_u
    return sys.modules['polyinterface']

