

from bamboo.request import http


res = http.get("http://localhost:8000/elephant.jpg")

with open("recieved.jpg", "wb") as f:
    f.write(res.body)
