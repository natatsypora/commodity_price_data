# https://dashaggridexamples.pythonanywhere.com/tooltips
from dash import Dash, html, Input, Output, dcc, no_update, ctx, State
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from cmo_function import *


pd.set_option('future.no_silent_downcasting', True)

# List of commodities indexed by group
Indices = ['Energy', 'Beverages', 'Oils and Meals', 'Grains', 'Other Food', 'Timber', 'Other Raw Materials', 'Fertilizers', 'Metals and Minerals', 'Precious Metals']

# Define url for data
url = "https://raw.githubusercontent.com/plotly/Figure-Friday/refs/heads/main/2024/week-50/CMO-Historical-Data-Monthly.csv"


#Data preprocessing================================================================
def read_and_clean_data(url):
    # Read data
    data = pd.read_csv(url)
    # Remove a few columns with empty values
    removelist = ['Barley', 'Sorghum', 'Shrimps, Mexican', 'Phosphate rock']
    data = data.drop(removelist, errors = 'ignore', axis = 1)
    # Remove special character from column names    
    data.columns = [col.strip(' **').replace('.', '') for col in data.columns]

    # Get unit of measurement for each commodity
    commodity_unit_of_measurement = data[:1].T.to_dict(orient='dict')[0]
    commodity_unit_of_measurement.pop('Unnamed: 0')
    # Clean unit of measurement
    unit = {}
    for k, v in commodity_unit_of_measurement.items():          
        val = v.strip('()').replace('$/cubic meter', '$/cum',).replace('$/troy oz', '$/toz').replace('cents/sheet', '¢/sheets')       
        unit[k] = val
    
    # Drop first two rows
    df = data.drop([0, 1])  
   
    # Convert all values to numeric in columns starting from the second one
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col], errors='coerce').ffill()

    # Rename first column and convert to datetime
    df = df.rename(columns={'Unnamed: 0': 'Date'})
    df['Date'] = pd.to_datetime(df['Date'], format='%YM%m')
    # Add year and formatted month columns 
    df['month_3'] = df['Date'].dt.strftime('%b')
    df['year'] = df['Date'].dt.year
    # Reorder months
    month_order_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    df['month_3'] = df['month_3'].astype("category").cat.set_categories(month_order_list, ordered=True) 

    # Filter data by selected years (2010-2024)
    df = df[df['year'] >= 2010].reset_index(drop=True)
   
    return df, unit

# Get data and unit
df_2010_2024, unit = read_and_clean_data(url)
df_for_table = df_2010_2024.iloc[-13:, :-2].copy()


def get_commodity_group(dff, indices):
    # Get commodity groups for each index    
    energy_cols = dff.columns[1:11].tolist()
    beverages_cols = dff.columns[11:18].tolist()
    oils_meals = dff.columns[18:29].tolist()
    grains = dff.columns[29:36].tolist()
    other_food = dff.columns[36:46].tolist()
    timber_cols = dff.columns[46:51].tolist()
    other_raw_cols = dff.columns[51:54].tolist()
    fertilizers_cols = dff.columns[54:58].tolist()
    metals_cols = dff.columns[58:65].tolist()
    precious_metals_cols = dff.columns[65:68].tolist()
    # Create a list of all groups
    all_groups = [energy_cols, beverages_cols, oils_meals, grains, other_food, timber_cols, 
                  other_raw_cols, fertilizers_cols, metals_cols, precious_metals_cols]
    # Create a dictionary with index as key and group as value
    commodity_groups = {}
    for i, g in zip(indices, all_groups):
        commodity_groups[i] = g

    return commodity_groups

# Get commodity groups
commodity_groups = get_commodity_group(df_2010_2024, Indices)


def melt_data(dff):  
    # Use melt to reshape the data 
    dfp = (pd.melt(
        dff, 
        id_vars=['Date'], 
        var_name='Product', 
        value_name='Price')
        .sort_values(by=['Product','Date'], ascending=[True, True])
        ) 
    
    #add price previous month and price previous year
    dfp['Price'] = dfp['Price'].astype(float)
    dfp['Price pm'] = dfp['Price'].shift(1).astype(float)
    dfp['Price py'] = dfp['Price'].shift(12).astype(float)
    
    #add YoY and MoM changes
    dfp['MoM change'] = dfp['Price'].pct_change().astype(float)
    dfp['YoY change'] = dfp['Price'].pct_change(12).astype(float)    
   
    return dfp

# Get melted data
df_melt  = melt_data(df_for_table)


