from numpy import ceil
import streamlit as st
import pandas as pd
from utils.calculations import calculate_total_element_area, calculate_sheets_needed, shutter_area, side_area, top_bottom_area, back_panel_area, shelf_area
from data.material_costs import material_costs
from utils.db import save_project, load_project
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

    # Use values from JSON if available, else defaults
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
    bedroom_elements = ["Wardrobe","Dresser", "Loft", "TV Unit", "Bunk Bed", "Bed", "Pooja Unit"]

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
        with st.spinner("Saving data..."):
            total_area = 0
            area_details = {}

            for room, elements in room_data.items():
                area_details[room] = {}
                for el, dims in elements.items():
                    if el == "Bunk Bed":
                        area_details[room][el] = {}
                        for section, sec_dims in dims.items():
                            sa = shutter_area(sec_dims["height"], sec_dims["length"])
                            sda = side_area(sec_dims["width"], sec_dims["height"])
                            tba = top_bottom_area(sec_dims["length"], sec_dims["width"])
                            bpa = back_panel_area(sec_dims["height"], sec_dims["length"])
                            sha = shelf_area(sec_dims["num_shelves"], sec_dims["width"], sec_dims["length"])
                            ta = ceil(sa + sda + tba + bpa + sha)
                            total_area += ta
                            area_details[room][el][section] = {
                                "shutter_area": sa,
                                "side_area": sda,
                                "top_bottom_area": tba,
                                "back_panel_area": bpa,
                                "shelf_area": sha,
                                "total_area": ta
                            }
                    else:
                        sa = shutter_area(dims["height"], dims["length"])
                        sda = side_area(dims["width"], dims["height"])
                        tba = top_bottom_area(dims["length"], dims["width"])
                        bpa = back_panel_area(dims["height"], dims["length"])
                        sha = shelf_area(dims["num_shelves"], dims["width"], dims["length"])
                        ta = ceil(sa + sda + tba + bpa + sha)
                        total_area += ta
                        area_details[room][el] = {
                            "shutter_area": sa,
                            "side_area": sda,
                            "top_bottom_area": tba,
                            "back_panel_area": bpa,
                            "shelf_area": sha,
                            "total_area": ta
                        }

            # Save all data to JSON
            if user and project:
                project_data = load_project(user, project) or {}
                project_data["rooms"] = room_data
                project_data["house_type"] = house_type
                project_data["num_bedrooms"] = num_bedrooms
                project_data["area_details"] = area_details
                project_data["last_modified"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                save_project(user, project, project_data)

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