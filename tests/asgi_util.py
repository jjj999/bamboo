from __future__ import annotations
import dataclasses
import multiprocessing
import os
import signal
import sys
import time
import typing as t

from bamboo import ASGIApp
from bamboo.util.string import ColorCode, insert_colorcode
import uvicorn


@dataclasses.dataclass
class ASGIServerForm:

    host: str
    port: int
    app: ASGIApp
    path_log: str


def serve_at(form: ASGIServerForm) -> None:
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


class ASGITestExecutor:

    def __init__(self, *forms: ASGIServerForm) -> None:
        self._forms: t.List[ASGIServerForm] = []
        self._children: t.List[multiprocessing.Process] = []

        self.add_forms(*forms)

    def add_forms(self, *forms: ASGIServerForm) -> None:
        for form in forms:
            self._forms.append(form)

    def start_serve(self, waiting: float = 0.1) -> ASGITestExecutor:
        for form in self._forms:
            child = multiprocessing.Process(target=serve_at, args=(form,))
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
        func: t.Callable[[t.Tuple[t.Any, ...]], None],
        args: t.Tuple[t.Any, ...] = (),
        waiting: float = 0.05,
    ) -> None:
        with self.start_serve(waiting=waiting):
            func(*args)

    @classmethod
    def debug(
        cls,
        app: ASGIApp,
        path_log: str,
        host: str = "localhost",
        port: int = 8000,
        waiting: float = 0.05
    ) -> None:
        form = ASGIServerForm(host, port, app, path_log)
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
