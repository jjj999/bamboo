# エラーハンドリング

このドキュメントでは Bamboo でのエラー時のレスポンス送信方法について説明します．

## 概要

Web アプリケーションではサーバーサイドでのエラー発生時に適切なエラーレスポンスをクライアントに返す必要があります．エラーレスポンスは通常のレスポンスと HTTP という点では変わりありませんが，基本的には決まったフォーマットで返されるべきです．また，`Endpoint` サブクラスのレスポンスメソッド内でエラーデータを生成し送信することは可能ですが，あまり良い方法とは言えません．なぜなら，エラーは副次的な処理に過ぎず，レスポンスメソッド内にエラーレスポンスのための副次的な処理が多く入り込むことにより，本処理がわかりにくくなりレスポンスメソッドの可読性が下がるためです．

Bamboo でのエラーレスポンスの送信方法は以下のステップで行います:

1. `ErrInfoBase` サブクラスの定義
2. `Endpoint.send_err()` メソッドに定義した `ErrInfoBase` サブクラスのオブジェクトを渡す

1 のステップは通常レスポンスメソッド外部で行うので，複数のレスポンスメソッドで同一のエラーレスポンスを送信することが可能です．`Endpoint.send_err()` メソッドは定義した `ErrInfoBase` サブクラスのオブジェクトを受け取って，`ErrInfoBase.get_all_form()` メソッドによって得られたエラーレスポンスのステータスコード，レスポンスヘッダ，レスポンスボディ情報を抽出します．その後，そのデータを用いてクライアントにレスポンスを送信します．

まずは `ErrInfoBase` の基本的な定義方法を述べ，その後レスポンスメソッド内での使用方法について説明します．

## ErrInfoBase サブクラスの定義方法

開発者が定義すべきエラーの要素は主に次の3つです:

- ステータスコード `ErrInfoBase.http_status`
  - `HTTPStatus` クラスの変数から選択します
  - デフォルトは `HTTPStatus.BAD_REQUEST` (ステータスコード `400`) です
- レスポンスヘッダ `ErrInfoBase.get_headers()`
  - 追加で送信したいヘッダを定義します
  - ヘッダ名と値の2要素のタプルのリストを返すメソッドとして定義します
  - デフォルトでは空のリストが返されます
- レスポンスボディ `ErrInfoBase.get_body()`
  - エラーを表すためのボディを定義します
  - `bytes` オブジェクトを返すメソッドとして定義します
  - デフォルトでは空の `bytes` が返されます
  - `_content_type_` クラスプロパティにレスポンスボディの `Content-Type` ヘッダの値を定義できます

以下ではこれらについて順に説明していきます．

### ステータスコード

ステータスコードはリクエストに対するサーバーサイドの状態を表すための3桁の数字で，HTTP で定義されているものです．`ErrInfoBase` サブクラスで `http_status` クラス変数を上書きすることでステータスコードを定義できますが，実際には `Enum` クラスである `bamboo.base.HTTPStatus` クラスのクラス変数を代入します．例えば，サーバー内部の原因によるエラーを示すステータスコード `500` を返すためには以下のようにします:

```python
class UselessErrInfo(ErrInfoBase):
    http_status = HTTPStatus.INTERNAL_SERVER_ERROR
    ...
```

### レスポンスヘッダ

エラー時のレスポンスヘッダは `get_headers()` インスタンスメソッドを用いて定義できます．このメソッドのシグネチャは以下のとおりです:

```python
def get_headers(self) -> List[Tuple[str, str]]:
    ...
```

`Tuple[str, str]` はヘッダの名前と値のペアであり，`get_headers()` メソッドが返すべきはそのペアのリストです．一例として，Basic 認証が必要なエンドポイントで `Authorization` ヘッダが含まれていない場合に送信するエラーを定義したものを以下に示します:

```python
class BasicAuthHeaderNotExistErrInfo(ErrInfoBase):
    http_status = HTTPStatus.UNAUTHORIZED

    def get_headers(self) -> List[Tuple[str, str]]:
        return [("WWW-Authentication", 'Basic realm="SECRET AREA"')]
```

