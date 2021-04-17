from __future__ import annotations
from dataclasses import dataclass
from multiprocessing import Process
import signal
import sys
import time
from typing import (
    Any,
    Callable,
    List,
    Optional,
    Tuple,
)
from wsgiref import simple_server

from bamboo.app import WSGIApp
from bamboo.util.string import ColorCode, insert_colorcode


__all__ = []


@dataclass
class WSGIServerForm:
    """Dataclass to register a server form.

    This dataclass would be used to register as a form
    into test classes such as WSGITestExecutor.

    Args:
        host: Hostname of the server.
        port: Port of the server.
        app: WSGIApp object with implemented Endpoints.
        path_log: Path log of the server will be written.
    """
    host: str
    port: int
    app: WSGIApp
    path_log: str


def serve_at(form: WSGIServerForm) -> None:
    """Subroutine for server application called at a child process.

    Args:
        form: Dataclass describing information of the server application.
    """
    server = simple_server.make_server(form.host, form.port, form.app)
    f_log = open(form.path_log, "wt")
    sys.stdout = f_log
    sys.stderr = f_log

    def server_close(signalnum, frame):
        print()
        f_log.flush()
        f_log.close()
        sys.exit()

    signal.signal(signal.SIGTERM, server_close)
    signal.signal(signal.SIGINT, server_close)
    server.serve_forever()


class WSGITestExecutor:
    """Utility class that can execute server applications at child processes.

    This class can be used in test scripts for holding several server forms
    and running the application based on the forms at the child processes.
    Also this object has feature of context manager and developers may use
    it to kill the processes safely.
    """

    def __init__(self, *forms: WSGIServerForm) -> None:
        """
        Args:
            *forms: Dataclass describing information of
                the server application.
        """
        self._forms: List[WSGIServerForm] = []
        self._children: List[Process] = []

        self.add_forms(*forms)

    def add_forms(self, *forms: WSGIServerForm) -> None:
        """Add forms with information of server applications.

        Args:
            *foms: Dataclass describing information of
                the server application
        """
        for form in forms:
            self._forms.append(form)

    def start_serve(self, waiting: float = 0.05) -> WSGITestExecutor:
        """Run registered server applications at child processes.

        This object has feature of context manager and the method
        returns the object itself. So developer can use the with
        sentence and in it, can define logic of clients.

        Args:
        waiting: Waiting time after running the processes.

        Returns:
            This object itself.

        Examples:
            ```python
            >>> holder = WSGITestExecutor(form)
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

        Args:
            pop: If the registered forms is to be removed.
        """
        for child in self._children:
            child.terminate()
            child.join()
            child.close()

        if pop:
            self._children.clear()

    def exec(
        self,
        func: Callable[[Tuple[Any, ...]], None],
        args: Tuple[Any, ...] = (),
        waiting: float = 0.1,
    ) -> None:
        """Executes a simple client-server test.

        Args:
            func: Function executed after all the server applications start.
            args: Arguments of the func.
            waiting: Waiting time after running the applications.
        """
        with self.start_serve(waiting=waiting):
            func(*args)

    @staticmethod
    def debug(
        app: WSGIApp,
        host: str = "localhost",
        port: int = 8000,
    ) -> None:
        """Executes a server application for debug.

        This method is a kind of shorcut for launching a server application
        and can be used to debug the application. If you want to deploy an
        application made with Bamboo, consider to use another WSGI server
        application for production.

        Args:
            app: WSGIApp object with implemented Endpoints.
            host: Hostname of the server.
            port: Port of the server.
        """
        server = simple_server.make_server(host, port, app)

        try:
            print(f"Hosting on {host}:{port} ...")
            print(insert_colorcode(
                "WARNING: This is debug mode. "
                "Do not use it in your production deployment.",
                ColorCode.RED
            ))

            server.serve_forever()
        except KeyboardInterrupt:
            server.server_close()
            print()

    def __enter__(self) -> None:
        pass

    def __exit__(self, type, value, traceback) -> None:
        self.close()
