

import requests


res = requests.get("http://localhost:8000/elephant.jpg")

with open("recieved.jpg", "wb") as f:
    f.write(res.content)
