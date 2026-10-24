"""Unit tests for temperature and pressure conversion functions in mainNetatmo."""
import unittest
from tests.mock_polyinterface import install_mock

install_mock()
import mainNetatmo


class TestConversions(unittest.TestCase):
    def test_round_half_up_positive(self):
        """Verify round_half_up on positive numbers."""
        self.assertEqual(mainNetatmo.round_half_up(1.5, 0), 2.0)
        self.assertEqual(mainNetatmo.round_half_up(1.4, 0), 1.0)
        self.assertEqual(mainNetatmo.round_half_up(1.235, 2), 1.24)
        self.assertEqual(mainNetatmo.round_half_up(1.234, 2), 1.23)
        self.assertEqual(mainNetatmo.round_half_up(0.0, 1), 0.0)

    def test_get_temperature_valid_values(self):
        """Verify Celsius to Fahrenheit temperature conversions."""
        # 0 C = 32 F
        self.assertEqual(mainNetatmo.get_temperature(0), 32.0)
        # 100 C = 212 F
        self.assertEqual(mainNetatmo.get_temperature(100), 212.0)
        # 20 C = 68 F
        self.assertEqual(mainNetatmo.get_temperature(20), 68.0)
        # 21.5 C = 70.7 F
        self.assertEqual(mainNetatmo.get_temperature(21.5), 70.7)
        # -40 C = -40 F
        self.assertEqual(mainNetatmo.get_temperature(-40), -40.0)

    def test_get_temperature_invalid_values(self):
        """Verify get_temperature gracefully handles invalid input and returns 0."""
        self.assertEqual(mainNetatmo.get_temperature(None), 0)
        self.assertEqual(mainNetatmo.get_temperature("invalid"), 0)
        self.assertEqual(mainNetatmo.get_temperature([]), 0)

    def test_get_pressure_valid_values(self):
        """Verify mbar/hPa to inHg pressure conversions."""
        # Standard atmospheric pressure ~1013.25 mbar = 29.92 inHg
        self.assertEqual(mainNetatmo.get_pressure(1013.25), 29.92)
        # 1000 mbar * 0.02953 = 29.53 inHg
        self.assertEqual(mainNetatmo.get_pressure(1000), 29.53)
        # 0 mbar = 0.0 inHg
        self.assertEqual(mainNetatmo.get_pressure(0), 0.0)

    def test_get_pressure_invalid_values(self):
        """Verify get_pressure gracefully handles invalid input and returns 0."""
        self.assertEqual(mainNetatmo.get_pressure(None), 0)
        self.assertEqual(mainNetatmo.get_pressure("invalid"), 0)
        self.assertEqual(mainNetatmo.get_pressure({}), 0)


if __name__ == '__main__':
    unittest.main()

