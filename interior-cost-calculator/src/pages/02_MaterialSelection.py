import streamlit as st
import pandas as pd
from data.material_costs import material_costs, material_costs_hdmr, material_costs_mdf, laminate
from utils.calculations import shutter_area, side_area, top_bottom_area, back_panel_area, shelf_area
from utils.db import save_project, load_project

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

if st.button("⬅️ Previous"):
    st.switch_page("pages/01_ProjectInput.py")

if st.button("Next ➡️"):
    st.switch_page("pages/03_Summary.py")

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

# --- Load existing materials if present ---
existing_materials = project_data.get("element_materials", {})

st.title("Material Selection (Element-wise)")

material_type_map = {
    "Plywood": material_costs,
    "HDHMR": material_costs_hdmr,
    "MDF": material_costs_mdf
}
material_types = list(material_type_map.keys())

if "element_materials" not in st.session_state:
    st.session_state["element_materials"] = existing_materials.copy()
element_materials = st.session_state["element_materials"]

# --- Group/Ungroup Toggle ---
group_by_room = st.toggle("Show Room-wise Details (Ungroup)", value=True)

for room, elements in project_data.get("rooms", {}).items():
    with st.expander(f"Room: {room}", expanded=group_by_room):
        for el_name, el in elements.items():
            if el_name == "Bunk Bed" and isinstance(el, dict):
                for section_name, section in el.items():
                    with st.expander(f"{el_name} - {section_name}", expanded=True):
                        key_prefix = f"{room}|{el_name}|{section_name}"
                        st.markdown("**Material Selection**")
                        mat_labels = [("shutter", "Shutter"), ("carcus", "Carcus"), ("laminate", "Laminate")]
                        prop_labels = ["Type", "Grade", "Brand", "Model", "Thickness", "Price/sft"]
                        cols = st.columns(len(prop_labels))
                        for idx, (mat, mat_label) in enumerate(mat_labels):
                            if mat == "laminate":
                                laminate_type = cols[0].selectbox(
                                    f"{mat_label} Type",
                                    list(laminate["Laminate"].keys()),
                                    key=f"{key_prefix}_{mat}_type",
                                    index=list(laminate["Laminate"].keys()).index(
                                        element_materials.get(key_prefix, {}).get(mat, {}).get("type", list(laminate["Laminate"].keys())[0])
                                    ) if element_materials.get(key_prefix, {}).get(mat, {}).get("type", list(laminate["Laminate"].keys())[0]) in list(laminate["Laminate"].keys()) else 0
                                )
                                cols[1].markdown("-")
                                cols[2].markdown("-")
                                cols[3].markdown("-")
                                laminate_thickness = cols[4].selectbox(
                                    f"{mat_label} Thickness",
                                    list(laminate["Laminate"][laminate_type].keys()),
                                    key=f"{key_prefix}_{mat}_thickness",
                                    index=list(laminate["Laminate"][laminate_type].keys()).index(
                                        element_materials.get(key_prefix, {}).get(mat, {}).get("thickness", list(laminate["Laminate"][laminate_type].keys())[0])
                                    ) if element_materials.get(key_prefix, {}).get(mat, {}).get("thickness", list(laminate["Laminate"][laminate_type].keys())[0]) in list(laminate["Laminate"][laminate_type].keys()) else 0
                                )
                                laminate_rate = laminate["Laminate"][laminate_type][laminate_thickness]
                                cols[5].info(f"₹{laminate_rate}/sft")
                                element_materials.setdefault(key_prefix, {})[mat] = {
                                    "type": laminate_type,
                                    "thickness": laminate_thickness,
                                    "rate": laminate_rate
                                }
                                st.session_state["element_materials"] = element_materials
                            else:
                                mat_type = cols[0].selectbox(
                                    f"{mat_label} Type",
                                    material_types,
                                    key=f"{key_prefix}_{mat}_type",
                                    index=material_types.index(
                                        element_materials.get(key_prefix, {}).get(mat, {}).get("type", material_types[0])
                                    ) if element_materials.get(key_prefix, {}).get(mat, {}).get("type", material_types[0]) in material_types else 0
                                )
                                df = material_type_map[mat_type]
                                grades = df["Grade"].dropna().unique().tolist()
                                if not grades or (mat_type == "MDF" and (len(grades) == 1 and (grades[0] == "" or pd.isna(grades[0])))):
                                    grade = "-"
                                    cols[1].markdown("-")
                                else:
                                    grade = cols[1].selectbox(
                                        f"{mat_label} Grade",
                                        grades,
                                        key=f"{key_prefix}_{mat}_grade",
                                        index=grades.index(
                                            element_materials.get(key_prefix, {}).get(mat, {}).get("grade", grades[0])
                                        ) if element_materials.get(key_prefix, {}).get(mat, {}).get("grade", grades[0]) in grades else 0
                                    )
                                filtered_df = df[df["Grade"] == grade] if grade != "-" else df
                                brands = filtered_df["Brand"].dropna().unique().tolist()
                                if brands:
                                    brand = cols[2].selectbox(
                                        f"{mat_label} Brand",
                                        brands,
                                        key=f"{key_prefix}_{mat}_brand",
                                        index=brands.index(
                                            element_materials.get(key_prefix, {}).get(mat, {}).get("brand", brands[0])
                                        ) if element_materials.get(key_prefix, {}).get(mat, {}).get("brand", brands[0]) in brands else 0
                                    )
                                else:
                                    brand = "-"
                                    cols[2].markdown("-")
                                filtered_df = filtered_df[filtered_df["Brand"] == brand] if brand != "-" else filtered_df
                                models = filtered_df["Model"].dropna().unique().tolist()
                                if models:
                                    model = cols[3].selectbox(
                                        f"{mat_label} Model",
                                        models,
                                        key=f"{key_prefix}_{mat}_model",
                                        index=models.index(
                                            element_materials.get(key_prefix, {}).get(mat, {}).get("model", models[0])
                                        ) if element_materials.get(key_prefix, {}).get(mat, {}).get("model", models[0]) in models else 0
                                    )
                                else:
                                    model = "-"
                                    cols[3].markdown("-")
                                filtered_df = filtered_df[filtered_df["Model"] == model] if model != "-" else filtered_df
                                thicknesses = filtered_df["Thickness"].dropna().unique().tolist()
                                if thicknesses:
                                    thickness = cols[4].selectbox(
                                        f"{mat_label} Thickness",
                                        thicknesses,
                                        key=f"{key_prefix}_{mat}_thickness",
                                        index=thicknesses.index(
                                            element_materials.get(key_prefix, {}).get(mat, {}).get("thickness", thicknesses[0])
                                        ) if element_materials.get(key_prefix, {}).get(mat, {}).get("thickness", thicknesses[0]) in thicknesses else 0
                                    )
                                else:
                                    thickness = "-"
                                    cols[4].markdown("-")
                                filtered_df = filtered_df[filtered_df["Thickness"] == thickness] if thickness != "-" else filtered_df
                                if not filtered_df.empty and "Per sft Price" in filtered_df.columns:
                                    per_sft_price = float(filtered_df.iloc[0]["Per sft Price"])
                                    cols[5].info(f"₹{per_sft_price}/sft")
                                else:
                                    per_sft_price = 0
                                    cols[5].warning("No price found")
                                element_materials.setdefault(key_prefix, {})[mat] = {
                                    "type": mat_type,
                                    "grade": grade,
                                    "brand": brand,
                                    "model": model,
                                    "thickness": thickness,
                                    "rate": per_sft_price
                                }
                                st.session_state["element_materials"] = element_materials
            else:
                with st.expander(f"{el_name}", expanded=True):
                    key_prefix = f"{room}|{el_name}"
                    mat_labels = [("shutter", "Shutter"), ("carcus", "Carcus"), ("laminate", "Laminate")]
                    prop_labels = ["Type", "Grade", "Brand", "Model", "Thickness", "Price/sft"]
                    cols = st.columns(len(prop_labels))
                    for idx, (mat, mat_label) in enumerate(mat_labels):
                        if mat == "laminate":
                            laminate_type = cols[0].selectbox(
                                f"{mat_label} Type",
                                list(laminate["Laminate"].keys()),
                                key=f"{key_prefix}_{mat}_type",
                                index=list(laminate["Laminate"].keys()).index(
                                    element_materials.get(key_prefix, {}).get(mat, {}).get("type", list(laminate["Laminate"].keys())[0])
                                ) if element_materials.get(key_prefix, {}).get(mat, {}).get("type", list(laminate["Laminate"].keys())[0]) in list(laminate["Laminate"].keys()) else 0
                            )
                            cols[1].markdown("-")
                            cols[2].markdown("-")
                            cols[3].markdown("-")
                            laminate_thickness = cols[4].selectbox(
                                f"{mat_label} Thickness",
                                list(laminate["Laminate"][laminate_type].keys()),
                                key=f"{key_prefix}_{mat}_thickness",
                                index=list(laminate["Laminate"][laminate_type].keys()).index(
                                    element_materials.get(key_prefix, {}).get(mat, {}).get("thickness", list(laminate["Laminate"][laminate_type].keys())[0])
                                ) if element_materials.get(key_prefix, {}).get(mat, {}).get("thickness", list(laminate["Laminate"][laminate_type].keys())[0]) in list(laminate["Laminate"][laminate_type].keys()) else 0
                            )
                            laminate_rate = laminate["Laminate"][laminate_type][laminate_thickness]
                            cols[5].info(f"₹{laminate_rate}/sft")
                            element_materials.setdefault(key_prefix, {})[mat] = {
                                "type": laminate_type,
                                "thickness": laminate_thickness,
                                "rate": laminate_rate
                            }
                            st.session_state["element_materials"] = element_materials
                        else:
                            mat_type = cols[0].selectbox(
                                f"{mat_label} Type",
                                material_types,
                                key=f"{key_prefix}_{mat}_type",
                                index=material_types.index(
                                    element_materials.get(key_prefix, {}).get(mat, {}).get("type", material_types[0])
                                ) if element_materials.get(key_prefix, {}).get(mat, {}).get("type", material_types[0]) in material_types else 0
                            )
                            df = material_type_map[mat_type]
                            grades = df["Grade"].dropna().unique().tolist()
                            if not grades or (mat_type == "MDF" and (len(grades) == 1 and (grades[0] == "" or pd.isna(grades[0])))):
                                grade = "-"
                                cols[1].markdown("-")
                            else:
                                grade = cols[1].selectbox(
                                    f"{mat_label} Grade",
                                    grades,
                                    key=f"{key_prefix}_{mat}_grade",
                                    index=grades.index(
                                        element_materials.get(key_prefix, {}).get(mat, {}).get("grade", grades[0])
                                    ) if element_materials.get(key_prefix, {}).get(mat, {}).get("grade", grades[0]) in grades else 0
                                )
                            filtered_df = df[df["Grade"] == grade] if grade != "-" else df
                            brands = filtered_df["Brand"].dropna().unique().tolist()
                            if brands:
                                brand = cols[2].selectbox(
                                    f"{mat_label} Brand",
                                    brands,
                                    key=f"{key_prefix}_{mat}_brand",
                                    index=brands.index(
                                        element_materials.get(key_prefix, {}).get(mat, {}).get("brand", brands[0])
                                    ) if element_materials.get(key_prefix, {}).get(mat, {}).get("brand", brands[0]) in brands else 0
                                )
                            else:
                                brand = "-"
                                cols[2].markdown("-")
                            filtered_df = filtered_df[filtered_df["Brand"] == brand] if brand != "-" else filtered_df
                            models = filtered_df["Model"].dropna().unique().tolist()
                            if models:
                                model = cols[3].selectbox(
                                    f"{mat_label} Model",
                                    models,
                                    key=f"{key_prefix}_{mat}_model",
                                    index=models.index(
                                        element_materials.get(key_prefix, {}).get(mat, {}).get("model", models[0])
                                    ) if element_materials.get(key_prefix, {}).get(mat, {}).get("model", models[0]) in models else 0
                                )
                            else:
                                model = "-"
                                cols[3].markdown("-")
                            filtered_df = filtered_df[filtered_df["Model"] == model] if model != "-" else filtered_df
                            thicknesses = filtered_df["Thickness"].dropna().unique().tolist()
                            if thicknesses:
                                thickness = cols[4].selectbox(
                                    f"{mat_label} Thickness",
                                    thicknesses,
                                    key=f"{key_prefix}_{mat}_thickness",
                                    index=thicknesses.index(
                                        element_materials.get(key_prefix, {}).get(mat, {}).get("thickness", thicknesses[0])
                                    ) if element_materials.get(key_prefix, {}).get(mat, {}).get("thickness", thicknesses[0]) in thicknesses else 0
                                )
                            else:
                                thickness = "-"
                                cols[4].markdown("-")
                            filtered_df = filtered_df[filtered_df["Thickness"] == thickness] if thickness != "-" else filtered_df
                            if not filtered_df.empty and "Per sft Price" in filtered_df.columns:
                                per_sft_price = float(filtered_df.iloc[0]["Per sft Price"])
                                cols[5].info(f"₹{per_sft_price}/sft")
                            else:
                                per_sft_price = 0
                                cols[5].warning("No price found")
                            element_materials.setdefault(key_prefix, {})[mat] = {
                                "type": mat_type,
                                "grade": grade,
                                "brand": brand,
                                "model": model,
                                "thickness": thickness,
                                "rate": per_sft_price
                            }
                            st.session_state["element_materials"] = element_materials

