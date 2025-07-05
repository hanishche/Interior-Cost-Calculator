import streamlit as st

def house_type_selector():
    house_types = ["Apartment flat", "Independent House", "Villa"]
    selected_house_type = st.selectbox("Select House Type", house_types)
    return selected_house_type

def bedroom_selector():
    num_bedrooms = st.number_input("Number of Bedrooms", min_value=1, max_value=10, value=1)
    return num_bedrooms

def room_type_selector(num_bedrooms):
    room_types = ["Master", "Child", "Guest", "Other Bedroom1", "Other Bedroom2"]
    selected_room_types = []
    for i in range(num_bedrooms):
        room_type = st.selectbox(f"Select Room Type for Bedroom {i + 1}", room_types)
        selected_room_types.append(room_type)
    return selected_room_types

def element_selector():
    elements = ["Wardrobe","Dresser", "Loft", "TV Unit", "Bunk Bed", "Bed", "Modular Kitchen", "Crockery", "Pooja unit"]
    selected_elements = st.multiselect("Select Elements", elements)
    return selected_elements

def dimension_input(element):
    dimensions = st.text_input(f"Enter dimensions for {element} (length x width x height in ft)", "0 x 0 x 0")
    return dimensions

def material_type_selector():
    materials = ["Material A", "Material B", "Material C"]  # Example materials
    selected_materials = {
        "Shutters": st.selectbox("Select Material for Shutters", materials),
        "Carcus": st.selectbox("Select Material for Carcus", materials),
        "Laminate": st.selectbox("Select Material for Laminate", materials)
    }
    return selected_materials

def calculate_sheets(total_area):
    sheet_area = 32  # 8x4 sheet area in sq ft
    num_sheets = total_area / sheet_area
    return num_sheets