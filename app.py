import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json, os

st.set_page_config(
    page_title="METAREC — República Dominicana",
    page_icon="🇩🇴",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

:root {
  --verde:    #1B6B3A;
  --verde-cl: #2E9E57;
  --verde-xs: #D4EDDF;
  --azul:     #1A4A7A;
  --azul-cl:  #2E72B5;
  --azul-xs:  #D6E8F7;
  --arena:    #F5F0E8;
  --gris-osc: #1C1C1C;
  --gris-med: #4A4A4A;
  --gris-cl:  #9E9E9E;
  --rojo:     #C0392B;
  --amarillo: #E67E22;
  --borde:    #DCDCDC;
  --blanco:   #FFFFFF;
}
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.block-container { padding: 1.2rem 2rem 2rem 2rem !important; max-width: 1400px !important; }

/* Header */
.metarec-header {
  background: linear-gradient(135deg, var(--verde) 0%, var(--azul) 100%);
  border-radius: 12px;
  padding: 1.6rem 2rem;
  margin-bottom: 1.4rem;
  display: flex; align-items: center; gap: 1.2rem;
}
.metarec-header h1 {
  color: white; font-size: 1.6rem; font-weight: 700; margin: 0; letter-spacing: -0.02em;
}
.metarec-header p { color: rgba(255,255,255,0.75); font-size: 0.85rem; margin: 0.2rem 0 0 0; }

/* Sección */
.section-title {
  font-size: 0.72rem; font-weight: 600; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--gris-cl); margin: 1.2rem 0 0.6rem 0;
}

