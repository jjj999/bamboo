# ルーティング

## ロケーション
今回のサンプルでは上記のような URI の定義で構わないのですが，より本格的な URI を定義するためには Location という概念について知っておく必要があります．次の URI を見てください:

```
http://localhost:8000/john0401/info/
```

上記の URI はユーザーID john0401 のユーザーの情報を取得するための URI だと仮定しましょう．この URI のホスト名以下のパスを分解してみます:

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

となります．どちらも2つの Location で分割されていますが，後方の Location である 'info' はユーザーの情報を表すための Location です．つまり，ユーザーIDが違うだけでサーバーアプリケーションの内部ロジックは同じはずです．一方で，前方のユーザーIDはユーザーによって変わりえます．Bamboo ではこのように，クライアントにより変化する Location のことを**フレキシブル Location** と呼んでいます．また，フレキシブル Location でないものを**静的 Location** と呼んでいます．Bamboo では**静的 Location は str**, **フレキシブル Location は FlexibleLocation 型**で表されます．

今回のサンプル API ではフレキシブル Location は使用しませんでした．先程のコードスニペットで指定したパスを Location で分割すると，

```
(upsidedown,)
```

となります．つまり，今回のエンドポイントの URI は1つの静的 Location により構成されていると言えます．