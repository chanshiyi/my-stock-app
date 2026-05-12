import streamlit as st
import pandas as pd
import akshare as ak
import plotly.express as px
import time
from datetime import datetime

# 基础页面配置
st.set_page_config(page_title="2026 实时资金监控云端版", layout="wide")

# 初始化云端记忆库
if 'history_data' not in st.session_state:
    st.session_state.history_data = pd.DataFrame(columns=['时间', '板块', '资金流(亿)'])

def get_data():
    try:
        # 云端抓取，不受本地网络限制
        df = ak.stock_sector_fund_flow_rank(indicator="今日")
        if df is not None and not df.empty:
            now_time = datetime.now().strftime('%H:%M:%S')
            # 选取前 10 名和后 5 名进行追踪
            subset = pd.concat([df.head(10), df.tail(5)])
            new_rows = []
            for _, row in subset.iterrows():
                new_rows.append({
                    '时间': now_time,
                    '板块': row['名称'],
                    '资金流(亿)': row['今日主力净流入-净额'] / 10000 
                })
            return pd.DataFrame(new_rows)
    except:
        return None
    return None

st.title("🏹 A股实时分时资金流轨迹 (云端版)")

# 侧边栏：频率建议设为 30 秒，太快容易被封 IP
refresh_rate = st.sidebar.slider("自动同步频率 (秒)", 15, 120, 30)
if st.sidebar.button("重置历史记录"):
    st.session_state.history_data = pd.DataFrame(columns=['时间', '板块', '资金流(亿)'])
    st.rerun()

# 核心更新逻辑
result = get_data()
if result is not None:
    st.session_state.history_data = pd.concat([st.session_state.history_data, result]).ignore_index=True
    # 只保留最近 2000 条数据，防止内存溢出
    if len(st.session_state.history_data) > 2000:
        st.session_state.history_data = st.session_state.history_data.tail(2000)

    # 绘制折线图 (图2效果)
    fig = px.line(
        st.session_state.history_data, 
        x="时间", y="资金流(亿)", color="板块",
        title="主力资金实时分时走势 (亿元)",
        template="plotly_dark"
    )
    fig.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(result.sort_values('资金流(亿)', ascending=False), use_container_width=True)
else:
    st.warning("📡 正在同步数据，请稍后...")

time.sleep(refresh_rate)
st.rerun()