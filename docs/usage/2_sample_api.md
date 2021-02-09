# サンプル API を実装してみる
ここでは Bamboo による設計に慣れるために，簡単なサンプル API を実装してみましょう．

## 実装の流れ
Bamboo による API 開発のほとんどの作業は，Endpoint クラスの定義です．Endpoint クラスはサーバー内の1つのエンドポイントに対応しており，以下のように HTTP メソッドに対応するコールバック関数を Endpoint クラスのインスタンスメソッドとして定義できます．その際，コールバック関数の名前は **do_(METHOD)** という命名規則に従います (具体例は下記のコードスニペットを参考)．また，扱うつもりのない HTTP メソッドに対応するコールバック関数は定義する必要はありません．もし定義しなければ，Endpoint はその HTTP メソッドに対応していないことになり，もしクライアントからアクセスがあれば自動的にエラーが返されます．

```python
@app.route("image")
class MockImageEndpoint(Endpoint):

    # GET メソッドに対応するコールバック
    def do_GET(self) -> None:
        """画像の取得処理をする"""
        ...

    # DELETE メソッドに対応するコールバック
    def do_DELETE(self) -> None:
        """画像の消去処理をする"""
        ...

    # POST メソッドに対応するコールバック
    def do_POST(self) -> None:
        """画像の登録処理をする"""
        ...

    # PUT メソッドに対応するコールバック
    def do_PUT(self) -> None:
        """画像の変更処理をする"""
        ...
```

上述したように，API の実装のほとんどは Endpoint クラスの実装ですが，Endpoint クラスの実装は以下の流れで行います:

1. URI を決める
2. setup メソッドに初期化処理を書く (省略可)
3. 内部ロジックを実装する


## Endpoint の実装

### サンプル API の概要
今回作成するサンプル API の機能は**リクエストで送られてきたテキストを反転させて返す**というものです．例えば，

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
エンドポイントには1つの URI を指定する必要があります．これは App オブジェクトがクライアントからのリクエスト URI をルーティングするために必要な情報であり**必須**です．Bamboo で URI を指定する上では Location という概念について知っておく必要があります．まず以下の URI を見てください:

```
http://localhost:8000/john0401/info/
```

上記の URI はユーザーID john0401 のユーザーの情報を取得するための URI だとします．この URI のホスト名以下のパスを分解してみましょう:

```python
(john0401, info)
```

パスは1つ1つのノード名で分割されますが，このノード名のことを Bamboo では Location と呼びます．つまり Bamboo において URI とは Location のタプルです．また，Location には2つのタイプがあります:

1. 静的 Location
2. フレキシブル Location

例えば以下の例を見てください:

```
http://localhost:8000/john0401/info/
http://localhost:8000/linda1010/info/
```

この2つの URI のパスを Location で分割すると

```
(john0401, info)
(linda1010, info)
```

となります．どちらも2つの Location で分割されていますが，後方の Location である 'info' はユーザーの情報を表すための Location です．つまり，ユーザーIDが違うだけでサーバーアプリケーションの内部ロジックは同じはずです．一方で，前方のユーザーIDはユーザーによって変わりえます．Bamboo ではこのように，クライアントにより変化する Location のことをフレキシブル Location と呼んでいます．また，フレキシブル Location でないものを静的 Location と呼んでいます．Bamboo では静的 Location は **str**, フレキシブル Location は **FlexibleLocation** 型で表されます．

今回のサンプル API ではフレキシブル Location は使用しません．そこで，今回作成する Endpoint クラスを UpsideDownEndpoint と名付け，その URI を

```
(upsidedown,)
```

と定義しましょう．URI は App オブジェクトに以下のようにして登録します．

```python
import bamboo

app = bamboo.App

@app.route("upsidedown")
class UpsideDownEndpoint(bamboo.Endpoint):
    pass
```

### setup メソッドに初期化処理を書く
Endpoint クラスには setup メソッドというインスタンスメソッドがあります．setup メソッドは Endpoint クラスのサブクラスのインスタンスが生成された際に呼び出されます．App オブジェクトはクライアントからリクエストが来てリクエストされた URI に対応する Endpoint を見つけると次のような処理を行います:

1. Endpoint のインスタンスを作る (インスタンスの初期化)
2. setup メソッドを呼び出す
3. リクエストされた HTTP メソッドに対応するコールバックを呼び出す

つまり，setup はコールバック関数の前に実行される関数です．通常はこのメソッドを定義しなくても問題なく動作します (このサンプルでも定義しません)．ただし，Endpoint に拡張性を持たせたい場合などは便利です．なぜなら，Bamboo には setup メソッドの引数を App オブジェクト経由で渡す機能があるからです:

```python
# データベースを操作するオブジェクト db を App オブジェクト経由で渡す
@app.route("mock", parcel=(db,))
class MockEndpoint(Endpoint):
    
    def setup(self, db):
        # コールバック関数で使えるようにインスタンス変数として代入
        self.db = db
```

上のコードスニペットだけ見ると，単に回りくどい方法で db オブジェクトを渡しているだけのように見えますが，次の例ではどうでしょうか:

```python
# FILE A
##################################################################
class MockEndpoint(Endpoint):
    
    def setup(self, db):
        self.db = db
##################################################################

# FILE B
##################################################################
from mock import MockEndpoint

app.route("mock", parcel=(db,))(MockEndpoint)
##################################################################
```

このように setup メソッドを上手く活用すれば，実装した Endpoint サブクラスに拡張性を持たせたり，そのクラスを配布可能にすることが出来ます．

