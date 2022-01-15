# ヘッダーの取扱い

HTTP ヘッダーは通信のメタデータとして非常に重要な情報です．`bamboo` では HTTP ヘッダーに対するいくつかのアクセスを用意しています．

## 低水準な API

まずは低水準な API について説明します．この方法は低水準ではありますが，それはすなわちヘッダーの取扱いに対して開発者の権限が大きいことを意味します．例えば，エンドポイントのレスポンスメソッド内で `EndpointBase.get_header()` メソッドを使用することでヘッダー情報を `str` オブジェクトとして取得することが出来ます：

```python
from bamboo import WSGIEndpoint

class CustomEndpoint(WSGIEndpoint):

    def do_GET(self) -> None:
        user_agent = self.get_header("User-Agent")

        # user_agent を使用してユーザーエージェントによって異なる処理を行える
        if user_agent == "...":
            ...
```

ここで，`EndpointBase.get_header()` メソッドの引数であるヘッダー名は大文字・小文字を区別しないこと，アンダーバー `_` はハイフン `-` と解釈されることに注意してください．

上記の API は最も低水準な方法であり，そのためオーバーヘッドが最も低い方法一つです．しかし，後述する*宣言的な API* に比べて一目でどのようなヘッダーを必要としているエンドポイントなのかがわかりにくいというデメリットがあります．

## 宣言的な高水準 API

次に宣言的な API を紹介します．これは `bamboo.sticky` モジュールの `has_header_of()` デコレータを使用する方法です．例えば，この宣言的な API を使用して上記の例と等価な処理を実行するには，以下のように記述します：

```python
import typing as t

from bamboo import WSGIEndpoint
from bamboo.sticky import has_header_of

class CustomEndpoint(WSGIEndpoint):

    @has_header_of("User-Agent")
    def do_GET(self, user_agent: t:Optional[str]) -> None:
        # user_agent を使用してユーザーエージェントによって異なる処理を行える
        if user_agent == "...":
            ...
```

上記の例では*低水準な API* の例に比べて，`has_header_of()` デコレータを使用することでレスポンスメソッド内のロジックに関与する引数として定義できている点で，宣言的であると言えます．

`has_header_of()` デコレータには `err` 引数があり，この引数はデフォルト `None` です．このとき `has_header_of()` デコレータは，もし指定したヘッダーが見つからなくても例外を送出することはありません．一方，この引数に `ErrInfo` サブクラスを指定すると，もし指定したヘッダーが見つからない場合，指定した `err` 引数が例外として送出されます．例えば，以下の例では `User-Agent` ヘッダーが存在しない場合 `UserAgentHeaderNotFoundErrInfo` を例外として送出します：

```python
from bamboo import ErrInfo, HTTPStatus, WSGIEndpoint
from bamboo.sticky import has_header_of

class UserAgentHeaderNotFoundErrInfo(ErrInfo):

    http_status = HTTPStatus.BAD_REQUEST

    def get_body(self) -> bytes:
        return b"Header 'User-Agent' not found."

class CustomEndpoint(WSGIEndpoint):

    @has_header_of("User-Agent", err=UserAgentHeaderNotFoundErrInfo())
    def do_GET(self, user_agent: str) -> None:
        # user_agent を使用してユーザーエージェントによって異なる処理を行える
        if user_agent == "...":
            ...
```

上記の例では，レスポンスメソッドの引数である `user_agent` が `str` オブジェクトであることが保証されるという点に注意してください．

## 低水準 API を使用して独自のデコレータを実装する

最後に `has_header_of()` のような宣言的で再利用可能なデコレータを定義する方法を紹介します．この方法はレスポンスメソッドを全て定義できてしまうほど強力な方法なので，デコレータの実行コンテキストについては注意が必要です．例えば今回の場合はヘッダーの処理について記述したいので，定義するデコレータ内ではヘッダーに関する処理のみを行います．

それでは，以下ではブラウザからのアクセスを拒否する雑な実装をしてみましょう．今回は `User-Agent` ヘッダーの値の先頭に `Mozilla` の文字が含まれている場合，そのユーザーエージェントはブラウザであると判断し例外を送出して処理を中断することにします（ここでは簡単のため `WSGIEndpoint` のみに対応したデコレータを定義します）：

