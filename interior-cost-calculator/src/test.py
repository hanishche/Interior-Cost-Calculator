import dash
from dash import dash_table, html, dcc, Input, Output, State
import pandas as pd

# Load data
df = pd.read_csv(r"C:\Users\hchebr\Downloads\materials_cost.csv")  # Or read_csv()

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H3("📊 Excel-Like Editable Table"),
    dash_table.DataTable(
        id='editable-table',
        columns=[{"name": i, "id": i, "editable": True} for i in df.columns],
        data=df.to_dict('records'),
        editable=True,
        filter_action='native',
        sort_action='native',
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'}
    ),
    html.Br(),
    html.Button("Save Changes", id="save-btn", n_clicks=0),
    html.Div(id="save-status")
])

@app.callback(
    Output("save-status", "children"),
    Input("save-btn", "n_clicks"),
    State("editable-table", "data"),
    prevent_initial_call=True
)
def save_data(n_clicks, table_data):
    new_df = pd.DataFrame(table_data)
    new_df.to_excel("updated_data.xlsx", index=False)
    return f"✅ Data saved to updated_data.xlsx!"

if __name__ == '__main__':
    app.run(debug=True)
