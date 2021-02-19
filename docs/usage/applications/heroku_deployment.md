# Heroku を利用したアプリケーションのデプロイ
[Heroku](https://devcenter.heroku.com/) を利用すれば Web アプリケーションを簡単にデプロイすることが出来ます．本ドキュメントでは，Bamboo を用いて作成した Web アプリケーションを Heroku を利用してデプロイする方法について説明します．本ドキュメントでは以下のような流れで順に説明します:

1. Heroku へのユーザー登録，Heroku CLI のインストール
2. Bamboo による Web アプリケーションの作成
3. ローカルでのテスト
4. Heroku を利用したデプロイ

## まず最初に
初めに Heroku にユーザー登録をし，Heroku CLI をインストールする必要があります．具体的な方法については[こちら](https://devcenter.heroku.com/articles/getting-started-with-python)を参照してください．

これと同時に必要になる Python ライブラリをインストールしておきましょう．ここでは Python は 3.8 系を仮定します (3.8 以上なら動作します) ．

```
$ pip install bamboo-core requests gunicorn
```

## Bamboo による Web アプリケーションの作成
Bamboo を用いた Web アプリケーションは[チュートリアル](../README.md#チュートリアル)で説明されている通りに製作することが出来ます．Bamboo についての詳細はチュートリアルを参照してください．今回は簡易的な Web アプリケーションを製作することにしましょう．本ドキュメントで作成する Web アプリケーションをより複雑化させることによって，高度なアプリケーションの構築を行えるはずです．

今回は簡易的な Web アプリケーションとして，ただ `Hello, World!` をレスポンスとして送信する Web アプリケーションを作ります．以下にサーバーサイドの実装を示します (ここでは hello.py として保存します):

```python
import bamboo

app = bamboo.App()

class HelloData(bamboo.JsonApiData):
    text: str
    
@app.route("hello")
class HelloEndpoint(bamboo.Endpoint):
    
    @bamboo.data_format(input=None, output=HelloData)
    def do_GET(self) -> None:
        body = {"text": "Hello, World!"}
        self.send_json(body)
```

## ローカルでのテスト
デプロイする前にローカルでテストを行い，アプリケーションが正常に動作するか確認しておくのが好ましいです．そのためにまず，クライアントサイドのスクリプトを用意しておきましょう．今回は `requests` ライブラリを使用してスクリプトを作成します (ここでは request.py として保存します) :

```python
import json
import requests

def main(root: str):
    URI = f"{root}/hello"
    
    res = requests.get(URI)
    if res.ok:
        body = json.loads(res.content)
        print(f"Response: {body['text']}")
    else:
        print(f"Error occured. Status code: {res.status_code}")
        
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    
    args = parser.parse_args()
    if args.debug:
        root = "http://localhost:8000"
    else:
        # TODO EDIT host name
        # ここは後ほど設定されるホスト名に編集する
        root = "https://XXXXXXXXXXXXXXXXXXXX.herokuapp.com"

    main(root)
```

それでは準備が整ったのでローカルでのテストを行いましょう．まずは gunicorn 上で先程実装した Web アプリケーションを起動させます:

```
$ gunicorn hello:app --log-file=-
```

次に別のターミナル上でクライアント用のスクリプトを実行します:

```
$ python request.py --debug
```

正常に動作していれば，

```
Response: Hello, World!
```

が出力されるはずです．

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

最後に作成したリモートリポジトリにコミット内容をプッシュすることでデプロイを行います:

```
$ git push heroku origin
```

上記コマンドを実行するとデプロイが開始し，正常に完了すると

```
remote:        https://XXXXXXXXXXXXXXXXXXX.herokuapp.com/ deployed to Heroku
```

のようなメッセージが出力されるはずです．特に `https://XXXXXXXXXXXXXXXXXXX.herokuapp.com/` の部分はデプロイされたアプリケーションのホスト名なので，コピーして先程作成したクライアント用のスクリプトの `TODO` の部分に貼り付けて上書きしましょう．

最後に，PC から Heroku でデプロイしたアプリケーションに正常にアクセスできるが確認して終了です．クライアント用のスクリプトを実行させ，ローカルでのテストのときと同じ出力が得られるか確認しましょう:

```
python request.py
```

以下のメッセージが出力されれば成功です．

``````
Response: Hello, World!
``````

## このさきの開発
ここまで出来れば後は自分のアプリケーションをどんどん大きくしていくだけです．今回は1つのエンドポイントを持つアプリケーションでしたが，より多くのエンドポイントを定義して大きなサービスを扱うことが出来ます．その過程でデータベースを導入し，MVC モデルで実装を行えば洗練されたアプリケーションが出来上がるかもしれません．その中で Bamboo の様々な hackable な機能を使用することになるでしょう．
