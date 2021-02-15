

import glob
import os
from typing import Any, Callable, Dict, List, Set, Type

from bamboo.app import App
from bamboo.endpoint import Endpoint
from bamboo.location import Location


def get_all_files(dir: str) -> Set[str]:
    paths = glob.glob(os.path.join(dir, "**"), recursive=True)
    return set(os.path.abspath(p) for p in paths if os.path.isfile(p))


class CommonNasEndpoint(Endpoint):
    
    def setup(self, file_path: str) -> None:
        self.file_path = file_path
    
    def do_GET(self) -> None:
        with open(self.file_path, "rb") as f:
            data = f.read()
            
        self.send_body(data)


class SimpleNasApp(App):
    
    def __init__(self, doc_root: str, 
                 endpoint: Type[CommonNasEndpoint]) -> None:
        super().__init__()  
        
        if doc_root[-1] == "/":
            doc_root = doc_root[:-1]
        
        self._doc_root = os.path.abspath(doc_root)
        self._endpoint = endpoint
        self._files = get_all_files(self._doc_root)
        self._restricted_files: Set[str] = set()
                
    def __call__(self, environ: Dict[str, Any], 
                 start_response: Callable) -> List[bytes]:
        method = environ.get("REQUEST_METHOD").upper()
        path = self._doc_root + environ.get("PATH_INFO")
        if path in self._restricted_files:
            return [self.send_404(start_response)]
            
        if path in self._files:
            endpoint = self._endpoint(environ, path)
            callback = self._endpoint._get_response_method(method)
            if callback is None:
                return [self.send_404(start_response)]
            
            callback(endpoint)
            start_response(endpoint._status.value, endpoint._headers)
            return [endpoint._res_body]
        
        # If no resources found, try to call other callbacks.
        return super().__call__(environ, start_response)

    def restrict_uri(self, *locs: Location) -> None:
        path = os.path.join(self._doc_root, "/".join(locs))
        self._restricted_files.add(path)
