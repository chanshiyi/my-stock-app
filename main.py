import streamlit as st
import pandas as pd
import requests
import time
import json

# 设置网页标题和布局
st.set_page_config(page_title="A股资金流向实时监控面板", layout="wide")

st.title("🔍 A股资金流向实时监控面板 (直连官方天花板版)")
st.caption("数据来源：东方财富网网关直连 | 丢弃第三方库依赖，再无报错隐患")

# --- 侧边栏控制区域 ---
st.sidebar.header("⚙️ 控制面板")
monitor_type = st.sidebar.selectbox("选择监控维度", ["行业板块资金流", "个股资金流"])
refresh_rate = st.sidebar.slider("数据自动刷新频率 (秒)", min_value=10, max_value=120, value=30)
auto_refresh = st.sidebar.checkbox("开启自动刷新", value=False)

def get_eastmoney_data(data_type):
    """通过直连东方财富公开网关获取最真实的数据流"""
    with st.spinner("📡 正在跨越网关，直连东方财富实时行情流..."):
        try:
            # 伪造标准的浏览器请求头，防止被拦截
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://data.eastmoney.com/"
            }
            
            if data_type == "行业板块资金流":
                # 东方财富官方行业板块资金流核心核心 API
                url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=100&po=1&np=1&fields=f12,f14,f62,f184,f66,f69,f72,f75,f136&fs=m:90+t:2"
                response = requests.get(url, headers=headers, timeout=10)
                json_data = response.json()
                
                # 提取核心列表
                data_list = json_data.get("data", {}).get("diff", [])
                if not data_list:
                    return pd.DataFrame()
                
                # 映射原始字段到中文
                df = pd.DataFrame(data_list)
                df = df.rename(columns={
                    "f14": "板块名称",
                    "f62": "主力净流入(元)",
                    "f184": "主力净流入率(%)",
                    "f66": "超大单净流入(元)",
                    "f69": "大单净流入(元)",
                    "f136": "领涨个股"
                })
                
            else:
                # 东方财富官方个股资金流核心核心 API (前100名)
                url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=100&po=1&np=1&fields=f12,f14,f2,f3,f62,f184,f66,f69,f72,f75&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:1+t:31,m:1+t:81+s:2048"
                response = requests.get(url, headers=headers, timeout=10)
                json_data = response.json()
                
                data_list = json_data.get("data", {}).get("diff", [])
                if not data_list:
                    return pd.DataFrame()
                
                df = pd.DataFrame(data_list)
                df = df.rename(columns={
                    "f12": "代码",
                    "f14": "简称",
                    "f62": "主力净流入(元)",
                    "f184": "主力净流入率(%)",
                    "f66": "超大单净流入(元)",
                    "f69": "大单净流入(元)"
                })
            
            # 统一的数据清洗：转换“元”到“亿元”
            if "主力净流入(元)" in df.columns:
                df["主力净流入(元)"] = pd.to_numeric(df["主力净流入(元)"], errors='coerce')
                df["主力净流入(亿元)"] = (df["主力净流入(元)"] / 100000000).round(2)
                df["主力净流入率(%)"] = pd.to_numeric(df["主力净流入率(%)"], errors='coerce').round(2)
                df["超大单净流入(亿元)"] = (pd.to_numeric(df["f66"], errors='coerce') / 100000000).round(2)
                df["大单净流入(亿元)"] = (pd.to_numeric(df["f69"], errors='coerce') / 100000000).round(2)
                
                # 生成动态排名
                df = df.sort_values(by="主力净流入(亿元)", ascending=False)
                df.insert(0, '排名', range(1, len(df) + 1))
                
                if data_type == "行业板块资金流":
                    return df[["排名", "板块名称", "主力净流入(亿元)", "主力净流入率(%)", "超大单净流入(亿元)", "大单净流入(亿元)", "领涨个股"]]
                else:
                    return df[["排名", "代码", "简称", "主力净流入(亿元)", "主力净流入率(%)", "超大单净流入(亿元)", "大单净流入(亿元)"]]
            return pd.DataFrame()
            
        except Exception as e:
            st.error(f"📡 核心数据通信失败：{str(e)}")
            return pd.DataFrame()

# --- 主面板数据渲染 ---
data_df = get_eastmoney_data(monitor_type)

if not data_df.empty:
    total_inflow = data_df["主力净流入(亿元)"].sum().round(2)
    name_col = "板块名称" if monitor_type == "行业板块资金流" else "简称"
    
    # 顶部指标看板
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label=f"今日整个市场监控总净流入", value=f"{total_inflow} 亿元")
    with col2:
        top_1 = data_df.iloc[0]
        st.metric(label="🥇 资金超级主力最青睐", value=top_1[name_col], delta=f"+{top_1['主力净流入(亿元)']} 亿")
    with col3:
        last_1 = data_df.iloc[-1]
        st.metric(label="💔 主力疯狂砸盘逃跑", value=last_1[name_col], delta=f"{last_1['主力净流入(亿元)']} 亿")
    
    st.markdown("---")
    
    # 数据表格展示
    left_col, right_col = st.columns(2)
    with left_col:
        st.subheader("🔥 主力资金【流入】前 15 名")
        st.dataframe(data_df.head(15), use_container_width=True, hide_index=True)
    with right_col:
        st.subheader("❄️ 主力资金【流出】前 15 名")
        st.dataframe(data_df.tail(15).iloc[::-1], use_container_width=True, hide_index=True)
        
    st.caption(f"⏱️ 接口最后通信时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
else:
    st.warning("⚠️ 未能成功建立数据握手，请尝试重新获取。")
    if st.button("🔄 强行突破获取数据"):
        st.rerun()

# 云端自动刷新逻辑
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()