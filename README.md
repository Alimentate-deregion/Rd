# Visor Territorial Agroalimentario — República Dominicana

Sistema de diagnóstico de capacidades productivas regionales para las 10 regiones de República Dominicana.

## Fuentes de datos

| Archivo | Fuente | Cobertura |
|---|---|---|
| `renagro_master.parquet` | RENAGRO 2024 · Ministerio de Agricultura RD | 10 regiones · 58 variables |
| `indicadores_regionales.parquet` | Calculado sobre RENAGRO 2024 | 43 indicadores derivados + IPT |
| `consolidado_agg.parquet` | Consolidado Regional SC&P · Min. Agricultura RD | 2000–2024 · 8 regiones · 118 productos |
| `consolidado_nacional.parquet` | Agregado nacional del consolidado | 2000–2024 · siembra/cosecha/producción |

## Pilares del visor

1. **Capacidad Productiva** — productores, superficie, cultivos, fuerza laboral
2. **Agua y Resiliencia** — riego, limitaciones ambientales
3. **Servicios de Apoyo** — asistencia técnica, maquinaria
4. **Financiamiento** — crédito agropecuario
5. **Organización y Vulnerabilidad** — asociatividad, inseguridad alimentaria

## Despliegue local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Estructura

```
app.py
requirements.txt
Datos/
  renagro_master.parquet
  indicadores_regionales.parquet
  consolidado_agg.parquet
  consolidado_nacional.parquet
.streamlit/
  config.toml
```

---
FAO UTF-COL-178 / SARA · Visor Territorial Agroalimentario RD
