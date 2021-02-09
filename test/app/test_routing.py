
import random
import string
from typing import List
import unittest

from bamboo.app import App
from bamboo.endpoint import Endpoint
from bamboo.request import http_get
from bamboo.test import ServerForm, TestExecutor


def rand_string(k: int) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=k))


def rand_strings(num: int) -> List[str]:
    return [rand_string(random.randint(10, 20)) for _ in range(num)]


# Make different uris
URIS = list(set(rand_strings(1000)))
IDEAL_RESNPONSE = "Hello, World".encode()


# Template endpoints
class MockEndpoint(Endpoint):
    
    def do_GET(self) -> None:
        self.send_body(IDEAL_RESNPONSE)
        

class TestRouting(unittest.TestCase):
        
    def test_routing(self):
        for i, uri in enumerate(URIS):
            res = http_get(f"http://localhost:{8000 + i}/{uri}")
            self.assertEqual(res.body, IDEAL_RESNPONSE)
            

if __name__ == "__main__":
    forms = []
    for i, uri in enumerate(URIS):
        app = App()
        app.route(uri)(MockEndpoint)
        forms.append(ServerForm("", 8000 + i, app, "test_routing.log"))
    
    executor = TestExecutor(unittest.main)
    executor.add_forms(*forms)
    executor.exec()
