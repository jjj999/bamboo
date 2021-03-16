# API の定義

Web アプリケーションの設計において API の定義は欠くことが出来ません．このドキュメントでは Bamboo の機能の一つである API の定義について述べます．

## 概要

Web アプリケーションはクライアントとの通信によって成立するアプリケーションです．クライアントはサーバーサイドのアプリケーションの内部実装について詳しく知る必要はなく，どのようなデータを送ればどのようなデータが返されてくるのかさえわかっていれば十分です．そのデータの入出力の規則を API と呼びます．

API は基本的にはアプリケーションを実装するサーバーサイドが定義します．サーバーサイドでは，定義した API 通りにクライアントから送られてくるデータを用いて適切な処理を行い，API に則った出力をクライアントに返します．しかし，実際には API の定義に則ったデータがクライアントから送られてくる保証はありません．これを保証するためにはデータが API に則っているか検証する必要があります．この操作を**バリデーション**といいます．

まとめると，API を定義し，その API に対応するバリデーションを行うことで，サーバーサイドの入力データが API に則ったものであることを保証することが出来ます．Bamboo ではこの API 定義とバリデーション機能を提供するために **ApiData** クラスと **data_format** デコレータが用意されています．本ドキュメントではこれらの概念とその基本的な使い方について説明します．

## ApiData クラス

**ApiData** は API を定義するためのデータクラスの抽象クラスです．このクラスはクライアントからの入力データが API に従うものかどうかを，このクラスのインスタンスが生成できるかどうかで判断します．このような理由から，バリデーションを行うメソッドは ApiData クラスのサブクラスの **\_\_init\_\_** メソッドです．バリデーションが失敗すると，このクラスのサブクラスは **ValidationFailedError** を送出します (独自実装する場合は送出すべきです) ．

以下では既存の ApiData 具象クラスをいくつか紹介します．

### BinaryApiData クラス

ApiData クラスの最も単純な具象クラスは **BinaryApiData** です．このクラスはバリデーションをほとんどしないクラスです．バリデーションをほとんどしないということは，リクエストボディとして任意のバイナリデータを受け付けるという意味です．つまり制限がないというのが，このクラスに対応する API の課す規則です．

このクラスは `raw` というプロパティを持っており，このプロパティからリクエストボディにアクセスできます．`Endpoint.body` プロパティからリクエストボディにアクセスすることが出来ることを考えれば，このクラスはほとんど意味を持ちませんが，`text/plain` という `Content-Type` を表すために使うことが出来ます．

### JsonApiData クラス

**JsonApiData** クラスは JSON データを定義するために使用できます．このクラスはインスタンス生成時にクライアントから送られてきた生データが定義した JSON フォーマットを持っているかどうかを検証します．API データの定義は Python 標準ライブラリの `dataclass` デコレータを使った定義と似ています:

```python
class MockApiData(JsonApiData):
    name: str
    email: str
    age: int
```

上記の `JsonApiData` クラスのサブクラスは以下のようなデータフォーマットを定義しています:

```python
{"name": "jjj999", "email": "hogehoge@example.com", "age": 10}
```

上記のデータフォーマットを持つオブジェクトのリストを定義したい場合は以下のように定義します:

```python
class MockListApiData(JsonApiData):
    mocks: List[MockApiData]
```

このように `JsonApiData` のサブクラスを連鎖的に定義することで，複雑な JSON データのフォーマットを定義することが出来ます．

## data_format デコレータ

このデコレータは `Endpoint` のレスポンスメソッド (コールバック関数) にデコレートするためのもので，コールバック関数の API を定義します．具体的には，API の定義は `data_format` デコレータの `input` 引数と `output` 引数に `ApiData` サブクラスを指定することで行います．これらの引数には入出力データが存在する場合には `ApiData` サブクラスを，存在しない場合には `None` を指定します．以下はリクエストボディが先程定義した `MockApiData` で，レスポンスボディが存在しないレスポンスメソッドのデータフォーマットの定義例です:

```python
@data_format(input=MockApiData, output=None)
def do_GET(self, rec_body: MockApiData) -> None:
    # Do something...
```

上記の例からわかるように，`data_format` デコレータを指定したことにより，引数が一つ増えます．増えた引数は `input` 引数に指定した ApiData サブクラスのインスタンスです．ApiData サブクラスのインスタンスが生成されているということは，前述したようにバリデーションが成功したという意味です．つまりレスポンスメソッド内では，リクエストボディが定義された API のデータフォーマットに則っていることが保証されます．ちなみに，`data_format` デコレータの `is_validate` 引数に `False` を指定するとバリデーションは行われず，レスポンスメソッドの引数も増えません．

## 実装例

API の定義は

1. `ApiData` サブクラスの実装
2. `data_format` デコレータに適切な `ApiData` サブクラスまたは `None` を指定

の手順で行います．

