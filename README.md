# Bamboo

[![Bamboo](docs/res/bamboo.png)](https://jjj999.github.io/bamboo/)
[![PyPI version](https://badge.fury.io/py/bamboo-core.svg)](http://badge.fury.io/py/bamboo-core)
[![License](https://img.shields.io/github/license/mashape/apistatus.svg)](https://pypi.python.org/pypi/bamboo-core/)
[![](https://img.shields.io/badge/docs-stable-blue.svg)](https://jjj999.github.io/bamboo)

## Supported Interfaces

- WSGI
- ASGI v3.0 (HTTP, WebSocket and Lifespan)

## Installling

* Python: >= 3.7

```
$ python -m pip install bamboo-core
```

## [Usage](https://jjj999.github.io/bamboo/tutorials/concept/)

以下は簡単な実装例です．

```python
from bamboo import WSGIApp, WSGIEndpoint, WSGITestExecutor

app = WSGIApp()

@app.route("hello")
class MockEndpoint(WSGIEndpoint):

    def do_GET(self) -> None:
        self.send_body(b"Hello, World!")

if __name__ == "__main__":
    WSGITestExecutor.debug(app)
```

上記スクリプトを実行後，ブラウザで http://localhost:8000/hello にアクセスするとレスポンスを確認できます．

## API documentation

API ドキュメントは[こちら](https://jjj999.github.io/bamboo/api/bamboo/pkg/)．

## Examples

### [upsidedown](https://github.com/jjj999/bamboo/tree/master/examples/upsidedown)

リクエストされた文字列を逆順に反転させて返すアプリケーションです．

### [image_traffic](https://github.com/jjj999/bamboo/tree/master/examples/image_traffic)

アクセスに対して静的な画像を返すアプリケーションです．

### [tweets](https://github.com/jjj999/bamboo/tree/master/examples/tweets)

CLI ベースの簡易的な Twitter のような投稿アプリです．認証機能は実装されていません．
