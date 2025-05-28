import streamlit as st
import pandas as pd
import numpy as np

# 设置页面配置
st.set_page_config(
    page_title="DMU学位计算器-UKEC Leicester",
    page_icon="🎓",
    layout="wide"
)

# 页面标题
st.title("DMU学位等级计算器·UKEC Leicester")
st.markdown("---")

# 新增：学分要求提示
st.markdown("**提示：最终学分总和需达到120，方可计算学位等级。**")
st.markdown("**如有疑问，请咨询UKEC老师微信：Ukec_kalen**")

# 初始化session state
if 'modules' not in st.session_state:
    st.session_state.modules = []

# 项目类型选择
project_type = st.radio(
    "选择项目类型",
    ["3+1", "2+2"],
    horizontal=True
)

# 年级映射
LEVEL_MAP = {"大二": 5, "大三": 6}
LEVEL_MAP_REV = {5: "大二", 6: "大三"}

# 创建模块输入表单
def create_module_form():
    with st.form(key="module_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            module_name = st.text_input("课程名称（选填）")
        with col2:
            credits = st.selectbox("学分", [15, 30, 45])
        with col3:
            score = st.number_input("分数（%）", min_value=0, max_value=100, step=1)
        
        # 年级选择
        if project_type == "2+2":
            level_str = st.selectbox("年级", ["大二", "大三"])
            level = LEVEL_MAP[level_str]
        else:
            level = 6
        
        submit_button = st.form_submit_button("添加课程")
        
        if submit_button:
            module = {
                "name": module_name,
                "credits": credits,
                "score": score,
                "level": level
            }
            st.session_state.modules.append(module)
            st.success("课程添加成功！")

# 显示已添加的模块（可编辑/删除）
def display_modules():
    if st.session_state.modules:
        st.subheader("已添加的课程")
        df = pd.DataFrame(st.session_state.modules)
        # 年级数字转中文
        df["年级"] = df["level"].map(LEVEL_MAP_REV)
        df = df.rename(columns={
            "name": "课程名称",
            "credits": "学分",
            "score": "分数",
        })
        df = df[["课程名称", "学分", "分数", "年级"]]
        # 可编辑表格
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="editable_table")
        # 同步回session_state（只同步内容，不同步顺序/删除）
        if edited_df.shape == df.shape:
            for i, row in edited_df.iterrows():
                st.session_state.modules[i]["name"] = row["课程名称"]
                st.session_state.modules[i]["credits"] = row["学分"]
                st.session_state.modules[i]["score"] = row["分数"]
                st.session_state.modules[i]["level"] = LEVEL_MAP[row["年级"]] if row["年级"] in LEVEL_MAP else 6
        # 删除某一行
        for idx in range(len(st.session_state.modules)):
            col = st.columns(len(st.session_state.modules))
            with col[idx]:
                if st.button(f"删除第{idx+1}门", key=f"del_{idx}"):
                    st.session_state.modules.pop(idx)
                    st.rerun()
        # 删除全部
        if st.button("清除所有课程"):
            st.session_state.modules = []
            st.rerun()
        # 实时显示还差多少学分
        total_credits = sum([m["credits"] for m in st.session_state.modules])
        st.info(f"当前已添加学分：{total_credits}，还差 {max(0, 120-total_credits)} 学分达到120学分。")

