from numpy import ceil
import streamlit as st
import pandas as pd
from utils.calculations import calculate_total_element_area, calculate_sheets_needed, shutter_area, side_area, top_bottom_area, back_panel_area, shelf_area
from data.material_costs import material_costs
from utils.db import save_project, load_project, save_area_details, get_db_connection
import os

st.set_page_config(initial_sidebar_state="collapsed")
hide_sidebar_style = """
    <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_sidebar_style, unsafe_allow_html=True)

if st.button("🏠 Home"):
    st.session_state.pop("project", None)
    st.switch_page("main.py")



def main():
    st.set_page_config(layout="wide")
    st.title("Interior Cost Calculator")

    # --- Load existing data if any ---
    user = st.session_state.get("username")
    project = st.session_state.get("project")
    project_data = {}
    existing_room_data = {}
    existing_house_type = None
    existing_num_bedrooms = None


    if user and project:
        project_data = load_project(user, project) or {}
        existing_room_data = project_data.get("rooms", {})
        existing_house_type = project_data.get("house_type")
        existing_num_bedrooms = project_data.get("num_bedrooms")

    # Use values from DB if available, else defaults
    house_type = st.selectbox(
        "Select House Type",
        ["Apartment Flat", "Independent House", "Villa"],
        index=(["Apartment Flat", "Independent House", "Villa"].index(existing_house_type)
               if existing_house_type in ["Apartment Flat", "Independent House", "Villa"] else 0)
    )
    num_bedrooms = st.number_input(
        "Number of Bedrooms",
        min_value=1,
        max_value=10,
        value=int(existing_num_bedrooms) if existing_num_bedrooms else 1
    )


    # Generate bedroom names automatically
    bedroom_ids = []
    if num_bedrooms >= 1:
        bedroom_ids.append("Master Bedroom")
    if num_bedrooms >= 2:
        bedroom_ids.append("Kids Bedroom")
    if num_bedrooms >= 3:
        bedroom_ids.append("Guest Bedroom")
    for i in range(4, int(num_bedrooms) + 1):
        bedroom_ids.append(f"Other Bedroom {i-3}")

    all_rooms = bedroom_ids + ["Kitchen", "Living", "Dining"]

    # Define allowed elements per room type
    kitchen_elements = ["Kitchen Lower", "Kitchen Upper", "Kitchen Side", "Loft"]
    living_elements = ["TV Unit", "Pooja Unit"]
    dining_elements = ["Crockery"]
    bedroom_elements = ["Wardrobe", "Loft", "TV Unit", "Bunk Bed", "Bed", "Pooja Unit"]

    room_data = {}

    st.subheader("Room Elements and Dimensions")
    cols = st.columns(len(all_rooms))
    for i, room in enumerate(all_rooms):
        with cols[i]:
            st.markdown(f"### {room}")

            # Select elements based on room type
            if "Kitchen" in room:
                element_options = kitchen_elements
            elif "Living" in room:
                element_options = living_elements
            elif "Dining" in room:
                element_options = dining_elements
            else:
                element_options = bedroom_elements

            # Preselect elements if present in existing data
            preselected_elements = [
                el for el in (existing_room_data.get(room, {}) or {}).keys()
                if el in element_options
            ]
            selected_elements = st.multiselect(
                f"Elements",
                element_options,
                default=preselected_elements,
                key=f"elements_{room}_{i}"
            )
            element_dims = {}

            for el in selected_elements:
                # Special handling for Bunk Bed in bedrooms
                if el == "Bunk Bed":
                    st.markdown("**Bunk Bed Sections:**")
                    bunk_sections = ["Bunk bed Lower", "Bunk bed Upper", "Bunk Bed Extra"]
                    bunk_dims = {}
                    bunk_cols = st.columns(3)
                    for j, section in enumerate(bunk_sections):
                        with bunk_cols[j]:
                            st.markdown(f"**{section}**")
                            prev = existing_room_data.get(room, {}).get(el, {}).get(section, {})
                            l = st.number_input(f"L", min_value=0.0, value=float(prev.get("length", 0.0)), key=f"{room}_{el}_{section}_length")
                            w = st.number_input(f"W", min_value=0.0, value=float(prev.get("width", 0.0)), key=f"{room}_{el}_{section}_width")
                            h = st.number_input(f"H", min_value=0.0, value=float(prev.get("height", 0.0)), key=f"{room}_{el}_{section}_height")
                            shelves = st.number_input(f"Shelves (same L & W)", min_value=0, max_value=10, value=int(prev.get("num_shelves", 0)), key=f"{room}_{el}_{section}_shelves")
                            bunk_dims[section] = {
                                "length": l,
                                "width": w,
                                "height": h,
                                "num_shelves": shelves
                            }
                    element_dims[el] = bunk_dims
                else:
                    st.markdown(f"**{el}**")
                    prev = existing_room_data.get(room, {}).get(el, {})
                    lwh_cols = st.columns(3)
                    length = lwh_cols[0].number_input(f"L", min_value=0.0, value=float(prev.get("length", 0.0)), key=f"{room}_{el}_length")
                    width = lwh_cols[1].number_input(f"W", min_value=0.0, value=float(prev.get("width", 0.0)), key=f"{room}_{el}_width")
                    height = lwh_cols[2].number_input(f"H", min_value=0.0, value=float(prev.get("height", 0.0)), key=f"{room}_{el}_height")
                    num_shelves = st.number_input(f"Shelves (same L & W)", min_value=0, max_value=10, value=int(prev.get("num_shelves", 0)), key=f"{room}_{el}_shelves")
                    element_dims[el] = {
                        "length": length,
                        "width": width,
                        "height": height,
                        "num_shelves": num_shelves
                    }
            room_data[room] = element_dims

    # Calculate total area and sheets
    if st.button("Calculate & Save"):
        total_area = 0
        area_details = {}
        conn = get_db_connection()
        cursor = conn.cursor()
        for room, elements in room_data.items():
            area_details[room] = {}
            for el, dims in elements.items():
                if el == "Bunk Bed":
                    area_details[room][el] = {}
                    for section, sec_dims in dims.items():
                        # Calculate areas
                        sa = shutter_area(sec_dims["height"], sec_dims["length"])
                        sda = side_area(sec_dims["width"], sec_dims["height"])
                        tba = top_bottom_area(sec_dims["length"], sec_dims["width"])
                        bpa = back_panel_area(sec_dims["height"], sec_dims["length"])
                        sha = shelf_area(sec_dims["num_shelves"], sec_dims["width"], sec_dims["length"])
                        ta = ceil(sa + sda + tba + bpa + sha)
                        area = ta
                        total_area += area
                        area_details[room][el][section] = {
                            "shutter_area": sa,
                            "side_area": sda,
                            "top_bottom_area": tba,
                            "back_panel_area": bpa,
                            "shelf_area": sha,
                            "total_area": ta
                        }
                        # 1. Get or insert project
                        cursor.execute(
                            "SELECT id FROM Projects WHERE user_id=(SELECT id FROM Users WHERE username=%s) AND project_name=%s",
                            (user, project)
                        )
                        project_row = cursor.fetchone()
                        if not project_row:
                            st.error("Project not found in DB.")
                            st.stop()
                        project_id = project_row[0]
                        # 2. Get or insert room
                        cursor.execute(
                            "SELECT id FROM Rooms WHERE project_id=%s AND room_name=%s",
                            (project_id, room)
                        )
                        room_row = cursor.fetchone()
                        if room_row:
                            room_id = room_row[0]
                        else:
                            cursor.execute(
                                "INSERT INTO Rooms (project_id, room_name) VALUES (%s, %s)",
                                (project_id, room)
                            )
                            room_id = cursor.lastrowid
                        # 3. Upsert element for each section
                        element_name = f"{el} - {section}"
                        cursor.execute(
                            "SELECT id FROM Elements WHERE room_id=%s AND element_name=%s",
                            (room_id, element_name)
                        )
                        element_row = cursor.fetchone()
                        if element_row:
                            element_id = element_row[0]
                            cursor.execute(
                                "UPDATE Elements SET height=%s, length=%s, width=%s, num_shelves=%s WHERE id=%s",
                                (sec_dims["height"], sec_dims["length"], sec_dims["width"], sec_dims["num_shelves"], element_id)
                            )
                        else:
                            cursor.execute(
                                "INSERT INTO Elements (room_id, element_name, height, length, width, num_shelves) VALUES (%s, %s, %s, %s, %s, %s)",
                                (room_id, element_name, sec_dims["height"], sec_dims["length"], sec_dims["width"], sec_dims["num_shelves"])
                            )
                            element_id = cursor.lastrowid
                        # 4. Upsert AreaDetails
                        cursor.execute(
                            "SELECT id FROM AreaDetails WHERE element_id=%s AND section_name=%s",
                            (element_id, section)
                        )
                        area_row = cursor.fetchone()
                        if area_row:
                            cursor.execute(
                                "UPDATE AreaDetails SET shutter_area=%s, side_area=%s, top_bottom_area=%s, back_panel_area=%s, shelf_area=%s, total_area=%s WHERE element_id=%s AND section_name=%s",
                                (
                                    sa, sda, tba, bpa, sha, ta, element_id, section
                                )
                            )
                        else:
                            save_area_details(
                                element_id=element_id,
                                section_name=section,
                                area_info=area_details[room][el][section],
                                cursor=cursor
                            )
                else:
                    # Calculate areas
                    sa = shutter_area(dims["height"], dims["length"])
                    sda = side_area(dims["width"], dims["height"])
                    tba = top_bottom_area(dims["length"], dims["width"])
                    bpa = back_panel_area(dims["height"], dims["length"])
                    sha = shelf_area(dims["num_shelves"], dims["width"], dims["length"])
                    ta = ceil(sa + sda + tba + bpa + sha)
                    area = ta
                    total_area += area
                    area_details[room][el] = {
                        "shutter_area": sa,
                        "side_area": sda,
                        "top_bottom_area": tba,
                        "back_panel_area": bpa,
                        "shelf_area": sha,
                        "total_area": ta
                    }
                    # 1. Get or insert project
                    cursor.execute(
                        "SELECT id FROM Projects WHERE user_id=(SELECT id FROM Users WHERE username=%s) AND project_name=%s",
                        (user, project)
                    )
                    project_row = cursor.fetchone()
                    if not project_row:
                        st.error("Project not found in DB.")
                        st.stop()
                    project_id = project_row[0]
                    # 2. Get or insert room
                    cursor.execute(
                        "SELECT id FROM Rooms WHERE project_id=%s AND room_name=%s",
                        (project_id, room)
                    )
                    room_row = cursor.fetchone()
                    if room_row:
                        room_id = room_row[0]
                    else:
                        cursor.execute(
                            "INSERT INTO Rooms (project_id, room_name) VALUES (%s, %s)",
                            (project_id, room)
                        )
                        room_id = cursor.lastrowid
                    # 3. Upsert element
                    cursor.execute(
                        "SELECT id FROM Elements WHERE room_id=%s AND element_name=%s",
                        (room_id, el)
                    )
                    element_row = cursor.fetchone()
                    if element_row:
                        element_id = element_row[0]
                        cursor.execute(
                            "UPDATE Elements SET height=%s, length=%s, width=%s, num_shelves=%s WHERE id=%s",
                            (dims["height"], dims["length"], dims["width"], dims["num_shelves"], element_id)
                        )
                    else:
                        cursor.execute(
                            "INSERT INTO Elements (room_id, element_name, height, length, width, num_shelves) VALUES (%s, %s, %s, %s, %s, %s)",
                            (room_id, el, dims["height"], dims["length"], dims["width"], dims["num_shelves"])
                        )
                        element_id = cursor.lastrowid
                    # 4. Upsert AreaDetails
                    cursor.execute(
                        "SELECT id FROM AreaDetails WHERE element_id=%s AND section_name IS NULL",
                        (element_id,)
                    )
                    area_row = cursor.fetchone()
                    if area_row:
                        cursor.execute(
                            "UPDATE AreaDetails SET shutter_area=%s, side_area=%s, top_bottom_area=%s, back_panel_area=%s, shelf_area=%s, total_area=%s WHERE element_id=%s AND section_name IS NULL",
                            (
                                sa, sda, tba, bpa, sha, ta, element_id
                            )
                        )
                    else:
                        save_area_details(
                            element_id=element_id,
                            section_name=None,
                            area_info=area_details[room][el],
                            cursor=cursor
                        )
   
        # --- Save room_data to DB ---
        if user and project:
            project_data = load_project(user, project) or {}
            project_data["rooms"] = room_data
            project_data["house_type"] = house_type
            project_data["num_bedrooms"] = num_bedrooms
            save_project(user, project, project_data)

        # --- CLEANUP: Remove AreaDetails/Elements not in current UI ---
        cursor.execute("""
            SELECT e.id, e.element_name, r.room_name
            FROM Elements e
            JOIN Rooms r ON e.room_id = r.id
            WHERE r.project_id = %s
        """, (project_id,))
        existing_elements = cursor.fetchall()

        current_element_names = set()
        for room, elements in room_data.items():
            for el, dims in elements.items():
                if el == "Bunk Bed":
                    for section in dims.keys():
                        current_element_names.add((room, f"{el} - {section}"))
                else:
                    current_element_names.add((room, el))

        for element in existing_elements:
            room_name = element[2]
            element_name = element[1]
            if (room_name, element_name) not in current_element_names:
                cursor.execute("DELETE FROM AreaDetails WHERE element_id=%s", (element[0],))
                cursor.execute("DELETE FROM Elements WHERE id=%s", (element[0],))

        # Now commit and close
        conn.commit()
        cursor.close()
        conn.close()
        sheets_required = calculate_sheets_needed(ceil(total_area))
        st.session_state['total_area'] = ceil(total_area)
        st.session_state['sheets_required'] = ceil(sheets_required)
        st.session_state['calculated'] = True

    if st.session_state.get('calculated', False):
        st.write(f"**Total Area:** {st.session_state['total_area']} sq ft")
        st.write(f"**Sheets of 8x4 required:** {st.session_state['sheets_required']}")

    # Add navigation button at the bottom

    st.markdown("---")
    if st.button("Next: Select Materials"):
        st.switch_page("pages/02_MaterialSelection.py")

if __name__ == "__main__":
    main()