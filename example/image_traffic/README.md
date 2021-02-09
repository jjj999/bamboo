# Image Traffic

## 概要
クライアントからリクエストを受けると単純に画像を返すアプリです．レスポンスとして以下のような画像を送信します．

![response](./elephant.jpg "response")

## 実行方法
以下のコマンドを実行して，サーバーとクライアントを起動します．

```
$ python image_traffic.py
```

### 結果
正常に動作すると，*receive.jpg* という画像が保存されます．サーバー側のログは *image_traffic.log* というファイルに出力されます．
