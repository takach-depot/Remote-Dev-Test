import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# ページの設定
st.set_page_config(page_title="相場チェッカー", layout="wide")
st.title("💰 相場チェッカー")

# キャッシュ機能を使ってデータを取得する関数
@st.cache_data(ttl=3600)  # 1時間でキャッシュを更新
def get_market_data(tickers, period="10y"):
    """すべての相場データを取得してキャッシュする"""
    data = {}
    for ticker in tickers:
        try:
            ticker_data = yf.download(ticker, period=period, interval="1d")
            if not ticker_data.empty:
                data[ticker] = ticker_data
        except Exception as e:
            st.warning(f"{ticker}のデータ取得中にエラーが発生しました: {e}")
    return data

# 表示したいティッカーのリスト
tickers = ["JPY=X", "GC=F", "BTC-USD", "HG=F", "^N225", "^GSPC"]

# データの取得（10年分をキャッシュ）
with st.spinner('データを取得中...'):
    all_data = get_market_data(tickers)

# より安全なデータ取得方法
usdjpy = all_data.get("JPY=X", pd.DataFrame()).copy()
gold = all_data.get("GC=F", pd.DataFrame()).copy()
btc = all_data.get("BTC-USD", pd.DataFrame()).copy()
copper = all_data.get("HG=F", pd.DataFrame()).copy()
nikkei = all_data.get("^N225", pd.DataFrame()).copy()
sp500 = all_data.get("^GSPC", pd.DataFrame()).copy()

# データを簡素化（マルチインデックスがあれば解消）
def simplify_dataframe(df):
    # 単純な列名のデータフレームに変換
    if isinstance(df.columns, pd.MultiIndex):
        # マルチインデックスの場合は最初のレベルだけを使用
        df.columns = df.columns.get_level_values(0)
    return df

# 全てのデータフレームを簡素化
usdjpy = simplify_dataframe(usdjpy)
gold = simplify_dataframe(gold)
btc = simplify_dataframe(btc)
copper = simplify_dataframe(copper)
nikkei = simplify_dataframe(nikkei)
sp500 = simplify_dataframe(sp500)

# 期間設定用の選択ボックス
period = st.selectbox(
    "期間を選択してね",
    ("1ヶ月", "3ヶ月", "6ヶ月", "1年", "5年", "10年"),
    index=2
)

# 期間の日数マッピング
period_days = {
    "1ヶ月": 30,
    "3ヶ月": 90,
    "6ヶ月": 180,
    "1年": 365,
    "5年": 365 * 5,
    "10年": 365 * 10
}

# 選択された期間に基づいてデータをフィルタリング
end_date = datetime.now()
start_date = end_date - timedelta(days=period_days[period])

# 表示する相場の選択（チェックボックス）
st.write("表示する相場を選択してね👇")
col1, col2, col3 = st.columns(3)
with col1:
    show_usdjpy = st.checkbox("ドル円", value=True)
    show_nikkei = st.checkbox("日経平均", value=True)
with col2:
    show_sp500 = st.checkbox("S&P500（円建て）", value=True)
    show_gold = st.checkbox("金相場（円建て）", value=True)
with col3:
    show_copper = st.checkbox("銅相場（円建て）", value=True)
    show_btc = st.checkbox("ビットコイン（円建て）", value=True)

