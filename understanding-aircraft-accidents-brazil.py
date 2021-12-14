# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.0
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Understanding aircraft accidents
#
# When aircraft accidents happen it generates a lot of commotion and
# people want to know what caused it. In Brazil, they are investigated
# by the Center for Investigation and Prevention of Aircraft Accidents
# (*Centro de Investigação e Prevenção de Acidentes Aeronáuticos* –
# Cenipa), after which publishes reports on its findings. The data on
# all that published yearly as open data.
#
# We're going to take a look at that.

# %%
from datetime import date, time, datetime

# %%
import locale

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

# %%
import pandas as pd
import numpy as np

import plotly.io as pio
import plotly.express as px
import folium

# %%
pio.templates.default='plotly_dark'

# %% [markdown] tags=[]
# ## Source of data: Cenipa
#
# Cenipa has actually been one of the first public organizations in
# Brazil to publish open data. The
# [dataset](https://dados.gov.br/dataset/ocorrencias-aeronauticas-da-aviacao-civil-brasileira)
# is on the Brazilian open data portal and is updated yearly.

# %% [markdown]
# ## Loading the tables

# %%
df_tipo_ocorrencia = pd.read_csv('http://sistema.cenipa.aer.mil.br/cenipa/media/opendata/ocorrencia_tipo.csv', sep=';')

# %%
df_aeronave = pd.read_csv('http://sistema.cenipa.aer.mil.br/cenipa/media/opendata/aeronave.csv', sep=';')

# %%
df_fator_contribuinte = pd.read_csv('http://sistema.cenipa.aer.mil.br/cenipa/media/opendata/fator_contribuinte.csv', sep=';')

# %%
df_ocorrencia = pd.read_csv('http://sistema.cenipa.aer.mil.br/cenipa/media/opendata/ocorrencia.csv', sep=';')

# %% [markdown]
# ### Cleanup

# %%
df_ocorrencia['ocorrencia_data'] = df_ocorrencia.apply(
    lambda row: datetime.strptime(
        row['ocorrencia_dia'] + ' ' +
        (row['ocorrencia_hora'] if isinstance(row['ocorrencia_hora'], str) else '00:00:00'), '%d/%m/%Y %H:%M:%S'),
    axis=1
)


# %%
def clean_float(original: str) -> float:
    if isinstance(original, float):
        return original
    try:
        return locale.atof(original)
    except ValueError:
        return np.NaN

df_ocorrencia['ocorrencia_latitude'] = df_ocorrencia['ocorrencia_latitude'].apply(clean_float)
df_ocorrencia['ocorrencia_longitude'] = df_ocorrencia['ocorrencia_longitude'].apply(clean_float)

# %%
# separates the category type
df_tipo_ocorrencia['ocorrencia_tipo_categoria'] = \
    df_tipo_ocorrencia['ocorrencia_tipo_categoria'].apply(lambda t: t.split('|')[0].strip())

# %% [markdown]
# ## Basic data exploration

# %% [markdown]
# ### Occurrence

# %%
df_ocorrencia.info()

# %%
occurencies_in_time = df_ocorrencia.groupby(pd.Grouper(key='ocorrencia_data', axis=0, freq='M')).codigo_ocorrencia.count()
occurencies_in_time

# %%
px.line(
    occurencies_in_time,
    title='Occurencies per month',
    labels={
        'index': 'date',
        'ocorrencia_data': 'month'
    }
)

# %%
df_ocorrencia.ocorrencia_classificacao.value_counts()

# %%
px.bar(
    df_ocorrencia.ocorrencia_classificacao.value_counts().iloc[::-1],
    orientation='h',
    title='Occurrence class',
    labels={
        'index': 'category',
        'value': 'quantity',
    }
)

# %%
occurrence_in_time_by_class = (
    df_ocorrencia
    .set_index('ocorrencia_data')
    .groupby([pd.Grouper(freq='M'), 'ocorrencia_classificacao'])
    .codigo_ocorrencia
    .count()
)
occurrence_in_time_by_class

# %%
px.line(
    occurrence_in_time_by_class,
    x=occurrence_in_time_by_class.index.get_level_values(0),
    y=occurrence_in_time_by_class.values,
    color=occurrence_in_time_by_class.index.get_level_values(1),
    title='Occurencies by class per month',
    labels={
        'x': 'category',
        'y': 'quantity',
    }
)

# %%
accidents = df_ocorrencia[df_ocorrencia.ocorrencia_classificacao == 'ACIDENTE']

# %%
accidents_2020 = accidents[accidents.ocorrencia_data >= datetime(2020,1,1)]

# %%
len(accidents_2020[accidents_2020.ocorrencia_latitude.notna()])

# %% [markdown]
# There were 237 accidents in 2020. Let's see the location of those accidents in a map.

# %%
m = folium.Map(location=[-15.24,-51.33], zoom_start=4)
for occurence in accidents_2020[accidents_2020.ocorrencia_latitude.notna()].itertuples():
    folium.Marker(
        [occurence.ocorrencia_latitude, occurence.ocorrencia_longitude],
        popup=occurence.ocorrencia_cidade
    ).add_to(m)
