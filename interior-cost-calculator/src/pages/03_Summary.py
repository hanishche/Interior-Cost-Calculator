import streamlit as st
import pandas as pd
from utils.db import load_project, get_db_connection

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


if st.button("⬅️⬅️ Back to Add Elements"):
    st.session_state["edit_mode"] = True
    st.switch_page("pages/01_ProjectInput.py")


# Load project data from DB
user = st.session_state.get("username")
project = st.session_state.get("project")
if not user or not project:
    st.error("User or project not found. Please login and select a project.")
    st.stop()

project_data = load_project(user, project)
if not project_data:
    st.error("Project data not found in database.")
    st.stop()

element_materials = project_data.get("element_materials", {})
rooms = project_data.get("rooms", {})

# --- Load area details from AreaDetails table ---
conn = get_db_connection()
cursor = conn.cursor(dictionary=True)

# Get project_id
cursor.execute(
    "SELECT id FROM Projects WHERE user_id=(SELECT id FROM Users WHERE username=%s) AND project_name=%s",
    (user, project)
)
project_row = cursor.fetchone()
if not project_row:
    st.error("Project not found in DB.")
    st.stop()
project_id = project_row["id"]

# Get all elements for this project
cursor.execute("""
    SELECT e.id as element_id, e.element_name, e.height, e.length, e.width, e.num_shelves, r.room_name
    FROM Elements e
    JOIN Rooms r ON e.room_id = r.id
    WHERE r.project_id = %s
""", (project_id,))
elements_db = cursor.fetchall()

# Get all area details for these elements
element_ids = [row["element_id"] for row in elements_db]
if element_ids:
    format_strings = ','.join(['%s'] * len(element_ids))
    cursor.execute(
        f"SELECT * FROM AreaDetails WHERE element_id IN ({format_strings})",
        tuple(element_ids)
    )
    area_details_db = cursor.fetchall()
else:
    area_details_db = []

# Build a lookup for area details by element_id and section_name
area_lookup = {}
for area in area_details_db:
    key = (area["element_id"], area.get("section_name"))
    area_lookup[key] = area

# Build a lookup for element_id by (room, element_name)
elementid_lookup = {}
for row in elements_db:
    elementid_lookup[(row["room_name"], row["element_name"])] = row["element_id"]

elements_data = []
total_area = 0
total_cost = 0

for row in elements_db:
    room = row["room_name"]
    el_name = row["element_name"]
    height = row["height"]
    length = row["length"]
    width = row["width"]
    num_shelves = row["num_shelves"]
    element_id = row["element_id"]

    # Try to split out section for Bunk Bed
    if "Bunk Bed" in el_name and " - " in el_name:
        el_base, section = el_name.split(" - ", 1)
        key_prefix = f"{room}|{el_base}|{section}"
        area_info = area_lookup.get((element_id, section), {})
    else:
        section = None
        key_prefix = f"{room}|{el_name}"
        area_info = area_lookup.get((element_id, None), {})

    mat_data = element_materials.get(key_prefix, {})
    shutter = mat_data.get("shutter", {})
    carcus = mat_data.get("carcus", {})
    laminate_ = mat_data.get("laminate", {})

    sa = area_info.get("shutter_area", 0)
    sda = area_info.get("side_area", 0)
    tba = area_info.get("top_bottom_area", 0)
    bpa = area_info.get("back_panel_area", 0)
    sha = area_info.get("shelf_area", 0)
    ta = area_info.get("total_area", 0)

    shutter_rate = shutter.get("rate", 0)
    carcus_rate = carcus.get("rate", 0)
    laminate_rate = laminate_.get("rate", 0)

    shutter_cost = sa * shutter_rate
    carcus_cost = (sda + tba + bpa + sha) * carcus_rate
    laminate_cost = sa * laminate_rate
    el_total_cost = shutter_cost + carcus_cost + laminate_cost

    cost_per_sft = el_total_cost / ta if ta else 0

    factory_binding = 340 * length * height
    carpenter = 300 * length * height

    SHEET_SQFT = 32
    total_sheets = ta / SHEET_SQFT if SHEET_SQFT else 0

    elements_data.append({
        "Room": room,
        "Element": el_name,
        "Height": height,
        "Length": length,
        "Width": width,
        "No of Shelves": num_shelves,
        "Shutter Material": " ".join([
            str(shutter.get("brand", "")),
            str(shutter.get("model", "")),
            str(shutter.get("grade", "")),
            str(shutter.get("thickness", ""))
        ]).strip(),
        "Carcus Material": " ".join([
            str(carcus.get("brand", "")),
            str(carcus.get("model", "")),
            str(carcus.get("grade", "")),
            str(carcus.get("thickness", ""))
        ]).strip(),
        "Laminate Type": " ".join([
            str(laminate_.get("material_type", "")),
            str(laminate_.get("brand", "")),
            str(laminate_.get("model", "")),
            str(laminate_.get("grade", "")),
            str(laminate_.get("thickness", ""))
        ]).strip(),
        "Total Sheets": round(total_sheets, 2),
        "Total Area (sft)": round(ta, 2),
        "Material Cost (₹)": round(el_total_cost, 2),
        "Cost per sft (₹)": round(cost_per_sft, 2),
        "Factory Binding (220+120 Install) (₹)": round(factory_binding, 2),
        "Carpenter (300) (₹)": round(carpenter, 2)
    })

    total_area += ta
    total_cost += el_total_cost

