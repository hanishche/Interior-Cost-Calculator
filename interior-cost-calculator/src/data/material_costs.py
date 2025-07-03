
import pandas as pd
import os

# Get the absolute path to the repo root
base_dir = os.path.dirname(os.path.abspath(__file__))
excel_path = os.path.join(base_dir, 'materials_cost.xlsx')

material_costs = pd.read_excel(excel_path, sheet_name='Plywood', engine='openpyxl')
material_costs_hdmr_mdf = pd.read_excel(excel_path, sheet_name='HDMR', engine='openpyxl')
material_costs_hdmr = material_costs_hdmr_mdf[material_costs_hdmr_mdf['Grade'] == 'HDHMR']
material_costs_mdf = material_costs_hdmr_mdf[material_costs_hdmr_mdf['Grade'] == 'MDF'].reset_index(drop=True)

laminate={"Laminate": {
        "Standard": {
            "1mm": 20
        },
        "Premium": {
            "1mm": 35
        },
        "Luxury": {
            "1mm": 60
        }
    }}
