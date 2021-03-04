# サンプルアプリケーションを実装してみる
ここでは Bamboo による実装に慣れるために，簡単なサンプルアプリケーションを実装してみましょう．今回実装するのはモノリシックなサーバーですが，これを応用することでマイクロサービスアーキテクチャに則ったサーバーサイドシステムを構築することは可能です．

## アプリケーションとエンドポイントの種類
Bamboo にはアプリケーションとエンドポイントを実装したクラスがいくつかあります．これらのクラスは，アプリケーションとエンドポイントの根底の概念自体は共通ですが，対応しているインターフェースやプロトコルなどにバリエーションがあります．現在サポートされているエンドポイントには以下のようなものがあります (今後アップデートにより追加される可能性があります) :

- WSGIEndpoint (WSGI・HTTP をサポート)
- ASGIHTTPEndpoint (ASGI・HTTP をサポート)

今回のサンプルアプリケーションでは `WSGIEndpoint` を使ってエンドポイントを作成していきます．

!!! Note
    特定のエンドポイントクラスは対応しているアプリケーションオブジェクトにしか登録できません．例えば `WSGIEndpoint` クラスの場合は `WSGIApp` オブジェクト，`ASGIHTTPEndpoint` の場合は `ASGIHTTPApp` にしか登録することが出来ません．

## 実装の流れ
Bamboo による開発におけるほとんどの作業は，**エンドポイントクラスの実装**です．エンドポイントクラスは採用したサーバーアプリケーションのインターフェースとプロトコルによって，その元となるスーパークラスが異なります．上述したように今回は `WSGIEndpoint` を使用するので，このクラスのサブクラスを実装することでアプリケーションを実装していきます．

エンドポイントの実装は以下の流れで行っていきます:

1. URI を決める
2. setup メソッドに初期化処理を書く (今回は省略)
3. 内部ロジックを実装する


## Endpoint の実装

### サンプルアプリケーションの概要
今回作成するサンプルアプリケーションの機能は**リクエストで送られてきたテキストを反転させて返す**というものです．例えば，

```
{
    "token" : "abcdefg"
}
```

という Json データに対して，

```
{
    "result" : "gfedcba"
}
```

というレスポンスを返します．入出力の JSON スキーマは上の例のものをそのまま使います．ではさっそく作っていきましょう．

### URI を決める
リクエストされた URI を解析して対応するエンドポイントを探し当てるためには事前の準備が必要です．その準備とはアプリケーションオブジェクトに URI とエンドポイントの対応表を渡すことです．アプリケーションオブジェクトはその対応表さえあれば，リクエストされた URI に対応するエンドポイントを見つけることが出来ます．

エンドポイントと URI を紐付けるためには，アプリケーションオブジェクトの *route* メソッドを使用します．エンドポイント名は *UpsideDownEndpoint* と命名しました (お好きなもので構いません) ．

```python
from bamboo import WSGIApp, WSGIEndpoint

app = WSGIApp()

# URI の指定
# http://host:port/upsidedown でアクセス出来るようになる
@app.route("upsidedown")
class UpsideDownEndpoint(WSGIEndpoint):
    pass
```

### 内部ロジックを実装する
次に最も重要な工程である内部ロジックの実装に移りましょう．内部ロジックとは，エンドポイントがクライアントからのリクエストへの対処の仕方のことです．内部ロジックはそのエンドポイントにどのような機能を持たせたいかで様々に変化します．エンドポイントにはそのユースケースによって，単純に HTML ファイルを返すものもあれば，認証をしてユーザーのリソースへのアクセスを提供するようなものも考えられます．

今作成しているエンドポイントでは，クライアントから送られてきた JSON データの中からトークンを取り出し，そのトークンを反転させたものを JSON 形式で返すというのが内部ロジックになります．以下ではその内部ロジックを Bamboo で実装する方法について説明していきます．

#### レスポンスメソッド
HTTP をサポートするエンドポイントには**レスポンスメソッド**という特別なメソッドが存在します．レスポンスメソッドは，内部ロジックを実装するためのコールバックで，クライアントからリクエストが来るとアプリケーションオブジェクトはこのレスポンスメソッドを実行させます．

もう少し詳しく説明しましょう．上述したように，アプリケーションオブジェクトはリクエストされた URI を解析することでエンドポイントを特定します．一方で，エンドポイント内の内部ロジックは，リクエストされた HTTP メソッドで特定されます．つまり，エンドポイントにはいくつかの HTTP メソッドに対応するレスポンスメソッドを定義することが出来ます．これはエンドポイントがエンドポイントたる所以でもあります．すなわち，エンドポイントは**クライアントがアクセスして処理を行ってもらう場所**なのであり，その場所に行けば GET や POST などの目的にあった処理を行ってもらえるというわけです．

