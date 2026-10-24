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


class MockInterface:
    def __init__(self, name='MockNetatmo'):
        self.name = name
        self.version = None
        self.callbacks = []
        self.restarted = False
        self.profile_installed = False

    def start(self, version=None):
        self.version = version

    def restart(self):
        self.restarted = True

    def installprofile(self):
        self.profile_installed = True
        return True

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
    def __init__(self, controller, primary, address, name):
        self.controller = controller
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


def install_mock():
    """Install mock polyinterface into sys.modules if not present."""
    if 'polyinterface' not in sys.modules:
        mod = types.ModuleType('polyinterface')
        mod.LOGGER = MockLogger()
        mod.Interface = MockInterface
        mod.Controller = MockController
        mod.Node = MockNode
        sys.modules['polyinterface'] = mod
    return sys.modules['polyinterface']

