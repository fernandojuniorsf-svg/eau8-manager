
import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import io
import hashlib
import random
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from PIL import Image

FUSO_BR = ZoneInfo("America/Sao_Paulo")
NL = chr(10)
SITE = "EUA" + "8"

for p in ["dados_" + SITE.lower(), "fotos_validacao", "fotos_motoristas"]:
    if not os.path.exists(p):
        os.makedirs(p)

PASTA_DADOS = "dados_" + SITE.lower()
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

POSICOES = ["Receive", "Stow", "Pick", "Pack", "Depart", "Problem Solve", "Scanning", "Induc", "Rebag", "Water Spider", "Lider"]
TIPOS_VEICULO = ["Carreta (28 pallets)", "Truck (16 pallets)", "VUC (6 pallets)", "Van", "Outro"]
TIPOS_VALIDACAO = ["Veiculo Carregado", "Pallet Montado", "Area de Stow", "Area de Receive", "Depart", "Outro"]
SENHA_PADRAO = SITE.lower()


def cifrar_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def primeiro(lista):
    for item in lista:
        return item
    return None


def carregar_json(arq):
    if os.path.exists(arq):
        with open(arq, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salvar_json(arq, dados):
    with open(arq, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def carregar_usuarios():
    u = carregar_json(ARQ_USUARIOS)
    if not u:
        admin = {"usuario": "fernando", "senha": cifrar_senha(SENHA_PADRAO), "nome": "Fernando Junior", "perfil": "Admin", "status": "Ativo", "criado_em": "2026-05-03"}
        salvar_json(ARQ_USUARIOS, [admin])
        return [admin]
    return u

def salvar_usuarios(u):
    salvar_json(ARQ_USUARIOS, u)

def carregar_funcionarios():
    return carregar_json(ARQ_FUNCIONARIOS)

def salvar_funcionarios(d):
    salvar_json(ARQ_FUNCIONARIOS, d)

def carregar_escalas():
    return carregar_json(ARQ_ESCALAS)

def salvar_escalas(d):
    salvar_json(ARQ_ESCALAS, d)

def carregar_motoristas():
    return carregar_json(ARQ_MOTORISTAS)

def salvar_motoristas(d):
    salvar_json(ARQ_MOTORISTAS, d)

def carregar_forecast():
    return carregar_json(ARQ_FORECAST)

def salvar_forecast(d):
    salvar_json(ARQ_FORECAST, d)

def carregar_validacoes():
    return carregar_json(ARQ_VALIDACOES)

def salvar_validacoes(d):
    salvar_json(ARQ_VALIDACOES, d)

def carregar_absenteismo():
    return carregar_json(ARQ_ABSENTEISMO)

def salvar_absenteismo(d):
    salvar_json(ARQ_ABSENTEISMO, d)

def carregar_desempenho():
    return carregar_json(ARQ_DESEMPENHO)

def salvar_desempenho(d):
    salvar_json(ARQ_DESEMPENHO, d)


PERFIS_ACESSO = {
    "Admin": ["Dashboard", "Cadastro de Funcionarios", "Gerador de Escala", "Registro de Motorista", "Absenteismo", "Desempenho por Funcao", "Forecast / Volume", "Validacao por Foto (IA)", "Scanner QR/Barcode", "Enviar por WhatsApp", "Relatorios", "Configuracoes", "Gerenciar Usuarios"],
    "Supervisor": ["Dashboard", "Cadastro de Funcionarios", "Gerador de Escala", "Registro de Motorista", "Absenteismo", "Desempenho por Funcao", "Forecast / Volume", "Validacao por Foto (IA)", "Scanner QR/Barcode", "Enviar por WhatsApp", "Relatorios"],
    "Operador": ["Dashboard", "Registro de Motorista", "Validacao por Foto (IA)", "Scanner QR/Barcode"],
    "Visualizador": ["Dashboard", "Relatorios"]
}

st.set_page_config(page_title=SITE + " Manager", page_icon="F", layout="wide")

css_texto = "<style>"
css_texto += ".stApp {background-color: #1a1a1a !important;}"
css_texto += 'section[data-testid="stSidebar"] {background-color: #2d2d2d !important;}'
css_texto += 'section[data-testid="stSidebar"] * {color: #e0e0e0 !important;}'
css_texto += 'section[data-testid="stSidebar"] h2 {color: #FF9900 !important;}'
css_texto += 'section[data-testid="stSidebar"] .stRadio label span {color: #e0e0e0 !important;}'
css_texto += 'section[data-testid="stSidebar"] .stRadio label:hover span {color: #FF9900 !important;}'
css_texto += 'section[data-testid="stSidebar"] button {border: 2px solid #FF9900 !important; color: #FF9900 !important; background: transparent !important; border-radius: 10px !important; padding: 12px 32px !important;}'
css_texto += 'section[data-testid="stSidebar"] button:hover {background-color: #FF9900 !important; color: #000 !important;}'
css_texto += "h1 {color: #FF9900 !important;}"
css_texto += "h2 {color: #FF9900 !important;}"
css_texto += "h3 {color: #FF9900 !important;}"
css_texto += "h4 {color: #FF9900 !important;}"
css_texto += "h5 {color: #cccccc !important;}"
css_texto += ".stMarkdown p {color: #e0e0e0 !important;}"
css_texto += ".stMarkdown li {color: #e0e0e0 !important;}"
css_texto += ".stMarkdown strong {color: #ffffff !important;}"
css_texto += ".stMarkdown em {color: #cccccc !important;}"
css_texto += ".stMarkdown code {color: #FF9900 !important; background-color: #333 !important;}"
css_texto += ".stMetricValue {color: #FF9900 !important; font-weight: 700 !important;}"
css_texto += 'div[data-testid="stMetricDelta"] {color: #00C853 !important;}'
css_texto += 'div[data-testid="stMetricLabel"] p {color: #cccccc !important;}'
css_texto += 'div[data-testid="stMetric"] {background-color: #2d2d2d !important; border-left: 4px solid #FF9900; border-radius: 10px; padding: 16px; box-shadow: 0 3px 8px rgba(0,0,0,0.3);}'
css_texto += '.stTabs [data-baseweb="tab-list"] {background-color: #2d2d2d; border-radius: 10px 10px 0 0;}'
css_texto += '.stTabs [data-baseweb="tab"] {color: #cccccc !important; font-weight: 500; padding: 12px 24px !important;}'
css_texto += '.stTabs [aria-selected="true"] {background-color: #FF9900 !important; color: #000 !important; border-radius: 10px 10px 0 0; font-weight: 700;}'
css_texto += '.stButton>button {background-color: #FF9900 !important; color: #000 !important; border: none !important; border-radius: 10px !important; padding: 16px 48px !important; font-weight: 600 !important; font-size: 16px !important; box-shadow: 0 3px 8px rgba(255,153,0,0.4) !important; letter-spacing: 0.5px !important; margin-top: 8px !important; margin-bottom: 8px !important;}'
css_texto += '.stButton>button:hover {background-color: #e68a00 !important; box-shadow: 0 6px 16px rgba(255,153,0,0.5) !important; transform: translateY(-2px);}'
css_texto += '.stButton>button[kind="secondary"] {border: 2px solid #FF9900 !important; color: #FF9900 !important; background: transparent !important; padding: 16px 48px !important;}'
css_texto += '.stButton>button[kind="secondary"]:hover {background-color: #FF9900 !important; color: #000 !important;}'
css_texto += 'div[data-testid="stForm"] {background-color: #2d2d2d !important; border: 1px solid #444; border-radius: 12px; padding: 24px; box-shadow: 0 3px 10px rgba(0,0,0,0.25);}'
css_texto += 'div[data-testid="stForm"] * {color: #e0e0e0;}'
css_texto += ".stSelectbox label, .stTextInput label, .stNumberInput label, .stDateInput label, .stMultiSelect label, .stSlider label, .stTextArea label, .stFileUploader label, .stCameraInput label {color: #cccccc !important; font-weight: 500 !important;}"
css_texto += 'input {background-color: #3a3a3a !important; color: #e0e0e0 !important; border: 1px solid #555 !important; border-radius: 8px !important;}'
css_texto += 'textarea {background-color: #3a3a3a !important; color: #e0e0e0 !important; border: 1px solid #555 !important; border-radius: 8px !important;}'
css_texto += '[data-baseweb="select"] {background-color: #3a3a3a !important;}'
css_texto += '[data-baseweb="select"] * {color: #e0e0e0 !important;}'
css_texto += ".stDataFrame {border-radius: 8px;}"
css_texto += "hr {border-color: #FF9900 !important; opacity: 0.4;}"
css_texto += '[data-testid="stHeader"] {background-color: #1a1a1a !important;}'
css_texto += ".stAlert {border-radius: 8px !important;}"
css_texto += '[data-testid="stNotification"] {border-radius: 8px !important;}'
css_texto += ".stDownloadButton>button {background-color: #FF9900 !important; color: #000 !important; border: none !important; border-radius: 10px !important; padding: 14px 40px !important; font-weight: 600 !important; box-shadow: 0 3px 8px rgba(255,153,0,0.4) !important;}"
css_texto += ".stDownloadButton>button:hover {background-color: #e68a00 !important; box-shadow: 0 6px 14px rgba(255,153,0,0.5) !important;}"
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
st.sidebar.markdown("*First Mile Operations | Amazon Logistics*")
st.sidebar.markdown("Bem-vindo, **" + nome_logado + "** (" + perfil_logado + ")")
st.sidebar.markdown("---")
menus_permitidos = PERFIS_ACESSO.get(perfil_logado, [])
todos_menus = ["Dashboard", "Cadastro de Funcionarios", "Gerador de Escala", "Registro de Motorista", "Absenteismo", "Desempenho por Funcao", "Forecast / Volume", "Validacao por Foto (IA)", "Scanner QR/Barcode", "Enviar por WhatsApp", "Relatorios", "Configuracoes", "Gerenciar Usuarios"]
menus_visiveis = [m for m in todos_menus if m in menus_permitidos]
menu = st.sidebar.radio("Menu Principal", menus_visiveis)
st.sidebar.markdown("---")
agora = datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M")
st.sidebar.markdown("Data: **" + agora + "**")
st.sidebar.markdown("Site: **" + SITE + "**")
st.sidebar.markdown("Turno: **Tarde (14h-20h)**")
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
        obj_ia_h = sum(v.get("total_objetos_ia", v.get("total_objetos", 0)) for v in val_hoje)
        obj_eq_h = sum(v.get("total_objetos_manual", 0) for v in val_hoje)
        st.metric("Objetos Validados", "IA: " + str(obj_ia_h) + " | Eq: " + str(obj_eq_h))
    with c7:
        st.metric("Faltas Hoje", len(abs_hoje))
    st.markdown("---")
    st.markdown("### Graficos")
    tg1, tg2, tg3, tg4, tg5 = st.tabs(["Validacoes", "Forecast", "Motoristas", "Absenteismo", "Equipe"])
    with tg1:
        d7, ia7, eq7 = [], [], []
        for i in range(6, -1, -1):
            dd = (datetime.now(FUSO_BR) - timedelta(days=i)).strftime("%Y-%m-%d")
            dl = (datetime.now(FUSO_BR) - timedelta(days=i)).strftime("%d/%m")
            d7.append(dl)
            vd = [v for v in validacoes if v.get("data", "")[:10] == dd]
            ia7.append(sum(v.get("total_objetos_ia", v.get("total_objetos", 0)) for v in vd))
            eq7.append(sum(v.get("total_objetos_manual", 0) for v in vd))
        dfv7 = pd.DataFrame({"Data": d7, "IA": ia7, "Equipe": eq7})
        st.dataframe(dfv7, use_container_width=True, hide_index=True)
        st.bar_chart(dfv7.set_index("Data"))
    with tg2:
        dfc7, vfc7 = [], []
        for i in range(6, -1, -1):
            dd = (datetime.now(FUSO_BR) - timedelta(days=i)).strftime("%Y-%m-%d")
            dl = (datetime.now(FUSO_BR) - timedelta(days=i)).strftime("%d/%m")
            dfc7.append(dl)
            fd = [f for f in forecasts if f.get("data", "") == dd]
            vfc7.append(primeiro(fd).get("volume", 0) if fd else 0)
        dff7 = pd.DataFrame({"Data": dfc7, "Volume": vfc7})
        st.dataframe(dff7, use_container_width=True, hide_index=True)
        st.line_chart(dff7.set_index("Data"))
    with tg3:
        dm7, qm7 = [], []
        for i in range(6, -1, -1):
            dd = (datetime.now(FUSO_BR) - timedelta(days=i)).strftime("%Y-%m-%d")
            dl = (datetime.now(FUSO_BR) - timedelta(days=i)).strftime("%d/%m")
            dm7.append(dl)
            md = [m for m in motoristas if m.get("data_chegada", "")[:10] == dd or m.get("data_registro", "")[:10] == dd]
            qm7.append(len(md))
        dfm7 = pd.DataFrame({"Data": dm7, "Motoristas": qm7})
        st.dataframe(dfm7, use_container_width=True, hide_index=True)
        st.bar_chart(dfm7.set_index("Data"))
    with tg4:
        dab7, qab7 = [], []
        for i in range(6, -1, -1):
            dd = (datetime.now(FUSO_BR) - timedelta(days=i)).strftime("%Y-%m-%d")
            dl = (datetime.now(FUSO_BR) - timedelta(days=i)).strftime("%d/%m")
            dab7.append(dl)
            abd = [a for a in absenteismo if a.get("data", "") == dd]
            qab7.append(len(abd))
        dfab7 = pd.DataFrame({"Data": dab7, "Faltas": qab7})
        st.dataframe(dfab7, use_container_width=True, hide_index=True)
        st.bar_chart(dfab7.set_index("Data"))
    with tg5:
        if funcionarios:
            pt, pst = {}, {}
            for f in funcionarios:
                t = f.get("tipo", "Outro")
                s = f.get("status", "Ativo")
                pt[t] = pt.get(t, 0) + 1
                pst[s] = pst.get(s, 0) + 1
            ce1, ce2 = st.columns(2)
            with ce1:
                st.markdown("**Por Tipo:**")
                dft = pd.DataFrame(list(pt.items()), columns=["Tipo", "Qtd"])
                st.dataframe(dft, use_container_width=True, hide_index=True)
                st.bar_chart(dft.set_index("Tipo"))
            with ce2:
                st.markdown("**Por Status:**")
                dfss = pd.DataFrame(list(pst.items()), columns=["Status", "Qtd"])
                st.dataframe(dfss, use_container_width=True, hide_index=True)
                st.bar_chart(dfss.set_index("Status"))
        else:
            st.info("Cadastre funcionarios.")
    st.markdown("---")
    st.markdown("### Ultimas Atividades")
    ca1, ca2 = st.columns(2)
    with ca1:
        st.markdown("#### Ultimas Validacoes")
        if validacoes:
            uv = sorted(validacoes, key=lambda x: x.get("data", ""), reverse=True)[:5]
            for v in uv:
                tia = v.get("total_objetos_ia", v.get("total_objetos", 0))
                teq = v.get("total_objetos_manual", 0)
                st.markdown("- **" + v.get("tipo", "") + "** " + v.get("data", "")[:16] + " | IA:" + str(tia) + " Eq:" + str(teq))
        else:
            st.info("Nenhuma validacao.")
    with ca2:
        st.markdown("#### Ultimos Motoristas")
        if motoristas:
            umot = sorted(motoristas, key=lambda x: x.get("data_chegada", x.get("data_registro", "")), reverse=True)[:5]
            for m in umot:
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
                    nv = {"nome": nome, "tipo": tipo, "telefone": telefone, "qualidades": qualidades, "status": status_func, "observacoes": obs_func, "cadastrado_em": datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M")}
                    funcionarios.append(nv)
                    salvar_funcionarios(funcionarios)
                    st.success(nome + " cadastrado!")
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
                    funcionarios[idx_f]["nome"] = en
                    funcionarios[idx_f]["tipo"] = et
                    funcionarios[idx_f]["telefone"] = etel
                    funcionarios[idx_f]["qualidades"] = eq
                    funcionarios[idx_f]["status"] = es
                    funcionarios[idx_f]["observacoes"] = eo
                    salvar_funcionarios(funcionarios)
                    st.success("Atualizado!")
                    st.rerun()
                if bef:
                    funcionarios.pop(idx_f)
                    salvar_funcionarios(funcionarios)
                    st.success("Excluido!")
                    st.rerun()
        else:
            st.info("Nenhum funcionario cadastrado.")


elif menu == "Gerador de Escala":
    st.markdown("### Gerador de Escala")
    funcionarios = carregar_funcionarios()
    absenteismo = carregar_absenteismo()
    desempenho = carregar_desempenho()
    ativos = [f for f in funcionarios if f.get("status") == "Ativo"]
    tab1, tab2 = st.tabs(["Gerar Escala", "Anteriores / Editar"])
    with tab1:
        ge1, ge2, ge3 = st.columns(3)
        with ge1:
            data_escala = st.date_input("Data", value=date.today() + timedelta(days=1), key="dt_esc")
        with ge2:
            turno_escala = st.selectbox("Turno", ["Tarde (14h-20h)"])
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
            st.info("TPH: " + str(tph) + " | Turno: " + str(horas_turno) + "h | " + str(volume_prev) + " / (" + str(tph) + " x " + str(horas_turno) + ") = **" + str(pessoas_necessarias) + " pessoas**")
            if len(disponiveis) < pessoas_necessarias:
                st.warning("ALERTA: Disponiveis: " + str(len(disponiveis)) + " | Necessarios: " + str(pessoas_necessarias) + " - Faltam " + str(pessoas_necessarias - len(disponiveis)) + "!")
            if len(disponiveis) >= pessoas_necessarias:
                st.success("HC suficiente! Disponiveis: " + str(len(disponiveis)) + " | Necessarios: " + str(pessoas_necessarias))


        usar_desemp = st.checkbox("Priorizar por nota de desempenho (mais recente)", value=False)
        if st.button("Sortear / Gerar Escala", type="primary", use_container_width=True):
            escala = []
            usados = []
            for pos in POSICOES:
                cands = [f for f in disponiveis if f["nome"] not in usados]
                if not cands:
                    continue
                nota_map = {}
                if usar_desemp and desempenho:
                    for c in cands:
                        notas_p = [d for d in desempenho if d.get("funcionario") == c["nome"] and d.get("posicao") == pos]
                        notas_p.sort(key=lambda x: x.get("data_avaliacao", "2000-01-01")[:10], reverse=True)
                        nota_map[c["nome"]] = notas_p[0].get("nota", 0) if notas_p else 0
                    cands.sort(key=lambda x: nota_map.get(x["nome"], 0), reverse=True)
                if not usar_desemp or not desempenho:
                    random.shuffle(cands)
                escolhido = cands[0]
                ei = {"posicao": pos, "funcionario": escolhido["nome"], "telefone": escolhido.get("telefone", ""), "tipo": escolhido.get("tipo", ""), "nota": nota_map.get(escolhido["nome"], 0)}
                escala.append(ei)
                usados.append(escolhido["nome"])
            st.session_state["escala_temp"] = escala


        if "escala_temp" in st.session_state and st.session_state["escala_temp"]:
            esc = st.session_state["escala_temp"]
            st.markdown("---")
            st.markdown("#### Escala Gerada (editavel antes de salvar)")
            ndisp = [f["nome"] for f in disponiveis]
            df_esc = pd.DataFrame(esc)
            df_ed = st.data_editor(df_esc, use_container_width=True, hide_index=True, num_rows="dynamic", column_config={"posicao": st.column_config.SelectboxColumn("Posicao", options=POSICOES), "funcionario": st.column_config.SelectboxColumn("Funcionario", options=ndisp)}, key="ed_esc")
            cs1, cs2, cs3 = st.columns(3)
            with cs1:
                if st.button("Salvar Escala", type="primary", use_container_width=True):
                    ne = {"data": data_esc_str, "turno": turno_escala, "volume": volume_prev, "escala": df_ed.to_dict("records"), "gerada_em": datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M"), "gerada_por": st.session_state.get("nome_logado", "Admin")}
                    escalas = carregar_escalas()
                    escalas.append(ne)
                    salvar_escalas(escalas)
                    tw = "*ESCALA " + SITE + " - " + data_esc_str + "*" + NL
                    tw += "Turno: " + turno_escala + NL
                    tw += "Volume: " + str(volume_prev) + NL + NL
                    for it in df_ed.to_dict("records"):
                        tw += it.get("posicao", "") + ": " + it.get("funcionario", "") + NL
                    tw += NL + "Bora, time!"
                    st.session_state["ultima_escala_wpp"] = tw
                    st.session_state["escala_temp"] = None
                    st.success("Escala salva!")
                    st.rerun()
            with cs2:
                if st.button("Sortear Novamente", use_container_width=True):
                    st.session_state["escala_temp"] = None
                    st.rerun()
            with cs3:
                if st.button("Limpar", use_container_width=True):
                    st.session_state["escala_temp"] = None
                    st.rerun()
    with tab2:
        escalas = carregar_escalas()
        if escalas:
            es_s = sorted(escalas, key=lambda x: x.get("data", ""), reverse=True)
            ops = [e["data"] + " - " + e["turno"] + " - Vol:" + str(e.get("volume", "")) for e in es_s]
            sel_e = st.selectbox("Selecione", ops, key="sel_esc_h")
            idx_e = ops.index(sel_e)
            esel = es_s[idx_e]
            st.markdown("**Data:** " + esel["data"] + " | **Turno:** " + esel["turno"] + " | **Volume:** " + str(esel.get("volume", "")))
            st.markdown("**Gerada em:** " + esel.get("gerada_em", "") + " | **Por:** " + esel.get("gerada_por", ""))
            df_e_h = pd.DataFrame(esel.get("escala", []))
            st.dataframe(df_e_h, use_container_width=True, hide_index=True)
            if st.button("Excluir Escala Selecionada", type="secondary"):
                todas = carregar_escalas()
                todas = [x for x in todas if not (x.get("data") == esel.get("data") and x.get("gerada_em") == esel.get("gerada_em"))]
                salvar_escalas(todas)
                st.success("Escala excluida!")
                st.rerun()
        else:
            st.info("Nenhuma escala gerada.")


elif menu == "Registro de Motorista":
    st.markdown("### Registro de Motorista")
    motoristas = carregar_motoristas()
    tab1, tab2 = st.tabs(["Novo Registro", "Historico / Editar"])
    with tab1:
        with st.form("form_mot"):
            rm1, rm2 = st.columns(2)
            with rm1:
                nome_mot = st.text_input("Nome do Motorista")
                placa_mot = st.text_input("Placa do Veiculo", placeholder="ABC1D23")
                tel_mot = st.text_input("Telefone do Motorista", placeholder="11999999999")
                tipo_veic = st.selectbox("Tipo de Veiculo", TIPOS_VEICULO)
            with rm2:
                h_chegada = st.text_input("Horario Chegada (HH:MM)", placeholder="14:30")
                h_saida = st.text_input("Horario Saida (HH:MM)", placeholder="16:00")
                obs_mot = st.text_input("Observacoes", placeholder="Ex: 28 pallets, doca 3")
            foto_mot = st.camera_input("Foto do Veiculo (opcional)")
            btn_mot = st.form_submit_button("Registrar", use_container_width=True)
            if btn_mot:
                if nome_mot and placa_mot:
                    nm = {"nome": nome_mot, "placa": placa_mot.upper(), "telefone": tel_mot, "tipo_veiculo": tipo_veic,"horario_chegada": h_chegada, "horario_saida": h_saida, "observacoes": obs_mot, "data_chegada": datetime.now(FUSO_BR).strftime("%Y-%m-%d"), "data_registro": datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M")}
                    if foto_mot:
                        nf = "mot_" + datetime.now(FUSO_BR).strftime("%Y%m%d_%H%M%S") + ".jpg"
                        cf = os.path.join(PASTA_MOTORISTAS, nf)
                        img_m = Image.open(foto_mot)
                        img_m.save(cf)
                        nm["foto"] = nf
                    motoristas.append(nm)
                    salvar_motoristas(motoristas)
                    st.success(nome_mot + " registrado!")
                    st.rerun()
                else:
                    st.error("Preencha nome e placa!")
    with tab2:
        if motoristas:
            df_mot = pd.DataFrame(motoristas)
            cols_m = ["nome", "placa", "tipo_veiculo", "horario_chegada", "horario_saida", "data_chegada", "observacoes"]
            cols_ok = [c for c in cols_m if c in df_mot.columns]
            st.dataframe(df_mot[cols_ok], use_container_width=True, hide_index=True)
            st.markdown("---")
            st.markdown("#### Editar Motorista")
            ops_m = [m.get("nome", "") + " - " + m.get("placa", "") + " - " + m.get("data_chegada", "")[:10] for m in motoristas]
            sel_m = st.selectbox("Selecione", ops_m, key="sel_m_edit")
            idx_m = ops_m.index(sel_m)
            me = motoristas[idx_m]
            with st.form("form_edit_mot"):
                em1, em2 = st.columns(2)
                with em1:
                    enm = st.text_input("Nome", value=me.get("nome", ""))
                    epm = st.text_input("Placa", value=me.get("placa", ""))
                    etv = st.selectbox("Tipo Veiculo", TIPOS_VEICULO, index=TIPOS_VEICULO.index(me.get("tipo_veiculo", "Outro")) if me.get("tipo_veiculo", "Outro") in TIPOS_VEICULO else 4)
                with em2:
                    ehc = st.text_input("Hora Chegada", value=me.get("horario_chegada", ""))
                    ehs = st.text_input("Hora Saida", value=me.get("horario_saida", ""))
                    eom = st.text_input("Obs", value=me.get("observacoes", ""))
                csm, cem = st.columns(2)
                with csm:
                    bsm = st.form_submit_button("Salvar Alteracoes", use_container_width=True)
                with cem:
                    bem = st.form_submit_button("Excluir Registro", use_container_width=True)
                if bsm:
                    motoristas[idx_m]["nome"] = enm
                    motoristas[idx_m]["placa"] = epm.upper()
                    motoristas[idx_m]["tipo_veiculo"] = etv
                    motoristas[idx_m]["horario_chegada"] = ehc
                    motoristas[idx_m]["horario_saida"] = ehs
                    motoristas[idx_m]["observacoes"] = eom
                    salvar_motoristas(motoristas)
                    st.success("Atualizado!")
                    st.rerun()
                if bem:
                    motoristas.pop(idx_m)
                    salvar_motoristas(motoristas)
                    st.success("Excluido!")
                    st.rerun()
        else:
            st.info("Nenhum motorista registrado.")
elif menu == "Absenteismo":
    st.markdown("### Registro de Absenteismo")
    funcionarios = carregar_funcionarios()
    absenteismo = carregar_absenteismo()
    ativos = [f for f in funcionarios if f.get("status") == "Ativo"]
    tab1, tab2 = st.tabs(["Registrar Falta", "Historico / Editar"])
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
                    nabs = {"funcionario": func_abs, "data": data_abs.strftime("%Y-%m-%d"), "motivo": motivo_abs, "observacoes": obs_abs, "registrado_em": datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M"), "registrado_por": st.session_state.get("nome_logado", "Admin")}
                    absenteismo.append(nabs)
                    salvar_absenteismo(absenteismo)
                    st.success("Falta registrada para " + func_abs)
                    st.rerun()
                else:
                    st.error("Selecione um funcionario!")
    with tab2:
        if absenteismo:
            df_abs = pd.DataFrame(absenteismo)
            cols_abs = ["funcionario", "data", "motivo", "observacoes", "registrado_em"]
            cols_ok = [c for c in cols_abs if c in df_abs.columns]
            st.dataframe(df_abs[cols_ok], use_container_width=True, hide_index=True)
            st.markdown("---")
            st.markdown("#### Editar / Excluir")
            ops_abs = [a.get("funcionario", "") + " - " + a.get("data", "") + " - " + a.get("motivo", "") for a in absenteismo]
            sel_abs = st.selectbox("Selecione", ops_abs, key="sel_abs_ed")
            idx_abs = ops_abs.index(sel_abs)
            ae = absenteismo[idx_abs]
            motivos_list = ["Falta sem Justificativa", "Falta Justificada", "Atestado Medico", "Atraso", "Saiu mais cedo", "Outro"]
            mi = motivos_list.index(ae.get("motivo", "Outro")) if ae.get("motivo", "Outro") in motivos_list else 5
            with st.form("form_edit_abs"):
                ea1, ea2 = st.columns(2)
                with ea1:
                    eaf = st.text_input("Funcionario", value=ae.get("funcionario", ""))
                    ead = st.text_input("Data (AAAA-MM-DD)", value=ae.get("data", ""))
                with ea2:
                    eam = st.selectbox("Motivo", motivos_list, index=mi)
                    eao = st.text_input("Obs", value=ae.get("observacoes", ""))
                cab, dab = st.columns(2)
                with cab:
                    bsa = st.form_submit_button("Salvar Alteracoes", use_container_width=True)
                with dab:
                    bea = st.form_submit_button("Excluir Registro", use_container_width=True)
                if bsa:
                    absenteismo[idx_abs]["funcionario"] = eaf
                    absenteismo[idx_abs]["data"] = ead
                    absenteismo[idx_abs]["motivo"] = eam
                    absenteismo[idx_abs]["observacoes"] = eao
                    salvar_absenteismo(absenteismo)
                    st.success("Atualizado!")
                    st.rerun()
                if bea:
                    absenteismo.pop(idx_abs)
                    salvar_absenteismo(absenteismo)
                    st.success("Excluido!")
                    st.rerun()
        else:
            st.info("Nenhuma falta registrada.")


elif menu == "Desempenho por Funcao":
    st.markdown("### Desempenho por Funcao")
    funcionarios = carregar_funcionarios()
    desempenho = carregar_desempenho()
    ativos = [f for f in funcionarios if f.get("status") == "Ativo"]
    tab1, tab2 = st.tabs(["Nova Avaliacao", "Historico / Editar"])
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
                    nd = {"funcionario": func_desemp, "posicao": pos_desemp, "nota": nota_desemp, "data_avaliacao": data_desemp.strftime("%Y-%m-%d"), "observacoes": obs_desemp, "registrado_em": datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M"), "registrado_por": st.session_state.get("nome_logado", "Admin")}
                    desempenho.append(nd)
                    salvar_desempenho(desempenho)
                    st.success("Avaliacao registrada!")
                    st.rerun()
                else:
                    st.error("Selecione um funcionario!")
    with tab2:
        if desempenho:
            df_desemp = pd.DataFrame(desempenho)
            cols_d = ["funcionario", "posicao", "nota", "data_avaliacao", "observacoes"]
            cols_ok = [c for c in cols_d if c in df_desemp.columns]
            st.dataframe(df_desemp[cols_ok], use_container_width=True, hide_index=True)
            st.markdown("---")
            st.markdown("#### Editar / Excluir")
            ops_d = [d.get("funcionario", "") + " - " + d.get("posicao", "") + " - " + d.get("data_avaliacao", "") + " - Nota:" + str(d.get("nota", "")) for d in desempenho]
            sel_d = st.selectbox("Selecione", ops_d, key="sel_desemp_ed")
            idx_d = ops_d.index(sel_d)
            de = desempenho[idx_d]
            with st.form("form_edit_desemp"):
                ed1, ed2 = st.columns(2)
                with ed1:
                    edf = st.text_input("Funcionario", value=de.get("funcionario", ""))
                    edp = st.selectbox("Posicao", POSICOES, index=POSICOES.index(de.get("posicao", "Receive")) if de.get("posicao", "Receive") in POSICOES else 0)
                with ed2:
                    edn = st.slider("Nota", min_value=1, max_value=10, value=de.get("nota", 5))
                    edo = st.text_area("Obs", value=de.get("observacoes", ""))
                csd, ced = st.columns(2)
                with csd:
                    bsd = st.form_submit_button("Salvar Alteracoes", use_container_width=True)
                with ced:
                    bed = st.form_submit_button("Excluir Registro", use_container_width=True)
                if bsd:
                    desempenho[idx_d]["funcionario"] = edf
                    desempenho[idx_d]["posicao"] = edp
                    desempenho[idx_d]["nota"] = edn
                    desempenho[idx_d]["observacoes"] = edo
                    salvar_desempenho(desempenho)
                    st.success("Atualizado!")
                    st.rerun()
                if bed:
                    desempenho.pop(idx_d)
                    salvar_desempenho(desempenho)
                    st.success("Excluido!")
                    st.rerun()
        else:
            st.info("Nenhuma avaliacao registrada.")


elif menu == "Forecast / Volume":
    st.markdown("### Forecast / Volume")
    forecasts = carregar_forecast()
    tab1, tab2 = st.tabs(["Registrar Manual", "Historico / Editar"])
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
                nfc = {"data": data_fc.strftime("%Y-%m-%d"), "volume": volume_fc, "observacoes": obs_fc, "registrado_em": datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M"), "registrado_por": st.session_state.get("nome_logado", "Admin")}
                forecasts.append(nfc)
                salvar_forecast(forecasts)
                st.success("Forecast salvo!")
                st.rerun()
        st.markdown("---")
        st.markdown("#### Upload de Forecast (CSV/Excel)")
        arq_up = st.file_uploader("Envie um arquivo com colunas: data, volume", type=["csv", "xlsx"])
        if arq_up:
            try:
                if arq_up.name.endswith(".csv"):
                    df_up = pd.read_csv(arq_up)
                else:
                    df_up = pd.read_excel(arq_up)
                st.dataframe(df_up, use_container_width=True, hide_index=True)
                if st.button("Importar Forecast", type="primary"):
                    for idx_row, row in df_up.iterrows():
                        nfc = {"data": str(row.get("data", "")), "volume": int(row.get("volume", 0)), "observacoes": "Upload", "registrado_em": datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M"), "registrado_por": st.session_state.get("nome_logado", "Admin")}
                        forecasts.append(nfc)
                    salvar_forecast(forecasts)
                    st.success(str(len(df_up)) + " registros importados!")
                    st.rerun()
            except Exception as ex:
                st.error("Erro ao ler arquivo: " + str(ex))
    with tab2:
        if forecasts:
            df_fc = pd.DataFrame(forecasts)
            cols_fc = ["data", "volume", "observacoes", "registrado_em"]
            cols_ok = [c for c in cols_fc if c in df_fc.columns]
            st.dataframe(df_fc[cols_ok], use_container_width=True, hide_index=True)
            st.markdown("---")
            st.markdown("#### Editar / Excluir")
            ops_fc = [f.get("data", "") + " - Vol:" + str(f.get("volume", "")) for f in forecasts]
            sel_fc = st.selectbox("Selecione", ops_fc, key="sel_fc_ed")
            idx_fc = ops_fc.index(sel_fc)
            fce = forecasts[idx_fc]
            with st.form("form_edit_fc"):
                efc1, efc2 = st.columns(2)
                with efc1:
                    efcd = st.text_input("Data (AAAA-MM-DD)", value=fce.get("data", ""))
                    efcv = st.number_input("Volume", min_value=0, max_value=100000, value=fce.get("volume", 0), step=100)
                with efc2:
                    efco = st.text_input("Obs", value=fce.get("observacoes", ""))
                csfc, cefc = st.columns(2)
                with csfc:
                    bsfc = st.form_submit_button("Salvar Alteracoes", use_container_width=True)
                with cefc:
                    befc = st.form_submit_button("Excluir Registro", use_container_width=True)
                if bsfc:
                    forecasts[idx_fc]["data"] = efcd
                    forecasts[idx_fc]["volume"] = efcv
                    forecasts[idx_fc]["observacoes"] = efco
                    salvar_forecast(forecasts)
                    st.success("Atualizado!")
                    st.rerun()
                if befc:
                    forecasts.pop(idx_fc)
                    salvar_forecast(forecasts)
                    st.success("Excluido!")
                    st.rerun()
        else:
            st.info("Nenhum forecast registrado.")


elif menu == "Validacao por Foto (IA)":
    st.markdown("### Validacao por Foto (IA)")
    validacoes = carregar_validacoes()
    tab1, tab2 = st.tabs(["Nova Validacao", "Historico / Editar"])
    with tab1:
        tipo_val = st.selectbox("Tipo de Validacao", TIPOS_VALIDACAO)
        foto_val = st.camera_input("Tire a foto para validacao")
        if foto_val:
            image = Image.open(foto_val)
            st.image(image, caption="Foto capturada", use_container_width=True)
            contagem_ia = {}
            total_ia = 0
            img_resultado = None
            if yolo_ok:
                import tempfile
                temp_path = os.path.join(tempfile.gettempdir(), "foto_val.jpg")
                image.save(temp_path)
                modelo = YOLO("yolov8n.pt")
                resultados = modelo(temp_path, conf=0.15)
                primeiro_res = resultados[0] if resultados else None
                if primeiro_res is not None:
                    for box in primeiro_res.boxes:
                        cls_id = int(box.cls)
                        nome_obj = modelo.names.get(cls_id, "desconhecido")
                        contagem_ia[nome_obj] = contagem_ia.get(nome_obj, 0) + 1
                    total_ia = sum(contagem_ia.values())
                    try:
                        img_resultado = primeiro_res.plot()
                        st.image(img_resultado, caption="Deteccao IA - " + str(total_ia) + " objetos", use_container_width=True)
                    except Exception:
                        st.info("Nao foi possivel exibir imagem com deteccoes.")
                st.success("IA detectou: " + str(total_ia) + " objetos")
                if contagem_ia:
                    df_ia = pd.DataFrame(list(contagem_ia.items()), columns=["Objeto", "Quantidade"])
                    st.dataframe(df_ia, use_container_width=True, hide_index=True)
            else:
                st.warning("YOLO nao instalado. Modo demonstracao ativo.")
                st.info("Para IA real, rode: pip install ultralytics")
            st.markdown("---")
            st.markdown("#### Contagem Manual da Equipe")
            st.markdown("Informe a contagem feita manualmente pela equipe:")
            contagem_manual = {}
            objetos_manual = st.text_input("Objetos (ex: caixa, pallet, saco)", placeholder="caixa, pallet")
            if objetos_manual:
                lista_obj = [x.strip() for x in objetos_manual.split(",") if x.strip()]
                for obj in lista_obj:
                    qtd = st.number_input("Qtd de " + obj, min_value=0, max_value=9999, value=0, step=1, key="man_" + obj)
                    contagem_manual[obj] = qtd
            total_manual = sum(contagem_manual.values())
            st.markdown("---")
            st.markdown("#### Comparativo IA x Equipe")
            todos_obj = sorted(set(list(contagem_ia.keys()) + list(contagem_manual.keys())))
            if todos_obj:
                linhas_comp = []
                for obj in todos_obj:
                    qia = contagem_ia.get(obj, 0)
                    qeq = contagem_manual.get(obj, 0)
                    dif = qeq - qia
                    linhas_comp.append({"Objeto": obj, "IA": qia, "Equipe": qeq, "Diferenca": dif})
                linhas_comp.append({"Objeto": "TOTAL", "IA": total_ia, "Equipe": total_manual, "Diferenca": total_manual - total_ia})
                df_comp = pd.DataFrame(linhas_comp)
                st.dataframe(df_comp, use_container_width=True, hide_index=True)
            if st.button("Salvar Validacao", type="primary", use_container_width=True):
                nv = {"tipo": tipo_val, "data": datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M"), "total_objetos_ia": total_ia, "contagem_ia": contagem_ia, "total_objetos_manual": total_manual, "contagem_manual": contagem_manual, "registrado_por": st.session_state.get("nome_logado", "Admin")}
                nf = "val_" + datetime.now(FUSO_BR).strftime("%Y%m%d_%H%M%S") + ".jpg"
                cf = os.path.join(PASTA_FOTOS, nf)
                image.save(cf)
                nv["foto"] = nf
                validacoes.append(nv)
                salvar_validacoes(validacoes)
                st.success("Validacao salva! IA:" + str(total_ia) + " | Equipe:" + str(total_manual))
                st.rerun()
    with tab2:
        if validacoes:
            st.markdown("#### Ultimas Validacoes")
            for v in sorted(validacoes, key=lambda x: x.get("data", ""), reverse=True)[:10]:
                tia = v.get("total_objetos_ia", v.get("total_objetos", 0))
                teq = v.get("total_objetos_manual", 0)
                st.markdown("- **" + v.get("tipo", "") + "** - " + v.get("data", "")[:16] + " - IA: " + str(tia) + " | Equipe: " + str(teq))
            st.markdown("---")
            st.markdown("#### Editar / Excluir")
            ops_v = [v.get("tipo", "") + " - " + v.get("data", "")[:16] + " - IA:" + str(v.get("total_objetos_ia", v.get("total_objetos", 0))) for v in validacoes]
            sel_v = st.selectbox("Selecione", ops_v, key="sel_val_ed")
            idx_v = ops_v.index(sel_v)
            ve = validacoes[idx_v]
            with st.form("form_edit_val"):
                ev1, ev2 = st.columns(2)
                with ev1:
                    evt = st.selectbox("Tipo", TIPOS_VALIDACAO, index=TIPOS_VALIDACAO.index(ve.get("tipo", "Outro")) if ve.get("tipo", "Outro") in TIPOS_VALIDACAO else 5)
                    evia = st.number_input("Total IA", value=ve.get("total_objetos_ia", ve.get("total_objetos", 0)))
                with ev2:
                    evman = st.number_input("Total Equipe", value=ve.get("total_objetos_manual", 0))
                csv_btn, cev = st.columns(2)
                with csv_btn:
                    bsv = st.form_submit_button("Salvar Alteracoes", use_container_width=True)
                with cev:
                    bev = st.form_submit_button("Excluir Registro", use_container_width=True)
                if bsv:
                    validacoes[idx_v]["tipo"] = evt
                    validacoes[idx_v]["total_objetos_ia"] = evia
                    validacoes[idx_v]["total_objetos_manual"] = evman
                    salvar_validacoes(validacoes)
                    st.success("Atualizado!")
                    st.rerun()
                if bev:
                    validacoes.pop(idx_v)
                    salvar_validacoes(validacoes)
                    st.success("Excluido!")
                    st.rerun()
        else:
            st.info("Nenhuma validacao registrada.")


elif menu == "Scanner QR/Barcode":
    st.markdown("### Scanner QR / Barcode")
    if "scanner_lista" not in st.session_state:
        st.session_state["scanner_lista"] = []
    tab1, tab2 = st.tabs(["Escanear", "Lista / Exportar"])
    with tab1:
        st.markdown("#### Leitura por Camera ou Scanner Externo")
        codigo_input = st.text_input("Codigo (escaneie ou digite)", placeholder="Escaneie o codigo aqui...", key="scan_input")
        destino_input = st.text_input("Destino", placeholder="Digite o destino")
        if st.button("Adicionar a Lista", type="primary", use_container_width=True):
            if codigo_input:
                item_scan = {"codigo": codigo_input, "destino": destino_input, "horario": datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M:%S"), "registrado_por": st.session_state.get("nome_logado", "Admin")}
                st.session_state["scanner_lista"].append(item_scan)
                st.success("Adicionado: " + codigo_input)
            else:
                st.error("Escaneie ou digite um codigo!")
        st.markdown("#### Ou use a camera do celular")
        foto_qr = st.camera_input("Fotografe o QR Code / Barcode")
        if foto_qr:
            st.info("Foto capturada! Digite o codigo lido manualmente acima.")
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
                import urllib.parse
                texto_encoded = urllib.parse.quote(escala_wpp)
                if numeros_wpp.strip():
                    for num in numeros_wpp.strip().split(NL):
                        num = num.strip()
                        if num:
                            link = "https://wa.me/55" + num + "?text=" + texto_encoded
                            st.markdown("[Enviar para " + num + "](" + link + ")")
                else:
                    link = "https://wa.me/?text=" + texto_encoded
                    st.markdown("[Abrir WhatsApp com mensagem](" + link + ")")
        else:
            st.info("Gere uma escala primeiro no menu Gerador de Escala.")
    with tab2:
        msg_livre = st.text_area("Mensagem", placeholder="Digite sua mensagem aqui...")
        numeros_livre = st.text_area("Numeros (um por linha)", placeholder="11999999999", key="nums_livre")
        if st.button("Gerar Links", type="primary", use_container_width=True, key="btn_wpp_livre"):
            if msg_livre:
                import urllib.parse
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
    tipo_rel = st.selectbox("Tipo de Relatorio", ["Escalas", "Motoristas", "Validacoes", "Funcionarios", "Absenteismo", "Desempenho", "Forecast"])
    dr1, dr2 = st.columns(2)
    with dr1:
        data_ini = st.date_input("Data Inicio", value=date.today() - timedelta(days=7), key="rel_ini")
    with dr2:
        data_fim = st.date_input("Data Fim", value=date.today(), key="rel_fim")
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
        dados_rel = [d for d in carregar_desempenho() if di_str <= d.get("data_avaliacao", d.get("registrado_em", ""))[:10] <= df_str]
    elif tipo_rel == "Forecast":
        dados_rel = [f for f in carregar_forecast() if di_str <= f.get("data", "") <= df_str]
    if dados_rel:
        df_rel = pd.DataFrame(dados_rel)
        st.dataframe(df_rel, use_container_width=True, hide_index=True)
        st.markdown("Total: **" + str(len(dados_rel)) + "** registros")
        re1, re2 = st.columns(2)
        with re1:
            buf = io.BytesIO()
            df_rel.to_excel(buf, index=False, engine="openpyxl")
            st.download_button("Baixar Excel", data=buf.getvalue(), file_name="relatorio_" + tipo_rel.lower() + "_" + datetime.now(FUSO_BR).strftime("%Y%m%d") + ".xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        with re2:
            csv_rel = df_rel.to_csv(index=False)
            st.download_button("Baixar CSV", data=csv_rel, file_name="relatorio_" + tipo_rel.lower() + "_" + datetime.now(FUSO_BR).strftime("%Y%m%d") + ".csv", mime="text/csv", use_container_width=True)
    else:
        st.info("Nenhum registro encontrado no periodo.")


elif menu == "Configuracoes":
    st.markdown("### Configuracoes")
    tab1, tab2, tab3 = st.tabs(["Site", "Sistema", "Ajuda"])
    with tab1:
        st.markdown("#### Informacoes do Site")
        st.markdown("- **Site:** " + SITE)
        st.markdown("- **Operacao:** First Mile / Cross Dock")
        st.markdown("- **Turno:** Tarde (14h-20h)")
        st.markdown("- **Fuso:** America/Sao_Paulo (Brasilia)")
    with tab2:
        st.markdown("#### Informacoes do Sistema")
        st.markdown("- **Versao:** 6.0")
        st.markdown("- **Python:** Streamlit")
        st.markdown("- **IA:** YOLO v8 (ultralytics)")
        st.markdown("- **Status YOLO:** " + ("Instalado" if yolo_ok else "Nao instalado"))
    with tab3:
        st.markdown("#### Ajuda")
        st.markdown("**Como usar o app:**")
        st.markdown("1. Cadastre os funcionarios")
        st.markdown("2. Registre o forecast do dia")
        st.markdown("3. Gere a escala")
        st.markdown("4. Registre motoristas conforme chegam")
        st.markdown("5. Faca validacoes por foto")
        st.markdown("6. Use o scanner para leituras")
        st.markdown("7. Envie a escala por WhatsApp")
        st.markdown("8. Consulte relatorios")


elif menu == "Gerenciar Usuarios":
    st.markdown("### Gerenciar Usuarios")
    usuarios = carregar_usuarios()
    tab1, tab2, tab3 = st.tabs(["Novo Usuario", "Lista / Editar", "Remover"])
    with tab1:
        with st.form("form_novo_user"):
            nu1, nu2 = st.columns(2)
            with nu1:
                novo_user = st.text_input("Login (usuario)")
                novo_nome = st.text_input("Nome Completo")
            with nu2:
                novo_perfil = st.selectbox("Perfil", ["Admin", "Supervisor", "Operador", "Visualizador"])
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
                        nu = {"usuario": novo_user.lower().strip(), "senha": cifrar_senha(nova_senha), "nome": novo_nome, "perfil": novo_perfil, "status": "Ativo", "criado_em": datetime.now(FUSO_BR).strftime("%Y-%m-%d")}
                        usuarios.append(nu)
                        salvar_usuarios(usuarios)
                        st.success("Usuario " + novo_user + " criado!")
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
            perfis_list = ["Admin", "Supervisor", "Operador", "Visualizador"]
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
                    nova_s = st.text_input("Nova Senha (deixe vazio para manter)", type="password")
                bsu = st.form_submit_button("Salvar Alteracoes", use_container_width=True)
                if bsu:
                    usuarios[idx_u]["nome"] = eun
                    usuarios[idx_u]["perfil"] = eup
                    usuarios[idx_u]["status"] = eus
                    if nova_s:
                        usuarios[idx_u]["senha"] = cifrar_senha(nova_s)
                    salvar_usuarios(usuarios)
                    st.success("Usuario atualizado!")
                    st.rerun()
        else:
            st.info("Nenhum usuario.")
    with tab3:
        if len(usuarios) > 1:
            usr_logado = st.session_state.get("usuario_logado", "")
            outros = [u["usuario"] + " (" + u["nome"] + ")" for u in usuarios if u["usuario"] != usr_logado]
            if outros:
                sel_rem = st.selectbox("Selecione para remover", outros, key="sel_rem_u")
                if st.button("Remover Usuario", type="secondary"):
                    user_rem = sel_rem.split(" (")
                    user_rem_login = primeiro(user_rem)
                    usuarios = [u for u in usuarios if u["usuario"] != user_rem_login]
                    salvar_usuarios(usuarios)
                    st.success("Usuario removido!")
                    st.rerun()
            else:
                st.info("Nao ha usuarios para remover.")
        else:
            st.warning("Voce e o unico admin. Nao pode se remover!")


rodape = "<div style='text-align: center; color: #666; padding: 20px;'>" + SITE + " Manager v6.0 | First Mile Operations | Amazon Logistics</div>"
st.markdown("---")
st.markdown(rodape, unsafe_allow_html=True)

