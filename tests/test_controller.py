"""Unit tests for the Controller class in mainNetatmo."""
import unittest
from unittest.mock import MagicMock, patch
from tests.mock_polyinterface import install_mock, MockInterface

install_mock()
import mainNetatmo


class TestController(unittest.TestCase):
    def setUp(self):
        self.mock_interface = MockInterface()
        self.controller = mainNetatmo.Controller(self.mock_interface)

    def test_controller_initial_state(self):
        """Verify Controller initializes with expected default attributes and NodeDef ID."""
        self.assertEqual(self.controller.id, 'NETATMO')
        self.assertEqual(self.controller.address, 'netatmo_ws')
        self.assertEqual(self.controller.primary, 'netatmo_ws')
        self.assertEqual(self.controller.version, mainNetatmo.__version__)
        self.assertEqual(self.controller.version, '1.3.0')
        self.assertFalse(self.controller.configured)
        self.assertEqual(self.controller.clientId, '')
        self.assertEqual(self.controller.clientSecret, '')

    def test_polyglot_start_version(self):
        """Verify polyglot.start accepts and stores __version__."""
        poly = MockInterface('Netatmo')
        poly.start(mainNetatmo.__version__)
        self.assertEqual(poly.version, '1.3.0')

        fb = mainNetatmo._FallbackInterface('Netatmo')
        fb.start(mainNetatmo.__version__)
        self.assertEqual(fb.version, '1.3.0')

    def test_check_params_unconfigured(self):
        """Verify check_params sets configured to False when credentials are empty."""
        self.controller.polyConfig = {'customParams': {}}
        self.controller.check_params()
        self.assertFalse(self.controller.configured)
        self.assertTrue(self.controller.notices_removed)

    def test_check_params_configured(self):
        """Verify check_params sets configured to True when all required credentials are present."""
        self.controller.polyConfig = {
            'customParams': {
                'ClientID': 'client_id_123',
                'ClientSecret': 'client_secret_abc'
            }
        }
        self.controller.check_params()
        self.assertTrue(self.controller.configured)
        self.assertEqual(self.controller.clientId, 'client_id_123')
        self.assertEqual(self.controller.clientSecret, 'client_secret_abc')
        self.assertEqual(self.controller.custom_params['ClientID'], 'client_id_123')

    def test_process_config_triggers_discovery_on_change(self):
        """Verify process_config detects parameter changes and triggers discover()."""
        config = {
            'customParams': {
                'ClientID': 'newclient',
                'ClientSecret': 'newsecret'
            }
        }
        with patch.object(self.controller, 'discover') as mock_discover:
            self.controller.process_config(config)
            self.assertTrue(self.controller.configured)
            self.assertEqual(self.controller.clientId, 'newclient')
            mock_discover.assert_called_once()

    def test_process_config_no_change_does_not_discover(self):
        """Verify process_config does not re-discover if customParams haven't changed."""
        initial_params = {
            'ClientID': 'sameclient',
            'ClientSecret': 'samesecret'
        }
        self.controller.myConfig = initial_params.copy()
        config = {'customParams': initial_params.copy()}
        with patch.object(self.controller, 'discover') as mock_discover:
            self.controller.process_config(config)
            mock_discover.assert_not_called()

    def test_discover_unconfigured_skips(self):
        """Verify discover() returns early if controller is not configured."""
        self.controller.configured = False
        with patch('lnetatmo.WeatherStationData') as mock_ws:
            self.controller.discover()
            mock_ws.assert_not_called()

    def test_discover_identifies_and_adds_all_module_types(self):
        """Verify discover() correctly identifies and instantiates each module node type."""
        self.controller.configured = True
        mock_ws_data = MagicMock()
        mock_ws_data.default_home = 'MyHome'
        mock_ws_data.lastData.return_value = {
            'Master Module': {
                'Noise': 40,
                'Temperature': 22,
                'Pressure': 1013,
                'AbsolutePressure': 1010,
                'min_temp': 18,
                'max_temp': 24,
                'temp_trend': 'stable',
                'pressure_trend': 'stable',
                'CO2': 500,
                'Humidity': 45,
                'When': 1600000000,
                'wifi_status': 70
            },
            'Bedroom Module': {
                'CO2': 450,
                'Temperature': 20,
                'min_temp': 17,
                'max_temp': 22,
                'temp_trend': 'stable',
                'Humidity': 50,
                'When': 1600000000,
                'battery_percent': 90,
                'rf_status': 80
            },
            'Outdoor Module': {
                'Temperature': 15,
                'min_temp': 10,
                'max_temp': 18,
                'temp_trend': 'up',
                'Humidity': 75,
                'When': 1600000000,
                'battery_percent': 85,
                'rf_status': 75
            },
            'Wind Gauge': {
                'WindStrength': 10,
                'WindAngle': 90,
                'GustStrength': 15,
                'GustAngle': 95,
                'max_wind_str': 20,
                'max_wind_angle': 100,
                'When': 1600000000,
                'battery_percent': 95,
                'rf_status': 85
            },
            'Rain Gauge': {
                'Rain': 0.0,
                'sum_rain_1': 0.0,
                'sum_rain_24': 1.5,
                'When': 1600000000,
                'battery_percent': 92,
                'rf_status': 88
            }
        }

        with patch('lnetatmo.WeatherStationData', return_value=mock_ws_data):
            self.controller.discover()

            # Verify all 5 expected node addresses exist
            self.assertIn('netwsmain', self.controller.nodes)
            self.assertIn('netwsin0', self.controller.nodes)
            self.assertIn('netwsout', self.controller.nodes)
            self.assertIn('netwswind', self.controller.nodes)
            self.assertIn('netwsrain', self.controller.nodes)

            # Verify classes
            self.assertIsInstance(self.controller.nodes['netwsmain'], mainNetatmo.mainModuleNode)
            self.assertIsInstance(self.controller.nodes['netwsin0'], mainNetatmo.indoorModuleNode)
            self.assertIsInstance(self.controller.nodes['netwsout'], mainNetatmo.outdoorModuleNode)
            self.assertIsInstance(self.controller.nodes['netwswind'], mainNetatmo.windModuleNode)
            self.assertIsInstance(self.controller.nodes['netwsrain'], mainNetatmo.rainModuleNode)

    def test_query_reports_all_drivers(self):
        """Verify query() calls reportDrivers on all nodes."""
        node1 = MagicMock()
        node2 = MagicMock()
        self.controller.nodes = {'n1': node1, 'n2': node2}
        self.controller.query()
        node1.reportDrivers.assert_called_once()
        node2.reportDrivers.assert_called_once()

    def test_discover_indoor_module_with_hardware_id(self):
        """Verify discover() derives deterministic indoor address from module _id."""
        self.controller.configured = True
        mock_ws_data = MagicMock()
        mock_ws_data.default_home = 'MyHome'
        mock_ws_data.lastData.return_value = {
            'Bedroom Module': {
                'CO2': 450,
                'Temperature': 20,
                'min_temp': 17,
                'max_temp': 22,
                'temp_trend': 'stable',
                'Humidity': 50,
                'When': 1600000000,
                'battery_percent': 90,
                'rf_status': 80
            }
        }
        mock_ws_data.moduleByName.return_value = {'_id': '03:00:00:1a:2b:3c'}

        with patch('lnetatmo.WeatherStationData', return_value=mock_ws_data):
            self.controller.discover()
            self.assertIn('nwin1a2b3c', self.controller.nodes)
            self.assertIsInstance(self.controller.nodes['nwin1a2b3c'], mainNetatmo.indoorModuleNode)

    def test_short_poll_unconfigured_skips(self):
        """Verify shortPoll() returns early without doing anything when unconfigured."""
        self.controller.configured = False
        with patch('lnetatmo.WeatherStationData') as mock_ws:
            self.controller.shortPoll()
            mock_ws.assert_not_called()
            self.assertFalse(self.mock_interface.restarted)

    def test_short_poll_auth_failure_calls_restart_and_returns(self):
        """Verify shortPoll() triggers restart and returns immediately on auth error without crashing."""
        self.controller.configured = True
        self.controller.weatherStation = None
        with patch('lnetatmo.WeatherStationData', side_effect=Exception("Token expired")):
            self.controller.shortPoll()
            self.assertTrue(self.mock_interface.restarted)
            self.assertIsNone(self.controller.lastData)

    def test_short_poll_empty_last_data_returns_safely(self):
        """Verify shortPoll() safely handles empty lastData without crashing."""
        self.controller.configured = True
        mock_ws = MagicMock()
        mock_ws.lastData.return_value = None
        with patch('lnetatmo.WeatherStationData', return_value=mock_ws):
            self.controller.shortPoll()
            self.assertIsNone(self.controller.lastData)

    def test_short_poll_successful_updates_child_nodes(self):
        """Verify shortPoll() fetches lastData and updates all child nodes."""
        self.controller.configured = True
        child_node = MagicMock()
        child_node.id = 'MAINNETATMO'
        self.controller.nodes = {'netwsmain': child_node}

        mock_ws = MagicMock()
        mock_data = {'Main Station': {'Temperature': 21}}
        mock_ws.lastData.return_value = mock_data

        with patch('lnetatmo.WeatherStationData', return_value=mock_ws):
            self.controller.shortPoll()
            self.assertEqual(self.controller.lastData, mock_data)
            child_node.get_status.assert_called_once_with(False)

    def test_fallback_polyinterface_attributes(self):
        """Verify fallback polyinterface provides expected Controller, Node, Interface, and LOGGER."""
        fallback = mainNetatmo._FallbackPolyinterface()
        self.assertTrue(hasattr(fallback, 'LOGGER'))
        self.assertTrue(hasattr(fallback, 'Controller'))
        self.assertTrue(hasattr(fallback, 'Node'))
        self.assertTrue(hasattr(fallback, 'Interface'))

    def test_update_profile(self):
        """Verify update_profile calls poly.installprofile()."""
        res = self.controller.update_profile({})
        self.assertTrue(res)
        self.assertTrue(self.mock_interface.profile_installed)


if __name__ == '__main__':
    unittest.main()

