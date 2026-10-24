"""Unit tests for the lnetatmo client library."""
import unittest
from unittest.mock import MagicMock, patch
import lnetatmo


class TestLNetatmo(unittest.TestCase):
    def test_custom_exceptions(self):
        """Verify custom exception classes can be instantiated and caught."""
        with self.assertRaises(lnetatmo.NoDevice):
            raise lnetatmo.NoDevice("Device not found")
        with self.assertRaises(lnetatmo.NoHome):
            raise lnetatmo.NoHome("Home not found")
        with self.assertRaises(lnetatmo.AuthFailure):
            raise lnetatmo.AuthFailure("Authentication failed")

    def test_today_stamps(self):
        """Verify todayStamps returns a valid tuple of start and end timestamps."""
        start, end = lnetatmo.todayStamps()
        self.assertIsInstance(start, int)
        self.assertIsInstance(end, int)
        self.assertGreater(end, start)
        self.assertEqual(end - start, 86400)

    @patch('lnetatmo.postRequest')
    def test_weather_station_data_init_and_last_data(self, mock_post):
        """Verify WeatherStationData initialization and lastData() processing."""
        mock_post.return_value = {
            'body': {
                'devices': [
                    {
                        '_id': '70:ee:50:00:11:22',
                        'station_name': 'Home Station',
                        'home_name': 'My Home',
                        'module_name': 'Main Living',
                        'wifi_status': 55,
                        'dashboard_data': {
                            'time_utc': 1600000000,
                            'Temperature': 21.5,
                            'Humidity': 50,
                            'Pressure': 1012.0
                        },
                        'modules': [
                            {
                                '_id': '02:00:00:11:22:33',
                                'module_name': 'Balcony',
                                'battery_percent': 80,
                                'rf_status': 60,
                                'dashboard_data': {
                                    'time_utc': 1600000000,
                                    'Temperature': 14.2,
                                    'Humidity': 75
                                }
                            },
                            {
                                '_id': '03:00:00:11:22:33',
                                'module_name': 'Lost Module'
                                # No dashboard_data (simulating disconnected module)
                            }
                        ]
                    }
                ],
                'user': {
                    'mail': 'test@example.com',
                    'administrative': {
                        'unit': 0,
                        'windunit': 0,
                        'pressureunit': 0,
                        'lang': 'en-US'
                    }
                }
            }
        }

        mock_auth = MagicMock()
        mock_auth.accessToken = 'test_token'

        ws = lnetatmo.WeatherStationData(mock_auth)
        self.assertEqual(ws.default_home, 'My Home')
        self.assertEqual(ws.default_station, 'Home Station')
        self.assertIn('02:00:00:11:22:33', ws.modules)
        self.assertEqual(ws.user.mail, 'test@example.com')

        # Test station and module lookups
        self.assertIsNotNone(ws.stationByName('Home Station'))
        self.assertIsNone(ws.stationByName('Nonexistent Station'))
        self.assertIsNotNone(ws.moduleByName('Balcony'))
        self.assertIsNone(ws.moduleByName('Nonexistent Module'))

        # Test lastData()
        last_d = ws.lastData()
        self.assertIn('Main Living', last_d)
        self.assertIn('Balcony', last_d)
        # Verify lost module without dashboard_data is excluded
        self.assertNotIn('Lost Module', last_d)

        # Verify dashboard data structure
        self.assertEqual(last_d['Main Living']['Temperature'], 21.5)
        self.assertEqual(last_d['Main Living']['wifi_status'], 55)
        self.assertEqual(last_d['Main Living']['When'], 1600000000)

        self.assertEqual(last_d['Balcony']['Temperature'], 14.2)
        self.assertEqual(last_d['Balcony']['battery_percent'], 80)
        self.assertEqual(last_d['Balcony']['rf_status'], 60)

    @patch('lnetatmo.postRequest')
    def test_weather_station_data_no_devices_raises(self, mock_post):
        """Verify WeatherStationData raises NoDevice when devices list is empty."""
        mock_post.return_value = {
            'body': {
                'devices': [],
                'user': {'mail': 'test@example.com', 'administrative': {}}
            }
        }
        mock_auth = MagicMock()
        mock_auth.accessToken = 'test_token'

        with self.assertRaises(lnetatmo.NoDevice):
            lnetatmo.WeatherStationData(mock_auth)


if __name__ == '__main__':
    unittest.main()

