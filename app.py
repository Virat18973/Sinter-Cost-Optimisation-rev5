
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from optimizer import (
    TARGETS, FE_LOWER, FE_UPPER,
    get_default_chemistry, load_chemistry_from_excel,
    solve_blend_with_compensation, calculate_cost_breakdown,
    quality_checks, quality_table, redistribute_adjustment,
    what_if_analysis, compute_achieved,
)

# ============================================================
# PAGE
# ============================================================
st.set_page_config(
    page_title="Sinter Burden Optimizer",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# INDUSTRIAL THEME
# ============================================================
st.markdown("""
<style>
:root {
    --bg:#071018;
    --panel:#0c1620;
    --panel2:#101c27;
    --border:#203342;
    --text:#edf3f8;
    --muted:#8798a8;
    --blue:#2f80ed;
    --cyan:#20c4d9;
    --green:#36d47a;
    --amber:#f5b642;
    --red:#f15b5b;
    --purple:#8b6cff;
}

.stApp {
    background:
        radial-gradient(circle at 90% 0%, rgba(47,128,237,.10), transparent 28%),
        linear-gradient(180deg,#071018 0%,#09131c 100%);
    color:var(--text);
}

.block-container {
    max-width: 1700px;
    padding: .55rem 1rem 1.5rem 1rem;
}

h1,h2,h3,h4,h5 { color:#f5f8fb !important; }

.small {
    color:var(--muted);
    font-size:.72rem;
}

.section {
    color:#55a9ff;
    font-size:.70rem;
    font-weight:800;
    letter-spacing:.10em;
    text-transform:uppercase;
    margin:.15rem 0 .42rem;
}

.panel {
    background:rgba(12,22,32,.92);
    border:1px solid var(--border);
    border-radius:8px;
    padding:.65rem;
}

.kpi {
    background:linear-gradient(145deg,#0d1924,#0b151f);
    border:1px solid #223848;
    border-radius:8px;
    padding:.65rem .75rem;
    min-height:92px;
    box-shadow:0 6px 20px rgba(0,0,0,.12);
}

.kpi-blue { border-left:3px solid var(--blue); }
.kpi-green { border-left:3px solid var(--green); }
.kpi-amber { border-left:3px solid var(--amber); }
.kpi-cyan { border-left:3px solid var(--cyan); }
.kpi-purple { border-left:3px solid var(--purple); }

.kpi-label {
    font-size:.62rem;
    color:#7fa4c4;
    text-transform:uppercase;
    letter-spacing:.08em;
    font-weight:800;
}
.kpi-value {
    color:#f4f8fb;
    font-size:1.32rem;
    line-height:1.2;
    font-weight:800;
    margin-top:.22rem;
}
.kpi-sub {
    color:#80909e;
    font-size:.66rem;
    margin-top:.18rem;
}

.banner-ok,.banner-warn,.banner-bad {
    border-radius:7px;
    padding:.48rem .7rem;
    font-size:.72rem;
    font-weight:700;
    margin:.35rem 0 .55rem;
}
.banner-ok {
    background:#08291d;
    border:1px solid #145f3b;
    color:#54df96;
}
.banner-warn {
    background:#38290d;
    border:1px solid #70501a;
    color:#ffc65b;
}
.banner-bad {
    background:#391216;
    border:1px solid #77242d;
    color:#ff7474;
}

.edit-hint {
    background:#0a1b2b;
    border:1px solid #245274;
    border-radius:6px;
    padding:.35rem .55rem;
    color:#7fc6ff;
    font-size:.65rem;
    margin-bottom:.4rem;
}

.sidebar-title {
    color:#eaf1f7;
    font-size:1.02rem;
    font-weight:800;
    letter-spacing:.02em;
}
.sidebar-sub {
    color:#7f92a4;
    font-size:.63rem;
    margin-bottom:.7rem;
}

div[data-testid="stSidebar"] {
    background:linear-gradient(180deg,#071019,#09141d);
    border-right:1px solid #203342;
}
div[data-testid="stSidebar"] .block-container {
    padding:.9rem .65rem;
}

button[kind="primary"] {
    background:#176eea !important;
    border-color:#176eea !important;
}
button[kind="primary"]:hover {
    background:#0f59c9 !important;
}

[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
    border:1px solid var(--border);
    border-radius:7px;
}

.stTabs [data-baseweb="tab-list"] {
    gap:.1rem;
    background:#09131d;
    border:1px solid #1d3040;
    border-radius:7px;
    padding:.16rem;
}
.stTabs [data-baseweb="tab"] {
    color:#9eb0c0;
    font-size:.70rem;
}
.stTabs [aria-selected="true"] {
    color:#55a9ff !important;
}

div[data-testid="stMetric"] {
    background:#0c1721;
    border:1px solid #203342;
    border-radius:7px;
}

hr { border-color:#203342; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# STATE
# ============================================================
if "df" not in st.session_state:
    st.session_state.df = get_default_chemistry()
if "source" not in st.session_state:
    st.session_state.source = "Built-in Master Chemistry"
if "source_name" not in st.session_state:
    st.session_state.source_name = "Built-in Master Chemistry"
if "availability" not in st.session_state:
    st.session_state.availability = {}
if "result" not in st.session_state:
    st.session_state.result = None
if "previous_cost" not in st.session_state:
    st.session_state.previous_cost = None
if "inputs_changed" not in st.session_state:
    st.session_state.inputs_changed = False
if "what_if" not in st.session_state:
    st.session_state.what_if = None
if "adjusted_blend" not in st.session_state:
    st.session_state.adjusted_blend = None

df = st.session_state.df
for material in df.index:
    st.session_state.availability.setdefault(material, True)
for material in list(st.session_state.availability):
    if material not in df.index:
        del st.session_state.availability[material]

GROUP_ORDER = ["Iron_ore", "Flux", "Recycle", "Fuel"]
GROUP_LABEL = {
    "Iron_ore": "Iron Ore",
    "Flux": "Flux",
    "Recycle": "Recycle",
    "Fuel": "Fuel",
}
GROUP_COLORS = {
    "Iron_ore": "#2f80ed",
    "Flux": "#39c77b",
    "Recycle": "#f2b134",
    "Fuel": "#ef5350",
}

# ============================================================
# HELPERS
# ============================================================
def active_df():
    out = st.session_state.df.copy()
    for m in out.index:
        if not st.session_state.availability.get(m, True):
            out.loc[m, "Available_Tonnes"] = 0
    return out


def set_dataset(new_df, source, name):
    st.session_state.df = new_df.copy()
    st.session_state.source = source
    st.session_state.source_name = name
    st.session_state.availability = {m: True for m in new_df.index}
    st.session_state.result = None
    st.session_state.previous_cost = None
    st.session_state.inputs_changed = False
    st.session_state.what_if = None
    st.session_state.adjusted_blend = None


def ordered_cost(df_breakdown):
    out = df_breakdown.copy()
    out["_order"] = out["Group"].map({g:i for i,g in enumerate(GROUP_ORDER)}).fillna(99)
    return out.sort_values(["_order", "Material"]).drop(columns="_order")


def total_row(df_breakdown, total_burden, total_cost):
    row = {c: "" for c in df_breakdown.columns}
    row["Material"] = "TOTAL"
    if "Group" in row:
        row["Group"] = "—"
    if "kg/t" in row:
        row["kg/t"] = total_burden
    if "% of Burden" in row:
        row["% of Burden"] = 100.0
    if "Cost Rs/t" in row:
        row["Cost Rs/t"] = total_cost
    if "% of Cost" in row:
        row["% of Cost"] = 100.0
    return pd.concat([df_breakdown, pd.DataFrame([row])], ignore_index=True)


def quality_banner(achieved):
    checks = quality_checks(achieved, TARGETS)
    failed = [k for k,v in checks.items() if not v]
    if not failed:
        st.markdown(
            '<div class="banner-ok">● QUALITY OK — All mandatory quality constraints satisfied</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="banner-bad">● QUALITY ALERT — {", ".join(failed)} outside target</div>',
            unsafe_allow_html=True
        )


def quality_display(achieved):
    q = quality_table(achieved, TARGETS).copy()
    q["Status"] = q["Status"].map({"OK":"🟢 OK","OUT":"🔴 OUT"}).fillna(q["Status"])
    return q


def run_optimizer():
    before = st.session_state.result["cost"] if st.session_state.result else None
    result = solve_blend_with_compensation(
        active_df(), production_tonnes=1000, targets=TARGETS
    )
    st.session_state.previous_cost = before
    st.session_state.result = {
        "status": result[0],
        "blend": result[1],
        "cost": result[2],
        "achieved": result[3],
        "diagnostics": result[4],
        "fallback": result[5],
        "df": active_df().copy(),
    }
    st.session_state.inputs_changed = False


def change_signature():
    vals = []
    for m in st.session_state.df.index:
        vals.append((
            m,
            round(float(st.session_state.df.loc[m,"Price_Rs_t"]),4),
            round(float(st.session_state.df.loc[m,"Available_Tonnes"]),4),
            bool(st.session_state.availability.get(m,True))
        ))
    return tuple(vals)

if "signature" not in st.session_state:
    st.session_state.signature = change_signature()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown('<div class="sidebar-title">🏭 BAJAJ MUKAND</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">Alloy Steel Group • Hospet Plant</div>', unsafe_allow_html=True)
    st.markdown("---")

    nav = st.radio(
        "Navigation",
        [
            "Dashboard",
            "RM Stock",
            "Cost Composition",
            "Burden Composition",
            "Optimization Results",
            "What-if Analysis",
            "Bottleneck Analysis",
            "Reports",
            "Upload & Settings",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(
        f'<div class="small">Data source</div><b>{st.session_state.source_name}</b>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<div class="small">{len(st.session_state.df)} materials loaded</div>',
        unsafe_allow_html=True
    )
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("Sinter Burden Optimizer v22.4")

# ============================================================
# HEADER
# ============================================================
h1, h2, h3 = st.columns([5.5, 2.0, 1.4])
with h1:
    st.markdown("## SINTER BURDEN OPTIMIZER")
    st.markdown('<div class="small">Cost Optimal Sinter Mix with Quality Assurance</div>', unsafe_allow_html=True)
with h2:
    if st.session_state.result and st.session_state.result["achieved"] is not None:
        checks = quality_checks(st.session_state.result["achieved"], TARGETS)
        if all(checks.values()):
            st.markdown('<div class="banner-ok" style="text-align:center;">✓ QUALITY OK</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="banner-bad" style="text-align:center;">⚠ QUALITY ALERT</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="banner-ok" style="text-align:center;">● READY</div>', unsafe_allow_html=True)
with h3:
    now = datetime.now()
    st.markdown(
        f'<div style="text-align:right;font-size:.68rem;color:#b8c4cf;">'
        f'<b>Plant: Hospet</b><br>{now:%d %b %Y} | {now:%I:%M %p}</div>',
        unsafe_allow_html=True
    )

# ============================================================
# DASHBOARD
# ============================================================
def dashboard_page():
    tabs = st.tabs([
        "01 Optimization",
        "02 Raw Material Chemistry",
        "03 Manual Adjustment",
        "04 What-if Analysis",
        "05 Bottleneck Analysis",
        "06 Upload & Settings",
    ])

    # --------------------------------------------------------
    # Optimization
    # --------------------------------------------------------
    with tabs[0]:
        top1, top2, top3 = st.columns([3.7, 1.7, 1.6])
        with top1:
            st.markdown(
                f'<div class="panel"><div class="small">DATA SOURCE</div>'
                f'<b>🟢 {st.session_state.source_name}</b>'
                f'<br><span class="small">{len(df)} materials loaded</span></div>',
                unsafe_allow_html=True
            )
        with top2:
            if st.button("📂 Upload Excel", use_container_width=True):
                st.session_state.show_uploader = not st.session_state.get("show_uploader", False)
                st.rerun()
        with top3:
            if st.button("🚀 RUN OPTIMIZER", type="primary", use_container_width=True):
                with st.spinner("Running PuLP / CBC optimizer..."):
                    run_optimizer()
                st.rerun()

        if st.session_state.get("show_uploader", False):
            st.markdown('<div class="edit-hint">Optional Excel — standby master chemistry. Built-in chemistry remains active until you choose the uploaded file.</div>', unsafe_allow_html=True)
            up = st.file_uploader("Drag & drop Excel file here", type=["xlsx"], label_visibility="collapsed")
            if up is not None:
                try:
                    loaded = load_chemistry_from_excel(up)
                    if st.button("Use Uploaded Excel as Active Chemistry", type="primary"):
                        set_dataset(loaded, "Uploaded Excel", up.name)
                        st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        if st.session_state.inputs_changed:
            st.markdown('<div class="banner-warn">✏ Inputs changed — click RUN OPTIMIZER to refresh burden, chemistry and cost.</div>', unsafe_allow_html=True)

        result = st.session_state.result

        if result is None or result["blend"] is None:
            st.info("Edit RM Stock / Price / Availability if required, then click RUN OPTIMIZER.")
            return

        r_df = result["df"]
        blend = result["blend"]
        achieved = result["achieved"]
        cost = result["cost"]

        breakdown, total_cost, total_burden = calculate_cost_breakdown(blend, r_df)
        breakdown = ordered_cost(breakdown)
        groups = breakdown.groupby("Group")["kg/t"].sum().reindex(GROUP_ORDER).fillna(0)
        group_costs = breakdown.groupby("Group")["Cost Rs/t"].sum().reindex(GROUP_ORDER).fillna(0)

        # KPI row
        k1,k2,k3,k4,k5 = st.columns(5)
        cost_delta = ""
        if st.session_state.previous_cost is not None and cost is not None:
            d = cost - st.session_state.previous_cost
            cost_delta = f"{'↓' if d < 0 else '↑'} ₹{abs(d):,.2f}/t vs last run"

        cards = [
            ("kpi-blue","TOTAL COST",f"₹ {cost:,.2f} /t","Cost per tonne of sinter"),
            ("kpi-green","TOTAL BURDEN",f"{total_burden:,.1f} kg/t","Total mix per tonne"),
            ("kpi-amber","ACHIEVED Fe",f"{achieved['Fe']:.2f} %",f"Target {FE_LOWER:.1f}–{FE_UPPER:.1f}%"),
            ("kpi-cyan","SOLUTION STATUS","Optimal" if result["status"]=="Optimal" else "Review","Optimization successful" if result["status"]=="Optimal" else "Quality relaxed"),
            ("kpi-purple","TOTAL COST CHANGE",cost_delta or "—","vs last run"),
        ]
        for col, card in zip([k1,k2,k3,k4,k5], cards):
            cls,label,val,sub = card
            with col:
                st.markdown(
                    f'<div class="kpi {cls}"><div class="kpi-label">{label}</div>'
                    f'<div class="kpi-value">{val}</div><div class="kpi-sub">{sub}</div></div>',
                    unsafe_allow_html=True
                )

        quality_banner(achieved)

        # Main content row
        a,b,c = st.columns([1.15,1.0,1.25])

        with a:
            st.markdown('<div class="section">RAW MATERIALS — COMMERCIAL INPUTS</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="edit-hint">✏ <b>Editable:</b> Price (₹/t) • RM Stock (t) • Availability '
                '&nbsp;&nbsp; 🔒 <span style="color:#8998a5">Chemistry / Tech Max read-only</span></div>',
                unsafe_allow_html=True
            )

            rows=[]
            for m in df.index:
                rows.append({
                    "Material":m,
                    "Group":df.loc[m,"Group"],
                    "Available":bool(st.session_state.availability.get(m,True)),
                    "Price (₹/t)":float(df.loc[m,"Price_Rs_t"]),
                    "RM Stock (t)":float(df.loc[m,"Available_Tonnes"]),
                    "Tech Max":float(df.loc[m,"Tech_Max"]),
                    "Status":"Available" if st.session_state.availability.get(m,True) and df.loc[m,"Available_Tonnes"]>0 else "Unavailable",
                })
            commercial=pd.DataFrame(rows)

            edited=st.data_editor(
                commercial,
                hide_index=True,
                use_container_width=True,
                height=365,
                key="commercial_dashboard_editor",
                disabled=["Material","Group","Tech Max","Status"],
                column_config={
                    "Available":st.column_config.CheckboxColumn("Available", help="Toggle whether this material is available for the optimizer."),
                    "Price (₹/t)":st.column_config.NumberColumn("Price (₹/t)", min_value=0, step=1, format="₹ %.0f"),
                    "RM Stock (t)":st.column_config.NumberColumn("RM Stock (t)", min_value=0, step=100, format="%.0f"),
                    "Tech Max":st.column_config.NumberColumn("Tech Max", format="%.0f"),
                }
            )

            changed=False
            for _, row in edited.iterrows():
                m=row["Material"]
                if float(row["Price (₹/t)"]) != float(df.loc[m,"Price_Rs_t"]):
                    df.loc[m,"Price_Rs_t"]=float(row["Price (₹/t)"]); changed=True
                if float(row["RM Stock (t)"]) != float(df.loc[m,"Available_Tonnes"]):
                    df.loc[m,"Available_Tonnes"]=float(row["RM Stock (t)"]); changed=True
                if bool(row["Available"]) != bool(st.session_state.availability.get(m,True)):
                    st.session_state.availability[m]=bool(row["Available"]); changed=True
            if changed:
                st.session_state.inputs_changed=True

        with b:
            st.markdown('<div class="section">BURDEN COMPOSITION (kg/t)</div>', unsafe_allow_html=True)
            chart_df=pd.DataFrame({"Group":GROUP_ORDER,"kg/t":groups.values})
            chart_df["Label"]=chart_df["Group"].map(GROUP_LABEL)
            fig=px.pie(
                chart_df,names="Label",values="kg/t",hole=.58,
                color="Label",
                color_discrete_map={GROUP_LABEL[k]:v for k,v in GROUP_COLORS.items()}
            )
            fig.update_traces(
                textinfo="percent",
                hovertemplate="<b>%{label}</b><br>%{value:.1f} kg/t<br>%{percent}<extra></extra>",
                marker=dict(line=dict(color="#0c1620",width=2))
            )
            fig.update_layout(
                height=315,margin=dict(l=0,r=0,t=0,b=0),
                paper_bgcolor="#0c1620",plot_bgcolor="#0c1620",
                font=dict(color="#dfe8ef"),
                legend=dict(orientation="v",x=.98,y=.5,font=dict(size=10)),
                annotations=[dict(text=f"<b>{total_burden:,.1f}</b><br>kg/t",x=.5,y=.5,showarrow=False,font=dict(size=16,color="#fff"))]
            )
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

        with c:
            st.markdown('<div class="section">FINAL SINTER CHEMISTRY VS TARGET</div>', unsafe_allow_html=True)
            q=quality_display(achieved)
            st.dataframe(q[["KPI","Achieved","Target","Status"]],hide_index=True,use_container_width=True,height=315)

        # Lower row
        a,b,c=st.columns([1.15,1.0,1.25])
        with a:
            st.markdown('<div class="section">RAW MATERIAL CHEMISTRY — INPUT PREVIEW</div>', unsafe_allow_html=True)
            chem=r_df.reset_index()[["Material","Group","Fe","SiO2","Al2O3","CaO","MgO","LOI"]]
            st.dataframe(chem,hide_index=True,use_container_width=True,height=275)

        with b:
            st.markdown('<div class="section">QUALITY CONSTRAINTS STATUS</div>', unsafe_allow_html=True)
            q=quality_display(achieved)
            st.dataframe(q[["KPI","Achieved","Target","Status"]],hide_index=True,use_container_width=True,height=275)

        with c:
            st.markdown('<div class="section">OPTIMAL BURDEN & COST BREAKDOWN</div>', unsafe_allow_html=True)
            show=breakdown.copy()
            show["kg/t"]=show["kg/t"].round(1)
            show["% of Burden"]=show["% of Burden"].round(1)
            show["Cost Rs/t"]=show["Cost Rs/t"].round(0)
            show["% of Cost"]=show["% of Cost"].round(1)
            show=total_row(show,total_burden,total_cost)
            st.dataframe(show,hide_index=True,use_container_width=True,height=290)

        # Cost summary
        st.markdown('<div class="section">COST SUMMARY (₹/t)</div>', unsafe_allow_html=True)
        cost_cards=[
            ("TOTAL COST",total_cost,100,"kpi-blue"),
            ("IRON ORE COST",group_costs["Iron_ore"],group_costs["Iron_ore"]/total_cost*100 if total_cost else 0,"kpi-blue"),
            ("FLUX COST",group_costs["Flux"],group_costs["Flux"]/total_cost*100 if total_cost else 0,"kpi-green"),
            ("RECYCLE COST",group_costs["Recycle"],group_costs["Recycle"]/total_cost*100 if total_cost else 0,"kpi-amber"),
            ("FUEL COST",group_costs["Fuel"],group_costs["Fuel"]/total_cost*100 if total_cost else 0,"kpi-purple"),
        ]
        cols=st.columns(5)
        for col,(label,val,pct,cls) in zip(cols,cost_cards):
            with col:
                st.markdown(
                    f'<div class="kpi {cls}"><div class="kpi-label">{label}</div>'
                    f'<div class="kpi-value">₹ {val:,.2f}</div>'
                    f'<div class="kpi-sub">{pct:.1f}% of total cost</div></div>',
                    unsafe_allow_html=True
                )

    # --------------------------------------------------------
    # Raw Material Chemistry
    # --------------------------------------------------------
    with tabs[1]:
        st.markdown("### Raw Material Chemistry")
        st.caption(f"Source: {st.session_state.source_name}")
        chem=df.reset_index()[["Material","Group","Fe","SiO2","Al2O3","CaO","MgO","LOI","Tech_Min","Tech_Max"]]
        st.dataframe(chem,hide_index=True,use_container_width=True,height=560)
        st.download_button("⬇ Download Active Chemistry",chem.to_csv(index=False).encode(), "active_chemistry.csv","text/csv")

    # --------------------------------------------------------
    # Manual Adjustment
    # --------------------------------------------------------
    with tabs[2]:
        st.markdown("### Manual Burden Adjustment")
        result=st.session_state.result
        if result is None or result["blend"] is None:
            st.warning("Run the optimizer first.")
        else:
            base=result["blend"]; r_df=result["df"]
            adjustable=[m for m in base if r_df.loc[m,"Group"] in ("Iron_ore","Flux")]
            req={}
            cols=st.columns(2)
            for i,m in enumerate(adjustable):
                with cols[i%2]:
                    req[m]=st.number_input(
                        f"{m} — kg/t",
                        min_value=0.0,
                        value=float(base[m]),
                        step=.5,
                        key=f"manual_{m}"
                    )
            if st.button("🔄 Apply Proportional Redistribution",type="primary"):
                st.session_state.adjusted_blend=redistribute_adjustment(base,r_df,req)
            adjusted=st.session_state.adjusted_blend or base
            adj_achieved=compute_achieved(adjusted,r_df,1000)
            adj_breakdown,adj_cost,adj_total=calculate_cost_breakdown(adjusted,r_df)
            m1,m2,m3,m4=st.columns(4)
            m1.metric("Base Cost",f"₹ {result['cost']:,.2f}/t")
            m2.metric("Adjusted Cost",f"₹ {adj_cost:,.2f}/t",f"{adj_cost-result['cost']:+,.2f}")
            m3.metric("Base Fe",f"{result['achieved']['Fe']:.2f}%")
            m4.metric("Adjusted Fe",f"{adj_achieved['Fe']:.2f}%",f"{adj_achieved['Fe']-result['achieved']['Fe']:+.2f}")
            quality_banner(adj_achieved)
            st.dataframe(quality_display(adj_achieved),hide_index=True,use_container_width=True)
            adj_show=ordered_cost(adj_breakdown)
            adj_show=total_row(adj_show,adj_total,adj_cost)
            st.markdown("### Adjusted Burden")
            st.dataframe(adj_show,hide_index=True,use_container_width=True)

    # --------------------------------------------------------
    # What-if
    # --------------------------------------------------------
    with tabs[3]:
        st.markdown("### What-if Analysis")
        st.caption("Test missing Iron Ore / Flux / Fuel scenarios against the current active dataset.")
        if st.button("▶ Run What-if Analysis",type="primary"):
            with st.spinner("Evaluating scenarios..."):
                st.session_state.what_if=what_if_analysis(active_df(),TARGETS)
        if st.session_state.what_if is not None:
            wi=st.session_state.what_if.copy()
            if "Group" in wi.columns:
                wi["_order"]=wi["Group"].map({g:i for i,g in enumerate(GROUP_ORDER)}).fillna(99)
                wi=wi.sort_values(["_order","Missing Material"]).drop(columns="_order")
            st.dataframe(wi,hide_index=True,use_container_width=True)

    # --------------------------------------------------------
    # Bottleneck
    # --------------------------------------------------------
    with tabs[4]:
        st.markdown("### Bottleneck Analysis")
        result=st.session_state.result
        if result is None or result["achieved"] is None:
            st.info("Run the optimizer first.")
        else:
            if result["diagnostics"]:
                for d in result["diagnostics"]:
                    st.warning(d)
            q=quality_display(result["achieved"])
            st.dataframe(q,hide_index=True,use_container_width=True)

    # --------------------------------------------------------
    # Upload / settings
    # --------------------------------------------------------
    with tabs[5]:
        st.markdown("### Upload & Settings")
        st.info("Excel is optional. The built-in master chemistry is the default.")
        uploaded=st.file_uploader("Upload Master Chemistry Excel",type=["xlsx"])
        if uploaded:
            try:
                loaded=load_chemistry_from_excel(uploaded)
                if st.button("Use Uploaded Excel",type="primary"):
                    set_dataset(loaded,"Uploaded Excel",uploaded.name)
                    st.rerun()
            except Exception as exc:
                st.error(str(exc))
        if st.button("Restore Built-in Master Chemistry"):
            set_dataset(get_default_chemistry(),"Built-in Master Chemistry","Built-in Master Chemistry")
            st.rerun()

# ============================================================
# OTHER NAVIGATION PAGES
# ============================================================
def rm_stock_page():
    st.markdown("## RM Stock")
    st.caption("Commercial controls used by the optimizer.")
    st.markdown('<div class="edit-hint">✏ Editable: Price • RM Stock • Availability &nbsp;&nbsp; 🔒 Read-only: Chemistry • Technical Max</div>',unsafe_allow_html=True)

    rows=[]
    for m in df.index:
        rows.append({
            "Material":m,
            "Group":GROUP_LABEL.get(df.loc[m,"Group"],df.loc[m,"Group"]),
            "Available":bool(st.session_state.availability.get(m,True)),
            "Price (₹/t)":float(df.loc[m,"Price_Rs_t"]),
            "RM Stock (t)":float(df.loc[m,"Available_Tonnes"]),
            "Tech Max (kg/t)":float(df.loc[m,"Tech_Max"]),
        })
    ed=st.data_editor(
        pd.DataFrame(rows),hide_index=True,use_container_width=True,height=500,
        key="rm_stock_editor",
        disabled=["Material","Group","Tech Max (kg/t)"],
        column_config={
            "Available":st.column_config.CheckboxColumn("Available",help="OFF means the optimizer cannot use the material."),
            "Price (₹/t)":st.column_config.NumberColumn("Price (₹/t)",min_value=0,step=1,format="₹ %.0f"),
            "RM Stock (t)":st.column_config.NumberColumn("RM Stock (t)",min_value=0,step=100,format="%.0f"),
        }
    )
    changed=False
    for _,row in ed.iterrows():
        m=row["Material"]
        if float(row["Price (₹/t)"]) != float(df.loc[m,"Price_Rs_t"]):
            df.loc[m,"Price_Rs_t"]=float(row["Price (₹/t)"]);changed=True
        if float(row["RM Stock (t)"]) != float(df.loc[m,"Available_Tonnes"]):
            df.loc[m,"Available_Tonnes"]=float(row["RM Stock (t)"]);changed=True
        if bool(row["Available"]) != bool(st.session_state.availability.get(m,True)):
            st.session_state.availability[m]=bool(row["Available"]);changed=True
    if changed:
        st.session_state.inputs_changed=True
        st.markdown('<div class="banner-warn">Inputs changed — return to Dashboard and run the optimizer.</div>',unsafe_allow_html=True)

def cost_page():
    st.markdown("## Cost Composition")
    if not st.session_state.result:
        st.info("Run the optimizer first.")
        return
    result=st.session_state.result
    bd,total_cost,total_burden=calculate_cost_breakdown(result["blend"],result["df"])
    bd=ordered_cost(bd)
    group_cost=bd.groupby("Group")["Cost Rs/t"].sum().reindex(GROUP_ORDER).fillna(0)
    data=pd.DataFrame({"Group":[GROUP_LABEL[g] for g in GROUP_ORDER],"Cost Rs/t":group_cost.values})
    fig=px.pie(data,names="Group",values="Cost Rs/t",hole=.58,color="Group",
               color_discrete_map={GROUP_LABEL[k]:v for k,v in GROUP_COLORS.items()})
    fig.update_layout(height=470,paper_bgcolor="#0c1620",plot_bgcolor="#0c1620",
                      font=dict(color="#dfe8ef"),legend=dict(font=dict(size=11)),
                      annotations=[dict(text=f"<b>₹{total_cost:,.0f}</b><br>₹/t",x=.5,y=.5,showarrow=False,font=dict(size=17,color="#fff"))])
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.dataframe(total_row(
        pd.DataFrame({"Group":[GROUP_LABEL[g] for g in GROUP_ORDER],
                      "Cost Rs/t":group_cost.values,
                      "% of Cost":(group_cost.values/total_cost*100 if total_cost else 0)}),
        total_cost,total_cost
    ),hide_index=True,use_container_width=True)

def burden_page():
    st.markdown("## Burden Composition")
    if not st.session_state.result:
        st.info("Run the optimizer first.")
        return
    result=st.session_state.result
    bd,total_cost,total_burden=calculate_cost_breakdown(result["blend"],result["df"])
    group=bd.groupby("Group")["kg/t"].sum().reindex(GROUP_ORDER).fillna(0)
    data=pd.DataFrame({"Group":[GROUP_LABEL[g] for g in GROUP_ORDER],"kg/t":group.values})
    fig=px.pie(data,names="Group",values="kg/t",hole=.58,color="Group",
               color_discrete_map={GROUP_LABEL[k]:v for k,v in GROUP_COLORS.items()})
    fig.update_layout(height=470,paper_bgcolor="#0c1620",plot_bgcolor="#0c1620",
                      font=dict(color="#dfe8ef"),legend=dict(font=dict(size=11)),
                      annotations=[dict(text=f"<b>{total_burden:,.1f}</b><br>kg/t",x=.5,y=.5,showarrow=False,font=dict(size=17,color="#fff"))])
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    table=pd.DataFrame({"Group":[GROUP_LABEL[g] for g in GROUP_ORDER],"kg/t":group.values})
    table["% of Burden"]=table["kg/t"]/total_burden*100 if total_burden else 0
    st.dataframe(total_row(table,total_burden,total_burden),hide_index=True,use_container_width=True)

def results_page():
    st.markdown("## Optimization Results")
    if not st.session_state.result:
        st.info("Run the optimizer first.")
        return
    result=st.session_state.result
    bd,cost,total=calculate_cost_breakdown(result["blend"],result["df"])
    bd=ordered_cost(bd)
    st.metric("Total Cost",f"₹ {cost:,.2f}/t")
    st.metric("Total Burden",f"{total:,.1f} kg/t")
    quality_banner(result["achieved"])
    st.dataframe(total_row(bd,total,cost),hide_index=True,use_container_width=True)
    st.markdown("### Achieved Chemistry")
    st.dataframe(quality_display(result["achieved"]),hide_index=True,use_container_width=True)

def what_if_page():
    st.markdown("## What-if Analysis")
    if st.button("▶ Evaluate Missing-Material Scenarios",type="primary"):
        with st.spinner("Running scenarios..."):
            st.session_state.what_if=what_if_analysis(active_df(),TARGETS)
    if st.session_state.what_if is not None:
        wi=st.session_state.what_if.copy()
        if "Group" in wi.columns:
            wi["_order"]=wi["Group"].map({g:i for i,g in enumerate(GROUP_ORDER)}).fillna(99)
            wi=wi.sort_values(["_order","Missing Material"]).drop(columns="_order")
        st.dataframe(wi,hide_index=True,use_container_width=True)

def bottleneck_page():
    st.markdown("## Bottleneck Analysis")
    if not st.session_state.result:
        st.info("Run the optimizer first.")
        return
    result=st.session_state.result
    if result["diagnostics"]:
        for d in result["diagnostics"]:
            st.warning(d)
    q=quality_display(result["achieved"])
    st.dataframe(q,hide_index=True,use_container_width=True)

def reports_page():
    st.markdown("## Reports")
    if not st.session_state.result:
        st.info("Run the optimizer first.")
        return
    result=st.session_state.result
    bd,cost,total=calculate_cost_breakdown(result["blend"],result["df"])
    report=pd.DataFrame([{
        "Material":m,
        "Group":result["df"].loc[m,"Group"],
        "kg/t":qty,
        "Price Rs/t":result["df"].loc[m,"Price_Rs_t"],
        "Cost Rs/t":qty*result["df"].loc[m,"Price_Rs_t"]/1000
    } for m,qty in result["blend"].items()])
    st.dataframe(ordered_cost(report),hide_index=True,use_container_width=True)
    st.download_button("⬇ Download Optimization Report",report.to_csv(index=False).encode(),"sinter_optimization_report.csv","text/csv")

def settings_page():
    st.markdown("## Upload & Settings")
    st.markdown("### Active Chemistry Source")
    st.write(f"**{st.session_state.source_name}**")
    uploaded=st.file_uploader("Upload Master Chemistry Excel",type=["xlsx"],key="settings_excel")
    if uploaded:
        try:
            loaded=load_chemistry_from_excel(uploaded)
            if st.button("Activate Uploaded Excel",type="primary"):
                set_dataset(loaded,"Uploaded Excel",uploaded.name)
                st.rerun()
        except Exception as exc:
            st.error(str(exc))
    if st.button("Restore Built-in Master Chemistry"):
        set_dataset(get_default_chemistry(),"Built-in Master Chemistry","Built-in Master Chemistry")
        st.rerun()

# ============================================================
# ROUTING
# ============================================================
if nav == "Dashboard":
    dashboard_page()
elif nav == "RM Stock":
    rm_stock_page()
elif nav == "Cost Composition":
    cost_page()
elif nav == "Burden Composition":
    burden_page()
elif nav == "Optimization Results":
    results_page()
elif nav == "What-if Analysis":
    what_if_page()
elif nav == "Bottleneck Analysis":
    bottleneck_page()
elif nav == "Reports":
    reports_page()
elif nav == "Upload & Settings":
    settings_page()
