# LangGraph Agent with Chainlit

LangGraphによるシンプルなエージェントを、ChainlitでWebアプリとして利用できるようにします。

詳しくは[こちらの記事](https://zenn.dev/0msys/articles/9873e25a610c5e)を参照してください。


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
chainlit run -w main.py
```

http://localhost:8000 にアクセスすると、画面を確認しながら開発を行うことができます。

