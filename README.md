# kin-chan
King of Time リマインダ bot

## 構成
![](architecture.png)

## 開発環境構築
`bot/.env` ファイルを作成し環境変数を設定する。

``` :.env
KINGTIME_ADMIN_USERNAME=...
KINGTIME_ADMIN_PASSWORD=...
SLACK_API_TOKEN=...
SLACK_SIGNING_SECRET=...
```

サーバを起動する。

``` console
$ docker-compose up
```

データベースのテーブルを作成する。

``` console
$ docker-compose exec -T db psql -U postgres < db/schema.sql
```