# 计算学位等级
def calculate_degree_classification(modules_df, project_type):
    if modules_df.empty:
        return "未添加任何课程"
    
    # 检查总学分
    total_credits = modules_df['credits'].sum()
    # 统计挂科（<30分）学分
    fail_credits = modules_df[modules_df['score'] < 30]['credits'].sum()
    
    # 先判断学分严重不足
    if total_credits < 60:
        return f"学分严重不足（{total_credits}学分），无法授予任何学位或证书。"
    
    # 计算加权均分（所有课程都计入，权重=学分/15）
    weighted_sum_all = (modules_df['score'] * modules_df['credits'] / 15).sum()
    total_weight_all = (modules_df['credits'] / 15).sum()
    avg_all = weighted_sum_all / total_weight_all if total_weight_all > 0 else 0

    # 如果有挂科（<30分）且总学分>=120，且挂科学分<=30且均分>=40，授予ordinary degree
    if total_credits >= 120 and fail_credits > 0 and fail_credits <= 30 and avg_all >= 40:
        return f"存在不超过30学分的挂科（<30分），整体加权均分为{avg_all:.2f}分，授予普通学士学位（Non-honours/Ordinary Degree）。"

    # 如果学分不足120
    if total_credits < 120:
        if total_credits >= 60:
            return f"学分不足（{total_credits}学分），无法授予学位。可授予：高等教育证书（Certificate of Higher Education）"
        else:
            return f"学分严重不足（{total_credits}学分），无法授予任何学位或证书。"
    
    # 检查是否有分数低于30的模块
    if fail_credits > 0:
        if fail_credits <= 30 and avg_all >= 40:
            return f"存在不超过30学分的挂科（<30分），整体加权均分为{avg_all:.2f}分，授予普通学士学位（Non-honours/Ordinary Degree）。"
        else:
            return f"存在分数低于30分的课程（共{fail_credits}学分），无法补偿。已修满120学分，可授予：高等教育文凭（Diploma of Higher Education）"
    
    # 补偿处理
    compensation_credits = modules_df[(modules_df['score'] >= 30) & (modules_df['score'] < 40)]['credits'].sum()
    if compensation_credits > 30:
        if total_credits >= 120:
            return f"补偿学分过多（{compensation_credits}学分），无法授予学位。已修满120学分，可授予：高等教育文凭（Diploma of Higher Education）"
        elif total_credits >= 60:
            return f"补偿学分过多（{compensation_credits}学分），无法授予学位。已修满60学分，可授予：高等教育证书（Certificate of Higher Education）"
        else:
            return f"补偿学分过多且学分不足，无法授予任何学位或证书。"
    
    # 选择最优105学分
    if project_type == "3+1":
        # 3+1项目只考虑Level 6
        valid_modules = modules_df[modules_df['level'] == 6].copy()
        valid_modules = valid_modules[valid_modules['score'] >= 40]
        valid_modules = valid_modules.sort_values('score', ascending=False)
        
        # 计算加权平均分
        total_weight = 0
        weighted_sum = 0
        credits_used = 0
        
        for _, row in valid_modules.iterrows():
            if credits_used + row['credits'] <= 105:
                weight = row['credits'] / 15
                weighted_sum += weight * row['score']
                total_weight += weight
                credits_used += row['credits']
        
        if total_weight == 0:
            return "没有可用于计算的课程"
        
        final_average = weighted_sum / total_weight
        
    else:  # 2+2项目
        # 分别计算Level 5和Level 6
        l5_modules = modules_df[modules_df['level'] == 5].copy()
        l6_modules = modules_df[modules_df['level'] == 6].copy()
        
        # 计算Level 5平均分
        l5_valid = l5_modules[l5_modules['score'] >= 40].sort_values('score', ascending=False)
        l5_credits_used = 0
        l5_weighted_sum = 0
        l5_total_weight = 0
        
        for _, row in l5_valid.iterrows():
            if l5_credits_used + row['credits'] <= 105:
                weight = row['credits'] / 15
                l5_weighted_sum += weight * row['score']
                l5_total_weight += weight
                l5_credits_used += row['credits']
        
        # 计算Level 6平均分
        l6_valid = l6_modules[l6_modules['score'] >= 40].sort_values('score', ascending=False)
        l6_credits_used = 0
        l6_weighted_sum = 0
        l6_total_weight = 0
        
        for _, row in l6_valid.iterrows():
            if l6_credits_used + row['credits'] <= 105:
                weight = row['credits'] / 15
                l6_weighted_sum += weight * row['score']
                l6_total_weight += weight
                l6_credits_used += row['credits']
        
        if l5_total_weight == 0 or l6_total_weight == 0:
            return "Level 5或Level 6的课程不足"
        
        l5_average = l5_weighted_sum / l5_total_weight
        l6_average = l6_weighted_sum / l6_total_weight
        
        # 2+2项目的最终平均分计算
        final_average = (l5_average + 3 * l6_average) / 4
    
    # 确定学位等级
    if final_average >= 70:
        degree_class = "一等学位"
    elif final_average >= 60:
        degree_class = "二等一学位"
    elif final_average >= 50:
        degree_class = "二等二学位"
    elif final_average >= 40:
        degree_class = "三等学位"
    else:
        degree_class = "未通过"
    
    # 检查是否在考虑提升区间
    consideration = ""
    if 68 <= final_average < 70:
        consideration = "可能提升至一等学位"
    elif 58 <= final_average < 60:
        consideration = "可能提升至二等一学位"
    elif 48 <= final_average < 50:
        consideration = "可能提升至二等二学位"
    
    return f"""
    最终平均分：{final_average:.2f}%\n学位等级：{degree_class}\n{consideration if consideration else ''}
    """

# 主程序流程
create_module_form()
display_modules()

if st.session_state.modules:
    if st.button("计算学位等级"):
        modules_df = pd.DataFrame(st.session_state.modules)
        result = calculate_degree_classification(modules_df, project_type)
        st.markdown("---")
        st.subheader("计算结果")
        st.write(result)
