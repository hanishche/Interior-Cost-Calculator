import os

def migrate_element_materials_only(username, project_name, project_json_path):
    import json
    from utils.db import get_db_connection, get_user_id

    with open(project_json_path, "r") as f:
        data = json.load(f)
    user_id = get_user_id(username)
    if not user_id:
        print(f"User {username} not found in DB.")
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    # Get project_id
    cursor.execute("SELECT id FROM Projects WHERE user_id=%s AND project_name=%s", (user_id, project_name))
    row = cursor.fetchone()
    if not row:
        print(f"Project {project_name} not found for user {username}.")
        cursor.close()
        conn.close()
        return
    project_id = row[0]
    # Get all rooms for this project
    cursor.execute("SELECT id, room_name FROM Rooms WHERE project_id=%s", (project_id,))
    room_id_map = {room_name: room_id for room_id, room_name in cursor.fetchall()}
    # Get all elements for these rooms
    if room_id_map:
        cursor.execute(
            "SELECT id, room_id, element_name FROM Elements WHERE room_id IN (%s)" % ','.join(['%s']*len(room_id_map)),
            tuple(room_id_map.values())
        )
        element_id_map = {}
        for el in cursor.fetchall():
            room_name = [k for k, v in room_id_map.items() if v == el[1]][0]
            el_name = el[2]
            # Handle Bunk Bed sections
            if el_name.startswith("Bunk Bed - "):
                base = "Bunk Bed"
                section = el_name[len("Bunk Bed - "):]
                element_id_map[f"{room_name}|{base}|{section}"] = el[0]
            # Also map the full name for non-bunk-bed
            element_id_map[f"{room_name}|{el_name}"] = el[0]
    else:
        element_id_map = {}

    # Insert only materials
    for key_prefix, mats in data.get("element_materials", {}).items():
        element_id = element_id_map.get(key_prefix)
        if not element_id:
            print(f"Element for key '{key_prefix}' not found in DB, skipping.")
            continue
        for mat_type in ["shutter", "carcus", "laminate"]:
            mat = mats.get(mat_type, {})
            if mat:
                # Check if material already exists for this element and type
                cursor.execute(
                    "SELECT id FROM Materials WHERE element_id=%s AND material_type=%s",
                    (element_id, mat_type)
                )
                if cursor.fetchone():
                    # Update existing material
                    cursor.execute(
                        "UPDATE Materials SET type=%s, brand=%s, model=%s, grade=%s, thickness=%s, rate=%s WHERE element_id=%s AND material_type=%s",
                        (mat.get("type", ""), mat.get("brand", ""), mat.get("model", ""), mat.get("grade", ""), mat.get("thickness", ""), mat.get("rate", 0), element_id, mat_type)
                    )
                else:
                    # Insert new material
                    cursor.execute(
                        "INSERT INTO Materials (element_id, material_type, type, brand, model, grade, thickness, rate) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (element_id, mat_type, mat.get("type", ""), mat.get("brand", ""), mat.get("model", ""), mat.get("grade", ""), mat.get("thickness", ""), mat.get("rate", 0))
                    )
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Element materials for project '{project_name}' and user '{username}' migrated.")
if __name__ == "__main__":
    # 1. Migrate users
    # 2. Migrate projects
    projects_root = os.path.join("projects")
    for username in os.listdir(projects_root):
        user_dir = os.path.join(projects_root, username)
        if os.path.isdir(user_dir):
            for file in os.listdir(user_dir):
                if file.endswith(".json"):
                    project_name = file.replace(".json", "")
                    project_json_path = os.path.join(user_dir, file)
                    migrate_element_materials_only(username, project_name, project_json_path)