import os
import unittest

from helpers import *


class Tests(unittest.TestCase):

    # integration test
    def test_command(self):
        sub_process = os.popen("python http_log_monitoring.py LOG_FILE.csv")
        result = sub_process.read()
        with open("results.txt", 'r') as file:
            res = file.read()
            self.assertEqual(result, res)
        sub_process.close()

    # using different config for test alerting
    def test_alert(self):
        config = {STATS_TIMESPAN: 1, ALERT_TIMESPAN: 2, TOLERANCE: 0, THRESHOLD: 2}
        al = AnalyzeLogs(config)
        self.assertFalse(al.alert_status)
        al.execute(HttpLog(None, None, None, '1', '/', '200', '1'))
        self.assertFalse(al.alert_status)
        al.execute(HttpLog(None, None, None, '1', '/', '200', '1'))
        self.assertFalse(al.alert_status)
        al.execute(HttpLog(None, None, None, '1', '/', '200', '1'))
        self.assertFalse(al.alert_status)
        al.execute(HttpLog(None, None, None, '1', '/', '200', '1'))
        # Should generate an alert
        self.assertTrue(al.alert_status)
        al.execute(HttpLog(None, None, None, '3', '/', '200', '1'))
        # Should recover from alert
        self.assertFalse(al.alert_status)


if __name__ == '__main__':
    unittest.main()
