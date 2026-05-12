import streamlit as st
import pandas as pd
import akshare as ak
import plotly.express as px
import time
from datetime import datetime

st.set_page_config(page_title="2026 实时资金监控云端版", layout="wide")

if 'history_data' not in st.session_state:
    st.session_state.history_data = pd.DataFrame(columns=['时间', '板块', '资金流(亿)'])

def get_data_debug():
    try:
        # 尝试获取数据
        df = ak.stock_sector_fund_flow_rank(indicator="今日")
        if df is not None and not df.empty:
            now_time = datetime.now().strftime('%H:%M:%S')
            subset = pd.concat([df.head(10), df.tail(5)])
            new_rows = []
            for _, row in subset.iterrows():
                new_rows.append({
                    '时间': now_time,
                    '板块': row['名称'],
                    '资金流(亿)': row['今日主力净流入-净额'] / 10000 
                })
            return pd.DataFrame(new_rows)
        else:
            return "警告：服务器返回了空数据，可能现在正处于盘后结算。"
    except Exception as e:
        # 如果报错，把具体的错误码扔出来
        return f"接口报错详情: {str(e)}"

st.title("🏹 A股实时分时资金流轨迹 (云端版)")

# 显示当前服务器时间（看看是不是时差问题）
st.caption(f"云端服务器当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

result = get_data_debug()

if isinstance(result, pd.DataFrame):
    st.session_state.history_data = pd.concat([st.session_state.history_data, result]).ignore_index=True
    if len(st.session_state.history_data) > 2000:
        st.session_state.history_data = st.session_state.history_data.tail(2000)

    fig = px.line(
        st.session_state.history_data, 
        x="时间", y="资金流(亿)", color="板块",
        title="主力资金实时分时走势 (亿元)",
        template="plotly_dark"
    )
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
else:
    # 这样你就不会“盲等”了，直接能看到是什么错误
    st.error(result)

time.sleep(30)
st.rerun()