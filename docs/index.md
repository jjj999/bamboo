[![Bamboo](res/bamboo.png)](https://jjj999.github.io/bamboo/)
[![PyPI version](https://badge.fury.io/py/bamboo-core.svg)](http://badge.fury.io/py/bamboo-core)
[![License](https://img.shields.io/github/license/mashape/apistatus.svg)](https://pypi.python.org/pypi/bamboo-core/)

# Bamboo

## Installing

- Python >= 3.8

```
python -m pip install bamboo-core
```

## Usage
詳細は[チュートリアル](tutorials/concept)を参照してください．以下は簡単な実装例です．

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
API ドキュメントは[こちら](api/bamboo/pkg/)．