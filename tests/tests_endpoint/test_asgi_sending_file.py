import os
import time
import unittest

from bamboo import (
    ASGIApp,
    ASGIHTTPEndpoint,
)
from bamboo.api import BinaryApiData
from bamboo.request import http
from bamboo.sticky.http import data_format

from .. import (
    NAME_BIGDATA_1GB,
    NAME_BIGDATA_1KB,
    NAME_BIGDATA_1MB,
    PATH_BIGDATA_1GB,
    PATH_BIGDATA_1KB,
    PATH_BIGDATA_1MB,
    get_log_name,
    get_client_log_name
)
from ..asgi_util import ASGIServerForm, ASGITestExecutor


app = ASGIApp()
PATH_SERVER_LOG = get_log_name(__file__)
PATH_CLIENT_LOG = get_client_log_name(__file__)
FILE_CLIENT_LOG = open(PATH_CLIENT_LOG, "wt")


@app.route("small")
class SmallFileServingEndpoint(ASGIHTTPEndpoint):

    @data_format(input=None, output=BinaryApiData)
    async def do_GET(self) -> None:
        self.send_file(PATH_BIGDATA_1KB, NAME_BIGDATA_1KB)


@app.route("medium")
class MediumFileServingEndpoint(ASGIHTTPEndpoint):

    @data_format(input=None, output=BinaryApiData)
    async def do_GET(self) -> None:
        self.send_file(PATH_BIGDATA_1MB, NAME_BIGDATA_1MB)


@app.route("big")
class BigFileServingEndpoint(ASGIHTTPEndpoint):

    @data_format(input=None, output=BinaryApiData)
    async def do_GET(self) -> None:
        self.send_file(PATH_BIGDATA_1GB, NAME_BIGDATA_1GB)


class TestASGISendingFile(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        form = ASGIServerForm("", 8000, app, PATH_SERVER_LOG)
        cls.executor = ASGITestExecutor(form).start_serve()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.executor.close()
        FILE_CLIENT_LOG.close()

    def measure_downloading(self, uri: str, fpath: str) -> None:
        filesize = os.path.getsize(fpath)
        time_init = time.time()
        bufsize = 8192

        with http.get(uri) as res:
            with open(fpath, "rb") as fsrc:
                total = 0
                while True:
                    chunk = res.read(bufsize)
                    chunksize = len(chunk)
                    if not chunk:
                        break

                    total += chunksize
                    chunk_src = fsrc.read(chunksize)
                    self.assertEqual(chunk, chunk_src)
                self.assertEqual(total, filesize)

        time_total = time.time() - time_init
        FILE_CLIENT_LOG.write(
            f"Time of downloading {fpath} : {time_total} sec\n"
        )

    def test_small(self) -> None:
        uri = "http://localhost:8000/small"
        self.measure_downloading(uri, PATH_BIGDATA_1KB)

    def test_medium(self) -> None:
        uri = "http://localhost:8000/medium"
        self.measure_downloading(uri, PATH_BIGDATA_1MB)

    def test_big(self) -> None:
        uri = "http://localhost:8000/big"
        self.measure_downloading(uri, PATH_BIGDATA_1GB)


if __name__ == "__main__":
    unittest.main()
