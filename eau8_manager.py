import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import io
import hashlib
import random
import urllib.parse
import tempfile
import psycopg2
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from PIL import Image

FUSO_BR = ZoneInfo("America/Sao_Paulo")
NL = chr(10)
SITE = "EUA8"

for p in ["fotos_validacao", "fotos_motoristas"]:
    if not os.path.exists(p):
        os.makedirs(p)

PASTA_FOTOS = "fotos_validacao"
PASTA_MOTORISTAS = "fotos_motoristas"

try:
    from ultralytics import YOLO
    yolo_ok = True
except Exception:
    yolo_ok = False

POSICOES = ["Pick to Buffer Esteira 1", "Pick to Buffer Esteira 2", "Receiver", "Spider de Fechamento / Stow Esteira 2", "Stow Esteira 2", "Stow Esteira 1", "Stow Esteira 1 (2)", "Unloader", "YardMarshall"]
TIPOS_VEICULO = ["Carreta (28 pallets)", "Truck (16 pallets)", "VUC (6 pallets)", "3/4", "Fiorino", "Van", "Toco", "Bi-truck", "Outro"]
TIPOS_VALIDACAO = ["Veiculo Carregado", "Pallet Montado", "Area de Stow", "Area de Receive", "Depart", "Outro"]


def get_conn():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        port=st.secrets["DB_PORT"],
        dbname=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASS"]
    )


