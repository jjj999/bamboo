

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
    """Dataclass to register a server form.
    
    This dataclass would be used to register as a form 
    into test classes such as TestExecutor.
    
    Parameters
    ----------
    hostname : str
        Hostname of the server
    port : int
        Port of the server
    app : App
        App object with implemented Endpoints
    path_log : str
        Path log of the server will be written
    """
    hostname: str
    port: int
    app: App
    path_log: str
    
    
def serve_at(form: ServerForm) -> None:
    """Subroutine for server application called at a child process.

    Parameters
    ----------
    form : ServerForm
        Dataclass describing information of the server application
    """
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
    """Utility class that can execute server applications at child processes.
    
    This class can be used in test scripts for holding several server forms 
    and running the application based on the forms at the child processes. 
    Also this object has feature of context manager and developers may use 
    it to kill the processes safely.
    """
    
    def __init__(self, *forms: ServerForm) -> None:
        self._forms: List[ServerForm] = []
        self._children: List[Process] = []

        self.add_forms(*forms)
        
    def add_forms(self, *forms: ServerForm) -> None:
        """Add forms with information of server applications.
        
        Parameters
        ----------
        *foms : ServerForm
            Dataclass describing information of the server application
        """
        for form in forms:
            self._forms.append(form)
            
    def start_serve(self, waiting: float = 0.05) -> TestExecutor:
        """Run registered server applications at child processes.
        
        This object has feature of context manager and the method 
        returns the object itself. So developer can use the with 
        sentence and in it, can define logic of clients.

        Parameters
        ----------
        waiting : float, optional
            Waiting time after running the processes, by default 0.05

        Returns
        -------
        TestExecutor
            This object itself
            
        Examples
        --------
        ```python
        >>> holder = TestExecutor(form)
        >>> with holder.start_serve():
        ...    res = http_get("http://localhost:8000/image")
        >>> print(res.body)
        ```
        """
        for form in self._forms:
            child = Process(target=serve_at, args=(form,))
            child.start()
            self._children.append(child)
        time.sleep(waiting)
        
        return self
        
    def close(self, pop: bool = True) -> None:
        """Kill the all child processes derived from registered forms.

        Parameters
        ----------
        pop : bool, optional
            If removing the registered forms, by default True
        """
        for child in self._children:
            child.terminate()
            child.join()
            child.close()
            
        if pop:
            self._children.clear()
            
    def exec(self, func: Callable[[Tuple[Any, ...]], None], 
             args: Tuple[Any, ...] = (), waiting: float = 0.05) -> None:
        """Executes a simple client-server test.

        Parameters
        ----------
        func : Callable[[Tuple[Any, ...]], None]
            Function executed after all the server applications start
        args : Tuple[Any, ...], optional
            Arguments of the func, by default ()
        waiting : float, optional
            Waiting time after running the applications, by default 0.05
        """
        with self.start_serve(waiting=waiting):
            func(*args)
            
    def __enter__(self) -> None:
        pass
    
    def __exit__(self, type, value, traceback) -> None:
        self.close()
