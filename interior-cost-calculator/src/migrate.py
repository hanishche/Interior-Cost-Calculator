import json
import os
import hashlib
from utils.db import get_db_connection, hash_password

def migrate_users(users_json_path):
    with open(users_json_path, "r") as f:
        users = json.load(f)
    conn = get_db_connection()
    cursor = conn.cursor()
    for username, info in users.items():
        password = info["password"]
        password_hash = hash_password(password)
        try:
            cursor.execute("INSERT IGNORE INTO Users (username, password_hash) VALUES (%s, %s)", (username, password_hash))
        except Exception as e:
            print(f"Error inserting user {username}: {e}")
    conn.commit()
    cursor.close()
    conn.close()
    print("Users migrated.")

def get_user_id(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Users WHERE username=%s", (username,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else None

def migrate_project(username, project_name, project_json_path):
    with open(project_json_path, "r") as f:
        data = json.load(f)
    user_id = get_user_id(username)
    if not user_id:
        print(f"User {username} not found in DB.")
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    # Insert project
    cursor.execute(
        "INSERT INTO Projects (user_id, project_name, created_at, last_modified) VALUES (%s, %s, NOW(), NOW()) ON DUPLICATE KEY UPDATE last_modified=NOW()",
        (user_id, project_name)
    )
    conn.commit()
    cursor.execute("SELECT id FROM Projects WHERE user_id=%s AND project_name=%s", (user_id, project_name))
    project_id = cursor.fetchone()[0]
    # Insert rooms, elements, materials
    for room_name, elements in data.get("rooms", {}).items():
        cursor.execute("INSERT INTO Rooms (project_id, room_name) VALUES (%s, %s)", (project_id, room_name))
        room_id = cursor.lastrowid
        for el_name, el in elements.items():
            if el_name == "Bunk Bed" and isinstance(el, dict):
                for section_name, section in el.items():
                    cursor.execute(
                        "INSERT INTO Elements (room_id, element_name, height, length, width, num_shelves) VALUES (%s, %s, %s, %s, %s, %s)",
                        (room_id, f"{el_name} - {section_name}", section.get("height", 0), section.get("length", 0), section.get("width", 0), section.get("num_shelves", 0))
                    )
                    element_id = cursor.lastrowid
                    key_prefix = f"{room_name}|{el_name}|{section_name}"
                    for mat_type in ["shutter", "carcus", "laminate"]:
                        mat = data.get("element_materials", {}).get(key_prefix, {}).get(mat_type, {})
                        if mat:
                            cursor.execute(
                                "INSERT INTO Materials (element_id, material_type, brand, model, grade, thickness, rate) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                (element_id, mat_type, mat.get("brand", ""), mat.get("model", ""), mat.get("grade", ""), mat.get("thickness", ""), mat.get("rate", 0))
                            )
            else:
                cursor.execute(
                    "INSERT INTO Elements (room_id, element_name, height, length, width, num_shelves) VALUES (%s, %s, %s, %s, %s, %s)",
                    (room_id, el_name, el.get("height", 0), el.get("length", 0), el.get("width", 0), el.get("num_shelves", 0))
                )
                element_id = cursor.lastrowid
                key_prefix = f"{room_name}|{el_name}"
                for mat_type in ["shutter", "carcus", "laminate"]:
                    mat = data.get("element_materials", {}).get(key_prefix, {}).get(mat_type, {})
                    if mat:
                        cursor.execute(
                            "INSERT INTO Materials (element_id, material_type, brand, model, grade, thickness, rate) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (element_id, mat_type, mat.get("brand", ""), mat.get("model", ""), mat.get("grade", ""), mat.get("thickness", ""), mat.get("rate", 0))
                        )
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Project '{project_name}' for user '{username}' migrated.")

if __name__ == "__main__":
    # 1. Migrate users
    migrate_users("users.json")
    # 2. Migrate projects
    projects_root = os.path.join("projects")
    for username in os.listdir(projects_root):
        user_dir = os.path.join(projects_root, username)
        if os.path.isdir(user_dir):
            for file in os.listdir(user_dir):
                if file.endswith(".json"):
                    project_name = file.replace(".json", "")
                    project_json_path = os.path.join(user_dir, file)
                    migrate_project(username, project_name, project_json_path)