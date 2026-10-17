from pathlib import Path

from bamboo import WSGIServerForm, WSGITestExecutor
from bamboo.request import http

from tests import get_unused_port

from . import ROOT, load_example


def serve(app, tmp_path: Path) -> tuple[WSGITestExecutor, str]:
    port = get_unused_port()
    form = WSGIServerForm("", port, app, str(tmp_path / "server.log"))
    return WSGITestExecutor(form).start_serve(), f"http://localhost:{port}"


def test_upsidedown_round_trip(tmp_path: Path) -> None:
    module = load_example("examples/upsidedown/serve.py", "example_upsidedown_http")
    executor, root = serve(module.app, tmp_path)

    with (
        executor,
        http.get(
            f"{root}/upsidedown",
            json=module.UpsideDownRequest(token="bamboo"),
            datacls=module.UpsideDownResponse,
        ) as response,
    ):
        assert response.ok
        assert response.attach().result == "oobmab"


def test_image_traffic_round_trip(tmp_path: Path) -> None:
    module = load_example(
        "examples/image_traffic/image_traffic.py", "example_image_traffic_http"
    )
    source = ROOT / "examples/image_traffic/elephant.jpg"
    destination = tmp_path / "received.jpg"
    module.app.set_parcel(module.MockServeImageEndpoint, str(source))
    executor, root = serve(module.app, tmp_path)

    with executor:
        module.request_image(f"{root}/example/image", str(destination))

    assert destination.read_bytes() == source.read_bytes()


def test_heroku_hello_round_trip(tmp_path: Path) -> None:
    module = load_example(
        "examples/heroku_deployment/hello.py", "example_heroku_hello_http"
    )
    executor, root = serve(module.app, tmp_path)

    with (
        executor,
        http.get(
            f"{root}/hello",
            datacls=module.HelloData,
        ) as response,
    ):
        assert response.ok
        assert response.attach().text == "Hello, World!"
