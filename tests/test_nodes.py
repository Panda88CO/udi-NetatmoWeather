"""Unit tests for Netatmo Node classes in mainNetatmo."""
import unittest
from tests.mock_polyinterface import install_mock, MockController, MockInterface

install_mock()
import mainNetatmo


class TestNodes(unittest.TestCase):
    def setUp(self):
        self.mock_interface = MockInterface()
        self.mock_controller = MockController(self.mock_interface)

    def test_node_ids_match_profile_definitions(self):
        """Verify each Node class has an uppercase id without special characters."""
        expected_ids = {
            mainNetatmo.mainModuleNode: 'MAINNETATMO',
            mainNetatmo.indoorModuleNode: 'INNETATMO',
            mainNetatmo.outdoorModuleNode: 'OUTNETATMO',
            mainNetatmo.windModuleNode: 'WINDNETATMO',
            mainNetatmo.rainModuleNode: 'RAINNETATMO',
        }
        for node_cls, expected_id in expected_ids.items():
            with self.subTest(node_class=node_cls.__name__):
                self.assertEqual(node_cls.id, expected_id)

    def test_temp_trend_parsing(self):
        """Verify temp_trend correctly parses 'stable', 'up', 'down', and unknown."""
        node = mainNetatmo.mainModuleNode(self.mock_controller, 'netatmo_ws', 'main_addr', 'Main')
        self.assertEqual(node.temp_trend({'temp_trend': 'stable'}), 0)
        self.assertEqual(node.temp_trend({'temp_trend': 'up'}), 1)
        self.assertEqual(node.temp_trend({'temp_trend': 'down'}), 2)
        self.assertEqual(node.temp_trend({'temp_trend': 'other'}), 2)
        self.assertEqual(node.temp_trend({}), 99)
        self.assertEqual(node.temp_trend(None), 99)

    def test_pressure_trend_parsing(self):
        """Verify pressure_trend correctly parses 'stable', 'up', 'down', and unknown."""
        node = mainNetatmo.mainModuleNode(self.mock_controller, 'netatmo_ws', 'main_addr', 'Main')
        self.assertEqual(node.pressure_trend({'pressure_trend': 'stable'}), 0)
        self.assertEqual(node.pressure_trend({'pressure_trend': 'up'}), 1)
        self.assertEqual(node.pressure_trend({'pressure_trend': 'down'}), 2)
        self.assertEqual(node.pressure_trend({}), 99)

    def test_main_module_get_status(self):
        """Verify mainModuleNode parses all drivers from lastData and calls setDriver."""
        node = mainNetatmo.mainModuleNode(self.mock_controller, 'netatmo_ws', 'netwsmain', 'Main Station')
        node.lastData = {
            'Main Station': {
                'Temperature': 20.0,
                'min_temp': 15.0,
                'max_temp': 25.0,
                'temp_trend': 'stable',
                'Pressure': 1013.25,
                'AbsolutePressure': 1010.0,
                'pressure_trend': 'up',
                'CO2': 450,
                'Humidity': 55,
                'Noise': 38,
                'When': 1600000000,
                'wifi_status': 60
            }
        }
        result = node.get_status(first=True)
        self.assertTrue(result)

        # Check driver values
        self.assertEqual(node.driver_values['ST'], 1)
        self.assertEqual(node.driver_values['GV0'], 68.0)    # 20 C -> 68 F
        self.assertEqual(node.driver_values['GV1'], 450)     # CO2
        self.assertEqual(node.driver_values['GV2'], 55)      # Humidity
        self.assertEqual(node.driver_values['GV3'], 38)      # Noise
        self.assertEqual(node.driver_values['GV4'], 29.92)   # 1013.25 mbar -> 29.92 inHg
        self.assertEqual(node.driver_values['GV5'], 29.83)   # 1010.0 mbar -> 29.83 inHg
        self.assertEqual(node.driver_values['GV6'], 59.0)    # 15 C -> 59 F
        self.assertEqual(node.driver_values['GV7'], 77.0)    # 25 C -> 77 F
        self.assertEqual(node.driver_values['GV8'], 0)       # stable
        self.assertEqual(node.driver_values['GV9'], 1)       # up
        self.assertEqual(node.driver_values['GV10'], 160000000.0)
        self.assertEqual(node.driver_values['GV11'], 60)

    def test_indoor_module_get_status(self):
        """Verify indoorModuleNode parses all drivers from lastData."""
        node = mainNetatmo.indoorModuleNode(self.mock_controller, 'netatmo_ws', 'netwsin0', 'Living Room')
        node.lastData = {
            'Living Room': {
                'Temperature': 21.0,
                'min_temp': 18.0,
                'max_temp': 23.0,
                'temp_trend': 'up',
                'CO2': 600,
                'Humidity': 50,
                'When': 1600000000,
                'battery_percent': 85,
                'rf_status': 70
            }
        }
        result = node.get_status(first=True)
        self.assertTrue(result)
        self.assertEqual(node.driver_values['ST'], 1)
        self.assertEqual(node.driver_values['GV0'], 69.8)
        self.assertEqual(node.driver_values['GV1'], 600)
        self.assertEqual(node.driver_values['GV2'], 50)
        self.assertEqual(node.driver_values['GV3'], 64.4)
        self.assertEqual(node.driver_values['GV4'], 73.4)
        self.assertEqual(node.driver_values['GV5'], 1)
        self.assertEqual(node.driver_values['GV6'], 160000000.0)
        self.assertEqual(node.driver_values['GV7'], 85)
        self.assertEqual(node.driver_values['GV8'], 70)

    def test_outdoor_module_get_status(self):
        """Verify outdoorModuleNode parses all drivers from lastData."""
        node = mainNetatmo.outdoorModuleNode(self.mock_controller, 'netatmo_ws', 'netwsout', 'Outdoor')
        node.lastData = {
            'Outdoor': {
                'Temperature': 10.0,
                'min_temp': 5.0,
                'max_temp': 15.0,
                'temp_trend': 'down',
                'Humidity': 80,
                'When': 1600000000,
                'battery_percent': 90,
                'rf_status': 65
            }
        }
        result = node.get_status(first=False)
        self.assertTrue(result)
        self.assertEqual(node.driver_values['ST'], 1)
        self.assertEqual(node.driver_values['GV0'], 50.0)
        self.assertEqual(node.driver_values['GV1'], 80)
        self.assertEqual(node.driver_values['GV2'], 41.0)
        self.assertEqual(node.driver_values['GV3'], 59.0)
        self.assertEqual(node.driver_values['GV4'], 2)
        self.assertEqual(node.driver_values['GV5'], 160000000.0)
        self.assertEqual(node.driver_values['GV6'], 90)
        self.assertEqual(node.driver_values['GV7'], 65)

    def test_wind_module_get_status(self):
        """Verify windModuleNode parses all drivers from lastData."""
        node = mainNetatmo.windModuleNode(self.mock_controller, 'netatmo_ws', 'netwswind', 'Wind Gauge')
        node.lastData = {
            'Wind Gauge': {
                'WindStrength': 12,
                'WindAngle': 180,
                'GustStrength': 25,
                'GustAngle': 190,
                'max_wind_str': 30,
                'max_wind_angle': 200,
                'When': 1600000000,
                'battery_percent': 75,
                'rf_status': 55
            }
        }
        result = node.get_status(first=True)
        self.assertTrue(result)
        self.assertEqual(node.driver_values['ST'], 1)
        self.assertEqual(node.driver_values['GV0'], 12)
        self.assertEqual(node.driver_values['GV1'], 180)
        self.assertEqual(node.driver_values['GV2'], 25)
        self.assertEqual(node.driver_values['GV3'], 190)
        self.assertEqual(node.driver_values['GV4'], 30)
        self.assertEqual(node.driver_values['GV5'], 200)
        self.assertEqual(node.driver_values['GV6'], 160000000.0)
        self.assertEqual(node.driver_values['GV7'], 75)
        self.assertEqual(node.driver_values['GV8'], 55)

    def test_rain_module_get_status(self):
        """Verify rainModuleNode parses all drivers from lastData."""
        node = mainNetatmo.rainModuleNode(self.mock_controller, 'netatmo_ws', 'netwsrain', 'Rain Gauge')
        node.lastData = {
            'Rain Gauge': {
                'Rain': 0.5,
                'sum_rain_1': 1.2,
                'sum_rain_24': 5.8,
                'When': 1600000000,
                'battery_percent': 95,
                'rf_status': 72
            }
        }
        result = node.get_status(first=True)
        self.assertTrue(result)
        self.assertEqual(node.driver_values['ST'], 1)
        self.assertEqual(node.driver_values['GV0'], 0.5)
        self.assertEqual(node.driver_values['GV1'], 1.2)
        self.assertEqual(node.driver_values['GV2'], 5.8)
        self.assertEqual(node.driver_values['GV3'], 160000000.0)
        self.assertEqual(node.driver_values['GV4'], 95)
        self.assertEqual(node.driver_values['GV5'], 72)

    def test_node_get_status_missing_from_last_data(self):
        """Verify node returns False gracefully when its name is not in lastData."""
        node = mainNetatmo.rainModuleNode(self.mock_controller, 'netatmo_ws', 'netwsrain', 'Missing Gauge')
        node.lastData = {'Other Device': {}}
        result = node.get_status(first=True)
        self.assertFalse(result)

    def test_drivers_structure_and_names(self):
        """Verify all node classes define drivers with driver, value, uom, and name."""
        all_node_classes = [
            mainNetatmo.Controller,
            mainNetatmo.mainModuleNode,
            mainNetatmo.indoorModuleNode,
            mainNetatmo.outdoorModuleNode,
            mainNetatmo.windModuleNode,
            mainNetatmo.rainModuleNode,
        ]
        for node_cls in all_node_classes:
            with self.subTest(node_class=node_cls.__name__):
                self.assertTrue(hasattr(node_cls, 'drivers'))
                self.assertGreater(len(node_cls.drivers), 0)
                for d in node_cls.drivers:
                    self.assertIn('driver', d)
                    self.assertIn('value', d)
                    self.assertIn('uom', d)
                    self.assertIn('name', d)
                    self.assertIsInstance(d['name'], str)
                    self.assertGreater(len(d['name']), 0)


if __name__ == '__main__':
    unittest.main()

