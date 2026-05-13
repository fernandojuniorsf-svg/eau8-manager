import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import io
import hashlib
from datetime import datetime, date, timedelta
import pytz
import psycopg2

@st.cache_data(ttl=30)
def cached_query(sql):
    return query(sql)

FUSO_BR = pytz.timezone("America/Sao_Paulo")
SITE = "EUA8"
POSICOES = ["Pick to Buffer Esteira 1", "Pick to Buffer Esteira 2", "Stow Esteira 1", "Stow Esteira 1 (2)", "Stow Esteira 2", "Spider de Fechamento / Stow Esteira 2", "Receiver", "Unloader", "YardMarshall", "Spider de Inducao - Doca", "Carregamento", "Xerife"]
TIPOS_VEICULO = ["Carreta (28 pallets)", "Truck (16 pallets)", "VUC (6 pallets)", "3/4", "Fiorino", "Van", "Bitruck", "Outro"]

def gerar_hash(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

SENHA_ADMIN = gerar_hash(str(4848) + str(8813) + str(58) + "fer")
SENHA_EQUIPE = gerar_hash("eua" + str(8))

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
    cols = [desc.name for desc in cur.description] if cur.description else []
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(zip(cols, r)) for r in rows]

def query_one(sql, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    cols = [desc.name for desc in cur.description] if cur.description else []
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return dict(zip(cols, row))
    return None

def execute(sql, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    conn.commit()
    cur.close()
    conn.close()
    
def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, usuario TEXT UNIQUE, senha TEXT, nome TEXT, perfil TEXT, status TEXT, criado_em TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS funcionarios (id SERIAL PRIMARY KEY, nome TEXT, tipo TEXT, funcao TEXT, turno TEXT, status TEXT, data_admissao TEXT, telefone TEXT, observacoes TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS escalas (id SERIAL PRIMARY KEY, data TEXT, funcionario TEXT, posicao TEXT, turno TEXT, tipo_escala TEXT, gerado_em TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS motoristas (id SERIAL PRIMARY KEY, nome TEXT, placa TEXT, tipo_veiculo TEXT, telefone TEXT, observacao TEXT, horario_chegada TEXT, horario_saida TEXT, observacoes TEXT, destino TEXT, data_chegada TEXT, data_registro TEXT, importado BOOLEAN DEFAULT FALSE, foto TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS absenteismo (id SERIAL PRIMARY KEY, funcionario TEXT, data TEXT, motivo TEXT, observacoes TEXT, registrado_em TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS desempenho (id SERIAL PRIMARY KEY, funcionario TEXT, posicao TEXT, nota INTEGER, data_avaliacao TEXT, observacoes TEXT, registrado_em TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS forecast (id SERIAL PRIMARY KEY, data TEXT, volume INTEGER, observacoes TEXT, registrado_em TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS validacoes (id SERIAL PRIMARY KEY, tipo TEXT, data TEXT, total_objetos_ia INTEGER, contagem_ia TEXT, total_objetos_manual INTEGER, contagem_manual TEXT, foto TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS timer_historico (id SERIAL PRIMARY KEY, data TEXT, hora_inicio TEXT, hora_conclusao TEXT, registrado_em TEXT, registrado_por TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS configuracoes (id SERIAL PRIMARY KEY, chave TEXT UNIQUE, valor TEXT)""")
    cur.execute("SELECT COUNT(*) FROM usuarios")
    if cur.fetchone() == 0:
        cur.execute("INSERT INTO usuarios (usuario, senha, nome, perfil, status, criado_em) VALUES (%s,%s,%s,%s,%s,%s)", ("fernando", SENHA_ADMIN, "Fernando Junior", "Admin", "Ativo", "2026-05-03"))
        cur.execute("INSERT INTO usuarios (usuario, senha, nome, perfil, status, criado_em) VALUES (%s,%s,%s,%s,%s,%s)", ("equipe", SENHA_EQUIPE, "[PASSWORD]", "Equipe", "Ativo", "2026-05-03"))
    conn.commit()
    cur.close()
    conn.close()

def carregar_usuarios():
    return query("SELECT * FROM usuarios ORDER BY id")

def carregar_funcionarios():
    return query("SELECT * FROM funcionarios ORDER BY nome")

def salvar_funcionario(f):
    execute("INSERT INTO funcionarios (nome, tipo, funcao, turno, status, data_admissao, telefone, observacoes, posicoes_permitidas) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", (f["nome"], f["tipo"], f["funcao"], f["turno"], f["status"], f.get("data_admissao",""), f.get("telefone",""), f.get("observacoes",""), f.get("posicoes_permitidas","")))

def atualizar_funcionario(fid, dados):
    sets = ", ".join([k + "=%s" for k in dados.keys()])
    execute("UPDATE funcionarios SET " + sets + " WHERE id=%s", list(dados.values()) + [fid])

def atualizar_usuario(uid, dados):
    campos = []
    valores = []
    for k, v in dados.items():
        campos.append(k + " = %s")
        valores.append(v)
    valores.append(uid)
    execute("UPDATE usuarios SET " + ", ".join(campos) + " WHERE id = %s", tuple(valores))

def excluir_funcionario(fid):
    execute("DELETE FROM funcionarios WHERE id=%s", (fid,))

def carregar_escalas():
    return query("SELECT * FROM escalas ORDER BY data DESC, id")

def salvar_escala(e):
    execute("INSERT INTO escalas (data, funcionario, posicao, turno, tipo_escala, gerado_em) VALUES (%s,%s,%s,%s,%s,%s)", (e["data"], e["funcionario"], e["posicao"], e["turno"], e.get("tipo_escala","operacional"), e["gerado_em"]))

def limpar_escalas_data(data_str, tipo_escala):
    execute("DELETE FROM escalas WHERE data=%s AND tipo_escala=%s", (data_str, tipo_escala))

def carregar_motoristas():
    return query("SELECT * FROM motoristas ORDER BY id DESC")

def salvar_motorista(m):
    execute("INSERT INTO motoristas (nome, placa, tipo_veiculo, telefone, observacao, horario_chegada, horario_saida, observacoes, destino, data_chegada, data_registro, importado, foto) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (m["nome"], m.get("placa",""), m.get("tipo_veiculo",""), m.get("telefone",""), m.get("observacao",""), m.get("horario_chegada",""), m.get("horario_saida",""), m.get("observacoes",""), m.get("destino",""), m.get("data_chegada",""), m.get("data_registro",""), m.get("importado", False), m.get("foto","")))

def atualizar_motorista(mid, dados):
    sets = ", ".join([k + "=%s" for k in dados.keys()])
    execute("UPDATE motoristas SET " + sets + " WHERE id=%s", list(dados.values()) + [mid])

def limpar_motoristas_importados():
    execute("DELETE FROM motoristas WHERE importado = true")

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

def carregar_config():
    rows = query("SELECT * FROM configuracoes")
    return {r["chave"]: r["valor"] for r in rows}

def salvar_config(chave, valor):
    execute("INSERT INTO configuracoes (chave, valor) VALUES (%s, %s) ON CONFLICT (chave) DO UPDATE SET valor = EXCLUDED.valor", (chave, valor))

def get_config_valor(chave, default="0"):
    r = query_one("SELECT valor FROM configuracoes WHERE chave=%s", (chave,))
    return r["valor"] if r else default

try:
    init_db()
except Exception as e:
    st.error("Erro ao conectar no banco: " + str(e))
    st.stop()

CONFIG = carregar_config()
CPT_HORA = int(CONFIG.get("cpt_hora", "20"))
CPT_MINUTO = int(CONFIG.get("cpt_minuto", "0"))
ALERTA_HORA = int(CONFIG.get("alerta_hora", "19"))
PERFIS_ACESSO = {"Admin": ["Dashboard", "Cadastro de Funcionários", "Gerador de Escala", "Registro de Motorista", "Absenteísmo", "Desempenho por Função", "Forecast / Volume", "Validação por Foto (IA)", "Scanner QR/Barcode", "Enviar por WhatsApp", "Relatorios", "Configurações", "Gerenciar Usuários"], "Supervisor": ["Dashboard", "Cadastro de Funcionários", "Gerador de Escala", "Registro de Motorista", "Absenteísmo", "Desempenho por Função", "Forecast / Volume", "Validação por Foto (IA)", "Scanner QR/Barcode", "Enviar por WhatsApp", "Relatórios"], "operador": ["Dashboard", "Registro de Motorista", "Validação por Foto (IA)", "Scanner QR/Barcode"], "equipe": ["Dashboard", "Registro de Motorista"], "Visualizador": ["Dashboard", "Relatorios"]}
st.set_page_config(page_title=SITE + " Manager", page_icon="F", layout="wide")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&display=swap');
* {font-family: 'Inter', sans-serif;}
.stApp {background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #0a0a0a 100%); color: #e0e0e0;}
[data-testid="stSidebar"] {background: linear-gradient(180deg, #0d0d0d 0%, #1a1a1a 100%) !important; border-right: 1px solid #2a2a2a;}
[data-testid="stSidebar"] .stMarkdown {color: #ccc;}
div[data-testid="stMetric"] {background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3a 100%); padding: 20px; border-radius: 14px; border: 1px solid #333; box-shadow: 0 4px 20px rgba(0,0,0,0.3);}
div[data-testid="stMetric"] label {color: #888 !important; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {color: #FF9900 !important; font-weight: 700;}
div[data-testid="stForm"] {background: linear-gradient(135deg, #1a1a2a 0%, #222233 100%); padding: 24px; border-radius: 16px; border: 1px solid #333; box-shadow: 0 8px 32px rgba(0,0,0,0.3);}
.stButton > button {background: linear-gradient(135deg, #FF9900 0%, #e68a00 100%); color: #000; font-weight: 600; border: none; border-radius: 8px; padding: 8px 24px; transition: all 0.3s;}
.stButton > button:hover {background: linear-gradient(135deg, #ffad33 0%, #FF9900 100%); transform: translateY(-1px); box-shadow: 0 4px 12px rgba(255,153,0,0.3);}
.success-box {background: linear-gradient(135deg, #0a2a0a 0%, #1a3a1a 100%); border: 1px solid #00C853; border-radius: 10px; padding: 14px; color: #a5d6a7; box-shadow: 0 4px 12px rgba(0,200,83,0.1);}
.warning-box {background: linear-gradient(135deg, #2a2a0a 0%, #3a3a1a 100%); border: 1px solid #FF9900; border-radius: 10px; padding: 14px; color: #ffe082; box-shadow: 0 4px 12px rgba(255,153,0,0.1);}
.error-box {background: linear-gradient(135deg, #2a0a0a 0%, #3a1a1a 100%); border: 1px solid #EF4444; border-radius: 10px; padding: 14px; color: #ef9a9a; box-shadow: 0 4px 12px rgba(239,68,68,0.1);}
.progress-bar {width: 100%; height: 10px; background: #222; border-radius: 6px; margin: 10px 0; overflow: hidden;}
.progress-fill {height: 100%; background: linear-gradient(90deg, #FF9900 0%, #ffcc00 100%); border-radius: 6px; transition: width 0.8s ease;}
h1, h2, h3 {color: #FF9900 !important; font-weight: 700;}
.stDataFrame {border-radius: 12px; overflow: hidden;}
div[data-testid="stDataFrame"] > div {border-radius: 12px;}
.stSelectbox > div > div {background: #1e1e2e; border: 1px solid #333; border-radius: 8px;}
.stTextInput > div > div > input {background: #1e1e2e; border: 1px solid #333; border-radius: 8px; color: #e0e0e0;}
.stNumberInput > div > div > input {background: #1e1e2e; border: 1px solid #333; border-radius: 8px; color: #e0e0e0;}
</style>""", unsafe_allow_html=True)

if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    _, col_login, _ = st.columns([1,2,1])
    with col_login:
        st.markdown("# " + SITE + " Manager")
        st.markdown("*First Mile Operations | Amazon Logistics*")
        st.markdown("---")
        st.markdown("### Login")
        with st.form("form_login"):
            usuario_input = st.text_input("Usuário")
            senha_input = st.text_input("Senha", type="password")
            btn_login = st.form_submit_button("Entrar", use_container_width=True)
            if btn_login:
                if usuario_input and senha_input:
                    usuarios = carregar_usuarios()
                    encontrou = False
                    for u in usuarios:
                        if u["usuario"] == usuario_input and u["senha"] == gerar_hash(senha_input):
                            if u.get("status", "Ativo") != "Ativo":
                                st.error("Usuário inativo.")
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
                        st.error("Usuário ou senha incorretos!")
                else:
                    st.error("Preencha usuário e senha!")
    st.stop()

nome_logado = st.session_state.get("nome_logado", "Usuário")
perfil_logado = st.session_state.get("perfil_logado", "Operador")
st.sidebar.markdown("## " + SITE + " Manager")
st.sidebar.markdown("*First Mile Operations*")
st.sidebar.markdown("Bem-vindo, **" + nome_logado + "** (" + perfil_logado + ")")
st.sidebar.markdown("---")
menus_permitidos = PERFIS_ACESSO.get(perfil_logado, ["Dashboard"])
todos_menus = ["Dashboard", "Cadastro de Funcionários", "Gerador de Escala", "Registro de Motorista", "Absenteísmo", "Desempenho por Função", "Forecast / Volume", "Validação por Foto (IA)", "Scanner QR/Barcode", "Enviar por WhatsApp", "Relatorios", "Configurações", "Gerenciar Usuários"]
menus_visiveis = [m for m in todos_menus if m in menus_permitidos]
menu = st.sidebar.radio("Menu Principal", menus_visiveis)
st.sidebar.markdown("---")
agora_dt = datetime.now(FUSO_BR)
agora = agora_dt.strftime("%d/%m/%Y %H:%M")
hoje_str = agora_dt.strftime("%Y-%m-%d")
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
    motoristas = carregar_motoristas()
    funcionarios = carregar_funcionarios()
    escalas = carregar_escalas()
    absenteismo_lista = carregar_absenteismo()
    forecasts = carregar_forecast()
    st.markdown("### Timer CPT")
    timer_hoje = [t for t in carregar_timer_historico() if t.get("data","") == hoje_str]
    ultimo_timer = None
    for tt in timer_hoje:
        if tt.get("hora_conclusao", "") == "":
            ultimo_timer = tt
            break
    timer_ativo = ultimo_timer is not None
    cpt_target = agora_dt.replace(hour=CPT_HORA, minute=CPT_MINUTO, second=0, microsecond=0)
    if not timer_ativo:
        timer_texto = "Aguardando"
        timer_cor = "#666666"
        timer_sombra = "0 0 20px rgba(100,100,100,0.3)"
        timer_sub = "Inicie o turno abaixo"
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
    timer_html = "<div style=\"display:flex; justify-content:center; margin:20px 0;\">"
    timer_html += "<div style=\"width:280px; height:280px; border-radius:50%; background:" + grad_circulo + "; display:flex; align-items:center; justify-content:center; box-shadow:" + timer_sombra + ";\">"
    timer_html += "<div style=\"width:240px; height:240px; border-radius:50%; background:#1a1a1a; display:flex; flex-direction:column; align-items:center; justify-content:center;\">"
    timer_html += "<p style=\"font-size:56px; font-weight:900; color:" + timer_cor + "; margin:0; letter-spacing:-2px;\">" + timer_texto + "</p>"
    timer_html += "<p style=\"font-size:13px; color:#999; margin:4px 0 0 0; text-transform:uppercase; letter-spacing:1px;\">" + timer_sub + "</p>"
    timer_html += "<p style=\"font-size:11px; color:#666; margin:4px 0 0 0;\">" + agora_dt.strftime("%H:%M:%S") + "</p>"
    timer_html += "</div></div></div>"
    st.markdown(timer_html, unsafe_allow_html=True)
    js_rt = "<script>function atRelogio(){var e=document.getElementById('timer-clock');if(e){var d=new Date();e.innerText=String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0')+':'+String(d.getSeconds()).padStart(2,'0');}}setInterval(atRelogio,1000);setTimeout(function(){window.location.reload();},60000);</script>"
    st.markdown(js_rt, unsafe_allow_html=True)
    bt1, bt2, bt3 = st.columns(3)
    with bt1:
        if not timer_ativo:
            with st.form("form_iniciar_turno"):
                hora_inicio_input = st.text_input("Horario de inicio (HH:MM)", value=agora_dt.strftime("%H:%M"))
                btn_iniciar = st.form_submit_button("Iniciar Turno", use_container_width=True)
                if btn_iniciar:
                    t = {"data": hoje_str, "hora_inicio": hora_inicio_input, "hora_conclusao": "", "registrado_em": agora_dt.strftime("%d/%m/%Y %H:%M"), "registrado_por": nome_logado}
                    salvar_timer_historico(t)
                    st.rerun()
        else:
            st.markdown("<div class=\"success-box\">Turno iniciado as " + ultimo_timer.get("hora_inicio", "") + "</div>", unsafe_allow_html=True)
    with bt2:
        if timer_ativo:
            with st.form("form_concluir_turno"):
                hora_conclusao_input = st.text_input("Horario de conclusao (HH:MM)", value=agora_dt.strftime("%H:%M"))
                btn_concluir = st.form_submit_button("Concluir Turno", use_container_width=True)
                if btn_concluir:
                    execute("UPDATE timer_historico SET hora_conclusao=%s WHERE id=%s", (hora_conclusao_input, ultimo_timer["id"]))
                    st.rerun()
    with bt3:
        if st.button("Atualizar", use_container_width=True):
            st.rerun()
    st.markdown("---")
    st.markdown("### Volumes do Dia")
    vol1, vol2, vol3 = st.columns(3)
    with vol1:
        with st.form("form_previsao_dia"):
            prev_atual = int(get_config_valor("previsao_" + hoje_str, "0"))
            previsao_dia = st.number_input("Previsao do Dia (pacotes)", min_value=0, max_value=200000, value=prev_atual, step=100, key="prev_dia")
            btn_prev = st.form_submit_button("Salvar Previsao", use_container_width=True)
            if btn_prev:
                salvar_config("previsao_" + hoje_str, str(previsao_dia))
                st.rerun()
        prev_valor = int(get_config_valor("previsao_" + hoje_str, "0"))
        st.metric("Previsao do Dia", str(prev_valor) + " pacotes")
    with vol2:
        fc_hoje = [f for f in forecasts if f.get("data","") == hoje_str]
        fc_valor = fc_hoje[0] ["volume"] if fc_hoje else 0
        st.metric("Forecast", str(fc_valor) + " pacotes")
    with vol3:
        with st.form("form_processados"):
            proc_atual = int(get_config_valor("processados_" + hoje_str, "0"))
            processados = st.number_input("Pacotes Processados", min_value=0, max_value=200000, value=proc_atual, step=100, key="proc_dia")
            btn_proc = st.form_submit_button("Atualizar Processados", use_container_width=True)
            if btn_proc:
                salvar_config("processados_" + hoje_str, str(processados))
                st.rerun()
        proc_valor = int(get_config_valor("processados_" + hoje_str, "0"))
        st.metric("Processados", str(proc_valor) + " pacotes")
    st.markdown("---")
    st.markdown("### Desempenho")
    pct_prev = int((proc_valor / prev_valor) * 100) if prev_valor > 0 else 0
    pct_fc = int((proc_valor / fc_valor) * 100) if fc_valor > 0 else 0
    gr1, gr2 = st.columns(2)
    with gr1:
        cor_prev = "#00C853" if pct_prev >= 100 else "#FF9900" if pct_prev >= 70 else "#EF4444"
        st.markdown("<div style=\"background:#2d2d2d; border-radius:12px; padding:20px; text-align:center; border:1px solid #444;\"><p style=\"color:#999; font-size:12px; margin:0 0 8px 0;\">PROCESSADOS x PREVISAO DO DIA</p><p style=\"font-size:48px; font-weight:900; color:" + cor_prev + "; margin:0;\">" + str(pct_prev) + "%</p><p style=\"color:#999; font-size:11px; margin:4px 0 0 0;\">" + str(proc_valor) + " / " + str(prev_valor) + " pacotes</p><div class=\"progress-bar\"><div class=\"progress-fill\" style=\"width:" + str(min(pct_prev, 100)) + "%; background:" + cor_prev + ";\"></div></div></div>", unsafe_allow_html=True)
    with gr2:
        cor_fc = "#00C853" if pct_fc >= 100 else "#FF9900" if pct_fc >= 70 else "#EF4444"
        st.markdown("<div style=\"background:#2d2d2d; border-radius:12px; padding:20px; text-align:center; border:1px solid #444;\"><p style=\"color:#999; font-size:12px; margin:0 0 8px 0;\">PROCESSADOS x FORECAST</p><p style=\"font-size:48px; font-weight:900; color:" + cor_fc + "; margin:0;\">" + str(pct_fc) + "%</p><p style=\"color:#999; font-size:11px; margin:4px 0 0 0;\">" + str(proc_valor) + " / " + str(fc_valor) + " pacotes</p><div class=\"progress-bar\"><div class=\"progress-fill\" style=\"width:" + str(min(pct_fc, 100)) + "%; background:" + cor_fc + ";\"></div></div></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Progresso Motoristas")
    mot_hoje = [m for m in motoristas if m.get("data_chegada","")[:10] == hoje_str and m.get("importado", False)]
    total_mot = len(mot_hoje)
    mot_com_saida = len([m for m in mot_hoje if m.get("horario_saida", "")])
    pct_mot = int((mot_com_saida / total_mot) * 100) if total_mot > 0 else 0
    cm1, cm2 = st.columns(2)
    with cm1:
        st.markdown("<div style=\"background:#2d2d2d; border-radius:12px; padding:20px; text-align:center; border:1px solid #444;\"><p style=\"font-size:42px; font-weight:900; color:#FF9900; margin:0;\">" + str(pct_mot) + "%</p><p style=\"color:#999; font-size:12px; margin:4px 0 0 0;\">MOTORISTAS DESPACHADOS</p><div class=\"progress-bar\"><div class=\"progress-fill\" style=\"width:" + str(pct_mot) + "%;\"></div></div></div>", unsafe_allow_html=True)
    with cm2:
        st.markdown("<div style=\"background:#2d2d2d; border-radius:12px; padding:20px; text-align:center; border:1px solid #444;\"><p style=\"color:#999; font-size:12px; margin:0 0 8px 0;\">DETALHAMENTO</p><p style=\"color:#00C853; font-size:14px; margin:4px 0;\"><strong>" + str(mot_com_saida) + "</strong> despachados</p><p style=\"color:#FF9900; font-size:14px; margin:4px 0;\"><strong>" + str(total_mot - mot_com_saida) + "</strong> aguardando</p><p style=\"color:#8B5CF6; font-size:14px; margin:4px 0;\"><strong>" + str(total_mot) + "</strong> total do dia</p></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Equipe do Dia")
    ativos = [f for f in funcionarios if f.get("status") == "Ativo"]
    abs_hoje = [a for a in absenteismo_lista if a.get("data","") == hoje_str]
    eq1, eq2 = st.columns(2)
    with eq1:
        st.metric("Associados Ativos", len(ativos))
    with eq2:
        st.metric("Absenteismo Hoje", len(abs_hoje))
    if abs_hoje:
        st.markdown("**Ausentes:**")
        for ab in abs_hoje:
            st.markdown("- " + ab["funcionario"] + " (" + ab.get("motivo", "") + ")")
elif menu == "Cadastro de Funcionários":
    st.markdown("### Cadastro de Funcionários")
    funcionarios = carregar_funcionarios()
    tab1, tab2 = st.tabs(["Cadastrar", "Lista / Editar"])
    with tab1:
        with st.form("form_func"):
            f1, f2 = st.columns(2)
            with f1:
                nome_func = st.text_input("Nome Completo")
                tipo_func = st.selectbox("Tipo", ["Fixo", "Freelancer/Diarista"])
                funcao_func = st.text_input("Funcao", value="Associado")
            with f2:
                turno_func = st.selectbox("Turno", ["Noturno", "Diurno", "Misto"])
                status_func = st.selectbox("Status", ["Ativo", "Inativo", "Ferias", "Afastado"])
                tel_func = st.text_input("Telefone (opcional)")
            obs_func = st.text_area("Observacoes", height=80)
            st.markdown("**Posicoes habilitadas:**")
            todas_pos = st.checkbox("Selecionar todas", value=True, key="chk_todas")
            posicoes_func = []
            for idx_p, pos_nome in enumerate(POSICOES):
                marcado = st.checkbox(pos_nome, value=todas_pos, key="pos_" + str(idx_p))
                if marcado:
                    posicoes_func.append(pos_nome)
            btn_func = st.form_submit_button("Cadastrar", use_container_width=True)
            if btn_func:
                if nome_func:
                    salvar_funcionario({"nome": nome_func, "tipo": tipo_func, "funcao": funcao_func, "turno": turno_func, "status": status_func, "data_admissao": hoje_str, "telefone": tel_func, "observacoes": obs_func, "posicoes_permitidas": ",".join(posicoes_func)})
                    st.markdown("<div class=\"success-box\">" + nome_func + " cadastrado!</div>", unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.error("Informe o nome.")

    with tab2:
        if funcionarios:
            df_func = pd.DataFrame(funcionarios)
            cols_f = ["nome", "tipo", "funcao", "turno", "status", "telefone"]
            cols_ok = [c for c in cols_f if c in df_func.columns]
            st.dataframe(df_func[cols_ok], use_container_width=True, hide_index=True)
            st.markdown("---")
            st.markdown("#### Editar / Excluir")
            nomes_func = [f["nome"] for f in funcionarios]
            sel_func = st.selectbox("Selecione o funcionario:", nomes_func, key="sel_func_edit")
            idx_func = nomes_func.index(sel_func)
            func_sel = funcionarios[idx_func]
            with st.form("form_edit_func"):
                ef1, ef2 = st.columns(2)
                with ef1:
                    edit_tipo = st.selectbox("Tipo", ["Fixo", "Freelancer/Diarista"], index=["Fixo", "Freelancer/Diarista"].index(func_sel.get("tipo","Fixo")) if func_sel.get("tipo","Fixo") in ["Fixo", "Freelancer/Diarista"] else 0)
                    edit_status = st.selectbox("Status", ["Ativo", "Inativo", "Ferias", "Afastado"], index=["Ativo", "Inativo", "Ferias", "Afastado"].index(func_sel.get("status","Ativo")) if func_sel.get("status","Ativo") in ["Ativo", "Inativo", "Ferias", "Afastado"] else 0)
                with ef2:
                    edit_turno = st.selectbox("Turno", ["Noturno", "Diurno", "Misto"], index=["Noturno", "Diurno", "Misto"].index(func_sel.get("turno","Noturno")) if func_sel.get("turno","Noturno") in ["Noturno", "Diurno", "Misto"] else 0)
                    edit_tel = st.text_input("Telefone", value=func_sel.get("telefone",""))
                pos_atuais = func_sel.get("posicoes_permitidas", "")
                lista_pos_atuais = pos_atuais.split(",") if pos_atuais else POSICOES
                todas_edit = st.checkbox("Todas as posicoes", value=(pos_atuais == "" or len(pos_atuais) < 3), key="chk_todas_edit")
                if todas_edit:
                    posicoes_edit = POSICOES
                else:
                    posicoes_edit = st.multiselect("Posicoes permitidas", POSICOES, default=[p for p in lista_pos_atuais if p in POSICOES], key="ms_pos_edit")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    btn_salvar_func = st.form_submit_button("Salvar Alteracoes", use_container_width=True)
                with col_btn2:
                    btn_excluir_func = st.form_submit_button("Excluir Funcionario", use_container_width=True)
                if btn_salvar_func:
                    atualizar_funcionario(func_sel["id"], {"tipo": edit_tipo, "status": edit_status, "turno": edit_turno, "telefone": edit_tel, "posicoes_permitidas": ",".join(posicoes_edit)})
                    st.markdown("<div class=\"success-box\">Alteracoes salvas!</div>", unsafe_allow_html=True)
                    st.rerun()
                if btn_excluir_func:
                    excluir_funcionario(func_sel["id"])
                    st.markdown("<div class=\"warning-box\">Funcionario excluido!</div>", unsafe_allow_html=True)
                    st.rerun()
        else:
            st.info("Nenhum funcionario cadastrado.")

elif menu == "Gerador de Escala":
    st.markdown("### Gerador de Escala")
    funcionarios = carregar_funcionarios()
    escalas = carregar_escalas()
    desempenho_lista = carregar_desempenho()
    absenteismo_lista = carregar_absenteismo()
    tab_op, tab_car, tab_hist = st.tabs(["Escala Operacional", "Escala de Carregamento", "Historico"])
    with tab_op:
        st.markdown("#### Configurar Escala do Dia")
        data_escala = st.date_input("Data da Escala", value=date.today(), key="dt_escala_op")
        data_escala_str = data_escala.strftime("%Y-%m-%d")
        abs_dia = [a["funcionario"] for a in absenteismo_lista if a.get("data","") == data_escala_str]
        ativos = [f for f in funcionarios if f.get("status") == "Ativo" and f["nome"] not in abs_dia]
        fixos = [f for f in ativos if f.get("tipo") == "Fixo"]
        diaristas = [f for f in ativos if f.get("tipo") == "Freelancer/Diarista"]
        st.markdown("**Disponiveis:** " + str(len(fixos)) + " fixos | " + str(len(diaristas)) + " diaristas | **Ausentes:** " + str(len(abs_dia)))
        st.markdown("---")
        st.markdown("#### Posicoes Necessarias")
        usar_spider_ind = st.toggle("Tera Spider de Inducao - Doca hoje?", value=False, key="tg_spider_ind")
        usar_notas = st.toggle("Priorizar por nota de desempenho?", value=False, key="tg_notas")
        st.markdown("Ajuste a quantidade de pessoas por posicao:")
        pos_config = {}
        pc1, pc2 = st.columns(2)
        with pc1:
            pos_config["Pick to Buffer Esteira 1"] = st.number_input("Pick to Buffer Esteira 1", min_value=0, max_value=5, value=1, key="pos_ptb1")
            pos_config["Pick to Buffer Esteira 2"] = st.number_input("Pick to Buffer Esteira 2", min_value=0, max_value=5, value=1, key="pos_ptb2")
            pos_config["Stow Esteira 1"] = st.number_input("Stow Esteira 1", min_value=0, max_value=5, value=2, key="pos_st1")
            pos_config["Stow Esteira 2"] = st.number_input("Stow Esteira 2", min_value=0, max_value=5, value=1, key="pos_st2")
        with pc2:
            pos_config["Spider de Fechamento / Stow Esteira 2"] = st.number_input("Spider de Fechamento", min_value=0, max_value=2, value=1, key="pos_spf")
            pos_config["Receiver"] = st.number_input("Receiver", min_value=0, max_value=3, value=1, key="pos_rec")
            pos_config["Unloader"] = st.number_input("Unloader", min_value=0, max_value=5, value=1, key="pos_unl")
            pos_config["YardMarshall"] = st.number_input("YardMarshall", min_value=0, max_value=2, value=1, key="pos_ym")
        if usar_spider_ind:
            pos_config["Spider de Inducao - Doca"] = st.number_input("Spider de Inducao - Doca", min_value=0, max_value=2, value=1, key="pos_spi")
        st.markdown("---")
        st.markdown("#### Restricoes")
        st.markdown("- Diaristas so podem: Spider Inducao, Unloader, Pick to Buffer")
        st.markdown("- Spider de Fechamento nunca vai pro Carregamento")
        if st.button("Gerar Escala Operacional", type="primary", use_container_width=True, key="btn_gerar_op"):
            escala_gerada = []
            pool_fixos = [f["nome"] for f in fixos]
            pool_diaristas = [f["nome"] for f in diaristas]
            posicoes_diarista = ["Spider de Inducao - Doca", "Unloader", "Pick to Buffer Esteira 1", "Pick to Buffer Esteira 2"]
            import random
            if usar_notas and desempenho_lista:
                notas_por_func = {}
                for d in desempenho_lista:
                    chave = d["funcionario"] + "|" + d["posicao"]
                    if chave not in notas_por_func:
                        notas_por_func[chave] = []
                    notas_por_func[chave].append(d["nota"])
                def media_nota(func, pos):
                    chave = func + "|" + pos
                    if chave in notas_por_func:
                        return sum(notas_por_func[chave]) / len(notas_por_func[chave])
                    return 0
            else:
                def media_nota(func, pos):
                    return 0
            usados = []
            for posicao, qtd in pos_config.items():
                for i in range(qtd):
                    if posicao in posicoes_diarista and pool_diaristas:
                        if usar_notas:
                            pool_diaristas.sort(key=lambda x: media_nota(x, posicao), reverse=True)
                        else:
                            random.shuffle(pool_diaristas)
                        escolhido = pool_diaristas.pop(0)
                        escala_gerada.append({"funcionario": escolhido, "posicao": posicao})
                        usados.append(escolhido)
                    elif pool_fixos:
                        candidatos = [f for f in pool_fixos if f not in usados]
                        if not candidatos:
                            candidatos = pool_fixos
                        if usar_notas:
                            candidatos.sort(key=lambda x: media_nota(x, posicao), reverse=True)
                        else:
                            random.shuffle(candidatos)
                        if candidatos:
                            escolhido = candidatos[0]
                            if escolhido in pool_fixos:
                                pool_fixos.remove(escolhido)
                            escala_gerada.append({"funcionario": escolhido, "posicao": posicao})
                            usados.append(escolhido)
                    elif pool_diaristas and posicao in posicoes_diarista:
                        escolhido = pool_diaristas.pop(0)
                        escala_gerada.append({"funcionario": escolhido, "posicao": posicao})
                        usados.append(escolhido)
            if escala_gerada:
                limpar_escalas_data(data_escala_str, "operacional")
                for eg in escala_gerada:
                    salvar_escala({"data": data_escala_str, "funcionario": eg["funcionario"], "posicao": eg["posicao"], "turno": "Noturno", "tipo_escala": "operacional", "gerado_em": agora_dt.strftime("%d/%m/%Y %H:%M")})
                st.markdown("<div class=\"success-box\">Escala gerada com " + str(len(escala_gerada)) + " alocacoes!</div>", unsafe_allow_html=True)
                st.rerun()
            else:
                st.error("Nao foi possivel gerar a escala. Verifique os funcionarios disponiveis.")
        esc_dia_op = [e for e in escalas if e.get("data","") == data_escala_str and e.get("tipo_escala","") == "operacional"]
        if esc_dia_op:
            st.markdown("---")
            st.markdown("#### Escala Atual (" + data_escala.strftime("%d/%m/%Y") + ")")
            df_esc = pd.DataFrame(esc_dia_op)
            cols_esc = ["funcionario", "posicao", "turno"]
            cols_ok = [c for c in cols_esc if c in df_esc.columns]
            st.dataframe(df_esc[cols_ok], use_container_width=True, hide_index=True)
            st.markdown("#### Editar Escala Manualmente")
            with st.form("form_edit_escala"):
                sel_esc_func = st.selectbox("Funcionario", [e["funcionario"] for e in esc_dia_op], key="sel_esc_edit")
                nova_pos = st.selectbox("Nova posicao", POSICOES, key="nova_pos_edit")
                btn_edit_esc = st.form_submit_button("Alterar posicao", use_container_width=True)
                if btn_edit_esc:
                    for e in esc_dia_op:
                        if e["funcionario"] == sel_esc_func:
                            execute("UPDATE escalas SET posicao=%s WHERE id=%s", (nova_pos, e["id"]))
                            break
                    st.rerun()
    with tab_car:
        st.markdown("#### Escala de Carregamento")
        data_car = st.date_input("Data", value=date.today(), key="dt_escala_car")
        data_car_str = data_car.strftime("%Y-%m-%d")
        data_ontem_str = (data_car - timedelta(days=1)).strftime("%Y-%m-%d")
        esc_ontem_car = [e for e in escalas if e.get("data","") == data_ontem_str and e.get("tipo_escala","") == "carregamento"]
        nomes_ontem = [e["funcionario"] for e in esc_ontem_car]
        abs_dia_car = [a["funcionario"] for a in absenteismo_lista if a.get("data","") == data_car_str]
        fixos_car = [f for f in funcionarios if f.get("status") == "Ativo" and f.get("tipo") == "Fixo" and f["nome"] not in abs_dia_car]
        esc_dia_op_car = [e for e in escalas if e.get("data","") == data_car_str and e.get("tipo_escala","") == "operacional"]
        nomes_spider = [e["funcionario"] for e in esc_dia_op_car if "Spider de Fechamento" in e.get("posicao","")]
        pool_car = [f["nome"] for f in fixos_car if f["nome"] not in nomes_spider and f["nome"] not in nomes_ontem]
        st.markdown("**Pool disponivel:** " + str(len(pool_car)) + " associados fixos")
        if nomes_ontem:
            st.markdown("<div class=\"warning-box\">Fizeram carregamento ontem (bloqueados): " + ", ".join(nomes_ontem) + "</div>", unsafe_allow_html=True)
        if nomes_spider:
            st.markdown("Spider de Fechamento (bloqueado): **" + ", ".join(nomes_spider) + "**")
        st.markdown("---")
        qtd_car = st.number_input("Quantidade para carregamento", min_value=1, max_value=10, value=4, key="qtd_car")
        xerife_options = ["Nenhum"] + pool_car
        xerife_sel = st.selectbox("Xerife", xerife_options, key="sel_xerife")
        if st.button("Gerar Escala de Carregamento", type="primary", use_container_width=True, key="btn_gerar_car"):
            import random
            random.shuffle(pool_car)
            selecionados = pool_car[:qtd_car]
            if selecionados:
                limpar_escalas_data(data_car_str, "carregamento")
                for s in selecionados:
                    salvar_escala({"data": data_car_str, "funcionario": s, "posicao": "Carregamento", "turno": "Noturno", "tipo_escala": "carregamento", "gerado_em": agora_dt.strftime("%d/%m/%Y %H:%M")})
                if xerife_sel != "Nenhum":
                    salvar_escala({"data": data_car_str, "funcionario": xerife_sel, "posicao": "Xerife", "turno": "Noturno", "tipo_escala": "carregamento", "gerado_em": agora_dt.strftime("%d/%m/%Y %H:%M")})
                st.markdown("<div class=\"success-box\">Escala de carregamento gerada!</div>", unsafe_allow_html=True)
                st.rerun()
            else:
                st.error("Nao ha associados disponiveis para carregamento.")
        esc_dia_car = [e for e in escalas if e.get("data","") == data_car_str and e.get("tipo_escala","") == "carregamento"]
        if esc_dia_car:
            st.markdown("---")
            st.markdown("#### Carregamento Atual (" + data_car.strftime("%d/%m/%Y") + ")")
            df_car = pd.DataFrame(esc_dia_car)
            cols_car = ["funcionario", "posicao"]
            cols_ok = [c for c in cols_car if c in df_car.columns]
            st.dataframe(df_car[cols_ok], use_container_width=True, hide_index=True)
    with tab_hist:
        st.markdown("#### Historico de Escalas")
        if escalas:
            df_all_esc = pd.DataFrame(escalas)
            cols_h = ["data", "funcionario", "posicao", "tipo_escala", "turno"]
            cols_ok = [c for c in cols_h if c in df_all_esc.columns]
            st.dataframe(df_all_esc[cols_ok], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma escala gerada ainda.")
elif menu == "Registro de Motorista":
    st.markdown("### Registro de Motorista")
    motoristas = carregar_motoristas()
    tab1, tab2, tab3 = st.tabs(["Registrar Chegada", "Importar Lista", "Historico"])
    with tab1:
        st.markdown("#### Filtro por Data")
        data_mot_filtro = st.date_input("Data", value=date.today(), key="dt_mot_filtro")
        data_mot_str = data_mot_filtro.strftime("%Y-%m-%d")
        mot_dia = [m for m in motoristas if m.get("data_chegada","")[:10] == data_mot_str]
        mot_importados = [m for m in mot_dia if m.get("importado", False)]
        mot_manuais = [m for m in mot_dia if not m.get("importado", False)]
        st.markdown("**" + str(len(mot_dia)) + " motoristas no dia** (" + str(len(mot_importados)) + " importados, " + str(len(mot_manuais)) + " manuais)")
        st.markdown("---")
        if mot_importados:
            st.markdown("#### Motoristas Importados (dar baixa)")
            mot_pendentes = [m for m in mot_importados if not m.get("horario_saida", "")]
            mot_concluidos = [m for m in mot_importados if m.get("horario_saida", "")]
            if mot_pendentes:
                st.markdown("**Pendentes:** " + str(len(mot_pendentes)))
                for mi in mot_pendentes:
                    with st.expander(mi["nome"] + " | " + mi.get("tipo_veiculo","") + " | " + mi.get("placa","")):
                        with st.form("form_baixa_" + str(mi["id"])):
                            bc1, bc2 = st.columns(2)
                            with bc1:
                                h_chegada = st.text_input("Horario Chegada", value=mi.get("horario_chegada",""), key="hc_" + str(mi["id"]))
                            with bc2:
                                h_saida = st.text_input("Horario Saida (HH:MM)", value=agora_dt.strftime("%H:%M"), key="hs_" + str(mi["id"]))
                            obs_mot = st.text_input("Observacao", value=mi.get("observacoes",""), key="obs_" + str(mi["id"]))
                            btn_baixa = st.form_submit_button("Dar Baixa", use_container_width=True)
                            if btn_baixa:
                                atualizar_motorista(mi["id"], {"horario_chegada": h_chegada, "horario_saida": h_saida, "observacoes": obs_mot})
                                st.rerun()
            if mot_concluidos:
                st.markdown("**Concluidos:** " + str(len(mot_concluidos)))
                df_conc = pd.DataFrame(mot_concluidos)
                cols_conc = ["nome", "placa", "tipo_veiculo", "horario_chegada", "horario_saida", "observacoes"]
                cols_ok = [c for c in cols_conc if c in df_conc.columns]
                st.dataframe(df_conc[cols_ok], use_container_width=True, hide_index=True)
        st.markdown("---")
        st.markdown("#### Registro Manual")
        with st.form("form_mot_manual"):
            mm1, mm2 = st.columns(2)
            with mm1:
                nome_mot = st.text_input("Nome do Motorista")
                placa_mot = st.text_input("Placa do Veiculo")
                tipo_veic = st.selectbox("Tipo de Veiculo", TIPOS_VEICULO, key="tipo_v_manual")
            with mm2:
                tel_mot = st.text_input("Telefone (opcional)")
                dest_mot = st.text_input("Destino / Rota")
                obs_mot_m = st.text_input("Observacao")
            hm1, hm2 = st.columns(2)
            with hm1:
                h_cheg_m = st.text_input("Horario Chegada (HH:MM)", value=agora_dt.strftime("%H:%M"), key="hcm")
            with hm2:
                h_said_m = st.text_input("Horario Saida (HH:MM, deixe vazio se ainda nao saiu)", value="", key="hsm")
            btn_mot_m = st.form_submit_button("Registrar", use_container_width=True)
            if btn_mot_m:
                if nome_mot:
                    salvar_motorista({"nome": nome_mot, "placa": placa_mot, "tipo_veiculo": tipo_veic, "telefone": tel_mot, "observacao": "", "horario_chegada": h_cheg_m, "horario_saida": h_said_m, "observacoes": obs_mot_m, "destino": dest_mot, "data_chegada": data_mot_str, "data_registro": agora_dt.strftime("%d/%m/%Y %H:%M"), "importado": False, "foto": ""})
                    st.markdown("<div class=\"success-box\">" + nome_mot + " registrado!</div>", unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.error("Informe o nome do motorista.")
    with tab2:
        st.markdown("#### Importar Motoristas em Massa")
        st.markdown("Envie um arquivo Excel (.xlsx) ou CSV com as colunas: **nome, placa, tipo_veiculo, telefone, destino**")
        data_imp_mot = st.date_input("Data de chegada dos motoristas", value=date.today(), key="dt_imp_mot")
        data_imp_str = data_imp_mot.strftime("%Y-%m-%d")
        arq_mot = st.file_uploader("Envie o arquivo", type=["xlsx", "csv"], key="up_mot")
        if arq_mot:
            try:
                if arq_mot.name.endswith(".csv"):
                    df_imp = pd.read_csv(arq_mot)
                else:
                    df_imp = pd.read_excel(arq_mot)
                st.session_state["df_mot_upload"] = df_imp
                cols_imp = ["nome", "placa", "tipo_veiculo", "telefone", "destino"]
                cols_ok = [c for c in cols_imp if c in df_imp.columns]
                st.dataframe(df_imp[cols_ok], use_container_width=True, hide_index=True)
            except Exception as ex:
                st.error("Erro ao ler arquivo: " + str(ex))
        if "df_mot_upload" in st.session_state and st.session_state["df_mot_upload"] is not None:
            df_imp_up = st.session_state["df_mot_upload"]
            if st.button("Importar Todos", type="primary", use_container_width=True, key="btn_imp_mot"):
                qtd_imp = 0
                for idx_row, row in df_imp_up.iterrows():
                    nome_r = str(row.get("nome", "")).strip()
                    if nome_r:
                        placa_r = str(row.get("placa", "")).strip()
                        tipo_r = str(row.get("tipo_veiculo", "")).strip()
                        tel_r = str(row.get("telefone", "")).strip()
                        dest_r = str(row.get("destino", "")).strip()
                        salvar_motorista({"nome": nome_r, "placa": placa_r, "tipo_veiculo": tipo_r, "telefone": tel_r, "observacao": "", "horario_chegada": "", "horario_saida": "", "observacoes": "", "destino": dest_r, "data_chegada": data_imp_str, "data_registro": agora_dt.strftime("%d/%m/%Y %H:%M"), "importado": True, "foto": ""})
                        qtd_imp += 1
                st.session_state["df_mot_upload"] = None
                st.markdown("<div class=\"success-box\">" + str(qtd_imp) + " motoristas importados!</div>", unsafe_allow_html=True)
                st.rerun()
        st.markdown("---")
        if st.button("Limpar Motoristas Importados", use_container_width=True, key="btn_limpar_imp"):
            limpar_motoristas_importados()
            st.markdown("<div class=\"warning-box\">Motoristas importados removidos!</div>", unsafe_allow_html=True)
            st.rerun()
    with tab3:
        st.markdown("#### Historico de Motoristas")
        data_hist_mot = st.date_input("Filtrar por data", value=date.today(), key="dt_hist_mot")
        data_hist_str = data_hist_mot.strftime("%Y-%m-%d")
        mot_hist = [m for m in motoristas if m.get("data_chegada","")[:10] == data_hist_str]
        if mot_hist:
            df_hist = pd.DataFrame(mot_hist)
            cols_hist = ["nome", "placa", "tipo_veiculo", "horario_chegada", "horario_saida", "destino", "observacoes", "importado"]
            cols_ok = [c for c in cols_hist if c in df_hist.columns]
            st.dataframe(df_hist[cols_ok], use_container_width=True, hide_index=True)
            st.markdown("**Total:** " + str(len(mot_hist)) + " motoristas")
            st.markdown("---")
            st.markdown("#### Editar Registro")
            nomes_mot_hist = [m["nome"] + " | " + m.get("placa","") for m in mot_hist]
            sel_mot_edit = st.selectbox("Selecione:", nomes_mot_hist, key="sel_mot_edit")
            idx_mot_sel = nomes_mot_hist.index(sel_mot_edit)
            mot_sel = mot_hist[idx_mot_sel]
            with st.form("form_edit_mot"):
                em1, em2 = st.columns(2)
                with em1:
                    edit_hc = st.text_input("Horario Chegada", value=mot_sel.get("horario_chegada",""))
                with em2:
                    edit_hs = st.text_input("Horario Saida", value=mot_sel.get("horario_saida",""))
                edit_obs_mot = st.text_input("Observacao", value=mot_sel.get("observacoes",""))
                em3, em4 = st.columns(2)
                with em3:
                    btn_salvar_mot = st.form_submit_button("Salvar", use_container_width=True)
                with em4:
                    btn_excluir_mot = st.form_submit_button("Excluir", use_container_width=True)
                if btn_salvar_mot:
                    execute("UPDATE motoristas SET horario_chegada=%s, horario_saida=%s, observacoes=%s WHERE id=%s", (edit_hc, edit_hs, edit_obs_mot, mot_sel["id"]))
                    st.rerun()
                if btn_excluir_mot:
                    execute("DELETE FROM motoristas WHERE id=%s", (mot_sel["id"],))
                    st.rerun()
        else:
            st.info("Nenhum motorista registrado nesta data.")
            
elif menu == "Absenteismo":
    st.markdown("### Registro de Absenteismo")
    funcionarios = carregar_funcionarios()
    absenteismo_lista = carregar_absenteismo()
    tab1, tab2, tab3 = st.tabs(["Registrar", "Importar Excel", "Historico / Editar"])
    with tab1:
        with st.form("form_abs"):
            nomes_f = [f["nome"] for f in funcionarios if f.get("status") == "Ativo"]
            func_abs = st.selectbox("Funcionario", nomes_f, key="sel_abs")
            data_abs = st.date_input("Data", value=date.today(), key="dt_abs")
            motivo_abs = st.selectbox("Motivo", ["Falta injustificada", "Atestado medico", "Atraso", "Ferias", "Folga", "Licenca", "Outro"])
            obs_abs = st.text_area("Observacoes", height=80, key="obs_abs")
            btn_abs = st.form_submit_button("Registrar", use_container_width=True)
            if btn_abs:
                salvar_absenteismo_reg({"funcionario": func_abs, "data": data_abs.strftime("%Y-%m-%d"), "motivo": motivo_abs, "observacoes": obs_abs, "registrado_em": agora_dt.strftime("%d/%m/%Y %H:%M")})
                st.markdown("<div class=\"success-box\">Absenteismo registrado!</div>", unsafe_allow_html=True)
                st.rerun()
    with tab2:
        st.markdown("#### Importar Absenteismo por Excel")
        st.markdown("Colunas: **funcionario, data** (DD/MM/YYYY), **motivo, observacoes**")
        arq_abs = st.file_uploader("Envie o arquivo", type=["xlsx", "csv"], key="up_abs")
        if arq_abs:
            try:
                if arq_abs.name.endswith(".csv"):
                    df_abs_imp = pd.read_csv(arq_abs)
                else:
                    df_abs_imp = pd.read_excel(arq_abs)
                st.dataframe(df_abs_imp, use_container_width=True, hide_index=True)
                if st.button("Importar Todos", type="primary", use_container_width=True, key="btn_imp_abs"):
                    qtd = 0
                    for idx_r, row in df_abs_imp.iterrows():
                        func_r = str(row.get("funcionario", "")).strip()
                        data_r = str(row.get("data", "")).strip()
                        motivo_r = str(row.get("motivo", "")).strip()
                        obs_r = str(row.get("observacoes", "")).strip()
                        if func_r and data_r:
                            try:
                                if "/" in data_r:
                                    dt_p = datetime.strptime(data_r, "%d/%m/%Y")
                                else:
                                    dt_p = datetime.strptime(data_r[:10], "%Y-%m-%d")
                                salvar_absenteismo_reg({"funcionario": func_r, "data": dt_p.strftime("%Y-%m-%d"), "motivo": motivo_r if motivo_r else "Outro", "observacoes": obs_r, "registrado_em": agora_dt.strftime("%d/%m/%Y %H:%M")})
                                qtd += 1
                            except Exception:
                                pass
                    st.markdown("<div class=\"success-box\">" + str(qtd) + " registros importados!</div>", unsafe_allow_html=True)
                    st.rerun()
            except Exception as ex:
                st.error("Erro ao ler arquivo: " + str(ex))
    with tab3:
        if absenteismo_lista:
            df_abs = pd.DataFrame(absenteismo_lista)
            cols_abs = ["funcionario", "data", "motivo", "observacoes", "registrado_em"]
            cols_ok = [c for c in cols_abs if c in df_abs.columns]
            st.dataframe(df_abs[cols_ok], use_container_width=True, hide_index=True)
            st.markdown("---")
            st.markdown("#### Editar / Excluir Registro")
            ids_abs = [str(a["id"]) + " - " + a["funcionario"] + " (" + a.get("data","") + ")" for a in absenteismo_lista]
            sel_abs_edit = st.selectbox("Selecione o registro:", ids_abs, key="sel_abs_edit")
            idx_abs_sel = ids_abs.index(sel_abs_edit)
            abs_sel = absenteismo_lista[idx_abs_sel]
            with st.form("form_edit_abs"):
                edit_motivo = st.text_input("Motivo", value=abs_sel.get("motivo",""))
                edit_obs = st.text_input("Observacoes", value=abs_sel.get("observacoes",""))
                ea1, ea2 = st.columns(2)
                with ea1:
                    btn_salvar_abs = st.form_submit_button("Salvar", use_container_width=True)
                with ea2:
                    btn_excluir_abs = st.form_submit_button("Excluir", use_container_width=True)
                if btn_salvar_abs:
                    execute("UPDATE absenteismo SET motivo=%s, observacoes=%s WHERE id=%s", (edit_motivo, edit_obs, abs_sel["id"]))
                    st.rerun()
                if btn_excluir_abs:
                    execute("DELETE FROM absenteismo WHERE id=%s", (abs_sel["id"],))
                    st.rerun()
        else:
            st.info("Nenhum registro de absenteismo.")

elif menu == "Desempenho por Funcao":
    st.markdown("### Avaliacao de Desempenho por Funcao")
    funcionarios = carregar_funcionarios()
    desempenho_lista = carregar_desempenho()
    tab1, tab2, tab3 = st.tabs(["Avaliar", "Importar Excel", "Historico / Editar"])
    with tab1:
        with st.form("form_desemp"):
            nomes_f = [f["nome"] for f in funcionarios if f.get("status") == "Ativo"]
            func_desemp = st.selectbox("Funcionario", nomes_f, key="sel_desemp")
            pos_desemp = st.selectbox("Posicao Avaliada", POSICOES, key="pos_desemp")
            nota_desemp = st.slider("Nota (1 a 5)", min_value=1, max_value=5, value=3, key="nota_desemp")
            data_desemp = st.date_input("Data da Avaliacao", value=date.today(), key="dt_desemp")
            obs_desemp = st.text_area("Observacoes", height=80, key="obs_desemp")
            btn_desemp = st.form_submit_button("Registrar Avaliacao", use_container_width=True)
            if btn_desemp:
                salvar_desempenho_reg({"funcionario": func_desemp, "posicao": pos_desemp, "nota": nota_desemp, "data_avaliacao": data_desemp.strftime("%Y-%m-%d"), "observacoes": obs_desemp, "registrado_em": agora_dt.strftime("%d/%m/%Y %H:%M")})
                st.markdown("<div class=\"success-box\">Avaliacao registrada!</div>", unsafe_allow_html=True)
                st.rerun()
    with tab2:
        st.markdown("#### Importar Avaliacoes por Excel")
        st.markdown("Colunas: **funcionario, posicao, nota** (1-5), **data** (DD/MM/YYYY), **observacoes**")
        arq_desemp = st.file_uploader("Envie o arquivo", type=["xlsx", "csv"], key="up_desemp")
        if arq_desemp:
            try:
                if arq_desemp.name.endswith(".csv"):
                    df_d_imp = pd.read_csv(arq_desemp)
                else:
                    df_d_imp = pd.read_excel(arq_desemp)
                st.dataframe(df_d_imp, use_container_width=True, hide_index=True)
                if st.button("Importar Todos", type="primary", use_container_width=True, key="btn_imp_desemp"):
                    qtd = 0
                    for idx_r, row in df_d_imp.iterrows():
                        func_r = str(row.get("funcionario", "")).strip()
                        pos_r = str(row.get("posicao", "")).strip()
                        nota_r = int(row.get("nota", 3))
                        data_r = str(row.get("data", "")).strip()
                        obs_r = str(row.get("observacoes", "")).strip()
                        if func_r and pos_r:
                            try:
                                if "/" in data_r:
                                    dt_p = datetime.strptime(data_r, "%d/%m/%Y")
                                else:
                                    dt_p = datetime.strptime(data_r[:10], "%Y-%m-%d")
                                data_final = dt_p.strftime("%Y-%m-%d")
                            except Exception:
                                data_final = hoje_str
                            salvar_desempenho_reg({"funcionario": func_r, "posicao": pos_r, "nota": nota_r, "data_avaliacao": data_final, "observacoes": obs_r, "registrado_em": agora_dt.strftime("%d/%m/%Y %H:%M")})
                            qtd += 1
                    st.markdown("<div class=\"success-box\">" + str(qtd) + " avaliacoes importadas!</div>", unsafe_allow_html=True)
                    st.rerun()
            except Exception as ex:
                st.error("Erro ao ler arquivo: " + str(ex))
    with tab3:
        if desempenho_lista:
            df_desemp = pd.DataFrame(desempenho_lista)
            cols_d = ["funcionario", "posicao", "nota", "data_avaliacao", "observacoes"]
            cols_ok = [c for c in cols_d if c in df_desemp.columns]
            st.dataframe(df_desemp[cols_ok], use_container_width=True, hide_index=True)
            st.markdown("---")
            st.markdown("#### Editar / Excluir Registro")
            ids_d = [str(d["id"]) + " - " + d["funcionario"] + " | " + d.get("posicao","") + " (" + str(d.get("nota","")) + ")" for d in desempenho_lista]
            sel_d_edit = st.selectbox("Selecione:", ids_d, key="sel_d_edit")
            idx_d_sel = ids_d.index(sel_d_edit)
            d_sel = desempenho_lista[idx_d_sel]
            with st.form("form_edit_desemp"):
                edit_nota = st.number_input("Nota", min_value=1, max_value=5, value=int(d_sel.get("nota", 3)), key="edit_nota_d")
                edit_obs_d = st.text_input("Observacoes", value=d_sel.get("observacoes",""), key="edit_obs_d")
                ed1, ed2 = st.columns(2)
                with ed1:
                    btn_salvar_d = st.form_submit_button("Salvar", use_container_width=True)
                with ed2:
                    btn_excluir_d = st.form_submit_button("Excluir", use_container_width=True)
                if btn_salvar_d:
                    execute("UPDATE desempenho SET nota=%s, observacoes=%s WHERE id=%s", (edit_nota, edit_obs_d, d_sel["id"]))
                    st.rerun()
                if btn_excluir_d:
                    execute("DELETE FROM desempenho WHERE id=%s", (d_sel["id"],))
                    st.rerun()
        else:
            st.info("Nenhuma avaliacao registrada.")

elif menu == "Forecast / Volume":
    st.markdown("### Forecast / Volume Previsto")
    forecasts = carregar_forecast()
    tab1, tab2, tab3 = st.tabs(["Registrar", "Importar Excel", "Historico / Editar"])
    with tab1:
        with st.form("form_forecast"):
            data_fc = st.date_input("Data", value=date.today(), key="dt_fc")
            volume_fc = st.number_input("Volume Previsto (pacotes)", min_value=0, max_value=200000, value=0, step=100, key="vol_fc")
            obs_fc = st.text_area("Observacoes", height=80, key="obs_fc")
            btn_fc = st.form_submit_button("Salvar Forecast", use_container_width=True)
            if btn_fc:
                if volume_fc > 0:
                    salvar_forecast_reg({"data": data_fc.strftime("%Y-%m-%d"), "volume": volume_fc, "observacoes": obs_fc, "registrado_em": agora_dt.strftime("%d/%m/%Y %H:%M")})
                    st.markdown("<div class=\"success-box\">Forecast salvo!</div>", unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.error("Informe um volume maior que zero.")
    with tab2:
        st.markdown("#### Importar Forecast por Excel")
        st.markdown("Colunas: **data** (DD/MM/YYYY ou YYYY-MM-DD), **volume** (numero inteiro), **observacoes** (opcional)")
        arq_fc = st.file_uploader("Envie o arquivo", type=["xlsx", "csv"], key="up_fc")
        if arq_fc:
            try:
                if arq_fc.name.endswith(".csv"):
                    df_fc_imp = pd.read_csv(arq_fc)
                else:
                    df_fc_imp = pd.read_excel(arq_fc)
                st.dataframe(df_fc_imp, use_container_width=True, hide_index=True)
                if st.button("Importar Todos", type="primary", use_container_width=True, key="btn_imp_fc"):
                    qtd_fc = 0
                    for idx_r, row_fc in df_fc_imp.iterrows():
                        data_val = str(row_fc.get("data", "")).strip()
                        vol_val = row_fc.get("volume", 0)
                        obs_val = str(row_fc.get("observacoes", "")).strip()
                        if data_val and vol_val:
                            try:
                                if "/" in data_val:
                                    dt_parsed = datetime.strptime(data_val, "%d/%m/%Y")
                                else:
                                    dt_parsed = datetime.strptime(data_val[:10], "%Y-%m-%d")
                                data_final = dt_parsed.strftime("%Y-%m-%d")
                                salvar_forecast_reg({"data": data_final, "volume": int(vol_val), "observacoes": obs_val if obs_val else "Importado via Excel", "registrado_em": agora_dt.strftime("%d/%m/%Y %H:%M")})
                                qtd_fc += 1
                            except Exception:
                                pass
                    st.markdown("<div class=\"success-box\">" + str(qtd_fc) + " registros importados!</div>", unsafe_allow_html=True)
                    st.rerun()
            except Exception as ex:
                st.error("Erro ao ler arquivo: " + str(ex))
    with tab3:
        if forecasts:
            df_fc_h = pd.DataFrame(forecasts)
            cols_fc = ["data", "volume", "observacoes", "registrado_em"]
            cols_ok = [c for c in cols_fc if c in df_fc_h.columns]
            st.dataframe(df_fc_h[cols_ok], use_container_width=True, hide_index=True)
            st.markdown("---")
            st.markdown("#### Editar / Excluir Registro")
            ids_fc = [str(f["id"]) + " - " + f.get("data","") + " | " + str(f.get("volume","")) + " pacotes" for f in forecasts]
            sel_fc_edit = st.selectbox("Selecione:", ids_fc, key="sel_fc_edit")
            idx_fc_sel = ids_fc.index(sel_fc_edit)
            fc_sel = forecasts[idx_fc_sel]
            with st.form("form_edit_fc"):
                edit_vol = st.number_input("Volume", min_value=0, max_value=200000, value=int(fc_sel.get("volume", 0)), step=100, key="edit_vol_fc")
                edit_obs_fc = st.text_input("Observacoes", value=fc_sel.get("observacoes",""), key="edit_obs_fc")
                ef1, ef2 = st.columns(2)
                with ef1:
                    btn_salvar_fc = st.form_submit_button("Salvar", use_container_width=True)
                with ef2:
                    btn_excluir_fc = st.form_submit_button("Excluir", use_container_width=True)
                if btn_salvar_fc:
                    execute("UPDATE forecast SET volume=%s, observacoes=%s WHERE id=%s", (edit_vol, edit_obs_fc, fc_sel["id"]))
                    st.rerun()
                if btn_excluir_fc:
                    execute("DELETE FROM forecast WHERE id=%s", (fc_sel["id"],))
                    st.rerun()
        else:
            st.info("Nenhum forecast registrado.")

elif menu == "Validacao por Foto (IA)":
    st.markdown("### Validacao por Foto")
    st.markdown("Registre contagens de pacotes/pallets manualmente.")
    validacoes = carregar_validacoes()
    tab1, tab2 = st.tabs(["Nova Validacao", "Historico / Editar"])
    with tab1:
        with st.form("form_valid"):
            tipo_valid = st.selectbox("Tipo de Validacao", ["Contagem de Pacotes", "Contagem de Pallets", "Verificacao de Carga", "Outro"])
            total_manual = st.number_input("Contagem Manual (total)", min_value=0, max_value=50000, value=0, step=1, key="cnt_manual")
            obs_valid = st.text_area("Observacoes", height=80, key="obs_valid")
            btn_valid = st.form_submit_button("Registrar Validacao", use_container_width=True)
            if btn_valid:
                salvar_validacao({"tipo": tipo_valid, "data": hoje_str, "total_objetos_ia": 0, "contagem_ia": {}, "total_objetos_manual": total_manual, "contagem_manual": {"total": total_manual, "obs": obs_valid}, "foto": ""})
                st.markdown("<div class=\"success-box\">Validacao registrada!</div>", unsafe_allow_html=True)
                st.rerun()
    with tab2:
        if validacoes:
            df_val = pd.DataFrame(validacoes)
            cols_val = ["tipo", "data", "total_objetos_manual"]
            cols_ok = [c for c in cols_val if c in df_val.columns]
            st.dataframe(df_val[cols_ok], use_container_width=True, hide_index=True)
            st.markdown("---")
            st.markdown("#### Excluir Registro")
            ids_val = [str(v["id"]) + " - " + v.get("tipo","") + " (" + v.get("data","") + ") - " + str(v.get("total_objetos_manual","")) for v in validacoes]
            sel_val_edit = st.selectbox("Selecione:", ids_val, key="sel_val_edit")
            idx_val_sel = ids_val.index(sel_val_edit)
            val_sel = validacoes[idx_val_sel]
            if st.button("Excluir Validacao", use_container_width=True, key="btn_exc_val"):
                execute("DELETE FROM validacoes WHERE id=%s", (val_sel["id"],))
                st.rerun()
        else:
            st.info("Nenhuma validacao registrada.")

elif menu == "Scanner QR/Barcode":
    st.markdown("### Scanner QR / Barcode")
    site_scanner = st.selectbox("Site destino:", ["EUA8", "ELP8", "ESA8"], key="site_scan")
    if "lista_scan" not in st.session_state:
        st.session_state["lista_scan"] = []
    with st.form("form_scan"):
        codigo_scan = st.text_input("Digite ou escaneie o codigo")
        btn_add = st.form_submit_button("Adicionar", use_container_width=True)
        if btn_add and codigo_scan:
            st.session_state["lista_scan"].append({"codigo": codigo_scan, "site": site_scanner, "hora": agora_dt.strftime("%H:%M")})
            st.rerun()
    if st.session_state["lista_scan"]:
        st.markdown("---")
        lista_site = [x for x in st.session_state["lista_scan"] if x["site"] == site_scanner]
        st.markdown("**" + site_scanner + " (" + str(len(lista_site)) + " codigos):**")
        for i, item in enumerate(lista_site):
            st.markdown(str(i+1) + ". " + item["codigo"] + " - " + item["hora"])
        st.markdown("---")
        st.markdown("**Resumo geral:**")
        for s in ["EUA8", "ELP8", "ESA8"]:
            qtd_s = len([x for x in st.session_state["lista_scan"] if x["site"] == s])
            if qtd_s > 0:
                st.markdown("- " + s + ": " + str(qtd_s) + " codigos")
        st.markdown("---")
        texto_wpp = "*Lista Scanner - " + hoje_str + "*" + chr(10) + chr(10)
        for s in ["EUA8", "ELP8", "ESA8"]:
            itens_s = [x for x in st.session_state["lista_scan"] if x["site"] == s]
            if itens_s:
                texto_wpp += "*" + s + " (" + str(len(itens_s)) + "):*" + chr(10)
                for idx_s, it in enumerate(itens_s):
                    texto_wpp += str(idx_s+1) + ". " + it["codigo"] + " - " + it["hora"] + chr(10)
                texto_wpp += chr(10)
        import urllib.parse
        link_wpp = "https://wa.me/?text=" + urllib.parse.quote(texto_wpp)
        st.markdown("[Enviar por WhatsApp](" + link_wpp + ")")

        st.markdown("[Enviar por WhatsApp](" + link_wpp + ")")
        c_limpar1, c_limpar2 = st.columns(2)
        with c_limpar1:
            if st.button("Limpar lista", use_container_width=True):
                st.session_state["lista_scan"] = []
                st.rerun()
    else:
        st.info("Nenhum codigo escaneado ainda.")

elif menu == "Enviar por WhatsApp":
    st.markdown("### Enviar Informacoes por WhatsApp")
    import urllib.parse
    opcao_wpp = st.selectbox("O que deseja enviar?", ["Escala do Dia", "Motoristas do Dia", "Resumo Dashboard"])
    numeros_wpp = st.text_input("Numeros (separados por virgula, com DDD)", placeholder="11999999999, 11988888888")
    if st.button("Gerar Link WhatsApp", type="primary", use_container_width=True, key="btn_wpp"):
        if opcao_wpp == "Escala do Dia":
            escalas = carregar_escalas()
            esc_hoje = [e for e in escalas if e.get("data","") == hoje_str]
            if esc_hoje:
                texto_wpp = "ESCALA " + SITE + " - " + agora_dt.strftime("%d/%m/%Y") + chr(10) + chr(10)
                for e in esc_hoje:
                    texto_wpp += e["funcionario"] + " - " + e["posicao"] + chr(10)
            else:
                texto_wpp = "Nenhuma escala gerada para hoje."
        elif opcao_wpp == "Motoristas do Dia":
            motoristas = carregar_motoristas()
            mot_hoje = [m for m in motoristas if m.get("data_chegada","")[:10] == hoje_str]
            texto_wpp = "MOTORISTAS " + SITE + " - " + agora_dt.strftime("%d/%m/%Y") + chr(10) + chr(10)
            texto_wpp += "Total: " + str(len(mot_hoje)) + chr(10) + chr(10)
            for m in mot_hoje:
                texto_wpp += m["nome"] + " | " + m.get("placa","") + " | " + m.get("horario_chegada","") + " - " + m.get("horario_saida","pendente") + chr(10)
        else:
            texto_wpp = "RESUMO " + SITE + " - " + agora_dt.strftime("%d/%m/%Y %H:%M") + chr(10)
            texto_wpp += "Previsao: " + get_config_valor("previsao_" + hoje_str, "0") + " pacotes" + chr(10)
            texto_wpp += "Processados: " + get_config_valor("processados_" + hoje_str, "0") + " pacotes" + chr(10)
        texto_encoded = urllib.parse.quote(texto_wpp)
        if numeros_wpp.strip():
            for num in numeros_wpp.split(","):
                num_limpo = num.strip().replace("-","").replace(" ","")
                link_wpp = "https://wa.me/55" + num_limpo + "?text=" + texto_encoded
                st.markdown("[Enviar para " + num_limpo + "](" + link_wpp + ")")
        else:
            link_wpp = "https://wa.me/?text=" + texto_encoded
            st.markdown("[Abrir WhatsApp](" + link_wpp + ")")

elif menu == "Relatorios":
    st.markdown("### Relatorios")
    funcionarios = carregar_funcionarios()
    motoristas = carregar_motoristas()
    escalas = carregar_escalas()
    absenteismo_lista = carregar_absenteismo()
    forecasts = carregar_forecast()
    tab1, tab2, tab3 = st.tabs(["Resumo Geral", "Por Periodo", "Exportar"])
    with tab1:
        st.markdown("#### Resumo do Dia (" + agora_dt.strftime("%d/%m/%Y") + ")")
        ativos = [f for f in funcionarios if f.get("status") == "Ativo"]
        mot_hoje = [m for m in motoristas if m.get("data_chegada","")[:10] == hoje_str]
        esc_hoje = [e for e in escalas if e.get("data","") == hoje_str]
        abs_hoje = [a for a in absenteismo_lista if a.get("data","") == hoje_str]
        rc1, rc2, rc3, rc4 = st.columns(4)
        with rc1:
            st.metric("Funcionarios Ativos", len(ativos))
        with rc2:
            st.metric("Motoristas Hoje", len(mot_hoje))
        with rc3:
            st.metric("Escala Gerada", len(esc_hoje))
        with rc4:
            st.metric("Ausentes Hoje", len(abs_hoje))
        prev_valor = int(get_config_valor("previsao_" + hoje_str, "0"))
        proc_valor = int(get_config_valor("processados_" + hoje_str, "0"))
        st.markdown("---")
        rp1, rp2 = st.columns(2)
        with rp1:
            st.metric("Previsao do Dia", str(prev_valor) + " pacotes")
        with rp2:
            st.metric("Processados", str(proc_valor) + " pacotes")
    with tab2:
        st.markdown("#### Filtrar por Periodo")
        rp1, rp2 = st.columns(2)
        with rp1:
            dt_inicio = st.date_input("De", value=date.today() - timedelta(days=7), key="dt_rel_ini")
        with rp2:
            dt_fim = st.date_input("Ate", value=date.today(), key="dt_rel_fim")
        dt_ini_str = dt_inicio.strftime("%Y-%m-%d")
        dt_fim_str = dt_fim.strftime("%Y-%m-%d")
        mot_periodo = [m for m in motoristas if dt_ini_str <= m.get("data_chegada","")[:10] <= dt_fim_str]
        abs_periodo = [a for a in absenteismo_lista if dt_ini_str <= a.get("data","") <= dt_fim_str]
        esc_periodo = [e for e in escalas if dt_ini_str <= e.get("data","") <= dt_fim_str]
        st.markdown("**Motoristas no periodo:** " + str(len(mot_periodo)))
        st.markdown("**Absenteismo no periodo:** " + str(len(abs_periodo)))
        st.markdown("**Escalas no periodo:** " + str(len(esc_periodo)))
        if mot_periodo:
            st.markdown("---")
            df_mot_rel = pd.DataFrame(mot_periodo)
            cols_r = ["nome", "placa", "tipo_veiculo", "data_chegada", "horario_chegada", "horario_saida"]
            cols_ok = [c for c in cols_r if c in df_mot_rel.columns]
            st.dataframe(df_mot_rel[cols_ok], use_container_width=True, hide_index=True)
    with tab3:
        st.markdown("#### Exportar Dados")
        tipo_export = st.selectbox("O que exportar?", ["Motoristas", "Escalas", "Absenteismo", "Forecast", "Funcionarios"])
        if st.button("Gerar CSV", type="primary", use_container_width=True, key="btn_export"):
            if tipo_export == "Motoristas":
                df_exp = pd.DataFrame(motoristas)
            elif tipo_export == "Escalas":
                df_exp = pd.DataFrame(escalas)
            elif tipo_export == "Absenteismo":
                df_exp = pd.DataFrame(absenteismo_lista)
            elif tipo_export == "Forecast":
                df_exp = pd.DataFrame(forecasts)
            else:
                df_exp = pd.DataFrame(funcionarios)
            if not df_exp.empty:
                csv_data = df_exp.to_csv(index=False)
                st.download_button("Baixar CSV", data=csv_data, file_name=tipo_export.lower() + "_" + hoje_str + ".csv", mime="text/csv")
            else:
                st.info("Nenhum dado para exportar.")

elif menu == "Configurações":
    st.markdown("### Configuracoes")
    tab1, tab2 = st.tabs(["Geral", "Meta CPT"])
    with tab1:
        st.markdown("#### Configuracoes Gerais")
        with st.form("form_config"):
            novo_site = st.text_input("Nome do Site", value=get_config_valor("site_nome", SITE))
            novo_turno = st.selectbox("Turno Padrao", ["Noturno", "Diurno", "Misto"], index=["Noturno", "Diurno", "Misto"].index(get_config_valor("turno_padrao", "Noturno")) if get_config_valor("turno_padrao", "Noturno") in ["Noturno", "Diurno", "Misto"] else 0)
            btn_config = st.form_submit_button("Salvar", use_container_width=True)
            if btn_config:
                salvar_config("site_nome", novo_site)
                salvar_config("turno_padrao", novo_turno)
                st.markdown("<div class=\"success-box\">Configuracoes salvas!</div>", unsafe_allow_html=True)
                st.rerun()
    with tab2:
        st.markdown("#### Meta CPT (Horario Limite)")
        with st.form("form_cpt_config"):
            cpt_h = st.number_input("Hora CPT", min_value=0, max_value=23, value=int(get_config_valor("cpt_hora", str(CPT_HORA))), key="cpt_h_cfg")
            cpt_m = st.number_input("Minuto CPT", min_value=0, max_value=59, value=int(get_config_valor("cpt_minuto", str(CPT_MINUTO))), key="cpt_m_cfg")
            btn_cpt = st.form_submit_button("Salvar Meta CPT", use_container_width=True)
            if btn_cpt:
                salvar_config("cpt_hora", str(cpt_h))
                salvar_config("cpt_minuto", str(cpt_m))
                st.markdown("<div class=\"success-box\">Meta CPT atualizada para " + str(cpt_h).zfill(2) + ":" + str(cpt_m).zfill(2) + "!</div>", unsafe_allow_html=True)
                st.rerun()
        st.markdown("**Meta atual:** " + str(int(get_config_valor("cpt_hora", str(CPT_HORA)))).zfill(2) + ":" + str(int(get_config_valor("cpt_minuto", str(CPT_MINUTO)))).zfill(2))

elif menu == "Gerenciar Usuários":
    st.markdown("### Gerenciar Usuarios")
    usuarios_lista = carregar_usuarios()
    tab1, tab2 = st.tabs(["Criar Usuario", "Lista / Editar"])
    with tab1:
        with st.form("form_novo_user"):
            nu1, nu2 = st.columns(2)
            with nu1:
                novo_user = st.text_input("Usuario (login)")
                nova_senha = st.text_input("Senha", type="password")
            with nu2:
                novo_nome = st.text_input("Nome Completo")
                novo_perfil = st.selectbox("Perfil", ["admin", "operador", "equipe"])
            btn_novo_user = st.form_submit_button("Criar Usuario", use_container_width=True)
            if btn_novo_user:
                if novo_user and nova_senha and novo_nome:
                    hash_senha = gerar_hash(nova_senha)
                    execute("INSERT INTO usuarios (usuario, senha, nome, perfil, status) VALUES (%s,%s,%s,%s,%s)", (novo_user, hash_senha, novo_nome, novo_perfil, "Ativo"))
                    st.markdown("<div class=\"success-box\">Usuario " + novo_user + " criado!</div>", unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.error("Preencha todos os campos.")
    with tab2:
        if usuarios_lista:
            df_users = pd.DataFrame(usuarios_lista)
            cols_u = ["usuario", "nome", "perfil", "status"]
            cols_ok = [c for c in cols_u if c in df_users.columns]
            st.dataframe(df_users[cols_ok], use_container_width=True, hide_index=True)
            st.markdown("---")
            st.markdown("#### Editar / Excluir")
            nomes_u = [u["usuario"] for u in usuarios_lista]
            sel_user = st.selectbox("Selecione:", nomes_u, key="sel_user_edit")
            idx_u = nomes_u.index(sel_user)
            user_sel = usuarios_lista[idx_u]
            with st.form("form_edit_user"):
                eu1, eu2 = st.columns(2)
                with eu1:
                    edit_perfil_u = st.selectbox("Perfil", ["admin", "operador", "equipe"], index=["admin", "operador", "equipe"].index(user_sel.get("perfil","operador")) if user_sel.get("perfil","operador") in ["admin", "operador", "equipe"] else 1)
                with eu2:
                    edit_status_u = st.selectbox("Status", ["Ativo", "Inativo"], index=["Ativo", "Inativo"].index(user_sel.get("status","Ativo")) if user_sel.get("status","Ativo") in ["Ativo", "Inativo"] else 0)
                nova_senha_u = st.text_input("Nova Senha (deixe vazio para manter)", type="password", key="nova_senha_edit")
                bu1, bu2 = st.columns(2)
                with bu1:
                    btn_salvar_u = st.form_submit_button("Salvar", use_container_width=True)
                with bu2:
                    btn_excluir_u = st.form_submit_button("Excluir", use_container_width=True)
                if btn_salvar_u:
                    dados_u = {"perfil": edit_perfil_u, "status": edit_status_u}
                    if nova_senha_u:
                        dados_u["senha"] = gerar_hash(nova_senha_u)
                    atualizar_usuario(user_sel["id"], dados_u)
                    st.markdown("<div class=\"success-box\">Usuario atualizado!</div>", unsafe_allow_html=True)
                    st.rerun()
                if btn_excluir_u:
                    execute("DELETE FROM usuarios WHERE id=%s", (user_sel["id"],))
                    st.markdown("<div class=\"warning-box\">Usuario excluido!</div>", unsafe_allow_html=True)
                    st.rerun()
        else:
            st.info("Nenhum usuario cadastrado.")

st.markdown("---")
rodape = "<div style=\"text-align:center; padding:20px 0;\"><p style=\"color:#666; font-size:11px;\">" + SITE + " Manager | First Mile Operations | Amazon Logistics</p></div>"
st.markdown(rodape, unsafe_allow_html=True)

