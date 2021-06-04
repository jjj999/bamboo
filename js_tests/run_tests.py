import http.server
import multiprocessing as mp
from pathlib import Path
import socket
import socketserver
import time
import typing as t
import webbrowser

from bamboo import (
    HTTPStatus,
    JsonApiData,
    WSGIApp,
    WSGIEndpoint,
    WSGITestExecutor,
)
from bamboo.sticky.http import (
    add_preflight,
    allow_simple_access_control,
    data_format,
    set_cookie,
)


HOST_WEB = "localhost"
PORT_WEB = 8000
HOST_APP = "localhost"
PORT_APP = 9000
DIR_WEB = str((Path(__file__).parent / "web").absolute())
app = WSGIApp()


@app.route("cookie")
class TestCookieEndpoint(WSGIEndpoint):

    @set_cookie("bamboo")
    def do_GET(self) -> None:
        pass


@app.route("cors", "simple-request")
class TestCORSSimpleRequestEndpoint(WSGIEndpoint):

    @allow_simple_access_control()
    def do_GET(self, origin: str) -> None:
        assert origin == "http://localhost:8000"
        self.send_body(b"Hello, Client!")


class TestPreFlightRequest(JsonApiData):

    account_id: str
    email_addr: str
    age: int


@app.route("cors", "preflight")
@add_preflight(
    allow_methods=("POST",),
    allow_origins=("http://localhost:8000",)
)
class TestCORSPreFlightEndpoint(WSGIEndpoint):

    @data_format(input=TestPreFlightRequest, output=None)
    def do_POST(self, req: TestPreFlightRequest, origin: str) -> None:
        assert req.account_id == "hogehoge"
        assert origin == "http://localhost:8000"

        self.send_only_status(HTTPStatus.OK)


class WebHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):

    def setup(self) -> None:
        super().setup()

        self.directory = DIR_WEB


class WebServer(socketserver.TCPServer):

    def __init__(
        self,
        server_address: t.Tuple[str, int],
        RequestHandlerClass: t.Callable[..., socketserver.BaseRequestHandler],
        bind_and_activate: bool = True,
    ) -> None:
        socketserver.BaseServer.__init__(
            self,
            server_address,
            RequestHandlerClass,
        )
        self.socket = socket.socket(
            self.address_family,
            self.socket_type,
        )
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if bind_and_activate:
            try:
                self.server_bind()
                self.server_activate()
            except:
                self.server_close()
                raise


def run_app_server() -> None:
    WSGITestExecutor.debug(app, HOST_APP, PORT_APP)


def run_web_server() -> None:
    with WebServer(
        (HOST_WEB, PORT_WEB),
        WebHTTPRequestHandler,
    ) as server:
        server.serve_forever()


def run_servers() -> t.Tuple[mp.Process, mp.Process]:
    ps_app = mp.Process(target=run_app_server)
    ps_app.start()
    ps_web = mp.Process(target=run_web_server)
    ps_web.start()
    time.sleep(0.05)
    return (ps_app, ps_web)


def main() -> None:
    ps_app, ps_web = run_servers()
    webbrowser.open_new(f"http://{HOST_WEB}:{PORT_WEB}")

    try:
        while True:
            time.sleep(10000)
    except KeyboardInterrupt:
        print()
    finally:
        ps_app.terminate()
        ps_web.terminate()
        ps_app.join()
        ps_web.join()
        ps_app.close()
        ps_web.close()


if __name__ == "__main__":
    main()
