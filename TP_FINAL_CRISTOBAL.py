
"""
TP Final – Análisis de precipitación en SESA
Autor: Ignacio N. Cristobal
Versión corregida
"""

#%% Importo librerías

import os
import numpy as np
import pandas as pd
from netCDF4 import Dataset
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

#%% Directorio de trabajo

# El script ahora usa el directorio donde se ejecuta.
os.makedirs("Carpeta_guardado", exist_ok=True)

#%% Apertura del archivo

data = Dataset("./precip.CPC.nc", mode='r', format='NETCDF4')

precip   = data.variables["precip"][:].filled()
time     = data.variables["time"][:].filled()
Latitud  = data.variables["lat"][:].filled()
Longitud = data.variables["lon"][:].filled()

# Conversión de longitud 0–360 -> -180–180
Longitud = Longitud - 360

# Reemplazo valor faltante por NaN
precip[precip == -9.96921e+36] = np.nan

data.close()

#%% A – Región SESA y mapa de ubicación

# Selección de la región SESA: 40°S–20°S, 66°W–50°W
mask_lat = (Latitud >= -40) & (Latitud <= -20)
mask_lon = (Longitud <= -50) & (Longitud >= -66)

Region_SESA = precip[:, mask_lat, :]
Region_SESA = Region_SESA[:, :, mask_lon]

# Mapa de la región de estudio
map_crs = ccrs.PlateCarree()

fig = plt.figure(figsize=(8, 8))
ax = plt.axes(projection=map_crs)
ax.set_extent([-66, -50, -40, -20], crs=map_crs)

ax.add_feature(cfeature.LAND,      facecolor="#FFDEAD")
ax.add_feature(cfeature.OCEAN,     facecolor="#4682B4")
ax.add_feature(cfeature.BORDERS,   linewidth=0.6)
ax.add_feature(cfeature.COASTLINE, linewidth=0.7)
ax.add_feature(cfeature.LAKES,     edgecolor="#4682B4", facecolor="#6495ED",
               linewidth=0.5, alpha=0.6)
ax.add_feature(cfeature.RIVERS,    edgecolor="#4682B4", linewidth=0.4, alpha=0.6)

gl = ax.gridlines(draw_labels=True, linewidth=0.3, linestyle="--", alpha=0.6)
gl.top_labels   = False
gl.right_labels = False

plt.title("Región de estudio: SESA (40°S–20°S, 66°W–50°W)")
plt.savefig("Carpeta_guardado/Region_de_estudio.png", dpi=300, bbox_inches="tight")
plt.show()

#%% B – Datos faltantes

total_datos = Region_SESA.size
faltantes   = np.isnan(Region_SESA).sum()

Datos = pd.DataFrame({
    "Cantidad total de datos":    [total_datos],
    "Cantidad total de faltantes":[faltantes],
    "Dato faltante original":     [-9.96921e+36]
})

Datos.to_csv("Carpeta_guardado/Datos_.txt", sep="\t", index=False)

#%% C – Precipitación media diaria 1981–2010 por semestre

n      = precip.shape[0]
fechas = pd.date_range(start="1979-01-01", periods=n, freq="D")

# Período de referencia 1981–2010 (incluye oct-1980 para el semestre cálido)
mask_81_10    = (fechas >= "1980-10-01") & (fechas <= "2011-03-31")
fechas_81_10  = fechas[mask_81_10]
Region_SESA_81_10 = Region_SESA[mask_81_10, :, :]

# Semestres
mask_calido   = (fechas_81_10.month >= 10) | (fechas_81_10.month <= 3)
mask_frio     = (fechas_81_10.month >= 4)  & (fechas_81_10.month <= 9)
precip_calido = Region_SESA_81_10[mask_calido, :, :]
precip_frio   = Region_SESA_81_10[mask_frio,   :, :]

umbral_lluvia = 1  # mm — umbral mínimo para considerar un día lluvioso

# ── Función auxiliar para evitar repetición de código ──────────────────────
def media_dias_lluvia(arr, umbral):
    """Precipitación media diaria considerando sólo días con lluvia > umbral."""
    mask  = arr > umbral
    suma  = np.where(mask, arr, 0).sum(axis=0)
    n_dias = mask.sum(axis=0)
    media  = np.full_like(suma, np.nan, dtype=float)
    ok     = n_dias > 0
    media[ok] = suma[ok] / n_dias[ok]
    return media

media_calido = media_dias_lluvia(precip_calido, umbral_lluvia)
media_frio   = media_dias_lluvia(precip_frio,   umbral_lluvia)

# Grilla espacial para graficar
lat_1d = Latitud[mask_lat]
lon_1d = Longitud[mask_lon]
Lon_SESA, Lat_SESA = np.meshgrid(lon_1d, lat_1d)

# Gráfico de 2 paneles
map_crs = ccrs.PlateCarree()
fig, axs = plt.subplots(1, 2, figsize=(11, 4),
                         subplot_kw={'projection': map_crs})
fig.subplots_adjust(wspace=0.05, top=0.88)

campos  = [media_calido, media_frio]
titulos = ["Semestre cálido (Oct–Mar)", "Semestre frío (Abr–Sep)"]

