"""
Visor Territorial Agroalimentario — República Dominicana
Sistema de diagnóstico de capacidades productivas regionales
Fuente: RENAGRO 2024 + Consolidado Regional SC y P 2000–2024
Ministerio de Agricultura de la República Dominicana
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ─────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Visor Territorial Agroalimentario — República Dominicana",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR  = Path("Datos")
RUTA_IND  = BASE_DIR / "indicadores_regionales.parquet"
RUTA_AGG  = BASE_DIR / "consolidado_agg.parquet"
RUTA_NAC  = BASE_DIR / "consolidado_nacional.parquet"
RUTA_REN  = BASE_DIR / "renagro_master.parquet"

# ─────────────────────────────────────────────────────────────────
# KEEP-ALIVE
# ─────────────────────────────────────────────────────────────────

st.markdown("""
<script>
(function keepAlive() {
    setInterval(function() {
        fetch(window.location.href, {method:'GET', cache:'no-store'}).catch(function(){});
    }, 45 * 60 * 1000);
})();
</script>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# ESTILO
# ─────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .stApp { background-color: #0F1116; color: #E8EDF5; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    .block-container {
        max-width: 100%; padding-top: 0.8rem; padding-bottom: 1rem;
        padding-left: 1.1rem; padding-right: 1.1rem;
    }
    h1, h2, h3, h4 { color: #E8EDF5 !important; margin-bottom: 0.2rem; }
    .panel {
        background: #171A21; border: 1px solid #2B3240;
        border-radius: 12px; padding: 0.85rem 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.18);
    }
    .panel-title { color: #F2F5FA; font-size: 1rem; font-weight: 600; margin-bottom: 0.65rem; }
    .metric-card {
        background: #171A21; border: 1px solid #2B3240;
        border-radius: 12px; padding: 0.8rem 1rem;
        text-align: center; margin-bottom: 0.8rem;
    }
    .metric-label { color: #9EABC0; font-size: 0.82rem; margin-bottom: 0.35rem; }
    .metric-value { color: #FFFFFF; font-size: 2rem; font-weight: 700; line-height: 1.05; }
    .metric-small { color: #C7D0DD; font-size: 0.8rem; margin-top: 0.25rem; }
    .method-note {
        background: #171A21; border: 1px solid #2B3240;
        border-left: 4px solid #4DA3FF; border-radius: 10px;
        padding: 0.8rem 1rem; color: #C7D0DD;
        font-size: 0.86rem; line-height: 1.55; margin-top: 0.8rem;
    }
    .filter-wrap {
        background: #171A21; border: 1px solid #2B3240;
        border-radius: 12px; padding: 0.65rem 0.9rem 0.15rem 0.9rem;
        margin-bottom: 0.85rem;
    }
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div {
        background-color: #12161D !important; border-color: #2B3240 !important;
    }
    div[data-baseweb="tag"] { background-color: #243042 !important; }
    [data-testid="stPlotlyChart"] {
        background: #171A21; border: 1px solid #2B3240;
        border-radius: 12px; padding: 0.45rem;
    }
    .stDataFrame, div[data-testid="stTable"] {
        background: #171A21; border-radius: 12px;
        border: 1px solid #2B3240; padding: 0.25rem;
    }
    .small-note { color: #99A7BC; font-size: 0.82rem; line-height: 1.45; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────────

REGIONES_COORD = {
    "01": (19.50, -70.65, "Cibao Norte"),
    "02": (18.90, -70.55, "Cibao Sur"),
    "03": (19.30, -69.70, "Cibao Nordeste"),
    "04": (19.60, -71.40, "Cibao Noroeste"),
    "05": (18.45, -70.15, "Valdesia"),
    "06": (18.20, -71.45, "Enriquillo"),
    "07": (18.75, -71.00, "El Valle"),
    "08": (18.70, -68.55, "Yuma"),
    "09": (18.85, -69.50, "Higuamo"),
    "10": (18.48, -69.93, "Ozama o Metropolitana"),
}

CULTIVOS_CLAVE = [
    "Arroz", "Plátano", "Cacao", "Café", "Yuca dulce",
    "Maíz", "Caña de azúcar", "Yuca amarga",
]
CULTIVOS_CONSOLIDADO = [
    "Arroz", "Plátano", "Cacao", "Café", "Yuca", "Maíz",
    "Frijol rojo", "Frijol negro", "Guandúl", "Batata",
    "Aguacate", "Coco", "Guineo/Banano", "Tabaco",
]
PILAR_LABELS = {
    "1. Capacidad Productiva":          "Capacidad Productiva",
    "3. Servicios de Apoyo":            "Servicios de Apoyo",
    "4. Financiamiento":                "Financiamiento",
    "5. Organización y Vulnerabilidad": "Organización y Vulnerabilidad",
}
COLORES_REG = [
    "#4DA3FF","#74C69D","#F5A020","#C77DFF","#FF6B6B",
    "#FFD166","#06D6A0","#EF476F","#118AB2","#FFB703",
]

# ─────────────────────────────────────────────────────────────────
# CARGA DE DATOS
# ─────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def cargar_datos():
    ind = pd.read_parquet(RUTA_IND)
    agg = pd.read_parquet(RUTA_AGG)
    nac = pd.read_parquet(RUTA_NAC)
    ren = pd.read_parquet(RUTA_REN)
    return ind, agg, nac, ren

ind, agg, nac, ren = cargar_datos()

@st.cache_data(show_spinner=False)
def build_pivot(ind):
    return ind.pivot_table(
        index=["cod_region", "region"],
        columns="indicador", values="valor", aggfunc="first"
    ).reset_index()

pivot = build_pivot(ind)
REGIONES_LIST = sorted(ind["cod_region"].unique())

# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────

def fmt_num(v, dec=0):
    if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
    return f"{v:,.{dec}f}"

def fmt_pct(v, dec=1):
    if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
    return f"{v:.{dec}f}%"

def get_val(cod, indicador):
    row = pivot[pivot["cod_region"] == cod]
    if row.empty or indicador not in row.columns: return np.nan
    return row.iloc[0][indicador]

def radar_region(cod_region):
    scores_cols = [
        "Score Capacidad Productiva (0-100)",
        "Score Servicios de Apoyo (0-100)",
        "Score Financiamiento (0-100)",
        "Score Organización y Vulnerabilidad (0-100)",
    ]
    labels = ["Cap. Productiva","Servicios Apoyo","Financiamiento","Org. y Vuln."]
    row = pivot[pivot["cod_region"] == cod_region]
    if row.empty: return go.Figure()
    vals = [float(row.iloc[0].get(c, 0) or 0) for c in scores_cols]
    vals_c  = vals + [vals[0]]
    labels_c = labels + [labels[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals_c, theta=labels_c, fill="toself",
        fillcolor="rgba(77,163,255,0.15)",
        line=dict(color="#4DA3FF", width=2),
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="#171A21", plot_bgcolor="#171A21",
        polar=dict(
            bgcolor="#12161D",
            radialaxis=dict(visible=True, range=[0,100], gridcolor="#2B3240",
                            tickfont=dict(color="#9EABC0", size=9)),
            angularaxis=dict(gridcolor="#2B3240", tickfont=dict(color="#C7D0DD", size=10)),
        ),
        margin=dict(l=25,r=25,t=20,b=20), height=270, showlegend=False,
    )
    return fig

# ─────────────────────────────────────────────────────────────────
# ENCABEZADO
# ─────────────────────────────────────────────────────────────────

st.markdown("""
<div style="background:#0D1117;border-bottom:2px solid #2B3240;padding:10px 20px;
    margin-bottom:0.85rem;margin-left:-1.1rem;margin-right:-1.1rem;margin-top:-0.8rem;
    display:flex;align-items:center;gap:18px;">
  <div style="width:52px;height:52px;border-radius:10px;
      background:linear-gradient(135deg,#006B35,#22A060);
      display:flex;align-items:center;justify-content:center;
      flex-shrink:0;font-size:1.6rem;">🇩🇴</div>
  <div>
    <div style="font-size:1.75rem;font-weight:700;color:#F0F4FA;
        letter-spacing:-0.01em;line-height:1.1;">
      Visor Territorial Agroalimentario &middot; República Dominicana
    </div>
    <div style="font-size:0.88rem;color:#6B7280;margin-top:4px;">
      Diagnóstico de capacidades productivas regionales
      &middot; RENAGRO 2024 + Consolidado SC&amp;P 2000–2024
      &middot; Ministerio de Agricultura
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs([
    "🗺️ Panorama nacional",
    "🌾 Producción y especialización",
    "📈 Series históricas 2000–2024",
    "📋 Perfil por región",
])

# ═════════════════════════════════════════════════════════════════
# TAB 1 — PANORAMA NACIONAL
# ═════════════════════════════════════════════════════════════════

with tab1:

    st.markdown('<div class="filter-wrap">', unsafe_allow_html=True)
    fc1, fc2 = st.columns([2, 2])
    with fc1:
        pilar_sel = st.selectbox(
            "Pilar a visualizar",
            options=list(PILAR_LABELS.keys()),
            format_func=lambda x: PILAR_LABELS[x],
            index=0, key="pan_pilar",
        )
    with fc2:
        ind_pilar = ind[ind["pilar"] == pilar_sel]["indicador"].unique().tolist()
        ind_pct   = [i for i in ind_pilar if "%" in i or "Score" in i or "Índice" in i]
        ind_num   = [i for i in ind_pilar if i not in ind_pct]
        ind_sel   = st.selectbox("Indicador", ind_pct + ind_num, index=0, key="pan_ind")
    st.markdown("</div>", unsafe_allow_html=True)

    left_col, right_col = st.columns([1.6, 1.4], gap="small")

    with left_col:
        st.markdown('<div class="panel-title">Distribución regional — indicador seleccionado</div>',
                    unsafe_allow_html=True)
        sub_ind = ind[(ind["pilar"]==pilar_sel)&(ind["indicador"]==ind_sel)].copy()
        sub_ind["lat"] = sub_ind["cod_region"].map(lambda c: REGIONES_COORD.get(c,(0,0,""))[0])
        sub_ind["lon"] = sub_ind["cod_region"].map(lambda c: REGIONES_COORD.get(c,(0,0,""))[1])
        sub_ind = sub_ind.dropna(subset=["lat","lon","valor"])

        if not sub_ind.empty:
            vmin, vmax = sub_ind["valor"].min(), sub_ind["valor"].max()
            sub_ind["norm"] = (sub_ind["valor"] - vmin) / (vmax - vmin + 1e-9)
            fig_map = go.Figure()
            fig_map.add_trace(go.Scattergeo(
                lat=sub_ind["lat"], lon=sub_ind["lon"],
                mode="markers",
                marker=dict(size=32, color="#1A2535", opacity=0.5),
                hoverinfo="skip", showlegend=False,
            ))
            fig_map.add_trace(go.Scattergeo(
                lat=sub_ind["lat"], lon=sub_ind["lon"],
                mode="markers+text",
                text=sub_ind["region"].str.replace("Cibao ","C.").str.replace("o Metropolitana",""),
                textposition="top center",
                textfont=dict(size=9, color="#C7D0DD"),
                marker=dict(
                    size=sub_ind["norm"]*35+15,
                    color=sub_ind["valor"],
                    colorscale=[[0,"#1A2535"],[0.4,"#2D5986"],[0.7,"#4DA3FF"],[1,"#74C69D"]],
                    showscale=True,
                    colorbar=dict(
                        title=dict(text=ind_sel[:28], font=dict(color="#9EABC0",size=10)),
                        tickfont=dict(color="#9EABC0",size=9),
                        bgcolor="#12161D", bordercolor="#2B3240", len=0.7, y=0.5,
                    ),
                    line=dict(width=1.5, color="#0F1116"),
                    opacity=0.88,
                ),
                customdata=sub_ind[["region","valor","unidad"]].values,
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]:,.2f} %{customdata[2]}<extra></extra>",
                showlegend=False,
            ))
            fig_map.update_layout(
                geo=dict(
                    scope="north america",
                    center=dict(lat=18.9, lon=-70.2),
                    projection_scale=18,
                    bgcolor="#0F1116", showframe=False,
                    showcoastlines=True, coastlinecolor="#2B3240", coastlinewidth=1,
                    showland=True, landcolor="#12161D",
                    showocean=True, oceancolor="#0A0D14",
                    showlakes=True, lakecolor="#0A0D14",
                    showcountries=True, countrycolor="#2B3240",
                ),
                paper_bgcolor="#0F1116",
                margin=dict(l=0,r=0,t=0,b=0), height=420,
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("Sin datos para el indicador seleccionado.")

    with right_col:
        st.markdown('<div class="panel-title">Ranking regional</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        if not sub_ind.empty:
            rank_df = sub_ind[["region","valor","unidad"]].sort_values("valor",ascending=False).reset_index(drop=True)
            vmax_r = rank_df["valor"].max()
            for i, row in rank_df.iterrows():
                pct_w = row["valor"]/vmax_r*100 if vmax_r > 0 else 0
                color = "#74C69D" if i<3 else "#4DA3FF" if i<6 else "#9EABC0"
                st.markdown(f"""
                <div style="margin-bottom:0.55rem;">
                  <div style="display:flex;justify-content:space-between;align-items:baseline;">
                    <span style="font-size:0.82rem;color:#C7D0DD;">
                      <b style="color:{color};">#{i+1}</b> {row['region']}
                    </span>
                    <span style="font-size:0.85rem;font-weight:600;color:#F0F4FA;">
                      {fmt_num(row['valor'],1)}
                      <span style="font-size:0.72rem;color:#6B7280;">{row['unidad']}</span>
                    </span>
                  </div>
                  <div style="background:#1E2530;border-radius:4px;height:6px;margin-top:3px;">
                    <div style="width:{pct_w:.1f}%;height:6px;border-radius:4px;background:{color};"></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel-title" style="margin-top:0.7rem;">Totales nacionales · RENAGRO 2024</div>',
                    unsafe_allow_html=True)
        tot_prod = ren[ren["variable"]=="Productores"]["valor"].sum()
        tot_sup  = ren[ren["variable"]=="Superficie agropecuaria"]["valor"].sum()
        tot_at   = ren[ren["variable"]=="Parcelas con asistencia técnica"]["valor"].sum()
        mc1, mc2, mc3 = st.columns(3)
        for col, label, val, unit in [
            (mc1,"Productores",tot_prod,""),
            (mc2,"Sup. agropecuaria",tot_sup,"Ta."),
            (mc3,"Parcelas con AT",tot_at,""),
        ]:
            col.markdown(f"""
            <div class="metric-card">
              <div class="metric-label">{label}</div>
              <div class="metric-value" style="font-size:1.2rem;">{fmt_num(val)}</div>
              <div class="metric-small">{unit}</div>
            </div>""", unsafe_allow_html=True)

    # ── IPT comparativo ───────────────────────────────────────
    st.markdown('<div class="panel-title" style="margin-top:0.6rem;">Índice de Preparación Territorial — contribución ponderada por pilar</div>',
                unsafe_allow_html=True)
    scores_cols_map = {
        "Score Capacidad Productiva (0-100)":          ("Cap. Productiva",  "#4DA3FF", 0.40),
        "Score Servicios de Apoyo (0-100)":            ("Servicios Apoyo",  "#74C69D", 0.20),
        "Score Financiamiento (0-100)":                ("Financiamiento",   "#F5A020", 0.20),
        "Score Organización y Vulnerabilidad (0-100)": ("Org. y Vuln.",     "#C77DFF", 0.20),
    }
    scores_df = ind[ind["indicador"].isin(scores_cols_map.keys())].pivot_table(
        index=["cod_region","region"], columns="indicador", values="valor", aggfunc="first"
    ).reset_index()
    ipt_df = ind[ind["indicador"]=="Índice de Preparación Territorial (0-100)"][["cod_region","valor"]].rename(columns={"valor":"IPT"})
    scores_df = scores_df.merge(ipt_df, on="cod_region", how="left").sort_values("IPT",ascending=False)

    fig_ipt = go.Figure()
    for col, (label, color, peso) in scores_cols_map.items():
        if col in scores_df.columns:
            y_vals = scores_df[col] * peso
            cd = scores_df[col].values
            fig_ipt.add_trace(go.Bar(
                x=scores_df["region"], y=y_vals, name=label,
                marker_color=color, opacity=0.85,
                customdata=cd,
                hovertemplate=f"<b>%{{x}}</b><br>{label}: %{{customdata:.1f}}<extra></extra>",
            ))
    fig_ipt.update_layout(
        barmode="stack",
        template="plotly_dark", paper_bgcolor="#171A21", plot_bgcolor="#171A21",
        margin=dict(l=10,r=10,t=10,b=10), height=280,
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(title="IPT (contribución ponderada)", gridcolor="#2B3240", range=[0,100]),
        legend=dict(orientation="h", y=1.12, x=0, font=dict(size=10)),
    )
    st.plotly_chart(fig_ipt, use_container_width=True)
    st.markdown("""
    <div class="method-note">
      <b>IPT:</b> Promedio ponderado de cuatro scores normalizados (min-max 0–100):
      Capacidad Productiva (40%), Servicios de Apoyo (20%), Financiamiento (20%)
      y Organización y Vulnerabilidad (20%). Fuente: RENAGRO 2024.
    </div>
    """, unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════
# TAB 2 — PRODUCCIÓN Y ESPECIALIZACIÓN
# ═════════════════════════════════════════════════════════════════

with tab2:

    st.markdown('<div class="filter-wrap">', unsafe_allow_html=True)
    p2c1, p2c2, p2c3 = st.columns([1.5, 1.5, 1])
    with p2c1:
        cultivo_sel = st.selectbox(
            "Cultivo", CULTIVOS_CLAVE + ["Todos los cultivos RENAGRO"],
            index=0, key="prod_cult",
        )
    with p2c2:
        regiones_opts = [REGIONES_COORD[r][2] for r in REGIONES_LIST if r in REGIONES_COORD]
        regiones_sel = st.multiselect(
            "Filtrar regiones", options=regiones_opts,
            default=[], placeholder="Todas", key="prod_regs",
        )
    with p2c3:
        metrica_sel = st.selectbox(
            "Métrica", ["Área sembrada","Área cosechada","Productores","Parcelas"],
            key="prod_met",
        )
    st.markdown("</div>", unsafe_allow_html=True)

    unidad_map = {"Área sembrada":"Tareas","Área cosechada":"Tareas","Productores":"Número","Parcelas":"Número"}

    if cultivo_sel == "Todos los cultivos RENAGRO":
        sufijo = f"- {metrica_sel}"
        ren_sub = ren[ren["variable"].str.endswith(sufijo)].copy()
        ren_sub["cultivo"] = ren_sub["variable"].str.replace(f" - {metrica_sel}","",regex=False)
    else:
        var_q = f"{cultivo_sel} - {metrica_sel}"
        ren_sub = ren[ren["variable"]==var_q].copy()
        ren_sub["cultivo"] = cultivo_sel

    if regiones_sel:
        ren_sub = ren_sub[ren_sub["region"].isin(regiones_sel)]

    lc, rc = st.columns([1.6, 1.4], gap="small")

    with lc:
        if not ren_sub.empty:
            if cultivo_sel == "Todos los cultivos RENAGRO":
                st.markdown('<div class="panel-title">Distribución por cultivo y región</div>',
                            unsafe_allow_html=True)
                fig_tree = px.treemap(
                    ren_sub,
                    path=[px.Constant("República Dominicana"),"cultivo","region"],
                    values="valor",
                    color="valor",
                    color_continuous_scale=[[0,"#1A2535"],[0.3,"#2D5986"],[0.7,"#4DA3FF"],[1,"#74C69D"]],
                    custom_data=["cultivo","region","valor","unidad"],
                )
                fig_tree.update_traces(
                    hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
                                  "%{customdata[2]:,.0f} %{customdata[3]}<extra></extra>",
                    textfont=dict(size=11),
                )
                fig_tree.update_layout(
                    paper_bgcolor="#171A21",
                    margin=dict(l=0,r=0,t=10,b=0), height=430,
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig_tree, use_container_width=True)
            else:
                st.markdown(f'<div class="panel-title">{metrica_sel} de {cultivo_sel} por región</div>',
                            unsafe_allow_html=True)
                ren_bar = ren_sub.sort_values("valor", ascending=True)
                fig_bar = go.Figure(go.Bar(
                    x=ren_bar["valor"], y=ren_bar["region"], orientation="h",
                    marker=dict(
                        color=ren_bar["valor"],
                        colorscale=[[0,"#1A2535"],[0.5,"#4DA3FF"],[1,"#74C69D"]],
                        line=dict(width=0),
                    ),
                    customdata=ren_bar[["region","valor","unidad"]].values,
                    hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]:,.0f} %{customdata[2]}<extra></extra>",
                ))
                fig_bar.update_layout(
                    template="plotly_dark", paper_bgcolor="#171A21", plot_bgcolor="#171A21",
                    margin=dict(l=10,r=10,t=10,b=10), height=360,
                    xaxis=dict(title=f"{metrica_sel} ({unidad_map[metrica_sel]})", gridcolor="#2B3240"),
                    yaxis=dict(showgrid=False),
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Sin datos para la selección actual.")

    with rc:
        st.markdown('<div class="panel-title">Especialización territorial</div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        if not ren_sub.empty and cultivo_sel != "Todos los cultivos RENAGRO":
            total_nac = ren_sub["valor"].sum()
            for _, row in ren_sub.sort_values("valor",ascending=False).iterrows():
                pct = row["valor"]/total_nac*100 if total_nac > 0 else 0
                color = "#74C69D" if pct>=20 else "#4DA3FF" if pct>=10 else "#9EABC0"
                st.markdown(f"""
                <div style="margin-bottom:0.5rem;">
                  <div style="display:flex;justify-content:space-between;">
                    <span style="font-size:0.82rem;color:#C7D0DD;">{row['region']}</span>
                    <span style="font-size:0.85rem;font-weight:600;color:{color};">{pct:.1f}%</span>
                  </div>
                  <div style="background:#1E2530;border-radius:4px;height:5px;margin-top:2px;">
                    <div style="width:{pct:.1f}%;height:5px;border-radius:4px;background:{color};"></div>
                  </div>
                  <div style="font-size:0.75rem;color:#6B7280;">{fmt_num(row['valor'])} {row['unidad']}</div>
                </div>""", unsafe_allow_html=True)
            st.markdown(f"""
            <div style="margin-top:0.6rem;padding-top:0.5rem;border-top:1px solid #2B3240;
                color:#6B7280;font-size:0.8rem;">
              Total nacional: {fmt_num(total_nac)} {ren_sub['unidad'].iloc[0]}
            </div>""", unsafe_allow_html=True)
        elif cultivo_sel == "Todos los cultivos RENAGRO":
            tot_cult = ren_sub.groupby("cultivo")["valor"].sum().sort_values(ascending=False).head(10)
            tot_all  = tot_cult.sum()
            for cult, val in tot_cult.items():
                pct = val/tot_all*100 if tot_all > 0 else 0
                st.markdown(f"""
                <div style="margin-bottom:0.42rem;">
                  <div style="display:flex;justify-content:space-between;">
                    <span style="font-size:0.8rem;color:#C7D0DD;">{cult}</span>
                    <span style="font-size:0.8rem;color:#4DA3FF;">{pct:.1f}%</span>
                  </div>
                  <div style="background:#1E2530;border-radius:3px;height:4px;margin-top:2px;">
                    <div style="width:{pct:.1f}%;height:4px;border-radius:3px;background:#4DA3FF;"></div>
                  </div>
                </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if cultivo_sel != "Todos los cultivos RENAGRO":
            st.markdown('<div class="panel-title" style="margin-top:0.7rem;">Aprovechamiento (cosechado/sembrado)</div>',
                        unsafe_allow_html=True)
            aprov_sub = ren[ren["variable"].isin([
                f"{cultivo_sel} - Área cosechada", f"{cultivo_sel} - Área sembrada"
            ])].copy()
            if not aprov_sub.empty:
                ap = aprov_sub.pivot_table(index="cod_region",columns="variable",values="valor",aggfunc="first").reset_index()
                c_var = f"{cultivo_sel} - Área cosechada"
                s_var = f"{cultivo_sel} - Área sembrada"
                if c_var in ap.columns and s_var in ap.columns:
                    ap["pct"] = ap[c_var]/ap[s_var]*100
                    ap["region"] = ap["cod_region"].map(lambda c: REGIONES_COORD.get(c,(0,0,c))[2])
                    ap = ap.dropna(subset=["pct"]).sort_values("pct",ascending=False)
                    fig_ap = go.Figure(go.Bar(
                        x=ap["pct"], y=ap["region"], orientation="h",
                        marker_color="#4DA3FF", opacity=0.8,
                        hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
                    ))
                    fig_ap.add_vline(x=100, line=dict(color="#F5A020",dash="dash",width=1.5))
                    fig_ap.update_layout(
                        template="plotly_dark", paper_bgcolor="#171A21", plot_bgcolor="#171A21",
                        margin=dict(l=10,r=10,t=5,b=10), height=240,
                        xaxis=dict(title="% cosechado/sembrado",gridcolor="#2B3240"),
                        yaxis=dict(showgrid=False),
                    )
                    st.plotly_chart(fig_ap, use_container_width=True)
                    st.markdown('<div class="small-note">Valores &gt;100% indican ciclos múltiples de cosecha anuales (ej: arroz).</div>',
                                unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════
# TAB 3 — SERIES HISTÓRICAS 2000–2024
# ═════════════════════════════════════════════════════════════════

with tab3:

    st.markdown('<div class="filter-wrap">', unsafe_allow_html=True)
    t3c1, t3c2, t3c3, t3c4 = st.columns([1.5, 1.5, 1.2, 1.2])
    with t3c1:
        cult_hist = st.selectbox("Cultivo", CULTIVOS_CONSOLIDADO, index=0, key="hist_cult")
    with t3c2:
        regs_hist = st.multiselect(
            "Regiones",
            [REGIONES_COORD[r][2] for r in REGIONES_LIST if r in REGIONES_COORD],
            default=[], placeholder="Todas", key="hist_regs",
        )
    with t3c3:
        tipo_hist = st.selectbox("Tipo", ["siembra","cosecha"], index=0, key="hist_tipo")
    with t3c4:
        anio_range = st.slider("Período", 2000, 2024, (2000,2024), key="hist_anio")
    st.markdown("</div>", unsafe_allow_html=True)

    agg_hist = agg[
        (agg["producto"]==cult_hist) &
        (agg["anio"]>=anio_range[0]) &
        (agg["anio"]<=anio_range[1])
    ].copy()
    if regs_hist:
        agg_hist = agg_hist[agg_hist["region"].isin(regs_hist)]

    nac_hist = nac[
        (nac["producto"]==cult_hist) &
        (nac["tipo"]==tipo_hist.upper()) &
        (nac["anio"]>=anio_range[0]) &
        (nac["anio"]<=anio_range[1])
    ].copy()

    h_left, h_right = st.columns([2, 1], gap="small")

    with h_left:
        st.markdown(f'<div class="panel-title">Evolución de {tipo_hist} — {cult_hist}</div>',
                    unsafe_allow_html=True)
        if not agg_hist.empty:
            regiones_en_datos = sorted(agg_hist["region"].unique())
            color_map_r = {r: COLORES_REG[i%len(COLORES_REG)] for i,r in enumerate(regiones_en_datos)}
            fig_hist = go.Figure()
            for reg in regiones_en_datos:
                sub = agg_hist[agg_hist["region"]==reg].sort_values("anio")
                vals = sub[tipo_hist] if tipo_hist in sub.columns else pd.Series(dtype=float)
                if vals.dropna().empty: continue
                fig_hist.add_trace(go.Scatter(
                    x=sub["anio"], y=vals, mode="lines+markers", name=reg,
                    line=dict(color=color_map_r[reg], width=2),
                    marker=dict(size=5, color=color_map_r[reg]),
                    hovertemplate=f"<b>{reg}</b><br>%{{x}}: %{{y:,.0f}} Ta.<extra></extra>",
                ))
            if not nac_hist.empty:
                fig_hist.add_trace(go.Scatter(
                    x=nac_hist["anio"], y=nac_hist["valor_nacional"],
                    mode="lines", name="Total nacional",
                    line=dict(color="#FFD166",width=2,dash="dash"),
                    yaxis="y2",
                    hovertemplate="Nacional: %{y:,.0f} Ta.<extra></extra>",
                ))
            fig_hist.update_layout(
                template="plotly_dark", paper_bgcolor="#171A21", plot_bgcolor="#171A21",
                margin=dict(l=10,r=10,t=10,b=10), height=400,
                xaxis=dict(showgrid=False, dtick=2),
                yaxis=dict(title="Tareas (región)", gridcolor="#2B3240"),
                yaxis2=dict(title="Tareas (nacional)", overlaying="y", side="right",
                            showgrid=False, tickfont=dict(color="#FFD166")),
                legend=dict(orientation="h", y=1.1, x=0, font=dict(size=9)),
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Sin datos para la selección.")

    with h_right:
        st.markdown('<div class="panel-title">Variación acumulada</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        if not agg_hist.empty:
            cambios = []
            for reg in sorted(agg_hist["region"].unique()):
                sub = agg_hist[agg_hist["region"]==reg].sort_values("anio")
                v0s = sub[sub["anio"]==anio_range[0]][tipo_hist].dropna().values
                v1s = sub[sub["anio"]==anio_range[1]][tipo_hist].dropna().values
                if len(v0s) and len(v1s) and v0s[0]>0:
                    cambios.append({"region":reg,"cambio":(v1s[0]-v0s[0])/v0s[0]*100,"v0":v0s[0],"v1":v1s[0]})
            if cambios:
                for row in sorted(cambios, key=lambda x: -x["cambio"]):
                    color = "#74C69D" if row["cambio"]>=0 else "#FF6B6B"
                    signo = "+" if row["cambio"]>=0 else ""
                    st.markdown(f"""
                    <div style="margin-bottom:0.5rem;">
                      <div style="display:flex;justify-content:space-between;">
                        <span style="font-size:0.8rem;color:#C7D0DD;">{row['region']}</span>
                        <span style="font-size:0.85rem;font-weight:600;color:{color};">
                          {signo}{row['cambio']:.1f}%
                        </span>
                      </div>
                      <div style="font-size:0.72rem;color:#6B7280;">
                        {fmt_num(row['v0'])} → {fmt_num(row['v1'])} Ta.
                      </div>
                    </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        if not nac_hist.empty:
            v0n = nac_hist[nac_hist["anio"]==anio_range[0]]["valor_nacional"].values
            v1n = nac_hist[nac_hist["anio"]==anio_range[1]]["valor_nacional"].values
            if len(v0n) and len(v1n) and v0n[0]>0:
                cn = (v1n[0]-v0n[0])/v0n[0]*100
                color_n = "#74C69D" if cn>=0 else "#FF6B6B"
                st.markdown(f"""
                <div class="metric-card" style="margin-top:0.6rem;">
                  <div class="metric-label">Cambio nacional {tipo_hist}</div>
                  <div class="metric-value" style="font-size:1.6rem;color:{color_n};">
                    {'+' if cn>=0 else ''}{cn:.1f}%
                  </div>
                  <div class="metric-small">{anio_range[0]} → {anio_range[1]}</div>
                </div>""", unsafe_allow_html=True)

    st.markdown(f'<div class="panel-title" style="margin-top:0.6rem;">Heatmap anual — {cult_hist}</div>',
                unsafe_allow_html=True)
    if not agg_hist.empty:
        heat_df = agg_hist.pivot_table(index="region",columns="anio",values=tipo_hist,aggfunc="sum").fillna(0)
        fig_heat = go.Figure(go.Heatmap(
            z=heat_df.values,
            x=[str(c) for c in heat_df.columns],
            y=heat_df.index.tolist(),
            colorscale=[[0,"#0F1116"],[0.2,"#1A2535"],[0.5,"#2D5986"],[0.8,"#4DA3FF"],[1,"#74C69D"]],
            hovertemplate="Región: %{y}<br>Año: %{x}<br>%{z:,.0f} Ta.<extra></extra>",
            colorbar=dict(tickfont=dict(color="#9EABC0",size=9),bgcolor="#12161D",bordercolor="#2B3240"),
        ))
        fig_heat.update_layout(
            template="plotly_dark", paper_bgcolor="#171A21", plot_bgcolor="#171A21",
            margin=dict(l=10,r=10,t=5,b=10), height=255,
            xaxis=dict(showgrid=False, tickangle=-45, tickfont=dict(size=9)),
            yaxis=dict(showgrid=False, tickfont=dict(size=10)),
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("""
    <div class="method-note">
      <b>Nota sobre regionalización:</b> Los datos 2000–2024 usan 8 zonas del Consolidado
      (Norte, Nordeste, Noroeste, Norcentral, Central, Sur, Suroeste, Este).
      La región "Este" agrupa Yuma + Higuamo + Ozama y no puede desagregarse en esta fuente.
    </div>
    """, unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════
# TAB 4 — PERFIL POR REGIÓN
# ═════════════════════════════════════════════════════════════════

with tab4:

    p4c1, p4c2 = st.columns([1, 3], gap="medium")

    with p4c1:
        st.markdown('<div class="panel-title">Selecciona una región</div>', unsafe_allow_html=True)
        ipt_vals = ind[ind["indicador"]=="Índice de Preparación Territorial (0-100)"][
            ["cod_region","region","valor"]
        ].sort_values("valor",ascending=False)

        region_sel = st.radio(
            "Región",
            options=ipt_vals["cod_region"].tolist(),
            format_func=lambda c: ipt_vals[ipt_vals["cod_region"]==c]["region"].iloc[0],
            label_visibility="collapsed",
            key="perfil_reg",
        )
        for _, row in ipt_vals.iterrows():
            sel = row["cod_region"] == region_sel
            border = "border-color:#4DA3FF;" if sel else ""
            bg     = "background:#1E2A3A;" if sel else ""
            st.markdown(f"""
            <div style="padding:0.35rem 0.6rem;border:1px solid #2B3240;border-radius:8px;
                margin-bottom:3px;{border}{bg}">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-size:0.8rem;color:{'#F0F4FA' if sel else '#9EABC0'};">
                  {row['region']}
                </span>
                <span style="font-size:0.8rem;font-weight:600;color:#FFD166;">
                  {row['valor']:.0f}
                </span>
              </div>
              <div style="background:#1E2530;border-radius:3px;height:4px;margin-top:3px;">
                <div style="width:{row['valor']:.1f}%;height:4px;border-radius:3px;
                    background:#FFD166;opacity:0.8;"></div>
              </div>
            </div>""", unsafe_allow_html=True)

    with p4c2:
        reg_nombre = ipt_vals[ipt_vals["cod_region"]==region_sel]["region"].iloc[0]
        reg_ind = ind[ind["cod_region"]==region_sel]

        st.markdown(f'<div class="panel-title" style="font-size:1.2rem;">📍 {reg_nombre}</div>',
                    unsafe_allow_html=True)

        ipt_v   = get_val(region_sel, "Índice de Preparación Territorial (0-100)")
        prod_v  = get_val(region_sel, "Productores totales")
        sup_v   = get_val(region_sel, "Superficie agropecuaria total")
        at_v    = get_val(region_sel, "% parcelas con asistencia técnica")
        cred_v  = get_val(region_sel, "% productores con crédito")
        org_v   = get_val(region_sel, "% productores en organización rural")
        inseg_v = get_val(region_sel, "% productores con inseguridad alimentaria")
        leche_v = get_val(region_sel, "Leche - Producción litros/día")

        m1, m2, m3, m4 = st.columns(4)
        for col, label, val, unit, note in [
            (m1,"IPT",         ipt_v,   "/ 100", "Índice compuesto"),
            (m2,"Productores", prod_v,  "",      "Total RENAGRO"),
            (m3,"Sup. Agrop.", sup_v,   "Ta.",   "Total"),
            (m4,"Asist. Téc.", at_v,    "%",     "Parcelas"),
        ]:
            col.markdown(f"""
            <div class="metric-card">
              <div class="metric-label">{label}</div>
              <div class="metric-value" style="font-size:1.35rem;">{fmt_num(val,1)}</div>
              <div class="metric-small">{unit} · {note}</div>
            </div>""", unsafe_allow_html=True)

        r_left, r_right = st.columns([1.1, 1.9], gap="small")

        with r_left:
            st.markdown('<div class="panel-title">Perfil de capacidades</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(radar_region(region_sel), use_container_width=True)
            for label, val, color in [
                ("Asistencia técnica", at_v,    "#74C69D"),
                ("Acceso a crédito",   cred_v,  "#F5A020"),
                ("Organización rural", org_v,   "#4DA3FF"),
                ("Inseg. alimentaria", inseg_v, "#FF6B6B"),
            ]:
                w = max(0, min(100, val or 0))
                st.markdown(f"""
                <div style="margin-bottom:0.4rem;">
                  <div style="display:flex;justify-content:space-between;font-size:0.8rem;">
                    <span style="color:#9EABC0;">{label}</span>
                    <span style="color:{color};font-weight:600;">{fmt_pct(val)}</span>
                  </div>
                  <div style="background:#1E2530;border-radius:3px;height:5px;margin-top:2px;">
                    <div style="width:{w:.1f}%;height:5px;border-radius:3px;background:{color};"></div>
                  </div>
                </div>""", unsafe_allow_html=True)
            if not np.isnan(leche_v):
                st.markdown(f"""
                <div class="metric-card" style="margin-top:0.6rem;">
                  <div class="metric-label">Producción leche</div>
                  <div class="metric-value" style="font-size:1.1rem;">{fmt_num(leche_v)}</div>
                  <div class="metric-small">Litros/día</div>
                </div>""", unsafe_allow_html=True)

        with r_right:
            st.markdown('<div class="panel-title">Cultivos principales — área sembrada (RENAGRO 2024)</div>',
                        unsafe_allow_html=True)
            cultivos_reg = ren[
                (ren["cod_region"]==region_sel) &
                (ren["variable"].str.endswith("- Área sembrada"))
            ].copy()
            cultivos_reg["cultivo"] = cultivos_reg["variable"].str.replace(" - Área sembrada","",regex=False)
            cultivos_reg = cultivos_reg[cultivos_reg["valor"]>0].sort_values("valor",ascending=False)

            if not cultivos_reg.empty:
                COLORES_CULT = ["#4DA3FF","#74C69D","#F5A020","#C77DFF","#FF6B6B",
                                "#FFD166","#06D6A0","#EF476F"]
                fig_pie = go.Figure(go.Pie(
                    labels=cultivos_reg["cultivo"],
                    values=cultivos_reg["valor"],
                    hole=0.45,
                    marker=dict(
                        colors=COLORES_CULT[:len(cultivos_reg)],
                        line=dict(color="#0F1116",width=2),
                    ),
                    textfont=dict(size=10,color="#E8EDF5"),
                    hovertemplate="<b>%{label}</b><br>%{value:,.0f} Ta.<br>%{percent}<extra></extra>",
                ))
                fig_pie.update_layout(
                    paper_bgcolor="#171A21",
                    margin=dict(l=10,r=10,t=10,b=10), height=255,
                    legend=dict(font=dict(size=9,color="#C7D0DD"),orientation="v",x=1.0,y=0.5),
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            st.markdown('<div class="panel-title" style="margin-top:0.4rem;">Todos los indicadores</div>',
                        unsafe_allow_html=True)
            tabla_reg = reg_ind[reg_ind["pilar"]!="0. Índice Compuesto"][
                ["pilar","indicador","valor","unidad"]
            ].copy()
            tabla_reg["pilar"] = tabla_reg["pilar"].map(PILAR_LABELS).fillna(tabla_reg["pilar"])
            tabla_reg["valor"] = tabla_reg["valor"].map(lambda x: f"{x:,.2f}" if pd.notna(x) else "—")
            tabla_reg.columns = ["Pilar","Indicador","Valor","Unidad"]
            st.dataframe(tabla_reg, use_container_width=True, hide_index=True, height=300)

# ─────────────────────────────────────────────────────────────────
# PIE DE PÁGINA
# ─────────────────────────────────────────────────────────────────

st.markdown("""
<div style="margin-top:1.2rem;padding-top:0.6rem;border-top:1px solid #2B3240;
    color:#4A5568;font-size:0.8rem;text-align:center;">
  Fuente: RENAGRO 2024 · Consolidado Regional SC&amp;P 2000–2024
  · Ministerio de Agricultura de la República Dominicana
  | FAO UTF-COL-178 / SARA · Visor Territorial Agroalimentario RD
</div>
""", unsafe_allow_html=True)
