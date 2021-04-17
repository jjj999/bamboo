from __future__ import annotations
from dataclasses import dataclass
from multiprocessing import Process
import os
import signal
import sys
import time
from typing import (
    Any,
    Callable,
    List,
    Tuple,
)

from bamboo import (
    ASGIHTTPApp,
)
from bamboo.util.string import ColorCode, insert_colorcode
import uvicorn


__all__ = [
    "ASGIHTTPServerForm",
    "ASGIHTTPTestExecutor",
]


@dataclass
class ASGIHTTPServerForm:

    host: str
    port: int
    app: ASGIHTTPApp
    path_log: str


def serve_at(form: ASGIHTTPServerForm) -> None:
    f_log = open(form.path_log, "wt")
    sys.stdout = f_log
    sys.stdin = f_log

    if not len(form.host):
        form.host = "localhost"
    uvicorn.run(
        form.app,
        host=form.host,
        port=form.port,
        log_level="debug"
    )


class ASGIHTTPTestExecutor:

    def __init__(self, *forms: ASGIHTTPServerForm) -> None:
        self._forms: List[ASGIHTTPServerForm] = []
        self._children: List[Process] = []

        self.add_forms(*forms)

    def add_forms(self, *forms: ASGIHTTPServerForm) -> None:
        for form in forms:
            self._forms.append(form)

    def start_serve(self, waiting: float = 0.1) -> ASGIHTTPTestExecutor:
        for form in self._forms:
            child = Process(target=serve_at, args=(form,))
            child.start()
            self._children.append(child)
        time.sleep(waiting)

        return self

    def close(self, pop: bool = True) -> None:
        for child in self._children:
            os.kill(child.pid, signal.SIGINT)
            child.join()
            child.close()

        if pop:
            self._children.clear()

    def exec(
        self,
        func: Callable[[Tuple[Any, ...]], None],
        args: Tuple[Any, ...] = (),
        waiting: float = 0.05
    ) -> None:
        with self.start_serve(waiting=waiting):
            func(*args)

    @classmethod
    def debug(
        cls,
        app: ASGIHTTPApp,
        path_log: str,
        host: str = "localhost",
        port: int = 8000,
        waiting: float = 0.05
    ) -> None:
        form = ASGIHTTPServerForm(host, port, app, path_log)
        executor = cls(form)

        try:
            print(f"Hosting on {host}:{port} ...")
            print(insert_colorcode(
                "WARNING: This is debug mode. "
                "Do not use it in your production deployment.",
                ColorCode.RED
            ))

            executor.start_serve(waiting=waiting)
            while True:
                time.sleep(60 * 60)
        finally:
            executor.close()
            print(
                "\nHosting terminated. The log was output into " +
                insert_colorcode(f"{path_log}", ColorCode.YELLOW) + "."
            )

    def __enter__(self) -> None:
        pass

    def __exit__(self, type, value, traceback) -> None:
        self.close()