cursor.close()
conn.close()

# Add Back button to go to Materials page
if st.button("⬅️ Back to Materials"):
    st.switch_page("pages/02_MaterialSelection.py")

# --- Dashboard KPIs ---
st.title("Project Summary Dashboard")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_factory_binding = sum(e["Factory Binding (220+120 Install) (₹)"] for e in elements_data)
total_carpenter = sum(e["Carpenter (300) (₹)"] for e in elements_data)
total_with_factory = total_cost + total_factory_binding
total_with_carpenter = total_cost + total_carpenter

with kpi1:
    st.metric("Total Area (sft)", round(total_area, 2))
with kpi2:
    st.metric("Total Material Cost (₹)", round(total_cost, 2))
with kpi3:
    st.metric("Material Cost + Factory Binding (₹)", round(total_with_factory, 2))
with kpi4:
    st.metric("Material Cost + Carpenter (₹)", round(total_with_carpenter, 2))

# --- Elements Table with Group/Ungroup Option ---
st.markdown("### Element-wise Details")

group_by_room = st.toggle("Show Room-wise Details (Ungroup)", value=True)

df = pd.DataFrame(elements_data)

cols_order = [
    "Room", "Element", "Height", "Length", "Width", "No of Shelves",
    "Shutter Material", "Carcus Material", "Laminate Type",
    "Total Sheets", "Total Area (sft)", "Material Cost (₹)", "Cost per sft (₹)",
    "Factory Binding (220+120 Install) (₹)", "Carpenter (300) (₹)"
]
df = df[[col for col in cols_order if col in df.columns]]

df["Final Cost with Factory (₹)"] = df["Material Cost (₹)"] + df["Factory Binding (220+120 Install) (₹)"]
df["Final Cost with Carpentry (₹)"] = df["Material Cost (₹)"] + df["Carpenter (300) (₹)"]

cols_order = [
    "Room", "Element", "Height", "Length", "Width", "No of Shelves",
    "Shutter Material", "Carcus Material", "Laminate Type",
    "Total Sheets", "Total Area (sft)", "Material Cost (₹)", "Cost per sft (₹)",
    "Factory Binding (220+120 Install) (₹)", "Carpenter (300) (₹)",
    "Final Cost with Factory (₹)", "Final Cost with Carpentry (₹)"
]
df = df[[col for col in cols_order if col in df.columns]]

from st_aggrid import AgGrid, GridOptionsBuilder

def show_aggrid(df):
    gb = GridOptionsBuilder.from_dataframe(df)
    for col in df.columns:
        max_len = max(df[col].astype(str).map(len).max(), len(col))
        width = min(max(80, max_len * 10), 400)
        gb.configure_column(col, width=width)
    gb.configure_grid_options(domLayout='autoHeight')
    try:
        AgGrid(df, gridOptions=gb.build(), fit_columns_on_grid_load=True, height=400)
    except:
        st.dataframe(df, use_container_width=True, hide_index=True)

if group_by_room:
    grouped = (
    df.groupby("Room", as_index=False)
    .agg({
        "Shutter Material": "first",
        "Carcus Material": "first",
        "Laminate Type": "first",
        "Total Sheets": "sum",
        "Total Area (sft)": "sum",
        "Material Cost (₹)": "sum",
        "Cost per sft (₹)": "mean",
        "Factory Binding (220+120 Install) (₹)": "sum",
        "Carpenter (300) (₹)": "sum"
    })
    )
    grouped["Final Cost with Factory (₹)"] = grouped["Material Cost (₹)"] + grouped["Factory Binding (220+120 Install) (₹)"]
    grouped["Final Cost with Carpentry (₹)"] = grouped["Material Cost (₹)"] + grouped["Carpenter (300) (₹)"]

    # Ensure all object columns are strings for AgGrid compatibility
    for col in grouped.select_dtypes(include='object').columns:
        grouped[col] = grouped[col].astype(str)

    show_aggrid(grouped.drop(columns=["Factory Binding (220+120 Install) (₹)", "Carpenter (300) (₹)"], errors='ignore'))
else:
    # grouped = (
    #     df.groupby("Element", as_index=False)
    #     .agg({
    #         "Shutter Material": "first",
    #         "Carcus Material": "first",
    #         "Laminate Type": "first",
    #         "Total Sheets": "sum",
    #         "Total Area (sft)": "sum",
    #         "Material Cost (₹)": "sum",
    #         "Cost per sft (₹)": "mean",
    #         "Factory Binding (220+120 Install) (₹)": "sum",
    #         "Carpenter (300) (₹)": "sum"
    #     })
    # )
    # grouped["Final Cost with Factory (₹)"] = grouped["Material Cost (₹)"] + grouped["Factory Binding (220+120 Install) (₹)"]
    # grouped["Final Cost with Carpentry (₹)"] = grouped["Material Cost (₹)"] + grouped["Carpenter (300) (₹)"]

    # # Ensure all object columns are strings for AgGrid compatibility
    # for col in grouped.select_dtypes(include='object').columns:
    #     grouped[col] = grouped[col].astype(str)

    show_aggrid(df)