# データ処理部分
try:
    # 選択された期間でフィルタリング
    usdjpy = usdjpy.loc[start_date:end_date]
    gold = gold.loc[start_date:end_date]
    btc = btc.loc[start_date:end_date]
    copper = copper.loc[start_date:end_date]
    nikkei = nikkei.loc[start_date:end_date]
    sp500 = sp500.loc[start_date:end_date]
    
    # 共通日付を確認
    common_dates = sorted(list(set(usdjpy.index) & set(gold.index) & set(btc.index) & 
                            set(copper.index) & set(nikkei.index) & set(sp500.index)))
    
    if not common_dates:
        st.error("共通の日付がありません。期間を変更してみてください。")
        st.stop()
    
    # 新しいデータフレームを作成
    usdjpy_filtered = usdjpy.loc[common_dates]
    
    # 各相場をフィルタリング
    gold_filtered = gold.loc[common_dates]
    btc_filtered = btc.loc[common_dates]
    copper_filtered = copper.loc[common_dates]
    nikkei_filtered = nikkei.loc[common_dates]
    sp500_filtered = sp500.loc[common_dates]
    
    # 最新価格を取得（変化率計算用）
    latest_usdjpy = usdjpy_filtered['Close'].iloc[-1] if not usdjpy_filtered.empty else 0
    latest_nikkei = nikkei_filtered['Close'].iloc[-1] if not nikkei_filtered.empty else 0

    # 円建て変換部分を修正（行循環処理ではなくDataFrame演算に変更）
    # 金相場（円建て）
    gold_jpy = pd.DataFrame(index=common_dates)
    gold_jpy['Open'] = gold_filtered['Open'] * usdjpy_filtered['Open']
    gold_jpy['High'] = gold_filtered['High'] * usdjpy_filtered['High']
    gold_jpy['Low'] = gold_filtered['Low'] * usdjpy_filtered['Low']
    gold_jpy['Close'] = gold_filtered['Close'] * usdjpy_filtered['Close']
    
    # ビットコイン（円建て）
    btc_jpy = pd.DataFrame(index=common_dates)
    btc_jpy['Open'] = btc_filtered['Open'] * usdjpy_filtered['Open']
    btc_jpy['High'] = btc_filtered['High'] * usdjpy_filtered['High']
    btc_jpy['Low'] = btc_filtered['Low'] * usdjpy_filtered['Low']
    btc_jpy['Close'] = btc_filtered['Close'] * usdjpy_filtered['Close']
    
    # 銅相場（円建て）
    copper_jpy = pd.DataFrame(index=common_dates)
    copper_jpy['Open'] = copper_filtered['Open'] * usdjpy_filtered['Open']
    copper_jpy['High'] = copper_filtered['High'] * usdjpy_filtered['High']
    copper_jpy['Low'] = copper_filtered['Low'] * usdjpy_filtered['Low']
    copper_jpy['Close'] = copper_filtered['Close'] * usdjpy_filtered['Close']
    
    # S&P500（円建て）
    sp500_jpy = pd.DataFrame(index=common_dates)
    sp500_jpy['Open'] = sp500_filtered['Open'] * usdjpy_filtered['Open']
    sp500_jpy['High'] = sp500_filtered['High'] * usdjpy_filtered['High']
    sp500_jpy['Low'] = sp500_filtered['Low'] * usdjpy_filtered['Low']
    sp500_jpy['Close'] = sp500_filtered['Close'] * usdjpy_filtered['Close']

    # 最新価格を取得（変化率計算用）
    latest_gold_jpy = gold_jpy['Close'].iloc[-1] if not gold_jpy.empty else 0
    latest_btc_jpy = btc_jpy['Close'].iloc[-1] if not btc_jpy.empty else 0
    latest_copper_jpy = copper_jpy['Close'].iloc[-1] if not copper_jpy.empty else 0
    latest_sp500_jpy = sp500_jpy['Close'].iloc[-1] if not sp500_jpy.empty else 0
    
    # 変化率の計算（最新価格を基準にした％表示）
    usdjpy_pct = ((usdjpy_filtered['Close'] / latest_usdjpy) - 1) * 100
    nikkei_pct = ((nikkei_filtered['Close'] / latest_nikkei) - 1) * 100
    gold_jpy_pct = ((gold_jpy['Close'] / latest_gold_jpy) - 1) * 100
    btc_jpy_pct = ((btc_jpy['Close'] / latest_btc_jpy) - 1) * 100
    copper_jpy_pct = ((copper_jpy['Close'] / latest_copper_jpy) - 1) * 100
    sp500_jpy_pct = ((sp500_jpy['Close'] / latest_sp500_jpy) - 1) * 100

