# クエリパラメータの取扱い

クエリパラメータはエンドポイントに与えるパラメータとして URI に埋め込むことが出来る情報の一種であり，アプリケーションの API 作成時には大きな役割を担います．`bamboo` ではこのクエリパラメータに対するいくつかのアクセスが用意されています．

## 低水準な API

ここではまず最も低水準な API について説明します．クエリパラメータに対するより細かい制御を行いたい場合は，この方法が有効です．開発者は `EndpointBase.get_queries()` メソッドを使用して，クエリパラメータを取り出すことが出来ます．

```python
from bamboo import WSGIEndpoint

class CustomEndpoint(WSGIEndpoint):

    def do_GET(self) -> None:
        # 以下のような URI の場合にクエリパラメータ token を取り出す
        # https://example.com/signup?token=AAAAAAAAAAAAA
        token = self.get_queries("token")
        assert isinstance(token, list)

        # 以下 token を用いて処理を行う
```

ここで，`get_queries()` メソッドの返り値は `str` オブジェクトの `list` である点に注意してください．これは同一パラメータの複数指定を許容するもので，例えば `https://example.com/query?a=AAA,a=AAB,a=AAC` という URI のクエリパラメータ `a` を `get_queries()` メソッドによって抽出すると，`["AAA", "AAB", "AAC"]` という `list` が返されます．

上記の API は `bamboo` におけるものとしては最も低水準なクエリパラメータへのアクセス方法で，それゆえオーバーヘッドは大きくありません．もし，クエリパラメータの処理を完全に開発者側でカスタマイズしたい場合には，この方法を取ることが最善です．

## 宣言的な高水準 API

次にクエリパラメータへのアクセスを提供する宣言的な API を紹介します．これは `bamboo.sticky` モジュールの `has_query_of()` デコレータ（厳密にはデコレータを返す関数）を使用する方法です．このデコレータを使用すると，上記の例は以下のように記述できます：

```python
import typing as t

from bamboo import WSGIEndpoint
from bamboo.sticky import has_query_of

class CustomEndpoint(WSGIEndpoint):

    @has_query_of("token")
    def do_GET(self, token: t.List[str]) -> None:
        # 以下 token を用いて処理を行う
```

この方法を取ることで，開発者にとってクエリパラメータ `token` はレスポンスメソッドにおける引数であるかのように見せかけることができ，それゆえレスポンスメソッド内にはコアな内部ロジックのみに絞って記述することが出来ます．また，デコレータを用いることで可読性が向上し，**`token` というクエリパラメータを許容するレスポンスである**という点をはっきりさせることが出来ます．

### 複数種類のクエリパラメータ

これまでは単一種類のクエリパラメータ（例として `token`）のみを扱ってきましたが，複数種類のクエリパラメータを扱うことも出来ます．例えば，リクエストに時間の情報をクエリパラメータとして指定することで，レスポンスの内容を変化させることが出来るアプリケーションを考えてみましょう．ここで時間を範囲で指定できるとして，その範囲の下限を示す `after` と上限を示す `before` というクエリパラメータを用意するとします．その場合，以下のように記述することが出来ます：

```python
class CustomEndpoint(WSGIEndpoint):

    @has_query_of("before")
    @has_query_of("after")
    def do_GET(self, after: t.List[str], before: t.List[str]) -> None:
        # 以下 after と before を用いて処理を行う
```

ここで，`after` や `before` といった引数は `has_query_of()` がリクエストを解析することで勝手に指定してくれるものであり，開発者自らが指定するものではない点に注意してください．

### `err_empty` 引数

`has_query_of()` 関数には `err_empty` という引数があります．これは `bamboo` におけるエラーを扱う `ErrInfo` オブジェクトまたは `None` を取る引数で，デフォルトは `None` です．この引数が `None` のとき，リクエストされた URI に指定したクエリパラメータが一つも含まれなくてもエラーは発生せず，この場合は空の `list` が `after` や `before` などの引数に入ります．一方，`err_empty` 引数に `ErrInfo` オブジェクトを指定した場合は，もし指定したクエリパラメータが一つも含まれなかったらその例外が送出されます．

