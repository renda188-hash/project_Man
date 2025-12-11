import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# ===================================================
# 1. 数据库配置 (从 Streamlit Secrets 读取，或者直接填在这里)
# ===================================================

# ⚠️ 极其重要：为了防止上传代码时泄露密码，我们通常使用 st.secrets
# 但为了你现在能立刻跑通，你可以先暂时填在这里
# (正式上线建议在 Streamlit Cloud 后台配置 Secrets)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# 连接数据库
@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# ===================================================
# 2. 数据库操作函数 (修改为 Supabase 版)
# ===================================================

def add_user(name, school, major, degree, contact):
    # 查重：看看手机号是不是存在
    response = supabase.table("users").select("*").eq("contact", contact).execute()
    if len(response.data) > 0:
        return False
    
    # 插入数据
    data = {
        "name": name,
        "school": school,
        "major": major,
        "degree": degree,
        "contact": contact
        # reg_time 数据库会自动生成
    }
    supabase.table("users").insert(data).execute()
    return True

def add_project(title, content, requirements):
    data = {
        "title": title,
        "content": content,
        "requirements": requirements,
        "status": "进行中"
    }
    supabase.table("projects").insert(data).execute()

def get_all_projects():
    # 获取所有项目，按创建时间倒序
    response = supabase.table("projects").select("*").order("create_time", desc=True).execute()
    df = pd.DataFrame(response.data)
    return df

def get_all_users():
    # 获取所有用户
    response = supabase.table("users").select("*").order("reg_time", desc=True).execute()
    df = pd.DataFrame(response.data)
    return df

# ===================================================
# 3. 界面 UI 设计 (这就不用大改了，逻辑复用)
# ===================================================
st.set_page_config(page_title="高校项目管理系统", layout="wide", page_icon="🎓")

st.sidebar.title("🎓 导航菜单")
menu = st.sidebar.radio("请选择身份：", ["我是同学 (登记/看项目)", "我是管理员 (发布/管理)"])

if menu == "我是同学 (登记/看项目)":
    st.title("📌 项目大厅 & 人员登记")
    
    tab1, tab2 = st.tabs(["📋 我要登记", "📢 查看项目"])
    
    with tab1:
        st.info("首次参与项目，请先填写个人信息录入库中。")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("姓名")
            school = st.text_input("学校")
            major = st.text_input("专业")
        with col2:
            degree = st.selectbox("学历", ["本科", "硕士", "博士", "其他"])
            contact = st.text_input("联系方式 (微信/手机)")
        
        if st.button("提交登记", type="primary"):
            if name and contact:
                try:
                    if add_user(name, school, major, degree, contact):
                        st.success(f"🎉 {name} 同学，登记成功！数据已存入云端。")
                    else:
                        st.warning("您似乎已经登记过了。")
                except Exception as e:
                    st.error(f"发生错误: {e}")
            else:
                st.error("请至少填写姓名和联系方式。")

    with tab2:
        st.header("正在招募的项目")
        try:
            df_projects = get_all_projects()
            if df_projects.empty:
                st.write("暂无项目发布...")
            else:
                for index, row in df_projects.iterrows():
                    with st.container():
                        st.markdown(f"### 🔹 {row['title']}")
                        # 处理时间格式
                        c_time = row['create_time'][:10] if 'create_time' in row else ''
                        st.caption(f"发布时间: {c_time} | 状态: {row['status']}")
                        st.markdown(f"**项目详情：** {row['content']}")
                        st.markdown(f"**人员要求：** {row['requirements']}")
                        st.markdown("---")
        except Exception as e:
             st.write("暂无数据或连接中...")

elif menu == "我是管理员 (发布/管理)":
    st.title("🔧 管理员后台")
    pwd = st.sidebar.text_input("输入管理员密码", type="password")
    
    if pwd == "admin888":
        admin_tab1, admin_tab2 = st.tabs(["🚀 发布新项目", "👥 人员花名册"])
        
        with admin_tab1:
            st.subheader("发布一个新的项目需求")
            p_title = st.text_input("项目标题")
            p_content = st.text_area("项目具体内容")
            p_req = st.text_area("对参与人员的要求")
            
            if st.button("确认发布"):
                if p_title:
                    add_project(p_title, p_content, p_req)
                    st.success("发布成功！已同步至云端数据库。")
                else:
                    st.error("标题不能为空")
        
        with admin_tab2:
            st.subheader("已登记人员列表")
            try:
                df_users = get_all_users()
                st.dataframe(df_users, use_container_width=True)
                if not df_users.empty:
                    st.download_button("下载花名册 Excel", df_users.to_csv(index=False).encode('utf-8'), "users.csv")
            except:
                st.write("暂无人员登记")
    else:
        st.info("请输入正确的管理员密码以访问后台。")
