import streamlit as st

def apply_custom_css():
    """Injects custom CSS to override Streamlit styling and make the UI look premium."""
    st.markdown("""
        <style>
        /* Load Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
        
        /* Apply font to Streamlit main elements */
        html, body, [class*="css"], .stMarkdown {
            font-family: 'Outfit', sans-serif;
        }
        
        /* Glassmorphism KPI Card CSS */
        .kpi-card {
            background: rgba(13, 33, 36, 0.65);
            backdrop-filter: blur(12px) saturate(180%);
            -webkit-backdrop-filter: blur(12px) saturate(180%);
            border-radius: 14px;
            border: 1px solid rgba(20, 184, 166, 0.15);
            padding: 22px;
            margin: 8px 0px;
            transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), border-color 0.3s ease, box-shadow 0.3s ease;
        }
        
        .kpi-card:hover {
            transform: translateY(-4px);
            border-color: rgba(45, 212, 191, 0.45);
            box-shadow: 0 10px 25px rgba(20, 184, 166, 0.15);
        }
        
        .kpi-title {
            color: #a0aec0;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            font-weight: 600;
        }
        
        .kpi-value {
            color: #ffffff;
            font-size: 2.2rem;
            font-weight: 800;
            margin-top: 6px;
            background: linear-gradient(135deg, #ffffff 50%, #2dd4bf 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .kpi-delta {
            font-size: 0.85rem;
            margin-top: 6px;
            font-weight: 600;
            display: flex;
            align-items: center;
        }
        
        .delta-positive {
            color: #14b8a6;
        }
        
        .delta-negative {
            color: #f43f5e;
        }
        
        .delta-neutral {
            color: #fbbf24;
        }
        
        /* Premium Gradient Header */
        .gradient-header {
            background: linear-gradient(45deg, #14b8a6, #06b6d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            font-size: 2.6rem;
            margin-bottom: 5px;
        }
        
        .gradient-subheader {
            background: linear-gradient(45deg, #2dd4bf, #22d3ee);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
            font-size: 1.6rem;
            margin-top: 15px;
            margin-bottom: 10px;
        }
        
        /* Custom Section containers */
        .premium-container {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(20, 184, 166, 0.05);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
        }
        
        /* Badge style tags */
        .premium-badge {
            display: inline-block;
            background: rgba(20, 184, 166, 0.1);
            color: #2dd4bf;
            border: 1px solid rgba(20, 184, 166, 0.25);
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.8rem;
            margin-right: 8px;
            margin-bottom: 8px;
            font-weight: 600;
        }
        
        /* Custom Table styling override for Streamlit */
        .stTable {
            border-radius: 10px;
            overflow: hidden;
        }
        
        /* Subtitle style */
        .subtitle {
            color: #cbd5e0;
            font-size: 1.05rem;
            line-height: 1.5;
            margin-bottom: 25px;
        }
        </style>
    """, unsafe_allow_html=True)

def kpi_card(title: str, value: str, delta: str = None, trend: str = "neutral"):
    """Renders a single premium glassmorphic KPI block.
    
    trend options: 'positive' (teal), 'negative' (rose), 'neutral' (gold)
    """
    if trend == "positive":
        delta_class = "delta-positive"
        arrow = "▲"
    elif trend == "negative":
        delta_class = "delta-negative"
        arrow = "▼"
    else:
        delta_class = "delta-neutral"
        arrow = "◆"
        
    delta_html = f'<div class="kpi-delta {delta_class}">{arrow} {delta}</div>' if delta else ""
    
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
    """, unsafe_allow_html=True)