例えば，クエリパラメータ `after` および `before` は必ず指定しなければいけないと制限する場合，以下のように実装できます：

```python
from bamboo import ErrInfo

class QueryParamNotExistsErrInfo(ErrInfo):

    def get_body(self) -> bytes:
        return b"Required query parameter was not found."

class CustomEndpoint(WSGIEndpoint):

    @has_query_of("before", err_empty=QueryParamNotExistsErrInfo)
    @has_query_of("after", err_empty=QueryParamNotExistsErrInfo)
    def do_GET(self, after: t.List[str], before: t.List[str]) -> None:
        assert len(after) >= 1
        assert len(before) >= 1

        # 以下 after と before を用いて処理を行う
```

このように `err_empty` 引数によって，目的のクエリパラメータが必ず1つ以上指定されることを保証できます．

### `err_not_unique` 引数

`err_empty` と似たような引数として `err_not_unique` 引数というものがあります．これも `err_empty` 引数と同様に，`ErrInfo` オブジェクトまたは `None` を取る引数で，デフォルトは `None` です．この引数が `None` のとき，単一種類のクエリパラメータの複数回の指定が許容されます．例えば，上記の例では `after` の `list` の長さは2以上である可能性があります．しかし，このような単一パラメータが複数値を取るような状況は，処理する上で曖昧さをもたらすことになるため（例えば `after` の値が複数個あると，特別なルールを設けない限りどの値を時間の下限ととるべきかを判断することが出来ません），あまり好ましいことではない場合が多々あります．そのような場合には，`err_not_unique` 引数に `ErrInfo` オブジェクトを指定することで，もし目的のクエリパラメータが複数値をとる場合，指定した例外が送出されるように設定することが出来ます．

例えば，クエリパラメータ `after` および `before` は複数値をとってはいけないとする場合，以下のように実装できます：

```python
from bamboo import ErrInfo

class DuplicatedQueryParamErrInfo(ErrInfo):

    def get_body(self) -> bytes:
        return b"Duplicated query parameters were found."

class CustomEndpoint(WSGIEndpoint):

    @has_query_of("before", err_not_unique=DuplicatedQueryParamErrInfo)
    @has_query_of("after", err_not_unique=DuplicatedQueryParamErrInfo)
    def do_GET(self, after: t.Optional[str], before: t.Optional[str]) -> None:
        # 以下 after と before を用いて処理を行う
```

上記のコードでは，`after` および `before` 引数はもはや `list` ではない点に注意してください．これらの引数は，対応するクエリパラメータが指定されなかった場合は `None` が指定され，指定された場合はその値が `str` オブジェクトとして指定されます．

`err_empty` 引数と `err_not_unique` 引数を同時に与えることによって，**目的のクエリパラメータは必ず指定されなければならず重複もしない**ということを保証できるようになります．例えば，上記2つの例をミックスして以下のように実装できます：

```python
class QueryParamNotExistsErrInfo(ErrInfo):

    def get_body(self) -> bytes:
        return b"Required query parameter was not found."


class DuplicatedQueryParamErrInfo(ErrInfo):

    def get_body(self) -> bytes:
        return b"Duplicated query parameters were found."

class CustomEndpoint(WSGIEndpoint):

    @has_query_of(
        "before",
        err_empty=QueryParamNotExistsErrInfo,
        err_not_unique=DuplicatedQueryParamErrInfo,
    )
    @has_query_of(
        "after",
        err_empty=QueryParamNotExistsErrInfo,
        err_not_unique=DuplicatedQueryParamErrInfo,
    )
    def do_GET(self, after: str, before: str) -> None:
        # 以下 after と before を用いて処理を行う
```

## `mapf` 引数

上2つの引数が**クエリパラメータの個数**を制御できる引数であったのに対し，この `mapf` 引数は**クエリパラメータの値**を制御できる引数です．この引数は関数または `None` を引数にとり，デフォルトは `None` です．この引数に与えることが出来る関数は，引数が1つであるもの
