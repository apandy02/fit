import unittest
from datetime import date, datetime
from unittest.mock import patch

from fit.utils.calendar import get_current_week_dates


class TestCalendar(unittest.TestCase):
    @patch("fit.utils.calendar.datetime")
    def test_get_current_week_dates(self, mock_datetime):
        # Test with a Wednesday (weekday = 2)
        mock_date = datetime(2023, 11, 15)  # A Wednesday
        mock_datetime.today.return_value = mock_date

        week_dates = get_current_week_dates()

        # Should return 7 dates
        self.assertEqual(len(week_dates), 7)
        # First date should be Sunday (Nov 12)
        self.assertEqual(week_dates[0], date(2023, 11, 12))
        # Last date should be Saturday (Nov 18)
        self.assertEqual(week_dates[-1], date(2023, 11, 18))

        for i in range(1, len(week_dates)):
            self.assertEqual(
                (week_dates[i] - week_dates[i - 1]).days,
                1,
                "Dates should be consecutive",
            )


if __name__ == "__main__":
    unittest.main()
