# ベースイメージは slim 版で軽量化
FROM python:3.11-slim

# 不要レイヤー削減のためキャッシュなし、かつロケール設定
ENV PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501

# 作業ディレクトリ
WORKDIR /app

# 1) 依存だけ先にコピーしてキャッシュ活用
COPY requirements.txt ./
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential gfortran libatlas-base-dev liblapack-dev \
    && pip install --no-cache-dir \
       --no-binary numpy,pandas,matplotlib,plotly,yfinance \
       -r requirements.txt \
    && apt-get purge -y \
       build-essential gfortran libatlas-base-dev liblapack-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# 2) アプリ本体をコピー（.dockerignore で .devcontainer/.git を除外）
COPY . .

# 3) 公開ポート
EXPOSE 8501

# 4) エントリーポイントとして Streamlit を実行
CMD ["streamlit", "run", "app.py"]