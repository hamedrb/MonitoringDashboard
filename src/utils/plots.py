import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
pio.templates.default = "ggplot2"


def custome_color_map():
    colors1 = px.colors.qualitative.Pastel
    colors1 = colors1[:-1]

    colors2 = px.colors.qualitative.Vivid
    colors2 = colors2[:-1]

    colors = colors1 + colors2

    return colors


def get_colormap(centers):
    colors = custome_color_map()
    colormap = {
        center: colors[i]
        for i, center in enumerate(centers)
    }
    return colormap


def generate_barplot(counts_df: pd.DataFrame, centers: list, time_unit: str):
    """
    Create grouped bar plot of counts per center.
    """
    fig = go.Figure()

    # Prepare x
    x = counts_df['Time']

    #colors = custome_color_map()
    colormap = get_colormap(centers)

    for i, center in enumerate(centers):
        fig.add_trace(go.Bar(x=x, 
                             y=counts_df[center], 
                             name=center, 
                             #marker_color=colors[i]
                             marker_color=colormap[center]
                             ))

    fig.update_layout(
        title=dict(
            text=f"{time_unit} counts by center",
            font=dict(size=18)
            ),
        xaxis_title=f"Time ({time_unit})",
        yaxis_title="Number of subjects",
        barmode="group",
        xaxis=dict(
            tickangle=-90
        ),
        margin=dict(l=60, r=40, t=100, b=80),
        font=dict(
            family="Arial, sans-serif",
            size=14,
            color="black"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        bargap=0.2,
        bargroupgap=0.05
    )

    fig.update_xaxes(
        showgrid=False
        )
    
    if time_unit == "Month":
        fig.update_xaxes(
            tickformat="%b %Y", # On hovering, show "Month Year" instead of "Month 01 Year"
            showgrid=False
            )
    else:
        fig.update_xaxes(
            showgrid=False
            )

    fig.update_yaxes(
        showgrid=True
        )
    
    fig.update_traces(
        hovertemplate="%{x}<br>%{y} subjects"
    )

    return fig


def generate_lineplot(counts_df: pd.DataFrame, centers: list, time_unit: str):
    """
    Create cumulative line plot per center.
    """

    fig = go.Figure()

    x = counts_df["Time"]

    colormap = get_colormap(centers)

    for center in centers:
        fig.add_trace(go.Scatter(
            x=x,
            y=counts_df[center].cumsum(),
            mode="lines+markers",
            name=center,
            marker_color=colormap[center],
            line=dict(width=2),
            marker=dict(size=6),
        ))

    fig.update_layout(
        title=dict(
            text=f"Cumulative {time_unit.lower()} counts by center",
            font=dict(size=18)
            ),
        xaxis_title=f"Time ({time_unit})",
        yaxis_title="Number of subjects",
        xaxis=dict(
            tickangle=-90
        ),
        margin=dict(l=60, r=40, t=100, b=80),
        font=dict(
            family="Arial, sans-serif",
            size=14,
            color="black"
            ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )

    if time_unit == "Month":
        fig.update_xaxes(
            tickformat="%b %Y", # On hovering, show "Month Year" instead of "Month 01 Year"
            showgrid=True
            )
    else:
        fig.update_xaxes(
            showgrid=True
            )

    fig.update_yaxes(
        showgrid=True
        )
    
    fig.update_traces(
        hovertemplate="%{x}<br>%{y} subjects"
    )
        
    return fig


def generate_donut_plot(stats_df, centers):

    labels = centers
    values = stats_df.loc["Total subjects", labels].astype(int)
    total_subjects = values.sum()

    # colors = custome_color_map()
    colormap = get_colormap(centers)

    fig = go.Figure()

    fig.add_trace(go.Pie(
        labels=labels,
        values=values,
        # marker=dict(colors=colors[:len(labels)]),
        marker=dict(colors=[colormap[c] for c in labels]),
        hole=0.4,
        sort=False # preserve centers order
    ))

    fig.update_traces(
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>"
    )

    fig.update_layout(
        title=dict(
            text="Total subject distribution",
            font=dict(size=18)
        ),
        margin=dict(l=60, r=40, t=100, b=80),
        font=dict(
            family="Arial, sans-serif",
            size=18
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        annotations=[
            dict(
                text=f"<b>Total</b><br><b>{total_subjects}</b>",
                x=0.5,
                y=0.5,
                showarrow=False,
                xanchor="center",
                font=dict(size=24)
            )
        ]
    )

    return fig