/* Score badge */
.score-badge {
  display: inline-block; padding: 0.15rem 0.6rem; border-radius: 20px;
  font-size: 0.78rem; font-weight: 600; font-family: 'DM Mono', monospace;
}
.badge-alto   { background: #D4EDDF; color: #1B6B3A; }
.badge-medio  { background: #FEF3CD; color: #8B5E00; }
.badge-bajo   { background: #FADBD8; color: #922B21; }

/* Panel de región */
.panel-region {
  background: var(--blanco); border: 1px solid var(--borde); border-radius: 10px;
  padding: 1rem 1.2rem; margin-bottom: 0.8rem;
}

/* Métricas */
.metrica-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.35rem 0; border-bottom: 1px solid #F0F0F0; font-size: 0.82rem;
}
.metrica-label { color: var(--gris-med); flex: 1; }
.metrica-val { font-weight: 600; font-family: 'DM Mono', monospace; color: var(--gris-osc); }
.eval-1 { color: var(--rojo);    font-weight: 700; }
.eval-2 { color: var(--amarillo);font-weight: 700; }
.eval-3 { color: var(--verde);   font-weight: 700; }

/* Separador de categoría */
.cat-label {
  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--blanco); padding: 0.25rem 0.7rem;
  border-radius: 4px; display: inline-block; margin: 0.7rem 0 0.3rem 0;
}

/* Toggle layer */
.layer-btn {
  display: inline-flex; align-items: center; gap: 0.4rem;
  padding: 0.3rem 0.8rem; border-radius: 20px; border: 1.5px solid var(--borde);
  font-size: 0.78rem; cursor: pointer; transition: all 0.15s;
  background: white; margin: 0.2rem;
}
</style>
""", unsafe_allow_html=True)

# ── DATOS ─────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def cargar_datos():
    df = pd.read_parquet(os.path.join(os.path.dirname(__file__), "Datos/metarec_rd.parquet"))
    with open(os.path.join(os.path.dirname(__file__), "Datos/regiones_coords.json")) as f:
        reg_json = json.load(f)
    with open(os.path.join(os.path.dirname(__file__), "Datos/centros_urbanos.json")) as f:
        cu_json = json.load(f)
    return df, reg_json, cu_json

df, reg_json, cu_json = cargar_datos()

REGIONES_ORD = ["01","02","03","04","05","06","07","08","09","10"]
REG_NOMBRES = {
    "01":"Cibao Norte","02":"Cibao Sur","03":"Cibao Nordeste","04":"Cibao Noroeste",
    "05":"Valdesia","06":"Enriquillo","07":"El Valle","08":"Yuma",
    "09":"Higuamo","10":"Ozama o Metropolitana",
}

# Variables transformadoras
BRECHAS_VARS = {
    "Electricidad":         "% cobertura electricidad_eval",
    "Agua potable":         "% cobertura agua potable_eval",
    "Internet":             "% cobertura internet_eval",
    "Inseg. alimentaria":   "% inseguridad alimentaria (productor)_eval",
    "Índice GINI":          "Indice GINI 2025_eval",
    "Mujeres productoras":  "% mujeres productoras_eval",
    "Propietarios":         "% productores propietarios_eval",
}
COMPET_VARS = {
    "Org. rural":           "% productores en organización rural_eval",
    "Asist. técnica":       "% parcelas con asistencia técnica_eval",
    "Crédito":              "% productores con crédito_eval",
    "Tecnif. riego":        "% Tecnificación (riego)_eval",
    "Volumen exportador":   "Volumen y Alcance Exportador_eval",
    "Densidad exportadora": "Densidad Empresarial Exportadora_eval",
    "Vulnerabilidad territ.":"Vulnerabilidad territorial_eval",
}

# Indicadores de entorno (para el mapa)
CAPAS_MAPA = {
    "Cierre de brechas":          "score_brechas",
    "Competitividad":             "score_competitividad",
    "% Inseguridad alimentaria":  "% inseguridad alimentaria (productor)_eval",
    "Vulnerabilidad territorial": "Vulnerabilidad territorial_eval",
    "Volumen exportador":         "Volumen y Alcance Exportador_eval",
    "Densidad exportadora":       "Densidad Empresarial Exportadora_eval",
    "% Cobertura internet":       "% cobertura internet_eval",
    "Índice GINI":                "Indice GINI 2025_eval",
    "% Agricultores familiares":  "% agricultores familiares (FAO)_eval",
    "% Parcelas con AT":          "% parcelas con asistencia técnica_eval",
    "% Productores con crédito":  "% productores con crédito_eval",
}

TIER_LABELS = {1:"Town",2:"Small city",3:"Intermediate city",4:"Large city"}
TIER_COLORES = {1:"#A8D5A2",2:"#3E9C6B",3:"#1B6B3A",4:"#0D3D21"}

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="metarec-header">
  <div>
    <h1>🇩🇴 METAREC — República Dominicana</h1>
    <p>Metodología de Evaluación Territorial para la Competitividad Agroalimentaria Regional &nbsp;·&nbsp;
       10 regiones de planificación &nbsp;·&nbsp; RENAGRO 2024 + FAO City-Region Explorer</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── LAYOUT PRINCIPAL ──────────────────────────────────────────────────────────
col_mapa, col_panel = st.columns([1.6, 1], gap="large")

# ══════════════════════════════════════════════════════════════════════════════
# MAPA
# ══════════════════════════════════════════════════════════════════════════════
with col_mapa:
    st.markdown('<div class="section-title">Mapa territorial</div>', unsafe_allow_html=True)

    # Controles del mapa
    c1, c2, c3 = st.columns([2, 1.2, 1.2])
    with c1:
        capa_sel = st.selectbox("Capa de color", list(CAPAS_MAPA.keys()), key="capa")
    with c2:
        mostrar_cu = st.checkbox("Centros urbanos", value=True)
    with c3:
        mostrar_patches = st.checkbox("Acceso FAO (WMS)", value=False)

    col_var = CAPAS_MAPA[capa_sel]

    # ── Construir mapa ─────────────────────────────────────────────────────
    @st.cache_data(show_spinner=False)
    def build_mapa(col_var, mostrar_cu):
        fig = go.Figure()

        # Polígonos de regiones (choropleth manual)
        vals = df.set_index("cod_region")[col_var].to_dict()
        vmin = min(v for v in vals.values() if pd.notna(v))
        vmax = max(v for v in vals.values() if pd.notna(v))

        for cod, d in reg_json.items():
            v = vals.get(cod, np.nan)
            if pd.isna(v):
                fill = "rgba(200,200,200,0.4)"
            else:
                norm = (v - vmin) / (vmax - vmin + 1e-9)
                # Escala verde→amarillo→rojo
                if norm < 0.5:
                    t = norm * 2
                    r = int(40 + (255-40)*t); g = int(140 - (140-200)*t); b = int(40*(1-t))
                else:
                    t = (norm-0.5)*2
                    r = 255; g = int(200 - 200*t); b = 0
                fill = f"rgba({r},{g},{b},0.80)"

            # Nombre de región
            reg_nom = d.get("nombre","")
            val_str = f"{v:.1f}" if not pd.isna(v) else "—"

            fig.add_trace(go.Scattermapbox(
                lon=d["lons"], lat=d["lats"],
                mode="lines", fill="toself",
                fillcolor=fill,
                line=dict(color="rgba(255,255,255,0.6)", width=1),
                hovertemplate=f"<b>{reg_nom}</b><br>{col_var.replace('_eval','')}: {val_str}<extra></extra>",
                showlegend=False, name=reg_nom,
            ))
            # Centroide con nombre
            fig.add_trace(go.Scattermapbox(
                lon=[d["cx"]], lat=[d["cy"]],
                mode="text",
                text=[reg_nom.replace(" o Metropolitana","")],
                textfont=dict(size=9, color="white"),
                hoverinfo="skip", showlegend=False,
            ))

        # Centros urbanos
        if mostrar_cu:
            for nom, cu in cu_json.items():
                tier = cu.get("tier", 1)
                color = TIER_COLORES.get(tier, "#999")
                size = {1:6, 2:9, 3:13, 4:18}.get(tier, 6)
                fig.add_trace(go.Scattermapbox(
                    lon=[cu["lon"]], lat=[cu["lat"]],
                    mode="markers",
                    marker=dict(size=size, color=color,
                                opacity=0.9, symbol="circle"),
                    name=TIER_LABELS.get(tier,""),
                    text=nom,
                    hovertemplate=f"<b>{nom}</b><br>Tier: {TIER_LABELS.get(tier,'')}<br>Pob.: {cu.get('poblacion',0):,}<extra></extra>",
                    showlegend=False,
                ))

        fig.update_layout(
            mapbox=dict(
                style="carto-darkmatter",
                center=dict(lat=18.8, lon=-70.3), zoom=6.2,
                layers=[]
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=0),
            height=440,
        )
        return fig

    fig_mapa = build_mapa(col_var, mostrar_cu)

    # Agregar capa WMS de FAO si está activada
    if mostrar_patches:
        fig_mapa.update_layout(
            mapbox=dict(
                style="carto-darkmatter",
                center=dict(lat=18.8, lon=-70.3), zoom=6.2,
                layers=[{
                    "sourcetype": "raster",
                    "source": ["https://data.apps.fao.org/map/gsrv/gsrv1/cre_fao/wms?"
                               "SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap"
                               "&LAYERS=cre_fao:dominican_republic_1h_city_region_patches"
                               "&FORMAT=image/png&TRANSPARENT=true"
                               "&BBOX={bbox-epsg-3857}&WIDTH=256&HEIGHT=256&SRS=EPSG:3857"],
                    "type": "raster", "opacity": 0.65,
                }],
            )
        )

    st.plotly_chart(fig_mapa, use_container_width=True, config={"displayModeBar": False})

    # Leyenda de centros urbanos
    if mostrar_cu:
        leg_cols = st.columns(4)
        for i, (tier, lbl) in enumerate(TIER_LABELS.items()):
            with leg_cols[i]:
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:6px;font-size:0.76rem;">'
                    f'<div style="width:12px;height:12px;border-radius:50%;background:{TIER_COLORES[tier]};"></div>'
                    f'{lbl}</div>', unsafe_allow_html=True)

    # ── Nota WMS ──────────────────────────────────────────────────────────
    if mostrar_patches:
        st.markdown(
            '<div style="font-size:0.72rem;color:#888;margin-top:0.3rem;">'
            '🛰️ Capa FAO City-Region Explorer — Patches de acceso urbano a 1h (WMS en tiempo real)</div>',
            unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PANEL LATERAL: Indicadores por región
# ══════════════════════════════════════════════════════════════════════════════
with col_panel:
    st.markdown('<div class="section-title">Perfil regional</div>', unsafe_allow_html=True)

    # Selector de región
    reg_opts = list(REG_NOMBRES.values())
    reg_sel_nom = st.selectbox("Región", reg_opts, key="reg_sel")
    reg_sel_cod = next(k for k,v in REG_NOMBRES.items() if v == reg_sel_nom)
    row = df[df["cod_region"]==reg_sel_cod].iloc[0]

    # Scores resumen
    sb = row.get("score_brechas", np.nan)
    sc = row.get("score_competitividad", np.nan)

    def badge_score(v):
        if pd.isna(v): return "—"
        if v >= 75: cls="badge-alto"
        elif v >= 55: cls="badge-medio"
        else: cls="badge-bajo"
        return f'<span class="score-badge {cls}">{v:.1f}%</span>'

    st.markdown(f"""
    <div class="panel-region" style="display:flex;gap:1rem;justify-content:space-between;">
      <div>
        <div style="font-size:0.7rem;color:#888;font-weight:600;text-transform:uppercase;letter-spacing:.06em;">
          Cierre de brechas</div>
        <div style="margin-top:0.2rem;">{badge_score(sb)}</div>
      </div>
      <div>
        <div style="font-size:0.7rem;color:#888;font-weight:600;text-transform:uppercase;letter-spacing:.06em;">
          Competitividad</div>
        <div style="margin-top:0.2rem;">{badge_score(sc)}</div>
      </div>
      <div>
        <div style="font-size:0.7rem;color:#888;font-weight:600;text-transform:uppercase;letter-spacing:.06em;">
          Productores</div>
        <div style="font-size:1rem;font-weight:700;color:#1C1C1C;margin-top:0.2rem;">
          {int(row.get("Productores (N°)", 0) or 0):,}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    def eval_color(v):
        if pd.isna(v): return "—"
        v = int(v)
        cls = {1:"eval-1",2:"eval-2",3:"eval-3"}.get(v,"")
        sym = {1:"▼",2:"◆",3:"▲"}.get(v,"")
        return f'<span class="{cls}">{sym} {v}</span>'

    # Categorías
    CATEGORIAS = [
        ("Servicios de soporte", "#1A4A7A", [
            ("Electricidad",       "% cobertura electricidad_eval"),
            ("Agua potable",       "% cobertura agua potable_eval"),
            ("Internet",           "% cobertura internet_eval"),
        ]),
        ("Capital social", "#2E7D32", [
            ("Inseg. alimentaria", "% inseguridad alimentaria (productor)_eval"),
            ("Índice GINI",        "Indice GINI 2025_eval"),
            ("Titulares mujeres",  "% titulares mujeres (UA)_eval"),
            ("Mujeres productoras","% mujeres productoras_eval"),
            ("Mujeres f. laboral", "% mujeres en fuerza laboral_eval"),
            ("Agr. familiares",    "% agricultores familiares (FAO)_eval"),
            ("Pequeños prod.",     "% pequeños productores_eval"),
            ("Propietarios",       "% productores propietarios_eval"),
        ]),
        ("Tecnología e innovación", "#6A1B9A", [
            ("Asist. técnica",     "% parcelas con asistencia técnica_eval"),
            ("Crédito",            "% productores con crédito_eval"),
            ("Pres. innovación",   "% presupuesto innovación agro_eval"),
            ("Tecnif. riego",      "% Tecnificación (riego)_eval"),
        ]),
        ("Producción", "#E65100", [
            ("Área sembrada",      "% área sembrada c/cultivos perm+temp_eval"),
            ("Actividad agrícola", "% actividad agrícola principal_eval"),
            ("Actividad ganadera", "% actividad ganadera principal_eval"),
            ("UA < 1 Ha",          "% UA menores de 1 Ha_eval"),
        ]),
        ("Competitividad y mercados", "#C62828", [
            ("Org. rural",         "% productores en organización rural_eval"),
            ("Volumen exportador",  "Volumen y Alcance Exportador_eval"),
            ("Densidad exportadora","Densidad Empresarial Exportadora_eval"),
            ("N° Centros urbanos",  "N° Centros Urbanos_eval"),
            ("Concentración urbana","Población centro / Pob.urbana_eval"),
            ("Vulnerabilidad territ.","Vulnerabilidad territorial_eval"),
        ]),
    ]

    with st.container():
        for cat_nom, cat_color, indicadores in CATEGORIAS:
            st.markdown(
                f'<span class="cat-label" style="background:{cat_color};">{cat_nom}</span>',
                unsafe_allow_html=True)
            lineas = ""
            for lbl, col in indicadores:
                v = row.get(col, np.nan)
                e_html = eval_color(v) if col.endswith("_eval") else f"<span style='color:#666'>{v:.2f}</span>" if isinstance(v,(int,float)) and not pd.isna(v) else "—"
                lineas += f'<div class="metrica-row"><span class="metrica-label">{lbl}</span>{e_html}</div>'
            st.markdown(f'<div class="panel-region" style="padding:0.4rem 0.8rem;">{lineas}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICOS DE TELARAÑA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="section-title">Variables transformadoras</div>', unsafe_allow_html=True)

t1, t2 = st.columns(2, gap="large")

def radar(df_r, vars_dict, titulo, color_fill, color_line, reg_cod):
    cats   = list(vars_dict.keys())
    cols   = list(vars_dict.values())
    row_r  = df_r[df_r["cod_region"]==reg_cod].iloc[0]
    vals_r = [row_r.get(c, np.nan) or 0 for c in cols]

    fig = go.Figure()

    # Zonas de referencia
    for v_ref, col_ref, lbl_ref in [(3,"rgba(40,167,69,0.06)","Alta"),
                                     (2,"rgba(255,193,7,0.06)","Media"),
                                     (1,"rgba(220,53,69,0.06)","Baja")]:
        fig.add_trace(go.Scatterpolar(
            r=[v_ref]*len(cats)+[v_ref],
            theta=cats+[cats[0]],
            fill="toself", fillcolor=col_ref,
            line=dict(color="rgba(0,0,0,0.08)", width=0.5, dash="dot"),
            name=lbl_ref, showlegend=(titulo=="Cierre de brechas"),
            hoverinfo="skip",
        ))

    # Línea de la región
    vals_cierre = vals_r + [vals_r[0]]
    fig.add_trace(go.Scatterpolar(
        r=vals_cierre, theta=cats+[cats[0]],
        fill="toself",
        fillcolor=color_fill,
        line=dict(color=color_line, width=2.5),
        name=REG_NOMBRES.get(reg_cod,""),
        hovertemplate="<b>%{theta}</b><br>Calificación: %{r}<extra></extra>",
    ))

    fig.update_layout(
        polar=dict(
            bgcolor="rgba(250,250,252,1)",
            radialaxis=dict(
                visible=True, range=[0,3.3], tickvals=[1,2,3],
                ticktext=["Baja","Media","Alta"],
                tickfont=dict(size=9, color="#888"),
                gridcolor="#E8E8E8", linecolor="#E0E0E0",
            ),
            angularaxis=dict(
                tickfont=dict(size=10, family="DM Sans", color="#3A3A3A"),
                linecolor="#E0E0E0", gridcolor="#E8E8E8",
            ),
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.18, x=0.5, xanchor="center",
                    font=dict(size=10)),
        title=dict(text=f"<b>{titulo}</b>", x=0.5, y=0.97,
                   font=dict(size=13, family="DM Sans", color="#1C1C1C")),
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=50, r=50, t=60, b=60),
        height=380,
    )
    return fig

