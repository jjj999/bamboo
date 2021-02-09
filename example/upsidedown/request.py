
import sys

from bamboo.request import http_get


def request(uri: str, token: str) -> None:
    body = {"token": token}
    res = http_get(uri, json=body)
    
    print("Headers")
    print("-------")
    for k, v in res.headers.items():
        print(f"{k} : {v}")
    print()
    
    print("Bodies")
    print("------")
    for k, v in res.json().items():
        print(f"{k} : {v}")
    print()
    
    
if __name__ == "__main__":
    URI = "http://localhost:8000/upsidedown"
    token = sys.argv[1]
    request(URI, token)
