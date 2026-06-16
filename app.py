"""
Visor Territorial Agroalimentario — República Dominicana
Fuente: RENAGRO 2024 + Consolidado Regional SC y P 2000–2024
Ministerio de Agricultura de la República Dominicana
"""

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ─────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Visor Territorial Agroalimentario — República Dominicana",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR       = Path("Datos")
RUTA_IND       = BASE_DIR / "indicadores_regionales.parquet"
RUTA_AGG       = BASE_DIR / "consolidado_agg.parquet"
RUTA_NAC       = BASE_DIR / "consolidado_nacional.parquet"
RUTA_REN       = BASE_DIR / "renagro_master.parquet"
RUTA_REGIONES  = BASE_DIR / "regiones_rd.parquet"
RUTA_VIAS      = BASE_DIR / "vias_rd.parquet"

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
    .panel-title {
        color: #F2F5FA; font-size: 1rem; font-weight: 600; margin-bottom: 0.65rem;
    }
    .metric-card {
        background: #171A21; border: 1px solid #2B3240;
        border-radius: 12px; padding: 0.8rem 1rem;
        text-align: center; margin-bottom: 0.8rem;
    }
    .metric-label  { color: #9EABC0; font-size: 0.82rem; margin-bottom: 0.35rem; }
    .metric-value  { color: #FFFFFF; font-size: 2rem; font-weight: 700; line-height: 1.05; }
    .metric-small  { color: #C7D0DD; font-size: 0.8rem; margin-top: 0.25rem; }
    .method-note {
        background: #171A21; border: 1px solid #2B3240;
        border-left: 4px solid #4DA3FF; border-radius: 10px;
        padding: 0.8rem 1rem; color: #C7D0DD;
        font-size: 0.86rem; line-height: 1.55; margin-top: 0.8rem;
    }
    .warn-note {
        background: #1E1A10; border: 1px solid #4A3800;
        border-left: 4px solid #F5A020; border-radius: 10px;
        padding: 0.8rem 1rem; color: #C7B080;
        font-size: 0.86rem; line-height: 1.55; margin-top: 0.8rem;
    }
    .filter-wrap {
        background: #171A21; border: 1px solid #2B3240;
        border-radius: 12px; padding: 0.65rem 0.9rem 0.15rem 0.9rem;
        margin-bottom: 0.85rem;
    }
    .fuente-tag {
        display: inline-block; background: #1A2535; border: 1px solid #2B3240;
        border-radius: 6px; padding: 2px 8px; font-size: 0.75rem;
        color: #6B8CAE; margin-left: 6px;
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

CULTIVOS_RENAGRO = [
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
# Solo indicadores que vienen directo de la fuente (sin índices calculados)
IND_DIRECTOS = {
    "1. Capacidad Productiva": [
        "Productores totales",
        "Superficie agropecuaria total",
        "Superficie promedio por productor",
        "Área sembrada Arroz",
        "Área sembrada Plátano",
        "Área sembrada Cacao",
        "Área sembrada Café",
        "Área sembrada Yuca dulce",
        "Área sembrada Maíz",
        "Área sembrada Caña de azúcar",
        "Área sembrada total cultivos RENAGRO",
        "Producción leche litros/día",
        "Total fuerza laboral agropecuaria",
        "% mujeres en fuerza laboral",
    ],
    "3. Servicios de Apoyo": [
        "Parcelas con asistencia técnica",
        "% parcelas con asistencia técnica",
    ],
    "4. Financiamiento": [
        "Productores con crédito",
        "% productores con crédito",
    ],
    "5. Organización y Vulnerabilidad": [
        "Productores en organización rural",
        "% productores en organización rural",
        "Productores con falta de alimento",
        "% productores con inseguridad alimentaria",
    ],
}
COLORES_REG = [
    "#4DA3FF","#74C69D","#F5A020","#C77DFF","#FF6B6B",
    "#FFD166","#06D6A0","#EF476F","#118AB2","#FFB703",
]
COLOR_VIAS = {
    "motorway":      "#FF6B35",
    "motorway_link": "#FF8C55",
    "trunk":         "#F5A020",
    "trunk_link":    "#F5B840",
    "primary":       "#9EABC0",
    "primary_link":  "#9EABC0",
}

# ─────────────────────────────────────────────────────────────────
# CARGA DE DATOS
# ─────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def cargar_datos():
    ind      = pd.read_parquet(RUTA_IND)
    agg      = pd.read_parquet(RUTA_AGG)
    nac      = pd.read_parquet(RUTA_NAC)
    ren      = pd.read_parquet(RUTA_REN)
    regiones = gpd.read_parquet(RUTA_REGIONES)
    vias     = gpd.read_parquet(RUTA_VIAS)
    return ind, agg, nac, ren, regiones, vias

ind, agg, nac, ren, regiones, vias = cargar_datos()

# Pivot para consultas rápidas (solo indicadores directos de fuente)
@st.cache_data(show_spinner=False)
def build_pivot(ind):
    excluir = ["Score Capacidad Productiva (0-100)","Score Servicios de Apoyo (0-100)",
               "Score Financiamiento (0-100)","Score Organización y Vulnerabilidad (0-100)",
               "Índice de Preparación Territorial (0-100)"]
    return ind[~ind["indicador"].isin(excluir)].pivot_table(
        index=["cod_region","region"], columns="indicador",
        values="valor", aggfunc="first"
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

def fuente_tag(txt):
    return f'<span class="fuente-tag">📋 {txt}</span>'

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

    # ── Filtros ───────────────────────────────────────────────
    st.markdown('<div class="filter-wrap">', unsafe_allow_html=True)
    fc1, fc2, fc3 = st.columns([2, 2, 1])
    with fc1:
        pilar_sel = st.selectbox(
            "Pilar a visualizar",
            options=list(PILAR_LABELS.keys()),
            format_func=lambda x: PILAR_LABELS[x],
            index=0, key="pan_pilar",
        )
    with fc2:
        # Solo indicadores directos de fuente para este pilar
        opciones_ind = IND_DIRECTOS.get(pilar_sel, [])
        # Cruzar con los que realmente existen en el pivot
        opciones_ind = [i for i in opciones_ind if i in pivot.columns]
        ind_sel = st.selectbox("Indicador", opciones_ind, index=0, key="pan_ind")
    with fc3:
        mostrar_vias = st.toggle("Mostrar vías", value=True, key="pan_vias")
    st.markdown("</div>", unsafe_allow_html=True)

    left_col, right_col = st.columns([1.9, 1.1], gap="small")

    with left_col:
        st.markdown(
            f'<div class="panel-title">Mapa regional — {ind_sel} '
            f'{fuente_tag("RENAGRO 2024")}</div>',
            unsafe_allow_html=True,
        )

        # Preparar datos para choropleth
        sub_ind = ind[
            (ind["pilar"] == pilar_sel) & (ind["indicador"] == ind_sel)
        ][["cod_region","valor","unidad"]].copy()

        geo_df = regiones.merge(sub_ind, on="cod_region", how="left")
        geojson = json.loads(geo_df.to_json())

        fig_map = go.Figure()

        # ── Capa 1: polígonos choropleth ──────────────────────
        if not geo_df["valor"].isna().all():
            vmin = geo_df["valor"].min()
            vmax = geo_df["valor"].max()
            for i, row in geo_df.iterrows():
                norm = (row["valor"] - vmin) / (vmax - vmin + 1e-9) if pd.notna(row["valor"]) else 0
                # Color: escala verde oscuro → verde claro (temática agrícola)
                r = int(15  + (45  - 15)  * norm)
                g = int(40  + (160 - 40)  * norm)
                b = int(25  + (80  - 25)  * norm)
                alpha = 0.75
                fill  = f"rgba({r},{g},{b},{alpha})"
                line  = f"rgba(180,220,180,0.9)"
                geom  = row["geometry"]
                val_txt = fmt_num(row["valor"], 1) if pd.notna(row["valor"]) else "Sin dato"
                unit_txt = row.get("unidad","") or ""
                # Nombre limpio
                nombre = row["nombre"]
                hover = f"<b>{nombre}</b><br>{ind_sel}<br>{val_txt} {unit_txt}"
                if geom and geom.geom_type == "MultiPolygon":
                    polys = list(geom.geoms)
                elif geom and geom.geom_type == "Polygon":
                    polys = [geom]
                else:
                    polys = []
                for poly in polys:
                    xs, ys = poly.exterior.xy
                    fig_map.add_trace(go.Scattermapbox(
                        lon=list(xs), lat=list(ys),
                        mode="lines",
                        fill="toself",
                        fillcolor=fill,
                        line=dict(color=line, width=1.2),
                        hovertemplate=hover + "<extra></extra>",
                        showlegend=False,
                        name=nombre,
                    ))

        # ── Capa 2: etiquetas de regiones ────────────────────
        centroids = geo_df.copy()
        centroids["cx"] = geo_df.geometry.centroid.x
        centroids["cy"] = geo_df.geometry.centroid.y
        centroids = centroids.merge(sub_ind, on="cod_region", how="left", suffixes=("","_y"))
        val_col = "valor" if "valor" in centroids.columns else "valor_y"

        fig_map.add_trace(go.Scattermapbox(
            lon=centroids["cx"],
            lat=centroids["cy"],
            mode="markers+text",
            marker=dict(size=6, color="#FFFFFF", opacity=0.6),
            text=centroids["nombre"].str.replace("Cibao ","C.").str.replace("O Metropolitana","Metropolitana"),
            textfont=dict(size=9, color="#E8EDF5"),
            textposition="top right",
            customdata=centroids[[val_col, "unidad_x" if "unidad_x" in centroids.columns else "unidad"]].values
                       if val_col in centroids.columns else None,
            hovertemplate="<b>%{text}</b><br>%{customdata[0]:,.1f} %{customdata[1]}<extra></extra>"
                          if val_col in centroids.columns else None,
            showlegend=False,
        ))

        # ── Capa 3: vías principales ──────────────────────────
        if mostrar_vias:
            for fclass, color in COLOR_VIAS.items():
                sub_v = vias[vias["fclass"] == fclass]
                if sub_v.empty: continue
                width = 2.5 if fclass in ("motorway","trunk") else 1.2
                for geom in sub_v.geometry:
                    if geom is None: continue
                    if geom.geom_type == "MultiLineString":
                        lines = list(geom.geoms)
                    elif geom.geom_type == "LineString":
                        lines = [geom]
                    else:
                        continue
                    for line in lines:
                        xs, ys = line.xy
                        fig_map.add_trace(go.Scattermapbox(
                            lon=list(xs), lat=list(ys),
                            mode="lines",
                            line=dict(color=color, width=width),
                            opacity=0.55,
                            hoverinfo="skip",
                            showlegend=False,
                        ))

        fig_map.update_layout(
            mapbox=dict(
                style="carto-darkmatter",
                center=dict(lat=18.9, lon=-70.2),
                zoom=6.8,
            ),
            paper_bgcolor="#0F1116",
            margin=dict(l=0, r=0, t=0, b=0),
            height=470,
        )
        st.plotly_chart(fig_map, use_container_width=True)

        # Leyenda de vías
        if mostrar_vias:
            st.markdown("""
            <div style="display:flex;gap:14px;flex-wrap:wrap;margin-top:0.3rem;font-size:0.78rem;color:#9EABC0;">
              <span><span style="display:inline-block;width:18px;height:3px;background:#FF6B35;vertical-align:middle;margin-right:4px;"></span>Autopista</span>
              <span><span style="display:inline-block;width:18px;height:3px;background:#F5A020;vertical-align:middle;margin-right:4px;"></span>Troncal</span>
              <span><span style="display:inline-block;width:18px;height:2px;background:#9EABC0;vertical-align:middle;margin-right:4px;"></span>Primaria</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div class="method-note">
            <b>Fuente mapa:</b> Polígonos regionales — ONE/IGN, RD_REG_20220630.
            Vías — OpenStreetMap (Geofabrik, 2024), selección de autopistas, troncales y
            primarias. <b>Indicador:</b> datos directos del RENAGRO 2024,
            Ministerio de Agricultura de la República Dominicana.
        </div>
        """, unsafe_allow_html=True)

    with right_col:
        # Ranking
        st.markdown('<div class="panel-title">Ranking regional</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        if not sub_ind.empty:
            rank_df = sub_ind.merge(
                regiones[["cod_region","nombre"]], on="cod_region", how="left"
            ).sort_values("valor", ascending=False).reset_index(drop=True)
            vmax_r = rank_df["valor"].max()
            for i, row in rank_df.iterrows():
                pct_w = row["valor"] / vmax_r * 100 if vmax_r > 0 else 0
                color = "#74C69D" if i < 3 else "#4DA3FF" if i < 6 else "#9EABC0"
                unit  = row.get("unidad","") or ""
                st.markdown(f"""
                <div style="margin-bottom:0.55rem;">
                  <div style="display:flex;justify-content:space-between;align-items:baseline;">
                    <span style="font-size:0.82rem;color:#C7D0DD;">
                      <b style="color:{color};">#{i+1}</b> {row['nombre']}
                    </span>
                    <span style="font-size:0.85rem;font-weight:600;color:#F0F4FA;">
                      {fmt_num(row['valor'],1)}
                      <span style="font-size:0.72rem;color:#6B7280;">{unit}</span>
                    </span>
                  </div>
                  <div style="background:#1E2530;border-radius:4px;height:6px;margin-top:3px;">
                    <div style="width:{pct_w:.1f}%;height:6px;border-radius:4px;background:{color};"></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Métricas nacionales
        st.markdown(
            '<div class="panel-title" style="margin-top:0.8rem;">'
            'Totales nacionales · RENAGRO 2024</div>',
            unsafe_allow_html=True,
        )
        tot_prod = ren[ren["variable"] == "Productores"]["valor"].sum()
        tot_sup  = ren[ren["variable"] == "Superficie agropecuaria"]["valor"].sum()
        tot_at   = ren[ren["variable"] == "Parcelas con asistencia técnica"]["valor"].sum()
        tot_cred = ren[ren["variable"] == "Productores que recibieron crédito"]["valor"].sum()

        for label, val, unit in [
            ("Productores",          tot_prod, ""),
            ("Sup. agropecuaria",    tot_sup,  "Tareas"),
            ("Parcelas con AT",      tot_at,   ""),
            ("Productores c/crédito",tot_cred, ""),
        ]:
            st.markdown(f"""
            <div class="metric-card">
              <div class="metric-label">{label}</div>
              <div class="metric-value" style="font-size:1.25rem;">{fmt_num(val)}</div>
              <div class="metric-small">{unit}</div>
            </div>""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════
# TAB 2 — PRODUCCIÓN Y ESPECIALIZACIÓN
# ═════════════════════════════════════════════════════════════════

with tab2:

    st.markdown('<div class="filter-wrap">', unsafe_allow_html=True)
    p2c1, p2c2, p2c3 = st.columns([1.5, 1.5, 1])
    with p2c1:
        cultivo_sel = st.selectbox(
            "Cultivo",
            CULTIVOS_RENAGRO + ["Todos los cultivos RENAGRO"],
            index=0, key="prod_cult",
        )
    with p2c2:
        regiones_opts = regiones["nombre"].tolist()
        regiones_sel  = st.multiselect(
            "Filtrar regiones", options=regiones_opts,
            default=[], placeholder="Todas", key="prod_regs",
        )
    with p2c3:
        metrica_sel = st.selectbox(
            "Métrica",
            ["Área sembrada","Área cosechada","Productores","Parcelas"],
            key="prod_met",
        )
    st.markdown("</div>", unsafe_allow_html=True)

    UNIDAD_MAP = {
        "Área sembrada":"Tareas","Área cosechada":"Tareas",
        "Productores":"Número","Parcelas":"Número",
    }

    if cultivo_sel == "Todos los cultivos RENAGRO":
        ren_sub = ren[ren["variable"].str.endswith(f"- {metrica_sel}")].copy()
        ren_sub["cultivo"] = ren_sub["variable"].str.replace(f" - {metrica_sel}","",regex=False)
    else:
        ren_sub = ren[ren["variable"] == f"{cultivo_sel} - {metrica_sel}"].copy()
        ren_sub["cultivo"] = cultivo_sel

    # Agregar nombre legible de región
    ren_sub = ren_sub.merge(regiones[["cod_region","nombre"]], on="cod_region", how="left")
    if regiones_sel:
        ren_sub = ren_sub[ren_sub["nombre"].isin(regiones_sel)]

    lc, rc = st.columns([1.6, 1.4], gap="small")

    with lc:
        if not ren_sub.empty:
            if cultivo_sel == "Todos los cultivos RENAGRO":
                st.markdown(
                    f'<div class="panel-title">Distribución por cultivo y región '
                    f'{fuente_tag("RENAGRO 2024")}</div>',
                    unsafe_allow_html=True,
                )
                fig_tree = px.treemap(
                    ren_sub,
                    path=[px.Constant("República Dominicana"),"cultivo","nombre"],
                    values="valor",
                    color="valor",
                    color_continuous_scale=[[0,"#1A2535"],[0.3,"#2D5986"],[0.7,"#4DA3FF"],[1,"#74C69D"]],
                    custom_data=["cultivo","nombre","valor","unidad"],
                )
                fig_tree.update_traces(
                    hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
                                  "%{customdata[2]:,.0f} %{customdata[3]}<extra></extra>",
                    textfont=dict(size=11),
                )
                fig_tree.update_layout(
                    paper_bgcolor="#171A21",
                    margin=dict(l=0,r=0,t=10,b=0), height=420,
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig_tree, use_container_width=True)
            else:
                st.markdown(
                    f'<div class="panel-title">{metrica_sel} de {cultivo_sel} por región '
                    f'{fuente_tag("RENAGRO 2024")}</div>',
                    unsafe_allow_html=True,
                )
                ren_bar = ren_sub.sort_values("valor", ascending=True)
                fig_bar = go.Figure(go.Bar(
                    x=ren_bar["valor"], y=ren_bar["nombre"], orientation="h",
                    marker=dict(
                        color=ren_bar["valor"],
                        colorscale=[[0,"#1A2535"],[0.5,"#4DA3FF"],[1,"#74C69D"]],
                        line=dict(width=0),
                    ),
                    customdata=ren_bar[["nombre","valor","unidad"]].values,
                    hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]:,.0f} %{customdata[2]}<extra></extra>",
                ))
                fig_bar.update_layout(
                    template="plotly_dark", paper_bgcolor="#171A21", plot_bgcolor="#171A21",
                    margin=dict(l=10,r=10,t=10,b=10), height=360,
                    xaxis=dict(title=f"{metrica_sel} ({UNIDAD_MAP[metrica_sel]})",gridcolor="#2B3240"),
                    yaxis=dict(showgrid=False),
                )
                st.plotly_chart(fig_bar, use_container_width=True)

                # Aprovechamiento cosecha/siembra — solo si la métrica lo permite
                if metrica_sel in ("Área sembrada","Área cosechada") and cultivo_sel != "Todos los cultivos RENAGRO":
                    ap_s = ren[ren["variable"]==f"{cultivo_sel} - Área sembrada"].merge(
                        regiones[["cod_region","nombre"]], on="cod_region", how="left")
                    ap_c = ren[ren["variable"]==f"{cultivo_sel} - Área cosechada"].merge(
                        regiones[["cod_region","nombre"]], on="cod_region", how="left")
                    if not ap_s.empty and not ap_c.empty:
                        ap = ap_s[["cod_region","nombre","valor"]].rename(columns={"valor":"siembra"}).merge(
                            ap_c[["cod_region","valor"]].rename(columns={"valor":"cosecha"}),
                            on="cod_region", how="inner"
                        )
                        ap = ap[ap["siembra"]>0].copy()
                        ap["pct"] = ap["cosecha"] / ap["siembra"] * 100
                        ap = ap.sort_values("pct", ascending=False)

                        st.markdown(
                            f'<div class="panel-title" style="margin-top:0.6rem;">'
                            f'Aprovechamiento — área cosechada / área sembrada '
                            f'{fuente_tag("RENAGRO 2024 — cálculo propio")}</div>',
                            unsafe_allow_html=True,
                        )
                        fig_ap = go.Figure(go.Bar(
                            x=ap["pct"], y=ap["nombre"], orientation="h",
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

                        # Nota especial si es arroz
                        if cultivo_sel == "Arroz":
                            st.markdown("""
                            <div class="warn-note">
                              <b>⚠️ Nota sobre el arroz:</b> Los valores superiores al 100% no indican
                              un error. El arroz en República Dominicana tiene <b>múltiples ciclos de
                              cosecha por año</b> (generalmente 2–3 ciclos anuales). Esto significa que
                              el área cosechada acumula varias cosechas sobre la misma superficie sembrada
                              en el año de referencia del censo, por lo que superar el 100% es
                              agronómicamente correcto y esperado.
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div class="method-note">
                              La línea naranja marca el 100% (toda el área sembrada fue cosechada).
                              Valores inferiores pueden indicar pérdidas, abandono de parcelas o
                              cultivos perennes con siembra y cosecha en diferentes ciclos anuales.
                              <b>Fuente:</b> RENAGRO 2024. <b>Este es un cociente calculado entre
                              dos variables del censo.</b>
                            </div>
                            """, unsafe_allow_html=True)
        else:
            st.info("Sin datos para la selección actual.")

    with rc:
        st.markdown('<div class="panel-title">Especialización territorial</div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        if not ren_sub.empty and cultivo_sel != "Todos los cultivos RENAGRO":
            total_nac = ren_sub["valor"].sum()
            for _, row in ren_sub.sort_values("valor",ascending=False).iterrows():
                pct = row["valor"] / total_nac * 100 if total_nac > 0 else 0
                color = "#74C69D" if pct>=20 else "#4DA3FF" if pct>=10 else "#9EABC0"
                st.markdown(f"""
                <div style="margin-bottom:0.5rem;">
                  <div style="display:flex;justify-content:space-between;">
                    <span style="font-size:0.82rem;color:#C7D0DD;">{row['nombre']}</span>
                    <span style="font-size:0.85rem;font-weight:600;color:{color};">{pct:.1f}%</span>
                  </div>
                  <div style="background:#1E2530;border-radius:4px;height:5px;margin-top:2px;">
                    <div style="width:{pct:.1f}%;height:5px;border-radius:4px;background:{color};"></div>
                  </div>
                  <div style="font-size:0.75rem;color:#6B7280;">{fmt_num(row['valor'])} {row.get('unidad','')}</div>
                </div>""", unsafe_allow_html=True)
            st.markdown(f"""
            <div style="margin-top:0.6rem;padding-top:0.5rem;border-top:1px solid #2B3240;
                color:#6B7280;font-size:0.8rem;">
              Total nacional: {fmt_num(total_nac)} {ren_sub['unidad'].iloc[0] if 'unidad' in ren_sub.columns else ''}
              <br><span style="font-size:0.72rem;">% calculado sobre datos RENAGRO 2024</span>
            </div>""", unsafe_allow_html=True)
        elif cultivo_sel == "Todos los cultivos RENAGRO":
            tot_cult = ren_sub.groupby("cultivo")["valor"].sum().sort_values(ascending=False).head(10)
            tot_all  = tot_cult.sum()
            for cult, val in tot_cult.items():
                pct = val / tot_all * 100 if tot_all > 0 else 0
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
            "Regiones", regiones["nombre"].tolist(),
            default=[], placeholder="Todas", key="hist_regs",
        )
    with t3c3:
        tipo_hist = st.selectbox("Tipo", ["siembra","cosecha"], index=0, key="hist_tipo")
    with t3c4:
        anio_range = st.slider("Período", 2000, 2024, (2000,2024), key="hist_anio")
    st.markdown("</div>", unsafe_allow_html=True)

    # El consolidado usa nombres de región del archivo fuente original
    # que mapeamos a los nombres del shapefile cuando es posible
    NOMBRE_MAP_CONSOLIDADO = {
        "Cibao Norte":  "Cibao Norte",
        "Cibao Sur":    "Cibao Sur",
        "Cibao Nordeste": "Cibao Nordeste",
        "Cibao Noroeste": "Cibao Noroeste",
        "Valdesia":     "Valdesia",
        "Enriquillo":   "Enriquillo",
        "El Valle":     "El Valle",
        "Yuma":         "Yuma",
        "Higuamo":      "Higuamo",
        "Ozama o Metropolitana": "Ozama O Metropolitana",
        "Este (Yuma+Higuamo+Ozama)": "Este (Yuma+Higuamo+Ozama)",
    }

    agg_hist = agg[
        (agg["producto"] == cult_hist) &
        (agg["anio"] >= anio_range[0]) &
        (agg["anio"] <= anio_range[1])
    ].copy()
    if regs_hist:
        # Buscar por nombre original del consolidado
        agg_hist = agg_hist[agg_hist["region"].isin(regs_hist)]

    nac_hist = nac[
        (nac["producto"] == cult_hist) &
        (nac["tipo"] == tipo_hist.upper()) &
        (nac["anio"] >= anio_range[0]) &
        (nac["anio"] <= anio_range[1])
    ].copy()

    h_left, h_right = st.columns([2, 1], gap="small")

    with h_left:
        st.markdown(
            f'<div class="panel-title">Evolución de {tipo_hist} — {cult_hist} '
            f'{fuente_tag("Consolidado SC&P, Min. Agricultura RD")}</div>',
            unsafe_allow_html=True,
        )
        if not agg_hist.empty:
            regiones_datos = sorted(agg_hist["region"].unique())
            color_map_r = {r: COLORES_REG[i%len(COLORES_REG)] for i,r in enumerate(regiones_datos)}
            fig_hist = go.Figure()
            for reg in regiones_datos:
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

        # Heatmap
        st.markdown(
            f'<div class="panel-title" style="margin-top:0.4rem;">Heatmap anual — {cult_hist} '
            f'{fuente_tag("Consolidado SC&P, Min. Agricultura RD")}</div>',
            unsafe_allow_html=True,
        )
        if not agg_hist.empty:
            heat_df = agg_hist.pivot_table(
                index="region", columns="anio", values=tipo_hist, aggfunc="sum"
            ).fillna(0)
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
                margin=dict(l=10,r=10,t=5,b=10), height=240,
                xaxis=dict(showgrid=False, tickangle=-45, tickfont=dict(size=9)),
                yaxis=dict(showgrid=False, tickfont=dict(size=10)),
            )
            st.plotly_chart(fig_heat, use_container_width=True)

        st.markdown("""
        <div class="method-note">
          <b>Fuente:</b> Consolidado Regional de Siembra, Cosecha y Producción de Productos
          Agrícolas 2000–2024. Ministerio de Agricultura, Departamento de Economía Agropecuaria
          y Estadísticas. Unidad: Tareas (1 tarea = 628.86 m²).
          <br><b>Nota sobre regionalización:</b> Esta fuente usa 8 zonas. La región "Este"
          agrupa Yuma + Higuamo + Ozama y no puede desagregarse con los datos disponibles.
        </div>
        """, unsafe_allow_html=True)

    with h_right:
        # Variación acumulada
        st.markdown(
            '<div class="panel-title">Variación acumulada '
            '<span style="font-size:0.75rem;color:#6B7280;font-weight:400;">'
            '(cálculo propio sobre datos fuente)</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        if not agg_hist.empty:
            cambios = []
            for reg in sorted(agg_hist["region"].unique()):
                sub = agg_hist[agg_hist["region"]==reg].sort_values("anio")
                v0s = sub[sub["anio"]==anio_range[0]][tipo_hist].dropna().values
                v1s = sub[sub["anio"]==anio_range[1]][tipo_hist].dropna().values
                if len(v0s) and len(v1s) and v0s[0] > 0:
                    cambios.append({
                        "region":reg,
                        "cambio":(v1s[0]-v0s[0])/v0s[0]*100,
                        "v0":v0s[0],"v1":v1s[0],
                    })
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

# ═════════════════════════════════════════════════════════════════
# TAB 4 — PERFIL POR REGIÓN
# ═════════════════════════════════════════════════════════════════

with tab4:

    p4c1, p4c2 = st.columns([1, 3], gap="medium")

    with p4c1:
        st.markdown('<div class="panel-title">Selecciona una región</div>',
                    unsafe_allow_html=True)
        # Ordenar regiones por número de productores (dato directo)
        prod_by_reg = ren[ren["variable"]=="Productores"][["cod_region","valor"]].sort_values(
            "valor", ascending=False
        )
        opciones_reg = prod_by_reg["cod_region"].tolist()

        region_sel = st.radio(
            "Región",
            options=opciones_reg,
            format_func=lambda c: regiones[regiones["cod_region"]==c]["nombre"].iloc[0]
                                  if len(regiones[regiones["cod_region"]==c])>0 else c,
            label_visibility="collapsed",
            key="perfil_reg",
        )
        # Mini ranking por productores
        for _, row in prod_by_reg.iterrows():
            sel = row["cod_region"] == region_sel
            nom = regiones[regiones["cod_region"]==row["cod_region"]]["nombre"].iloc[0] \
                  if len(regiones[regiones["cod_region"]==row["cod_region"]])>0 else row["cod_region"]
            border = "border-color:#4DA3FF;" if sel else ""
            bg     = "background:#1E2A3A;" if sel else ""
            vmax_p = prod_by_reg["valor"].max()
            pct_w  = row["valor"] / vmax_p * 100 if vmax_p > 0 else 0
            st.markdown(f"""
            <div style="padding:0.35rem 0.6rem;border:1px solid #2B3240;border-radius:8px;
                margin-bottom:3px;{border}{bg}">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-size:0.8rem;color:{'#F0F4FA' if sel else '#9EABC0'};">{nom}</span>
                <span style="font-size:0.78rem;color:#4DA3FF;">{fmt_num(row['valor'])}</span>
              </div>
              <div style="background:#1E2530;border-radius:3px;height:4px;margin-top:3px;">
                <div style="width:{pct_w:.1f}%;height:4px;border-radius:3px;background:#4DA3FF;opacity:0.8;"></div>
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown('<div class="small-note" style="margin-top:0.4rem;">Ordenado por número de productores · RENAGRO 2024</div>',
                    unsafe_allow_html=True)

    with p4c2:
        reg_nombre = regiones[regiones["cod_region"]==region_sel]["nombre"].iloc[0] \
                     if len(regiones[regiones["cod_region"]==region_sel])>0 else region_sel
        reg_ind = ind[ind["cod_region"] == region_sel]

        st.markdown(f'<div class="panel-title" style="font-size:1.2rem;">📍 {reg_nombre}</div>',
                    unsafe_allow_html=True)

        # ── Métricas directas de RENAGRO ──────────────────────
        prod_v  = get_val(region_sel, "Productores totales")
        sup_v   = get_val(region_sel, "Superficie agropecuaria total")
        at_v    = get_val(region_sel, "% parcelas con asistencia técnica")
        cred_v  = get_val(region_sel, "% productores con crédito")
        org_v   = get_val(region_sel, "% productores en organización rural")
        inseg_v = get_val(region_sel, "% productores con inseguridad alimentaria")
        leche_v = get_val(region_sel, "Leche - Producción litros/día")
        mujeres_v = get_val(region_sel, "% mujeres en fuerza laboral")

        m1, m2, m3, m4 = st.columns(4)
        for col, label, val, unit, nota in [
            (m1,"Productores",    prod_v,  "",    "RENAGRO 2024"),
            (m2,"Sup. Agropec.",  sup_v,   "Ta.", "RENAGRO 2024"),
            (m3,"Asist. Técnica", at_v,    "%",   "Parcelas"),
            (m4,"Acceso crédito", cred_v,  "%",   "Productores"),
        ]:
            col.markdown(f"""
            <div class="metric-card">
              <div class="metric-label">{label}</div>
              <div class="metric-value" style="font-size:1.35rem;">{fmt_num(val,1)}</div>
              <div class="metric-small">{unit} · {nota}</div>
            </div>""", unsafe_allow_html=True)

        r_left, r_right = st.columns([1.1, 1.9], gap="small")

        with r_left:
            # Reemplazar radar por panel de indicadores directos con barras
            st.markdown(
                '<div class="panel-title">Indicadores sociales '
                f'{fuente_tag("RENAGRO 2024")}</div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="panel">', unsafe_allow_html=True)

            indicadores_panel = [
                ("Asistencia técnica",    at_v,     100, "#74C69D", "% parcelas"),
                ("Acceso a crédito",      cred_v,   100, "#F5A020", "% productores"),
                ("Organización rural",    org_v,    100, "#4DA3FF", "% productores"),
                ("Inseg. alimentaria",    inseg_v,  100, "#FF6B6B", "% productores"),
                ("Mujeres en trabajo",    mujeres_v,100, "#C77DFF", "% fuerza laboral"),
            ]
            for label, val, escala, color, desc in indicadores_panel:
                w = max(0, min(100, val or 0))
                st.markdown(f"""
                <div style="margin-bottom:0.65rem;">
                  <div style="display:flex;justify-content:space-between;font-size:0.82rem;">
                    <span style="color:#C7D0DD;">{label}</span>
                    <span style="color:{color};font-weight:600;">{fmt_pct(val)}</span>
                  </div>
                  <div style="background:#1E2530;border-radius:3px;height:7px;margin-top:3px;">
                    <div style="width:{w:.1f}%;height:7px;border-radius:3px;background:{color};"></div>
                  </div>
                  <div style="font-size:0.72rem;color:#6B7280;margin-top:1px;">{desc}</div>
                </div>""", unsafe_allow_html=True)

            if not np.isnan(leche_v):
                st.markdown(f"""
                <div class="metric-card" style="margin-top:0.6rem;">
                  <div class="metric-label">Producción de leche</div>
                  <div class="metric-value" style="font-size:1.1rem;">{fmt_num(leche_v)}</div>
                  <div class="metric-small">Litros/día · RENAGRO 2024</div>
                </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with r_right:
            # Donut de cultivos
            st.markdown(
                '<div class="panel-title">Cultivos principales — área sembrada '
                f'{fuente_tag("RENAGRO 2024")}</div>',
                unsafe_allow_html=True,
            )
            cultivos_reg = ren[
                (ren["cod_region"]==region_sel) &
                (ren["variable"].str.endswith("- Área sembrada"))
            ].copy()
            cultivos_reg["cultivo"] = cultivos_reg["variable"].str.replace(
                " - Área sembrada","",regex=False)
            cultivos_reg = cultivos_reg[cultivos_reg["valor"]>0].sort_values(
                "valor",ascending=False)

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
                    margin=dict(l=10,r=10,t=10,b=10), height=240,
                    legend=dict(font=dict(size=9,color="#C7D0DD"),orientation="v",x=1.0,y=0.5),
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            # Tabla limpia — solo indicadores directos de fuente
            st.markdown(
                '<div class="panel-title" style="margin-top:0.4rem;">Datos de fuente por pilar '
                f'{fuente_tag("RENAGRO 2024")}</div>',
                unsafe_allow_html=True,
            )
            # Filtrar: excluir todos los scores e índices calculados
            EXCLUIR_CALCULADOS = {
                "Score Capacidad Productiva (0-100)",
                "Score Servicios de Apoyo (0-100)",
                "Score Financiamiento (0-100)",
                "Score Organización y Vulnerabilidad (0-100)",
                "Índice de Preparación Territorial (0-100)",
                # También excluir % de participación que son derivados
                "% área Arroz en total regional",
                "% área Plátano en total regional",
                "% área Cacao en total regional",
                "% área Café en total regional",
                "% área Yuca dulce en total regional",
                "% área Maíz en total regional",
                "% área Caña de azúcar en total regional",
                "N° cultivos con participación >5%",
                "Relación trabajadores / productores",
                "% leche para autoconsumo",
                "% aprovechamiento Arroz",
                "% aprovechamiento Plátano",
                "% aprovechamiento Cacao",
                "% aprovechamiento Café",
                "% aprovechamiento Yuca dulce",
                "% aprovechamiento Maíz",
            }
            tabla_reg = reg_ind[
                (reg_ind["pilar"] != "0. Índice Compuesto") &
                (~reg_ind["indicador"].isin(EXCLUIR_CALCULADOS))
            ][["pilar","indicador","valor","unidad"]].copy()
            tabla_reg["pilar"] = tabla_reg["pilar"].map(PILAR_LABELS).fillna(tabla_reg["pilar"])
            tabla_reg["valor"] = tabla_reg["valor"].map(
                lambda x: f"{x:,.2f}" if pd.notna(x) else "—")
            tabla_reg.columns = ["Pilar","Indicador","Valor","Unidad"]
            st.dataframe(tabla_reg, use_container_width=True, hide_index=True, height=280)

# ─────────────────────────────────────────────────────────────────
# PIE DE PÁGINA
# ─────────────────────────────────────────────────────────────────

st.markdown("""
<div style="margin-top:1.2rem;padding-top:0.6rem;border-top:1px solid #2B3240;
    color:#4A5568;font-size:0.8rem;text-align:center;">
  Fuente: RENAGRO 2024 · Consolidado Regional SC&amp;P 2000–2024
  · Ministerio de Agricultura de la República Dominicana
  · Cartografía ONE/IGN · Vías OSM/Geofabrik
  | FAO UTF-COL-178 / SARA · Visor Territorial Agroalimentario RD
</div>
""", unsafe_allow_html=True)
