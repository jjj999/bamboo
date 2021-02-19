
import json

import requests


def main(root: str):
    URI = f"{root}/hello"
    
    res = requests.get(URI)
    if res.ok:
        body = json.loads(res.content)
        print(f"Response: {body['text']}")
    else:
        print(f"Error occured. Status code: {res.status_code}")
        
        
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    
    args = parser.parse_args()
    if args.debug:
        root = "http://localhost:8000"
    else:
        # TODO EDIT host name
        root = "https://XXXXXXXXXXXXXXXXXXXX.herokuapp.com"

    main(root)
    