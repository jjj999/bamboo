

from dataclasses import dataclass
from multiprocessing import Process
import signal
import sys
import time
from typing import Any, Callable, List, Tuple
from wsgiref.simple_server import make_server

from bamboo.app import App


@dataclass
class ServerForm:
    
    hostname: str
    port: int
    app: App
    path_log: str
    
    
def serve_at(form: ServerForm) -> None:
    server = make_server(form.hostname, form.port, form.app)
    f_log = open(form.path_log, "wt")
    sys.stdout = f_log
    sys.stderr = f_log
    
    def server_close(signalnum, frame):
        server.server_close()
        print()
        f_log.close()
        sys.exit()
    
    signal.signal(signal.SIGTERM, server_close)
    server.serve_forever()


class TestExecutor:
    
    def __init__(self, f_client: Callable[[Tuple[Any, ...]], None], 
                 args: Tuple[Any, ...] = ()) -> None:
        self._f_client = f_client
        self._args = args
        self._forms: List[ServerForm] = []
    
    def add_forms(self, *forms: ServerForm) -> None:
        for form in forms:
            self._forms.append(form)
            
    def exec(self) -> None:
        children: List[Process] = []
        for form in self._forms:
            child = Process(target=serve_at, args=(form,))
            children.append(child)
            child.start()
            
        try:
            # Sleep until all server will launch
            time.sleep(0.005)
            self._f_client(*self._args)
        finally:
            for child in children:
                child.terminate()
                child.join()
                child.close()