for i, ax in enumerate(axs):
    ax.set_extent([-66, -50, -40, -20], crs=map_crs)
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle='-', alpha=0.5)
    im = ax.contourf(Lon_SESA, Lat_SESA, campos[i],
                     cmap="YlGnBu", transform=map_crs,
                     levels=np.arange(0, 15), extend="max")
    ax.set_title(titulos[i], fontsize=11)
    gl = ax.gridlines(draw_labels=True, linewidth=0.4, color='gray',
                      alpha=0.6, linestyle='--')
    gl.top_labels   = False
    gl.right_labels = False
    gl.xlabel_style = {"size": 8}
    gl.ylabel_style = {"size": 8}

fig.suptitle("Precipitación Media Diaria en SESA (1981–2010)",
             fontsize=14, fontweight="bold")
fig.colorbar(im, ax=axs, location="right",
             label="Precipitación media diaria (mm)")
plt.savefig("Carpeta_guardado/PMD_calido_frio.png", dpi=300, bbox_inches="tight")
plt.show()

#%% D – Índices de precipitación

umbral_lluvia = 1

# PRPTOT: acumulado total de precipitación en días lluviosos
mask_PRPTOT  = Region_SESA > umbral_lluvia
suma_PRPTOT  = np.where(mask_PRPTOT, Region_SESA, 0).sum(axis=0).astype(float)
suma_PRPTOT[suma_PRPTOT == 0] = np.nan

# R10mm: acumulado en días con precipitación > 10 mm
mask_R10  = Region_SESA > 10
suma_R10mm = np.where(mask_R10, Region_SESA, 0).sum(axis=0).astype(float)
suma_R10mm[suma_R10mm == 0] = np.nan

# R20mm: acumulado en días con precipitación > 20 mm
mask_R20  = Region_SESA > 20
R20mm     = mask_R20.sum(axis=0)          # cantidad de días con PP > 20 mm
suma_R20mm = np.where(mask_R20, Region_SESA, 0).sum(axis=0).astype(float)
suma_R20mm[suma_R20mm == 0] = np.nan

# Función auxiliar para los mapas de índices
def mapa_indice(campo, titulo, fname):
    fig = plt.figure(figsize=(8, 10))
    ax  = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([-66, -50, -40, -20], crs=ccrs.PlateCarree())
    im = ax.contourf(Lon_SESA, Lat_SESA, campo,
                     levels=12, cmap="Blues", extend="both",
                     transform=ccrs.PlateCarree())
    ax.add_feature(cfeature.BORDERS,   edgecolor='black', linewidth=1.2)
    ax.add_feature(cfeature.COASTLINE, edgecolor='black', linewidth=1.0)
    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="gray",
                      alpha=0.6, linestyle="--")
    gl.top_labels   = False
    gl.right_labels = False
    plt.title(titulo, fontsize=14)
    plt.colorbar(im, label="Precipitación (mm)")
    plt.tight_layout()
    plt.savefig(f"Carpeta_guardado/{fname}.png", dpi=300, bbox_inches="tight")
    plt.show()

mapa_indice(suma_PRPTOT, "Acumulado PRPTOT – SESA (1979–2019)", "PRPTOT")
mapa_indice(suma_R10mm,  "Acumulado R10mm – SESA (1979–2019)",  "R10mm")
mapa_indice(suma_R20mm,  "Acumulado R20mm – SESA (1979–2019)",  "R20mm")

#%% E – Series temporales con tendencia lineal

def serie_mensual(arr, fechas_arr, label, fname):
    """Promedio areal → agregación mensual → gráfico con tendencia."""
    prom = np.nanmean(arr, axis=(1, 2))

    df = pd.DataFrame({
        "anio": fechas_arr.year,
        "mes":  fechas_arr.month,
        "pp":   prom
    })
    mensual = df.groupby(["anio", "mes"])["pp"].sum()

    idx = pd.to_datetime({
        "year":  mensual.index.get_level_values("anio"),
        "month": mensual.index.get_level_values("mes"),
        "day":   1
    })

    fig, ax = plt.subplots(figsize=(9, 3))
    ax.plot(idx, mensual.values, linewidth=1.5, label=label)

    # Tendencia lineal
    x_ord = idx.map(pd.Timestamp.toordinal)
    coef  = np.polyfit(x_ord, mensual.values, 1)
    ax.plot(idx, np.poly1d(coef)(x_ord), color="red",
            linewidth=2, label="Tendencia lineal")

    ax.set_title(f"Precipitación media mensual – {label}")
    ax.set_xlabel("Tiempo")
    ax.set_ylabel("PP acumulada (mm)")
    ax.grid(alpha=0.3)
    ax.legend()
    plt.tight_layout()
    plt.savefig(f"Carpeta_guardado/{fname}.png", dpi=300, bbox_inches="tight")
    plt.show()

serie_mensual(precip_calido, fechas_81_10[mask_calido],
              "Semestre cálido (Oct–Mar)", "PP_media_mensual_calido")

serie_mensual(precip_frio, fechas_81_10[mask_frio],
              "Semestre frío (Abr–Sep)", "PP_media_mensual_frio")