レスポンスメソッドにはいくつかの決まりがあります．その中でも最も重要なのはその**命名規則**です．下表は HTTP メソッドとそれをメソッドを指定したリクエストを処理するレスポンスメソッドの名前の対応表です．

|   HTTP メソッド   |   レスポンスメソッド名  |
| :---------------: | :---------------------: |
|       GET         |       do_GET            |
|       POST        |       do_POST           |
|       PUT         |       do_PUT            |
|       DELETE      |       do_DELETE         |
|       HEAD        |       do_HEAD           |
|       OPTIONS     |       do_OPTIONS        |
|       PATCH       |       do_PATCH          |
|       TRACE       |       do_TRACE          |

上の表で出てきたレスポンスメソッド名は全て実装する必要はありません．実装したいものだけ実装すれば OK です．また，複数のレスポンスメソッドを実装することも可能です．

!!! Tip
    HTTP メソッドの示す意味とレスポンスメソッドによって定義される内部ロジックの挙動はマッチさせることを推奨します．例えばあなたが画像投稿アプリのバックエンドシステムを作るとして，画像の取得と画像の投稿を同じエンドポイントで行うとしましょう．このような場合は，画像の取得を処理するレスポンスメソッドは `do_GET()`，画像の投稿を処理するレスポンスメソッドは `do_POST()` にするのが意味合い的に自然でしょう．これがもし逆であったら，HTTP メソッドの意味と内部ロジックの挙動はかけ離れたものになり，フロントエンド側の開発者から嫌がられるかもしれません．HTTP メソッドは単なる名前であり，その内部ロジックについては開発者に一任されるという点に注意してください．

!!! Note
    コールバックとは，特定のイベントが発生した際に呼び出される関数 (Python では Callable と呼ばれます) です．`do_GET()` は「クライアントからそのエンドポイントに GET という HTTP メソッドが送られてきた」というイベントが発生した場合にのみ実行されるメソッドであり，一種のコールバックと言えます．`do_GET()` 以外の他のレスポンスメソッドについても同様です．

今回は GET メソッドのレスポンスメソッドを実装することにします．この場合，以下のようにレスポンスメソッドを定義できます:

```python
@app.route("upsidedown")
class UpsideDownEndpoint(WSGIEndpoint):

    def do_GET(self) -> None:
        # 後ほど実装
```

#### API の定義
Web アプリケーションを作る上で最も重要なことの1つに Web API の定義があります．API はソフトウェアコンポーネントの仕様などのことを指す抽象的な用語ですが，Web API というときには，ある URI にアクセスする際の入出力データのフォーマットという意味で使われることが多いです．以下でもそのような意味を持つ言葉として扱っていくことにします．

!!! Warninig
    一部サイトでは API は何か特別な機能を持ったものかのように説明されていますが，上述したように API という用語は単なるソフトウェアコンポーネントの仕様やインターフェースに過ぎません．ソフトウェアコンポーネントとはソフトウェアとして認識できるもののことを漠然と指す用語であり，規模の小さいものでは変数や関数，大きいものでは Goole や Amazon，Facebook などが提供するようなインターネット上の大規模なサービスなどがあります．ちなみに，フレームワークやライブラリなどのクラスや関数の仕様をドキュメント化したものは API リファレンスや API ドキュメントと呼ばれたりします．

Web API (以下単に API) は「データの入力および出力はこうあるべきだという規則」を定義します．クライアント側がこの規則に従わないデータを送ってきた場合，サーバー側ではそのデータを正しく解析できないかもしれません．逆に，サーバー側が API に従わないデータをレスポンスとして送っても，クライアント側は事前に決められていた規則にそぐわないデータを受け取って正しく処理することは困難になります．このようなことから，リクエストを処理する上で API を曖昧さなく定義し，それを明確化しておくことは重要と言えます．

ここでは，リクエストボディおよびレスポンスボディのデータフォーマットは JSON として話を進めていきましょう．すると，Web API を定義するとは，入出力に利用される JSON のスキーマ ，すなわち，どんなキーがあってそこにはどんな型のデータが入るかという規則を定義することと同じです．Bamboo ではこのスキーマを定義するのに **JsonApiData** というクラスが用意されています．このクラスを使うと，例えば

```
{
    name: "user_name", age: 20, email: "hoge@example.com"
}
```

という JSON データを扱いたいとしましょう．すると，上記のデータのキーと型は

```python
from bamboo import JsonApiData

class Account(JsonApiData):

    name: str
    age: int
    email: str
```

と定義できます．これは JSON スキーマを定義する上で大きな助けとなるでしょう．また，後述する **data_format** アノテーションと組み合わせることで，リクエストデータの型安全を保証できます．

#### レスポンスメソッドの実装

それではレスポンスメソッド `do_GET()` の実装に移っていきましょう．これまでのコールバックの命名規則，API の定義の議論を踏まえてコールバックを実装してみます．

