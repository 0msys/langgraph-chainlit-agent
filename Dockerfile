# ベースイメージとしてPython 3.12を使用
FROM python:3.12-bookworm

# ビルド時の引数を定義
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# ユーザーとグループを作成
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

# 環境変数を設定
ENV PYTHONUSERBASE=/home/$USERNAME/.local
ENV PATH=$PYTHONUSERBASE/bin:$PATH

# ユーザーを切り替え
USER $USERNAME

# 作業ディレクトリを設定
WORKDIR /workspace

# 必要なパッケージをインストール
RUN pip install --user --upgrade pip setuptools poetry

# ソースコードをコピー
COPY --chown=$USERNAME:$USERNAME . /workspace

# 依存関係をインストール
RUN poetry config virtualenvs.create true \
    && poetry install --no-dev --no-interaction --no-ansi

# アプリケーションを実行
CMD ["poetry", "run", "chainlit", "run", "src/main.py"]