def query(sql, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    if cur.description:
        cols = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return [dict(zip(cols, row)) for row in rows]
    conn.commit()
    cur.close()
    conn.close()
    return []


def execute(sql, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    conn.commit()
    cur.close()
    conn.close()


def init_db():
    sql = """
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        usuario TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        nome TEXT NOT NULL,
        perfil TEXT DEFAULT 'Operador',
        status TEXT DEFAULT 'Ativo',
        criado_em TEXT
    );
    CREATE TABLE IF NOT EXISTS funcionarios (
        id SERIAL PRIMARY KEY,
        nome TEXT NOT NULL,
        tipo TEXT DEFAULT 'Fixo',
        telefone TEXT,
        qualidades TEXT,
        status TEXT DEFAULT 'Ativo',
        observacoes TEXT,
        cadastrado_em TEXT
    );
    CREATE TABLE IF NOT EXISTS escalas (
        id SERIAL PRIMARY KEY,
        data TEXT,
        turno TEXT,
        volume INTEGER DEFAULT 0,
        escala TEXT,
        gerada_em TEXT,
        gerada_por TEXT
    );
    CREATE TABLE IF NOT EXISTS motoristas (
        id SERIAL PRIMARY KEY,
        nome TEXT NOT NULL,
        placa TEXT,
        telefone TEXT,
        tipo_veiculo TEXT,
        horario_chegada TEXT,
        horario_saida TEXT,
        observacoes TEXT,
        destino TEXT,
        transportadora TEXT,
        data_chegada TEXT,
        data_registro TEXT,
        importado BOOLEAN DEFAULT FALSE,
        foto TEXT
    );
    CREATE TABLE IF NOT EXISTS absenteismo (
        id SERIAL PRIMARY KEY,
        funcionario TEXT,
        data TEXT,
        motivo TEXT,
        observacoes TEXT,
        registrado_em TEXT
    );
    CREATE TABLE IF NOT EXISTS desempenho (
        id SERIAL PRIMARY KEY,
        funcionario TEXT,
        posicao TEXT,
        nota INTEGER,
        data_avaliacao TEXT,
        observacoes TEXT,
        registrado_em TEXT
    );
    CREATE TABLE IF NOT EXISTS forecast (
        id SERIAL PRIMARY KEY,
        data TEXT,
        volume INTEGER DEFAULT 0,
        observacoes TEXT,
        registrado_em TEXT
    );
    CREATE TABLE IF NOT EXISTS validacoes (
        id SERIAL PRIMARY KEY,
        tipo TEXT,
        data TEXT,
        total_objetos_ia INTEGER DEFAULT 0,
        contagem_ia TEXT,
        total_objetos_manual INTEGER DEFAULT 0,
        contagem_manual TEXT,
        foto TEXT
    );
    CREATE TABLE IF NOT EXISTS config (
        id SERIAL PRIMARY KEY,
        cpt_hora INTEGER DEFAULT 20,
        cpt_minuto INTEGER DEFAULT 0,
        alerta_hora INTEGER DEFAULT 19
    );
    CREATE TABLE IF NOT EXISTS timer_historico (
        id SERIAL PRIMARY KEY,
        data TEXT,
        hora_inicio TEXT,
        hora_conclusao TEXT,
        registrado_em TEXT,
        registrado_por TEXT
    );
    """
    execute(sql)


def cifrar_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


SENHA_ADMIN = cifrar_senha(str(4848881358) + "fer")
SENHA_EQUIPE = cifrar_senha("eua" + str(8))


def primeiro(lista):
    for item in lista:
        return item
    return None


def carregar_config():
    rows = query("SELECT cpt_hora, cpt_minuto, alerta_hora FROM config LIMIT 1")
    if rows:
        return rows[0]
    execute("INSERT INTO config (cpt_hora, cpt_minuto, alerta_hora) VALUES (20, 0, 19)")
    return {"cpt_hora": 20, "cpt_minuto": 0, "alerta_hora": 19}


def salvar_config(cfg):
    rows = query("SELECT id FROM config LIMIT 1")
    if rows:
        execute("UPDATE config SET cpt_hora=%s, cpt_minuto=%s, alerta_hora=%s WHERE id=%s", (cfg["cpt_hora"], cfg["cpt_minuto"], cfg["alerta_hora"], rows[0]["id"]))
    else:
        execute("INSERT INTO config (cpt_hora, cpt_minuto, alerta_hora) VALUES (%s,%s,%s)", (cfg["cpt_hora"], cfg["cpt_minuto"], cfg["alerta_hora"]))


def carregar_usuarios():
    rows = query("SELECT * FROM usuarios ORDER BY id")
    if not rows:
        execute("INSERT INTO usuarios (usuario, senha, nome, perfil, status, criado_em) VALUES (%s,%s,%s,%s,%s,%s)", ("fernando", SENHA_ADMIN, "Fernando Junior", "Admin", "Ativo", "2026-05-03"))
        execute("INSERT INTO usuarios (usuario, senha, nome, perfil, status, criado_em) VALUES (%s,%s,%s,%s,%s,%s)", ("equipe", SENHA_EQUIPE, "Equipe EUA8", "Equipe", "Ativo", "2026-05-11"))
        return query("SELECT * FROM usuarios ORDER BY id")
    return rows


def salvar_usuario(u):
    execute("INSERT INTO usuarios (usuario, senha, nome, perfil, status, criado_em) VALUES (%s,%s,%s,%s,%s,%s)", (u["usuario"], u["senha"], u["nome"], u["perfil"], u["status"], u["criado_em"]))


def atualizar_usuario(uid, dados):
    if dados.get("senha"):
        execute("UPDATE usuarios SET nome=%s, perfil=%s, status=%s, senha=%s WHERE id=%s", (dados["nome"], dados["perfil"], dados["status"], dados["senha"], uid))
    else:
        execute("UPDATE usuarios SET nome=%s, perfil=%s, status=%s WHERE id=%s", (dados["nome"], dados["perfil"], dados["status"], uid))


def carregar_funcionarios():
    rows = query("SELECT * FROM funcionarios ORDER BY id")
    for r in rows:
        if r.get("qualidades"):
            try:
                r["qualidades"] = json.loads(r["qualidades"])
            except Exception:
                r["qualidades"] = []
        else:
            r["qualidades"] = []
    return rows


def salvar_funcionario(f):
    execute("INSERT INTO funcionarios (nome, tipo, telefone, qualidades, status, observacoes, cadastrado_em) VALUES (%s,%s,%s,%s,%s,%s,%s)", (f["nome"], f["tipo"], f["telefone"], json.dumps(f.get("qualidades", []), ensure_ascii=False), f["status"], f.get("observacoes", ""), f["cadastrado_em"]))


def atualizar_funcionario(fid, f):
    execute("UPDATE funcionarios SET nome=%s, tipo=%s, telefone=%s, qualidades=%s, status=%s, observacoes=%s WHERE id=%s", (f["nome"], f["tipo"], f["telefone"], json.dumps(f.get("qualidades", []), ensure_ascii=False), f["status"], f.get("observacoes", ""), fid))


def excluir_funcionario(fid):
    execute("DELETE FROM funcionarios WHERE id=%s", (fid,))


def carregar_escalas():
    rows = query("SELECT * FROM escalas ORDER BY data DESC")
    for r in rows:
        if r.get("escala"):
            try:
                r["escala"] = json.loads(r["escala"])
            except Exception:
                r["escala"] = []
        else:
            r["escala"] = []
    return rows


def salvar_escala(e):
    execute("INSERT INTO escalas (data, turno, volume, escala, gerada_em, gerada_por) VALUES (%s,%s,%s,%s,%s,%s)", (e["data"], e["turno"], e["volume"], json.dumps(e.get("escala", []), ensure_ascii=False), e["gerada_em"], e["gerada_por"]))


def excluir_escala(eid):
    execute("DELETE FROM escalas WHERE id=%s", (eid,))


def carregar_motoristas():
    return query("SELECT * FROM motoristas ORDER BY id DESC")


def salvar_motorista(m):
    execute("INSERT INTO motoristas (nome, placa, telefone, tipo_veiculo, horario_chegada, horario_saida, observacoes, destino, transportadora, data_chegada, data_registro, importado, foto) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (m.get("nome",""), m.get("placa",""), m.get("telefone",""), m.get("tipo_veiculo",""), m.get("horario_chegada",""), m.get("horario_saida",""), m.get("observacoes",""), m.get("destino",""), m.get("transportadora",""), m.get("data_chegada",""), m.get("data_registro",""), m.get("importado", False), m.get("foto","")))


def atualizar_motorista(mid, m):
    execute("UPDATE motoristas SET nome=%s, placa=%s, tipo_veiculo=%s, horario_chegada=%s, horario_saida=%s, observacoes=%s WHERE id=%s", (m["nome"], m["placa"], m["tipo_veiculo"], m["horario_chegada"], m["horario_saida"], m.get("observacoes",""), mid))


def excluir_motorista(mid):
    execute("DELETE FROM motoristas WHERE id=%s", (mid,))


def limpar_motoristas_importados():
    execute("DELETE FROM motoristas WHERE importado=TRUE")


def carregar_absenteismo():
    return query("SELECT * FROM absenteismo ORDER BY data DESC")


def salvar_absenteismo_reg(a):
    execute("INSERT INTO absenteismo (funcionario, data, motivo, observacoes, registrado_em) VALUES (%s,%s,%s,%s,%s)", (a["funcionario"], a["data"], a["motivo"], a.get("observacoes",""), a["registrado_em"]))


def carregar_desempenho():
    return query("SELECT * FROM desempenho ORDER BY data_avaliacao DESC")


def salvar_desempenho_reg(d):
    execute("INSERT INTO desempenho (funcionario, posicao, nota, data_avaliacao, observacoes, registrado_em) VALUES (%s,%s,%s,%s,%s,%s)", (d["funcionario"], d["posicao"], d["nota"], d["data_avaliacao"], d.get("observacoes",""), d["registrado_em"]))


def carregar_forecast():
    return query("SELECT * FROM forecast ORDER BY data DESC")


def salvar_forecast_reg(f):
    execute("INSERT INTO forecast (data, volume, observacoes, registrado_em) VALUES (%s,%s,%s,%s)", (f["data"], f["volume"], f.get("observacoes",""), f["registrado_em"]))


def carregar_validacoes():
    rows = query("SELECT * FROM validacoes ORDER BY data DESC")
    for r in rows:
        if r.get("contagem_ia"):
            try:
                r["contagem_ia"] = json.loads(r["contagem_ia"])
            except Exception:
                r["contagem_ia"] = {}
        else:
            r["contagem_ia"] = {}
        if r.get("contagem_manual"):
            try:
                r["contagem_manual"] = json.loads(r["contagem_manual"])
            except Exception:
                r["contagem_manual"] = {}
        else:
            r["contagem_manual"] = {}
    return rows


def salvar_validacao(v):
    execute("INSERT INTO validacoes (tipo, data, total_objetos_ia, contagem_ia, total_objetos_manual, contagem_manual, foto) VALUES (%s,%s,%s,%s,%s,%s,%s)", (v["tipo"], v["data"], v["total_objetos_ia"], json.dumps(v.get("contagem_ia", {}), ensure_ascii=False), v["total_objetos_manual"], json.dumps(v.get("contagem_manual", {}), ensure_ascii=False), v.get("foto", "")))


def carregar_timer_historico():
    return query("SELECT * FROM timer_historico ORDER BY data DESC")


def salvar_timer_historico(t):
    execute("INSERT INTO timer_historico (data, hora_inicio, hora_conclusao, registrado_em, registrado_por) VALUES (%s,%s,%s,%s,%s)", (t["data"], t["hora_inicio"], t["hora_conclusao"], t["registrado_em"], t["registrado_por"]))


try:
    init_db()
except Exception as e:
    st.error("Erro ao conectar no banco: " + str(e))
    st.stop()

CONFIG = carregar_config()
CPT_HORA = CONFIG.get("cpt_hora", 20)
CPT_MINUTO = CONFIG.get("cpt_minuto", 0)
ALERTA_HORA = CONFIG.get("alerta_hora", 19)
PERFIS_ACESSO = {"Admin": ["Dashboard", "Cadastro de Funcionarios", "Gerador de Escala", "Registro de Motorista", "Absenteismo", "Desempenho por Funcao", "Forecast / Volume", "Validacao por Foto (IA)", "Scanner QR/Barcode", "Enviar por WhatsApp", "Relatorios", "Configuracoes", "Gerenciar Usuarios"], "Supervisor": ["Dashboard", "Cadastro de Funcionarios", "Gerador de Escala", "Registro de Motorista", "Absenteismo", "Desempenho por Funcao", "Forecast / Volume", "Validacao por Foto (IA)", "Scanner QR/Barcode", "Enviar por WhatsApp", "Relatorios"], "Operador": ["Dashboard", "Registro de Motorista", "Validacao por Foto (IA)", "Scanner QR/Barcode"], "Equipe": ["Registro de Motorista"], "Visualizador": ["Dashboard", "Relatorios"]}
st.set_page_config(page_title=SITE + " Manager", page_icon="F", layout="wide")

css_texto = "<style>"
css_texto += ".stApp {background-color: #1a1a1a !important;}"
css_texto += 'section[data-testid="stSidebar"] {background-color: #2d2d2d !important;}'
css_texto += 'section[data-testid="stSidebar"] * {color: #e0e0e0 !important;}'
css_texto += 'section[data-testid="stSidebar"] h2 {color: #FF9900 !important;}'
css_texto += "h1,h2,h3,h4 {color: #FF9900 !important;}"
css_texto += ".stMarkdown p {color: #e0e0e0 !important;}"
css_texto += ".stMarkdown li {color: #e0e0e0 !important;}"
css_texto += ".stMarkdown strong {color: #ffffff !important;}"
css_texto += ".stMetricValue {color: #FF9900 !important; font-weight: 700 !important;}"
css_texto += 'div[data-testid="stMetricDelta"] {color: #00C853 !important;}'
css_texto += 'div[data-testid="stMetricLabel"] p {color: #cccccc !important;}'
css_texto += 'div[data-testid="stMetric"] {background-color: #2d2d2d !important; border-left: 4px solid #FF9900; border-radius: 10px; padding: 16px; box-shadow: 0 3px 8px rgba(0,0,0,0.3);}'
css_texto += '.stTabs [data-baseweb="tab-list"] {background-color: #2d2d2d; border-radius: 10px 10px 0 0;}'
css_texto += '.stTabs [data-baseweb="tab"] {color: #cccccc !important; font-weight: 500;}'
css_texto += '.stTabs [aria-selected="true"] {background-color: #FF9900 !important; color: #000 !important; border-radius: 10px 10px 0 0; font-weight: 700;}'
css_texto += '.stButton>button {background-color: #FF9900 !important; color: #000 !important; border: none !important; border-radius: 10px !important; padding: 16px 48px !important; font-weight: 600 !important; box-shadow: 0 3px 8px rgba(255,153,0,0.4) !important;}'
css_texto += '.stButton>button:hover {background-color: #e68a00 !important;}'
css_texto += 'div[data-testid="stForm"] {background-color: #2d2d2d !important; border: 1px solid #444; border-radius: 12px; padding: 24px;}'
css_texto += 'input {background-color: #3a3a3a !important; color: #e0e0e0 !important; border: 1px solid #555 !important; border-radius: 8px !important;}'
css_texto += 'textarea {background-color: #3a3a3a !important; color: #e0e0e0 !important; border: 1px solid #555 !important; border-radius: 8px !important;}'
css_texto += '[data-baseweb="select"] {background-color: #3a3a3a !important;}'
css_texto += '[data-baseweb="select"] * {color: #e0e0e0 !important;}'
css_texto += "hr {border-color: #FF9900 !important; opacity: 0.4;}"
css_texto += '[data-testid="stHeader"] {background-color: #1a1a1a !important;}'
css_texto += ".stDownloadButton>button {background-color: #FF9900 !important; color: #000 !important; border: none !important; border-radius: 10px !important;}"
css_texto += ".success-box {background: rgba(0,200,83,0.1); border: 1px solid rgba(0,200,83,0.3); border-radius: 10px; padding: 12px 16px; color: #00C853; font-size: 14px; font-weight: 500; margin: 10px 0;}"
css_texto += ".progress-bar {background: #3a3a3a; border-radius: 8px; height: 14px; overflow: hidden; margin-top: 8px;}"
css_texto += ".progress-fill {background: linear-gradient(90deg, #FF9900, #FFB84D); height: 100%; border-radius: 8px;}"
css_texto += "</style>"
st.markdown(css_texto, unsafe_allow_html=True)

if "logado" not in st.session_state:
    st.session_state["logado"] = False
    st.session_state["usuario_logado"] = None
    st.session_state["perfil_logado"] = None
    st.session_state["nome_logado"] = None

if not st.session_state["logado"]:
    col_e, col_c, col_d = st.columns([1, 2, 1])
    with col_c:
        st.markdown("# " + SITE + " Manager")
        st.markdown("*First Mile Operations | Amazon Logistics*")
        st.markdown("---")
        st.markdown("### Login")
        with st.form("form_login"):
            usuario_input = st.text_input("Usuario")
            senha_input = st.text_input("Senha", type="password")
            btn_login = st.form_submit_button("Entrar", use_container_width=True)
            if btn_login:
                if usuario_input and senha_input:
                    usuarios = carregar_usuarios()
                    encontrou = False
                    for u in usuarios:
                        if u["usuario"] == usuario_input.lower().strip() and u["senha"] == cifrar_senha(senha_input):
                            if u.get("status", "Ativo") != "Ativo":
                                st.error("Usuario inativo.")
                                encontrou = True
                                break
                            st.session_state["logado"] = True
                            st.session_state["usuario_logado"] = u["usuario"]
                            st.session_state["nome_logado"] = u["nome"]
                            st.session_state["perfil_logado"] = u["perfil"]
                            encontrou = True
                            st.rerun()
                            break
                    if not encontrou:
                        st.error("Usuario ou senha incorretos!")
                else:
                    st.error("Preencha usuario e senha!")
    st.stop()

nome_logado = st.session_state.get("nome_logado", "Usuario")
perfil_logado = st.session_state.get("perfil_logado", "Operador")
st.sidebar.markdown("## " + SITE + " Manager")
st.sidebar.markdown("*First Mile Operations*")
st.sidebar.markdown("Bem-vindo, **" + nome_logado + "** (" + perfil_logado + ")")
st.sidebar.markdown("---")
menus_permitidos = PERFIS_ACESSO.get(perfil_logado, ["Dashboard"])
todos_menus = ["Dashboard", "Cadastro de Funcionarios", "Gerador de Escala", "Registro de Motorista", "Absenteismo", "Desempenho por Funcao", "Forecast / Volume", "Validacao por Foto (IA)", "Scanner QR/Barcode", "Enviar por WhatsApp", "Relatorios", "Configuracoes", "Gerenciar Usuarios"]
menus_visiveis = [m for m in todos_menus if m in menus_permitidos]
menu = st.sidebar.radio("Menu Principal", menus_visiveis)
st.sidebar.markdown("---")
agora = datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M")
st.sidebar.markdown("Data: **" + agora + "**")
st.sidebar.markdown("Site: **" + SITE + "**")
st.sidebar.markdown("Turno: **Noturno**")
st.sidebar.markdown("---")
if st.sidebar.button("Sair", use_container_width=True):
    for k in ["logado", "usuario_logado", "perfil_logado", "nome_logado"]:
        st.session_state[k] = None
    st.session_state["logado"] = False
    st.rerun()

st.markdown("# " + SITE + " Manager")
st.markdown("*First Mile Operations | Amazon Logistics*")
st.markdown("---")

if menu == "Dashboard":
    st.markdown("### Dashboard Operacional")
    funcionarios = carregar_funcionarios()
    validacoes = carregar_validacoes()
    escalas = carregar_escalas()
    motoristas = carregar_motoristas()
    forecasts = carregar_forecast()
    absenteismo = carregar_absenteismo()
    fixos = [f for f in funcionarios if f.get("tipo") == "Fixo" and f.get("status") == "Ativo"]
    freelancers = [f for f in funcionarios if f.get("tipo") == "Freelancer" and f.get("status") == "Ativo"]
    ativos = [f for f in funcionarios if f.get("status") == "Ativo"]
    hoje_str = datetime.now(FUSO_BR).strftime("%Y-%m-%d")
    val_hoje = [v for v in validacoes if v.get("data", "")[:10] == hoje_str]
    mot_hoje = [m for m in motoristas if m.get("data_chegada", "")[:10] == hoje_str or m.get("data_registro", "")[:10] == hoje_str]
    esc_hoje = [e for e in escalas if e.get("data", "") == hoje_str]
    fc_hoje = [f for f in forecasts if f.get("data", "") == hoje_str]
    volume_hoje = primeiro(fc_hoje).get("volume", 0) if fc_hoje else 0
    abs_hoje = [a for a in absenteismo if a.get("data", "") == hoje_str]
    agora_dt = datetime.now(FUSO_BR)
    timer_ativo = st.session_state.get("timer_ativo", False)
    st.markdown("### Timer CPT")
    cpt_target = agora_dt.replace(hour=CPT_HORA, minute=CPT_MINUTO, second=0, microsecond=0)
    if not timer_ativo:
        timer_texto = "Aguardando"
        timer_cor = "#666666"
        timer_sombra = "0 0 20px rgba(100,100,100,0.3)"
        timer_sub = "Clique em Iniciar Turno"
        pct_circulo = 0
    else:
        if agora_dt > cpt_target:
            diff = agora_dt - cpt_target
            minutos_passados = int(diff.total_seconds() / 60)
            timer_texto = "+" + str(minutos_passados) + "min"
            timer_sub = "CPT ESTOURADO"
            timer_cor = "#EF4444"
            timer_sombra = "0 0 60px rgba(239,68,68,0.6)"
            pct_circulo = 100
        else:
            diff = cpt_target - agora_dt
            seg_total = int(diff.total_seconds())
            minutos_falta = seg_total // 60
            horas_falta = minutos_falta // 60
            mins_falta = minutos_falta % 60
            if horas_falta > 0:
                timer_texto = str(horas_falta) + "h" + str(mins_falta).zfill(2)
            else:
                timer_texto = str(mins_falta) + "min"
            timer_sub = "para o CPT (" + str(CPT_HORA).zfill(2) + ":" + str(CPT_MINUTO).zfill(2) + ")"
            seg_total_turno = 6 * 3600
            seg_passados = seg_total_turno - seg_total
            pct_circulo = min(int((seg_passados / seg_total_turno) * 100), 100) if seg_total_turno > 0 else 0
            if minutos_falta <= 10:
                timer_cor = "#EF4444"
                timer_sombra = "0 0 60px rgba(239,68,68,0.6)"
            elif minutos_falta <= 60:
                timer_cor = "#FF9900"
                timer_sombra = "0 0 40px rgba(255,153,0,0.4)"
            else:
                timer_cor = "#00C853"
                timer_sombra = "0 0 30px rgba(0,200,83,0.3)"
    grau = int(pct_circulo * 3.6)
    if grau <= 180:
        grad_circulo = "linear-gradient(90deg, #3a3a3a 50%, transparent 50%), linear-gradient(" + str(90 + grau) + "deg, " + timer_cor + " 50%, #3a3a3a 50%)"
    else:
        grad_circulo = "linear-gradient(" + str(grau - 90) + "deg, " + timer_cor + " 50%, transparent 50%), linear-gradient(270deg, " + timer_cor + " 50%, #3a3a3a 50%)"
    timer_html = '<div style="display:flex; justify-content:center; margin:20px 0;">'
    timer_html += '<div style="width:280px; height:280px; border-radius:50%; background:' + grad_circulo + '; display:flex; align-items:center; justify-content:center; box-shadow:' + timer_sombra + ';">'
    timer_html += '<div style="width:240px; height:240px; border-radius:50%; background:#1a1a1a; display:flex; flex-direction:column; align-items:center; justify-content:center;">'
    timer_html += '<p style="font-size:56px; font-weight:900; color:' + timer_cor + '; margin:0; letter-spacing:-2px;">' + timer_texto + '</p>'
    timer_html += '<p style="font-size:13px; color:#999; margin:4px 0 0 0; text-transform:uppercase; letter-spacing:1px;">' + timer_sub + '</p>'
    timer_html += '<p style="font-size:11px; color:#666; margin:4px 0 0 0;">' + agora_dt.strftime("%H:%M:%S") + '</p>'
    timer_html += '</div></div></div>'
    st.markdown(timer_html, unsafe_allow_html=True)
    bt1, bt2, bt3 = st.columns(3)
    with bt1:
        if not timer_ativo:
            if st.button("Iniciar Turno", type="primary", use_container_width=True):
                st.session_state["timer_ativo"] = True
                st.session_state["timer_inicio"] = agora_dt.strftime("%H:%M")
                st.rerun()
        else:
            st.markdown('<div class="success-box">Turno iniciado as ' + st.session_state.get("timer_inicio", "") + '</div>', unsafe_allow_html=True)
    with bt2:
        if timer_ativo:
            if st.button("Concluir Turno", use_container_width=True):
                st.session_state["mostrar_conclusao"] = True
    with bt3:
        if st.button("Atualizar", use_container_width=True):
            st.rerun()
    if st.session_state.get("mostrar_conclusao", False):
        st.markdown("---")
        st.markdown("#### Registrar Conclusao")
        with st.form("form_conclusao"):
            hora_conclusao = st.text_input("Horario de conclusao (HH:MM)", value=agora_dt.strftime("%H:%M"))
            btn_conc = st.form_submit_button("Confirmar Conclusao", use_container_width=True)
            if btn_conc:
                t = {"data": hoje_str, "hora_inicio": st.session_state.get("timer_inicio", ""), "hora_conclusao": hora_conclusao, "registrado_em": agora_dt.strftime("%d/%m/%Y %H:%M"), "registrado_por": nome_logado}
                salvar_timer_historico(t)
                st.session_state["timer_ativo"] = False
                st.session_state["timer_inicio"] = ""
                st.session_state["mostrar_conclusao"] = False
                st.markdown('<div class="success-box">Turno concluido as ' + hora_conclusao + ' e registrado no historico!</div>', unsafe_allow_html=True)
                st.rerun()
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Funcionarios Ativos", len(ativos), str(len(fixos)) + " fixos / " + str(len(freelancers)) + " free")
    with c2:
        st.metric("Validacoes Hoje", len(val_hoje), str(len(validacoes)) + " total")
    with c3:
        st.metric("Escalas Geradas", len(esc_hoje), str(len(escalas)) + " total")
    with c4:
        st.metric("Motoristas Hoje", len(mot_hoje), str(len(motoristas)) + " total")
    st.markdown("---")
    c5, c6, c7 = st.columns(3)
    with c5:
        st.metric("Volume Previsto", str(volume_hoje) + " pacotes")
    with c6:
        obj_ia_h = sum(v.get("total_objetos_ia", 0) for v in val_hoje)
        obj_eq_h = sum(v.get("total_objetos_manual", 0) for v in val_hoje)
        st.metric("Objetos Validados", "IA: " + str(obj_ia_h) + " | Eq: " + str(obj_eq_h))
    with c7:
        st.metric("Faltas Hoje", len(abs_hoje))
    st.markdown("---")
    st.markdown("### Progresso Motoristas")
    total_mot = len(mot_hoje)
    mot_com_saida = len([m for m in mot_hoje if m.get("horario_saida", "")])
    pct_mot = int((mot_com_saida / total_mot) * 100) if total_mot > 0 else 0
    cm1, cm2 = st.columns(2)
    with cm1:
        st.markdown('<div style="background:#2d2d2d; border-radius:12px; padding:20px; text-align:center; border:1px solid #444;"><p style="font-size:42px; font-weight:900; color:#FF9900; margin:0;">' + str(pct_mot) + '%</p><p style="color:#999; font-size:12px; margin:4px 0 0 0;">MOTORISTAS DESPACHADOS</p><div class="progress-bar"><div class="progress-fill" style="width:' + str(pct_mot) + '%;"></div></div></div>', unsafe_allow_html=True)
    with cm2:
        st.markdown('<div style="background:#2d2d2d; border-radius:12px; padding:20px; text-align:center; border:1px solid #444;"><p style="color:#999; font-size:12px; margin:0 0 8px 0;">DETALHAMENTO</p><p style="color:#00C853; font-size:14px; margin:4px 0;"><strong>' + str(mot_com_saida) + '</strong> despachados</p><p style="color:#FF9900; font-size:14px; margin:4px 0;"><strong>' + str(total_mot - mot_com_saida) + '</strong> aguardando</p><p style="color:#8B5CF6; font-size:14px; margin:4px 0;"><strong>' + str(total_mot) + '</strong> total do dia</p></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Historico Timer CPT")
    hist_timer = carregar_timer_historico()
    if hist_timer:
        df_ht = pd.DataFrame(hist_timer)
        cols_ht = ["data", "hora_inicio", "hora_conclusao", "registrado_por"]
        cols_ok = [c for c in cols_ht if c in df_ht.columns]
        st.dataframe(df_ht[cols_ok].head(10), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum registro de timer.")
    st.markdown("---")
    st.markdown("### Ultimas Atividades")
    ca1, ca2 = st.columns(2)
    with ca1:
        st.markdown("#### Ultimas Validacoes")
        if validacoes:
            for v in validacoes[:5]:
                tia = v.get("total_objetos_ia", 0)
                teq = v.get("total_objetos_manual", 0)
                st.markdown("- **" + v.get("tipo", "") + "** " + v.get("data", "")[:16] + " | IA:" + str(tia) + " Eq:" + str(teq))
        else:
            st.info("Nenhuma validacao.")
    with ca2:
        st.markdown("#### Ultimos Motoristas")
        if motoristas:
            for m in motoristas[:5]:
                st.markdown("- **" + m.get("nome", "") + "** " + m.get("placa", "") + " | " + m.get("tipo_veiculo", ""))
        else:
            st.info("Nenhum motorista.")

elif menu == "Cadastro de Funcionarios":
    st.markdown("### Cadastro de Funcionarios")
    funcionarios = carregar_funcionarios()
    tab1, tab2 = st.tabs(["Novo Funcionario", "Lista / Editar"])
    with tab1:
        with st.form("form_func"):
            cf1, cf2 = st.columns(2)
            with cf1:
                nome = st.text_input("Nome Completo")
                tipo = st.selectbox("Tipo", ["Fixo", "Freelancer"])
                telefone = st.text_input("Telefone (com DDD)", placeholder="11999999999")
            with cf2:
                qualidades = st.multiselect("Qualidades / Posicoes", POSICOES)
                status_func = st.selectbox("Status", ["Ativo", "Inativo", "Afastado", "Ferias"])
                obs_func = st.text_input("Observacoes")
            btn_func = st.form_submit_button("Cadastrar", use_container_width=True)
            if btn_func:
                if nome:
                    nv = {"nome": nome, "tipo": tipo, "telefone": telefone, "qualidades": qualidades, "status": status_func, "observacoes": obs_func, "cadastrado_em": datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M")}
                    salvar_funcionario(nv)
                    st.markdown('<div class="success-box">' + nome + ' cadastrado com sucesso!</div>', unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.error("Preencha o nome!")
    with tab2:
        if funcionarios:
            df_func = pd.DataFrame(funcionarios)
            cols = ["nome", "tipo", "telefone", "qualidades", "status", "observacoes"]
            cols_ok = [c for c in cols if c in df_func.columns]
            st.dataframe(df_func[cols_ok], use_container_width=True, hide_index=True)
            st.markdown("---")
            st.markdown("#### Editar Funcionario")
            nomes_f = [f["nome"] for f in funcionarios]
            sel_f = st.selectbox("Selecione", nomes_f, key="sel_f_edit")
            idx_f = nomes_f.index(sel_f)
            fe = funcionarios[idx_f]
            sl = ["Ativo", "Inativo", "Afastado", "Ferias"]
            si = sl.index(fe.get("status", "Ativo")) if fe.get("status", "Ativo") in sl else 0
            with st.form("form_edit_func"):
                ef1, ef2 = st.columns(2)
                with ef1:
                    en = st.text_input("Nome", value=fe.get("nome", ""))
                    et = st.selectbox("Tipo", ["Fixo", "Freelancer"], index=["Fixo", "Freelancer"].index(fe.get("tipo", "Fixo")))
                    etel = st.text_input("Telefone", value=fe.get("telefone", ""))
                with ef2:
                    eq = st.multiselect("Qualidades", POSICOES, default=fe.get("qualidades", []))
                    es = st.selectbox("Status", sl, index=si)
                    eo = st.text_input("Obs", value=fe.get("observacoes", ""))
                csf, cef = st.columns(2)
                with csf:
                    bsf = st.form_submit_button("Salvar Alteracoes", use_container_width=True)
                with cef:
                    bef = st.form_submit_button("Excluir Funcionario", use_container_width=True)
                if bsf:
                    dados_f = {"nome": en, "tipo": et, "telefone": etel, "qualidades": eq, "status": es, "observacoes": eo}
                    atualizar_funcionario(fe["id"], dados_f)
                    st.markdown('<div class="success-box">Atualizado!</div>', unsafe_allow_html=True)
                    st.rerun()
                if bef:
                    excluir_funcionario(fe["id"])
                    st.markdown('<div class="success-box">Excluido!</div>', unsafe_allow_html=True)
                    st.rerun()
        else:
            st.info("Nenhum funcionario cadastrado.")


elif menu == "Gerador de Escala":
    st.markdown("### Gerador de Escala")
    funcionarios = carregar_funcionarios()
    absenteismo = carregar_absenteismo()
    ativos = [f for f in funcionarios if f.get("status") == "Ativo"]
    tab1, tab2 = st.tabs(["Gerar Escala", "Anteriores / Editar"])
    with tab1:
        ge1, ge2, ge3 = st.columns(3)
        with ge1:
            data_escala = st.date_input("Data", value=date.today() + timedelta(days=1), key="dt_esc")
        with ge2:
            turno_escala = st.selectbox("Turno", ["Noturno"])
        with ge3:
            volume_prev = st.number_input("Volume Previsto", min_value=0, max_value=50000, value=0, step=100)
        data_esc_str = data_escala.strftime("%Y-%m-%d")
        faltas_dia = [a.get("funcionario", "") for a in absenteismo if a.get("data", "") == data_esc_str]
        disponiveis = [f for f in ativos if f["nome"] not in faltas_dia]
        if faltas_dia:
            st.warning("Com falta registrada: **" + ", ".join(faltas_dia) + "**")
        st.markdown("Disponiveis: **" + str(len(disponiveis)) + "** de " + str(len(ativos)))
        if volume_prev > 0:
            tph = 70
            horas_turno = 5.75
            capacidade = tph * horas_turno
            pessoas_necessarias = -(-volume_prev // int(capacidade))
            st.info("TPH: " + str(tph) + " | Turno: " + str(horas_turno) + "h | Necessarios: **" + str(pessoas_necessarias) + " pessoas**")
            if len(disponiveis) < pessoas_necessarias:
                st.warning("ALERTA: Faltam " + str(pessoas_necessarias - len(disponiveis)) + " pessoas!")
            else:
                st.success("HC suficiente!")
        if st.button("Sortear / Gerar Escala", type="primary", use_container_width=True):
            escala = []
            usados = []
            for pos in POSICOES:
                cands = [f for f in disponiveis if f["nome"] not in usados]
                if not cands:
                    continue
                random.shuffle(cands)
                escolhido = cands[0]
                ei = {"posicao": pos, "funcionario": escolhido["nome"], "telefone": escolhido.get("telefone", ""), "tipo": escolhido.get("tipo", "")}
                escala.append(ei)
                usados.append(escolhido["nome"])
            st.session_state["escala_temp"] = escala
        if "escala_temp" in st.session_state and st.session_state["escala_temp"]:
            esc = st.session_state["escala_temp"]
            st.markdown("---")
            st.markdown("#### Escala Gerada")
            ndisp = [f["nome"] for f in disponiveis]
            df_esc = pd.DataFrame(esc)
            df_ed = st.data_editor(df_esc, use_container_width=True, hide_index=True, num_rows="dynamic", column_config={"posicao": st.column_config.SelectboxColumn("Posicao", options=POSICOES), "funcionario": st.column_config.SelectboxColumn("Funcionario", options=ndisp)}, key="ed_esc")
            cs1, cs2 = st.columns(2)
            with cs1:
                if st.button("Salvar Escala", type="primary", use_container_width=True):
                    ne = {"data": data_esc_str, "turno": turno_escala, "volume": volume_prev, "escala": df_ed.to_dict("records"), "gerada_em": datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M"), "gerada_por": st.session_state.get("nome_logado", "Admin")}
                    salvar_escala(ne)
                    tw = "*ESCALA " + SITE + " - " + data_escala.strftime("%d/%m/%Y") + "*" + NL
                    tw += "Turno: " + turno_escala + NL + NL
                    for it in df_ed.to_dict("records"):
                        tw += it.get("posicao", "") + ": " + it.get("funcionario", "") + NL
                    tw += NL + "Bora, time!"
                    st.session_state["ultima_escala_wpp"] = tw
                    st.session_state["escala_temp"] = None
                    st.markdown('<div class="success-box">Escala salva!</div>', unsafe_allow_html=True)
                    st.rerun()
            with cs2:
                if st.button("Sortear Novamente", use_container_width=True):
                    st.session_state["escala_temp"] = None
                    st.rerun()
    with tab2:
        escalas = carregar_escalas()
        if escalas:
            ops = [e.get("data","") + " - " + e.get("turno","") + " - Vol:" + str(e.get("volume", "")) for e in escalas]
            sel_e = st.selectbox("Selecione", ops, key="sel_esc_h")
            idx_e = ops.index(sel_e)
            esel = escalas[idx_e]
            st.markdown("**Data:** " + esel.get("data","") + " | **Turno:** " + esel.get("turno","") + " | **Volume:** " + str(esel.get("volume", "")))
            df_e_h = pd.DataFrame(esel.get("escala", []))
            st.dataframe(df_e_h, use_container_width=True, hide_index=True)
            if st.button("Excluir Escala", type="secondary"):
                excluir_escala(esel["id"])
                st.markdown('<div class="success-box">Excluida!</div>', unsafe_allow_html=True)
                st.rerun()
        else:
            st.info("Nenhuma escala gerada.")


elif menu == "Registro de Motorista":
    st.markdown("### Registro de Motorista")
    motoristas = carregar_motoristas()
    tab1, tab2, tab3 = st.tabs(["Novo Registro", "Historico / Editar", "Importar Motoristas"])
    with tab1:
        opcao_mot = st.radio("Como informar?", ["Selecionar da lista importada", "Digitar manualmente"], horizontal=True, key="opcao_mot_radio")
        nome_mot = ""
        placa_mot = ""
        tel_mot = ""
        tipo_veic = "Carreta (28 pallets)"
        if opcao_mot == "Selecionar da lista importada":
            mots_importados = [m for m in motoristas if m.get("importado", False)]
            if mots_importados:
                nomes_imp = ["Selecione..."] + [m["nome"] + " | " + str(m.get("placa", "")) for m in mots_importados]
                sel_imp = st.selectbox("Motorista importado:", nomes_imp, key="sel_mot_imp")
                if sel_imp != "Selecione...":
                    idx_imp = nomes_imp.index(sel_imp) - 1
                    mi = mots_importados[idx_imp]
                    nome_mot = mi["nome"]
                    placa_mot = mi.get("placa", "")
                    tel_mot = mi.get("telefone", "")
                    tipo_veic = mi.get("tipo_veiculo", "Carreta (28 pallets)")
                    st.markdown('<div class="success-box">Motorista selecionado: <strong>' + nome_mot + '</strong></div>', unsafe_allow_html=True)
            else:
                st.info("Nenhum motorista importado. Use a aba Importar ou digite manualmente.")
        with st.form("form_mot"):
            rm1, rm2 = st.columns(2)
            with rm1:
                nome_mot_input = st.text_input("Nome do Motorista", value=nome_mot)
                placa_mot_input = st.text_input("Placa (opcional)", value=placa_mot, placeholder="ABC1D23")
                tel_mot_input = st.text_input("Telefone (opcional)", value=tel_mot)
                tipo_veic_input = st.selectbox("Tipo de Veiculo", TIPOS_VEICULO, index=TIPOS_VEICULO.index(tipo_veic) if tipo_veic in TIPOS_VEICULO else 0)
            with rm2:
                h_chegada = st.text_input("Horario Chegada (opcional)", placeholder="14:30")
                h_saida = st.text_input("Horario Saida (opcional)", placeholder="16:00")
                obs_mot = st.text_input("Observacoes (opcional)")
                destino_mot = st.selectbox("Destino", ["ELP8", "ESA8", "DSP4", "Outro"])
            foto_mot = st.camera_input("Foto do Veiculo (opcional)")
            btn_mot = st.form_submit_button("Registrar", use_container_width=True)
            if btn_mot:
                nm = {"nome": nome_mot_input or "N/I", "placa": placa_mot_input.upper() if placa_mot_input else "", "telefone": tel_mot_input, "tipo_veiculo": tipo_veic_input, "horario_chegada": h_chegada, "horario_saida": h_saida, "observacoes": obs_mot, "destino": destino_mot, "transportadora": "", "data_chegada": datetime.now(FUSO_BR).strftime("%Y-%m-%d"), "data_registro": datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M"), "importado": False, "foto": ""}
                if foto_mot:
                    nf = "mot_" + datetime.now(FUSO_BR).strftime("%Y%m%d_%H%M%S") + ".jpg"
                    cf = os.path.join(PASTA_MOTORISTAS, nf)
                    img_m = Image.open(foto_mot)
                    img_m.save(cf)
                    nm["foto"] = nf
                salvar_motorista(nm)
                st.markdown('<div class="success-box">' + (nome_mot_input or "Motorista") + ' registrado com sucesso!</div>', unsafe_allow_html=True)
                st.rerun()
    with tab2:
        mots_registrados = [m for m in motoristas if not m.get("importado", False)]
        if mots_registrados:
            df_mot = pd.DataFrame(mots_registrados)
            cols_m = ["nome", "placa", "tipo_veiculo", "horario_chegada", "horario_saida", "destino", "data_chegada", "data_registro", "observacoes"]
            cols_ok = [c for c in cols_m if c in df_mot.columns]
            st.dataframe(df_mot[cols_ok], use_container_width=True, hide_index=True)
            st.markdown("---")
            st.markdown("#### Editar Motorista")
            ops_m = [m.get("nome", "") + " - " + m.get("placa", "") + " - " + str(m.get("data_chegada", ""))[:10] for m in mots_registrados]
            sel_m = st.selectbox("Selecione", ops_m, key="sel_m_edit")
            idx_m = ops_m.index(sel_m)
            me = mots_registrados[idx_m]
            with st.form("form_edit_mot"):
                em1, em2 = st.columns(2)
                with em1:
                    enm = st.text_input("Nome", value=me.get("nome", ""))
                    epm = st.text_input("Placa", value=me.get("placa", ""))
                    etv = st.selectbox("Tipo Veiculo", TIPOS_VEICULO, index=TIPOS_VEICULO.index(me.get("tipo_veiculo", "Outro")) if me.get("tipo_veiculo", "Outro") in TIPOS_VEICULO else len(TIPOS_VEICULO)-1)
                with em2:
                    ehc = st.text_input("Hora Chegada", value=me.get("horario_chegada", ""))
                    ehs = st.text_input("Hora Saida", value=me.get("horario_saida", ""))
                    eom = st.text_input("Obs", value=me.get("observacoes", ""))
                csm, cem = st.columns(2)
                with csm:
                    bsm = st.form_submit_button("Salvar", use_container_width=True)
                with cem:
                    bem = st.form_submit_button("Excluir", use_container_width=True)
                if bsm:
                    dados_m = {"nome": enm, "placa": epm.upper(), "tipo_veiculo": etv, "horario_chegada": ehc, "horario_saida": ehs, "observacoes": eom}
                    atualizar_motorista(me["id"], dados_m)
                    st.markdown('<div class="success-box">Atualizado!</div>', unsafe_allow_html=True)
                    st.rerun()
                if bem:
                    excluir_motorista(me["id"])
                    st.markdown('<div class="success-box">Excluido!</div>', unsafe_allow_html=True)
                    st.rerun()
        else:
            st.info("Nenhum motorista registrado.")
    with tab3:
        st.markdown("#### Importar Motoristas em Massa")
        st.markdown("Envie um Excel ou CSV. **Colunas:** nome, placa, telefone, tipo_veiculo, transportadora")
        st.markdown("Apenas **nome** e obrigatorio.")
        st.markdown("---")
        arq_mot = st.file_uploader("Envie o arquivo", type=["csv", "xlsx"], key="upload_mot")
        if arq_mot:
            try:
                if arq_mot.name.endswith(".csv"):
                    df_imp_up = pd.read_csv(arq_mot)
                else:
                    df_imp_up = pd.read_excel(arq_mot)
                st.session_state["df_mot_upload"] = df_imp_up
            except Exception as ex:
                st.error("Erro ao ler arquivo: " + str(ex))
        if "df_mot_upload" in st.session_state and st.session_state["df_mot_upload"] is not None:
            df_imp_up = st.session_state["df_mot_upload"]
            st.dataframe(df_imp_up, use_container_width=True, hide_index=True)
            st.markdown("Total: **" + str(len(df_imp_up)) + "** motoristas")
            if st.button("Importar Todos", type="primary", use_container_width=True):
                qtd_imp = 0
                for idx_row, row in df_imp_up.iterrows():
                    nome_r = str(row.get("nome", "")).strip()
                    if nome_r and nome_r != "nan":
                        ni = {"nome": nome_r, "placa": str(row.get("placa", "")).strip().upper() if str(row.get("placa", "")) != "nan" else "", "telefone": str(row.get("telefone", "")).strip() if str(row.get("telefone", "")) != "nan" else "", "tipo_veiculo": str(row.get("tipo_veiculo", "Carreta (28 pallets)")).strip() if str(row.get("tipo_veiculo", "")) != "nan" else "Carreta (28 pallets)", "transportadora": str(row.get("transportadora", "")).strip() if str(row.get("transportadora", "")) != "nan" else "", "horario_chegada": "", "horario_saida": "", "observacoes": "", "destino": "", "data_chegada": datetime.now(FUSO_BR).strftime("%Y-%m-%d"), "data_registro": datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M"), "importado": True, "foto": ""}
                        salvar_motorista(ni)
                        qtd_imp += 1
                st.session_state["df_mot_upload"] = None
                st.markdown('<div class="success-box">' + str(qtd_imp) + ' motoristas importados!</div>', unsafe_allow_html=True)
                st.rerun()
        st.markdown("---")
        st.markdown("#### Adicionar Manualmente")
        with st.form("form_imp_mot"):
            im1, im2 = st.columns(2)
            with im1:
                nome_imp = st.text_input("Nome do Motorista")
                placa_imp = st.text_input("Placa (opcional)")
            with im2:
                tel_imp = st.text_input("Telefone (opcional)")
                tipo_imp = st.selectbox("Tipo Veiculo", TIPOS_VEICULO)
                transp_imp = st.text_input("Transportadora (opcional)")
            btn_imp = st.form_submit_button("Importar", use_container_width=True)
            if btn_imp:
                if nome_imp:
                    ni = {"nome": nome_imp, "placa": placa_imp.upper() if placa_imp else "", "telefone": tel_imp, "tipo_veiculo": tipo_imp, "transportadora": transp_imp, "horario_chegada": "", "horario_saida": "", "observacoes": "", "destino": "", "data_chegada": datetime.now(FUSO_BR).strftime("%Y-%m-%d"), "data_registro": datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M"), "importado": True, "foto": ""}
                    salvar_motorista(ni)
                    st.markdown('<div class="success-box">' + nome_imp + ' importado!</div>', unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.error("Informe o nome!")
        st.markdown("---")
        st.markdown("#### Motoristas Importados")
        mots_imp = [m for m in motoristas if m.get("importado", False)]
        if mots_imp:
            df_imp = pd.DataFrame(mots_imp)
            cols_imp = ["nome", "placa", "tipo_veiculo", "telefone", "transportadora"]
            cols_ok = [c for c in cols_imp if c in df_imp.columns]
            st.dataframe(df_imp[cols_ok], use_container_width=True, hide_index=True)
            st.markdown("Total: **" + str(len(mots_imp)) + "** importados")
            if st.button("Limpar Todos Importados", type="secondary"):
                limpar_motoristas_importados()
                st.markdown('<div class="success-box">Lista limpa!</div>', unsafe_allow_html=True)
                st.rerun()
        else:
            st.info("Nenhum motorista importado.")

elif menu == "Absenteismo":
    st.markdown("### Registro de Absenteismo")
    funcionarios = carregar_funcionarios()
    absenteismo = carregar_absenteismo()
    ativos = [f for f in funcionarios if f.get("status") == "Ativo"]
    tab1, tab2 = st.tabs(["Registrar Falta", "Historico"])
    with tab1:
        with st.form("form_abs"):
            fa1, fa2 = st.columns(2)
            with fa1:
                nomes_at = [f["nome"] for f in ativos]
                func_abs = st.selectbox("Funcionario", nomes_at if nomes_at else ["Nenhum"])
                data_abs = st.date_input("Data da Falta", value=date.today(), key="dt_abs")
            with fa2:
                motivo_abs = st.selectbox("Motivo", ["Falta sem Justificativa", "Falta Justificada", "Atestado Medico", "Atraso", "Saiu mais cedo", "Outro"])
                obs_abs = st.text_input("Observacoes")
            btn_abs = st.form_submit_button("Registrar Falta", use_container_width=True)
            if btn_abs:
                if func_abs and func_abs != "Nenhum":
                    nabs = {"funcionario": func_abs, "data": data_abs.strftime("%Y-%m-%d"), "motivo": motivo_abs, "observacoes": obs_abs, "registrado_em": datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M")}
                    salvar_absenteismo_reg(nabs)
                    st.markdown('<div class="success-box">Falta registrada!</div>', unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.error("Selecione um funcionario!")
    with tab2:
        if absenteismo:
            df_abs = pd.DataFrame(absenteismo)
            st.dataframe(df_abs, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma falta registrada.")


elif menu == "Desempenho por Funcao":
    st.markdown("### Desempenho por Funcao")
    funcionarios = carregar_funcionarios()
    desempenho = carregar_desempenho()
    ativos = [f for f in funcionarios if f.get("status") == "Ativo"]
    tab1, tab2 = st.tabs(["Nova Avaliacao", "Historico"])
    with tab1:
        with st.form("form_desemp"):
            fd1, fd2 = st.columns(2)
            with fd1:
                nomes_d = [f["nome"] for f in ativos]
                func_desemp = st.selectbox("Funcionario", nomes_d if nomes_d else ["Nenhum"])
                pos_desemp = st.selectbox("Posicao Avaliada", POSICOES)
                data_desemp = st.date_input("Data Avaliacao", value=date.today(), key="dt_desemp")
            with fd2:
                nota_desemp = st.slider("Nota (1 a 10)", min_value=1, max_value=10, value=5)
                obs_desemp = st.text_area("Observacoes / Feedback")
            btn_desemp = st.form_submit_button("Registrar Avaliacao", use_container_width=True)
            if btn_desemp:
                if func_desemp and func_desemp != "Nenhum":
                    nd = {"funcionario": func_desemp, "posicao": pos_desemp, "nota": nota_desemp, "data_avaliacao": data_desemp.strftime("%Y-%m-%d"), "observacoes": obs_desemp, "registrado_em": datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M")}
                    salvar_desempenho_reg(nd)
                    st.markdown('<div class="success-box">Avaliacao registrada!</div>', unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.error("Selecione um funcionario!")
    with tab2:
        if desempenho:
            df_desemp = pd.DataFrame(desempenho)
            st.dataframe(df_desemp, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma avaliacao registrada.")


elif menu == "Forecast / Volume":
    st.markdown("### Forecast / Volume")
    forecasts = carregar_forecast()
    tab1, tab2 = st.tabs(["Registrar", "Historico"])
    with tab1:
        with st.form("form_fc"):
            ff1, ff2 = st.columns(2)
            with ff1:
                data_fc = st.date_input("Data", value=date.today(), key="dt_fc")
                volume_fc = st.number_input("Volume Previsto (pacotes)", min_value=0, max_value=100000, value=0, step=100)
            with ff2:
                obs_fc = st.text_input("Observacoes")
            btn_fc = st.form_submit_button("Salvar Forecast", use_container_width=True)
            if btn_fc:
                if volume_fc > 0:
                    nfc = {"data": data_fc.strftime("%d/%m/%Y"), "volume": volume_fc, "observacoes": obs_fc, "registrado_em": datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M")}
                    salvar_forecast_reg(nfc)
                    st.markdown('<div class="success-box">Forecast salvo! Data: ' + data_fc.strftime("%d/%m/%Y") + ' | Volume: ' + str(volume_fc) + '</div>', unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.error("Informe um volume maior que zero!")
        st.markdown("---")
        st.markdown("#### Upload de Forecast (CSV/Excel)")
        st.markdown("**Colunas obrigatorias:** data (dd/mm/aaaa), volume")
        arq_up = st.file_uploader("Envie o arquivo", type=["csv", "xlsx"], key="up_fc")
        if arq_up:
            try:
                if arq_up.name.endswith(".csv"):
                    df_up = pd.read_csv(arq_up)
                else:
                    df_up = pd.read_excel(arq_up)
                st.dataframe(df_up, use_container_width=True, hide_index=True)
                st.markdown("Total: **" + str(len(df_up)) + "** registros")
                if st.button("Importar Forecast", type="primary", use_container_width=True):
                    qtd_ok = 0
                    for idx_row, row in df_up.iterrows():
                        data_raw = str(row.get("data", "")).strip()
                        vol_raw = row.get("volume", 0)
                        try:
                            vol_int = int(float(vol_raw))
                        except Exception:
                            vol_int = 0
                        if vol_int > 0 and data_raw and data_raw != "nan":
                            nfc = {"data": data_raw, "volume": vol_int, "observacoes": "Upload", "registrado_em": datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M")}
                            salvar_forecast_reg(nfc)
                            qtd_ok += 1
                    st.markdown('<div class="success-box">' + str(qtd_ok) + ' registros importados!</div>', unsafe_allow_html=True)
                    st.rerun()
            except Exception as ex:
                st.error("Erro: " + str(ex))
    with tab2:
        if forecasts:
            df_fc = pd.DataFrame(forecasts)
            cols_fc = ["data", "volume", "observacoes", "registrado_em"]
            cols_ok = [c for c in cols_fc if c in df_fc.columns]
            st.dataframe(df_fc[cols_ok], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum forecast registrado.")


elif menu == "Validacao por Foto (IA)":
    st.markdown("### Validacao por Foto (IA)")
    validacoes = carregar_validacoes()
    tab1, tab2 = st.tabs(["Nova Validacao", "Historico"])
    with tab1:
        tipo_val = st.selectbox("Tipo de Validacao", TIPOS_VALIDACAO)
        foto_val = st.camera_input("Tire a foto para validacao")
        if foto_val:
            image = Image.open(foto_val)
            st.image(image, caption="Foto capturada", use_container_width=True)
            contagem_ia = {}
            total_ia = 0
            try:
                temp_path = os.path.join(tempfile.gettempdir(), "foto_val.jpg")
                image.save(temp_path)
                if yolo_ok:
                    from ultralytics import YOLO
                    modelo = YOLO("yolov8n.pt")
                    resultados = modelo(temp_path, conf=0.15)
                    for r in resultados:
                        for box in r.boxes:
                            cls_id = int(box.cls.item())
                            nome_obj = modelo.names.get(cls_id, "desconhecido")
                            contagem_ia[nome_obj] = contagem_ia.get(nome_obj, 0) + 1
                    total_ia = sum(contagem_ia.values())
                    st.markdown('<div class="success-box">IA detectou: ' + str(total_ia) + ' objetos</div>', unsafe_allow_html=True)
                else:
                    st.warning("YOLO nao instalado. Contagem apenas manual.")
            except Exception as e:
                st.error("Erro IA: " + str(e))
            st.markdown("---")
            st.markdown("#### Contagem Manual da Equipe")
            contagem_manual = {}
            objetos_manual = st.text_input("Objetos (ex: caixa, pallet)", placeholder="caixa, pallet")
            if objetos_manual:
                lista_obj = [x.strip() for x in objetos_manual.split(",") if x.strip()]
                for obj in lista_obj:
                    qtd = st.number_input("Qtd de " + obj, min_value=0, max_value=9999, value=0, step=1, key="man_" + obj)
                    contagem_manual[obj] = qtd
            total_manual = sum(contagem_manual.values())
            if st.button("Salvar Validacao", type="primary", use_container_width=True):
                nv = {"tipo": tipo_val, "data": datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M"), "total_objetos_ia": total_ia, "contagem_ia": contagem_ia, "total_objetos_manual": total_manual, "contagem_manual": contagem_manual, "foto": ""}
                nf = "val_" + datetime.now(FUSO_BR).strftime("%Y%m%d_%H%M%S") + ".jpg"
                cf = os.path.join(PASTA_FOTOS, nf)
                image.save(cf)
                nv["foto"] = nf
                salvar_validacao(nv)
                st.markdown('<div class="success-box">Validacao salva!</div>', unsafe_allow_html=True)
                st.rerun()
    with tab2:
        if validacoes:
            for v in validacoes[:10]:
                tia = v.get("total_objetos_ia", 0)
                teq = v.get("total_objetos_manual", 0)
                st.markdown("- **" + v.get("tipo", "") + "** - " + v.get("data", "")[:16] + " - IA: " + str(tia) + " | Equipe: " + str(teq))
        else:
            st.info("Nenhuma validacao.")


elif menu == "Scanner QR/Barcode":
    st.markdown("### Scanner QR / Barcode")
    if "scanner_lista" not in st.session_state:
        st.session_state["scanner_lista"] = []
    tab1, tab2 = st.tabs(["Escanear", "Lista / Exportar"])
    with tab1:
        codigo_input = st.text_input("Codigo (escaneie ou digite)", placeholder="Escaneie aqui...", key="scan_input")
        destino_input = st.text_input("Destino", placeholder="Digite o destino")
        if st.button("Adicionar a Lista", type="primary", use_container_width=True):
            if codigo_input:
                item_scan = {"codigo": codigo_input, "destino": destino_input, "horario": datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M:%S")}
                st.session_state["scanner_lista"].append(item_scan)
                st.markdown('<div class="success-box">Adicionado: ' + codigo_input + '</div>', unsafe_allow_html=True)
            else:
                st.error("Escaneie ou digite um codigo!")
    with tab2:
        lista_sc = st.session_state.get("scanner_lista", [])
        if lista_sc:
            df_sc = pd.DataFrame(lista_sc)
            st.dataframe(df_sc, use_container_width=True, hide_index=True)
            st.markdown("Total: **" + str(len(lista_sc)) + "** itens")
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                buf = io.BytesIO()
                df_sc.to_excel(buf, index=False, engine="openpyxl")
                st.download_button("Baixar Excel", data=buf.getvalue(), file_name="scanner_" + datetime.now(FUSO_BR).strftime("%Y%m%d_%H%M") + ".xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            with sc2:
                csv_data = df_sc.to_csv(index=False)
                st.download_button("Baixar CSV", data=csv_data, file_name="scanner_" + datetime.now(FUSO_BR).strftime("%Y%m%d_%H%M") + ".csv", mime="text/csv", use_container_width=True)
            with sc3:
                if st.button("Limpar Lista", use_container_width=True):
                    st.session_state["scanner_lista"] = []
                    st.rerun()
        else:
            st.info("Nenhum item escaneado.")


elif menu == "Enviar por WhatsApp":
    st.markdown("### Enviar por WhatsApp")
    tab1, tab2 = st.tabs(["Escala do Dia", "Mensagem Livre"])
    with tab1:
        escala_wpp = st.session_state.get("ultima_escala_wpp", "")
        if escala_wpp:
            st.markdown("#### Escala pronta para envio:")
            st.code(escala_wpp)
            numeros_wpp = st.text_area("Numeros (um por linha, com DDD)", placeholder="11999999999")
            if st.button("Gerar Links WhatsApp", type="primary", use_container_width=True):
                texto_encoded = urllib.parse.quote(escala_wpp)
                if numeros_wpp.strip():
                    for num in numeros_wpp.strip().split(NL):
                        num = num.strip()
                        if num:
                            link = "https://wa.me/55" + num + "?text=" + texto_encoded
                            st.markdown("[Enviar para " + num + "](" + link + ")")
                else:
                    link = "https://wa.me/?text=" + texto_encoded
                    st.markdown("[Abrir WhatsApp](" + link + ")")
        else:
            st.info("Gere uma escala primeiro.")
    with tab2:
        msg_livre = st.text_area("Mensagem", placeholder="Digite sua mensagem...")
        numeros_livre = st.text_area("Numeros (um por linha)", placeholder="11999999999", key="nums_livre")
        if st.button("Gerar Links", type="primary", use_container_width=True, key="btn_wpp_livre"):
            if msg_livre:
                texto_enc = urllib.parse.quote(msg_livre)
                if numeros_livre.strip():
                    for num in numeros_livre.strip().split(NL):
                        num = num.strip()
                        if num:
                            link = "https://wa.me/55" + num + "?text=" + texto_enc
                            st.markdown("[Enviar para " + num + "](" + link + ")")
                else:
                    link = "https://wa.me/?text=" + texto_enc
                    st.markdown("[Abrir WhatsApp](" + link + ")")
            else:
                st.error("Digite uma mensagem!")

elif menu == "Relatorios":
    st.markdown("### Relatorios")
    tipo_rel = st.selectbox("Tipo", ["Escalas", "Motoristas", "Validacoes", "Funcionarios", "Absenteismo", "Desempenho", "Forecast", "Timer CPT"])
    dr1, dr2 = st.columns(2)
    with dr1:
        data_ini = st.date_input("Inicio", value=date.today() - timedelta(days=7), key="rel_ini")
    with dr2:
        data_fim = st.date_input("Fim", value=date.today(), key="rel_fim")
    di_str = data_ini.strftime("%Y-%m-%d")
    df_str = data_fim.strftime("%Y-%m-%d")
    dados_rel = []
    if tipo_rel == "Escalas":
        dados_rel = [e for e in carregar_escalas() if di_str <= e.get("data", "") <= df_str]
    elif tipo_rel == "Motoristas":
        dados_rel = [m for m in carregar_motoristas() if di_str <= m.get("data_chegada", m.get("data_registro", ""))[:10] <= df_str]
    elif tipo_rel == "Validacoes":
        dados_rel = [v for v in carregar_validacoes() if di_str <= v.get("data", "")[:10] <= df_str]
    elif tipo_rel == "Funcionarios":
        dados_rel = carregar_funcionarios()
    elif tipo_rel == "Absenteismo":
        dados_rel = [a for a in carregar_absenteismo() if di_str <= a.get("data", "") <= df_str]
    elif tipo_rel == "Desempenho":
        dados_rel = [d for d in carregar_desempenho() if di_str <= d.get("data_avaliacao", "")[:10] <= df_str]
    elif tipo_rel == "Forecast":
        dados_rel = carregar_forecast()
    elif tipo_rel == "Timer CPT":
        dados_rel = [t for t in carregar_timer_historico() if di_str <= t.get("data", "") <= df_str]
    if dados_rel:
        df_rel = pd.DataFrame(dados_rel)
        st.dataframe(df_rel, use_container_width=True, hide_index=True)
        st.markdown("Total: **" + str(len(dados_rel)) + "** registros")
        re1, re2 = st.columns(2)
        with re1:
            buf = io.BytesIO()
            df_rel.to_excel(buf, index=False, engine="openpyxl")
            st.download_button("Baixar Excel", data=buf.getvalue(), file_name="rel_" + tipo_rel.lower() + ".xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        with re2:
            csv_rel = df_rel.to_csv(index=False)
            st.download_button("Baixar CSV", data=csv_rel, file_name="rel_" + tipo_rel.lower() + ".csv", mime="text/csv", use_container_width=True)
    else:
        st.info("Nenhum registro no periodo.")


elif menu == "Configuracoes":
    st.markdown("### Configuracoes")
    tab1, tab2, tab3 = st.tabs(["Site / CPT", "Sistema", "Ajuda"])
    with tab1:
        st.markdown("#### Informacoes do Site")
        st.markdown("- **Site:** " + SITE)
        st.markdown("- **Operacao:** First Mile / Cross Dock")
        st.markdown("- **Turno:** Noturno")
        st.markdown("- **Fuso:** America/Sao_Paulo")
        st.markdown("---")
        st.markdown("#### Meta CPT (editavel)")
        st.markdown("CPT atual: **" + str(CPT_HORA).zfill(2) + ":" + str(CPT_MINUTO).zfill(2) + "** | Alerta: **" + str(ALERTA_HORA) + "h**")
        with st.form("form_cpt"):
            cpt1, cpt2, cpt3 = st.columns(3)
            with cpt1:
                novo_cpt_hora = st.number_input("CPT Hora", min_value=0, max_value=23, value=CPT_HORA)
            with cpt2:
                novo_cpt_min = st.number_input("CPT Minuto", min_value=0, max_value=59, value=CPT_MINUTO)
            with cpt3:
                novo_alerta = st.number_input("Alerta (hora)", min_value=0, max_value=23, value=ALERTA_HORA)
            btn_cpt = st.form_submit_button("Salvar Meta CPT", use_container_width=True)
            if btn_cpt:
                cfg = {"cpt_hora": novo_cpt_hora, "cpt_minuto": novo_cpt_min, "alerta_hora": novo_alerta}
                salvar_config(cfg)
                st.markdown('<div class="success-box">CPT atualizado para ' + str(novo_cpt_hora).zfill(2) + ':' + str(novo_cpt_min).zfill(2) + '</div>', unsafe_allow_html=True)
                st.rerun()
    with tab2:
        st.markdown("#### Sistema")
        st.markdown("- **Versao:** 8.0 (Supabase)")
        st.markdown("- **Banco:** PostgreSQL (Supabase)")
        st.markdown("- **Framework:** Streamlit")
        st.markdown("- **IA:** YOLO v8 (" + ("Instalado" if yolo_ok else "Nao instalado") + ")")
    with tab3:
        st.markdown("#### Como usar")
        st.markdown("1. Cadastre funcionarios")
        st.markdown("2. Registre o forecast")
        st.markdown("3. Gere a escala")
        st.markdown("4. Registre motoristas")
        st.markdown("5. Faca validacoes por foto")
        st.markdown("6. Use o scanner")
        st.markdown("7. Envie escala por WhatsApp")
        st.markdown("8. Consulte relatorios")


elif menu == "Gerenciar Usuarios":
    st.markdown("### Gerenciar Usuarios")
    usuarios = carregar_usuarios()
    tab1, tab2 = st.tabs(["Novo Usuario", "Lista / Editar"])
    with tab1:
        with st.form("form_novo_user"):
            nu1, nu2 = st.columns(2)
            with nu1:
                novo_user = st.text_input("Login (usuario)")
                novo_nome = st.text_input("Nome Completo")
            with nu2:
                novo_perfil = st.selectbox("Perfil", ["Admin", "Supervisor", "Operador", "Equipe", "Visualizador"])
                nova_senha = st.text_input("Senha", type="password")
            btn_nu = st.form_submit_button("Criar Usuario", use_container_width=True)
            if btn_nu:
                if novo_user and novo_nome and nova_senha:
                    existe = False
                    for u in usuarios:
                        if u["usuario"] == novo_user.lower().strip():
                            existe = True
                            break
                    if existe:
                        st.error("Usuario ja existe!")
                    else:
                        nu = {"usuario": novo_user.lower().strip(), "senha": cifrar_senha(nova_senha), "nome": novo_nome, "perfil": novo_perfil, "status": "Ativo", "criado_em": datetime.now(FUSO_BR).strftime("%d/%m/%Y")}
                        salvar_usuario(nu)
                        st.markdown('<div class="success-box">Usuario ' + novo_user + ' criado!</div>', unsafe_allow_html=True)
                        st.rerun()
                else:
                    st.error("Preencha todos os campos!")
    with tab2:
        if usuarios:
            df_u = pd.DataFrame(usuarios)
            cols_u = ["usuario", "nome", "perfil", "status", "criado_em"]
            cols_ok = [c for c in cols_u if c in df_u.columns]
            st.dataframe(df_u[cols_ok], use_container_width=True, hide_index=True)
            st.markdown("---")
            st.markdown("#### Editar Usuario")
            nomes_u = [u["usuario"] + " (" + u["nome"] + ")" for u in usuarios]
            sel_u = st.selectbox("Selecione", nomes_u, key="sel_u_edit")
            idx_u = nomes_u.index(sel_u)
            ue = usuarios[idx_u]
            perfis_list = ["Admin", "Supervisor", "Operador", "Equipe", "Visualizador"]
            status_u_list = ["Ativo", "Inativo"]
            pi = perfis_list.index(ue.get("perfil", "Operador")) if ue.get("perfil", "Operador") in perfis_list else 2
            sui = status_u_list.index(ue.get("status", "Ativo")) if ue.get("status", "Ativo") in status_u_list else 0
            with st.form("form_edit_user"):
                eu1, eu2 = st.columns(2)
                with eu1:
                    eun = st.text_input("Nome", value=ue.get("nome", ""))
                    eup = st.selectbox("Perfil", perfis_list, index=pi)
                with eu2:
                    eus = st.selectbox("Status", status_u_list, index=sui)
                    nova_s = st.text_input("Nova Senha (vazio = manter)", type="password")
                bsu = st.form_submit_button("Salvar", use_container_width=True)
                if bsu:
                    dados_u = {"nome": eun, "perfil": eup, "status": eus}
                    if nova_s:
                        dados_u["senha"] = cifrar_senha(nova_s)
                    atualizar_usuario(ue["id"], dados_u)
                    st.markdown('<div class="success-box">Atualizado!</div>', unsafe_allow_html=True)
                    st.rerun()
        else:
            st.info("Nenhum usuario.")


rodape = '<div style="text-align: center; color: #666; padding: 20px;">' + SITE + ' Manager v8.0 | First Mile Operations | Supabase</div>'
st.markdown("---")
st.markdown(rodape, unsafe_allow_html=True)



PERFIS_ACESSO = {"Admin": ["Dashboard", "Cadastro de Funcionarios", "Gerador de Escala", "Registro de Motorista", "Absenteismo", "Desempenho por Funcao", "Forecast / Volume", "Validacao por Foto (IA)", "Scanner QR/Barcode", "Enviar por WhatsApp", "Relatorios", "Configuracoes", "Gerenciar Usuarios"], "Supervisor": ["Dashboard", "Cadastro de Funcionarios", "Gerador de Escala", "Registro de Motorista", "Absenteismo", "Desempenho por Funcao", "Forecast / Volume", "Validacao por Foto (IA)", "Scanner QR/Barcode", "Enviar por WhatsApp", "Relatorios"], "Operador": ["Dashboard", "Registro de Motorista", "Validacao por Foto (IA)", "Scanner QR/Barcode"], "Equipe": ["Registro de Motorista"], "Visualizador": ["Dashboard", "Relatorios"]}
