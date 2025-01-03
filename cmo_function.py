import pandas as pd
import plotly.graph_objects as go


# Define colors for positive and negative values
pos_color = 'rgba(0, 160, 0, 0.7)'
neg_col = 'rgba(255, 0, 0, 0.7)'

# Define colorscale for positive and negative values
col_scale = [[0,'rgba(255, 255, 255, 0.1)'], [0.5,'rgba(31,119,180,0.2)'], [1,'rgba(31,119,180,0.5)']]
line_color = 'rgba(31,119,180,0.7)'

# Define config dictionary 
config_dict = dict(
    {'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d'],
    'displaylogo': True })


# ================================================================================
def create_sparkline(df_melt):
    # filter df by the last month of the available data
    df_with_graph = df_melt.loc[df_melt['Date'] == '2024-11-01'].copy()  

    #Create the spark line for each commodity 
    df_with_graph["graph"] = ''

    for i, r in df_with_graph.iterrows():
        filterDf = df_melt[df_melt["Product"] == r["Product"]]
        
        # Calculate min and max values 
        ymax, ymin = filterDf['Price'].max(), filterDf['Price'].min()
        # Get index of max and min values
        xmax = filterDf.loc[filterDf['Price'].idxmax(),'Date']    
        xmin = filterDf.loc[filterDf['Price'].idxmin(),'Date']  

        # Create figure
        fig = go.Figure()   

        # Add line with trend for last year     
        fig.add_scatter(
            x=filterDf['Date'],
            y=filterDf['Price'],    
            mode='lines', name='', 
            line=dict(color='lightgrey', width=1.5)) 
        
        # Add marker for max value
        fig.add_scatter(x=[xmax], y=[ymax], 
                        mode='markers', name='',
                        marker=dict(color='green', size=5)) 

        # Add marker for min value
        fig.add_scatter(x=[xmin], y=[ymin], 
                        mode='markers', name='',
                        marker=dict(color='red', size=5))
                        
        # Update hovertemplate for each trace
        fig.update_traces(hovertemplate='%{x}<br>Price: $%{y:,.2f}') 

        # Add horizontal baseline with previous year value
        fig.add_hline(y=filterDf['Price'].values[0], line=dict(color='grey', width=0.5, dash='dot'))  
        
        # Update layout properties 
        fig.update_layout(
            showlegend=False,
            yaxis_visible=False,       
            xaxis=dict(range=[filterDf['Date'].min()+pd.DateOffset(days=-7), 
                            filterDf['Date'].max()+pd.DateOffset(days=7)], 
                       visible=False),      
            margin=dict(l=0, r=0, t=0, b=0),
            template="plotly_white")
            
        # Add figure to dataframe
        df_with_graph.at[i,'graph'] = fig  

    return df_with_graph 

# ================================================================================
def line_chart_for_commodity_group(dff, commodity_group, commodity, index_name):
    # Create figure
    fig = go.Figure()
    # Add line for each commodity
    for col in dff[commodity_group]:
        fig.add_scatter(x=dff['Date'], y=dff[col],
                        line=dict(color='lightgray', width=1.5),
                        name=col, visible='legendonly',
                        customdata=[col]*dff.shape[0],
                        hovertemplate='%{y:,.2f}$ %{customdata}<extra></extra>')
        
    # Update line properties for selected commodity
    fig.update_traces(
        line=dict(color='#6fabd4', width=2),
        zorder=1, visible=True,
        fill='tozeroy', fillcolor='rgba(31,119,180,0.1)',
        selector={'name':commodity})
    
    # Add range selector with buttons and rangeslider  
    fig.update_xaxes(
        ticklabelstandoff=5,    
        rangeselector=dict(
            bgcolor='rgba(31,119,180,0.1)',
            x=1.02, y=1.05,                
            buttons=list([            
                dict(count=6, label="6M", step="month", stepmode="backward"),              
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(count=5, label="5Y", step="year", stepmode="backward"),
                dict(label="ALL", step="all")
            ])
        ),  
        rangeslider=dict(visible=True, thickness=0.1), # The height of the range slider(fraction) 
    )
    # Update layout properties
    if dff[commodity].max() <= 10:
        x_tickformat='.1f'    
    else:
        x_tickformat=',.0f'

    fig.update_layout(
        title=f'Monthly Price of {commodity}<br><sup>Historical Data: 01/2010 - 11/2024</sup>',
        title_font_size=20,
        height=450, margin=dict(l=50, t=70, b=0),
        legend=dict(title=f'{index_name}<br>'),
        #yaxis_autorange='max', yaxis_rangemode='tozero',
        yaxis=dict(ticklabelstandoff=5, ticksuffix='$', tickformat=x_tickformat),         
        hovermode='x', template='plotly_white')

    return fig

# ================================================================================
def get_min_max_values_and_index(dff, x_col_name, y_col_name):
    idx_max = dff.loc[dff[y_col_name].idxmax(), x_col_name]
    idx_min = dff.loc[dff[y_col_name].idxmin(), x_col_name]
    max_val, min_val = dff[y_col_name].agg(['max', 'min'])

    return  idx_max, idx_min, max_val, min_val