m

# %%
investigation_status = df_ocorrencia.investigacao_status.value_counts()
investigation_status

# %% [markdown]
# Most investigations have already been finished.

# %%
px.pie(
    investigation_status,
    hole=0.6,
    title='Investigation status',
    names=investigation_status.index,
    values=investigation_status.values
)

# %%
df_ocorrencia.total_aeronaves_envolvidas.value_counts()

# %%
px.bar(
    df_ocorrencia.total_aeronaves_envolvidas.value_counts(),
    orientation='h',
    title='Number of aircraft involved',
    labels={
        'index': 'number of aircraft',
        'value': 'occurencies',
    }
)

# %% [markdown]
# ### Occurrence type

# %%
df_tipo_ocorrencia.info()

# %%
most_common_occurrence_types = df_tipo_ocorrencia.ocorrencia_tipo.value_counts().head(10)
most_common_occurrence_types

# %%
px.bar(
    most_common_occurrence_types.iloc[::-1],
    orientation='h',
    title='Most common occurrence types',
    labels={
        'index': 'category',
        'value': 'quantity',
    }
)

# %%
most_common_occurrence_categories = df_tipo_ocorrencia.ocorrencia_tipo_categoria.value_counts().head(10)
most_common_occurrence_categories

# %%
px.bar(
    most_common_occurrence_categories.iloc[::-1],
    orientation='h',
    title='Most common occurrence categories',
    labels={
        'index': 'category',
        'value': 'quantity',
    }
)

# %% [markdown]
# ### Aircraft

# %%
df_aeronave.info()

# %%
aircraft_types = df_aeronave.aeronave_tipo_veiculo.value_counts()
aircraft_types

# %%
px.bar(
    aircraft_types.iloc[::-1],
    orientation='h',
    title='Aircraft types',
    labels={
        'index': 'aircraft type',
        'value': 'quantity',
    }
)

# %%
aircraft_operator_type = df_aeronave.aeronave_operador_categoria.value_counts()
aircraft_operator_type

# %%
px.bar(
    aircraft_operator_type.iloc[:0:-1],
    orientation='h',
    title='Aircraft operator type',
    labels={
        'index': 'operator type',
        'value': 'quantity',
    }
)

# %%
most_common_aircraft_makers = df_aeronave.aeronave_fabricante.value_counts().head(10)
most_common_aircraft_makers

# %%
px.bar(
    most_common_aircraft_makers.iloc[::-1],
    orientation='h',
    title='Most common aircraft makers',
    labels={
        'index': 'maker',
        'value': 'quantity',
    }
)

# %%
most_common_aircraft_make_models = (
    df_aeronave[['aeronave_fabricante','aeronave_modelo']]
    .apply(lambda row: ' '.join(row), axis=1)
    .value_counts()
    .head(10)
)
most_common_aircraft_make_models

# %%
px.bar(
    most_common_aircraft_make_models.iloc[::-1],
    orientation='h',
    title='Most common aircraft make and models',
    labels={
        'index': 'make and model',
        'value': 'quantity',
    }
)

# %%
aircraft_motor_quantity = df_aeronave.aeronave_motor_quantidade.value_counts()
aircraft_motor_quantity

# %%
px.bar(
    aircraft_motor_quantity.iloc[::-1],
    orientation='h',
    title='Aircraft motor quantity',
    labels={
        'index': 'motor quantity',
        'value': 'quantity',
    }
)

# %% [markdown]
# People often say that accidents happen more often with
# small aircraft than with big aircraft. But does the data back it up?

# %%
df_aeronave.aeronave_assentos.describe()

# %%
df_aeronave.aeronave_assentos.value_counts()

# %%
px.box(
    df_aeronave.aeronave_assentos,
    orientation='h',
    labels={
        'value': 'seats quantity',
    }
)

# %% [markdown]
# The median number of seats is 6, so yes, the data does back it up.

# %%
valid_year_of_fabrication = df_aeronave[
    # exclude invalid numbers
    (df_aeronave.aeronave_ano_fabricacao > 0.0) &
    (df_aeronave.aeronave_ano_fabricacao < 2100.0)
]['aeronave_ano_fabricacao']

# %%
valid_year_of_fabrication.describe()

# %%
valid_year_of_fabrication.value_counts()

# %%
px.box(
    valid_year_of_fabrication,
    orientation='h',
    labels={
        'value': 'year of fabrication',
    }
)

# %% [markdown]
# Most common airdromes.

# %%
most_common_origin_airdromes = df_aeronave.aeronave_voo_origem.value_counts().head(12)
most_common_origin_airdromes

# %%
px.bar(
    most_common_origin_airdromes.iloc[:1:-1],
    orientation='h',
    title='Most common airdromes of origin',
    labels={
        'index': 'airdrome',
        'value': 'quantity',
    }
)

# %%
most_common_destination_airdromes = df_aeronave.aeronave_voo_destino.value_counts().head(12)
most_common_destination_airdromes

# %%
px.bar(
    most_common_destination_airdromes.iloc[:1:-1],
    orientation='h',
    title='Most common destination airdromes',
    labels={
        'index': 'airdrome',
        'value': 'quantity',
    }
)

