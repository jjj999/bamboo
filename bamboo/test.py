

from __future__ import annotations
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
    
    
class MultiServerHolder:
    
    def __init__(self, *forms: ServerForm) -> None:
        self._forms: List[ServerForm] = []
        self._children: List[Process] = []

        self.add_forms(*forms)
        
    def add_forms(self, *forms: ServerForm) -> None:
        for form in forms:
            self._forms.append(form)
            
    def start_serve(self, waiting: float = 0.05) -> MultiServerHolder:
        for form in self._forms:
            child = Process(target=serve_at, args=(form,))
            child.start()
            self._children.append(child)
        time.sleep(waiting)
        
        return self
        
    def close(self, pop: bool = True) -> None:
        for child in self._children:
            child.terminate()
            child.join()
            child.close()
            
        if pop:
            self._children.clear()
            
    def __enter__(self) -> None:
        pass
    
    def __exit__(self, type, value, traceback) -> None:
        self.close()


class TestExecutor:
    
    def __init__(self) -> None:
        self._holder = MultiServerHolder()
    
    def add_forms(self, *forms: ServerForm) -> None:
        self._holder.add_forms(*forms)
            
    def exec(self, func: Callable[[Tuple[Any, ...]], None], 
             args: Tuple[Any, ...] = (), waiting: float = 0.05) -> None:
        with self._holder.start_serve(waiting=waiting):
            func(*args)
