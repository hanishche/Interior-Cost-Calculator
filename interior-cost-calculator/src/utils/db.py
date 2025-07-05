import mysql.connector
from mysql.connector import Error
import hashlib
import streamlit as st
import json
import os
from datetime import datetime
from uuid import uuid4

DATA_PATH = os.path.abspath(
                    os.path.join(
                        os.path.dirname(__file__),
                        "..", "..", "..", "json dumps", "data.json"
                    )
                )
                            


def get_db_connection():
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        database=st.secrets["mysql"]["database"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        port=st.secrets["mysql"].get("port", 3306)
    )


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Users (username, password_hash) VALUES (%s, %s)", (username, hash_password(password)))
        conn.commit()
        return True
    except Error:
        return False
    finally:
        cursor.close()
        conn.close()


def authenticate_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM Users WHERE username=%s", (username,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row and row[0] == hash_password(password):
        return True
    return False


def _load_json():
    if not os.path.exists(DATA_PATH):
        return {"projects": []}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception:
            data = {"projects": []}
    if "projects" not in data:
        # migrate old format to new
        data = {"projects": [data]}
    return data


def _save_json(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def save_project(username, project_name, project_data):
    data = _load_json()
    # Ensure project_id exists
    if "project_id" not in project_data:
        project_data["project_id"] = str(uuid4())
    # Add username and project_name for filtering
    project_data["username"] = username
    project_data["project_name"] = project_name
    # Remove old project with same username+project_name
    data["projects"] = [p for p in data["projects"] if not (p.get("username") == username and p.get("project_name") == project_name)]
    data["projects"].append(project_data)
    _save_json(data)
    return True


def load_project(username, project_name):
    data = _load_json()
    for p in data.get("projects", []):
        if p.get("username") == username and p.get("project_name") == project_name:
            return p
    return None


def list_projects(username):
    data = _load_json()
    result = []
    for p in data.get("projects", []):
        if p.get("username") == username:
            result.append((
                p.get("project_name"),
                p.get("created_at", ""),
                p.get("last_modified", "")
            ))
    return result