```python
from bamboo import WSGIApp, WSGIEndpoint, JsonApiData
from bamboo.sticky.http import data_format

app = WSGIApp()

# リクエスト，レスポンスボディのJSONスキーマの定義
class UpsideDownRequest(JsonApiData):
    token: str

class UpsideDownResponse(JsonApiData):
    result: str


# エンドポイントの定義
@app.route("upsidedown")
class UpsideDownEndpoint(WSGIEndpoint):

    # 入出力データフォーマットの登録
    @bamboo.data_format(input=UpsideDownRequest, output=UpsideDownResponse)
    def do_GET(self, req_body: UpsideDownRequest) -> None:
        # 反転処理
        result = req_body.token[::-1]

        # レスポンスの作成
        body = {"result": result}
        self.send_json(body)
```

上の例で，`do_GET()` が **data_format()** というデコレータでデコレートされているのに気が付いたでしょうか．このデコレータを使うと，入出力データのデータフォーマットを登録することが出来ます．特に，*input* 引数に登録すると，リクエストボディをデコードしたデータをコールバックの引数として受け取れます．その引数は既にバイナリからデコードされ，型バリデーション (型の検証) まで実行します．もし，型バリデーションの段階でエラーが発生した場合，クライアントにレスポンスコード 415 (Unsupported Media Type) が返されます．

!!! Tip
    `data_format()` デコレータの `input` および `output` 引数には `ApiData` クラスのサブクラスを指定することが出来ます．詳しくは [API ドキュメント](https://jjj999.github.io/api/bamboo/api/)を参照してください．

## サーバーを起動する
最後にサーバーを起動します．今回はチュートリアルなので，デバッグモードでサーバーを起動しましょう．Bamboo にはテスト用に `TestExecutor` というユーティリティクラスが定義されており，このクラスを用いて簡単にデバッグモードでサーバーアプリケーションを起動できます．以下は今回のチュートリアルで作成するサーバーサイドの完全なスクリプトです．

```python
from bamboo import WSGIApp, WSGIEndpoint, JsonApiData, TestExecutor
from bamboo.sticky.http import data_format

app = WSGIApp()

class UpsideDownRequest(JsonApiData):
    token: str

class UpsideDownResponse(JsonApiData):
    result: str

@app.route("upsidedown")
class UpsideDownEndpoint(WSGIEndpoint):

    @data_format(input=UpsideDownRequest, output=UpsideDownResponse)
    def do_GET(self, req_body: UpsideDownRequest) -> None:
        result = req_body.token[::-1]

        body = {"result": result}
        self.send_json(body)

if __name__ == "__main__":
    TestExecutor.debug(app, "debug_app.log")
```

## クライアントサイドの処理
ここまでは bamboo によるサーバーサイドの処理でした．実験をするためにはクライアントサイドの処理も当然必要になります．今回はクライアント側の実装の解説は割愛します．

```python
import sys

from bamboo import JsonApiData
from bamboo.request import http

class UpsideDownResponse(JsonApiData):
    result: str

def request(uri: str, token: str) -> None:
    body = {"token": token}
    with http.get(uri, json=body, datacls=UpsideDownResponse) as res:

        # レスポンスヘッダの表示
        print("Headers")
        print("-------")
        for k, v in res.headers.items():
            print(f"{k} : {v}")
        print()

        # レスポンスボディの表示
        body = res.attach()
        print("Bodies")
        print("------")
        print(body.result)

if __name__ == "__main__":
    URI = "http://localhost:8000/upsidedown"
    token = sys.argv[1]         # コマンドライン引数として送信するトークンを指定
    request(URI, token)
```

実装では，サーバーに送るトークンをコマンドライン引数として指定できるようにしました．これでいろんなトークンを指定して，全て逆さまになって返ってくるか確かめることが出来ます．

## 実行

### サーバー側
先程のスクリプトを serve.py という名前のファイルで保存したとしましょう．その場合，以下のコマンドを実行します．

```
python serve.py
```

実行し，正常に動作すると

```
Hosting on localhost:8000 ...
WARNING: This is debug mode. Do not use it in your production deployment.
```

と表示されます．

### クライアント側
サーバー側の実行が終わったら，別のターミナルで以下のコマンドを実行しましょう．ただし，先程実装したクライアントサイドのスクリプトは request.py で保存したと仮定します．

```
python request.py abcdefg
```

実行後，ターミナルに以下のように表示されたら成功です．

```
Headers
-------
Date : Thu, 18 Feb 2021 07:07:58 GMT
Server : WSGIServer/0.2 CPython/3.8.5
Content-Type : application/json; charset=UTF-8
Content-Length : 21

Bodies
------
gfedcba
```

レスポンスボディの結果にコマンドライン引数で指定したトークン (上の例では abcdefg) が逆さまになって返ってきていることを確認しましょう．また，他のトークンを指定しても同様の結果になるか確認してみましょう．
