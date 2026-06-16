"""
Visor Territorial Agroalimentario — República Dominicana
Fuente: RENAGRO 2024 + Consolidado Regional SC y P 2000-2024
Ministerio de Agricultura de la República Dominicana
"""

import json
from pathlib import Path

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
RUTA_VIAS_JSON = BASE_DIR / "vias_coords.json"
RUTA_REG_JSON  = BASE_DIR / "regiones_coords.json"

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
    .stDataFrame { background: #171A21; border-radius: 12px;
        border: 1px solid #2B3240; padding: 0.25rem; }
    .small-note { color: #99A7BC; font-size: 0.82rem; line-height: 1.45; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────────

# Cultivos con datos en RENAGRO 2024 por región (nombres exactos del parquet)
CULTIVOS_RENAGRO_VARS = [
    "Arroz","Plátano","Cacao","Café","Yuca dulce",
    "Maíz","Caña de azúcar","Yuca amarga",
]
# Productos con datos reales en el consolidado (>= 5 anos de siembra)
CULTIVOS_CONSOLIDADO = sorted([
    "Aguacate","Ajo","Ajies","Arroz","Auyama","Berenjena","Batata",
    "Cebolla","Frijol rojo","Frijol blanco","Frijol negro","Coco",
    "Chinola","Guineo","Lechosa","Guandul","Sorgo","Yuca","Zanahoria",
    "Yautia","Toronja","Naranja dulce","Papa","Pina","Pepino","Platano",
    "Melon","Maiz","Mani","Name","Tayota","Tomate ensalada","Repollo",
    "Tomate industrial","Tindora","Rabano","Remolacha","Lechuga",
    "Coliflor","Cundeamor","Brocoli","Limon agrio","Molondron","Oregano",
    "Mandarina","Pitahaya","Guanabana","Guayaba","Granadillo","Apio",
    "Bangana","Calabacin","Cereza","Mango","Mapuey","Sandia","Zapote",
])
PILAR_LABELS = {
    "1. Capacidad Productiva":          "Capacidad Productiva",
    "2. Uso del suelo":                 "Uso del suelo",
    "3. Servicios de Apoyo":            "Servicios de Apoyo",
    "4. Financiamiento":                "Financiamiento",
    "5. Organización y Vulnerabilidad": "Organización y Vulnerabilidad",
    "6. Precenso RENAGRO 2024":         "Perfil productor (Precenso)",
}
IND_DIRECTOS = {
    "1. Capacidad Productiva": [
        "Productores totales",
        "Superficie agropecuaria total",
        "Área sembrada total cultivos RENAGRO",
        "Producción leche litros/día",
        "Total fuerza laboral agropecuaria",
        "% mujeres en fuerza laboral",
        "Trabajadores hombres permanentes",
        "Trabajadores mujeres permanentes",
        "Trabajadores hombres temporales",
        "Trabajadores mujeres temporales",
    ],
    "2. Uso del suelo": [
        "Sembradas - Cultivos temporeros",
        "Sembradas - Cultivos permanentes",
        "Sembradas - Pasto para el ganado",
        "Dedicadas - Pastos naturales",
        "Dedicadas - Bosques sembrados",
        "Dedicadas - Montes y bosques naturales",
        "Sin siembra - Menos de 1 año",
        "Sin siembra - Más de 1 año",
        "Sin usos productivos o áreas marginales",
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
    "6. Precenso RENAGRO 2024": [
        "% titulares mujeres",
        "% agricultores familiares (criterio FAO)",
        "% agricultores familiares (criterio RD)",
        "% pequeños productores",
        "% medianos productores",
        "% productores propietarios",
        "% productores arrendatarios",
        "% actividad principal Agricultura",
        "% actividad principal Ganadería",
        "% actividad principal Agropecuario mixto",
        "Mediana tamaño UA (ha)",
        "% UA menores de 1 ha",
        "% UA de 1 a 10 ha",
        "% UA mayores de 10 ha",
        "Total unidades agropecuarias en precenso",
        "Municipios cubiertos en precenso",
    ],
}
EXCLUIR_CALCULADOS = {
    "Score Capacidad Productiva (0-100)",
    "Score Servicios de Apoyo (0-100)",
    "Score Financiamiento (0-100)",
    "Score Organizacion y Vulnerabilidad (0-100)",
    "Indice de Preparacion Territorial (0-100)",
    "% area Arroz en total regional",
    "% area Platano en total regional",
    "% area Cacao en total regional",
    "% area Cafe en total regional",
    "% area Yuca dulce en total regional",
    "% area Maiz en total regional",
    "% area Cana de azucar en total regional",
    "N cultivos con participacion >5%",
    "Relacion trabajadores / productores",
    "% leche para autoconsumo",
    "% aprovechamiento Arroz",
    "% aprovechamiento Platano",
    "% aprovechamiento Cacao",
    "% aprovechamiento Cafe",
    "% aprovechamiento Yuca dulce",
    "% aprovechamiento Maiz",
    "Superficie promedio por productor",
}
COLORES_REG = [
    "#4DA3FF","#74C69D","#F5A020","#C77DFF","#FF6B6B",
    "#FFD166","#06D6A0","#EF476F","#118AB2","#FFB703",
]
COLOR_VIAS = {
    "motorway":      ("#FF6B35", 2.5),
    "motorway_link": ("#FF8C55", 1.5),
    "trunk":         ("#F5A020", 2.0),
    "trunk_link":    ("#F5B840", 1.2),
    "primary":       ("#9EABC0", 1.2),
    "primary_link":  ("#B0BCCC", 0.9),
}

# ─────────────────────────────────────────────────────────────────
# CARGA DE DATOS
# ─────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def cargar_datos():
    ind  = pd.read_parquet(RUTA_IND)
    agg  = pd.read_parquet(RUTA_AGG)
    nac  = pd.read_parquet(RUTA_NAC)
    ren  = pd.read_parquet(RUTA_REN)
    with open(RUTA_VIAS_JSON)  as f: vias_json = json.load(f)
    with open(RUTA_REG_JSON)   as f: reg_json  = json.load(f)
    return ind, agg, nac, ren, vias_json, reg_json

ind, agg, nac, ren, vias_json, reg_json = cargar_datos()

# Lista de productos con datos reales en el consolidado
@st.cache_data(show_spinner=False)
def productos_con_datos(agg):
    return sorted(
        agg[agg["siembra"] > 0]
        .groupby("producto")["anio"].nunique()
        .reset_index()
        .query("anio >= 5")["producto"]
        .tolist()
    )

PRODS_VALIDOS = productos_con_datos(agg)

@st.cache_data(show_spinner=False)
def build_pivot(ind):
    return ind[~ind["indicador"].isin(EXCLUIR_CALCULADOS)].pivot_table(
        index=["cod_region","region"], columns="indicador",
        values="valor", aggfunc="first"
    ).reset_index()

pivot         = build_pivot(ind)
NOMBRES_REG   = {cod: d["nombre"] for cod, d in reg_json.items()}

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

def ftag(txt):
    return f'<span class="fuente-tag">{txt}</span>'

def unit_label(unidad):
    """Etiqueta legible para la unidad."""
    MAP = {
        "Hectareas": "Ha",
        "Hectáreas": "Ha",
        "Numero":    "",
        "Número":    "",
        "%":         "%",
        "Litros/dia":"L/dia",
        "Litros/día":"L/dia",
        "Personas":  "personas",
        "Ha/productor":"Ha/prod.",
    }
    return MAP.get(unidad, unidad or "")

# ─────────────────────────────────────────────────────────────────
# MAPA (cacheado por indicador + vias)
# max 17 traces: 10 regiones + 1 centroides + 6 clases de vias
# Escala verde -> amarillo -> rojo (mayor = verde, menor = rojo)
# ─────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def build_mapa(ind_sel, pilar_sel, mostrar_vias):
    sub = ind[
        (ind["pilar"] == pilar_sel) & (ind["indicador"] == ind_sel)
    ][["cod_region","valor","unidad"]].set_index("cod_region")

    vmin = sub["valor"].min()
    vmax = sub["valor"].max()
    unidad = sub["unidad"].iloc[0] if not sub.empty else ""
    ul = unit_label(unidad)

    fig = go.Figure()

    # -- Poligonos: un trace por region --
    for cod, d in reg_json.items():
        val  = sub.loc[cod, "valor"] if cod in sub.index else np.nan
        norm = (val - vmin) / (vmax - vmin + 1e-9) if pd.notna(val) else 0.5

        # Verde -> amarillo -> rojo  (norm=1 verde, norm=0 rojo)
        if norm >= 0.5:
            t = (norm - 0.5) * 2          # 0->0.5 en [0,1]
            r = int(255 * (1 - t))
            g = int(180 + (75 * t))       # 180->255
            b = int(20  * (1 - t))
        else:
            t = norm * 2                   # 0->1 en [0,1]
            r = int(220 - (20 * t))        # 220->200
            g = int(50  + (130 * t))       # 50->180
            b = 15
        fill_color = f"rgba({r},{g},{b},0.78)"

        val_txt = f"{val:,.1f} {ul}" if pd.notna(val) else "Sin dato"
        hover   = f"<b>{d['nombre']}</b><br>{ind_sel}<br>{val_txt}"

        fig.add_trace(go.Scattermapbox(
            lon=d["lons"], lat=d["lats"],
            mode="lines", fill="toself",
            fillcolor=fill_color,
            line=dict(color="rgba(220,230,220,0.6)", width=0.9),
            hovertemplate=hover + "<extra></extra>",
            showlegend=False, name=d["nombre"],
        ))

    # -- Centroides con etiquetas --
    cx_l, cy_l, txt_l, hov_l = [], [], [], []
    for cod, d in reg_json.items():
        val  = sub.loc[cod, "valor"] if cod in sub.index else np.nan
        cx_l.append(d["cx"])
        cy_l.append(d["cy"])
        txt_l.append(d["nombre"].replace("Cibao ","C.").replace("O Metropolitana","Metro"))
        hov_l.append(f"<b>{d['nombre']}</b><br>{fmt_num(val,1)} {ul}")

    fig.add_trace(go.Scattermapbox(
        lon=cx_l, lat=cy_l,
        mode="markers+text",
        marker=dict(size=5, color="rgba(255,255,255,0.5)"),
        text=txt_l,
        textfont=dict(size=9, color="#E8EDF5"),
        textposition="top right",
        hovertemplate=[h + "<extra></extra>" for h in hov_l],
        showlegend=False, name="Regiones",
    ))

    # -- Vias --
    if mostrar_vias:
        for fclass, (color, width) in COLOR_VIAS.items():
            if fclass not in vias_json: continue
            dv = vias_json[fclass]
            fig.add_trace(go.Scattermapbox(
                lon=dv["lons"], lat=dv["lats"],
                mode="lines",
                line=dict(color=color, width=width),
                opacity=0.5, hoverinfo="skip",
                showlegend=False, name=fclass,
            ))

    fig.update_layout(
        mapbox=dict(style="carto-darkmatter",
                    center=dict(lat=18.9, lon=-70.2), zoom=6.8),
        paper_bgcolor="#0F1116",
        margin=dict(l=0, r=0, t=0, b=0), height=455,
    )
    return fig, ul

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
      flex-shrink:0;font-size:1.6rem;">RD</div>
  <div>
    <div style="font-size:1.75rem;font-weight:700;color:#F0F4FA;
        letter-spacing:-0.01em;line-height:1.1;">
      Visor Territorial Agroalimentario · República Dominicana
    </div>
    <div style="font-size:0.88rem;color:#6B7280;margin-top:4px;">
      Diagnóstico de capacidades productivas regionales
      · RENAGRO 2024 + Consolidado SC&amp;P 2000–2024
      · Ministerio de Agricultura
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# TABS (sin emojis)
# ─────────────────────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs([
    "Panorama nacional",
    "Producción y series históricas",
    "Perfil por región",
])

# ═════════════════════════════════════════════════════════════════
# TAB 1 — PANORAMA NACIONAL
# ═════════════════════════════════════════════════════════════════

with tab1:

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
        # Solo indicadores que existen en el pivot
        opciones_ind = [i for i in IND_DIRECTOS.get(pilar_sel, []) if i in pivot.columns]
        ind_sel = st.selectbox("Indicador", opciones_ind, index=0, key="pan_ind")
    with fc3:
        mostrar_vias = st.toggle("Mostrar vias", value=True, key="pan_vias")
    st.markdown("</div>", unsafe_allow_html=True)

    left_col, right_col = st.columns([1.9, 1.1], gap="small")

    with left_col:
        fig_map, ul = build_mapa(ind_sel, pilar_sel, mostrar_vias)

        # Unidad correcta en el titulo
        st.markdown(
            f'<div class="panel-title">Mapa regional — {ind_sel}'
            f'{"  (" + ul + ")" if ul else ""} '
            f'{ftag("RENAGRO 2024")}</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(fig_map, use_container_width=True)

        # Leyenda escala de color
        st.markdown("""
        <div style="display:flex;align-items:center;gap:6px;margin-top:0.3rem;font-size:0.78rem;color:#9EABC0;">
          <span>Menor valor</span>
          <div style="flex:1;height:8px;border-radius:4px;
            background:linear-gradient(to right,#DC3215,#F5A020,#FFDC00,#74C69D);"></div>
          <span>Mayor valor</span>
        </div>
        """, unsafe_allow_html=True)

        if mostrar_vias:
            st.markdown("""
            <div style="display:flex;gap:14px;flex-wrap:wrap;margin-top:0.4rem;
                font-size:0.78rem;color:#9EABC0;">
              <span><span style="display:inline-block;width:18px;height:3px;
                background:#FF6B35;vertical-align:middle;margin-right:4px;"></span>Autopista</span>
              <span><span style="display:inline-block;width:18px;height:3px;
                background:#F5A020;vertical-align:middle;margin-right:4px;"></span>Troncal</span>
              <span><span style="display:inline-block;width:18px;height:2px;
                background:#9EABC0;vertical-align:middle;margin-right:4px;"></span>Primaria</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div class="method-note">
          <b>Fuente cartografica:</b> Poligonos regionales — ONE/IGN (RD_REG_20220630).
          Vias — OpenStreetMap / Geofabrik (2024), autopistas, troncales y primarias.
          <b>Indicador:</b> datos directos del RENAGRO 2024, Ministerio de Agricultura RD.
        </div>
        """, unsafe_allow_html=True)

    with right_col:
        # Ranking
        st.markdown('<div class="panel-title">Ranking regional</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        sub_ind = ind[(ind["pilar"]==pilar_sel)&(ind["indicador"]==ind_sel)].copy()
        sub_ind["nombre"] = sub_ind["cod_region"].map(NOMBRES_REG)
        rank_df = sub_ind.sort_values("valor",ascending=False).reset_index(drop=True)
        vmax_r  = rank_df["valor"].max()
        for i, row in rank_df.iterrows():
            pct_w = row["valor"]/vmax_r*100 if vmax_r>0 else 0
            color = "#74C69D" if i<3 else "#4DA3FF" if i<6 else "#9EABC0"
            ul_r  = unit_label(row.get("unidad","") or "")
            st.markdown(f"""
            <div style="margin-bottom:0.55rem;">
              <div style="display:flex;justify-content:space-between;align-items:baseline;">
                <span style="font-size:0.82rem;color:#C7D0DD;">
                  <b style="color:{color};">#{i+1}</b> {row['nombre']}
                </span>
                <span style="font-size:0.85rem;font-weight:600;color:#F0F4FA;">
                  {fmt_num(row['valor'],1)}
                  <span style="font-size:0.72rem;color:#6B7280;">{ul_r}</span>
                </span>
              </div>
              <div style="background:#1E2530;border-radius:4px;height:6px;margin-top:3px;">
                <div style="width:{pct_w:.1f}%;height:6px;border-radius:4px;background:{color};"></div>
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Metricas nacionales
        st.markdown(
            '<div class="panel-title" style="margin-top:0.8rem;">Totales nacionales · RENAGRO 2024</div>',
            unsafe_allow_html=True)
        tot_prod = ren[ren["variable"]=="Productores"]["valor"].sum()
        tot_sup  = ren[ren["variable"]=="Superficie agropecuaria"]["valor"].sum()
        tot_at   = ren[ren["variable"]=="Parcelas con asistencia técnica"]["valor"].sum()
        tot_cred = ren[ren["variable"]=="Productores que recibieron crédito"]["valor"].sum()
        for label, val, unit in [
            ("Productores",           tot_prod, ""),
            ("Sup. agropecuaria",     tot_sup,  "Ha"),
            ("Parcelas con AT",       tot_at,   ""),
            ("Productores c/crédito", tot_cred, ""),
        ]:
            st.markdown(f"""
            <div class="metric-card">
              <div class="metric-label">{label}</div>
              <div class="metric-value" style="font-size:1.2rem;">{fmt_num(val)}</div>
              <div class="metric-small">{unit}</div>
            </div>""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════
# TAB 2 — PRODUCCIÓN Y SERIES HISTÓRICAS (fusionadas)
# ═════════════════════════════════════════════════════════════════

with tab2:

    # ── Filtros superiores ────────────────────────────────────────
    st.markdown('<div class="filter-wrap">', unsafe_allow_html=True)
    p2c1, p2c2 = st.columns([2, 2])
    with p2c1:
        # Unir cultivos del consolidado + cultivos solo en RENAGRO (sin duplicar)
        opciones_cult = PRODS_VALIDOS + [
            c for c in CULTIVOS_RENAGRO_VARS if c not in PRODS_VALIDOS
        ] + ["Todos los cultivos RENAGRO"]
        cultivo_sel = st.selectbox(
            "Cultivo",
            opciones_cult,
            index=opciones_cult.index("Arroz") if "Arroz" in opciones_cult else 0,
            key="prod_cult",
        )
    with p2c2:
        metrica_sel = st.selectbox(
            "Métrica",
            ["Área sembrada","Área cosechada","Productores","Parcelas"],
            key="prod_met",
        )
    st.markdown("</div>", unsafe_allow_html=True)

    UNIDAD_MET = {
        "Área sembrada":"Ha","Área cosechada":"Ha",
        "Productores":"Número","Parcelas":"Número",
    }

    # ── Datos RENAGRO ──────────────────────────────────────────
    ren_named = ren.copy()
    ren_named["nombre"] = ren_named["cod_region"].map(NOMBRES_REG)

    # Determinar si este cultivo tiene datos en RENAGRO 2024
    cult_ren = cultivo_sel  # nombre tal como aparece en el parquet
    tiene_renagro = cultivo_sel in CULTIVOS_RENAGRO_VARS

    if cultivo_sel == "Todos los cultivos RENAGRO":
        sufijo = f"- {metrica_sel}"
        ren_sub = ren_named[ren_named["variable"].str.endswith(sufijo)].copy()
        ren_sub["cultivo"] = ren_sub["variable"].str.replace(f" - {metrica_sel}","",regex=False)
        ren_sub = ren_sub[~ren_sub["pilar"].str.contains("Uso del suelo", na=False)]
    elif tiene_renagro:
        var_q  = f"{cult_ren} - {metrica_sel}"
        ren_sub = ren_named[ren_named["variable"]==var_q].copy()
        ren_sub["cultivo"] = cultivo_sel
    else:
        ren_sub = pd.DataFrame()  # cultivo no está en RENAGRO 2024

    # ── Datos consolidado historico ────────────────────────────
    agg_hist = agg[agg["producto"]==cultivo_sel].copy() if cultivo_sel != "Todos los cultivos RENAGRO" else pd.DataFrame()
    nac_hist = nac[(nac["producto"]==cultivo_sel)&(nac["tipo"]==tipo_hist.upper())].copy() if cultivo_sel != "Todos los cultivos RENAGRO" else pd.DataFrame()

    # ═══ SECCIÓN SUPERIOR: RENAGRO ═══════════════════════════════
    st.markdown('<div class="panel-title">Distribucion regional — RENAGRO 2024</div>',
                unsafe_allow_html=True)

    col_bar, col_mapa_esp = st.columns([1.3, 1.7], gap="small")

    with col_bar:
        if not ren_sub.empty:
            if cultivo_sel == "Todos los cultivos RENAGRO":
                fig_tree = px.treemap(
                    ren_sub,
                    path=[px.Constant("Republica Dominicana"),"cultivo","nombre"],
                    values="valor", color="valor",
                    color_continuous_scale=[[0,"#1A2535"],[0.5,"#2D5986"],[1,"#74C69D"]],
                    custom_data=["cultivo","nombre","valor","unidad"],
                )
                fig_tree.update_traces(
                    hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
                                  "%{customdata[2]:,.1f} %{customdata[3]}<extra></extra>",
                    textfont=dict(size=11),
                )
                fig_tree.update_layout(
                    paper_bgcolor="#171A21",
                    margin=dict(l=0,r=0,t=10,b=0), height=340,
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig_tree, use_container_width=True)
            else:
                ren_bar = ren_sub.sort_values("valor",ascending=True)
                fig_bar = go.Figure(go.Bar(
                    x=ren_bar["valor"], y=ren_bar["nombre"], orientation="h",
                    marker=dict(
                        color=ren_bar["valor"],
                        colorscale=[[0,"#1A2535"],[0.5,"#4DA3FF"],[1,"#74C69D"]],
                        line=dict(width=0),
                    ),
                    customdata=ren_bar[["nombre","valor","unidad"]].values,
                    hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]:,.1f} %{customdata[2]}<extra></extra>",
                ))
                unidad_label = unit_label(ren_sub["unidad"].iloc[0]) if not ren_sub.empty else ""
                fig_bar.update_layout(
                    template="plotly_dark", paper_bgcolor="#171A21", plot_bgcolor="#171A21",
                    margin=dict(l=10,r=10,t=10,b=10), height=320,
                    xaxis=dict(title=f"{metrica_sel} ({unidad_label})",gridcolor="#2B3240"),
                    yaxis=dict(showgrid=False),
                )
                st.plotly_chart(fig_bar, use_container_width=True)

                # Aprovechamiento
                if metrica_sel in ("Área sembrada","Área cosechada"):
                    ap_s = ren_named[ren_named["variable"]==f"{cult_ren} - Área sembrada"]
                    ap_c = ren_named[ren_named["variable"]==f"{cult_ren} - Área cosechada"]
                    if not ap_s.empty and not ap_c.empty:
                        ap = (ap_s[["cod_region","nombre","valor"]]
                              .rename(columns={"valor":"siembra"})
                              .merge(ap_c[["cod_region","valor"]].rename(columns={"valor":"cosecha"}),
                                     on="cod_region", how="inner"))
                        ap = ap[ap["siembra"]>0].copy()
                        ap["pct"] = ap["cosecha"]/ap["siembra"]*100
                        ap = ap.sort_values("pct",ascending=False)

                        st.markdown(
                            '<div class="panel-title" style="margin-top:0.5rem;">'
                            f'Aprovechamiento cosechado/sembrado {ftag("RENAGRO 2024 · calculo propio")}</div>',
                            unsafe_allow_html=True)
                        fig_ap = go.Figure(go.Bar(
                            x=ap["pct"], y=ap["nombre"], orientation="h",
                            marker_color="#4DA3FF", opacity=0.8,
                            hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
                        ))
                        fig_ap.add_vline(x=100,line=dict(color="#F5A020",dash="dash",width=1.5))
                        fig_ap.update_layout(
                            template="plotly_dark", paper_bgcolor="#171A21", plot_bgcolor="#171A21",
                            margin=dict(l=10,r=10,t=5,b=10), height=210,
                            xaxis=dict(title="% cosechado/sembrado",gridcolor="#2B3240"),
                            yaxis=dict(showgrid=False),
                        )
                        st.plotly_chart(fig_ap, use_container_width=True)
                        if cultivo_sel == "Arroz":
                            st.markdown("""
                            <div class="warn-note">
                              <b>Nota sobre el arroz:</b> Los valores superiores al 100% no son un error.
                              El arroz en Republica Dominicana tiene 2-3 ciclos de cosecha por año.
                              El area cosechada acumula varios ciclos sobre la misma superficie sembrada
                              del año de referencia del censo. Es un resultado agronómicamente correcto.
                            </div>""", unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div class="method-note">
                              La linea naranja marca el 100%. Valores inferiores pueden indicar perdidas,
                              abandono de parcelas o cultivos perennes con ciclos desfasados.
                              Este cociente se calcula entre dos variables del RENAGRO 2024.
                            </div>""", unsafe_allow_html=True)
        else:
            st.info("Sin datos RENAGRO para la seleccion actual.")

    with col_mapa_esp:
        # Mapa de especializacion: choropleth de area sembrada por region
        st.markdown(
            f'<div class="panel-title">Especializacion territorial {ftag("RENAGRO 2024")}</div>',
            unsafe_allow_html=True)

        if not ren_sub.empty and cultivo_sel != "Todos los cultivos RENAGRO":
            total_nac = ren_sub["valor"].sum()
            # Construir mapa de especializacion
            esp_by_cod = ren_sub.set_index("cod_region")["valor"].to_dict()
            vmax_e = max(esp_by_cod.values()) if esp_by_cod else 1

            fig_esp = go.Figure()
            for cod, d in reg_json.items():
                val  = esp_by_cod.get(cod, 0)
                norm = val / vmax_e if vmax_e > 0 else 0
                # Escala verde→rojo igual que el mapa principal
                if norm >= 0.5:
                    t = (norm - 0.5) * 2
                    r = int(255 * (1 - t))
                    g = int(180 + (75 * t))
                    b = int(20 * (1 - t))
                else:
                    t = norm * 2
                    r = int(220 - (20 * t))
                    g = int(50 + (130 * t))
                    b = 15
                fill = f"rgba({r},{g},{b},0.82)"
                pct  = val/total_nac*100 if total_nac>0 else 0
                hover = f"<b>{d['nombre']}</b><br>{fmt_num(val,1)} Ha<br>{pct:.1f}% del total nacional"
                fig_esp.add_trace(go.Scattermapbox(
                    lon=d["lons"], lat=d["lats"],
                    mode="lines", fill="toself",
                    fillcolor=fill,
                    line=dict(color="rgba(180,220,180,0.5)",width=0.8),
                    hovertemplate=hover+"<extra></extra>",
                    showlegend=False, name=d["nombre"],
                ))

            # Etiquetas con %
            cx_l, cy_l, txt_l, hov_l = [], [], [], []
            for cod, d in reg_json.items():
                val = esp_by_cod.get(cod, 0)
                pct = val/total_nac*100 if total_nac>0 else 0
                cx_l.append(d["cx"]); cy_l.append(d["cy"])
                txt_l.append(f"{pct:.0f}%")
                hov_l.append(f"<b>{d['nombre']}</b><br>{fmt_num(val,1)} Ha")
            fig_esp.add_trace(go.Scattermapbox(
                lon=cx_l, lat=cy_l,
                mode="markers+text",
                marker=dict(size=4,color="rgba(255,255,255,0.4)"),
                text=txt_l,
                textfont=dict(size=9,color="#F0F4FA"),
                textposition="top right",
                hovertemplate=[h+"<extra></extra>" for h in hov_l],
                showlegend=False,
            ))
            fig_esp.update_layout(
                mapbox=dict(style="carto-darkmatter",center=dict(lat=18.9,lon=-70.2),zoom=6.5),
                paper_bgcolor="#0F1116",
                margin=dict(l=0,r=0,t=0,b=0), height=320,
            )
            st.plotly_chart(fig_esp, use_container_width=True)

            # Panel de porcentajes
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            for _, row in ren_sub.sort_values("valor",ascending=False).iterrows():
                pct = row["valor"]/total_nac*100 if total_nac>0 else 0
                color = "#74C69D" if pct>=20 else "#4DA3FF" if pct>=10 else "#9EABC0"
                st.markdown(f"""
                <div style="margin-bottom:0.4rem;">
                  <div style="display:flex;justify-content:space-between;">
                    <span style="font-size:0.8rem;color:#C7D0DD;">{row['nombre']}</span>
                    <span style="font-size:0.82rem;font-weight:600;color:{color};">{pct:.1f}%</span>
                  </div>
                  <div style="background:#1E2530;border-radius:3px;height:5px;margin-top:2px;">
                    <div style="width:{pct:.1f}%;height:5px;border-radius:3px;background:{color};"></div>
                  </div>
                  <div style="font-size:0.72rem;color:#6B7280;">{fmt_num(row['valor'],1)} Ha</div>
                </div>""", unsafe_allow_html=True)
            st.markdown(f"""
            <div style="margin-top:0.5rem;padding-top:0.4rem;border-top:1px solid #2B3240;
                color:#6B7280;font-size:0.78rem;">
              Total nacional: {fmt_num(total_nac,1)} Ha · % calculado sobre RENAGRO 2024
            </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        elif cultivo_sel == "Todos los cultivos RENAGRO":
            tot_cult = ren_sub.groupby("cultivo")["valor"].sum().sort_values(ascending=False).head(12)
            tot_all  = tot_cult.sum()
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            for cult, val in tot_cult.items():
                pct = val/tot_all*100 if tot_all>0 else 0
                st.markdown(f"""
                <div style="margin-bottom:0.4rem;">
                  <div style="display:flex;justify-content:space-between;">
                    <span style="font-size:0.8rem;color:#C7D0DD;">{cult}</span>
                    <span style="font-size:0.8rem;color:#4DA3FF;">{pct:.1f}%</span>
                  </div>
                  <div style="background:#1E2530;border-radius:3px;height:4px;margin-top:2px;">
                    <div style="width:{pct:.1f}%;height:4px;border-radius:3px;background:#4DA3FF;"></div>
                  </div>
                </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # ═══ SECCIÓN INFERIOR: SERIES HISTÓRICAS ══════════════════════

    st.markdown("---")
    st.markdown(
        f'<div class="panel-title">Series históricas 2000–2024 — {cultivo_sel} '
        f'{ftag("Consolidado SC&P, Min. Agricultura RD")}</div>',
        unsafe_allow_html=True)

    if cultivo_sel == "Todos los cultivos RENAGRO" or agg_hist.empty:
        st.info("Selecciona un cultivo especifico para ver la serie historica.")
    else:
        anio_range = st.slider("Periodo", 2000, 2024, (2000,2024), key="hist_anio")
        agg_h = agg_hist[(agg_hist["anio"]>=anio_range[0])&(agg_hist["anio"]<=anio_range[1])]
        nac_h = nac_hist[(nac_hist["anio"]>=anio_range[0])&(nac_hist["anio"]<=anio_range[1])]

        hs_left, hs_right = st.columns([2.2, 0.8], gap="small")

        with hs_left:
            h_top, h_bot = st.columns(2, gap="small")

            with h_top:
                # Serie por region
                regiones_datos = sorted(agg_h["region"].unique())
                color_map_r = {r: COLORES_REG[i%len(COLORES_REG)] for i,r in enumerate(regiones_datos)}
                fig_hist = go.Figure()
                for reg in regiones_datos:
                    sub = agg_h[agg_h["region"]==reg].sort_values("anio")
                    vals = sub[tipo_hist] if tipo_hist in sub.columns else pd.Series(dtype=float)
                    if vals.dropna().empty: continue
                    fig_hist.add_trace(go.Scatter(
                        x=sub["anio"], y=vals, mode="lines+markers", name=reg,
                        line=dict(color=color_map_r[reg],width=2),
                        marker=dict(size=4,color=color_map_r[reg]),
                        hovertemplate=f"<b>{reg}</b><br>%{{x}}: %{{y:,.1f}} Ha<extra></extra>",
                    ))
                if not nac_h.empty:
                    fig_hist.add_trace(go.Scatter(
                        x=nac_h["anio"], y=nac_h["valor_nacional"],
                        mode="lines", name="Total nacional",
                        line=dict(color="#FFD166",width=2,dash="dash"),
                        yaxis="y2",
                        hovertemplate="Nacional: %{y:,.1f} Ha<extra></extra>",
                    ))
                fig_hist.update_layout(
                    template="plotly_dark",paper_bgcolor="#171A21",plot_bgcolor="#171A21",
                    margin=dict(l=10,r=10,t=10,b=10),height=320,
                    xaxis=dict(showgrid=False,dtick=2),
                    yaxis=dict(title="Ha (region)",gridcolor="#2B3240"),
                    yaxis2=dict(title="Ha (nacional)",overlaying="y",side="right",
                                showgrid=False,tickfont=dict(color="#FFD166")),
                    legend=dict(orientation="h",y=1.1,x=0,font=dict(size=9)),
                )
                st.plotly_chart(fig_hist, use_container_width=True)

            with h_bot:
                # Heatmap
                if not agg_h.empty:
                    heat_df = agg_h.pivot_table(index="region",columns="anio",values=tipo_hist,aggfunc="sum").fillna(0)
                    fig_heat = go.Figure(go.Heatmap(
                        z=heat_df.values,
                        x=[str(c) for c in heat_df.columns],
                        y=heat_df.index.tolist(),
                        colorscale=[[0,"#0F1116"],[0.3,"#1A2535"],[0.6,"#2D5986"],[0.9,"#4DA3FF"],[1,"#74C69D"]],
                        hovertemplate="Region: %{y}<br>Año: %{x}<br>%{z:,.1f} Ha<extra></extra>",
                        colorbar=dict(tickfont=dict(color="#9EABC0",size=9),bgcolor="#12161D",bordercolor="#2B3240",thickness=10),
                    ))
                    fig_heat.update_layout(
                        template="plotly_dark",paper_bgcolor="#171A21",plot_bgcolor="#171A21",
                        margin=dict(l=10,r=10,t=5,b=10),height=310,
                        xaxis=dict(showgrid=False,tickangle=-60,tickfont=dict(size=8)),
                        yaxis=dict(showgrid=False,tickfont=dict(size=9)),
                    )
                    st.plotly_chart(fig_heat, use_container_width=True)

        with hs_right:
            st.markdown('<div class="panel-title">Variacion acumulada</div>', unsafe_allow_html=True)
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            cambios = []
            for reg in sorted(agg_h["region"].unique()):
                sub = agg_h[agg_h["region"]==reg].sort_values("anio")
                v0s = sub[sub["anio"]==anio_range[0]][tipo_hist].dropna().values
                v1s = sub[sub["anio"]==anio_range[1]][tipo_hist].dropna().values
                if len(v0s) and len(v1s) and v0s[0]>0:
                    cambios.append({"region":reg,"cambio":(v1s[0]-v0s[0])/v0s[0]*100,"v0":v0s[0],"v1":v1s[0]})
            for row in sorted(cambios,key=lambda x:-x["cambio"]):
                color = "#74C69D" if row["cambio"]>=0 else "#FF6B6B"
                signo = "+" if row["cambio"]>=0 else ""
                st.markdown(f"""
                <div style="margin-bottom:0.5rem;">
                  <div style="display:flex;justify-content:space-between;">
                    <span style="font-size:0.78rem;color:#C7D0DD;">{row['region']}</span>
                    <span style="font-size:0.82rem;font-weight:600;color:{color};">
                      {signo}{row['cambio']:.1f}%
                    </span>
                  </div>
                  <div style="font-size:0.7rem;color:#6B7280;">
                    {fmt_num(row['v0'],1)} -> {fmt_num(row['v1'],1)} Ha
                  </div>
                </div>""", unsafe_allow_html=True)

            if not nac_h.empty:
                v0n = nac_h[nac_h["anio"]==anio_range[0]]["valor_nacional"].values
                v1n = nac_h[nac_h["anio"]==anio_range[1]]["valor_nacional"].values
                if len(v0n) and len(v1n) and v0n[0]>0:
                    cn = (v1n[0]-v0n[0])/v0n[0]*100
                    cn_color = "#74C69D" if cn>=0 else "#FF6B6B"
                    st.markdown(f"""
                    <div style="margin-top:0.8rem;padding-top:0.6rem;border-top:1px solid #2B3240;
                        text-align:center;">
                      <div style="font-size:0.78rem;color:#9EABC0;">Nacional {anio_range[0]}–{anio_range[1]}</div>
                      <div style="font-size:1.4rem;font-weight:700;color:{cn_color};">
                        {'+' if cn>=0 else ''}{cn:.1f}%
                      </div>
                    </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
        <div class="method-note">
          <b>Fuente:</b> Consolidado Regional de Siembra, Cosecha y Produccion 2000–2024,
          Ministerio de Agricultura RD. Valores originales en Tareas convertidos a Hectareas
          (1 tarea = 0.062886 Ha). La region "Este" agrupa Yuma + Higuamo + Ozama
          segun la fuente original y no puede desagregarse.
        </div>""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════
# TAB 3 — PERFIL POR REGIÓN
# ═════════════════════════════════════════════════════════════════

with tab3:

    p4c1, p4c2 = st.columns([1, 3], gap="medium")

    with p4c1:
        st.markdown('<div class="panel-title">Selecciona una region</div>',
                    unsafe_allow_html=True)
        prod_by_reg = ren[ren["variable"]=="Productores"][["cod_region","valor"]].sort_values(
            "valor",ascending=False)
        opciones_reg = prod_by_reg["cod_region"].tolist()

        region_sel = st.radio(
            "Region", options=opciones_reg,
            format_func=lambda c: NOMBRES_REG.get(c, c),
            label_visibility="collapsed", key="perfil_reg",
        )
        for _, row in prod_by_reg.iterrows():
            sel    = row["cod_region"] == region_sel
            nom    = NOMBRES_REG.get(row["cod_region"], row["cod_region"])
            border = "border-color:#4DA3FF;" if sel else ""
            bg     = "background:#1E2A3A;" if sel else ""
            vmax_p = prod_by_reg["valor"].max()
            pct_w  = row["valor"]/vmax_p*100 if vmax_p>0 else 0
            st.markdown(f"""
            <div style="padding:0.35rem 0.6rem;border:1px solid #2B3240;border-radius:8px;
                margin-bottom:3px;{border}{bg}">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-size:0.8rem;color:{'#F0F4FA' if sel else '#9EABC0'};">{nom}</span>
                <span style="font-size:0.78rem;color:#4DA3FF;">{fmt_num(row['valor'])}</span>
              </div>
              <div style="background:#1E2530;border-radius:3px;height:4px;margin-top:3px;">
                <div style="width:{pct_w:.1f}%;height:4px;border-radius:3px;
                    background:#4DA3FF;opacity:0.8;"></div>
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown('<div class="small-note" style="margin-top:0.4rem;">Ordenado por productores · RENAGRO 2024</div>',
                    unsafe_allow_html=True)

    with p4c2:
        reg_nombre = NOMBRES_REG.get(region_sel, region_sel)
        reg_ind    = ind[ind["cod_region"]==region_sel]

        # ── Mini-mapa con región resaltada ───────────────────────────────
        import json as _json
        with open(RUTA_REG_JSON) as _f:
            _rj = _json.load(_f)

        @st.cache_data(show_spinner=False)
        def build_mapa_region(region_cod):
            fig_r = go.Figure()
            for cod, d in _rj.items():
                es_sel = (cod == region_cod)
                # Color: verde brillante si seleccionada, gris oscuro si no
                if es_sel:
                    fill = "rgba(116,198,157,0.85)"
                    line_c = "rgba(255,255,255,0.9)"
                    lw = 2.0
                else:
                    fill = "rgba(30,37,48,0.7)"
                    line_c = "rgba(80,100,120,0.5)"
                    lw = 0.7
                fig_r.add_trace(go.Scattermapbox(
                    lon=d["lons"], lat=d["lats"],
                    mode="lines", fill="toself",
                    fillcolor=fill,
                    line=dict(color=line_c, width=lw),
                    hovertemplate=f"<b>{d['nombre']}</b><extra></extra>",
                    showlegend=False,
                ))
            # Centrar en la región seleccionada
            cx = _rj[region_cod]["cx"]
            cy = _rj[region_cod]["cy"]
            fig_r.update_layout(
                mapbox=dict(style="carto-darkmatter",
                            center=dict(lat=cy, lon=cx), zoom=6.5),
                paper_bgcolor="#0F1116",
                margin=dict(l=0, r=0, t=0, b=0), height=200,
            )
            return fig_r

        map_col, title_col = st.columns([1, 2])
        with map_col:
            st.plotly_chart(build_mapa_region(region_sel),
                            use_container_width=True, config={"displayModeBar": False})
        with title_col:
            st.markdown(
                f'<div style="font-size:1.3rem;font-weight:700;color:#F0F4FA;'
                f'padding-top:0.6rem;">{reg_nombre}</div>',
                unsafe_allow_html=True)
            st.markdown(
                '<div style="font-size:0.82rem;color:#6B7280;margin-top:0.2rem;">'
                'Región de planificación · RENAGRO 2024 + Precenso'
                '</div>',
                unsafe_allow_html=True)

        prod_v  = get_val(region_sel,"Productores totales")
        sup_v   = get_val(region_sel,"Superficie agropecuaria total")
        at_v    = get_val(region_sel,"% parcelas con asistencia técnica")
        cred_v  = get_val(region_sel,"% productores con crédito")
        org_v   = get_val(region_sel,"% productores en organización rural")
        inseg_v = get_val(region_sel,"% productores con inseguridad alimentaria")
        leche_v = get_val(region_sel,"Leche - Producción litros/día")
        muj_v   = get_val(region_sel,"% mujeres en fuerza laboral")

        m1,m2,m3,m4 = st.columns(4)
        for col,label,val,unit in [
            (m1,"Productores",    prod_v,  ""),
            (m2,"Sup. Agropec.",  sup_v,   "Ha"),
            (m3,"Asist. Tecnica", at_v,    "%"),
            (m4,"Acceso crédito", cred_v,  "%"),
        ]:
            col.markdown(f"""
            <div class="metric-card">
              <div class="metric-label">{label}</div>
              <div class="metric-value" style="font-size:1.35rem;">{fmt_num(val,1)}</div>
              <div class="metric-small">{unit} · RENAGRO 2024</div>
            </div>""", unsafe_allow_html=True)

        r_left, r_right = st.columns([1.1, 1.9], gap="small")

        with r_left:
            st.markdown(f'<div class="panel-title">Indicadores sociales {ftag("RENAGRO 2024")}</div>',
                        unsafe_allow_html=True)
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            for label, val, color, desc in [
                ("Asistencia técnica", at_v,    "#74C69D", "% parcelas"),
                ("Acceso a crédito",   cred_v,  "#F5A020", "% productores"),
                ("Organización rural", org_v,   "#4DA3FF", "% productores"),
                ("Inseg. alimentaria", inseg_v, "#FF6B6B", "% productores"),
                ("Mujeres en trabajo", muj_v,   "#C77DFF", "% fuerza laboral"),
            ]:
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
                <div class="metric-card" style="margin-top:0.5rem;">
                  <div class="metric-label">Produccion de leche</div>
                  <div class="metric-value" style="font-size:1.1rem;">{fmt_num(leche_v)}</div>
                  <div class="metric-small">Litros/dia · RENAGRO 2024</div>
                </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with r_right:
            st.markdown(f'<div class="panel-title">Cultivos — area sembrada {ftag("RENAGRO 2024")}</div>',
                        unsafe_allow_html=True)
            cultivos_reg = ren[
                (ren["cod_region"]==region_sel) &
                (ren["variable"].str.endswith("- Área sembrada"))
            ].copy()
            cultivos_reg["cultivo"] = cultivos_reg["variable"].str.replace(
                " - Área sembrada","",regex=False)
            cultivos_reg = cultivos_reg[cultivos_reg["valor"]>0].sort_values(
                "valor",ascending=False)

            if not cultivos_reg.empty:
                COLORES_CULT = ["#4DA3FF","#74C69D","#F5A020","#C77DFF",
                                "#FF6B6B","#FFD166","#06D6A0","#EF476F"]
                fig_pie = go.Figure(go.Pie(
                    labels=cultivos_reg["cultivo"],
                    values=cultivos_reg["valor"],
                    hole=0.45,
                    marker=dict(colors=COLORES_CULT[:len(cultivos_reg)],
                                line=dict(color="#0F1116",width=2)),
                    textfont=dict(size=10,color="#E8EDF5"),
                    hovertemplate="<b>%{label}</b><br>%{value:,.1f} Ha<br>%{percent}<extra></extra>",
                ))
                fig_pie.update_layout(
                    paper_bgcolor="#171A21",
                    margin=dict(l=10,r=10,t=10,b=10), height=230,
                    legend=dict(font=dict(size=9,color="#C7D0DD"),orientation="v",x=1.0,y=0.5),
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            # Indicadores del precenso por región
            pre_reg = ren[
                (ren["cod_region"]==region_sel) &
                (ren["pilar"]=="6. Precenso RENAGRO 2024")
            ].copy()
            if not pre_reg.empty:
                st.markdown(
                    f'<div class="panel-title" style="margin-top:0.5rem;">Perfil del productor {ftag("Precenso RENAGRO 2024")}</div>',
                    unsafe_allow_html=True)
                # Agrupar por tema
                temas_pre = pre_reg["tema"].unique()
                TEMA_COLOR = {
                    "Género":               "#C77DFF",
                    "Agricultura familiar": "#74C69D",
                    "Tamaño de productor":  "#4DA3FF",
                    "Régimen de tenencia":  "#FFD166",
                    "Actividad principal":  "#F5A020",
                    "Tamaño UA":            "#FF6B6B",
                }
                for tema in ["Género","Agricultura familiar","Tamaño de productor",
                             "Actividad principal","Régimen de tenencia","Tamaño UA"]:
                    sub_t = pre_reg[pre_reg["tema"]==tema]
                    if sub_t.empty: continue
                    color_t = TEMA_COLOR.get(tema, "#9EABC0")
                    st.markdown(f"""
                    <div style="font-size:0.78rem;font-weight:600;color:{color_t};
                        margin:0.4rem 0 0.2rem 0;text-transform:uppercase;
                        letter-spacing:0.05em;">{tema}</div>""",
                    unsafe_allow_html=True)
                    pct_vars = sub_t[sub_t["unidad"]=="%"].sort_values("variable")
                    num_vars = sub_t[sub_t["unidad"]!= "%"].sort_values("variable")
                    # Barras para %
                    for _, vr in pct_vars.iterrows():
                        w = max(0, min(100, vr["valor"] or 0))
                        st.markdown(f"""
                        <div style="margin-bottom:0.35rem;">
                          <div style="display:flex;justify-content:space-between;font-size:0.8rem;">
                            <span style="color:#C7D0DD;">{vr['variable'].replace('% ','')}</span>
                            <span style="color:{color_t};font-weight:600;">{vr['valor']:.1f}%</span>
                          </div>
                          <div style="background:#1E2530;border-radius:3px;height:5px;margin-top:2px;">
                            <div style="width:{w:.1f}%;height:5px;border-radius:3px;background:{color_t};"></div>
                          </div>
                        </div>""", unsafe_allow_html=True)
                    # Métricas numéricas
                    for _, vr in num_vars.iterrows():
                        unidad = vr["unidad"] if vr["unidad"] != "Número" else ""
                        st.markdown(f"""
                        <div style="display:flex;justify-content:space-between;
                            font-size:0.8rem;margin-bottom:0.25rem;">
                          <span style="color:#9EABC0;">{vr['variable']}</span>
                          <span style="color:#F0F4FA;font-weight:600;">{vr['valor']:,.0f} {unidad}</span>
                        </div>""", unsafe_allow_html=True)

            # Uso del suelo de la región
            uso_reg = ren[
                (ren["cod_region"]==region_sel) &
                (ren["pilar"]=="2. Uso del suelo")
            ].copy()
            if not uso_reg.empty:
                st.markdown(
                    f'<div class="panel-title" style="margin-top:0.5rem;">Uso del suelo {ftag("RENAGRO 2024 · Cuadro N°21")}</div>',
                    unsafe_allow_html=True)
                sup_total = ren[(ren["cod_region"]==region_sel)&(ren["variable"]=="Superficie agropecuaria")]["valor"].sum()
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                for _, ur in uso_reg.sort_values("valor",ascending=False).iterrows():
                    pct = ur["valor"]/sup_total*100 if sup_total>0 else 0
                    color = "#74C69D" if "temporero" in ur["variable"].lower() or "permanente" in ur["variable"].lower() else "#4DA3FF" if "pasto" in ur["variable"].lower() else "#9EABC0"
                    st.markdown(f"""
                    <div style="margin-bottom:0.4rem;">
                      <div style="display:flex;justify-content:space-between;font-size:0.8rem;">
                        <span style="color:#C7D0DD;">{ur['variable']}</span>
                        <span style="color:{color};font-weight:600;">{pct:.1f}%</span>
                      </div>
                      <div style="background:#1E2530;border-radius:3px;height:5px;margin-top:2px;">
                        <div style="width:{min(pct,100):.1f}%;height:5px;border-radius:3px;background:{color};"></div>
                      </div>
                      <div style="font-size:0.72rem;color:#6B7280;">{fmt_num(ur['valor'],1)} Ha</div>
                    </div>""", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # Tabla limpia solo con datos directos de fuente
            st.markdown(f'<div class="panel-title" style="margin-top:0.4rem;">Datos por pilar {ftag("RENAGRO 2024")}</div>',
                        unsafe_allow_html=True)
            tabla_reg = reg_ind[
                (~reg_ind["pilar"].isin(["0. Índice Compuesto","2. Uso del suelo"])) &
                (~reg_ind["indicador"].isin(EXCLUIR_CALCULADOS))
            ][["pilar","indicador","valor","unidad"]].copy()
            tabla_reg["pilar"] = tabla_reg["pilar"].map(PILAR_LABELS).fillna(tabla_reg["pilar"])
            def fix_unit(u):
                if u in ("Tareas","Tareas/productor","Tareas/día"):
                    return "Ha" if "productor" not in str(u) else "Ha/prod."
                return unit_label(u)
            tabla_reg["unidad"] = tabla_reg["unidad"].apply(fix_unit)
            tabla_reg["valor"] = tabla_reg["valor"].map(
                lambda x: f"{x:,.2f}" if pd.notna(x) else "—")
            tabla_reg.columns = ["Pilar","Indicador","Valor","Unidad"]
            st.dataframe(tabla_reg, use_container_width=True, hide_index=True, height=270)

# ─────────────────────────────────────────────────────────────────
# PIE DE PÁGINA
# ─────────────────────────────────────────────────────────────────

st.markdown("""
<div style="margin-top:1.2rem;padding-top:0.6rem;border-top:1px solid #2B3240;
    color:#4A5568;font-size:0.8rem;text-align:center;">
  Fuente: RENAGRO 2024 · Consolidado Regional SC&amp;P 2000–2024
  · Ministerio de Agricultura de la Republica Dominicana
  · Cartografia ONE/IGN · Vias OSM/Geofabrik
  · Precenso RENAGRO 2024 (microdatos)
  | FAO UTF-COL-178 / SARA · Visor Territorial Agroalimentario RD
  <br><span style="color:#3A4558;font-size:0.76rem;">
  Las superficies se presentan en <b>hectareas (Ha)</b>.
  Datos originales del RENAGRO y Consolidado SC&amp;P en <b>tareas</b>
  (unidad oficial dominicana). Factor de conversion: 1 tarea = 0.062886 Ha = 628.86 m². 1 Ha = ~15.9 tareas.
  </span>
</div>
""", unsafe_allow_html=True)