# ================================================================================
def create_area_fillgradient(dff, x_col_name, y_col_name, col_scale, line_color, title):
    fig = go.Figure()
    fig.add_scatter(
        x=dff[x_col_name], y=dff[y_col_name],        
        mode='lines',  name='',
        line=dict(color=line_color, width=1), 
        fill='tozeroy',
        fillgradient=dict(            
            type = 'vertical',
            colorscale=col_scale)) 
       
    # Culculate min and max values
    xmax, xmin, ymax, ymin = get_min_max_values_and_index(dff, x_col_name, y_col_name)
    # Add vertical line for max value
    fig.add_shape(type="line", x0=xmax, y0=0, x1=xmax, y1=ymax, 
                  line=dict(color='green', width=0.5, dash='dot'))
    # Add vertical line for min value
    fig.add_shape(type="line", x0=xmin, y0=0, x1=xmin, y1=ymin, 
                  line=dict(color='red', width=0.5, dash='dot'))
    # Add markers for max and min values
    fig.add_scatter(
        x=[xmax, xmin], y=[ymax, ymin], 
        mode='markers', 
        marker=dict(color=['green', 'red'], size=5), 
        name='' )
    
    fig.update_traces(hovertemplate='%{x}<br>Index = $%{y:,.2f}')

    # Calculate trend
    cng = dff[y_col_name].values[[0, -1]]
    trend = (cng[-1] - cng[0]) / cng[0]
    # Determine color based on trend value 
    color = 'red' if trend < 0 else 'green'
    # Define text for annotation
    text=f'15-years<br>trend<br><span style="color:{color}"><b>{trend:.1%}</span>' 
    # Add horizontal line with trend value
    fig.add_hline(y=cng[0], line=dict(color='black', width=0.5, dash='dot'), 
                  annotation_text=text, annotation_position='right')
    
    # Update layout properties
    if ymax < 10:
        y_tickformat = ',.1f'
    else:
        y_tickformat = ',.0f'

    fig.update_layout(
        title=title, title_font_size=20,  title_y=0.94,      
        showlegend=False, modebar_orientation='v',
        height=400, xaxis_range=[dff[x_col_name].min(), dff[x_col_name].max()],
        yaxis=dict(ticklabelstandoff=5, ticksuffix='$' , tickformat=y_tickformat), 
        xaxis_ticklabelstandoff=5,template='plotly_white',
        margin=dict(l=50, t=70, r=70, b=20))    

    return fig

#===============================================================================
def colorscale_with_zero_position(diff_values, neg_col, pos_color ) : 
    # Calculate min and max of the diff values
    min_diff = min(diff_values)
    max_diff = max(diff_values)
    # Normalize the zero point in the range of the data
    zero_position = (0 - min_diff) / (max_diff - min_diff)
    # Define a colorscale using zero position for negative and positive values
    colorscale=[[0, neg_col], [zero_position, neg_col], [zero_position, pos_color], [1.0 , pos_color]]
    
    return colorscale

#===============================================================================
def line_chart_with_pos_and_neg_colors(dff, x_col_name, y_col_name, 
                                       pos_color, neg_col, title):  

    # Culculate the percentage change in y-values
    y = 100*dff[y_col_name].pct_change().fillna(0).values

    # Create a list of colors for each data point based on its sign
    # If the value is positive or zero, use 'pos_color', otherwise use 'neg_col'
    marker_colors = [pos_color if v > 0 else neg_col if v < 0 else 'lightgrey' for v in y]  

    # Generate a colorscale that transitions between neg_col and pos_color at zero    
    colorscale = colorscale_with_zero_position(y, neg_col, pos_color)  

    # Create a new Plotly figure
    fig = go.Figure()  

    # Add a scatter trace to the figure, representing the line chart
    fig.add_scatter(
        x=dff[x_col_name],  
        y=y,  
        name='',  
        hovertemplate='%{x}<br>MoM growth = %{y:.2f}%',  # Hover text format
        mode='markers',  # Display as connected points with colored markers
        marker=dict(color=marker_colors, size=0.1),  # Marker styling
        fill='tozeroy',  # Fill area under the line to zero
        fillgradient=dict(type="vertical", colorscale=colorscale) # Apply vertical fill gradient
    )
    # Add horizontal lines for max rate
    fig.add_hline(y=max(y), line=dict(color='green', width=0.5, dash='dot'), 
                  annotation_text=f'Max<br><span style="color:green"><b>{max(y):.1f}%</span>',
                  annotation_position='right')
    # Add horizontal lines for min rate
    fig.add_hline(y=min(y), line=dict(color='red', width=0.5, dash='dot'), 
                  annotation_text=f'Min<br><span style="color:red"><b>{min(y):.1f}%</span>', 
                  annotation_position='right')
    
    # Update the layout of the figure for styling and labels
    fig.update_layout(
        title=title,  
        title_font_size=20,     
        height=250, template='plotly_white', 
        margin=dict(l=30, t=50, r=70, b=20),  
        yaxis=dict(ticksuffix='%', ticklabelstandoff=5),  
        xaxis_ticklabelstandoff=10  
    )
   
    return fig
