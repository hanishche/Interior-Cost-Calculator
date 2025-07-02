
import pandas as pd
material_costs = pd.read_excel(r"C:\Users\hchebr\Downloads\materials_cost.xlsx",sheet_name='Plywood',engine='openpyxl')
material_costs_hdmr_mdf = pd.read_excel(r"C:\Users\hchebr\Downloads\materials_cost.xlsx", sheet_name='HDMR', engine='openpyxl')
material_costs_hdmr=material_costs_hdmr_mdf[material_costs_hdmr_mdf['Grade']=='HDHMR']
material_costs_mdf = material_costs_hdmr_mdf[material_costs_hdmr_mdf['Grade']=='MDF'].reset_index(drop=True)

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
print(material_costs_mdf)