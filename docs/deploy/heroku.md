# Heroku を利用したアプリケーションのデプロイ
[Heroku](https://devcenter.heroku.com/) を利用すれば Web アプリケーションを簡単にデプロイすることが出来ます．本ドキュメントでは，Bamboo を用いて作成した Web アプリケーションを Heroku を利用してデプロイする方法について説明します．本ドキュメントでは以下のような流れで順に説明します:

1. Heroku へのユーザー登録，Heroku CLI のインストール
2. Bamboo による Web アプリケーションの作成
3. Heroku を利用したデプロイ

## まず最初に
初めに Heroku にユーザー登録をし，Heroku CLI をインストールする必要があります．具体的な方法については[こちら](https://devcenter.heroku.com/articles/getting-started-with-python)を参照してください．

これと同時に必要になる Python ライブラリをインストールしておきましょう．ここでは Python は 3.8 系を仮定します (3.8 以上なら動作します) ．

```
$ pip install bamboo-core requests gunicorn
```

## Bamboo による Web アプリケーションの作成
Bamboo を用いた Web アプリケーションの具体的な実装方法は[チュートリアル](../tutorials/concept/)を参照してください．今回は簡易的な Web アプリケーションを製作することにしましょう．

今回は例として，ただ `Hello, World!` をレスポンスとして送信する Web アプリケーションを作ります．以下にその実装を示します (ここでは hello.py として保存します):

```python
from bamboo import (
    JsonApiData,
    WSGIApp,
    WSGIEndpoint,
)
from bamboo.sticky.http import data_format

app = WSGIApp()

class HelloData(JsonApiData):
    text: str

@app.route("hello")
class HelloEndpoint(WSGIEndpoint):

    @data_format(input=None, output=HelloData)
    def do_GET(self) -> None:
        body = {"text": "Hello, World!"}
        self.send_json(body)
```

## Heroku を利用したデプロイ
Heroku でデプロイするには下記のファイル名と中身を持つファイルが必要です．ここまでで作成したファイルは[こちら](../../../example/heroku_deployment/)から参照できます．

- requirements.txt
    ```
    -i https://pypi.org/simple
    git+https://github.com/jjj999/bamboo.git@c26be5771e39bf8765fc9a3570e4c6b7fe7f3361#egg=bamboo
    gunicorn==20.0.4
    ```
- Procfile
    ```
    web: gunicorn hello:app --log-file=-
    ```
- runtime.txt
    ```
    python-3.8.7
    ```

上記のファイルを作成したら，新たに Git リポジトリを作成しましょう:

```
$ git init
$ git add *
$ git commit -m "First commit."
```

次に Heroku にログインし，リモートリポジトリを作成します:

```
$ heroku login
$ heroku create
$ git remote
heroku
```

最後に作成したリモートリポジトリにコミット内容をプッシュすることでデプロイを行います (デフォルトのブランチが main の場合は master ではなく main をプッシュしてください):

```
$ git push heroku master [or main]
```

上記コマンドを実行するとデプロイが開始し，正常に完了すると

```
remote:        https://XXXXXXXXXXXXXXXXXXX.herokuapp.com/ deployed to Heroku
```

のようなメッセージが出力されるはずです．特に `https://XXXXXXXXXXXXXXXXXXX.herokuapp.com/` の部分はデプロイされたアプリケーションのホスト名なので控えておきましょう．

## 通信テスト
デプロイが無事完了したらリクエストを送ってみましょう．

```python
from bamboo.request import https

def main(root: str):
    uri = f"{root}/hello"

    with https.get(uri) as res:
        if res.ok:
            body = json.loads(res.content)
            print(f"Response: {body['text']}")
        else:
            print(f"Error occured. Status code: {res.status_code}")

if __name__ == "__main__":
    # TODO EDIT host name
    # ここは後ほど設定されるホスト名に編集する
    root = "https://XXXXXXXXXXXXXXXXXXXX.herokuapp.com"
    main(root)
```