with t1:
    reg_radar = st.selectbox("Región", list(REG_NOMBRES.values()),
                              index=list(REG_NOMBRES.values()).index(reg_sel_nom),
                              key="radar_reg")
    reg_radar_cod = next(k for k,v in REG_NOMBRES.items() if v==reg_radar)
    fig_b = radar(df, BRECHAS_VARS, "Cierre de brechas sociales",
                  "rgba(26,74,122,0.15)", "#1A4A7A", reg_radar_cod)
    st.plotly_chart(fig_b, use_container_width=True, config={"displayModeBar":False})

with t2:
    fig_c = radar(df, COMPET_VARS, "Competitividad territorial",
                  "rgba(27,107,58,0.15)", "#1B6B3A", reg_radar_cod)
    st.plotly_chart(fig_c, use_container_width=True, config={"displayModeBar":False})

# ══════════════════════════════════════════════════════════════════════════════
# COMPARATIVO REGIONAL — tabla resumen
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="section-title">Comparativo por región</div>', unsafe_allow_html=True)

df_tabla = df[["region","score_brechas","score_competitividad"]].copy()
df_tabla.columns = ["Región","Cierre de brechas (%)","Competitividad (%)"]
df_tabla = df_tabla.sort_values("Cierre de brechas (%)", ascending=False).reset_index(drop=True)

