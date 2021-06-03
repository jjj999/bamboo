import os
import time
import unittest

from bamboo import (
    BinaryApiData,
    WSGIApp,
    WSGIEndpoint,
    WSGIServerForm,
    WSGITestExecutor,
)
from bamboo.request import http
from bamboo.sticky.http import data_format

from . import (
    NAME_BIGDATA_1GB,
    NAME_BIGDATA_1KB,
    NAME_BIGDATA_1MB,
    PATH_BIGDATA_1GB,
    PATH_BIGDATA_1KB,
    PATH_BIGDATA_1MB,
    get_client_log_name,
    get_log_name,
)


app = WSGIApp()
PATH_SERVER_LOG = get_log_name(__file__)
PATH_CLIENT_LOG = get_client_log_name(__file__)
FILE_CLIENT_LOG = open(PATH_CLIENT_LOG, "wt")


def buffering_generator(fpath: str) -> bytes:
    bufsize = 4096
    with open(fpath, "rb") as f:
        while True:
            chunk = f.read(bufsize)
            yield chunk
            if len(chunk) < bufsize:
                break


@app.route("small")
class SmallFileServingEndpoint(WSGIEndpoint):

    @data_format(input=None, output=BinaryApiData)
    def do_GET(self) -> None:
        self.send_body(buffering_generator(PATH_BIGDATA_1KB))


@app.route("medium")
class MediumFileServingEndpoint(WSGIEndpoint):

    @data_format(input=None, output=BinaryApiData)
    def do_GET(self) -> None:
        self.send_body(buffering_generator(PATH_BIGDATA_1MB))


@app.route("big")
class BigFileServingEndpoint(WSGIEndpoint):

    @data_format(input=None, output=BinaryApiData)
    def do_GET(self) -> None:
        self.send_body(buffering_generator(PATH_BIGDATA_1GB))


class WSGISendingFileTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        form = WSGIServerForm("", 8000, app, PATH_SERVER_LOG)
        cls.executor = WSGITestExecutor(form).start_serve()

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
