# LangGraph Agent with Chainlit

LangGraphによるシンプルなエージェントを、ChainlitでWebアプリとして利用できるようにします。

詳細は以下の記事で解説しています。

- 最初の実装の記事
  - https://zenn.dev/0msys/articles/9873e25a610c5e
- マルチモーダル対応の記事
  - https://zenn.dev/0msys/articles/3d38729aa7f75b
- ライブラリアップデートの記事
  - https://zenn.dev/0msys/articles/49ebb76cea1af6

## 使い方

### 起動方法

リポジトリをクローンします。

graph_agent.envを作成し、以下の内容を記述します。

```
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
```

以下のコマンドを実行します。

```
docker compose up -d
```

http://localhost:8000 にアクセスします。


### 終了方法

以下のコマンドを実行する。

```
docker compose down
```

### 開発方法

自作Toolを追加するなど、開発を行う場合は、このディレクトリをdevcontainerとして開いてください。

devcontainerが開いたら、以下のコマンドを実行してください。

```
chainlit run -w src/main.py
```

http://localhost:8000 にアクセスすると、画面を確認しながら開発を行うことができます。


#### Agentのみの起動確認

ChainlitとLangGraphどちらも更新頻度が高いため、動かなかったときにどちらが原因かを特定しやすくするために、Agentのみを起動する方法を用意しています。

開発コンテナ上で以下のコマンドを実行してください。

```
python src/test_agent.py
```

これで、Agentのみが起動し、動作を確認することができます。
"stream" or "invoke"のどちらかを引数に渡すことで、それぞれの動作を確認することができます。

```
python src/test_agent.py invoke
```
(何も渡さない場合は、"stream"がデフォルトで実行されます。)