# --- Save per-element materials to JSON only when user clicks Save ---
st.markdown("---")
if st.button("Save Materials"):
    project_data["element_materials"] = st.session_state["element_materials"]
    save_project(user, project, project_data)
    st.success("Materials saved successfully!")

# --- Calculate total areas and costs ---
total_shutter_area = 0
total_carcus_area = 0
total_laminate_area = 0
total_shutter_cost = 0
total_carcus_cost = 0
total_laminate_cost = 0
elements_cost_breakup = []

for room, elements in project_data.get("rooms", {}).items():
    for el_name, el in elements.items():
        if el_name == "Bunk Bed" and isinstance(el, dict):
            for section_name, section in el.items():
                key_prefix = f"{room}|{el_name}|{section_name}"
                mat_data = element_materials.get(key_prefix, {})
                h = section.get("height", 0)
                l = section.get("length", 0)
                w = section.get("width", 0)
                shelves = section.get("num_shelves", 0)
                shutter_area_val = shutter_area(h, l)
                carcus_area_val = side_area(w, h) + top_bottom_area(l, w) + back_panel_area(h, l) + shelf_area(shelves, w, l)
                laminate_area_val = shutter_area_val + carcus_area_val
                shutter_cost = shutter_area_val * mat_data.get("shutter", {}).get("rate", 0)
                carcus_cost = carcus_area_val * mat_data.get("carcus", {}).get("rate", 0)
                laminate_cost = laminate_area_val * mat_data.get("laminate", {}).get("rate", 0)
                total_shutter_area += shutter_area_val
                total_carcus_area += carcus_area_val
                total_laminate_area += laminate_area_val
                total_shutter_cost += shutter_cost
                total_carcus_cost += carcus_cost
                total_laminate_cost += laminate_cost
                elements_cost_breakup.append({
                    "Room": room,
                    "Element": f"{el_name} - {section_name}",
                    "Shutter Area": shutter_area_val,
                    "Carcus Area": carcus_area_val,
                    "Laminate Area": laminate_area_val,
                    "Shutter Cost": shutter_cost,
                    "Carcus Cost": carcus_cost,
                    "Laminate Cost": laminate_cost
                })
        else:
            key_prefix = f"{room}|{el_name}"
            mat_data = element_materials.get(key_prefix, {})
            h = el.get("height", 0)
            l = el.get("length", 0)
            w = el.get("width", 0)
            shelves = el.get("num_shelves", 0)
            shutter_area_val = shutter_area(h, l)
            carcus_area_val = side_area(w, h) + top_bottom_area(l, w) + back_panel_area(h, l) + shelf_area(shelves, w, l)
            laminate_area_val = shutter_area_val + carcus_area_val
            shutter_cost = shutter_area_val * mat_data.get("shutter", {}).get("rate", 0)
            carcus_cost = carcus_area_val * mat_data.get("carcus", {}).get("rate", 0)
            laminate_cost = laminate_area_val * mat_data.get("laminate", {}).get("rate", 0)
            total_shutter_area += shutter_area_val
            total_carcus_area += carcus_area_val
            total_laminate_area += laminate_area_val
            total_shutter_cost += shutter_cost
            total_carcus_cost += carcus_cost
            total_laminate_cost += laminate_cost
            elements_cost_breakup.append({
                "Room": room,
                "Element": el_name,
                "Shutter Area": shutter_area_val,
                "Carcus Area": carcus_area_val,
                "Laminate Area": laminate_area_val,
                "Shutter Cost": shutter_cost,
                "Carcus Cost": carcus_cost,
                "Laminate Cost": laminate_cost
            })

