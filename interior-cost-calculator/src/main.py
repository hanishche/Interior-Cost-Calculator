import streamlit as st
import pandas as pd
from datetime import datetime
from utils.db import create_user, authenticate_user, save_project, load_project, list_projects

st.set_page_config(page_title="Interior Cost Calculator", layout="wide", initial_sidebar_state="collapsed")
hide_sidebar_style = """
    <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_sidebar_style, unsafe_allow_html=True)

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None

def get_current_datetime():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def project_selector():
    st.title("Projects")
    user = st.session_state.get("username")
    projects = list_projects(user)
    if projects:
        df = pd.DataFrame(projects, columns=["Project", "Created Date", "Last Modified"])
        st.dataframe(df, use_container_width=True)
        selected_project = st.selectbox(
            "Select a project to manage:",
            df["Project"].tolist()
        )
        col1, col2 = st.columns(2)
        if col1.button("Open Project"):
            st.session_state["project"] = selected_project
            project_data = load_project(user, selected_project)
            if not project_data:
                st.error("Project data not found.")
                st.stop()
            has_materials = "element_materials" in project_data and bool(project_data["element_materials"])
            has_area = "area_details" in project_data and bool(project_data.get("area_details", {}))
            if has_materials and has_area:
                st.switch_page("pages/03_Summary.py")
            else:
                st.switch_page("pages/01_ProjectInput.py")
        if col2.button("Delete Project"):
            # Remove project from JSON
            from utils.db import _load_json, _save_json
            data = _load_json()
            data["projects"] = [p for p in data["projects"] if not (p.get("username") == user and p.get("project_name") == selected_project)]
            _save_json(data)
            st.success(f"Project '{selected_project}' deleted.")
            st.rerun()
    else:
        st.info("No projects found. Add a new project to get started.")

    # Add new project
    with st.expander("➕ Add New Project"):
        new_project = st.text_input("Enter new project name", key="new_project_name")
        house_type = st.selectbox("House Type", ["Apartment", "Independent House", "Villa", "Other"], key="house_type")
        num_bedrooms = st.number_input("Number of Bedrooms", min_value=1, max_value=10, value=3, step=1, key="num_bedrooms")
        if st.button("Create Project"):
            if not new_project.strip():
                st.warning("Project name cannot be empty!")
            else:
                now = get_current_datetime()
                data = {
                    "project_name": new_project,
                    "created_at": now,
                    "last_modified": now,
                    "house_type": house_type,
                    "num_bedrooms": num_bedrooms,
                    "rooms": {},
                    "element_materials": {},
                    "area_details": {}
                }
                save_project(user, new_project, data)
                st.success(f"Project '{new_project}' created!")
                st.rerun()

if not st.session_state.authenticated:
    st.title("Login or Register")
    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            # User authentication is always performed using the database
            if authenticate_user(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password.")
    with tab2:
        new_username = st.text_input("New Username", key="reg_user")
        new_password = st.text_input("New Password", type="password", key="reg_pass")
        if st.button("Register"):
            # User registration is always performed using the database
            if create_user(new_username, new_password):
                st.success("Registration successful.")
            else:
                st.error("Username already exists.")
else:
    st.sidebar.write(f"Logged in as **{st.session_state.username}**")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.project = None
        st.rerun()
    if "project" not in st.session_state:
        project_selector()
    else:
        st.switch_page("pages/01_ProjectInput.py")