# %%
operational_phases = df_aeronave.aeronave_fase_operacao.value_counts().head(10)
operational_phases

# %%
px.bar(
    operational_phases.iloc[::-1],
    orientation='h',
    title='Operational phases',
    labels={
        'index': 'phase',
        'value': 'quantity',
    }
)

# %%
operation_type = df_aeronave.aeronave_tipo_operacao.value_counts()
operation_type

# %%
px.bar(
    operation_type.iloc[::-1],
    orientation='h',
    title='Operation type',
    labels={
        'index': 'category',
        'value': 'quantity',
    }
)

# %%
damage_level = df_aeronave.aeronave_nivel_dano.value_counts()
damage_level

# %%
px.bar(
    damage_level.iloc[::-1],
    orientation='h',
    title='Damage level',
    labels={
        'index': 'level',
        'value': 'quantity',
    }
)

# %%
df_aeronave.aeronave_fatalidades_total.value_counts()

# %% [markdown]
# Most occurrences do not involve fatalities. Let's exclude the ones where there have been no damage to the aircraft and see the number of fatalities there.

# %%
df_aeronave[df_aeronave.aeronave_nivel_dano != 'NENHUM'].aeronave_fatalidades_total.value_counts()

# %% [markdown]
# Now also without the occurrences where the aircraft has been lightly damaged.

# %%
substantial_damage_or_more = df_aeronave[
    ~df_aeronave.aeronave_nivel_dano.isin(['NENHUM', 'LEVE'])
].aeronave_fatalidades_total
substantial_damage_or_more.value_counts()

# %%
substantial_damage_or_more.describe()

# %%
px.box(
    substantial_damage_or_more,
    orientation='h',
    title='Fatalities in occurencies where the aircraft has sustained substantial damage or more',
    labels={
        'value': 'number of fatalities',
    }
)

# %%
fatalities_aircraft_destroyed = df_aeronave[df_aeronave.aeronave_nivel_dano == 'DESTRUÍDA'].aeronave_fatalidades_total

# %%
fatalities_aircraft_destroyed.describe()

# %%
px.box(
    fatalities_aircraft_destroyed,
    orientation='h',
    title='Fatalities in occurencies where the aircraft was completely destroyed',
    labels={
        'value': 'number of fatalities',
    }
)

# %% [markdown]
# ### Contributing factor

# %%
df_fator_contribuinte.info()

# %%
df_fator_contribuinte

# %%
contributing_factor_area = df_fator_contribuinte.fator_area.value_counts()
contributing_factor_area

# %%
px.bar(
    contributing_factor_area.iloc[::-1],
    orientation='h',
    title='Area of contributing factor',
    labels={
        'index': 'category',
        'value': 'quantity',
    }
)

# %% [markdown]
# Operational factors are the most common. Let's explore
# which conditional factors happen more often in this case.

# %%
operational_factor_conditioning = \
    df_fator_contribuinte[df_fator_contribuinte.fator_area == 'FATOR OPERACIONAL']
operational_factor_conditioning['fator_condicionante'].value_counts()

# %%
px.bar(
    operational_factor_conditioning['fator_condicionante'].value_counts().iloc[::-1],
    orientation='h',
    title='Conditioning of operational factors',
    labels={
        'index': 'category',
        'value': 'quantity',
    }
)

# %%
aircraft_operation = operational_factor_conditioning[
    operational_factor_conditioning.fator_condicionante == 'OPERAÇÃO DA AERONAVE'
]
aircraft_operation.fator_nome.value_counts()

# %%
px.bar(
    aircraft_operation.fator_nome.value_counts().head(10).iloc[::-1],
    orientation='h',
    title='Most common aircraft operational factors',
    labels={
        'index': 'factor',
        'value': 'quantity',
    }
)

# %%
human_factor_conditioning = \
    df_fator_contribuinte[df_fator_contribuinte.fator_area == 'FATOR HUMANO']
human_factor_conditioning['fator_condicionante'].value_counts()

# %%
px.bar(
    human_factor_conditioning['fator_condicionante'].value_counts().iloc[::-1],
    orientation='h',
    title='Conditioning of human factors',
    labels={
        'index': 'category',
        'value': 'quantity',
    }
)

# %%
individual_factors = \
    human_factor_conditioning[human_factor_conditioning.fator_condicionante == 'INDIVIDUAL']
individual_factors.fator_nome.value_counts()

# %%
px.bar(
    individual_factors['fator_nome'].value_counts().iloc[::-1],
    orientation='h',
    title='Individual contributing human factors',
    labels={
        'index': 'category',
        'value': 'quantity',
    }
)

# %%
organisational_factors = \
    human_factor_conditioning[human_factor_conditioning.fator_condicionante == 'ORGANIZACIONAL']
organisational_factors.fator_nome.value_counts()

# %%
px.bar(
    organisational_factors['fator_nome'].value_counts().iloc[::-1],
    orientation='h',
    title='Organisational contributing human factors',
    labels={
        'index': 'category',
        'value': 'quantity',
    }
)