fig_comp = go.Figure()
colors_b = ["#1A4A7A"] * len(df_tabla)
colors_c = ["#1B6B3A"] * len(df_tabla)

fig_comp.add_trace(go.Bar(
    x=df_tabla["Región"], y=df_tabla["Cierre de brechas (%)"],
    name="Cierre de brechas", marker_color="#2E72B5", opacity=0.85,
    hovertemplate="<b>%{x}</b><br>Cierre de brechas: %{y:.1f}%<extra></extra>",
))
fig_comp.add_trace(go.Bar(
    x=df_tabla["Región"], y=df_tabla["Competitividad (%)"],
    name="Competitividad", marker_color="#2E9E57", opacity=0.85,
    hovertemplate="<b>%{x}</b><br>Competitividad: %{y:.1f}%<extra></extra>",
))
fig_comp.update_layout(
    barmode="group",
    template="plotly_white",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=10, b=10), height=280,
    xaxis=dict(tickfont=dict(size=10), gridcolor="#F0F0F0"),
    yaxis=dict(title="Score (%)", range=[0,105], gridcolor="#F0F0F0", tickfont=dict(size=10)),
    legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center", font=dict(size=11)),
    bargap=0.2, bargroupgap=0.05,
)
st.plotly_chart(fig_comp, use_container_width=True, config={"displayModeBar":False})

# ── Pie ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;font-size:0.72rem;color:#B0B0B0;margin-top:1.5rem;padding-top:1rem;border-top:1px solid #EBEBEB;">
  METAREC · República Dominicana &nbsp;·&nbsp; FAO UTF-COL-178 / SARA &nbsp;·&nbsp;
  Fuentes: RENAGRO 2024 · Precenso RENAGRO 2024 · FAO City-Region Explorer (Cattaneo et al., 2024)
  · ProDominicana · ONE / ENFT · DIGEPRES/MEPYD
</div>
""", unsafe_allow_html=True)
