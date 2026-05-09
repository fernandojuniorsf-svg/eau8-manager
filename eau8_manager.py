import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import io
import hashlib
import random
import urllib.parse
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from PIL import Image

FUSO_BR = ZoneInfo("America/Sao_Paulo")
NL = chr(10)
SITE = "EUA8"

for p in ["[PASSWORD]", "fotos_validacao", "fotos_motoristas"]:
    if not os.path.exists(p):
        os.makedirs(p)

PASTA_DADOS = "[PASSWORD]"
PASTA_FOTOS = "fotos_validacao"
PASTA_MOTORISTAS = "fotos_motoristas"

try:
    from ultralytics import YOLO
    yolo_ok = True
except Exception as erro_yolo:
    yolo_ok = False

ARQ_FUNCIONARIOS = os.path.join(PASTA_DADOS, "funcionarios.json")
ARQ_ESCALAS = os.path.join(PASTA_DADOS, "escalas.json")
ARQ_MOTORISTAS = os.path.join(PASTA_DADOS, "motoristas.json")
ARQ_FORECAST = os.path.join(PASTA_DADOS, "forecast.json")
ARQ_VALIDACOES = os.path.join(PASTA_DADOS, "validacoes.json")
ARQ_USUARIOS = os.path.join(PASTA_DADOS, "usuarios.json")
ARQ_ABSENTEISMO = os.path.join(PASTA_DADOS, "absenteismo.json")
ARQ_DESEMPENHO = os.path.join(PASTA_DADOS, "desempenho.json")

POSICOES = ["Pick to Buffer Esteira 1", "Pick to Buffer Esteira 2", "Receiver", "Spider de Fechamento / Stow Esteira 2", "Stow Esteira 2", "Stow Esteira 1", "Stow Esteira 1 (2)", "Unloader", "YardMarshall"]
TIPOS_VEICULO = ["Carreta (28 pallets)", "Truck (16 pallets)", "VUC (6 pallets)", "Van", "Outro"]
TIPOS_VALIDACAO = ["Veiculo Carregado", "Pallet Montado", "Area de Stow", "Area de Receive", "Depart", "Outro"]
SENHA_PADRAO = "[PASSWORD]"
CPT_HORA = 20
ALERTA_HORA = 19
