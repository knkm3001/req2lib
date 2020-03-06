# req2lib - TUMSAT OPAC
amazonの欲しい物リストから図書館webサイト([TUMSAT OPAC](https://lib.s.kaiyodai.ac.jp/opac/opac_search/?lang=0))への書籍リクエスト自動化スクリプト

## About req2lib
Google Chrome を自動操作することによって、Amazonの公開されているほしい物リストから書籍とそのデータを取得  
その後、図書館webサイト(tumsat OPAC)にて
対象書籍を検索し、蔵書に含まれていなければ書籍リクエスト画面にて  
自動的にフォーム入力を行い、その本をリクエストする。  
また対象書籍の検索前に自身が行った過去の書籍リクエスト履歴を確認し、リクエストの重複を防ぐ。  
以上の動作をボタンひとつで自動的に行うのでとても便利!!  
headlessChrome(画面表示を行わない)にも対応。

## 注意!
過去にクローラを用いたことで以下のような事件が発生しました。  
※[岡崎市立中央図書館事件](https://ja.wikipedia.org/wiki/%E5%B2%A1%E5%B4%8E%E5%B8%82%E7%AB%8B%E4%B8%AD%E5%A4%AE%E5%9B%B3%E6%9B%B8%E9%A4%A8%E4%BA%8B%E4%BB%B6)... wikipediaより  
本スクリプトを利用する際は時間をおいて実行するなど、対象サーバに過度な不可をかけないよう十分に注意してご利用ください。


## 動作環境
dockerを用いるかどうかで準備が異なる。
- docker を利用する場合
  - docker 動作環境
- docker を利用しない場合
  - python 3.6 以上
  - Google Chrome
  - Chrome driver (使用するChromeのverに対応したものが必要)

  
## 使い方
以下 dockerを利用する場合を想定して説明を行う。
1. docker動作環境を構築
2. amazon にて任意の名前で公開されたほしい物リストを作成  
参考: [amazon ヘルプ](https://www.amazon.co.jp/gp/help/customer/display.html?nodeId=201936700)
1. `mkdir req2lib`
2. `cd req2lib`
1.  `git init && git pull https://github.com/knkm0301/req2lib.git`
3. `src/env_sample.py` を `src/env.py` にリネーム
4. `src/env.py` 内の変数を自身の設定に合わせて以下のように設定  
   - AMAZON_WISHLIST_URL ... アマゾンほしい物リスト(公開)のURL
   - REASON_FOR_PURCHASE ... リクエストフォーム必須項目。リクエストするすべての書籍にこの文字列が入力される(リクエスト完了後、書籍ごとに変更可能)
   - OPAC_ID             ... OPAC のログインID
   - OPAC_PW             ... OPAC のログインPW
5. `docker-compose up --build` を実行 (chromeのインストールに時間がかかる)
6. コンテナが立ち上がり、自動的に `python req2lib.py --headless` が実行、amazonのほしいものリストから書籍を取得し、OPAC にて検索、書籍リクエストをおこなう。  
※ req2lib.py はコンテナが起動されるたびに実行される。コンテナビルド後は `docker restart req2lib` をcron実行などすることで定期的に書籍リクエストが行える。

