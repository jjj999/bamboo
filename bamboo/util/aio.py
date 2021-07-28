import asyncio
import typing as t


def gather_and_execute(*awaitables: t.Awaitable[t.Any]) -> t.List:
    eloop = asyncio.get_event_loop()
    tasks = asyncio.gather(*awaitables)
    eloop.run_until_complete(tasks)