# --- Cost Summary Side by Side ---
st.markdown("### Cost Summary")
cost1, cost2, cost3, cost4 = st.columns(4)
with cost1:
    st.metric("Total Shutter Area (sq.ft)", round(total_shutter_area, 2))
    st.metric("Shutter Cost (₹)", round(total_shutter_cost, 2))
with cost2:
    st.metric("Total Carcus Area (sq.ft)", round(total_carcus_area, 2))
    st.metric("Carcus Cost (₹)", round(total_carcus_cost, 2))
with cost3:
    st.metric("Total Laminate Area (sq.ft)", round(total_laminate_area, 2))
    st.metric("Laminate Cost (₹)", round(total_laminate_cost, 2))
with cost4:
    st.metric("Grand Total (₹)", round(total_shutter_cost + total_carcus_cost + total_laminate_cost, 2))

st.markdown("### Element-wise Cost Breakup")
df_breakup = pd.DataFrame(elements_cost_breakup)
if not df_breakup.empty:
    st.dataframe(
        df_breakup[
            [
                "Room", "Element",
                "Shutter Area", "Carcus Area", "Laminate Area",
                "Shutter Cost", "Carcus Cost", "Laminate Cost"
            ] + [col for col in df_breakup.columns if col not in [
                "Room", "Element", "Shutter Area", "Carcus Area", "Laminate Area",
                "Shutter Cost", "Carcus Cost", "Laminate Cost"
            ]]
        ],
        use_container_width=True
    )
else:
    st.info("No element-wise cost breakup to display.")

st.markdown("---")
if st.button("Next: Go to Summary"):
    st.switch_page("pages/03_Summary.py")