except Exception as e:
    st.error(f"データ処理中にエラーが発生しました：{str(e)}")
    usdjpy = pd.DataFrame()
    gold = pd.DataFrame()
    btc = pd.DataFrame()
    copper = pd.DataFrame()
    nikkei = pd.DataFrame()
    sp500 = pd.DataFrame()
    gold_jpy = pd.DataFrame()
    btc_jpy = pd.DataFrame()
    copper_jpy = pd.DataFrame()
    sp500_jpy = pd.DataFrame()

# 表示する相場の数を計算
active_charts = sum([show_usdjpy, show_gold, show_btc, show_copper, show_nikkei, show_sp500])
if active_charts == 0:
    st.warning("少なくとも1つの相場を選択してください")
    active_charts = 1  # エラー防止

# タブを作成
tab1, tab2 = st.tabs(["ローソク足", "折れ線グラフ"])

# ローソク足チャート
with tab1:
    if not usdjpy.empty:
        # サブプロットを作成（選択された相場の数だけ行を作成）
        fig_candle = make_subplots(
            rows=active_charts, 
            cols=1, 
            shared_xaxes=True,
            vertical_spacing=0.05
        )
        
        row_idx = 1  # 行インデックス
        
        # ドル円 (1)
        if show_usdjpy:
            # 通常のローソク足チャート
            fig_candle.add_trace(
                go.Candlestick(
                    x=usdjpy.index,
                    open=usdjpy['Open'],
                    high=usdjpy['High'],
                    low=usdjpy['Low'],
                    close=usdjpy['Close'],
                    name="USD/JPY"
                ),
                row=row_idx, col=1
            )
            
            # 価格と変化率を両方表示するためのy軸設定
            y_min = usdjpy['Low'].min()
            y_max = usdjpy['High'].max()
            
            # 軸設定とグリッドラインのティックを追加（%表示）
            pct_ticks = []
            pct_labels = []
            for pct in range(-20, 21, 5):  # -20%から+20%まで5%刻み
                tick_value = latest_usdjpy * (1 + pct/100)
                if y_min <= tick_value <= y_max:  # グラフの範囲内のみ表示
                    pct_ticks.append(tick_value)
                    pct_labels.append(f"{pct}%")
            
            fig_candle.update_yaxes(
                title_text="USD/JPY",
                tickvals=pct_ticks,  # カスタムティックの位置
                ticktext=pct_labels,  # カスタムティックのラベル
                showgrid=True,  # グリッドラインを表示
                gridcolor='rgba(128, 128, 128, 0.3)'  # グリッドラインの色
            )
            
            row_idx += 1
        
        # 日経平均 (2)
        if show_nikkei:
            fig_candle.add_trace(
                go.Candlestick(
                    x=nikkei.index,
                    open=nikkei['Open'],
                    high=nikkei['High'],
                    low=nikkei['Low'],
                    close=nikkei['Close'],
                    name="日経平均"
                ),
                row=row_idx, col=1
            )
            
            # 価格と変化率を両方表示するためのy軸設定
            y_min = nikkei['Low'].min()
            y_max = nikkei['High'].max()
            
            # 軸設定とグリッドラインのティックを追加（%表示）
            pct_ticks = []
            pct_labels = []
            for pct in range(-20, 21, 5):
                tick_value = latest_nikkei * (1 + pct/100)
                if y_min <= tick_value <= y_max:
                    pct_ticks.append(tick_value)
                    pct_labels.append(f"{pct}%")
            
            fig_candle.update_yaxes(
                title_text="日経平均",
                tickvals=pct_ticks,
                ticktext=pct_labels,
                row=row_idx, col=1,
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.3)'
            )
            
            row_idx += 1
        
        # S&P500（円建て） (3)
        if show_sp500:
            fig_candle.add_trace(
                go.Candlestick(
                    x=sp500_jpy.index,
                    open=sp500_jpy['Open'],
                    high=sp500_jpy['High'],
                    low=sp500_jpy['Low'],
                    close=sp500_jpy['Close'],
                    name="S&P500（円）"
                ),
                row=row_idx, col=1
            )
            
            # 価格と変化率を両方表示するためのy軸設定
            y_min = sp500_jpy['Low'].min()
            y_max = sp500_jpy['High'].max()
            
            # 軸設定とグリッドラインのティックを追加（%表示）
            pct_ticks = []
            pct_labels = []
            for pct in range(-20, 21, 5):
                tick_value = latest_sp500_jpy * (1 + pct/100)
                if y_min <= tick_value <= y_max:
                    pct_ticks.append(tick_value)
                    pct_labels.append(f"{pct}%")
            
            fig_candle.update_yaxes(
                title_text="S&P500（円）",
                tickvals=pct_ticks,
                ticktext=pct_labels,
                row=row_idx, col=1,
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.3)'
            )
            
            row_idx += 1
        
        # 金相場（円建て） (4)
        if show_gold:
            fig_candle.add_trace(
                go.Candlestick(
                    x=gold_jpy.index,
                    open=gold_jpy['Open'],
                    high=gold_jpy['High'],
                    low=gold_jpy['Low'],
                    close=gold_jpy['Close'],
                    name="金価格（円）"
                ),
                row=row_idx, col=1
            )
            
            # 価格と変化率を両方表示するためのy軸設定
            y_min = gold_jpy['Low'].min()
            y_max = gold_jpy['High'].max()
            
            # 軸設定とグリッドラインのティックを追加（%表示）
            pct_ticks = []
            pct_labels = []
            for pct in range(-20, 21, 5):
                tick_value = latest_gold_jpy * (1 + pct/100)
                if y_min <= tick_value <= y_max:
                    pct_ticks.append(tick_value)
                    pct_labels.append(f"{pct}%")
            
            fig_candle.update_yaxes(
                title_text="金価格（円）",
                tickvals=pct_ticks,
                ticktext=pct_labels,
                row=row_idx, col=1,
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.3)'
            )
            
            row_idx += 1
        
        # 銅相場（円建て） (5)
        if show_copper:
            fig_candle.add_trace(
                go.Candlestick(
                    x=copper_jpy.index,
                    open=copper_jpy['Open'],
                    high=copper_jpy['High'],
                    low=copper_jpy['Low'],
                    close=copper_jpy['Close'],
                    name="銅価格（円）"
                ),
                row=row_idx, col=1
            )
            
            # 価格と変化率を両方表示するためのy軸設定
            y_min = copper_jpy['Low'].min()
            y_max = copper_jpy['High'].max()
            
            # 軸設定とグリッドラインのティックを追加（%表示）
            pct_ticks = []
            pct_labels = []
            for pct in range(-20, 21, 5):
                tick_value = latest_copper_jpy * (1 + pct/100)
                if y_min <= tick_value <= y_max:
                    pct_ticks.append(tick_value)
                    pct_labels.append(f"{pct}%")
            
            fig_candle.update_yaxes(
                title_text="銅価格（円）",
                tickvals=pct_ticks,
                ticktext=pct_labels,
                row=row_idx, col=1,
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.3)'
            )
            
            row_idx += 1
        
        # ビットコイン（円建て） (6)
        if show_btc:
            fig_candle.add_trace(
                go.Candlestick(
                    x=btc_jpy.index,
                    open=btc_jpy['Open'],
                    high=btc_jpy['High'],
                    low=btc_jpy['Low'],
                    close=btc_jpy['Close'],
                    name="ビットコイン（円）"
                ),
                row=row_idx, col=1
            )
            
            # 価格と変化率を両方表示するためのy軸設定
            y_min = btc_jpy['Low'].min()
            y_max = btc_jpy['High'].max()
            
            # 軸設定とグリッドラインのティックを追加（%表示）
            pct_ticks = []
            pct_labels = []
            for pct in range(-20, 21, 5):
                tick_value = latest_btc_jpy * (1 + pct/100)
                if y_min <= tick_value <= y_max:
                    pct_ticks.append(tick_value)
                    pct_labels.append(f"{pct}%")
            
            fig_candle.update_yaxes(
                title_text="BTC/JPY",
                tickvals=pct_ticks,
                ticktext=pct_labels,
                row=row_idx, col=1,
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.3)'
            )
        
        # ローソク足のレンジスライダーを非表示
        fig_candle.update_xaxes(rangeslider_visible=False)
        
        # レイアウト設定
        height_per_chart = 250  # 1つのチャートあたりの高さ
        fig_candle.update_layout(
            height=height_per_chart * active_charts,  # チャート数に応じて高さを設定
            template="plotly_dark",
            showlegend=True,
            legend=dict(orientation="h", y=1.02),
            margin=dict(l=10, r=10, t=30, b=10)
        )
        
        # X軸は最後の行だけラベルを表示
        fig_candle.update_xaxes(title_text="日付", row=active_charts, col=1)
        
        # グラフ表示
        st.plotly_chart(fig_candle, use_container_width=True)
    else:
        st.error("データが取得できなかったためローソク足チャートを表示できません")