### 内部ロジックを実装する
次に最も重要な工程である内部ロジックの実装に移りましょう．内部ロジックの実装はサポートしたい HTTP メソッドに対応するコールバックごとに行います．下表は HTTP メソッドとコールバック名の対応表です．

|   HTTP Method     |   コールバック名  |
| :---------------: | :---------------: |
|       GET         |       do_GET      |
|       POST        |       do_POST     |
|       PUT         |       do_PUT      |
|       DELETE      |       do_DELETE   |
|       HEAD        |       do_HEAD     |
|       OPTIONS     |       do_OPTIONS  |

これらのコールバックは全て実装する必要はありません．実装したいものだけ実装すれば OK です．また，複数のコールバックを実装することも可能です．ただし，コールバックの機能と HTTP メソッドの意味がマッチするように注意しましょう．例えば，画像のアップロードを行うのに，GET メソッドや DELETE メソッドを実装すると挙動と命令が噛み合いません．

今回はリクエスト内容を逆さまにして返すということで，サーバーにデータは保存されません．なので，強いて選ぶなら GET メソッドがいいでしょう．それでは GET メソッドに対応するコールバックを実装します:

```python
from dataclasses import dataclass

@dataclass
class UnpsideDownRequest:
    token: str
    
@dataclass
class UpsideDownResponse:
    result: str

@app.route("upsidedown")
class UpsideDownEndpoint(bamboo.Endpoint):

    # 入出力データフォーマットの登録
    @bamboo.data_format(input=UnpsideDownRequest, output=UpsideDownResponse)
    def do_GET(self, req_body: UnpsideDownRequest) -> None:
        token = req_body.token
        result = token[::-1]

        body = {"result": result}
        self.send_json(body)
```

上の例で，コールバック関数である *do_GET* に *data_format* というデコレータでデコレートしているのがわかるでしょうか．このデコレータは入出力データフォーマットを登録するためもので，*input* 引数にリクエストボディのJSONデータのスキーマを，*output* 引数にレスポンスボディのJSONデータのスキーマを *dataclass* でデコレーとしたデータクラスを登録することが出来ます．特に，*input* 引数に登録すると，リクエストボディをデコードしたデータをコールバックの引数として受け取れます．

*data_format*によるデコレートは必須ではありませんが，特に理由のない場合はデコレートすることをおすすめします．なぜなら，コールバックにデコレートすることで，そのコールバックの性質がわかりやすくなるからです．もし，このようなデコレーションがなければ内部ロジックを読んでコールバックの性質を読み取る必要が出てきてしまいます．また，Bamboo にはこの他にもコールバックの性質を定義する様々なデコレータがありますので，積極的にデコレートを行うことをおすすめします．


## サーバーを起動する
最後にサーバーを起動します．今回は簡易的に Python の wsgiref で実装されているサーバーアプリケーションを利用します．

```python
from dataclasses import dataclass
from wsgiref.simple_server import make_server

from bamboo import App, Endpoint, data_format

app = App()

@dataclass
class UnpsideDownRequest:    
    token: str
    
@dataclass
class UpsideDownResponse:
    result: str

@app.route("upsidedown")
class UpsideDownEndpoint(Endpoint):

    @data_format(input=UnpsideDownRequest, output=UpsideDownResponse)
    def do_GET(self, req_body: UnpsideDownRequest) -> None:
        token = req_body.token
        result = token[::-1]

        body = {"result": result}
        self.send_json(body)

if __name__ == "__main__":
    HOST_ADDRESS = ("localhost", 8000)
    server = make_server("", 8000, app)

    try:
        print(f"Hosting on : {HOST_ADDRESS}...")
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        print()

```

## クライアントサイドの処理
ここまでは bamboo によるサーバーサイドの処理でした．実験をするためにはクライアントサイドの処理も当然必要になります．ここでは，クライアントサイドの処理にはサードパーティ製の *requests* ライブラリを使用することにしましょう．

```python
import json
import sys

import requests

def request(uri: str, token: str) -> None:
    body = {"token": token}
    data = json.dumps(body).encode()
    res = requests.get(uri, data=data)
    
    # レスポンスヘッダの表示
    print("Headers")
    print("-------")
    for k, v in res.headers.items():
        print(f"{k} : {v}")
    print()
    
    # レスポンスボディの表示
    content = json.loads(res.content)
    print("Bodies")
    print("------")
    for k, v in content.items():
        print(f"{k} : {v}")
    print()
    
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
$ python serve.py
```

実行し，正常に動作すると

```
Hosting on : ('localhost', 8000)...
```

と表示されます．

### クライアント側
サーバー側の実行が終わったら，別のターミナルで以下のコマンドを実行しましょう．ただし，先程実装したクライアントサイドのスクリプトは request.py で保存したと仮定します．

```
$ python request.py abcdefg
```

実行後，ターミナルに以下のように表示されたら成功です．

```
Headers
-------
Date : Tue, 02 Feb 2021 08:45:03 GMT
Server : WSGIServer/0.2 CPython/3.8.5
Content-Length : 21

Bodies
------
{'result': 'gfedcba'}
```

レスポンスボディの結果にコマンドライン引数で指定したトークン (上の例では abcdefg) が逆さまになって返ってきていることを確認しましょう．また，他のトークンを指定しても同様の結果になるか確認してみましょう．

## その他のサンプル
今回のサンプル API の他にも様々なサンプルが [bamboo/example](../../example/) 内にあります．実際に実行してみると段々コツが掴めていくかもしれません．
