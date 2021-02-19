
import random
import unittest

import bamboo
from bamboo.request import http
from bamboo.util.string import rand_string
from bamboo.util.time import get_datetime_rfc822


app = bamboo.App()


class InfoResponse(bamboo.JsonApiData):
    
    name: str
    datetime: str


@app.route(bamboo.AnyStringLocation(), "info")
class InfoEndpoint(bamboo.Endpoint):
    
    @bamboo.data_format(input=None, output=InfoResponse)
    def do_GET(self) -> None:
        name, = self.flexible_locs
        
        body = {"name": name, "datetime": get_datetime_rfc822()}
        self.send_json(body)
        
        
class CalculationResult(bamboo.JsonApiData):

    result: int
        
        
@app.route(bamboo.AsciiDigitLocation(10), 
           bamboo.AsciiDigitLocation(10),
           "multiply")
class MultiplyEndpoint(bamboo.Endpoint):
    
    @bamboo.data_format(input=None, output=CalculationResult)
    def do_GET(self) -> None:
        num_1, num_2 = self.flexible_locs
        
        body = {"result": int(num_1) * int(num_2)}
        self.send_json(body)
        
        
class FlexibleLocsTest(unittest.TestCase):
    
    def setUp(self) -> None:
        form = bamboo.ServerForm("", 8000, app, "test_flexible_locs.log")
        self.executor = bamboo.TestExecutor(form)
        self.executor.start_serve()
    
    def tearDown(self) -> None:
        self.executor.close()
        
    def test_info(self):
        names = [rand_string(10) for _ in range(100)]
        
        for name in names:
            res = http.get(f"http://localhost:8000/{name}/info",
                           datacls=InfoResponse)
            if res.ok:
                body = res.attach()
                self.assertEqual(body.name, name)
            else:
                print(f"Request failed. Status code: {res.status}")
                
    def test_multiply(self):
        get_num = lambda: random.randint(10**9, 10**10 - 1)
        num_pairs = [(get_num(), get_num()) for _ in range(100)]
        
        for num_1, num_2 in num_pairs:
            res = http.get(f"http://localhost:8000/{num_1}/{num_2}/multiply",
                           datacls=CalculationResult)
            if res.ok:
                body = res.attach()
                self.assertEqual(body.result, num_1 * num_2)
            else:
                print(f"Request failed. Status code: {res.status}")
                
                
if __name__ == "__main__":
    unittest.main()
