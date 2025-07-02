import streamlit as st
import os
import json
import pandas as pd

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
    
if st.button("✏️ Edit Project"):
    st.session_state["edit_mode"] = True
    st.switch_page("pages/01_ProjectInput.py")

# Load project data
user = st.session_state.get("username")  # <-- use "username" not "user"
project = st.session_state.get("project")
if not user or not project:
    st.error("User or project not found. Please login and select a project.")
    st.stop()

project_file = os.path.join("projects", user, f"{project}.json")
if not os.path.exists(project_file):
    st.error("Project file not found.")
    st.stop()

with open(project_file, "r") as f:
    project_data = json.load(f)

materials = project_data.get("materials", {})
rooms = project_data.get("rooms", {})
area_details = project_data.get("area_details", {})

# Prepare summary data
elements_data = []
total_area = 0
total_cost = 0

for room, elements in rooms.items():
    for el_name, el in elements.items():
        # --- Handle Bunk Bed Sections ---
        if el_name == "Bunk Bed" and isinstance(el, dict):
            for section_name, section in el.items():
                area_info = area_details.get(room, {}).get(el_name, {}).get(section_name, {})
                if not area_info:
                    sa = sda = tba = bpa = sha = ta = 0
                else:
                    sa = area_info.get("shutter_area", 0)
                    sda = area_info.get("side_area", 0)
                    tba = area_info.get("top_bottom_area", 0)
                    bpa = area_info.get("back_panel_area", 0)
                    sha = area_info.get("shelf_area", 0)
                    ta = area_info.get("total_area", 0)

                shutter_rate = materials.get("shutter", {}).get("rate", 0)
                carcus_rate = materials.get("carcus", {}).get("rate", 0)
                laminate_rate = materials.get("laminate", {}).get("rate", 0)

                shutter_cost = sa * shutter_rate
                carcus_cost = (sda + tba + bpa + sha) * carcus_rate
                laminate_cost = sa * laminate_rate
                el_total_cost = shutter_cost + carcus_cost + laminate_cost

                cost_per_sft = el_total_cost / ta if ta else 0

                length = section.get("length", 0)
                height = section.get("height", 0)
                factory_binding = 340 * length * height
                carpenter = 300 * length * height

                elements_data.append({
                    "Room": room,
                    "Element": f"{el_name} - {section_name}",
                    "Height": height,
                    "Length": length,
                    "Width": section.get("width", 0),
                    "No of Shelves": section.get("num_shelves", 0),
                    "Shutter Material": materials.get("shutter", {}).get("brand", ""),
                    "Carcus Material": materials.get("carcus", {}).get("brand", ""),
                    "Laminate Type": materials.get("laminate", {}).get("type", ""),
                    "Total Area (sft)": round(ta, 2),
                    "Total Cost (₹)": round(el_total_cost, 2),
                    "Cost per sft (₹)": round(cost_per_sft, 2),
                    "Factory Binding (220+120 Install) (₹)": round(factory_binding, 2),
                    "Carpenter (300) (₹)": round(carpenter, 2)
                })

                total_area += ta
                total_cost += el_total_cost
        else:
            # --- Normal elements ---
            area_info = area_details.get(room, {}).get(el_name, {})
            if not area_info:
                sa = sda = tba = bpa = sha = ta = 0
            else:
                sa = area_info.get("shutter_area", 0)
                sda = area_info.get("side_area", 0)
                tba = area_info.get("top_bottom_area", 0)
                bpa = area_info.get("back_panel_area", 0)
                sha = area_info.get("shelf_area", 0)
                ta = area_info.get("total_area", 0)

            shutter_rate = materials.get("shutter", {}).get("rate", 0)
            carcus_rate = materials.get("carcus", {}).get("rate", 0)
            laminate_rate = materials.get("laminate", {}).get("rate", 0)

            shutter_cost = sa * shutter_rate
            carcus_cost = (sda + tba + bpa + sha) * carcus_rate
            laminate_cost = sa * laminate_rate
            el_total_cost = shutter_cost + carcus_cost + laminate_cost

            cost_per_sft = el_total_cost / ta if ta else 0

            length = el.get("length", 0)
            height = el.get("height", 0)
            factory_binding = 340 * length * height
            carpenter = 300 * length * height

            elements_data.append({
                "Room": room,
                "Element": el_name,
                "Height": height,
                "Length": length,
                "Width": el.get("width", 0),
                "No of Shelves": el.get("num_shelves", 0),
                "Shutter Material": materials.get("shutter", {}).get("brand", ""),
                "Carcus Material": materials.get("carcus", {}).get("brand", ""),
                "Laminate Type": materials.get("laminate", {}).get("type", ""),
                "Total Area (sft)": round(ta, 2),
                "Total Cost (₹)": round(el_total_cost, 2),
                "Cost per sft (₹)": round(cost_per_sft, 2),
                "Factory Binding (220+120 Install) (₹)": round(factory_binding, 2),
                "Carpenter (300) (₹)": round(carpenter, 2)
            })

            total_area += ta
            total_cost += el_total_cost

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
    st.metric("Total Project Cost (₹)", round(total_cost, 2))
with kpi3:
    st.metric("Total Cost + Factory Binding (₹)", round(total_with_factory, 2))
with kpi4:
    st.metric("Total Cost + Carpenter (₹)", round(total_with_carpenter, 2))

# --- Elements Table with Group/Ungroup Option ---
st.markdown("### Element-wise Details")

group_by_room = st.toggle("Show Room-wise Details (Ungroup)", value=True)

df = pd.DataFrame(elements_data)

if group_by_room:
    # Show full details (room + element)
    st.dataframe(df, use_container_width=True)
else:
    # Group by Element (ignore room), sum numeric columns, show representative material columns
    group_cols = [
        "Element",
        "Shutter Material", "Carcus Material", "Laminate Type"
    ]
    sum_cols = [
        "Height", "Length", "Width", "No of Shelves",
        "Total Area (sft)", "Total Cost (₹)", "Cost per sft (₹)",
        "Factory Binding (220+120 Install) (₹)", "Carpenter (300) (₹)"
    ]
    # For material columns, take the first non-null value per group
    grouped = (
        df.groupby("Element", as_index=False)
        .agg({
            "Shutter Material": "first",
            "Carcus Material": "first",
            "Laminate Type": "first",
            "Total Area (sft)": "sum",
            "Total Cost (₹)": "sum",
            "Cost per sft (₹)": "mean",
            "Factory Binding (220+120 Install) (₹)": "sum",
            "Carpenter (300) (₹)": "sum"
        })
    )
    # Add final cost columns
    grouped["Final Cost with Factory (₹)"] = grouped["Total Cost (₹)"] + grouped["Factory Binding (220+120 Install) (₹)"]
    grouped["Final Cost with Carpentry (₹)"] = grouped["Total Cost (₹)"] + grouped["Carpenter (300) (₹)"]
    st.dataframe(grouped, use_container_width=True)