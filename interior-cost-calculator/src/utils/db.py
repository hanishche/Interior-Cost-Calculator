import mysql.connector
from mysql.connector import Error
import hashlib
from datetime import datetime
import streamlit as st


# DB_CONFIG = {
#     "host": "gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
#     "user": "31Ua6EQVsEhaNWW.root",
#     "password": "o0mOBe7xjhxymToB",
#     "database": "Interiors",
#     "port": 4000
# }
# ---- MySQL Connection ----


def get_db_connection():
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        database=st.secrets["mysql"]["database"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        port=st.secrets["mysql"].get("port", 3306)
    )

# def get_db_connection():
#     return mysql.connector.connect(**DB_CONFIG)

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

def get_user_id(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Users WHERE username=%s", (username,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else None

def save_project(username, project_name, project_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_id = get_user_id(username)
    if not user_id:
        return False
    try:
        house_type = project_data.get("house_type")
        num_bedrooms = project_data.get("num_bedrooms")
        # Insert or update project with house_type and num_bedrooms
        cursor.execute("""
            INSERT INTO Projects (user_id, project_name, created_at, last_modified, house_type, num_bedrooms)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE last_modified=%s, house_type=%s, num_bedrooms=%s
        """, (user_id, project_name, now, now, house_type, num_bedrooms, now, house_type, num_bedrooms))
        conn.commit()
        # Get project_id
        cursor.execute("SELECT id FROM Projects WHERE user_id=%s AND project_name=%s", (user_id, project_name))
        project_id = cursor.fetchone()[0]
        # Remove old rooms/elements/materials/areadetails for this project
        cursor.execute("SELECT id FROM Rooms WHERE project_id=%s", (project_id,))
        room_ids = [row[0] for row in cursor.fetchall()]
        if room_ids:
            # Get all element ids for these rooms
            cursor.execute("SELECT id FROM Elements WHERE room_id IN (%s)" % ','.join(['%s']*len(room_ids)), tuple(room_ids))
            element_ids = [row[0] for row in cursor.fetchall()]
            if element_ids:
                cursor.execute("DELETE FROM AreaDetails WHERE element_id IN (%s)" % ','.join(['%s']*len(element_ids)), tuple(element_ids))
                cursor.execute("DELETE FROM Materials WHERE element_id IN (%s)" % ','.join(['%s']*len(element_ids)), tuple(element_ids))
                cursor.execute("DELETE FROM Elements WHERE id IN (%s)" % ','.join(['%s']*len(element_ids)), tuple(element_ids))
            cursor.execute("DELETE FROM Rooms WHERE project_id=%s", (project_id,))
        # Insert rooms, elements, materials
        for room_name, elements in project_data.get("rooms", {}).items():
            cursor.execute("INSERT INTO Rooms (project_id, room_name) VALUES (%s, %s)", (project_id, room_name))
            room_id = cursor.lastrowid
            for el_name, el in elements.items():
                # Handle Bunk Bed (sections) or normal element
                if el_name == "Bunk Bed" and isinstance(el, dict):
                    for section_name, section in el.items():
                        cursor.execute(
                            "INSERT INTO Elements (room_id, element_name, height, length, width, num_shelves) VALUES (%s, %s, %s, %s, %s, %s)",
                            (room_id, f"{el_name} - {section_name}", section.get("height", 0), section.get("length", 0), section.get("width", 0), section.get("num_shelves", 0))
                        )
                        element_id = cursor.lastrowid
                        key_prefix = f"{room_name}|{el_name}|{section_name}"
                        for mat_type in ["shutter", "carcus", "laminate"]:
                            mat = project_data.get("element_materials", {}).get(key_prefix, {}).get(mat_type, {})
                            if mat:
                                cursor.execute(
                                    "INSERT INTO Materials (element_id, material_type, type, brand, model, grade, thickness, rate) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                                    (
                                        element_id, mat_type,
                                        mat.get("type", ""),  # <-- Save the type value
                                        mat.get("brand", ""),
                                        mat.get("model", ""),
                                        mat.get("grade", ""),
                                        mat.get("thickness", ""),
                                        mat.get("rate", 0)
                                    )
                                )
                else:
                    cursor.execute(
                        "INSERT INTO Elements (room_id, element_name, height, length, width, num_shelves) VALUES (%s, %s, %s, %s, %s, %s)",
                        (room_id, el_name, el.get("height", 0), el.get("length", 0), el.get("width", 0), el.get("num_shelves", 0))
                    )
                    element_id = cursor.lastrowid
                    key_prefix = f"{room_name}|{el_name}"
                    for mat_type in ["shutter", "carcus", "laminate"]:
                        mat = project_data.get("element_materials", {}).get(key_prefix, {}).get(mat_type, {})
                        if mat:
                            cursor.execute(
                                "INSERT INTO Materials (element_id, material_type, type, brand, model, grade, thickness, rate) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                                (
                                    element_id, mat_type,
                                    mat.get("type", ""),  # <-- Save the type value
                                    mat.get("brand", ""),
                                    mat.get("model", ""),
                                    mat.get("grade", ""),
                                    mat.get("thickness", ""),
                                    mat.get("rate", 0)
                                )
            )
        conn.commit()
        return True
    except Error as e:
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def load_project(username, project_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    user_id = get_user_id(username)
    if not user_id:
        return None
    # Fetch project row with house_type and num_bedrooms
    cursor.execute("SELECT id, house_type, num_bedrooms FROM Projects WHERE user_id=%s AND project_name=%s", (user_id, project_name))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return None
    project_id = row["id"]
    house_type = row.get("house_type")
    num_bedrooms = row.get("num_bedrooms")
    # Load rooms
    cursor.execute("SELECT id, room_name FROM Rooms WHERE project_id=%s", (project_id,))
    rooms = {}
    room_id_map = {}
    for r in cursor.fetchall():
        rooms[r["room_name"]] = {}
        room_id_map[r["id"]] = r["room_name"]
    # Load elements
    element_id_map = {}
    if room_id_map:
        cursor.execute(
            "SELECT id, room_id, element_name, height, length, width, num_shelves FROM Elements WHERE room_id IN (%s)" % ','.join(['%s']*len(room_id_map)),
            tuple(room_id_map.keys())
        )
        for el in cursor.fetchall():
            room_name = room_id_map[el["room_id"]]
            el_name = el["element_name"]
            # Handle Bunk Bed sections
            if el_name.startswith("Bunk Bed - "):
                base = "Bunk Bed"
                section = el_name.replace("Bunk Bed - ", "")
                if base not in rooms[room_name]:
                    rooms[room_name][base] = {}
                rooms[room_name][base][section] = {
                    "height": el["height"],
                    "length": el["length"],
                    "width": el["width"],
                    "num_shelves": el["num_shelves"]
                }
                # For materials mapping
                element_id_map[el["id"]] = (room_name, f"{base}|{section}")
            else:
                rooms[room_name][el_name] = {
                    "height": el["height"],
                    "length": el["length"],
                    "width": el["width"],
                    "num_shelves": el["num_shelves"]
                }
                element_id_map[el["id"]] = (room_name, el_name)
        # Load materials
        if element_id_map:
            cursor.execute(
                "SELECT element_id, material_type, type, brand, model, grade, thickness, rate FROM Materials WHERE element_id IN (%s)" % ','.join(['%s']*len(element_id_map)),
                tuple(element_id_map.keys())
            )
            element_materials = {}
            for mat in cursor.fetchall():
                room_name, el_key = element_id_map[mat["element_id"]]
                # el_key is either "Element" or "Bunk Bed|Section"
                if "|" in el_key:
                    base, section = el_key.split("|", 1)
                    key = f"{room_name}|{base}|{section}"
                else:
                    key = f"{room_name}|{el_key}"
                if key not in element_materials:
                    element_materials[key] = {}
                element_materials[key][mat["material_type"]] = {
                    "type": mat.get("type", ""),  # <-- Load the type value
                    "brand": mat["brand"],
                    "model": mat["model"],
                    "grade": mat["grade"],
                    "thickness": mat["thickness"],
                    "rate": mat["rate"]
                }
        else:
            element_materials = {}
    else:
        element_materials = {}
    cursor.close()
    conn.close()
    return {
        "rooms": rooms,
        "element_materials": element_materials,
        "house_type": house_type,
        "num_bedrooms": num_bedrooms
    }

def list_projects(username):
    user_id = get_user_id(username)
    if not user_id:
        return []
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT project_name, created_at, last_modified FROM Projects WHERE user_id=%s", (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def save_area_details(element_id, section_name, area_info, cursor):
    cursor.execute("""
        INSERT INTO AreaDetails (
            element_id, section_name, shutter_area, side_area, top_bottom_area, back_panel_area, shelf_area, total_area
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            shutter_area=VALUES(shutter_area),
            side_area=VALUES(side_area),
            top_bottom_area=VALUES(top_bottom_area),
            back_panel_area=VALUES(back_panel_area),
            shelf_area=VALUES(shelf_area),
            total_area=VALUES(total_area)
    """, (
        element_id, section_name,
        area_info.get("shutter_area", 0),
        area_info.get("side_area", 0),
        area_info.get("top_bottom_area", 0),
        area_info.get("back_panel_area", 0),
        area_info.get("shelf_area", 0),
        area_info.get("total_area", 0)
    ))