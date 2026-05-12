import streamlit as st
import pandas as pd
import akshare as ak
import plotly.express as px
import time
from datetime import datetime, timedelta
import numpy as np

# 1. 基础配置
def get_beijing_time():
    return datetime.utcnow() + timedelta(hours=8)

st.set_page_config(page_title="2026 相对强度雷达", layout="wide")

# 初始化：如果不存在则创建
if 'history_data' not in st.session_state:
    st.session_state.history_data = pd.DataFrame(columns=['时间', '板块', '资金流(亿)'])
if 'delta_history' not in st.session_state:
    st.session_state.delta_history = {}

# 2. 侧边栏
with st.sidebar:
    st.header("⚙️ 监控设置")
    n_inflow = st.slider("流入榜单数量", 1, 30, 10)
    n_outflow = st.slider("流出榜单数量", 1, 20, 5)
    st.write("---")
    st.header("🚨 异动阈值")
    intensity_threshold = st.slider("异动倍数", 2.0, 10.0, 4.0, 0.5)
    st.write("---")
    demo_mode = st.toggle("开启演示模式 (强制出图测试)")
    if st.button("清空历史数据"):
        st.session_state.history_data = pd.DataFrame(columns=['时间', '板块', '资金流(亿)'])
        st.session_state.delta_history = {}
        st.rerun()

# 3. 核心算法 (增加安全检查)
def get_data_robust(in_count, out_count):
    try:
        df = ak.stock_sector_fund_flow_rank(indicator="今日")
        if df is None or df.empty:
            return None, "接口暂无数据 (可能非交易时间)"
            
        now_time = get_beijing_time().strftime('%H:%M:%S')
        subset = pd.concat([df.head(in_count), df.tail(out_count)])
        
        new_rows = []
        alerts = []
        
        for _, row in subset.iterrows():
            name = row['名称']
            val = row['今日主力净流入-净额'] / 10000 
            
            # 安全检查：历史记录中是否有该板块
            if not st.session_state.history_data.empty:
                prev_points = st.session_state.history_data[st.session_state.history_data['板块'] == name]
                if not prev_points.empty:
                    last_val = prev_points['资金流(亿)'].iloc[-1]
                    delta = abs(val - last_val)
                    
                    if name not in st.session_state.delta_history:
                        st.session_state.delta_history[name] = []
                    
                    hist = st.session_state.delta_history[name]
                    if len(hist) > 2:
                        avg = np.mean(hist)
                        intensity = delta / avg if avg > 0.01 else 0
                        if intensity >= intensity_threshold:
                            alerts.append({'板块': name, '强度': intensity, '变动': val - last_val})
                    
                    hist.append(delta)
                    if len(hist) > 10: hist.pop(0)
            
            new_rows.append({'时间': now_time, '板块': name, '资金流(亿)': val})
            
        return pd.DataFrame(new_rows), alerts
    except Exception as e:
        return None, f"数据引擎故障: {str(e)}"

# 4. 页面渲染
st.title("🏹 A股相对强度资金监控台")
st.info(f"⏰ 北京时间：{get_beijing_time().strftime('%H:%M:%S')}")

if demo_mode:
    # 演示模式：无论如何都要出图
    now = get_beijing_time().strftime('%H:%M:%S')
    demo_df = pd.DataFrame({
        '时间': [now]*3, 
        '板块': ['演示板块A', '演示板块B', '演示板块C'], 
        '资金流(亿)': [10.5, -5.2, 2.1]
    })
    st.session_state.history_data = pd.concat([st.session_state.history_data, demo_df], ignore_index=True)
    st.success("🚨 演示预警：演示板块A 异动强度 5.0 倍！")
    fig = px.line(st.session_state.history_data.tail(100), x="时间", y="资金流(亿)", color="板块", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
else:
    res, alerts = get_data_robust(n_inflow, n_outflow)
    
    if res is not None:
        # 处理预警
        if alerts:
            for a in alerts:
                if a['变动'] > 0:
                    st.success(f"🚨 **猛烈吸筹**：【{a['板块']}】强度 {a['强度']:.1f} 倍 (变动:{a['变动']:.2f}亿)")
                else:
                    st.error(f"🚨 **主力砸盘**：【{a['板块']}】强度 {a['强度']:.1f} 倍 (变动:{a['变动']:.2f}亿)")
        
        # 更新数据
        st.session_state.history_data = pd.concat([st.session_state.history_data, res], ignore_index=True)
        if len(st.session_state.history_data) > 1500:
            st.session_state.history_data = st.session_state.history_data.tail(1500)
            
        # 绘图
        fig = px.line(st.session_state.history_data, x="时间", y="资金流(亿)", color="板块", template="plotly_dark")
        fig.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"📡 状态：{res if res else '正在等待开盘数据流...'}")
        st.caption(f"错误排查日志：{alerts if isinstance(alerts, str) else '无'}")

time.sleep(30)
st.rerun()