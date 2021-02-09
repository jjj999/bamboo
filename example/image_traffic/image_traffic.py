
from bamboo import App, Endpoint, data_format
from bamboo.api import JsonApiData
from bamboo.location import StringLocation
from bamboo.request import http_get
from bamboo.test import ServerForm, TestExecutor
from bamboo.util.convert import encode_binary, decode2binary
from bamboo.util.time import get_datetime_rfc822


app = App()
PATH_IMAGE = "elephant.jpg"


class MockResponseData(JsonApiData):
    
    image: str
    datetime: str


@app.route(StringLocation(), "image", parcel=(PATH_IMAGE,))
class MockServeImageEndpoint(Endpoint):
    """Api class sending useless image to clients."""
    
    def setup(self, path_img: str) -> None:
        self.path_img = path_img
    
    @data_format(input=None, output=MockResponseData)
    def do_GET(self):
        with open(self.path_img, "rb") as f:
            img = f.read()
                        
        body = {
            "image": encode_binary(img),
            "datetime": get_datetime_rfc822()
        }
        
        self.send_json(body)


def request_image(uri: str, path_save: str) -> None:
    res = http_get(uri, datacls=MockResponseData)

    if res.ok:
        data = res.attach()
        print(f"Date time: {data.datetime}")
        print("Saving image in the response...")
        with open(path_save, "wb") as f:
            f.write(decode2binary(data.image))
    else:
        print("Request failed.", end="\n\n")
        print("headers")
        print("-------")
        for key, val in res.headers.items():
            print(f"{key} : {val}")
            

if __name__ == "__main__":
    me = "hoge"
    URI = f"http://localhost:8000/{me}/image"
    PATH_SAVE = "recieved.jpg"
    
    form = ServerForm("", 8000, app, "image_traffic.log")
    executer = TestExecutor(request_image, (URI, PATH_SAVE))
    executer.add_forms(form)
    executer.exec()
