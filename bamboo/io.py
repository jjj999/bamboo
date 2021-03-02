
from collections import deque
from io import BytesIO, IOBase
from typing import (
    Deque,
    Iterable,
    Iterator,
    TypeVar,
    Union,
)


__all__ = []


class ResponseBodyIteratorBase:

    def __iter__(self) -> Iterable[bytes]:
        return self

    def __next__(self) -> bytes:
        pass

    def __del__(self) -> None:
        pass


class BufferedBinaryIterator(ResponseBodyIteratorBase):

    def __init__(self, data: bytes, bufsize: int = 8192) -> None:
        super().__init__()

        self._data = BytesIO(data)
        self._bufsize = bufsize

    def __next__(self) -> bytes:
        buffer = self._data.read(self._bufsize)
        if buffer:
            return buffer
        raise StopIteration()

    def __del__(self) -> None:
        self._data.close()


BinaryReadableStream_t = TypeVar("BinaryReadableStream_t")


class BufferedStreamIterator(ResponseBodyIteratorBase):

    def __init__(
        self,
        stream: BinaryReadableStream_t,
        bufsize: int = 8192
    ) -> None:
        super().__init__()

        if not (isinstance(stream, IOBase) and hasattr(stream, "read")):
            raise TypeError(
                "'stream' must be IOBase and have the 'read' method."
            )

        self._stream = stream
        self._bufsize = bufsize

    def __next__(self) -> bytes:
        buffer = self._stream.read(self._bufsize)
        if buffer:
            return buffer
        raise StopIteration()

    def __del__(self) -> None:
        self._stream.close()


class BufferedFileIterator(BufferedStreamIterator):

    def __init__(self, filename: str, bufsize: int = 8192) -> None:
        file = open(filename, "br")
        super().__init__(file, bufsize=bufsize)


class BufferedIteratorWrapper(ResponseBodyIteratorBase):

    def __init__(self, iter: Iterator[bytes], bufsize: int = 8192) -> None:
        super().__init__()

        self._iter = iter
        self._bufsize = bufsize
        self._buffer = BytesIO()

    @property
    def _is_buffer_filled(self) -> bool:
        return self._buffer.tell() >= self._bufsize

    def _update_buffer(self) -> bytes:
        self._buffer.seek(0)
        data = self._buffer.read(self._bufsize)
        other = self._buffer.read()
        self._buffer.close()
        self._buffer = BytesIO(other)
        return data

    def __next__(self) -> bytes:
        if self._is_buffer_filled:
            return self._update_buffer()

        while True:
            try:
                chunk = next(self._iter)
            except StopIteration:
                if self._buffer.tell():
                    return self._update_buffer()
                else:
                    raise StopIteration()
            else:
                diff = self._bufsize - self._buffer.tell()
                chunk_size = len(chunk)
                if chunk_size >= diff:
                    self._buffer.write(chunk[:diff])
                    self._buffer.flush()
                    data = self._update_buffer()

                    if chunk_size > diff:
                        self._buffer.write(chunk[diff:])

                    return data
                else:
                    self._buffer.write(chunk)
                    continue

    def __del__(self) -> None:
        self._buffer.close()


class BufferedConcatIterator(ResponseBodyIteratorBase):

    def __init__(
        self,
        *items: Union[bytes, Iterator[bytes]],
        bufsize: int = 8192
    ) -> None:
        super().__init__()

        self._iters: Deque[Iterator[bytes]] = deque()
        self._current: Iterator[bytes] = None
        self._bufsize = bufsize
        self._buffer = BytesIO()

        for item in items:
            self.append(item)

    def append(self, item: Union[bytes, Iterator[bytes]]) -> None:
        if isinstance(item, bytes):
            self._iters.append(
                BufferedBinaryIterator(item, bufsize=self._bufsize)
            )
        else:
            self._iters.append(
                BufferedIteratorWrapper(item, bufsize=self._bufsize)
            )

    @property
    def _is_buffer_filled(self) -> bool:
        return self._buffer.tell() >= self._bufsize

    def _update_buffer(self) -> bytes:
        data = self._buffer.getvalue()
        self._buffer = BytesIO()
        return data

    def __next__(self) -> bytes:
        if self._current is None:
            if len(self._iters):
                self._current = self._iters.popleft()
            else:
                raise StopIteration()

        while True:
            try:
                chunk = next(self._current)
            except StopIteration:
                if len(self._iters):
                    self._current = self._iters.popleft()
                    continue
                else:
                    if self._buffer.tell():
                        return self._update_buffer()
                    else:
                        raise StopIteration()
            else:
                diff = self._bufsize - self._buffer.tell()
                chunk_size = len(chunk)
                if chunk_size >= diff:
                    self._buffer.write(chunk[:diff])
                    self._buffer.flush()
                    data = self._update_buffer()

                    if chunk_size > diff:
                        self._buffer.write(chunk[diff:])

                    return data
                else:
                    self._buffer.write(chunk)
                    continue

    def __del__(self) -> None:
        self._buffer.close()
