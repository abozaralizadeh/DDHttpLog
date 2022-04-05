from collections import deque, defaultdict
from models import HttpLog
from datetime import datetime

STATS_TIMESPAN = 'stats_timespan'
ALERT_TIMESPAN = 'alert_timespan'
TOLERANCE = 'tolerance'
THRESHOLD = 'threshold'


class Statistics:

    def __init__(self, time_indicator=None):
        self.time_indicator = time_indicator
        self.total_number_of_calls = 0
        self._stats = defaultdict(int)
        self._status_code = defaultdict(lambda: defaultdict(int))

    def _trace_errors(self, http_log: HttpLog):
        if http_log.status != '200':
            self._status_code[http_log.status][http_log.request] += 1

    def _increment_hits(self, section):
        self._stats[section] += 1

    def _decrement_hits(self, section):
        self._stats[section] -= 1

    def aggregate(self, http_log: HttpLog):
        self._increment_hits(http_log.section)
        self.total_number_of_calls += 1
        self._trace_errors(http_log)

    def detach(self, http_log: HttpLog):
        self._decrement_hits(http_log.section)
        self.total_number_of_calls -= 1

    def get_max_hits(self):
        if not len(self._stats):
            return None, None
        most_visited = max(self._stats, key=self._stats.get)
        number_of_hits = self._stats[most_visited]
        return most_visited, number_of_hits

    def print_statistics(self):
        print("Statistics for the time period starting at", str(datetime.fromtimestamp(self.time_indicator)), ":")
        print("Total number of calls:", self.total_number_of_calls)
        print("The most hit section is {0}, with the total number of {1}".format(*self.get_max_hits()))
        if len(self._status_code):
            print("Errors:")
            for k in sorted(self._status_code):
                print("Http error", k, " in the following requests:")
                for v in sorted(self._status_code[k].items(), key=lambda item: item[1], reverse=True):
                    print(v)
            print('\n')


class AnalyzeLogs:

    def __init__(self, config=None):
        if config is None:
            # tolerance is used to accept and process out of order data arrival
            config = {STATS_TIMESPAN: 10, ALERT_TIMESPAN: 2 * 60, TOLERANCE: 1, THRESHOLD: 10}
        self._stats_queue = deque()
        self._alert_queue = deque()
        self.config = config
        self.first_iteration = True
        self.alert_statistic = Statistics()
        self.alert_status = False

    def execute(self, http_log: HttpLog):
        self._manage_queues(http_log)

    def _manage_queues(self, http_log: HttpLog):
        self._manage_stat_queue(http_log)
        self._manage_alert_queue(http_log)

    def _find_statistic_pack(self, http_log: HttpLog):
        for q in self._stats_queue:
            if http_log.timestamp - q.time_indicator < self.config[STATS_TIMESPAN]:
                return q
        return None

    def _creating_missing_statistic_pack(self, http_log: HttpLog):
        latest_timestamp = self._stats_queue[-1].time_indicator
        # in case of gaps between logs we should still create statistics for the missing the period of time
        while http_log.timestamp - latest_timestamp > self.config[STATS_TIMESPAN]:
            latest_timestamp += self.config[STATS_TIMESPAN]
            stat_pack = Statistics(latest_timestamp)
            self._stats_queue.append(stat_pack)
        stat_pack = Statistics(latest_timestamp + self.config[STATS_TIMESPAN])
        self._stats_queue.append(stat_pack)
        self.first_iteration = False
        return stat_pack

    def _publish_statistic_packs(self, http_log: HttpLog):
        new_log_oldest_delta = http_log.timestamp - self._stats_queue[0].time_indicator
        while new_log_oldest_delta > self.config[STATS_TIMESPAN] + self.config[TOLERANCE] \
                and len(self._stats_queue):
            stat_result = self._stats_queue.popleft()
            new_log_oldest_delta = http_log.timestamp - self._stats_queue[0].time_indicator
            stat_result.print_statistics()

    def _correct_first_static_pack(self, http_log: HttpLog):
        stat_pack = self._stats_queue[0].time_indicator = http_log.timestamp

    def _manage_stat_queue(self, new_log: HttpLog):
        # first iteration
        if not len(self._stats_queue):
            self._stats_queue.append(Statistics(new_log.timestamp))

        stat_pack = self._stats_queue[0]
        oldest_timestamp = stat_pack.time_indicator
        new_log_delta = new_log.timestamp - oldest_timestamp
        if new_log_delta < 0:
            if self.first_iteration:
                self._correct_first_static_pack(new_log)
            else:
                # drop the data, data loss due to low tolerance, the data arrived too late
                return

        if new_log_delta >= self.config[STATS_TIMESPAN]:
            # finding th right statistic pack
            stat_pack = self._find_statistic_pack(new_log)
            # creating missing statistic packs
            if not stat_pack:
                stat_pack = self._creating_missing_statistic_pack(new_log)
            # publish static packs who meet the tolerance
            self._publish_statistic_packs(new_log)

        # populate statistic pack
        stat_pack.aggregate(new_log)

    def _manage_alert_queue(self, new_log: HttpLog):
        self._alert_queue.append(new_log)
        self.alert_statistic.aggregate(new_log)

        # moving time window based of alert timespan config
        while len(self._alert_queue)\
                and new_log.timestamp - self._alert_queue[0].timestamp >= self.config[ALERT_TIMESPAN]:
            old_log = self._alert_queue.popleft()
            self.alert_statistic.detach(old_log)

        # calculate the total traffic average in the timespan
        total_traffic_average = self.alert_statistic.total_number_of_calls / self.config[ALERT_TIMESPAN]

        # Alert
        if not self.alert_status \
                and total_traffic_average >= self.config[THRESHOLD]:
            print("High traffic generated an alert - hits = {0}, triggered at {1}\n"
                  .format(self.alert_statistic.total_number_of_calls, datetime.fromtimestamp(new_log.timestamp)))
            self.alert_status = True

        # Recover
        if self.alert_status \
                and total_traffic_average < self.config[THRESHOLD]:
            print("Alert recovered\n")
            self.alert_status = False
