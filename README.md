# Sinter Burden Optimizer — Industrial Streamlit Dashboard

This version implements the requested industrial dashboard layout:

- Permanent left navigation
- Hospet plant header
- Compact optional Excel upload
- Built-in master chemistry as default
- Editable Price and RM Stock
- Material availability toggle
- Prominent Run Optimizer button
- KPI cards
- Grouped burden donut chart
- Chemistry and quality tables
- Quality status indicators
- Optimal burden and cost breakdown
- TOTAL rows in result tables
- Manual adjustment
- What-if analysis
- Bottleneck analysis
- Reports
- Upload/settings

## GitHub / Streamlit deployment

Upload these files to the repository:

- `app.py`
- `optimizer.py`
- `requirements.txt`

Then connect the repository to Streamlit Community Cloud and select `app.py` as the main file.

The optimization engine is kept in `optimizer.py` and is not mixed into the UI.
