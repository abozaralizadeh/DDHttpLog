

#HttpLogMonitoring
Simple Python console app to read http log files and produce statistics and alerts.


### Download and install Python 3

[Download Python](https://www.python.org/downloads/)

using homebrew on Mac:
```sh
> brew install python
```
using chocholatory on Windows:
```sh
> choco install python
```
using apt-get on Ubuntu:
```sh
> sudo apt-get install python
```
### Run the console app

```sh
> cd HttpLogMonitoring
> python http_log_monitoring.py LOG_FILE.csv
```
* the csv file should be passed as the last argument
### Run the tests
```sh
> cd HttpLogMonitoring
> python tests.py
```

## How to improve

* Dockerize the app to make it portable and easy to use
* Use a pubsub messaging queue to buffer the live log and handing it to different services 
(statistics, alerting, etc.) to make the application more modular
and scalable.
* Use parallel workers (like celery workers with the chosen technology stack) 
as the consumers of the log stream (statistics, alerting, etc.) 
to provide segregation of duties and modularity.
* Use a time series database (such as influxdb) as the destination of calculated
alerts or aggregated statistic to provide better options for post analysis
instead of the printing results in standard io.


© [Abozar Alizadeh](abozar.alizadeh@gmail.com)