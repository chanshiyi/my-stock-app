import streamlit as st
import pandas as pd
import akshare as ak
import plotly.express as px
import time
from datetime import datetime, timedelta
import numpy as np

# ==========================================
# 1. 基础工具
# ==========================================
def get_beijing_time():
    return datetime.utcnow() + timedelta(hours=8)

st.set_page_config(page_title="2026 资金雷达 (个股穿透版)", layout="wide")

if 'history_data' not in st.session_state:
    st.session_state.history_data = pd.DataFrame(columns=['时间', '板块', '资金流(亿)', '领涨股'])
if 'delta_history' not in st.session_state:
    st.session_state.delta_history = {}

# ==========================================
# 2. 侧边栏设置
# ==========================================
with st.sidebar:
    st.header("⚙️ 监控设置")
    n_inflow = st.slider("流入榜单数量", 1, 20, 8)
    n_outflow = st.slider("流出榜单数量", 1, 10, 4)
    st.write("---")
    st.header("🚨 异动阈值")
    intensity_threshold = st.slider("异动倍数", 2.0, 10.0, 4.0, 0.5)
    st.write("---")
    demo_mode = st.toggle("开启演示模式 (测试悬停)")
    if st.button("重置所有数据"):
        st.session_state.history_data = pd.DataFrame(columns=['时间', '板块', '资金流(亿)', '领涨股'])
        st.session_state.delta_history = {}
        st.rerun()

# ==========================================
# 3. 数据下钻算法：获取板块内的“一哥”
# ==========================================
@st.cache_data(ttl=60) # 缓存1分钟，避免频繁请求封IP
def get_top_stock(sector_name):
    try:
        # 获取该板块下的个股资金流向
        stock_df = ak.stock_sector_detail_flow_rank(symbol=sector_name)
        if stock_df is not None and not stock_df.empty:
            # 拿到第一名的 股票名称 和 净流入额
            top_name = stock_df.iloc[0]['名称']
            top_flow = stock_df.iloc[0]['今日主力净流入-净额'] / 10000 # 转为亿元
            return f"{top_name} ({top_flow:.2f}亿)"
    except:
        return "查询中..."
    return "无数据"

def get_data_with_stocks(in_count, out_count):
    try:
        df = ak.stock_sector_fund_flow_rank(indicator="今日")
        if df is None or df.empty: return None, "无数据"
        
        now_time = get_beijing_time().strftime('%H:%M:%S')
        subset = pd.concat([df.head(in_count), df.tail(out_count)])
        
        new_rows = []
        alerts = []
        
        # 遍历选中的板块，逐个下钻抓个股
        for _, row in subset.iterrows():
            name = row['名称']
            val = row['今日主力净流入-净额'] / 10000 
            
            # 获取该板块的领涨股 (这一步是新增的)
            top_stock_info = get_top_stock(name)
            
            # --- 异动算法逻辑开始 ---
            if not st.session_state.history_data.empty:
                prev_points = st.session_state.history_data[st.session_state.history_data['板块'] == name]
                if not prev_points.empty:
                    last_val = prev_points['资金流(亿)'].iloc[-1]
                    delta = abs(val - last_val)
                    if name not in st.session_state.delta_history: st.session_state.delta_history[name] = []
                    hist = st.session_state.delta_history[name]
                    if len(hist) > 2:
                        avg = np.mean(hist)
                        intensity = delta / avg if avg > 0.01 else 0
                        if intensity >= intensity_threshold:
                            alerts.append({'板块': name, '强度': intensity, '变动': val - last_val, '领涨': top_stock_info})
                    hist.append(delta)
                    if len(hist) > 10: hist.pop(0)
            # --- 异动算法逻辑结束 ---
            
            new_rows.append({
                '时间': now_time, 
                '板块': name, 
                '资金流(亿)': val, 
                '领涨股': top_stock_info # 将个股信息存入行
            })
            
        return pd.DataFrame(new_rows), alerts
    except Exception as e:
        return None, str(e)

# ==========================================
# 4. 页面渲染
# ==========================================
st.title("🏹 A股相对强度雷达 (个股穿透版)")

if demo_mode:
    st.info("💡 演示模式：请尝试将鼠标悬停在下方的折线上！")
    now = get_beijing_time().strftime('%H:%M:%S')
    demo_df = pd.DataFrame({
        '时间': [now]*3, 
        '板块': ['人工智能', '中药', '半导体'], 
        '资金流(亿)': [15.2, 8.5, -4.2],
        '领涨股': ['科大讯飞 (2.5亿)', '片仔癀 (1.1亿)', '中芯国际 (-0.8亿)']
    })
    st.session_state.history_data = pd.concat([st.session_state.history_data, demo_df], ignore_index=True)
    # 绘图逻辑同下...
else:
    res, alerts = get_data_with_stocks(n_inflow, n_outflow)
    if res is not None:
        if alerts:
            for a in alerts:
                if a['变动'] > 0:
                    st.success(f"🚨 **吸筹**：【{a['板块']}】强度 {a['强度']:.1f}倍！ 领涨：{a['领涨']}")
                else:
                    st.error(f"🚨 **砸盘**：【{a['板块']}】强度 {a['强度']:.1f}倍！ 领跌：{a['领涨']}")
        
        st.session_state.history_data = pd.concat([st.session_state.history_data, res], ignore_index=True)
        if len(st.session_state.history_data) > 1500:
            st.session_state.history_data = st.session_state.history_data.tail(1500)

if not st.session_state.history_data.empty:
    # --- 核心交互设计：Plotly 悬停配置 ---
    fig = px.line(
        st.session_state.history_data, 
        x="时间", 
        y="资金流(亿)", 
        color="板块",
        custom_data=["领涨股"], # 将领涨股列传给图表，但不直接画出来
        template="plotly_dark",
        title="主力资金实时轨迹 (鼠标悬停查看个股)"
    )

    # 自定义悬停显示内容
    fig.update_traces(
        hovertemplate="<br>".join([
            "时间: %{x}",
            "板块: %{fullData.name}",
            "累计净额: %{y} 亿",
            "<b>该板块第一名: %{customdata[0]}</b>", # 重点在这里！
            "<extra></extra>" # 隐藏侧边多余的标签
        ])
    )

    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("正在等待开盘数据...")

time.sleep(30)
st.rerun()