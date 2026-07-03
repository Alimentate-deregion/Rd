import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json, os, pickle

st.set_page_config(
    page_title="METAREC — República Dominicana",
    page_icon="🇩🇴",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=DM+Mono:wght@400;500&display=swap');
html,[class*="css"]{font-family:'DM Sans',sans-serif;}
.block-container{padding:1rem 1.5rem 2rem!important;max-width:1600px!important;}
.metarec-header{background:linear-gradient(135deg,#1B4332 0%,#1A3A6B 100%);
  border-radius:10px;padding:1.2rem 1.8rem;margin-bottom:1rem;}
.metarec-header h1{color:white;font-size:1.4rem;font-weight:700;margin:0;letter-spacing:-.02em;}
.metarec-header p{color:rgba(255,255,255,.65);font-size:.78rem;margin:.2rem 0 0;}
.sec-title{font-size:.68rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
  color:#9E9E9E;margin:1rem 0 .5rem;}
/* Layer toggles */
.layer-wrap{display:flex;flex-wrap:wrap;gap:.4rem;margin-bottom:.6rem;}
.layer-chip{display:inline-flex;align-items:center;gap:.35rem;padding:.2rem .65rem;
  border-radius:16px;border:1.5px solid #DDD;font-size:.75rem;cursor:pointer;
  background:white;transition:all .12s;white-space:nowrap;}
.layer-chip.active{border-color:#1B6B3A;background:#E8F5E9;color:#1B4332;font-weight:600;}
/* Tabla evaluada */
.eval-tbl{width:100%;border-collapse:collapse;font-size:.78rem;}
.eval-tbl th{background:#1B4332;color:white;padding:.4rem .6rem;
  text-align:center;font-weight:600;font-size:.72rem;white-space:nowrap;}
.eval-tbl td{padding:.32rem .55rem;border-bottom:1px solid #F0F0F0;text-align:center;}
.eval-tbl .cat-hdr td{background:#E8F5E9;font-weight:700;font-size:.72rem;
  color:#1B4332;text-align:left;letter-spacing:.04em;text-transform:uppercase;}
.eval-tbl .ind-name{text-align:left;color:#444;}
.v1{color:#C0392B;font-weight:700;} .v2{color:#E67E22;font-weight:700;}
.v3{color:#27AE60;font-weight:700;}
.score-cell{font-family:'DM Mono',monospace;font-weight:600;font-size:.82rem;}
.s-alto{color:#27AE60;} .s-med{color:#E67E22;} .s-bajo{color:#C0392B;}
.bg-alto{background:#C6EFCE!important;color:#006100!important;font-weight:700;}
.bg-med{background:#FFEB9C!important;color:#9C6500!important;font-weight:700;}
.bg-bajo{background:#FFC7CE!important;color:#9C0006!important;font-weight:700;}
/* Sidebar */
[data-testid="stSidebar"]{background:#F8FAF8;border-right:1px solid #E0E8E4;}
</style>
""", unsafe_allow_html=True)

# ── CARGAR DATOS ──────────────────────────────────────────────────────────────
BASE = os.path.dirname(__file__)

@st.cache_data(show_spinner=False)
def cargar():
    df = pd.read_parquet(os.path.join(BASE,"Datos/metarec_rd.parquet"))
    with open(os.path.join(BASE,"Datos/regiones_coords.json")) as f:
        reg_json = json.load(f)
    with open(os.path.join(BASE,"Datos/fao_layers.pkl"),"rb") as f:
        fao = pickle.load(f)
    return df, reg_json, fao

df, reg_json, fao = cargar()

REG_NOMBRES = {
    "01":"Cibao Norte","02":"Cibao Sur","03":"Cibao Nordeste","04":"Cibao Noroeste",
    "05":"Valdesia","06":"Enriquillo","07":"El Valle","08":"Yuma",
    "09":"Higuamo","10":"Ozama o Metropolitana",
}
REGIONES_ORD = ["01","02","03","04","05","06","07","08","09","10"]

TIER_LABELS = {1:"Town",2:"Small city",3:"Intermediate city",4:"Large city"}
TIER_COLORS = {1:"#81C784",2:"#388E3C",3:"#1B5E20",4:"#F57F17"}

def hex_to_rgba(hex_color, alpha=0.88):
    hex_color = str(hex_color).lstrip("#")
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"

def patch_color(tipo, fao_colors=None, alpha=0.88):
    base = (fao_colors or {}).get(tipo, "#CCCCCC")
    return hex_to_rgba(base, alpha)


# ── Indicador ajustado: área agropecuaria disponible ─────────────────────────
def _eval_terciles_mayor_mejor(serie):
    serie = pd.to_numeric(serie, errors="coerce")
    if serie.notna().sum() == 0:
        return np.nan
    p33 = serie.quantile(1/3)
    p66 = serie.quantile(2/3)
    return np.where(serie >= p66, 3, np.where(serie <= p33, 1, 2))

# Reemplaza el indicador proporcional anterior por un indicador absoluto.
# Prioriza el área sembrada total: cultivos temporeros + cultivos permanentes.
# Si esas columnas no están disponibles, usa superficie agropecuaria como respaldo.
_area_temp = "Sembradas con cultivos temporeros"
_area_perm = "Sembradas con cultivos permanentes"
_area_agro = "Superficie agropecuaria (Ha)"
_nuevo_ind_area = "Área agropecuaria disponible"
_nuevo_eval_area = "Área agropecuaria disponible_eval"

if _area_temp in df.columns and _area_perm in df.columns:
    df[_nuevo_ind_area] = pd.to_numeric(df[_area_temp], errors="coerce").fillna(0) + pd.to_numeric(df[_area_perm], errors="coerce").fillna(0)
elif _area_agro in df.columns:
    df[_nuevo_ind_area] = pd.to_numeric(df[_area_agro], errors="coerce")

if _nuevo_ind_area in df.columns:
    df[_nuevo_eval_area] = _eval_terciles_mayor_mejor(df[_nuevo_ind_area])
elif "% área sembrada c/cultivos perm+temp_eval" in df.columns:
    df[_nuevo_eval_area] = df["% área sembrada c/cultivos perm+temp_eval"]

# Estructura de categorías y sus indicadores evaluados
CATEGORIAS = {
    "Servicios de soporte": [
        ("Electricidad",         "% cobertura electricidad_eval"),
        ("Agua potable",         "% cobertura agua potable_eval"),
        ("Internet",             "% cobertura internet_eval"),
    ],
    "Capital social": [
        ("Inseg. alimentaria",   "% inseguridad alimentaria (productor)_eval"),
        ("Índice GINI",          "Indice GINI 2025_eval"),
        ("Titulares mujeres",    "% titulares mujeres (UA)_eval"),
        ("Mujeres productoras",  "% mujeres productoras_eval"),
        ("Mujeres f. laboral",   "% mujeres en fuerza laboral_eval"),
        ("Agr. familiares FAO",  "% agricultores familiares (FAO)_eval"),
        ("Pequeños productores", "% pequeños productores_eval"),
        ("Propietarios",         "% productores propietarios_eval"),
        ("Vulnerabilidad territ.","Vulnerabilidad territorial_eval"),
    ],
    "Tecnología e innovación": [
        ("Asist. técnica",       "% parcelas con asistencia técnica_eval"),
        ("Crédito",              "% productores con crédito_eval"),
        ("Pres. innovación",     "% presupuesto innovación agro_eval"),
        ("Tecnificación riego",  "% Tecnificación (riego)_eval"),
    ],
    "Producción": [
        ("Área agropecuaria disponible", "Área agropecuaria disponible_eval"),
        ("Actividad agrícola",   "% actividad agrícola principal_eval"),
        ("Actividad ganadera",   "% actividad ganadera principal_eval"),
        ("UA < 1 Ha",            "% UA menores de 1 Ha_eval"),
        ("Org. rural",           "% productores en organización rural_eval"),
    ],
    "Competitividad y mercados": [
        ("Volumen exportador",   "Volumen y Alcance Exportador_eval"),
        ("Densidad exportadora", "Densidad Empresarial Exportadora_eval"),
        ("N° Centros urbanos",   "N° Centros Urbanos_eval"),
        ("Concentración urbana", "Población centro / Pob.urbana_eval"),
    ],
}

# Calificación general por categoría (del Excel: cols AH-AL)
# Score = valor de Entorno precomputado
SCORE_COLS = {
    "Servicios de soporte":     "score_ss",
    "Capital social":           "score_cs",
    "Tecnología e innovación":  "score_ti",
    "Producción":               "score_pr",
    "Competitividad y mercados":"score_cm",
}
# Calcular scores por categoría desde los _eval disponibles
for cat, inds in CATEGORIAS.items():
    cols_cat = [c for _,c in inds if c in df.columns]
    key = SCORE_COLS[cat]
    df[key] = df[cols_cat].mean(axis=1) / 3 * 100

CAT_COLORS = {
    "Servicios de soporte":     "#1565C0",
    "Capital social":           "#2E7D32",
    "Tecnología e innovación":  "#6A1B9A",
    "Producción":               "#E65100",
    "Competitividad y mercados":"#B71C1C",
}

# ── SIDEBAR: capas del mapa ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🗺️ Capas del mapa")

    # Capa de color choropleth
    CAPAS_CHORO = {
        "Ninguno":                 None,
        "Cierre de brechas":       "score_brechas",
        "Competitividad":          "score_competitividad",
        "Servicios de soporte":    "score_ss",
        "Capital social":          "score_cs",
        "Tecnología e innovación": "score_ti",
        "Producción":              "score_pr",
        "Competitividad y mercados":"score_cm",
        "GINI 2025":               "Indice GINI 2025_eval",
        "Inseg. alimentaria":      "% inseguridad alimentaria (productor)_eval",
        "Vulnerabilidad territorial":"Vulnerabilidad territorial_eval",
        "Crédito":                 "% productores con crédito_eval",
        "Asistencia técnica":      "% parcelas con asistencia técnica_eval",
        "Volumen exportador":      "Volumen y Alcance Exportador_eval",
        "Área agropecuaria disponible": "Área agropecuaria disponible",
    }
    capa_choro = st.selectbox("Seleccione el indicador", list(CAPAS_CHORO.keys()), key="choro")

    st.markdown("---")
    st.markdown("**Capas FAO City-Region Explorer:**")

    mostrar_patches = st.checkbox("Patches de acceso urbano", value=False)
    if mostrar_patches:
        cutoff_sel = st.radio("Travel time", ["1h","2h","3h"], horizontal=True, key="cutoff")
    else:
        cutoff_sel = "1h"

    mostrar_cu = st.checkbox("Centros urbanos FAO", value=True)

    if mostrar_patches:
        st.markdown("**Leyenda patches:**")
        tipos_legend = {
            "4444":"Large city (todos los accesos)",
            "3334":"Intermediate + Large",
            "3330":"Solo Intermediate city",
            "2244":"Small + Large",
            "2234":"Small + Intermediate + Large",
            "2230":"Small + Intermediate",
            "2200":"Solo Small city",
            "1444":"Large + Small + Town",
            "1330":"Small + Intermediate + Town",
            "1234":"Todos los tiers",
            "1244":"Small + Large + Town",
            "1230":"Small + Intermediate + Town",
            "1200":"Small + Town",
            "1000":"Solo Town",
        }
        for tipo_str, desc in tipos_legend.items():
            tipo = int(tipo_str)
            color = fao["fao_colors"].get(tipo,"#CCC")
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:6px;font-size:.72rem;margin:.15rem 0;">'
                f'<div style="width:14px;height:10px;border-radius:2px;background:{color};flex-shrink:0;"></div>'
                f'{tipo_str} — {desc}</div>', unsafe_allow_html=True)

    if mostrar_cu:
        st.markdown("**Leyenda centros urbanos:**")
        for tier, lbl in TIER_LABELS.items():
            c = TIER_COLORS[tier]
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:6px;font-size:.72rem;margin:.1rem 0;">'
                f'<div style="width:10px;height:10px;border-radius:50%;background:{c};flex-shrink:0;"></div>'
                f'{lbl}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div style="font-size:.68rem;color:#AAA;">FAO UTF-COL-178 / SARA<br>RENAGRO 2024 + FAO City-Region Explorer</div>', unsafe_allow_html=True)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="metarec-header">
  <h1>🇩🇴 METAREC — República Dominicana</h1>
  <p>Metodología para la valoración y análisis de cadenas para la reactivación económica
     · Adaptación a República Dominicana · 10 regiones de planificación · RENAGRO 2024 + FAO City-Region Explorer</p>
</div>
""", unsafe_allow_html=True)

# ── MAPA ──────────────────────────────────────────────────────────────────────
col_var_key = CAPAS_CHORO.get(capa_choro)

@st.cache_data(show_spinner=False)
def build_mapa(col_var, mostrar_cu, mostrar_patches, cutoff_sel, _fao):
    fig = go.Figure()

    # ── Regiones (choropleth) ─────────────────────────────────────────────────
    if col_var and col_var in df.columns:
        vals = df.set_index("cod_region")[col_var].to_dict()
        num_vals = {k:v for k,v in vals.items() if pd.notna(v)}
        vmin = min(num_vals.values()) if num_vals else 0
        vmax = max(num_vals.values()) if num_vals else 3

        for cod, d in reg_json.items():
            v = vals.get(cod, np.nan)
            if pd.isna(v):
                fill = "rgba(200,200,200,0.3)"
            else:
                # Escala correcta: valores bajos = rojo, medios = amarillo/naranja, altos = verde
                norm = (v - vmin) / (vmax - vmin + 1e-9)
                if norm < 0.5:
                    # Rojo -> Amarillo
                    t = norm * 2
                    r = int(192 + t*(245-192))
                    g = int(57  + t*(176-57))
                    b = int(43  + t*(65-43))
                else:
                    # Amarillo -> Verde
                    t = (norm-0.5)*2
                    r = int(245 + t*(39-245))
                    g = int(176 + t*(174-176))
                    b = int(65  + t*(96-65))
                fill = f"rgba({r},{g},{b},0.58)"
            nom = d.get("nombre","")
            val_str = f"{v:.1f}" if not pd.isna(v) else "—"
            fig.add_trace(go.Scattermapbox(
                lon=d["lons"], lat=d["lats"],
                mode="lines", fill="toself",
                fillcolor=fill,
                line=dict(color="rgba(70,70,70,0.55)", width=1.1),
                name=nom,
                hovertemplate=f"<b>{nom}</b><br>{capa_choro}: {val_str}<extra></extra>",
                showlegend=False,
            ))
            # Etiqueta
            fig.add_trace(go.Scattermapbox(
                lon=[d["cx"]], lat=[d["cy"]], mode="text",
                text=[nom],
                textfont=dict(size=9.5, color="#1B4332"),
                hoverinfo="skip", showlegend=False,
            ))
    else:
        # Sin capa: solo bordes
        for cod, d in reg_json.items():
            nom = d.get("nombre","")
            fig.add_trace(go.Scattermapbox(
                lon=d["lons"], lat=d["lats"], mode="lines",
                fill="toself", fillcolor="rgba(255,255,255,0.08)",
                line=dict(color="rgba(70,70,70,0.55)", width=1.1),
                name=nom, hovertemplate=f"<b>{nom}</b><extra></extra>", showlegend=False,
            ))

    # ── Centros urbanos ────────────────────────────────────────────────────────
    if mostrar_cu:
        for cu in _fao["urban_centres"]:
            tier = cu["tier"]
            color = TIER_COLORS.get(tier,"#999")
            size  = {1:7,2:10,3:14,4:20}.get(tier,7)
            fig.add_trace(go.Scattermapbox(
                lon=[cu["cx"]], lat=[cu["cy"]], mode="markers",
                marker=dict(size=size, color=color, opacity=0.95, sizemode="diameter"),
                name=TIER_LABELS.get(tier,""),
                text=cu["name"],
                hovertemplate=(
                    f"<b>{cu['name']}</b><br>"
                    f"Tier: {TIER_LABELS.get(tier,'')}<br>"
                    f"Pob. (GHS-POP 2020): {int(cu.get('ghspop',0) or 0):,}<extra></extra>"
                ),
                showlegend=False,
            ))

    # ── Patches FAO ───────────────────────────────────────────────────────────
    if mostrar_patches and cutoff_sel in _fao["patches"]:
        por_tipo = _fao["patches"][cutoff_sel]
        for tipo, coords in sorted(por_tipo.items()):
            color = patch_color(tipo, _fao.get("fao_colors", {}), 0.88)
            desc  = _fao.get("tier_desc",{}).get(tipo, str(tipo))
            fig.add_trace(go.Scattermapbox(
                lon=coords["lons"], lat=coords["lats"],
                mode="lines", fill="toself",
                fillcolor=color,
                line=dict(color="rgba(80,80,80,0.45)", width=0.45),
                opacity=1,
                name=f"{tipo} — {desc}",
                hovertemplate=f"<b>{desc}</b><br>Tipo: {tipo}<br>Travel time: {cutoff_sel}<extra></extra>",
                showlegend=False,
            ))

    fig.update_layout(
        mapbox=dict(style="carto-positron",
                    center=dict(lat=18.75, lon=-70.2), zoom=6.8),
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=0,b=0), height=520,
    )
    return fig

fig_mapa = build_mapa(col_var_key, mostrar_cu, mostrar_patches, cutoff_sel, fao)
st.plotly_chart(fig_mapa, use_container_width=True, config={"displayModeBar":True,
    "modeBarButtonsToRemove":["lasso2d","select2d"],"displaylogo":False})

# ── RADAR + RANKING ───────────────────────────────────────────────────────────
st.markdown("---")
col_radar, col_rank = st.columns([1.3, 1], gap="large")

BRECHAS_VARS = {
    "Electricidad":         "% cobertura electricidad_eval",
    "Agua potable":         "% cobertura agua potable_eval",
    "Internet":             "% cobertura internet_eval",
    "Inseg. alimentaria":   "% inseguridad alimentaria (productor)_eval",
    "GINI":                 "Indice GINI 2025_eval",
    "Mujeres productoras":  "% mujeres productoras_eval",
    "Propietarios":         "% productores propietarios_eval",
}
COMPET_VARS = {
    "Org. rural":           "% productores en organización rural_eval",
    "Asist. técnica":       "% parcelas con asistencia técnica_eval",
    "Crédito":              "% productores con crédito_eval",
    "Tecnif. riego":        "% Tecnificación (riego)_eval",
    "Volumen export.":      "Volumen y Alcance Exportador_eval",
    "Densidad export.":     "Densidad Empresarial Exportadora_eval",
    "Vulnerabilidad":       "Vulnerabilidad territorial_eval",
}

with col_radar:
    st.markdown('<div class="sec-title">Variables transformadoras</div>', unsafe_allow_html=True)
    reg_sel_nom = st.selectbox("Región", list(REG_NOMBRES.values()), key="reg_radar")
    reg_sel_cod = next(k for k,v in REG_NOMBRES.items() if v==reg_sel_nom)
    row_r = df[df["cod_region"]==reg_sel_cod].iloc[0]

    def radar_fig(vars_dict, titulo, color_l, color_f):
        cats = list(vars_dict.keys())
        vals = [float(row_r.get(c,0) or 0) for c in vars_dict.values()]
        fig = go.Figure()
        for v_ref, cf in [(3,"rgba(39,174,96,.06)"),(2,"rgba(230,126,34,.05)"),(1,"rgba(192,57,43,.05)")]:
            fig.add_trace(go.Scatterpolar(
                r=[v_ref]*len(cats)+[v_ref], theta=cats+[cats[0]],
                fill="toself", fillcolor=cf,
                line=dict(color="rgba(0,0,0,.07)",width=.6,dash="dot"),
                showlegend=False, hoverinfo="skip",
            ))
        fig.add_trace(go.Scatterpolar(
            r=vals+[vals[0]], theta=cats+[cats[0]],
            fill="toself", fillcolor=color_f,
            line=dict(color=color_l, width=2.5),
            name=reg_sel_nom,
            hovertemplate="<b>%{theta}</b><br>Calificación: %{r}<extra></extra>",
        ))
        fig.update_layout(
            polar=dict(bgcolor="rgba(250,252,250,1)",
                radialaxis=dict(visible=True,range=[0,3.2],
                    tickvals=[1,2,3],ticktext=["Baja","Media","Alta"],
                    tickfont=dict(size=8,color="#AAA"),
                    gridcolor="#E8E8E8",linecolor="#DDD"),
                angularaxis=dict(tickfont=dict(size=9.5,color="#333"),
                    gridcolor="#EEE",linecolor="#DDD")),
            showlegend=False,
            title=dict(text=f"<b>{titulo}</b>",x=.5,y=.97,
                       font=dict(size=12,color="#1C1C1C")),
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=45,r=45,t=50,b=30), height=310,
        )
        return fig

    r1, r2 = st.columns(2)
    with r1:
        st.plotly_chart(radar_fig(BRECHAS_VARS,"Cierre de brechas","#1A4A7A","rgba(26,74,122,.15)"),
                        use_container_width=True, config={"displayModeBar":False})
    with r2:
        st.plotly_chart(radar_fig(COMPET_VARS,"Competitividad","#1B6B3A","rgba(27,107,58,.15)"),
                        use_container_width=True, config={"displayModeBar":False})

with col_rank:
    st.markdown('<div class="sec-title">Ranking regional</div>', unsafe_allow_html=True)
    df_rk = df[["region","score_brechas","score_competitividad"]].copy().sort_values("score_brechas",ascending=False)

    def badge(v):
        if pd.isna(v): return "—"
        cls = "bg-alto" if v>80 else "bg-bajo" if v<60 else "bg-med"
        return f'<span class="score-cell {cls}" style="display:inline-block;min-width:42px;border-radius:3px;padding:.08rem .25rem;">{v:.0f}</span>'

    html_rk = '<table class="eval-tbl"><tr><th>#</th><th style="text-align:left">Región</th><th>Brechas</th><th>Competitividad</th></tr>'
    for i, (_, row) in enumerate(df_rk.iterrows(), 1):
        html_rk += f'<tr><td style="color:#AAA;font-size:.72rem">{i}</td><td style="text-align:left">{row["region"].replace(" o Metropolitana","")}</td><td>{badge(row["score_brechas"])}</td><td>{badge(row["score_competitividad"])}</td></tr>'
    html_rk += "</table>"
    st.markdown(html_rk, unsafe_allow_html=True)

# ── TABLA EVALUADA ────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="sec-title">Matriz evaluada por indicador (calificación 1–3)</div>', unsafe_allow_html=True)

# Encabezados de tabla
reg_headers = "".join(f'<th>{REG_NOMBRES[c].replace(" o Metropolitana","")}</th>' for c in REGIONES_ORD)
html_tbl = f'<table class="eval-tbl"><tr><th style="text-align:left;min-width:160px">Categoría / Indicador</th>{reg_headers}<th>Resultado</th></tr>'

def vhtml(v):
    if v is None or (isinstance(v,float) and np.isnan(v)): return '<td>—</td>'
    v = int(v)
    cls = {1:"v1",2:"v2",3:"v3"}.get(v,"")
    sym = {1:"▼",2:"◆",3:"▲"}.get(v,"")
    return f'<td class="{cls}">{sym}{v}</td>'

for cat, inds in CATEGORIAS.items():
    cat_color = CAT_COLORS.get(cat,"#333")
    # Fila de categoría con score
    score_key = SCORE_COLS[cat]
    scores_cat = "".join(
        f'<td></td>' for _ in REGIONES_ORD
    )
    score_vals = df.set_index("cod_region")[score_key]
    scores_html = "".join(
        f'<td class="score-cell {"bg-alto" if score_vals.get(c,0)>80 else "bg-bajo" if score_vals.get(c,0)<60 else "bg-med"}">{score_vals.get(c,0):.0f}</td>'
        for c in REGIONES_ORD
    )
    html_tbl += f'<tr class="cat-hdr"><td colspan="1" style="border-left:4px solid {cat_color};padding-left:.6rem;">{cat}</td>{scores_html}<td></td></tr>'

    # Filas de indicadores
    for lbl, col in inds:
        if col not in df.columns:
            continue
        vals_row = df.set_index("cod_region")[col]
        tds = "".join(vhtml(vals_row.get(c, np.nan)) for c in REGIONES_ORD)
        html_tbl += f'<tr><td class="ind-name" style="padding-left:1rem;">{lbl}</td>{tds}<td></td></tr>'

# Filas de scores globales y variables transformadoras
def score_bg(v):
    if pd.isna(v):
        return ""
    return "bg-alto" if v > 80 else "bg-bajo" if v < 60 else "bg-med"

html_tbl += '<tr style="font-weight:700;"><td style="text-align:left;">TOTAL ENTORNO</td>'
for c in REGIONES_ORD:
    tot_row = df[df["cod_region"]==c]
    all_scores = [tot_row[k].values[0] if k in tot_row.columns else np.nan for k in SCORE_COLS.values()]
    total = np.nanmean(all_scores)
    html_tbl += f'<td class="score-cell {score_bg(total)}">{total:.0f}</td>'
html_tbl += '<td></td></tr>'

for label, col_score in [
    ("TOTAL VARIABLES TRANSFORMADORAS PARA CIERRE DE BRECHAS SOCIALES", "score_brechas"),
    ("TOTAL VARIABLES TRANSFORMADORAS PARA COMPETITIVIDAD", "score_competitividad"),
]:
    html_tbl += f'<tr style="font-weight:700;"><td style="text-align:left;">{label}</td>'
    score_vals = df.set_index("cod_region")[col_score] if col_score in df.columns else pd.Series(dtype=float)
    for c in REGIONES_ORD:
        val = score_vals.get(c, np.nan)
        html_tbl += f'<td class="score-cell {score_bg(val)}">{val:.0f}</td>' if pd.notna(val) else '<td>—</td>'
    html_tbl += '<td></td></tr>'

html_tbl += "</table>"

st.markdown(f'<div style="overflow-x:auto;">{html_tbl}</div>', unsafe_allow_html=True)

# ── PIE ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;font-size:.7rem;color:#B0B0B0;margin-top:1.5rem;
  padding-top:1rem;border-top:1px solid #EEE;">
  METAREC · Adaptación República Dominicana · FAO UTF-COL-178 / SARA ·
  RENAGRO 2024 · Precenso RENAGRO 2024 · FAO City-Region Explorer (Cattaneo et al., 2024)
  · ProDominicana · ONE/ENFT · DIGEPRES/MEPYD
</div>""", unsafe_allow_html=True)
