import streamlit as st
import os
import json
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Interior Cost Calculator", layout="wide", initial_sidebar_state="collapsed")
hide_sidebar_style = """
    <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_sidebar_style, unsafe_allow_html=True)

USERS_FILE = "users.json"
PROJECTS_DIR = "projects"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

# ---- Streamlit App ----
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None

def authenticate_user(username, password):
    users = load_users()
    if username in users and users[username]["password"] == password:
        return True, username
    return False, None

def register_user(username, password):
    users = load_users()
    if username in users:
        return False, "Username already exists."
    users[username] = {"password": password}
    save_users(users)
    return True, "Registration successful."



def get_current_datetime():
    # Returns current date and time as a string, e.g., '2025-06-30 02:19:00'
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def project_selector():
    st.title("Projects")

    user = st.session_state.get("username", "default_user")
    user_dir = os.path.join("projects", user)
    os.makedirs(user_dir, exist_ok=True)

    # Load projects
    projects = []
    now = get_current_datetime()
    for file in os.listdir(user_dir):
        if file.endswith(".json"):
            with open(os.path.join(user_dir, file), "r") as f:
                data = json.load(f)
                created = data.get("created_at", now)
                last_modified = data.get("last_modified", created)
                projects.append({
                    "Project": data.get("name", file.replace(".json", "")),
                    "Created Date": created,
                    "Last Modified": last_modified
                })

    if projects:
        df = pd.DataFrame(projects)
        st.dataframe(df, use_container_width=True)

        selected_project = st.selectbox(
            "Select a project to manage:",
            df["Project"].tolist()
        )

        col1, col2 = st.columns(2)
        if col1.button("Open Project"):
            project_file = os.path.join(user_dir, f"{selected_project}.json")
            with open(project_file, "r") as f:
                project_data = json.load(f)

            st.session_state["project"] = selected_project

            # Check if 'materials' and 'area_details' exist and are not empty
            has_materials = "materials" in project_data and bool(project_data["materials"])
            has_area = "area_details" in project_data and bool(project_data["area_details"])

            if has_materials and has_area:
                st.switch_page("pages/03_Summary.py")  # Redirect to summary page
            else:
                st.switch_page("pages/01_ProjectInput.py")  # Redirect to project input page

        if col2.button("Delete Project"):
            os.remove(os.path.join(user_dir, f"{selected_project}.json"))
            st.success(f"Deleted project: {selected_project}")
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
                project_file = os.path.join(user_dir, f"{new_project}.json")
                if os.path.exists(project_file):
                    st.warning("Project already exists!")
                else:
                    now = get_current_datetime()
                    data = {
                        "name": new_project,
                        "created_at": now,
                        "last_modified": now,
                        "house_type": house_type,
                        "num_bedrooms": num_bedrooms
                    }
                    with open(project_file, "w") as f:
                        json.dump(data, f)
                    st.success(f"Project '{new_project}' created!")
                    st.rerun()


if not st.session_state.authenticated:
    st.title("Login or Register")
    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            success, user_id = authenticate_user(username, password)
            if success:
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
            ok, msg = register_user(new_username, new_password)
            if ok:
                st.success(msg)
            else:
                st.error(msg)
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

