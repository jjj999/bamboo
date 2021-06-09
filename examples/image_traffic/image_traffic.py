from bamboo import (
    AnyStringLocation,
    JsonApiData,
    WSGIApp,
    WSGIEndpoint,
    WSGIServerForm,
    WSGITestExecutor
)
from bamboo.request import http
from bamboo.sticky.http import data_format
from bamboo.util.convert import encode_binary, decode2binary
from bamboo.util.time import get_datetime_rfc822


app = WSGIApp()


class MockResponseData(JsonApiData):

    image: str
    datetime: str


@app.route(AnyStringLocation(), "image")
class MockServeImageEndpoint(WSGIEndpoint):
    """Api class sending useless image to clients."""

    def setup(self, path_img: str) -> None:
        self.path_img = path_img

    @data_format(input=None, output=MockResponseData)
    def do_GET(self):
        with open(self.path_img, "rb") as f:
            img = f.read()

        self.send_json(MockResponseData(
            image=encode_binary(img),
            datetime=get_datetime_rfc822(),
        ))


def request_image(uri: str, path_save: str) -> None:
    res = http.get(uri, datacls=MockResponseData)

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
    PATH_IMAGE = "elephant.jpg"
    PATH_SAVE = "received.jpg"

    app.set_parcel(MockServeImageEndpoint, PATH_IMAGE)

    form = WSGIServerForm("", 8000, app, "image_traffic.log")
    executer = WSGITestExecutor(form)
    executer.exec(request_image, (URI, PATH_SAVE))