# Get datafreame with graph for ag-grid table
dfgrid = create_sparkline(df_melt)
# Add column with unit of measurement
dfgrid['Unit'] = dfgrid['Product'].map(unit)   


# Create app object=================================================================
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, 
                                           dbc.icons.FONT_AWESOME,
                                          'assets/style.css'])
#===================================================================================

#Create component===================================================================

# Create ag-grid table--------------------------------------------------------------
# Define columns headers to show in ag-grid 
maxmonth = dfgrid['Date'].max()
lastmonth_label = maxmonth.strftime('%b %Y')
prevmonth_label = (maxmonth + pd.DateOffset(months=-1)).strftime('%b %Y')
prevyear_label = (maxmonth + pd.DateOffset(years=-1)).strftime('%b %Y')

# Conditional formatting
sellstyle_condition = {   
            # Set of rules           
            "styleConditions": [
                {"condition": "params.value > 0", "style": {"color": "green"}},
                {"condition": "params.value < 0", "style": {"color": "crimson"}, 
                }],
             # Default style if no rules apply  
            "defaultStyle": {"color": "black"}}

# Column definitions for ag-grid
columnDefs = [    
    {"headerName": "Commodity", "field": "Product", "minWidth": 160, 
     'type': 'leftAligned', "headerClass": "header-medium", 'tooltipField': "Product",
     'headerTooltip': "To view historical data, click on the cell with the Commodity name."},

    {"headerName": "Unit", "field": "Unit", "minWidth": 100, 'type': 'leftAligned', "headerClass": "header-medium"},

    # Header with subheaders
    {'headerName': 'Average Price', 
     "children": [           
         {"headerName": lastmonth_label,          
          "field": "Price",
          "valueFormatter": {"function": "d3.format(',.2f')(params.value)"}},
         {"headerName": prevmonth_label ,         
          "field": "Price pm",
          "valueFormatter": {"function": "d3.format(',.2f')(params.value)"}},
         {"headerName": prevyear_label,           
          "field": "Price py",
          "valueFormatter": {"function": "d3.format(',.2f')(params.value)"}},
          ]},

    # Header with subheaders and conditional formatting
    {'headerName': 'Percent Change',  
     "children": [  
        {"headerName": "PM",        
        "field": "MoM change", "minWidth": 85,
        'headerTooltip': "Previous Month", 
        "tooltipValueGetter": {
        "function": "'Price of ' + params.data.Product + ' changes vs PM in ' \
            + d3.format(',.2f')(params.data.Price - params.data['Price pm']) + '$'"}, 
        "valueFormatter": {"function": "d3.format('.1%')(params.value)"},
        'cellStyle': sellstyle_condition},

        {"headerName": "PY",        
        "field": "YoY change", "minWidth": 85,
        'headerTooltip': "Previous Year",        
        "tooltipValueGetter": {
            "function": "'Price of ' + params.data.Product + ' changes vs PY in ' \
                + d3.format(',.2f')(params.data.Price - params.data['Price py']) + '$'"},       
        "valueFormatter": {"function": "d3.format('.1%')(params.value)"},  
        'cellStyle': sellstyle_condition }
     ]},  
        
    # Fild with graphs
    {'headerName': 'Price Trend', 
     "children": [   
        {"field": "graph",
         "cellRenderer": "DCC_GraphClickData",
         "headerName": f"{prevyear_label} - {lastmonth_label}",     
         "filter": False, 'sortable': False,
         "maxWidth": 300,
         "minWidth": 200}
    ]}
]

# Set default column properties"
defaultColDef = {"resizable": True, "sortable": True, "filter": True, "minWidth": 112, 'type': 'rightAligned'}
# Set default table properties
dashGridOptions={"rowHeight": 49, "animateRows": False,  "pagination": True, "paginationPageSize": 20,  "tooltipShowDelay":0}

# Create ag-grid table
aggrid_table = dag.AgGrid(
    id="ag-grid-with-graph",
    columnDefs=columnDefs,
    rowData=dfgrid.to_dict("records"),
    columnSize="sizeToFit",                    
    className="ag-theme-alpine",
    rowStyle={"backgroundColor": "rgba(255,255,255,1)"},
    defaultColDef=defaultColDef,                                        
    dashGridOptions=dashGridOptions,                                     
    style={"height": "794px"})                


# Define unit abbreviations 
content_abbreviations = dcc.Markdown('''
                    - **$** = US dollar  
                    - **bbl** = barrel  
                    - **cum** = cubic meter  
                    - **dmt** = dry metric ton  
                    - **kg** = kilogram  
                    - **mmbtu** = million British thermal units  
                    - **mt** = metric ton  
                    - **toz** = troy oz  
                    - **¢/sheets** = cents per sheet''',
                     style={'font-size': '14px', 'color': 'dimgray'})


