# Latest Benchmark Results

OS: Ubuntu 20.04 TLS
Complete requests: 100 phases, 100 requests/phase

## bamboo (WSGI)
```
$ gunicorn bamboo_wsgi:app
$ python client.py 100 100

Total requests: 100 phases, 100 requests/phase
Requests per second (mean): 2005.8498765133447 [/sec]
Seconds per request (mean): 0.0004985417960282468 [sec]
Seconds per request (std): 1.6899379221741875e-09 [sec]
```

## bamboo (ASGI)
```
$ uvicorn bamboo_asgi:app --no-access-log
$ python client.py 100 100

Total requests: 100 phases, 100 requests/phase
Requests per second (mean): 1453.0483550805898 [/sec]
Seconds per request (mean): 0.0006882083424846089 [sec]
Seconds per request (std): 1.8897657861733784e-09 [sec]
```

## hug
```
$ gunicorn hug_wsgi:__hug_wsgi__
$ python client.py 100 100

Total requests: 100 phases, 100 requests/phase
Requests per second (mean): 1745.4486345569906 [/sec]
Seconds per request (mean): 0.0005729186068278706 [sec]
Seconds per request (std): 2.070883862028278e-09 [sec]
```

## flask
```
$ gunicorn flask_wsgi:app
$ python client.py 100 100

Total requests: 100 phases, 100 requests/phase
Requests per second (mean): 1590.3612998733486 [/sec]
Seconds per request (mean): 0.0006287879364768477 [sec]
Seconds per request (std): 1.6086186966284083e-09 [sec]
```

## falcon
```
$ gunicorn falcon_wsgi:app
$ python client.py 100 100

Total requests: 100 phases, 100 requests/phase
Requests per second (mean): 2044.2043251515033 [/sec]
Seconds per request (mean): 0.0004891878897310749 [sec]
Seconds per request (std): 2.2220663306521826e-09 [sec]
```

## fastapi
```
$ uvicorn --no-access-log fastapi_asgi:app
$ python client 100 100

Total requests: 100 phases, 100 requests/phase
Requests per second (mean): 1031.6064678455925 [/sec]
Seconds per request (mean): 0.0009693618944522521 [sec]
Seconds per request (std): 3.996070093344434e-09 [sec]
```