`ApiData` サブクラスの実装は API として利用するデータフォーマットに依存します．JSON データを API として利用するのであれば，バリデーションに関する実装は必要ありません．上述したように，`JsonApiData` サブクラスに適当なフィールドと type hints を定義するだけです．その他の特別なデータフォーマットを API として利用する場合には `ApiData` サブクラスを独自に定義する必要があります．

API のデータフォーマットとして利用する `ApiData` サブクラスが準備できたら，それを `data_format` デコレータの `input` または `output` 引数に指定します．特に `input` 引数に `None` ではない引数を指定した場合は，指定した `ApiData` サブクラスのインスタンスがレスポンスメソッドの引数に追加されます．もし，`is_validate` 引数を `False` に設定した場合にはバリデーションは行われず，引数の追加もありません．また，`err_validate` 引数には `ErrInfoBase` サブクラスを指定することが出来ます．この引数を指定することで，バリデーションが失敗し `ValidationFailedError` が送出された場合のレスポンスデータを制御できます．デフォルトでは，ステータスコード `415` のみがクライアントに返されます．

## 拡張性

上記のような既存の `ApiData` サブクラスを利用することも出来ますが，独自に定義することも出来ます．`ApiData` サブクラスを定義する上で注意することは，

- `__init__` メソッドにバリデーションロジックを定義する
- 生成されたオブジェクトから解析した生データにアクセスできるようにする

の2点です．以下では `BinaryApiData` の実装を例にとり，これらの注意点について説明していきます．

### バリデーションロジックの定義

バリデーションロジックとはバリデーションに用いるロジックのことで，つまりどのようにバリデーションするかということです．より具体的に言うと，`if` 文などを用いて，受け取ったデータが適切なものなのかを検証するコードのことです．バリデーションロジックはどのようなデータを用いるかによって決まるので，一概にこうあるべきというものはありません．したがって，まずは使用するデータフォーマットを決め，受け取ったデータがそのデータフォーマットに準ずるものであることを検証するためのロジックを考える必要があります．

例として，`BinaryApiData` のバリデーション部分を見てみましょう．このクラスはほとんどバリデーションを行わないと述べましたが，実際には生データ `raw` の型のみを検証します．`BinaryApiData` は任意のバイナリを許容する `ApiData` ですが，データフォーマットが具体的に決まっている場合にはより複雑なバリデーションロジックを必要とします．もしバリデーションが失敗した場合は，`ValidationFailedError` を送出しなければなりません．

```python
class BinaryApiData(ApiData):

    def __init__(self, raw: bytes, content_type: ContentType) -> None:
        super().__init__(raw, content_type)

        # バリデーションロジック
        if not isinstance(raw, bytes):
            raise ValidationFailedError(
                f"'raw' must be a 'bytes', but was {raw.__class__.__name__}.")

        # 生データをそのまま保持しておく
        self._raw = raw

    ...
```

`ApiData` サブクラスの `__init__` メソッドの第2引数には `ContentType` オブジェクトが渡されます．`ContentType` オブジェクトは

- `media_type`
- `charset`
- `boundary`

という `str` または `None` のインスタンス変数を持ちます．これらのインスタンス変数は MIME タイプの検証や生データのデコードのための文字コードを取得するのに使用できます．`boundary` には `Content-Type` ヘッダが `multipart/form-data` のときの `boundary` ディレクティブの値が格納されます．開発者はこれらのインスタンス変数は `None` である可能性があることを意識すべきです．`None` であるとは，すなわち`Content-Type` ヘッダにその情報がなかったということを意味しています．以下のコードスニペットは `JsonApiData` の `content_type` 引数に対する検証部分を示したものです．

```python
class JsonApiData(ApiData):

    def __init__(self, raw: bytes, content_type: ContentType) -> None:
        super().__init__(raw, content_type)

        # 文字コードの検証
        encoding = content_type.charset
        if encoding is None:
            encoding = "utf-8"

        # MIME タイプの検証
        media_type = content_type.media_type
        if media_type is None:
            raise ValidationFailedError(
                "'Content-Type' header was not specified. Specify "
                f"'{MediaTypes.json}' as media type.")
        if media_type.lower() != MediaTypes.json:
            raise ValidationFailedError(
                "Media type of 'Content-Type' header was not "
                f"{MediaTypes.json}, but {content_type.media_type}.")
        ...
```

### 解析した生データにアクセスできるようにする

`ApiData` サブクラスの役割はバリデーションのみではありません．バリデーション後，その解析したデータにアクセス出来る必要があります．アクセスの提供方法は特に制限はありません．一例として，`BinaryApiData` はデータへのアクセス方法として `raw` プロパティを用意しています．また，`JsonApiData` の場合は，開発者にそのサブクラスと JSON データのキーを定義させることでオブジェクト生成後にそのデータにアクセスできるようにしています．

```python
# BinaryApiData の例
class BinaryApiData(ApiData):

    def __init__(self, raw: bytes, content_type: ContentType) -> None:
        ...

    @property
    def raw(self) -> bytes:
        return self._raw

# JsonApiData の例
class UserData(JsonApiData):
    name: str
    email: str
    age: int
```
