from collections import deque
import io
import os
import typing as t


__all__ = []


class ResponseBodyIteratorBase:
    """Base class of iterator for buffering response body.
    """

    def __iter__(self) -> t.Iterable[bytes]:
        return self

    def __next__(self) -> bytes:
        pass

    def __del__(self) -> None:
        pass


class BufferedBinaryIterator(ResponseBodyIteratorBase):
    """Iterator for sending bytes as chunks.

    Its object can be used to generate iterator from a bytes object, which
    yields specified size of bytes objects.

    Note:
        Even if you generate its object from a bytes object sending to a client
        and specify it as response body, there may be no effect on performance
        of your web application. Its object should be used only for unifying
        interface as a subclass of `ResponseBodyIteratorBase`.
    """

    def __init__(self, data: bytes, bufsize: int = 8192) -> None:
        """
        Args:
            data: A bytes object to be iterated.
            bufsize: Chunk size of bytes objects yielded from the iterator.
        """
        super().__init__()

        self._data = io.BytesIO(data)
        self._bufsize = bufsize

    def __next__(self) -> bytes:
        buffer = self._data.read(self._bufsize)
        if buffer:
            return buffer
        raise StopIteration()

    def __del__(self) -> None:
        self._data.close()


BinaryReadableStream_t = t.TypeVar("BinaryReadableStream_t")


class BufferedStreamIterator(ResponseBodyIteratorBase):
    """Iterator of binary made with file-like object.

    Its object can be used to iterate file-like obj of binary.
    """

    def __init__(
        self,
        stream: BinaryReadableStream_t,
        bufsize: int = 8192
    ) -> None:
        """
        Args:
            stream: File-like object readable binary.
            bufsize: Chunk size of bytes objects yielded from the iterator.

        Raises:
            TypeError: Raised if `stream` is not readable.
        """
        super().__init__()

        if not (isinstance(stream, io.IOBase) and hasattr(stream, "read")):
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
    """Iterator of binary made with file path.

    Its object can be used to iterate file-like obj made with file path.
    """

    def __init__(
        self,
        path: str,
        bufsize: int = 8192,
        remove: bool = False,
    ) -> None:
        """
        Args:
            path: File path.
            bufsize: Chunk size of bytes objects yielded from the iterator.
        """
        self._path = path
        self._remove = remove

        file = open(path, "br")
        super().__init__(file, bufsize=bufsize)

    def __del__(self) -> None:
        super().__del__()

        if self._remove:
            os.remove(self._path)


class BufferedIteratorWrapper(ResponseBodyIteratorBase):
    """Iterator wrapping iterator yeilding bytes objects.

    Its object holds an iterator inner, which can yeilds bytes objects
    with arbitary sizes, and its object yeilds bytes objects with specified
    chunk size, i.e. this object changes chunk size of bytes yielded from
    given iterator.
    """

    def __init__(self, iter: t.Iterator[bytes], bufsize: int = 8192) -> None:
        """
        Args:
            iter: Iterator wrapped.
            bufsize: Chunk size of bytes objects yielded from the iterator.
        """
        super().__init__()

        self._iter = iter
        self._bufsize = bufsize
        self._buffer = io.BytesIO()

    @property
    def _is_buffer_filled(self) -> bool:
        return self._buffer.tell() >= self._bufsize

    def _update_buffer(self) -> bytes:
        self._buffer.seek(0)
        data = self._buffer.read(self._bufsize)
        other = self._buffer.read()
        self._buffer.close()
        self._buffer = io.BytesIO(other)
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
    """Iterator conbining serveral iterator yeilding bytes objects.

    Its object can concatenate several iterator or bytes objects and behaves
    as a single iterator yieding bytes objects with specified chunk size.
    """

    def __init__(
        self,
        *items: t.Union[bytes, t.Iterator[bytes]],
        bufsize: int = 8192
    ) -> None:
        """
        Args:
            *items: bytes objects or iterators yielding bytes.
            bufsize: Chunk size of bytes objects yielded from the iterator.
        """
        super().__init__()

        self._iters: t.Deque[t.Iterator[bytes]] = deque()
        self._current: t.Iterator[bytes] = None
        self._bufsize = bufsize
        self._buffer = io.BytesIO()

        for item in items:
            self.append(item)

    def append(self, item: t.Union[bytes, t.Iterator[bytes]]) -> None:
        """Add bytes or iterator yielding bytes inside.

        Args:
            item: bytes object or iterator yielding bytes.
        """
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
        self._buffer = io.BytesIO()
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
