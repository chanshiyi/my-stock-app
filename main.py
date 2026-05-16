import streamlit as st
import akshare as ak
import pandas as pd
import time
import socket

# 设置网页标题和布局
st.set_page_config(page_title="A股资金流向实时监控面板", layout="wide")

st.title("🔍 A股资金流向实时监控面板 (云端防卡死版)")
st.caption("数据来源：东方财富网 | 具备海外节点网络容错机制")

# 设置全局网络超时时间（防止 akshare 无限制死等）
socket.setdefaulttimeout(10)

# --- 侧边栏控制区域 ---
st.sidebar.header("⚙️ 控制面板")
refresh_rate = st.sidebar.slider("数据自动刷新频率 (秒)", min_value=10, max_value=120, value=30)
auto_refresh = st.sidebar.checkbox("开启自动刷新", value=False)

# 使用带状态提示的函数
def get_market_flow_safe():
    # 在界面上显示一个正在加载的菊花转圈提示
    with st.spinner("🔄 正在尝试连接国内财经服务器拉取历史资金数据..."):
        try:
            # 引入时间戳，强制刷新，绕过可能的本地坏缓存
            df = ak.stock_concept_fund_flow_rank_em()
            
            if df is None or df.empty:
                st.error("❌ 服务器返回了空数据。可能是非交易时间接口短暂维护，请稍后刷新重试。")
                return pd.DataFrame()
                
            # 数据清洗与转换
            df = df.rename(columns={
                "序号": "排名", "概念板块名称": "板块名称",
                "今日今日主力净流入-净额": "主力净流入(元)", "今日今日主力净流入-净率": "主力净流入率(%)",
                "今日超大单净流入-净额": "超大单净流入(元)", "今日大单净流入-净额": "大单净流入(元)",
                "主力净流入最大股": "领涨个股"
            })
            money_cols = ["主力净流入(元)", "超大单净流入(元)", "大单净流入(元)"]
            for col in money_cols:
                df[col] = (df[col] / 100000000).round(2)
                df = df.rename(columns={col: col.replace("(元)", "(亿元)")})
            return df[["排名", "板块名称", "主力净流入(亿元)", "主力净流入率(%)", "超大单净流入(亿元)", "大单净流入(亿元)", "领涨个股"]]
            
        except socket.timeout:
            st.error("📡 网络连接超时！云端服务器连接东方财富网失败，请点击右上角【Rerun】重试。")
            return pd.DataFrame()
        except Exception as e:
            st.error(f"⚠️ 发生未知错误：{str(e)}")
            return pd.DataFrame()

# --- 主面板数据渲染 ---
data_df = get_market_flow_safe()

if not data_df.empty:
    total_inflow = data_df["主力净流入(亿元)"].sum().round(2)
    
    # 顶部指标看板
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="今日监控概念板块总净流入", value=f"{total_inflow} 亿元")
    with col2:
        top_1 = data_df.iloc[0]
        st.metric(label="🥇 资金最青睐板块", value=top_1["板块名称"], delta=f"+{top_1['主力净流入(亿元)']} 亿")
    with col3:
        last_1 = data_df.iloc[-1]
        st.metric(label="💔 资金砸盘最狠板块", value=last_1["板块名称"], delta=f"{last_1['主力净流入(亿元)']} 亿")
    
    st.markdown("---")
    
    # 数据表格展示
    left_col, right_col = st.columns(2)
    with left_col:
        st.subheader("🔥 今日主力资金【流入】前 15 名")
        st.dataframe(data_df.sort_values(by="主力净流入(亿元)", ascending=False).head(15), use_container_width=True, hide_index=True)
    with right_col:
        st.subheader("❄️ 今日主力资金【流出】前 15 名")
        st.dataframe(data_df.sort_values(by="主力净流入(亿元)", ascending=True).head(15), use_container_width=True, hide_index=True)
        
    st.caption(f"⏱️ 界面最后刷新时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
else:
    # 如果数据为空，提供一个手动刷新的大按钮
    if st.button("🔄 重新尝试获取数据"):
        st.rerun()

# 云端自动刷新逻辑
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()