# 折れ線グラフ
with tab2:
    if not usdjpy.empty:
        # サブプロットを作成（選択された相場の数だけ行を作成）
        fig = make_subplots(
            rows=active_charts, 
            cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.05
        )
        
        row_idx = 1  # 行インデックス
        
        # ドル円 (1)
        if show_usdjpy:
            fig.add_trace(
                go.Scatter(
                    x=usdjpy.index,
                    y=usdjpy['Close'],
                    mode='lines',
                    name='USD/JPY'
                ),
                row=row_idx, col=1
            )
            
            # 価格と変化率を両方表示するためのy軸設定
            y_min = usdjpy['Close'].min()
            y_max = usdjpy['Close'].max()
            
            # 軸設定とグリッドラインのティックを追加（%表示）
            pct_ticks = []
            pct_labels = []
            for pct in range(-20, 21, 5):
                tick_value = latest_usdjpy * (1 + pct/100)
                if y_min <= tick_value <= y_max:
                    pct_ticks.append(tick_value)
                    pct_labels.append(f"{pct}%")
            
            fig.update_yaxes(
                title_text="USD/JPY",
                tickvals=pct_ticks,
                ticktext=pct_labels,
                row=row_idx, col=1,
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.3)'
            )
            
            row_idx += 1
        
        # 日経平均 (2)
        if show_nikkei:
            fig.add_trace(
                go.Scatter(
                    x=nikkei.index,
                    y=nikkei['Close'],
                    mode='lines',
                    name='日経平均'
                ),
                row=row_idx, col=1
            )
            
            # 価格と変化率を両方表示するためのy軸設定
            y_min = nikkei['Close'].min()
            y_max = nikkei['Close'].max()
            
            # 軸設定とグリッドラインのティックを追加（%表示）
            pct_ticks = []
            pct_labels = []
            for pct in range(-20, 21, 5):
                tick_value = latest_nikkei * (1 + pct/100)
                if y_min <= tick_value <= y_max:
                    pct_ticks.append(tick_value)
                    pct_labels.append(f"{pct}%")
            
            fig.update_yaxes(
                title_text="日経平均",
                tickvals=pct_ticks,
                ticktext=pct_labels,
                row=row_idx, col=1,
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.3)'
            )
            
            row_idx += 1
        
        # S&P500（円建て） (3)
        if show_sp500:
            fig.add_trace(
                go.Scatter(
                    x=sp500_jpy.index,
                    y=sp500_jpy['Close'],
                    mode='lines',
                    name='S&P500（円）'
                ),
                row=row_idx, col=1
            )
            
            # 価格と変化率を両方表示するためのy軸設定
            y_min = sp500_jpy['Close'].min()
            y_max = sp500_jpy['Close'].max()
            
            # 軸設定とグリッドラインのティックを追加（%表示）
            pct_ticks = []
            pct_labels = []
            for pct in range(-20, 21, 5):
                tick_value = latest_sp500_jpy * (1 + pct/100)
                if y_min <= tick_value <= y_max:
                    pct_ticks.append(tick_value)
                    pct_labels.append(f"{pct}%")
            
            fig.update_yaxes(
                title_text="S&P500（円）",
                tickvals=pct_ticks,
                ticktext=pct_labels,
                row=row_idx, col=1,
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.3)'
            )
            
            row_idx += 1
        
        # 金相場（円建て） (4)
        if show_gold:
            fig.add_trace(
                go.Scatter(
                    x=gold_jpy.index,
                    y=gold_jpy['Close'],
                    mode='lines',
                    name='金価格（円）'
                ),
                row=row_idx, col=1
            )
            
            # 価格と変化率を両方表示するためのy軸設定
            y_min = gold_jpy['Close'].min()
            y_max = gold_jpy['Close'].max()
            
            # 軸設定とグリッドラインのティックを追加（%表示）
            pct_ticks = []
            pct_labels = []
            for pct in range(-20, 21, 5):
                tick_value = latest_gold_jpy * (1 + pct/100)
                if y_min <= tick_value <= y_max:
                    pct_ticks.append(tick_value)
                    pct_labels.append(f"{pct}%")
            
            fig.update_yaxes(
                title_text="金価格（円）",
                tickvals=pct_ticks,
                ticktext=pct_labels,
                row=row_idx, col=1,
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.3)'
            )
            
            row_idx += 1
        
        # 銅相場（円建て） (5)
        if show_copper:
            fig.add_trace(
                go.Scatter(
                    x=copper_jpy.index,
                    y=copper_jpy['Close'],
                    mode='lines',
                    name='銅価格（円）'
                ),
                row=row_idx, col=1
            )
            
            # 価格と変化率を両方表示するためのy軸設定
            y_min = copper_jpy['Close'].min()
            y_max = copper_jpy['Close'].max()
            
            # 軸設定とグリッドラインのティックを追加（%表示）
            pct_ticks = []
            pct_labels = []
            for pct in range(-20, 21, 5):
                tick_value = latest_copper_jpy * (1 + pct/100)
                if y_min <= tick_value <= y_max:
                    pct_ticks.append(tick_value)
                    pct_labels.append(f"{pct}%")
            
            fig.update_yaxes(
                title_text="銅価格（円）",
                tickvals=pct_ticks,
                ticktext=pct_labels,
                row=row_idx, col=1,
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.3)'
            )
            
            row_idx += 1
        
        # ビットコイン（円建て） (6)
        if show_btc:
            fig.add_trace(
                go.Scatter(
                    x=btc_jpy.index,
                    y=btc_jpy['Close'],
                    mode='lines',
                    name='BTC/JPY'
                ),
                row=row_idx, col=1
            )
            
            # 価格と変化率を両方表示するためのy軸設定
            y_min = btc_jpy['Close'].min()
            y_max = btc_jpy['Close'].max()
            
            # 軸設定とグリッドラインのティックを追加（%表示）
            pct_ticks = []
            pct_labels = []
            for pct in range(-20, 21, 5):
                tick_value = latest_btc_jpy * (1 + pct/100)
                if y_min <= tick_value <= y_max:
                    pct_ticks.append(tick_value)
                    pct_labels.append(f"{pct}%")
            
            fig.update_yaxes(
                title_text="BTC/JPY",
                tickvals=pct_ticks,
                ticktext=pct_labels,
                row=row_idx, col=1,
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.3)'
            )
        
        # レイアウト設定
        height_per_chart = 250  # 1つのチャートあたりの高さ
        fig.update_layout(
            height=height_per_chart * active_charts,  # チャート数に応じて高さを設定
            template="plotly_dark",
            showlegend=True,
            legend=dict(orientation="h", y=1.02),
            margin=dict(l=10, r=10, t=30, b=10)
        )
        
        # X軸は最後の行だけラベルを表示
        fig.update_xaxes(title_text="日付", row=active_charts, col=1)
        
        # グラフ表示
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("データが取得できなかったためグラフを表示できません")

