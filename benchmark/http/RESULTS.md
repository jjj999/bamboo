# Latest Benchmark Results

OS: Ubuntu 20.04 TLS
Complete requests: 100 phases, 100 requests/phase

## bamboo
```
$ gunicorn bamboo_test:app
$ python client.py 100 100

Total requests: 100 phases, 100 requests/phase
Requests per second (mean): 580.5889958984944 [/sec]
Seconds per request (mean): 0.0017223888276636094 [sec]
Seconds per request (std): 1.2440019346484671e-09 [sec]
```

## hug
```
$ gunicorn hug_test:__hug_wsgi__
$ python client.py 100 100

Total requests: 100 phases, 100 requests/phase
Requests per second (mean): 510.7856283483159 [/sec]
Seconds per request (mean): 0.001957768473701218 [sec]
Seconds per request (std): 2.2639903664611397e-08 [sec]
```

## flask
```
$ gunicorn flask_test:app
$ python client.py 100 100

Total requests: 100 phases, 100 requests/phase
Requests per second (mean): 499.3675174254088 [/sec]
Seconds per request (mean): 0.002002533134625384 [sec]
Seconds per request (std): 1.5006368118821342e-08 [sec]
```

## falcon
```
$ gunicorn falcon_test:app
$ python client.py 100 100

Total requests: 100 phases, 100 requests/phase
Requests per second (mean): 530.3055677127595 [/sec]
Seconds per request (mean): 0.0018857052629355966 [sec]
Seconds per request (std): 5.92176145172369e-09 [sec]
```

## fastapi
```
$ uvicorn --no-access-log fastapi_test:app
$ python client 100 100

Total requests: 100 phases, 100 requests/phase
Requests per second (mean): 353.96158311635304 [/sec]
Seconds per request (mean): 0.002825165350419634 [sec]
Seconds per request (std): 4.5163463365291354e-08 [sec]
```
