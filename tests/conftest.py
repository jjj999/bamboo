from pathlib import Path
import shutil
from types import ModuleType

import pytest

from . import make_test_data


INTEGRATION_FILES = {
    "tests/tests_app/test_asgi_app.py",
    "tests/tests_app/test_flexible_locs.py",
    "tests/tests_app/test_grafting.py",
    "tests/tests_app/test_wsgi_app.py",
    "tests/tests_endpoint/test_asgi_send_api.py",
    "tests/tests_endpoint/test_asgi_sending_file.py",
    "tests/tests_endpoint/test_wsgi_send_api.py",
    "tests/tests_endpoint/test_wsgi_sending_file.py",
    "tests/tests_endpoint/test_wsgi_sending_generator.py",
    "tests/tests_error/tests_errinfo.py",
    "tests/tests_request/test_http_request.py",
    "tests/tests_request/test_response.py",
    "tests/tests_router/test_routing.py",
    "tests/tests_sticky/http/test_sticky_basic_auth.py",
    "tests/tests_sticky/http/test_sticky_bearer_auth.py",
    "tests/tests_sticky/http/test_sticky_data_format.py",
    "tests/tests_sticky/http/test_sticky_has_header_of.py",
    "tests/tests_sticky/http/test_sticky_has_query_of.py",
    "tests/tests_sticky/http/test_sticky_restricts_client.py",
    "tests/tests_test/test_test_executor.py",
}

TRANSFER_TEST_MODULES = {
    "tests.tests_endpoint.test_asgi_sending_file",
    "tests.tests_endpoint.test_wsgi_sending_file",
    "tests.tests_endpoint.test_wsgi_sending_generator",
}


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        relative_path = Path(item.path).relative_to(config.rootpath).as_posix()
        if relative_path in INTEGRATION_FILES:
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)

        if item.module.__name__ in TRANSFER_TEST_MODULES and item.name == "test_big":
            item.add_marker(pytest.mark.slow)


@pytest.fixture(scope="module", autouse=True)
def generated_transfer_data(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
):
    module = request.module
    if module.__name__ not in TRANSFER_TEST_MODULES:
        yield
        return

    paths = make_test_data(tmp_path_factory.mktemp(module.__name__.replace(".", "-")))
    replacements = {
        "PATH_BIGDATA_1KB": str(paths.small),
        "PATH_BIGDATA_1MB": str(paths.medium),
        "PATH_BIGDATA_1GB": str(paths.large),
    }
    originals = {name: getattr(module, name) for name in replacements}
    _set_module_attributes(module, replacements)
    yield
    _set_module_attributes(module, originals)
    shutil.rmtree(paths.small.parent)


@pytest.fixture(autouse=True)
def generated_large_transfer_data(request: pytest.FixtureRequest):
    module = request.module
    if request.node.get_closest_marker("slow") is None:
        yield
        return

    path = Path(module.PATH_BIGDATA_1GB)
    with path.open("wb") as large:
        large.truncate(10**9)
    yield
    path.unlink(missing_ok=True)


def _set_module_attributes(module: ModuleType, values: dict[str, object]) -> None:
    for name, value in values.items():
        setattr(module, name, value)