# Create dropdown for unit abbreviations(desebled)
dropdown_abreviations = dbc.DropdownMenu(
    label="Abbreviations of Units",
    children=dbc.DropdownMenuItem(content_abbreviations, disabled=True), 
    class_name='my-3', 
    toggle_style={'background': '#8FBBD9', 'border': '1px solid #8FBBD9'} )


# Create modal with line and area graphs
modal_with_graph = dbc.Modal([ 
    dbc.ModalBody([
        dcc.Graph(id='area-fillgradient-graph', figure={}, config=config_dict),
        dcc.Graph(id='line-prc-change-graph', figure={}, config=config_dict, className='mt-4')]),
    dbc.ModalFooter(dbc.Button("Close", id="close-modal-button", 
                               n_clicks=0, class_name='ms-auto btn-secondary'), 
                    className='p-0'),
        ],
        id="modal-with-graph",
        size="xl",
        centered=True,
        is_open=False)

# Create accordion with commodity groups
accordion_with_commodity_groups = dbc.Accordion(
        children=[
            dbc.AccordionItem(
                title=index,
                children=[
                    html.Ul([html.Li(
                        dbc.Button(commodity, id=f'{index}-{commodity}', 
                                   n_clicks=0, color='link', 
                                   className='btn-link text-decoration-none p-0', 
                                   style={'color': 'dimgray'})) for commodity in commodities])
                ]) for index, commodities in commodity_groups.items()
        ], start_collapsed=False) 


# Create modal with graph for commodity group 
modal_commodity_group_graph = dbc.Modal([            
            dbc.ModalBody(dcc.Graph(id="modal-commodity-group-graph", config=config_dict)),
            dbc.ModalFooter([
                html.Label('• To add a line for comparison, click on the corresponding item in the legend.', className='ms-5'),
                dbc.Button("Close", id="close-modal-commodity-group", className="ms-auto btn-secondary", n_clicks=0)], className='p-0'),
        ],
        id="commodity-group-modal",
        size="xl",
        centered=True,
        is_open=False)


# Create text for tooltip    
text_commodities = html.Label("To view historical data, click on the cell with the Product name in the 'Commodity' column or select from the list below.")


# Create dropdown menu for sources                             
dropdown_sources = dbc.DropdownMenu(
    label="Sources",
    children=[
        dbc.DropdownMenuItem('World Bank Group', href='https://www.worldbank.org/en/research/commodity-markets#1',
                             target='_blank ', style={'color': 'dimgray'}),
        dbc.DropdownMenuItem(divider=True),
        dbc.DropdownMenuItem('Figure Friday 2024-week 50', href='https://community.plotly.com/t/figure-friday-2024-week-50/89366/1', 
                             target='_blank ', style={'color': 'dimgray'}),
        dbc.DropdownMenuItem('Plotly Library for Python', href='https://plotly.com/python/', target='_blank ', style={'color': 'dimgray'}),
        dbc.DropdownMenuItem('Plotly Dash', href='https://dash.plotly.com/', target='_blank ', style={'color': 'dimgray'}),
        dbc.DropdownMenuItem(divider=True),
        dbc.DropdownMenuItem('GitHub Repository', href='https://github.com/natatsypora/commodity_price_index', 
                             target='_blank ', style={'color': 'dimgray'}),
        ],                                
    class_name='my-3', 
    toggle_style={'background': '#8FBBD9', 'border': '1px solid #8FBBD9'} )


# Create app layout==============================================================
app.layout = dbc.Container([
    # Header
        dbc.Row([ 
            dbc.Col([
                html.Img(src="/assets/cmo_2.png", alt="Commodities image", id='commodities-image', style={'height': '70px'}),
                dbc.Tooltip(text_commodities, target="commodities-image", placement='bottom', style={'color': 'lightgrey'}) ], 
                width=3, className='d-flex justify-content-center'),             
            dbc.Col(html.H2('World Bank Commodity Price Data',
                            className='text-center my-3', 
                            style={'color': 'rgba(31,119,180,0.8)'}),
                    width=8, className='text-center'), 
            dbc.Col(dropdown_sources,  width=1, className='d-flex align-items-center justify-content-center')                             
            ], class_name='mb-4 border-bottom bg-light'), 
    # Body               
        dbc.Row([
            dbc.Col(html.Div(accordion_with_commodity_groups), width=3 ),
            dbc.Col([
                aggrid_table, 
                html.Div([
                    dropdown_abreviations,
                    dbc.Button('Reset Table Filters', id='reset-filters-button', n_clicks=0, class_name='btn-secondary'),
                    dbc.Button('Download CSV', id='download-button', n_clicks=0, class_name='btn-secondary'), 
                    ], className='d-flex justify-content-between align-items-center'),                    
                ], width=9, style={'padding-left': '0px'}),
            ], class_name='mb-3'),
        dbc.Row([ modal_with_graph, modal_commodity_group_graph]),         
                      
], class_name='border-top bg-light')


