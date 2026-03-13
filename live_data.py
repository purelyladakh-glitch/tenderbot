"""
TenderBot — Live Market Data Context
This file provides current market rates for Indian construction materials,
labour, and standard profit margins. This data is injected into the Gemini
prompt to anchor its estimates in reality, preventing hallucinations.

Updated: March 2026
"""

def get_live_market_data() -> str:
    return """
[LIVE MARKET RATES - INDIA CONTEXT (March 2026)]
- Cement: ₹350 - ₹420 per 50kg bag (OPC/PPC)
- TMT Steel Rebar: ₹52,000 - ₹58,000 per Metric Tonne
- Sand (River/M-Sand): ₹3,500 - ₹6,000 per brass
- Aggregate (Gitti): ₹2,500 - ₹4,000 per brass
- Bricks (Red/Flyash): ₹6 - ₹12 per piece
- Bitumen (VG30/VG40): ₹48,000 - ₹55,000 per MT

[LABOUR RATES (Per Day)]
- Unskilled Labour: ₹400 - ₹600
- Skilled Labour (Mason/Carpenter): ₹700 - ₹1,100
- Operator / Driver: ₹800 - ₹1,200

[STANDARD ESTIMATION RULES]
- Typical Contractor Profit Margin: 10% to 15% (Never exceed 20% unless high-risk remote area like Ladakh)
- Overhead & Contingencies: 5% to 8%
- GST on Construction: 18% (usually specified in BOQ)
- Standard EMD: 2% of Tender Value
- Standard Retention/Performance Security: 3% to 5% of Tender Value

[REGIONAL MODIFIERS]
- If location is "Ladakh", "Leh", "Kargil", "J&K", or high altitude:
  - Increase transport costs by 30-40%
  - Restrict working season to May-October (6 months)
  - Apply 20-30% premium on labour due to scarcity
"""
