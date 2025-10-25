"""
Graph Generation Utilities
Generates base64-encoded PNG charts for portfolio visualization.
"""

import base64
import io
import logging
import os
from typing import List, Dict
import plotly.graph_objects as go
import plotly.express as px

logger = logging.getLogger(__name__)

import subprocess
try:
    chromium_path = subprocess.check_output(
        ['which', 'chromium-browser'], 
        stderr=subprocess.DEVNULL
    ).decode().strip()
    if chromium_path:
        os.environ.setdefault('CHROME_PATH', chromium_path)
except Exception:
    pass


def generate_allocation_chart(allocations: List[Dict]) -> str:
    """
    Generate a pie chart showing portfolio allocation by ticker.
    
    Args:
        allocations: List of allocation dicts with ticker and allocation_pct
        
    Returns:
        Base64-encoded PNG image string
    """
    try:
        if not allocations:
            return ""
        
        tickers = [alloc.get("ticker", "Unknown") for alloc in allocations]
        percentages = [alloc.get("allocation_pct", 0) for alloc in allocations]
        
        fig = go.Figure(data=[go.Pie(
            labels=tickers,
            values=percentages,
            hole=0.3,
            textinfo='label+percent',
            textposition='auto',
            marker=dict(
                line=dict(color='white', width=2)
            )
        )])
        
        fig.update_layout(
            title={
                'text': 'Portfolio Allocation by Ticker',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#333'}
            },
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05
            ),
            width=800,
            height=600,
            paper_bgcolor='white',
            plot_bgcolor='white'
        )
        
        img_bytes = fig.to_image(format="png", width=800, height=600, scale=2)
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        return img_base64
        
    except Exception as e:
        logger.error(f"Error generating allocation chart: {e}", exc_info=True)
        return ""


def generate_income_projection_chart(projections: List[Dict]) -> str:
    """
    Generate a bar/line chart showing projected annual dividend income.
    
    Args:
        projections: List of projection dicts with year and projected_income
        
    Returns:
        Base64-encoded PNG image string
    """
    try:
        if not projections:
            return ""
        
        years = [f"Year {p.get('year', 0)}" for p in projections]
        incomes = [p.get("projected_income", 0) for p in projections]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=years,
            y=incomes,
            name='Projected Income',
            marker=dict(
                color='#4CAF50',
                line=dict(color='#2E7D32', width=2)
            ),
            text=[f"${income:,.0f}" for income in incomes],
            textposition='outside'
        ))
        
        fig.add_trace(go.Scatter(
            x=years,
            y=incomes,
            mode='lines+markers',
            name='Growth Trend',
            line=dict(color='#FF9800', width=3),
            marker=dict(size=10, color='#FF5722')
        ))
        
        fig.update_layout(
            title={
                'text': 'Projected Annual Dividend Income (5-Year)',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#333'}
            },
            xaxis_title='Year',
            yaxis_title='Annual Income ($)',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            width=800,
            height=600,
            paper_bgcolor='white',
            plot_bgcolor='#f5f5f5',
            hovermode='x unified'
        )
        
        fig.update_yaxes(
            gridcolor='white',
            tickformat='$,.0f'
        )
        
        img_bytes = fig.to_image(format="png", width=800, height=600, scale=2)
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        return img_base64
        
    except Exception as e:
        logger.error(f"Error generating income projection chart: {e}", exc_info=True)
        return ""


def generate_sector_diversification_chart(diversification: Dict) -> str:
    """
    Generate a pie chart showing sector allocation percentages.
    
    Args:
        diversification: Dict mapping sector names to allocation percentages
        
    Returns:
        Base64-encoded PNG image string
    """
    try:
        if not diversification:
            return ""
        
        sectors = list(diversification.keys())
        percentages = list(diversification.values())
        
        colors = px.colors.qualitative.Set3[:len(sectors)]
        
        fig = go.Figure(data=[go.Pie(
            labels=sectors,
            values=percentages,
            hole=0.3,
            textinfo='label+percent',
            textposition='auto',
            marker=dict(
                colors=colors,
                line=dict(color='white', width=2)
            )
        )])
        
        fig.update_layout(
            title={
                'text': 'Sector Diversification',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#333'}
            },
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05
            ),
            width=800,
            height=600,
            paper_bgcolor='white',
            plot_bgcolor='white'
        )
        
        img_bytes = fig.to_image(format="png", width=800, height=600, scale=2)
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        return img_base64
        
    except Exception as e:
        logger.error(f"Error generating sector diversification chart: {e}", exc_info=True)
        return ""