複数のレスポンスヘッダを追加定義する場合は，上記のリスト内のタプルを追加することで実現できます．

### レスポンスボディ

クライアントに具体的なエラーの原因やエラーの解消方法を説明するためにエラーレスポンスにレスポンスボディを含める場合があります．そのためには，`get_body()` インスタンスメソッドを利用します．このメソッドのシグネチャは以下のとおりです:

```python
def get_body(self) -> bytes:
    ...
```

例えば JSON を API として通信を行う Web アプリケーションの場合，エラーレスポンスのレスポンスボディを JSON で送る場合があります．その場合以下のように `get_body()` メソッドを定義することが出来ます:

```python
def get_body(self) -> bytes:
    data = json.dumps({"err_code": 4000, "message": "The request was inappropriate"})
    return data.encode("utf-8")
```

### `_content_type_` クラスプロパティ

このプロパティは代入不可能なクラス変数で，レスポンスボディの `Content-Type` ヘッダの値を表します．`ErrInfoBase` に定義されているデフォルト値は `text/plain` です．上記のようにもし JSON データをエラーレスポンスとして送信するのなら，このプロパティも変更すべきです．以下は，上記の JSON データを送信する `ErrInfoBase` サブクラスの定義例です:

```python
from bamboo import ErrInfoBase, HTTPStatus, ContentType, MediaTypes
from bamboo.util.deco import class_property

class MockErrInfo(ErrInfoBase):

    http_status = HTTPStatus.BAD_REQUEST

    def get_body(self) -> bytes:
        data = json.dumps({"err_code": 4000, "message": "The request was inappropriate"})
        return data.encode("utf-8")

    @class_property
    def _content_type_(cls) -> ContentType:
        return ContentType(MediaTypes.json, "utf-8")
```

### 動的なエラーレスポンスの生成

`ErrInfoBase` サブクラスにはこの他にも `__init__` メソッドを定義することが出来ます．`__init__` メソッド内で定義されたインスタンス変数は全て `get_headers()` メソッドや `get_body()` メソッド内で使用できます．すなわち，これまでの実装例では静的なエラーレスポンスのみを定義していましたが，`__init__` メソッドの定義によって動的にエラーレスポンスを生成することが出来ます．

例えば先程定義した `MockErrInfo` を以下のように変更して，レスポンスボディ内のエラーメッセージを動的に生成することが出来ます:

```python
class MockErrInfo(ErrInfoBase):

    http_status = HTTPStatus.BAD_REQUEST

    def __init__(self, message: str) -> None:
        self._message = message

    def get_body(self) -> bytes:
        # インスタンス生成時に受け取ったメッセージを送る
        data = json.dumps({"err_code": 4000, "message": self._message"})
        return data.encode("utf-8")

    @class_property
    def _content_type_(cls) -> ContentType:
        return ContentType(MediaTypes.json, "utf-8")
```

## レスポンスメソッド内でのエラー送信

ここまでエラーの定義方法を述べてきましたが，定義した `ErrInfoBase` サブクラスは最終的にはレスポンスメソッド内でインスタンス化され，`Endpoint.send_err()` メソッドを使って送信されます．以下は先程定義した `MockErrInfo` を送信する例です:

```python
# なんらかの検証を行う関数
def is_valid() -> bool:
    return False

class MockEndpoint(Endpoint):

    @data_format(input=None, output=None)
    def do_GET(self) -> None:

        if not is_valid():
            self.send_err(MockErrInfo("Hogehoge Error!!!"))
            # エラーを送信ので処理を終了
            return

        # Do something...
```

このままでもエラーの送信は機能しますが，`may_occur` デコレータを利用するとコールバックで送信されうるエラーを明示的に定義できます:

```python
from bamboo.sticky.http import data_format, may_occur

class MockEndpoint(Endpoint):

    @may_occur(MockErrInfo)
    @data_format(input=None, output=None)
    def do_GET(self) -> None:

        if not is_valid():
            self.send_err(MockErrInfo("Hogehoge Error!!!"))
            # エラーを送信ので処理を終了
            return

        # Do something...
```
