# アプリケーションのテスト
このドキュメントでは開発の際に欠かせないアプリケーションのテストについて述べます．Bamboo ではローカルでのサーバーのテストのためのいくらかのユーティリティを提供しています．以下では，このユーティリティを利用したテスト方法について説明していきます．

## 概要
アプリケーションを作成したらまずローカル環境でテストを実行することでしょう．しかし，サーバーのテストは少し厄介です．なぜなら，サーバーとクライアントという少なくとも2つのプロセスが存在するからです．ましてや，マイクロサービスのようなサーバーサイドで複数のサーバーアプリケーションがホスティングしている状態では，1つのサーバーアプリケーションにつきコマンドを叩いて起動していてはデバッグも捗りません．

このような事態を回避するために，Bamboo では `TestExecutor` というクラスが用意されています．このクラスを使用することによって，テスト用の1つのスクリプトを実行することでテストを行うことが出来ます．以下ではこの `TestExecutor` と Python 標準ライブラリの `unittest` を用いたテストスクリプトの作成方法について説明します．

## TestExecutor と ServerForm
`TestExecutor` はサーバー起動時に使用するフォームを定義する `ServerForm` オブジェクトを登録することで，子プロセスとしてサーバーアプリケーションを起動するオブジェクトです．`ServerForm` は単なる `dataclass` であり以下のようなインスタンス変数を持ちます:

- ホスト名 (IP アドレス) `hostname`
- ポート番号 `port`
- サーバーアプリケーション `app`
- ログ出力用のパス `path_log`

特にサーバーアプリケーションとは Bamboo によって実装された `App` オブジェクトのことです．また，`path_log` に指定されたログファイルは，サーバーが子プロセスで起動された後にそのプロセスの標準出力，標準エラー出力へ接続されます．

作成したフォームは `TestExecutor` 生成時に指定できます．以下では `app1` と `app2` という2つのサーバーアプリケーションについてテストすると仮定して `TestExecutor` オブジェクトを生成する例を示しています:

```python
from bamboo import ServerForm, TestExecutor

form1 = ServerForm("localhost", 8000, app1, "test_app1.log")
form2 = ServerForm("localhost", 8001, app2, "test_app2.log")

executor = TestExecutor(form1, form2)
```

ここまで来れば準備完了です．`TestExecutor` オブジェクトはコンテキストマネージャでもあり，`with` 文を使ってブロック内部で定義された処理を行う間のみ子プロセスでフォームに定義されたサーバーアプリケーションを起動することが出来ます．フォームに定義されたサーバーアプリケーションの起動には，`TestExecutor.start_serve()` メソッドを使います:

```python
with executor.start_serve():
    # クライアントの処理
```

`with` 文のブロック内に定義するクライアントの処理はテストしたい処理に依ります．`with` 文を使用しない場合，`start_serve()` メソッドによってサーバーアプリケーションを起動し，`close()` メソッドによって起動したサーバーアプリケーションを終了させることが出来ます．また，クライアントの処理が単一の関数で定義されている場合，`TestExecutor.exec()` メソッドを使用できます:

```python
def client_test():
    # クライアントの処理

# サーバーアプリケーションを起動しクライアント処理を実行
# クライアント処理の実行後にサーバーアプリケーションを終了
executor.exec(client_test)
```

## テストスクリプトの作成とテストの実行
上述した `TestExecutor` オブジェクトを利用してテストスクリプトを作成できます．ここでは Python 標準ライブラリである [unittest](https://docs.python.org/ja/3.8/library/unittest.html) を使用したテストスクリプトの作成方法について説明します．`unittest` についての説明は行いませんので，その詳細は公式ドキュメントを参照してください．

`unittest` では `unittest.TestCase` サブクラスを定義することでユニットテストの1つのケースを定義します．`TestCase` クラスには `setUpClass()` クラスメソッドと `tearDownClass()` クラスメソッドがあり，それぞれテスト開始時，終了時に一度だけ実行されるメソッドです．この2つのメソッドと `TestExecutor` を利用することで，以下のように `unittest` のアーキテクチャに即したテストケースを定義できます:

```python
import unittest

class UselessTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # テスト実行前に実行される
        # サーバーを起動
        form1 = ServerForm("localhost", 8000, app1, "test_app1.log")
        form2 = ServerForm("localhost", 8001, app2, "test_app2.log")

        self.executor = TestExecutor(form1, form2)
        self.executor.start_serve()

    @classmethod
    def tearDownClass(self):
        # テスト実行後に実行される
        # サーバーを停止
        self.executor.close()

    # テストメソッドの定義
    # クライアントサイドの処理を記述
    def test_something(self):
        ...

if __name__ == "__main__":
    unittest.main()
```

このようにテストスクリプトを定義することで `unittest` の機能をそのまま利用することが出来ます．テストを実行するためには作成したテストスクリプトを実行するだけです．Bamboo 開発用のテストスクリプトはほとんどがこの方法で書かれています．[bamboo/test](https://github.com/jjj999/bamboo/tree/master/test) ディレクトリ内のテストコードからテストスクリプト作成のヒントが得られるかもしれません．
