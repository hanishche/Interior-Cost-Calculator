import streamlit as st
import pandas as pd
import numpy as np
from utils.db import load_project


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

# Load project data from JSON
user = st.session_state.get("username")
project = st.session_state.get("project")
if not user or not project:
    st.error("User or project not found. Please login and select a project.")
    st.stop()

project_data = load_project(user, project)
if not project_data:
    st.error("Project data not found.")
    st.stop()

element_materials = project_data.get("element_materials", {})
rooms = project_data.get("rooms", {})
area_details = project_data.get("area_details", {})

elements_data = []
total_area = 0
total_cost = 0

for room, elements in rooms.items():
    for el_name, el in elements.items():
        # Handle Bunk Bed sections
        if el_name == "Bunk Bed" and isinstance(el, dict):
            for section_name, section in el.items():
                key_prefix = f"{room}|{el_name}|{section_name}"
                area_info = area_details.get(room, {}).get(el_name, {}).get(section_name, {})
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
                laminate_cost = ta * laminate_rate
                el_total_cost = shutter_cost + carcus_cost + laminate_cost

                cost_per_sft = el_total_cost / ta if ta else 0

                factory_binding = 340 * section.get("length", 0) * section.get("height", 0)
                carpenter = 300 * section.get("length", 0) * section.get("height", 0)

                SHEET_SQFT = 32
                total_sheets = ta / SHEET_SQFT if SHEET_SQFT else 0

                elements_data.append({
                    "Room": room,
                    "Element": f"{el_name} - {section_name}",
                    "Height": section.get("height", 0),
                    "Length": section.get("length", 0),
                    "Width": section.get("width", 0),
                    "No of Shelves": section.get("num_shelves", 0),
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
        else:
            key_prefix = f"{room}|{el_name}"
            area_info = area_details.get(room, {}).get(el_name, {})
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
            laminate_cost = ta * laminate_rate
            el_total_cost = shutter_cost + carcus_cost + laminate_cost

            cost_per_sft = el_total_cost / ta if ta else 0

            factory_binding = 340 * el.get("length", 0) * el.get("height", 0)
            carpenter = 300 * el.get("length", 0) * el.get("height", 0)

            SHEET_SQFT = 32
            total_sheets = ta / SHEET_SQFT if SHEET_SQFT else 0

            elements_data.append({
                "Room": room,
                "Element": el_name,
                "Height": el.get("height", 0),
                "Length": el.get("length", 0),
                "Width": el.get("width", 0),
                "No of Shelves": el.get("num_shelves", 0),
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

def add_total_row(dataframe, label="Total"):
    if dataframe.empty:
        return dataframe
    total_row = {}
    for col in dataframe.columns:
        if dataframe[col].dtype in [np.float64, np.int64, float, int]:
            total_row[col] = dataframe[col].sum()
        else:
            total_row[col] = label if col in ["Room", "Element"] else ""
    return pd.concat([dataframe, pd.DataFrame([total_row])], ignore_index=True)

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

    # Add total row to grouped table
    grouped_with_total = add_total_row(grouped, label="Total")
    show_aggrid(grouped_with_total.drop(columns=["Factory Binding (220+120 Install) (₹)", "Carpenter (300) (₹)"], errors='ignore'))
else:
    # Add total row to summary df
    df_with_total = add_total_row(df, label="Total")
    show_aggrid(df_with_total)
