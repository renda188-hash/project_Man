import streamlit as st
from supabase import create_client
import pandas as pd
import time
from streamlit_option_menu import option_menu
# --- 1. 连接数据库 ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"❌ 数据库连接配置有误，请检查 .streamlit/secrets.toml 文件。\n错误信息: {e}")
    st.stop()

# --- 2. 核心功能函数 ---
def add_user(name, school, major, degree, contact):
    # 查重：防止重复提交
    res = supabase.table("users").select("*").eq("contact", contact).execute()
    if len(res.data) > 0:
        return False
    # 写入
    data = {"name": name, "school": school, "major": major, "degree": degree, "contact": contact}
    supabase.table("users").insert(data).execute()
    return True

def add_project(title, content, requirements):
    data = {"title": title, "content": content, "requirements": requirements}
    supabase.table("projects").insert(data).execute()

def get_projects():
    # 获取项目，按时间倒序
    res = supabase.table("projects").select("*").order("create_time", desc=True).execute()
    return pd.DataFrame(res.data)

def get_users():
    # 获取人员，按时间倒序
    res = supabase.table("users").select("*").order("reg_time", desc=True).execute()
    return pd.DataFrame(res.data)

# --- 3. 界面 UI ---
st.set_page_config(page_title="项目管理系统", page_icon="🎓", layout="centered")

# 侧边栏导航
with st.sidebar:
    # 这里的 icons 参考 Bootstrap Icons 名称
     menu = option_menu(
        "项目大厅",  # 菜单标题
        ["同学登记/看项目", "管理员后台"],  # 选项列表
        icons=['pencil-square', 'gear'],  # 对应的图标
        menu_icon="cast", # 菜单顶部的大图标
        default_index=0,
        styles={
            "container": {"padding": "5!important", "background-color": "#fafafa"},
            "icon": {"color": "orange", "font-size": "25px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#02ab21"},
        }
    )

if menu == "📝 同学登记/看项目":
    st.title("🎓 项目大厅")
    
    tab1, tab2 = st.tabs(["我是新同学 (登记)", "正在招募的项目"])
    
    with tab1:
        st.write("### 👋 欢迎加入！请先填写信息")
        with st.form("user_form"):
            name = st.text_input("姓名")
            col1, col2 = st.columns(2)
            school = col1.text_input("学校")
            major = col2.text_input("专业")
            degree = st.selectbox("学历", ["本科", "硕士", "博士", "其他"])
            contact = st.text_input("手机号/微信号 (作为唯一ID)")
            
            submitted = st.form_submit_button("提交信息", type="primary")
            if submitted:
                if name and contact:
                    try:
                        if add_user(name, school, major, degree, contact):
                            st.success(f"🎉 登记成功！{name} 同学你好。")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.warning("⚠️ 该联系方式已存在，请勿重复登记。")
                    except Exception as e:
                        st.error(f"连接错误: {e}")
                else:
                    st.error("姓名和联系方式必填！")

    with tab2:
        st.write("### 🔥 最新项目需求")
        try:
            df = get_projects()
            if df.empty:
                st.info("暂无正在进行的项目...")
            else:
                for idx, row in df.iterrows():
                    with st.container():
                        st.markdown(f"#### 📌 {row['title']}")
                        st.caption(f"状态: {row['status']}")
                        st.markdown(f"**【项目详情】**\n{row['content']}")
                        st.markdown(f"**【人员要求】**\n{row['requirements']}")
                        st.divider()
        except:
            st.write("加载中...")

elif menu == "🔧 管理员后台":
    st.title("🔧 管理员控制台")
    pwd = st.text_input("请输入管理员密码", type="password")
    
    if pwd == "admin888":  # 密码在这里改
        t1, t2 = st.tabs(["发布新项目", "查看花名册"])
        
        with t1:
            st.subheader("发布新需求")
            p_title = st.text_input("项目标题")
            p_content = st.text_area("详细内容")
            p_req = st.text_area("人员要求")
            
            if st.button("🚀 立即发布", type="primary"):
                if p_title:
                    add_project(p_title, p_content, p_req)
                    st.success("发布成功！所有同学均可见。")
                else:
                    st.warning("标题不能为空")
        
        with t2:
            st.subheader("📋 已登记人员名单")
            if st.button("🔄 刷新列表"):
                st.rerun()
                
            try:
                users_df = get_users()
                st.dataframe(users_df, use_container_width=True)
            except:
                st.info("暂无数据")


