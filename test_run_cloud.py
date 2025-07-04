import unittest

# Copied from run_cloud.py to avoid modal import issues for this specific test
def _check_rain(rain_values):
    """Analyze rain forecast values to determine current and upcoming rain conditions.

    This function takes a list of rain intensity values and checks two conditions:
    1. If it's currently raining by checking the first two time periods
    2. If it will rain soon by calculating the average of the next three time periods

    Args:
        rain_values (list): A list of integers representing rain intensity values
                          for 5 consecutive time periods. Each value represents
                          the rain intensity where 0 means no rain and higher
                          values indicate more intense rain.

    Returns:
        bool: True if either:
              - It is currently raining (any value > 0 in first 2 periods), or
              - It will rain soon (average of next 3 periods > 10)
             False otherwise.

    Note:
        The function assumes the input list contains exactly 5 values, where:
        - First 2 values represent current/very near future
        - Last 3 values represent upcoming forecast
    """
    if rain_values is None:
        # print("Warning: No rain data available. Assuming no rain and taking no action.") # Silenced for tests
        return False  # Do nothing if rain data is unavailable

    # Check if it's currently raining (first 2 time periods)
    rain_now = any(value > 0 for value in rain_values[:2])

    # Check if it will rain soon (next 3 time periods)
    # Added a check for len to prevent ZeroDivisionError if rain_values[2:5] is empty
    # although the function spec implies rain_values will have 5 elements if not None.
    # However, for robustness in testing and general use, this is a good addition.
    relevant_values_for_soon = rain_values[2:5]
    if not relevant_values_for_soon: # handles cases like rain_values = [0,0]
        average_rain_soon = 0
    else:
        average_rain_soon = sum(relevant_values_for_soon) / len(relevant_values_for_soon)

    rain_soon = average_rain_soon > 10

    # print(f"Is it raining? [{rain_now > 0}]. Will it rain soon? [{rain_soon}]") # Silenced for tests
    return rain_now or rain_soon

class TestCheckRain(unittest.TestCase):

    def test_check_rain_with_none_values(self):
        """
        Test _check_rain when rain_values is None.
        It should return False (do nothing as per new requirement).
        """
        self.assertFalse(_check_rain(None), "Should return False when rain_values is None")

    def test_check_rain_with_no_rain(self):
        """
        Test _check_rain with no current or upcoming rain.
        """
        rain_values = [0, 0, 0, 0, 0]
        self.assertFalse(_check_rain(rain_values), "Should return False when no rain is forecast")

    def test_check_rain_with_current_rain(self):
        """
        Test _check_rain when it is currently raining.
        """
        rain_values_period1 = [10, 0, 0, 0, 0] # Rain in the first period
        self.assertTrue(_check_rain(rain_values_period1), "Should return True when currently raining (period 1)")

        rain_values_period2 = [0, 10, 0, 0, 0] # Rain in the second period
        self.assertTrue(_check_rain(rain_values_period2), "Should return True when currently raining (period 2)")

    def test_check_rain_with_upcoming_rain_significant(self):
        """
        Test _check_rain when significant rain is upcoming.
        Average of next 3 periods > 10.
        """
        # Average is (20+20+20)/3 = 20, which is > 10
        rain_values = [0, 0, 20, 20, 20]
        self.assertTrue(_check_rain(rain_values), "Should return True when significant rain is upcoming")

    def test_check_rain_with_upcoming_rain_not_significant(self):
        """
        Test _check_rain when upcoming rain is not significant.
        Average of next 3 periods <= 10.
        """
        # Average is (5+5+5)/3 = 5, which is not > 10
        rain_values = [0, 0, 5, 5, 5]
        self.assertFalse(_check_rain(rain_values), "Should return False when upcoming rain is not significant")

    def test_check_rain_with_fewer_than_5_values_but_not_none(self):
        """
        Test _check_rain with a list that has fewer than 5 values.
        It should handle this gracefully due to the added check for relevant_values_for_soon.
        """
        rain_values_short1 = [0, 0] # No rain, list too short for 'soon' calculation
        self.assertFalse(_check_rain(rain_values_short1), "Should be False, not enough data for 'soon' but no current rain")

        rain_values_short2 = [10, 0] # Current rain, list too short for 'soon'
        self.assertTrue(_check_rain(rain_values_short2), "Should be True due to current rain")

        rain_values_empty = [] # Empty list
        self.assertFalse(_check_rain(rain_values_empty), "Should be False for empty list")

    def test_check_rain_with_exactly_3_values_for_soon_calc(self):
        """
        Test edge case for 'soon' calculation part.
        """
        # Average is (10+10+11)/3 = 10.333 > 10
        rain_values = [0,0,10,10,11]
        self.assertTrue(_check_rain(rain_values), "Should be True as average is just over 10")

        # Average is (10+10+10)/3 = 10, which is not > 10
        rain_values_edge = [0,0,10,10,10]
        self.assertFalse(_check_rain(rain_values_edge), "Should be False as average is exactly 10")


if __name__ == '__main__':
    # To make output cleaner during tests, _check_rain's prints can be silenced
    # or redirected if necessary. For now, this is fine.
    unittest.main()
