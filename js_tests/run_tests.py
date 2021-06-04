import http.server
import multiprocessing as mp
from pathlib import Path
import socketserver
import time
import typing as t
import webbrowser

from bamboo import (
    WSGIApp,
    WSGIEndpoint,
    WSGITestExecutor,
)
from bamboo.sticky.http import (
    add_preflight,
    allow_simple_access_control,
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


@app.route("cors", "preflight")
@add_preflight(
    allow_methods=("GET", "POST"),
    allow_origins=("http://localhost:9000",)
)
class TestCORSEndpoint(WSGIEndpoint):
    pass


class WebHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):

    def setup(self) -> None:
        super().setup()

        self.directory = DIR_WEB


def run_app_server() -> None:
    WSGITestExecutor.debug(app, HOST_APP, PORT_APP)


def run_web_server() -> None:
    with socketserver.TCPServer(
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
