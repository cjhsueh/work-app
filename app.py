import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
import calendar

# --- 設定頁面寬度與標題 ---
st.set_page_config(page_title="每日施工人數統計系統", layout="wide")

# --- 初始化 Session State (用於暫存資料) ---
# 在實際應用中，這裡通常會連接 Excel 或 Database
if 'projects' not in st.session_state:
    st.session_state.projects = {
        "專案 A": {"host": "台北市政府捷運局", "data": pd.DataFrame(columns=["日期", "廠商名稱", "施工工種", "班別", "施工人數", "備註"])},
        "專案 B": {"host": "新北市工務局", "data": pd.DataFrame(columns=["日期", "廠商名稱", "施工工種", "班別", "施工人數", "備註"])}
    }

# --- 輔助函式：判斷是否為假日 ---
def get_holiday_ranges(start_date, end_date):
    """
    回傳一段時間內的假日清單 (包含週末與自定義國定假日)。
    為了示範，這裡手動定義了一些2024-2025常見國定假日，
    實際應用可串接 API。
    """
    # 範例國定假日 (格式: YYYY-MM-DD)
    public_holidays = [
        "2024-01-01", "2024-02-08", "2024-02-09", "2024-02-12", "2024-02-13", "2024-02-14", 
        "2024-02-28", "2024-04-04", "2024-04-05", "2024-05-01", "2024-06-10", "2024-09-17", "2024-10-10",
        "2025-01-01", "2025-01-25", "2025-01-26", "2025-01-27", "2025-01-28", "2025-01-29", # 2025春節示意
    ]
    
    holidays = []
    current = start_date
    while current <= end_date:
        # 判斷週末 (5=週六, 6=週日) 或 國定假日
        if current.weekday() >= 5 or current.strftime("%Y-%m-%d") in public_holidays:
            holidays.append(current)
        current += timedelta(days=1)
    return holidays

# --- 主程式 ---
st.title("🏗️ 每日施工人數紀錄與統計 APP")

# 建立分頁
project_names = list(st.session_state.projects.keys())
tabs = st.tabs(project_names)

for i, project_name in enumerate(project_names):
    with tabs[i]:
        project_info = st.session_state.projects[project_name]
        
        # 1. 顯示標題與主辦單位
        col_header1, col_header2 = st.columns([3, 1])
        with col_header1:
            st.markdown(f"### 🚩 工程名稱：{project_name}")
        with col_header2:
            st.info(f"**主辦單位：** {project_info['host']}")
        
        st.markdown("---")

        # 2. 資料輸入區 (側邊欄或上方展開)
        with st.expander("➕ 新增施工紀錄", expanded=True):
            c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.5, 1.5, 1, 1, 1])
            with c1:
                input_date = st.date_input("施工日期", key=f"date_{i}", value=date.today())
            with c2:
                input_vendor = st.text_input("廠商名稱", key=f"vendor_{i}", placeholder="例如：甲級營造")
            with c3:
                input_type = st.selectbox("施工工種", ["鋼筋", "模板", "混凝土", "水電", "泥作", "其他"], key=f"type_{i}")
            with c4:
                input_shift = st.selectbox("班別", ["早班", "中班", "晚班"], key=f"shift_{i}")
            with c5:
                input_count = st.number_input("施工人數", min_value=1, value=5, step=1, key=f"count_{i}")
            with c6:
                input_remark = st.text_input("備註", key=f"remark_{i}")
            
            if st.button("寫入紀錄", key=f"btn_{i}"):
                new_data = pd.DataFrame({
                    "日期": [pd.to_datetime(input_date)],
                    "廠商名稱": [input_vendor],
                    "施工工種": [input_type],
                    "班別": [input_shift],
                    "施工人數": [input_count],
                    "備註": [input_remark]
                })
                # 更新 Session State
                st.session_state.projects[project_name]['data'] = pd.concat(
                    [st.session_state.projects[project_name]['data'], new_data], ignore_index=True
                )
                st.rerun()

        # 3. 資料展示 (樞紐分析/矩陣) 與 原始資料
        df = st.session_state.projects[project_name]['data']
        
        if not df.empty:
            # 整理資料以便顯示
            df = df.sort_values(by="日期")
            df['日期顯示'] = df['日期'].dt.strftime('%Y-%m-%d')
            
            st.subheader("📋 施工紀錄明細")
            # 這裡顯示您要求的橫列標題格式
            st.dataframe(
                df[["日期顯示", "廠商名稱", "施工工種", "班別", "施工人數", "備註"]],
                use_container_width=True,
                hide_index=True
            )

            # 4. 統計與折線圖
            st.markdown("---")
            st.subheader("📈 施工人數統計折線圖")

            # 依日期加總人數
            daily_stats = df.groupby("日期")["施工人數"].sum().reset_index()
            
            if not daily_stats.empty:
                # 準備圖表資料
                min_date = daily_stats['日期'].min()
                max_date = daily_stats['日期'].max()
                
                # 產生圖表
                fig = go.Figure()

                # 加入折線
                fig.add_trace(go.Scatter(
                    x=daily_stats['日期'], 
                    y=daily_stats['施工人數'],
                    mode='lines+markers',
                    name='施工人數',
                    line=dict(color='#1f77b4', width=3),
                    marker=dict(size=8)
                ))

                # 計算假日區間並加上背景色
                holidays_list = get_holiday_ranges(min_date, max_date)
                for h_date in holidays_list:
                    # 在圖表上畫出垂直矩形 (vrect)
                    # 設定為前後半天，蓋住整格
                    x0 = h_date - timedelta(hours=12)
                    x1 = h_date + timedelta(hours=12)
                    
                    fig.add_vrect(
                        x0=x0, x1=x1,
                        fillcolor="LightSkyBlue", 
                        opacity=0.5, # 透明度 50%
                        layer="below", 
                        line_width=0,
                    )

                # 設定圖表樣式 (白底)
                fig.update_layout(
                    title=f"{project_name} - 每日人力統計趨勢",
                    xaxis_title="日期",
                    yaxis_title="總人數",
                    plot_bgcolor='white', # 白底色
                    xaxis=dict(
                        showgrid=True, 
                        gridcolor='#eee',
                        tickformat='%Y-%m-%d'
                    ),
                    yaxis=dict(
                        showgrid=True, 
                        gridcolor='#eee'
                    ),
                    hovermode="x unified"
                )

                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("尚無資料，請由上方新增施工紀錄。")