```python
from functools
import typing as t

from bamboo import ErrInfo, WSGIEndpoint
# 型変数をインポート（任意）
from bamboo.sticky import Callback_WSGI_t

class BrowserRequestErrInfo(ErrInfo):

    def get_body(self) -> bytes:
        return b"Access from browsers are forbidden."

def pass_except_for_browsers(callback: Callback_WSGI_t) -> Callback_WSGI_t:

    @functools.wraps(callback)
    def response_method(self: WSGIEndpoint, *args) -> None:
        user_agent = self.get_header("User-Agent")
        if user_agent.startswith("Mozilla"):
            raise BrowserRequestErrInfo()

        callback(self, *args)

    return response_method
```

上記で定義した `pass_except_for_browsers()` デコレータは以下のようにして使用できます：

```python
class CustomEndpoint(WSGIEndpoint):

    @pass_except_for_browsers
    def do_GET(self) -> None:
        ...

    @pass_except_for_browsers
    def do_POST(self) -> None:
        ...
```

このように，独自にデコレータを定義して，それらを用いてレスポンスメソッドをデコレートすることで，拡張性の高い宣言的なコーディングを行えるようになります．

ちなみに，上記の `pass_except_for_browsers()` デコレータは `has_header_of()` デコレータを使用して実装することも出来ます（厳密にはデコレータを返す関数です）：

```python
from functools
import typing as t

from bamboo import ErrInfo, WSGIEndpoint
from bamboo.sticky import Callback_WSGI_t

Decorator_t = t.Callable[[Callback_WSGI_t], Callback_WSGI_t]

def pass_except_for_browsers(err: t.Optional[ErrInfo], add_arg: bool = True) -> Decorator_t:

    def decorator(callback: Callback_WSGI_t) -> Callback_WSGI_t:

        @functools.wraps(callback)
        @has_header_of("User-Agent", err=err)
        def response_method(self: WSGIEndpoint, user_agent: t.Optional[str], *args) -> None:
            if user_agent.startswith("Mozilla"):
                raise BrowserRequestErrInfo()

            if add_arg:
                callback(self, user_agent, *args)
            else:
                callback(self, *args)

        return response_method

    return decorator
```

上記実装を見ると，関数内に2つの関数が内包されており，やや複雑に感じられるかもしれません．まず `pass_except_for_browsers()` は厳密にはデコレータを返す関数であり，デコレータ内の処理に対してパラメータを与えるために定義されています（具体的には `err` 引数，`add_arg` 引数を定義）．次に `decorator()` という内部の関数はその名の通りデコレータであり，レスポンスメソッドをデコレートします．最後に `response_method` はデコレータによって拡張されたレスポンスメソッドであり，デコレートされるレスポンスメソッド内の処理を行う前に，`User-Agent` ヘッダーに対する処理を行っています．

## ヘッダー処理の方針

HTTP ヘッダーの中には，そのリクエストにおける補助的な役割を担うものや，大方のロジックを決定する情報として振る舞うものもあります．ヘッダーに関係する全ての処理をデコレータで実装し，内部ロジックを隠蔽することは事実上可能ですが，内部ロジックを完全に隠蔽することはレスポンスメソッドの可読性を損なう可能性があるため推奨されません．推奨されるヘッダー処理の方針としては，以下のような方針が考えられます：

1. 対象のヘッダーが内部ロジックにおいて補助的な役割を担う場合，デコレータを作成しレスポンスメソッドをデコレートする
2. 対象のヘッダーが内部ロジックにおいて中心的な役割を担う場合，`has_header_of()` デコレータを使用して実装する

開発者が最も重要視すべきことは，**レスポンスメソッドの実装を見るだけで内部ロジックと API を同時に把握することができるかどうか**です．例えば，前項で記述した

```python
class CustomEndpoint(WSGIEndpoint):

    @pass_except_for_browsers
    def do_GET(self) -> None:
        ...

    @pass_except_for_browsers
    def do_POST(self) -> None:
        ...
```

のようなコードを見て，開発者が **`CustomEndpoint` に `GET` または `POST` メソッドでアクセス出来るのはブラウザ以外である**と判断できれば，それで良いわけです．そのような状態を実現するためには，独自のデコレータを実装する際にデコレータ名でその挙動を説明出来る程度の処理のみ記述することが効果的です．