# Callbacks================================================================

# Callback to handle cell clicks and display modal with graph
@app.callback( 
    Output("modal-with-graph", "is_open"), 
    Output("area-fillgradient-graph", "figure"),
    Output("line-prc-change-graph", "figure"),
    Input('ag-grid-with-graph', 'cellClicked'),    
    State("modal-with-graph", "is_open") ,
    prevent_initial_call=True
     )
def display_modal(selected_cell, is_open):  
    if selected_cell and selected_cell['colId'] == 'Product':
            product = selected_cell['value'] 
            dff = df_2010_2024[['Date', product]]
            # Create line graph with positive and negative values colored differently
            line_prc_change_graph = line_chart_with_pos_and_neg_colors(dff, 'Date', product, 
                                       pos_color, neg_col, title=f"MoM Change of Price across Years") 
            line_prc_change_graph.update_layout(paper_bgcolor='white', plot_bgcolor='white',)
            # Create area graph for period from 01/2010 to 11/2024
            title = f"Monthly Price of {product} <br><sup>Historical Data for period from 01/2010 to 11/2024"
            fig = create_area_fillgradient(dff, 'Date', product, col_scale, line_color, title)
            fig.update_traces(hovertemplate='%{x}<br>Price = $%{y:,.2f}') 
            fig.update_layout(paper_bgcolor='white', plot_bgcolor='white', height=350) 
            # Update properties for Plywood Commodity
            if product == 'Plywood':
                fig.update_layout(yaxis_ticksuffix='¢') 
                fig.update_traces(hovertemplate='%{x}<br>Price = ¢%{y:,.2f}')  
            
            # Open modal and display graphs
            return True, fig , line_prc_change_graph 
   
    return is_open, no_update, no_update


# Callback to close the modal 
@app.callback( 
    Output("modal-with-graph", "is_open", allow_duplicate=True),     
    Input("close-modal-button", "n_clicks"),
    State("modal-with-graph", "is_open") ,
    prevent_initial_call=True
)
def display_modal( n_clicks_close, is_open):     
    if n_clicks_close  :        
        return False    
    return is_open
  

# Callback to reset filtering and column state (sort and filter)
@app.callback(
    Output('ag-grid-with-graph', 'filterModel'),    
    Output('ag-grid-with-graph', 'resetColumnState'),
    Input('reset-filters-button', 'n_clicks'),     
) 
def reset_all_filters(n_clicks):    
    if n_clicks > 0: 
        return {}, True 
    return no_update, no_update


# Callback to download the data as csv file
@app.callback(
    Output("ag-grid-with-graph", "exportDataAsCsv"),
    Output("ag-grid-with-graph", "csvExportParams"),
    Input("download-button", "n_clicks"),
    prevent_initial_call=True
)
def export_data_as_csv(n_clicks):
    if n_clicks:
        # Extract all column keys except for the last column 
        column_keys = dfgrid.columns[:-1].tolist()
        return True, {"fileName": "commodities-prices.csv", 'columnKeys': column_keys}
    return False, {}


# Callback to open modal and display commodity group graph
@app.callback(
    Output("commodity-group-modal", "is_open"),
    Output("modal-commodity-group-graph", "figure"),
     [Input(f'{index}-{commodity}', 'n_clicks') for index, com_group in commodity_groups.items() for commodity in com_group],
    Input("close-modal-commodity-group", "n_clicks"),
    State("commodity-group-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_modal(*args):        
    if not ctx.triggered_id:
        return no_update, no_update
    
    if ctx.triggered_id == "close-modal-commodity-group":
        return False, no_update   
     
    # Get button id
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    # Split button_id to get group and commodity names 
    group_name, commodity_name = button_id.split('-')
    # Get commodity columns for selected group
    commodity_columns = commodity_groups[group_name]
    # Create graph for commodity group
    commodity_groups_graph = line_chart_for_commodity_group(df_2010_2024, commodity_columns, commodity_name, group_name)

    return True, commodity_groups_graph


if __name__ == "__main__":
    app.run_server(debug=False, port=8051)
