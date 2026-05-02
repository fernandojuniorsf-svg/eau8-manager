import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import json
import os
import random
from PIL import Image
import io

NL = chr(10)

st.set_page_config(
    page_title="EUA8 Manager | Amazon Logistics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* {font-family: 'Inter', sans-serif;}
.main-header {
    text-align: center;
    padding: 1.5rem 1rem;
    background: linear-gradient(135deg, #232F3E 0%, #37475A 50%, #232F3E 100%);
    border-radius: 12px;
    margin-bottom: 1.5rem;
    border-bottom: 4px solid #FF9900;
}
.main-header h1 {color: #FFFFFF; font-size: 2.2rem; font-weight: 700; margin: 0;}
.main-header p {color: #FF9900; font-size: 1rem; margin: 0.3rem 0 0 0; font-weight: 500;}
.sidebar-logo {text-align: center; padding: 1rem 0; border-bottom: 2px solid #FF9900; margin-bottom: 1rem;}
div[data-testid="stSidebar"] {background: linear-gradient(180deg, #232F3E 0%, #1A242F 100%);}
div[data-testid="stSidebar"] .stMarkdown p, div[data-testid="stSidebar"] .stMarkdown li, div[data-testid="stSidebar"] .stRadio label {color: #FFFFFF;}
div[data-testid="stSidebar"] .stRadio label:hover {color: #FF9900;}
div[data-testid="stSidebar"] hr {border-color: #FF9900;}
.stButton > button[kind="primary"] {background: linear-gradient(90deg, #FF9900, #FFB84D); color: #232F3E; font-weight: 700; border: none; border-radius: 8px;}
.stButton > button[kind="primary"]:hover {background: linear-gradient(90deg, #FFB84D, #FF9900); color: #000;}
.stButton > button[kind="secondary"] {background: transparent; color: #FF9900; border: 2px solid #FF9900; font-weight: 600; border-radius: 8px;}
.stButton > button[kind="secondary"]:hover {background: #FF9900; color: #232F3E;}
div[data-testid="stMetric"] {background: linear-gradient(135deg, #232F3E, #37475A); border-radius: 12px; padding: 1rem; border-left: 4px solid #FF9900; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
div[data-testid="stMetric"] label {color: #AAAAAA;}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {color: #FF9900; font-weight: 700;}
.stTabs [data-baseweb="tab-list"] button {color: #FFFFFF; font-weight: 500;}
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {color: #FF9900; border-bottom-color: #FF9900;}
div[data-testid="stExpander"] {border: 1px solid #37475A; border-radius: 8px; border-left: 3px solid #FF9900;}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

sidebar_html = '<div class="sidebar-logo">'
sidebar_html += '<h2 style="color:#FF9900;margin:0;font-size:1.8rem;">EUA8 Manager</h2>'
sidebar_html += '<p style="color:#FFFFFF;margin:0.3rem 0 0 0;font-size:0.85rem;">First Mile Operations</p>'
sidebar_html += '<p style="color:#AAAAAA;margin:0.2rem 0 0 0;font-size:0.75rem;">Amazon Logistics</p>'
sidebar_html += '</div>'
st.sidebar.markdown(sidebar_html, unsafe_allow_html=True)

PASTA_DADOS = "[PASSWORD]"
PASTA_FOTOS = "validacoes_fotos"
PASTA_ESCALAS = "escalas"
PASTA_MOTORISTAS = "motoristas_fotos"
os.makedirs(PASTA_DADOS, exist_ok=True)
os.makedirs(PASTA_FOTOS, exist_ok=True)
os.makedirs(PASTA_ESCALAS, exist_ok=True)
os.makedirs(PASTA_MOTORISTAS, exist_ok=True)

ARQ_FUNCIONARIOS = os.path.join(PASTA_DADOS, "funcionarios.json")
ARQ_VALIDACOES = os.path.join(PASTA_DADOS, "validacoes.json")
ARQ_ESCALAS = os.path.join(PASTA_DADOS, "escalas.json")
ARQ_MOTORISTAS = os.path.join(PASTA_DADOS, "motoristas.json")
ARQ_FORECAST = os.path.join(PASTA_DADOS, "forecast.json")

POSICOES = [
    "Receive (Recebimento)",
    "Stow (Armazenamento)",
    "Depart (Expedicao)",
    "Pallet Building",
    "Scanning",
    "Problem Solve",
    "Water Spider",
    "Loading (Carregamento)",
    "Unloading (Descarga)",
    "Quality Audit"
]

TURNOS = ["Tarde (14h-20h)"]

TIPOS_VALIDACAO = [
    "Pallet Montado",
    "Veiculo Carregado",
    "Estacao Organizada",
    "Conferencia de Volumes",
    "Verificacao de Seguranca",
    "Auditoria de Qualidade"
]

TIPOS_VEICULO = [
    "Carreta (28 pallets)",
    "Truck (16 pallets)",
    "VUC (6 pallets)",
    "Van",
    "Outro"
]


def carregar_dados(arquivo, padrao=None):
    if padrao is None:
        padrao = []
    if os.path.exists(arquivo):
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    return padrao


def salvar_dados(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2, default=str)


def carregar_funcionarios():
    return carregar_dados(ARQ_FUNCIONARIOS, [])


def salvar_funcionarios(func):
    salvar_dados(ARQ_FUNCIONARIOS, func)


def carregar_validacoes():
    return carregar_dados(ARQ_VALIDACOES, [])


def salvar_validacoes(val):
    salvar_dados(ARQ_VALIDACOES, val)


def carregar_escalas():
    return carregar_dados(ARQ_ESCALAS, [])


def salvar_escalas(esc):
    salvar_dados(ARQ_ESCALAS, esc)


def carregar_motoristas():
    return carregar_dados(ARQ_MOTORISTAS, [])


def salvar_motoristas(mot):
    salvar_dados(ARQ_MOTORISTAS, mot)


def carregar_forecast():
    return carregar_dados(ARQ_FORECAST, [])


def salvar_forecast(fc):
    salvar_dados(ARQ_FORECAST, fc)


menu = st.sidebar.radio(
    "Menu Principal",
    [
        "Dashboard",
        "Cadastro de Funcionarios",
        "Gerador de Escala",
        "Registro de Motorista",
        "Forecast / Volume",
        "Validacao por Foto (IA)",
        "Enviar por WhatsApp",
        "Relatorios",
        "Configuracoes"
    ]
)

st.sidebar.markdown("---")
agora = datetime.now().strftime("%d/%m/%Y %H:%M")
info_sb = "<div style='color:#AAAAAA;font-size:0.8rem;'>"
info_sb += "<p>Data: <strong style='color:#FF9900;'>" + agora + "</strong></p>"
info_sb += "<p>Lider: <strong style='color:#FF9900;'>Fernando</strong></p>"
info_sb += "<p>Site: <strong style='color:#FF9900;'>EUA8</strong></p>"
info_sb += "<p>Turno: <strong style='color:#FF9900;'>Tarde (14h-20h)</strong></p>"
info_sb += "</div>"
st.sidebar.markdown(info_sb, unsafe_allow_html=True)


if menu == "Dashboard":
    header = '<div class="main-header">'
    header += '<h1>EUA8 Manager</h1>'
    header += '<p>First Mile Operations | Amazon Logistics</p>'
    header += '</div>'
    st.markdown(header, unsafe_allow_html=True)
    st.markdown("### Dashboard Operacional")
    funcionarios = carregar_funcionarios()
    validacoes = carregar_validacoes()
    escalas = carregar_escalas()
    motoristas = carregar_motoristas()
    forecasts = carregar_forecast()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_func = len(funcionarios)
        ativos = len([f for f in funcionarios if f.get("status", "Ativo") == "Ativo"])
        st.metric("Funcionarios Ativos", ativos, "/" + str(total_func) + " total")
    with col2:
        hoje = datetime.now().strftime("%Y-%m-%d")
        val_hoje = len([v for v in validacoes if v.get("data", "")[:10] == hoje])
        st.metric("Validacoes Hoje", val_hoje)
    with col3:
        st.metric("Escalas Geradas", len(escalas))
    with col4:
        mot_hoje = len([m for m in motoristas if m.get("data_chegada", "")[:10] == hoje])
        st.metric("Motoristas Hoje", mot_hoje)
    st.markdown("---")
    hoje_fc = datetime.now().strftime("%Y-%m-%d")
    fc_hoje = [f for f in forecasts if f.get("data", "") == hoje_fc]
    if fc_hoje:
        ultimo_fc = fc_hoje[-1]
        st.markdown("### Forecast de Hoje: **" + str(ultimo_fc.get("volume", "N/A")) + " pacotes**")
    else:
        st.info("Nenhum forecast cadastrado para hoje. Va em Forecast / Volume.")
    st.markdown("---")
    col_esq, col_dir = st.columns(2)
    with col_esq:
        st.markdown("### Ultimas Validacoes")
        if validacoes:
            ultimas = sorted(validacoes, key=lambda x: x.get("data", ""), reverse=True)[:5]
            for v in ultimas:
                msg = "- **" + v.get("tipo", "N/A") + "** - "
                msg += v.get("data", "N/A")[:16]
                msg += " - " + str(v.get("total_objetos", 0)) + " objetos"
                st.markdown(msg)
        else:
            st.info("Nenhuma validacao registrada ainda.")
    with col_dir:
        st.markdown("### Equipe EUA8")
        if funcionarios:
            for f in funcionarios[:10]:
                stat = f.get("status", "Ativo")
                st.markdown("- [" + stat + "] **" + f["nome"] + "** - " + f.get("tipo", "Fixo"))
        else:
            st.info("Nenhum funcionario cadastrado.")
            
elif menu == "Cadastro de Funcionarios":
    st.markdown("### Cadastro de Funcionarios")
    funcionarios = carregar_funcionarios()
    tab1, tab2, tab3 = st.tabs(["Novo Funcionario", "Lista / Editar", "Remover"])
    with tab1:
        st.markdown("#### Adicionar Funcionario")
        with st.form("form_func"):
            c1, c2 = st.columns(2)
            with c1:
                nome = st.text_input("Nome Completo")
                tipo = st.selectbox("Tipo", ["Fixo", "Freelancer"])
                telefone = st.text_input("Telefone (com DDD)", placeholder="11999999999")
            with c2:
                habilidades = st.multiselect("Habilidades/Posicoes", POSICOES)
                turno_pref = st.selectbox("Turno Preferencial", TURNOS)
                status = st.selectbox("Status", ["Ativo", "Inativo", "Ferias", "Afastado", "Falta"])
            enviado = st.form_submit_button("Cadastrar Funcionario", use_container_width=True)
            if enviado and nome:
                novo = {}
                novo["id"] = len(funcionarios) + 1
                novo["nome"] = nome
                novo["tipo"] = tipo
                novo["telefone"] = telefone
                novo["habilidades"] = habilidades
                novo["turno_preferencial"] = turno_pref
                novo["status"] = status
                novo["data_cadastro"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                funcionarios.append(novo)
                salvar_funcionarios(funcionarios)
                st.success(nome + " cadastrado(a) com sucesso!")
                st.rerun()
            elif enviado:
                st.error("Preencha pelo menos o nome!")
    with tab2:
        st.markdown("#### Lista de Funcionarios")
        if funcionarios:
            cf1, cf2 = st.columns(2)
            with cf1:
                ft = st.selectbox("Filtrar por Tipo", ["Todos", "Fixo", "Freelancer"])
            with cf2:
                fs = st.selectbox("Filtrar por Status", ["Todos", "Ativo", "Inativo", "Ferias", "Afastado", "Falta"])
            lista = funcionarios
            if ft != "Todos":
                lista = [f for f in lista if f.get("tipo") == ft]
            if fs != "Todos":
                lista = [f for f in lista if f.get("status") == fs]
            if lista:
                df = pd.DataFrame(lista)
                cols_show = ["nome", "tipo", "telefone", "turno_preferencial", "status"]
                cols_ok = [c for c in cols_show if c in df.columns]
                st.dataframe(df[cols_ok], use_container_width=True, hide_index=True)
            else:
                st.warning("Nenhum funcionario com esses filtros.")
            st.markdown("---")
            st.markdown("#### Editar Funcionario")
            nomes_edit = [f["nome"] for f in funcionarios]
            nome_editar = st.selectbox("Selecione o funcionario", nomes_edit, key="sel_edit")
            idx_edit = nomes_edit.index(nome_editar)
            func_edit = funcionarios[idx_edit]
            st.markdown("---")
            with st.form("form_editar"):
                st.markdown("**Editando: " + nome_editar + "**")
                ce1, ce2 = st.columns(2)
                with ce1:
                    novo_status = st.selectbox(
                        "Status",
                        ["Ativo", "Inativo", "Ferias", "Afastado", "Falta"],
                        index=["Ativo", "Inativo", "Ferias", "Afastado", "Falta"].index(func_edit.get("status", "Ativo")) if func_edit.get("status", "Ativo") in ["Ativo", "Inativo", "Ferias", "Afastado", "Falta"] else 0
                    )
                    novo_tipo = st.selectbox(
                        "Tipo",
                        ["Fixo", "Freelancer"],
                        index=["Fixo", "Freelancer"].index(func_edit.get("tipo", "Fixo")) if func_edit.get("tipo", "Fixo") in ["Fixo", "Freelancer"] else 0
                    )
                    novo_tel = st.text_input("Telefone", value=func_edit.get("telefone", ""))
                with ce2:
                    novas_hab = st.multiselect(
                        "Habilidades/Posicoes",
                        POSICOES,
                        default=[h for h in func_edit.get("habilidades", []) if h in POSICOES]
                    )
                btn_editar = st.form_submit_button("Salvar Alteracoes", use_container_width=True)
                if btn_editar:
                    funcionarios[idx_edit]["status"] = novo_status
                    funcionarios[idx_edit]["tipo"] = novo_tipo
                    funcionarios[idx_edit]["telefone"] = novo_tel
                    funcionarios[idx_edit]["habilidades"] = novas_hab
                    salvar_funcionarios(funcionarios)
                    st.success(nome_editar + " atualizado(a) com sucesso!")
                    st.rerun()
        else:
            st.info("Nenhum funcionario cadastrado ainda.")
    with tab3:
        st.markdown("#### Remover Funcionario")
        if funcionarios:
            nomes_rem = [f["nome"] for f in funcionarios]
            nome_rem = st.selectbox("Selecione", nomes_rem, key="sel_rem")
            if st.button("Remover", type="secondary"):
                funcionarios = [f for f in funcionarios if f["nome"] != nome_rem]
                salvar_funcionarios(funcionarios)
                st.success(nome_rem + " removido(a)!")
                st.rerun()
        else:
            st.info("Nenhum funcionario cadastrado.")


elif menu == "Gerador de Escala":
    st.markdown("### Gerador de Escala Automatico")
    funcionarios = carregar_funcionarios()
    ativos = [f for f in funcionarios if f.get("status", "Ativo") == "Ativo"]
    if not ativos:
        st.warning("Cadastre funcionarios ativos primeiro para gerar escalas!")
    else:
        tab1, tab2 = st.tabs(["Gerar Nova Escala", "Escalas Anteriores"])
        with tab1:
            st.markdown("#### Configurar Escala")
            c1, c2, c3 = st.columns(3)
            with c1:
                data_escala = st.date_input("Data da Escala", value=date.today() + timedelta(days=1))
            with c2:
                turno_escala = st.selectbox("Turno", TURNOS)
            with c3:
                forecasts = carregar_forecast()
                fc_dia = [f for f in forecasts if f.get("data", "") == data_escala.strftime("%Y-%m-%d")]
                if fc_dia:
                    vol_fc = str(fc_dia[-1].get("volume", "N/A"))
                    st.info("Forecast do dia: " + vol_fc + " pacotes")
                else:
                    st.warning("Sem forecast para esse dia.")
            st.markdown("#### Posicoes Necessarias")
            pos_nec = st.multiselect("Selecione as posicoes", POSICOES, default=POSICOES[:6])
            st.markdown("#### Funcionarios Disponiveis")
            disponiveis = []
            cols = st.columns(3)
            for i, func in enumerate(ativos):
                with cols[i % 3]:
                    label = func["nome"] + " (" + func["tipo"] + ")"
                    if st.checkbox(label, value=True, key="disp_" + str(i)):
                        disponiveis.append(func)
            st.markdown("---")
            if st.button("Gerar Escala Automatica", type="primary", use_container_width=True):
                if len(disponiveis) < len(pos_nec):
                    aviso = "Disponiveis: " + str(len(disponiveis))
                    aviso += " | Posicoes: " + str(len(pos_nec))
                    st.warning(aviso)
                escala = []
                pool = list(disponiveis)
                random.shuffle(pool)
                for posicao in pos_nec:
                    alocado = None
                    for func in pool:
                        if posicao in func.get("habilidades", []):
                            alocado = func
                            break
                    if not alocado and pool:
                        alocado = pool
                    if alocado:
                        item_esc = {}
                        item_esc["posicao"] = posicao
                        item_esc["funcionario"] = alocado["nome"]
                        item_esc["telefone"] = alocado.get("telefone", "")
                        item_esc["tipo"] = alocado.get("tipo", "Fixo")
                        escala.append(item_esc)
                        if alocado in pool:
                            pool.remove(alocado)
                        if not pool:
                            pool = list(disponiveis)
                            random.shuffle(pool)
                st.session_state["escala_rascunho"] = escala
                st.session_state["escala_data"] = data_escala.strftime("%Y-%m-%d")
                st.session_state["escala_turno"] = turno_escala
                st.session_state["escala_volume"] = vol_fc if fc_dia else "Sem forecast"
                st.session_state["escala_disponiveis"] = [f["nome"] for f in disponiveis]
                st.success("Escala gerada! Edite abaixo e depois clique em Salvar.")
            if "escala_rascunho" in st.session_state:
                st.markdown("---")
                st.markdown("### Escala Gerada (editavel)")
                data_str_edit = st.session_state.get("escala_data", "")
                turno_edit = st.session_state.get("escala_turno", "")
                volume_edit = st.session_state.get("escala_volume", "")
                info = "**Data:** " + data_str_edit
                info += " | **Turno:** " + turno_edit
                info += " | **Forecast:** " + str(volume_edit)
                st.markdown(info)
                st.info("Clique nas celulas para editar. Use + para adicionar linhas.")
                df_esc = pd.DataFrame(st.session_state["escala_rascunho"])
                nomes_disp = st.session_state.get("escala_disponiveis", [])
                if not nomes_disp:
                    nomes_disp = [f["nome"] for f in carregar_funcionarios()]
                df_editado = st.data_editor(
                    df_esc,
                    use_container_width=True,
                    hide_index=True,
                    num_rows="dynamic",
                    column_config={
                        "posicao": st.column_config.SelectboxColumn(
                            "Posicao",
                            options=POSICOES,
                            required=True
                        ),
                        "funcionario": st.column_config.SelectboxColumn(
                            "Funcionario",
                            options=nomes_disp,
                            required=True
                        ),
                        "telefone": st.column_config.TextColumn("Telefone"),
                        "tipo": st.column_config.SelectboxColumn(
                            "Tipo",
                            options=["Fixo", "Freelancer"]
                        ),
                    },
                    key="editor_escala"
                )
                st.markdown("---")
                col_salvar, col_limpar = st.columns(2)
                with col_salvar:
                    if st.button("Salvar Escala Final", type="primary", use_container_width=True):
                        escala_final = df_editado.to_dict("records")
                        escala_salvar = {}
                        escala_salvar["data"] = data_str_edit
                        escala_salvar["turno"] = turno_edit
                        escala_salvar["volume"] = volume_edit
                        escala_salvar["escala"] = escala_final
                        escala_salvar["gerada_em"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        escalas = carregar_escalas()
                        escalas.append(escala_salvar)
                        salvar_escalas(escalas)
                        data_fmt = data_str_edit
                        try:
                            dt_obj = datetime.strptime(data_str_edit, "%Y-%m-%d")
                            data_fmt = dt_obj.strftime("%d/%m/%Y")
                        except Exception:
                            pass
                        linhas_wpp = []
                        linhas_wpp.append("*ESCALA EUA8 - " + data_fmt + "*")
                        linhas_wpp.append("Turno: " + turno_edit)
                        linhas_wpp.append("Forecast: " + str(volume_edit))
                        linhas_wpp.append("")
                        for item in escala_final:
                            linha = "- " + str(item.get("posicao", "")) + ": *" + str(item.get("funcionario", "")) + "*"
                            linhas_wpp.append(linha)
                        linhas_wpp.append("")
                        linhas_wpp.append("Bora, time!")
                        texto_wpp = NL.join(linhas_wpp)
                        st.session_state["ultima_escala_wpp"] = texto_wpp
                        st.session_state["ultima_escala"] = escala_salvar
                        del st.session_state["escala_rascunho"]
                        st.success("Escala salva com sucesso!")
                        st.balloons()
                        st.markdown("#### Texto pronto para WhatsApp:")
                        st.code(texto_wpp, language=None)
                with col_limpar:
                    if st.button("Descartar Escala", type="secondary", use_container_width=True):
                        del st.session_state["escala_rascunho"]
                        st.info("Escala descartada.")
                        st.rerun()
        with tab2:
            st.markdown("#### Escalas Anteriores")
            escalas = carregar_escalas()
            if escalas:
                esc_sorted = sorted(escalas, key=lambda x: x.get("data", ""), reverse=True)
                for esc in esc_sorted[:10]:
                    label = esc["data"] + " - " + esc["turno"] + " - " + str(esc.get("volume", ""))
                    with st.expander(label):
                        df_e = pd.DataFrame(esc["escala"])
                        st.dataframe(df_e, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma escala gerada ainda.")


elif menu == "Registro de Motorista":
    st.markdown("### Registro de Motorista")
    motoristas = carregar_motoristas()
    tab1, tab2 = st.tabs(["Novo Registro", "Historico de Motoristas"])
    with tab1:
        st.markdown("#### Registrar Chegada / Saida")
        tipo_reg = st.radio("Tipo de Registro:", ["Chegada", "Saida"])
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Dados do Motorista")
            nome_mot = st.text_input("Nome do Motorista")
            tel_mot = st.text_input("Telefone (opcional)", placeholder="11999999999")
            placa = st.text_input("Placa do Veiculo", placeholder="ABC1D23")
            tipo_veic = st.selectbox("Tipo de Veiculo", TIPOS_VEICULO)
            st.markdown("---")
            st.markdown("#### Horario")
            horario_modo = st.radio("Modo do horario:", ["Automatico (agora)", "Manual (digitar)"])
            if horario_modo == "Automatico (agora)":
                horario_reg = datetime.now().strftime("%H:%M")
                st.info("Horario automatico: " + horario_reg)
            else:
                horario_reg = st.text_input("Digite o horario (HH:MM)", placeholder="14:30")
        with c2:
            st.markdown("#### Foto do Motorista / Veiculo")
            fonte_foto = st.radio("Origem da foto:", ["Upload", "Camera"], key="foto_mot_fonte")
            foto_mot = None
            if fonte_foto == "Upload":
                foto_mot = st.file_uploader("Selecione a foto", type=["jpg", "jpeg", "png"], key="up_mot")
            else:
                foto_mot = st.camera_input("Tire uma foto", key="cam_mot")
            st.markdown("---")
            st.markdown("#### Assinatura (opcional)")
            tem_assinatura = st.checkbox("Motorista vai assinar?")
            assinatura_texto = ""
            if tem_assinatura:
                assinatura_texto = st.text_input("Nome completo como assinatura")
        obs_mot = st.text_area("Observacoes", placeholder="Ex: Carga com avaria, motorista sem cracha...")
        st.markdown("---")
        if st.button("Registrar " + tipo_reg, type="primary", use_container_width=True):
            if nome_mot and placa:
                registro = {}
                registro["nome"] = nome_mot
                registro["telefone"] = tel_mot
                registro["placa"] = placa.upper()
                registro["tipo_veiculo"] = tipo_veic
                registro["tipo_registro"] = tipo_reg
                if tipo_reg == "Chegada":
                    registro["data_chegada"] = datetime.now().strftime("%Y-%m-%d") + " " + horario_reg
                    registro["horario_chegada"] = horario_reg
                    registro["modo_horario_chegada"] = horario_modo
                    registro["data_saida"] = ""
                    registro["horario_saida"] = ""
                else:
                    registro["data_saida"] = datetime.now().strftime("%Y-%m-%d") + " " + horario_reg
                    registro["horario_saida"] = horario_reg
                    registro["modo_horario_saida"] = horario_modo
                    registro["data_chegada"] = ""
                    registro["horario_chegada"] = ""
                registro["observacoes"] = obs_mot
                registro["assinatura"] = assinatura_texto
                registro["registrado_por"] = "Fernando"
                registro["data_registro"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                nome_foto_mot = ""
                if foto_mot is not None:
                    img_mot = Image.open(foto_mot)
                    nome_foto_mot = "mot_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
                    caminho_mot = os.path.join(PASTA_MOTORISTAS, nome_foto_mot)
                    img_mot.save(caminho_mot)
                registro["foto"] = nome_foto_mot
                encontrou = False
                for i, m in enumerate(motoristas):
                    if m.get("placa", "") == placa.upper() and m.get("data_chegada", "")[:10] == datetime.now().strftime("%Y-%m-%d"):
                        if tipo_reg == "Saida" and m.get("data_saida", "") == "":
                            motoristas[i]["data_saida"] = registro["data_saida"]
                            motoristas[i]["horario_saida"] = registro["horario_saida"]
                            motoristas[i]["modo_horario_saida"] = horario_modo
                            if nome_foto_mot:
                                motoristas[i]["foto_saida"] = nome_foto_mot
                            encontrou = True
                            break
                if not encontrou:
                    motoristas.append(registro)
                salvar_motoristas(motoristas)
                st.success(tipo_reg + " registrada para " + nome_mot + " - Placa: " + placa.upper())
                st.balloons()
            else:
                st.error("Preencha o nome e a placa!")
    with tab2:
        st.markdown("#### Historico de Motoristas")
        if motoristas:
            fd_mot = st.date_input("Filtrar por data", value=date.today(), key="fd_mot")
            mot_filtro = [m for m in motoristas if m.get("data_chegada", "")[:10] == fd_mot.strftime("%Y-%m-%d") or m.get("data_saida", "")[:10] == fd_mot.strftime("%Y-%m-%d")]
            if mot_filtro:
                df_mot = pd.DataFrame(mot_filtro)
                cols_mot = ["nome", "placa", "tipo_veiculo", "horario_chegada", "horario_saida", "observacoes"]
                cols_ok = [c for c in cols_mot if c in df_mot.columns]
                st.dataframe(df_mot[cols_ok], use_container_width=True, hide_index=True)
                for m in mot_filtro:
                    label = m.get("nome", "") + " - " + m.get("placa", "")
                    with st.expander(label):
                        st.markdown("**Veiculo:** " + m.get("tipo_veiculo", ""))
                        st.markdown("**Chegada:** " + m.get("horario_chegada", "N/A") + " (" + m.get("modo_horario_chegada", "") + ")")
                        st.markdown("**Saida:** " + m.get("horario_saida", "N/A") + " (" + m.get("modo_horario_saida", "") + ")")
                        st.markdown("**Telefone:** " + m.get("telefone", "N/A"))
                        st.markdown("**Assinatura:** " + m.get("assinatura", "Sem assinatura"))
                        st.markdown("**Obs:** " + m.get("observacoes", ""))
                        fp = os.path.join(PASTA_MOTORISTAS, m.get("foto", ""))
                        if m.get("foto", "") and os.path.exists(fp):
                            st.image(fp, width=300)
            else:
                st.info("Nenhum motorista registrado nessa data.")
        else:
            st.info("Nenhum motorista registrado ainda.")

elif menu == "Forecast / Volume":
    st.markdown("### Forecast / Volume Previsto")
    forecasts = carregar_forecast()
    tab1, tab2, tab3 = st.tabs(["Cadastro Manual", "Upload CSV/Excel", "Historico"])
    with tab1:
        st.markdown("#### Cadastrar Forecast do Dia")
        with st.form("form_forecast"):
            cf1, cf2 = st.columns(2)
            with cf1:
                data_fc = st.date_input("Data", value=date.today())
            with cf2:
                volume_fc = st.number_input("Volume previsto (pacotes)", min_value=0, max_value=50000, value=3000, step=100)
            obs_fc = st.text_input("Observacao (opcional)", placeholder="Ex: Pico por conta de promocao")
            btn_fc = st.form_submit_button("Salvar Forecast", use_container_width=True)
            if btn_fc:
                novo_fc = {}
                novo_fc["data"] = data_fc.strftime("%Y-%m-%d")
                novo_fc["volume"] = volume_fc
                novo_fc["observacao"] = obs_fc
                novo_fc["cadastrado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                novo_fc["origem"] = "manual"
                forecasts.append(novo_fc)
                salvar_forecast(forecasts)
                st.success("Forecast salvo para " + data_fc.strftime("%d/%m/%Y") + ": " + str(volume_fc) + " pacotes")
                st.rerun()
    with tab2:
        st.markdown("#### Upload de Forecast Semanal")
        st.markdown("O arquivo deve ter duas colunas: **data** e **volume**")
        st.markdown("Formato da data: YYYY-MM-DD (ex: 2026-05-03)")
        arquivo_fc = st.file_uploader("Selecione o arquivo", type=["csv", "xlsx"], key="up_fc")
        if arquivo_fc is not None:
            try:
                if arquivo_fc.name.endswith(".csv"):
                    df_up = pd.read_csv(arquivo_fc)
                else:
                    df_up = pd.read_excel(arquivo_fc)
                st.markdown("**Previa do arquivo:**")
                st.dataframe(df_up, use_container_width=True, hide_index=True)
                if st.button("Importar Forecast", type="primary", use_container_width=True):
                    count = 0
                    for idx, row in df_up.iterrows():
                        novo_fc = {}
                        novo_fc["data"] = str(row.get("data", ""))
                        novo_fc["volume"] = int(row.get("volume", 0))
                        novo_fc["observacao"] = str(row.get("observacao", ""))
                        novo_fc["cadastrado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        novo_fc["origem"] = "upload"
                        forecasts.append(novo_fc)
                        count += 1
                    salvar_forecast(forecasts)
                    st.success(str(count) + " registros importados com sucesso!")
                    st.rerun()
            except Exception as e:
                st.error("Erro ao ler arquivo: " + str(e))
    with tab3:
        st.markdown("#### Historico de Forecasts")
        if forecasts:
            df_fc = pd.DataFrame(forecasts)
            cols_fc = ["data", "volume", "observacao", "origem", "cadastrado_em"]
            cols_ok = [c for c in cols_fc if c in df_fc.columns]
            st.dataframe(df_fc[cols_ok].sort_values("data", ascending=False), use_container_width=True, hide_index=True)
            if st.button("Limpar Forecasts", type="secondary"):
                salvar_forecast([])
                st.success("Forecasts limpos!")
                st.rerun()
        else:
            st.info("Nenhum forecast cadastrado.")


elif menu == "Validacao por Foto (IA)":
    st.markdown("### Validacao por Foto com IA")
    st.markdown("*Tire uma foto e a IA identifica os objetos*")
    yolo_ok = False
    try:
        from ultralytics import YOLO
        yolo_ok = True
    except ImportError:
        yolo_ok = False
    tab1, tab2 = st.tabs(["Nova Validacao", "Historico"])
    with tab1:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("#### Informacoes da Validacao")
            tipo_val = st.selectbox("Tipo de Validacao", TIPOS_VALIDACAO)
            local_val = st.text_input("Local / Area", placeholder="Ex: Doca 3")
            obs = st.text_area("Observacoes", placeholder="Alguma observacao...")
        with c2:
            st.markdown("#### Enviar Foto")
            fonte = st.radio("Origem da foto:", ["Upload de arquivo", "Camera (celular)"])
            foto = None
            if fonte == "Upload de arquivo":
                foto = st.file_uploader("Selecione a imagem", type=["jpg", "jpeg", "png"])
            else:
                foto = st.camera_input("Tire uma foto")
        if foto is not None:
            st.markdown("---")
            image = Image.open(foto)
            col_orig, col_res = st.columns(2)
            with col_orig:
                st.markdown("#### Foto Original")
                st.image(image, use_container_width=True)
            with col_res:
                st.markdown("#### Analise da IA")
                deteccoes = []
                if yolo_ok:
                    with st.spinner("Analisando imagem com IA..."):
                        temp_path = os.path.join(PASTA_FOTOS, "temp_analise.jpg")
                        image.save(temp_path)
                        @st.cache_resource
                        def carregar_modelo():
                            return YOLO("yolov8n.pt")
                        modelo = carregar_modelo()
                        resultados = modelo(temp_path, conf=0.3)
                        for r in resultados:
                            for box in r.boxes:
                                classe = r.names[int(box.cls)]
                                conf = float(box.conf)
                                det = {}
                                det["objeto"] = classe
                                det["confianca"] = str(round(conf * 100, 1)) + "%"
                                deteccoes.append(det)
                        img_res = resultados.plot()
                        st.image(img_res, channels="BGR", use_container_width=True)
                        if deteccoes:
                            st.success(str(len(deteccoes)) + " objeto(s) detectado(s)!")
                            df_d = pd.DataFrame(deteccoes)
                            contagem = df_d["objeto"].value_counts().reset_index()
                            contagem.columns = ["Objeto", "Quantidade"]
                            st.dataframe(contagem, use_container_width=True, hide_index=True)
                        else:
                            st.warning("Nenhum objeto identificado.")
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                else:
                    st.warning("YOLO nao instalado. Modo demonstracao ativo.")
                    st.info("Para IA real, rode: pip install ultralytics")
                    obj_sim = {}
                    obj_sim["Pallet Montado"] = [
                        {"objeto": "caixa", "quantidade": random.randint(10, 30)},
                        {"objeto": "pallet", "quantidade": random.randint(1, 3)}
                    ]
                    obj_sim["Veiculo Carregado"] = [
                        {"objeto": "caixa", "quantidade": random.randint(50, 150)},
                        {"objeto": "pallet", "quantidade": random.randint(6, 28)}
                    ]
                    obj_sim["Estacao Organizada"] = [
                        {"objeto": "mesa", "quantidade": 1},
                        {"objeto": "scanner", "quantidade": random.randint(1, 3)}
                    ]
                    obj_sim["Conferencia de Volumes"] = [
                        {"objeto": "pacote", "quantidade": random.randint(20, 80)},
                        {"objeto": "etiqueta", "quantidade": random.randint(20, 80)}
                    ]
                    obj_sim["Verificacao de Seguranca"] = [
                        {"objeto": "pessoa", "quantidade": random.randint(1, 5)},
                        {"objeto": "colete", "quantidade": random.randint(0, 5)}
                    ]
                    obj_sim["Auditoria de Qualidade"] = [
                        {"objeto": "caixa", "quantidade": random.randint(5, 20)},
                        {"objeto": "etiqueta", "quantidade": random.randint(0, 3)}
                    ]
                    det_sim = obj_sim.get(tipo_val, [])
                    total_obj = sum(d["quantidade"] for d in det_sim)
                    st.image(image, use_container_width=True, caption="Modo demo")
                    st.success(str(total_obj) + " objeto(s) (simulacao)")
                    df_sim = pd.DataFrame(det_sim)
                    df_sim.columns = ["Objeto", "Quantidade"]
                    st.dataframe(df_sim, use_container_width=True, hide_index=True)
                    for d in det_sim:
                        for _ in range(d["quantidade"]):
                            det = {}
                            det["objeto"] = d["objeto"]
                            det["confianca"] = "demo"
                            deteccoes.append(det)
            st.markdown("---")
            if st.button("Salvar Validacao", type="primary", use_container_width=True):
                nome_foto = "val_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
                caminho_foto = os.path.join(PASTA_FOTOS, nome_foto)
                image.save(caminho_foto)
                registro = {}
                registro["data"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                registro["tipo"] = tipo_val
                registro["local"] = local_val
                registro["observacoes"] = obs
                registro["foto"] = nome_foto
                registro["total_objetos"] = len(deteccoes)
                registro["deteccoes"] = deteccoes[:20]
                registro["validado_por"] = "Fernando"
                validacoes = carregar_validacoes()
                validacoes.append(registro)
                salvar_validacoes(validacoes)
                st.success("Validacao salva com sucesso!")
                st.balloons()
    with tab2:
        st.markdown("#### Historico de Validacoes")
        validacoes = carregar_validacoes()
        if validacoes:
            cf1, cf2 = st.columns(2)
            with cf1:
                ft_val = st.selectbox("Filtrar por Tipo", ["Todos"] + TIPOS_VALIDACAO, key="fh")
            with cf2:
                fd = st.date_input("Filtrar por Data", value=None, key="fdh")
            lista = validacoes
            if ft_val != "Todos":
                lista = [v for v in lista if v.get("tipo") == ft_val]
            if fd:
                lista = [v for v in lista if v.get("data", "")[:10] == fd.strftime("%Y-%m-%d")]
            v_sorted = sorted(lista, key=lambda x: x.get("data", ""), reverse=True)
            for v in v_sorted[:20]:
                label = v.get("tipo", "") + " - "
                label += v.get("data", "")[:16] + " - "
                label += str(v.get("total_objetos", 0)) + " obj"
                with st.expander(label):
                    st.markdown("**Observacoes:** " + v.get("observacoes", "Nenhuma"))
                    st.markdown("**Validado por:** " + v.get("validado_por", "N/A"))
                    fp = os.path.join(PASTA_FOTOS, v.get("foto", ""))
                    if os.path.exists(fp):
                        st.image(fp, width=300)
                    if v.get("deteccoes"):
                        st.dataframe(pd.DataFrame(v["deteccoes"]), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma validacao registrada ainda.")


elif menu == "Enviar por WhatsApp":
    st.markdown("### Enviar por WhatsApp")
    pywhatkit_ok = False
    try:
        import pywhatkit as kit
        pywhatkit_ok = True
    except ImportError:
        pywhatkit_ok = False
    tab1, tab2, tab3, tab4 = st.tabs(["Enviar Escala", "Mensagem Personalizada", "Mensagens Rapidas", "Contatos Salvos"])
    with tab1:
        st.markdown("#### Enviar Ultima Escala")
        if "ultima_escala_wpp" in st.session_state:
            st.markdown("**Previa da mensagem:**")
            st.code(st.session_state["ultima_escala_wpp"], language=None)
            st.markdown("---")
            envio_tipo = st.radio("Enviar para:", ["Contato salvo", "Numero manual", "Grupo"])
            if envio_tipo == "Contato salvo":
                funcionarios = carregar_funcionarios()
                if funcionarios:
                    opcoes_envio = []
                    for f in funcionarios:
                        if f.get("telefone", ""):
                            op = f["nome"] + " (" + f.get("telefone", "") + ")"
                            opcoes_envio.append(op)
                    if opcoes_envio:
                        contato_sel = st.selectbox("Selecione o contato", opcoes_envio, key="cont_esc")
                        if st.button("Enviar para contato", type="primary", key="env_cont_esc"):
                            idx = opcoes_envio.index(contato_sel)
                            func_com_tel = [f for f in funcionarios if f.get("telefone", "")]
                            tel = func_com_tel[idx].get("telefone", "")
                            if pywhatkit_ok and tel:
                                try:
                                    num_fmt = "+55" + tel
                                    if tel.startswith("+"):
                                        num_fmt = tel
                                    kit.sendwhatmsg_instantly(num_fmt, st.session_state["ultima_escala_wpp"], wait_time=15)
                                    st.success("Mensagem enviada!")
                                except Exception as e:
                                    st.error("Erro ao enviar: " + str(e))
                            else:
                                st.warning("pywhatkit nao instalado. Copie o texto acima!")
                    else:
                        st.warning("Nenhum contato com telefone cadastrado.")
                else:
                    st.warning("Cadastre funcionarios primeiro!")
            elif envio_tipo == "Numero manual":
                numero = st.text_input("Numero com codigo do pais", placeholder="+5511999999999")
                if st.button("Enviar", type="primary", key="env_num_esc"):
                    if pywhatkit_ok and numero:
                        try:
                            kit.sendwhatmsg_instantly(numero, st.session_state["ultima_escala_wpp"], wait_time=15)
                            st.success("Mensagem enviada!")
                        except Exception as e:
                            st.error("Erro ao enviar: " + str(e))
                    elif not pywhatkit_ok:
                        st.warning("pywhatkit nao instalado.")
                        st.info("Copie o texto acima e cole no WhatsApp!")
                    else:
                        st.error("Preencha o numero!")
            else:
                st.info("Copie o texto acima e cole no grupo do WhatsApp.")
        else:
            st.info("Nenhuma escala gerada ainda. Va em Gerador de Escala primeiro!")
    with tab2:
        st.markdown("#### Mensagem Personalizada")
        funcionarios = carregar_funcionarios()
        if funcionarios:
            opcoes = []
            for f in funcionarios:
                if f.get("telefone", ""):
                    op = f["nome"] + " (" + f.get("telefone", "") + ")"
                    opcoes.append(op)
            if opcoes:
                func_sel = st.selectbox("Enviar para", opcoes, key="func_msg_pers")
                msg_custom = st.text_area("Mensagem", placeholder="Digite sua mensagem...")
                if st.button("Enviar Mensagem", type="primary", key="env_custom"):
                    idx = opcoes.index(func_sel)
                    func_com_tel = [f for f in funcionarios if f.get("telefone", "")]
                    tel = func_com_tel[idx].get("telefone", "")
                    if pywhatkit_ok and tel:
                        try:
                            num_fmt = "+55" + tel
                            if tel.startswith("+"):
                                num_fmt = tel
                            kit.sendwhatmsg_instantly(num_fmt, msg_custom, wait_time=15)
                            st.success("Mensagem enviada!")
                        except Exception as e:
                            st.error("Erro: " + str(e))
                    elif not pywhatkit_ok:
                        st.warning("pywhatkit nao instalado.")
                        st.code(msg_custom, language=None)
                        st.info("Copie e envie manualmente!")
                    else:
                        st.error("Sem telefone.")
            else:
                st.warning("Nenhum contato com telefone.")
        else:
            st.info("Cadastre funcionarios primeiro!")
    with tab3:
        st.markdown("#### Mensagens Rapidas para o Grupo")
        hoje_str = datetime.now().strftime("%d/%m/%Y")
        t1_linhas = [
            "*BOM TURNO, TIME EUA8!*",
            "Data: " + hoje_str,
            "Bora com tudo hoje!",
            "",
            "Qualquer duvida, me chamem!"
        ]
        t2_linhas = [
            "*FIM DE TURNO - EUA8*",
            "",
            "Obrigado pelo trabalho de hoje, time!",
            "Descansem e ate o proximo turno!"
        ]
        t3_linhas = [
            "*ATENCAO TIME EUA8*",
            "",
            "Amanha teremos *VOLUME DE PICO*!",
            "Precisamos de todo mundo focado.",
            "Confiram a escala e cheguem no horario!"
        ]
        t4_linhas = [
            "*LEMBRETE*",
            "",
            "Time, confiram a escala de amanha!",
            "Se alguem nao puder vir, me avise.",
            "Valeu!"
        ]
        t5_linhas = [
            "*PARABENS, TIME EUA8!*",
            "",
            "Batemos nossa meta hoje!",
            "Voces sao demais!",
            "",
            "-- Fernando"
        ]
        templates = {}
        templates["Inicio do Turno"] = NL.join(t1_linhas)
        templates["Fim do Turno"] = NL.join(t2_linhas)
        templates["Aviso de Pico"] = NL.join(t3_linhas)
        templates["Lembrete de Escala"] = NL.join(t4_linhas)
        templates["Parabens ao Time"] = NL.join(t5_linhas)
        tmpl = st.selectbox("Modelo de Mensagem", list(templates.keys()))
        msg_grupo = st.text_area("Editar mensagem:", value=templates[tmpl], height=200)
        st.code(msg_grupo, language=None)
        st.info("Copie a mensagem acima e cole no grupo do WhatsApp!")
    with tab4:
        st.markdown("#### Gerenciar Contatos")
        st.markdown("Os contatos sao os funcionarios cadastrados com telefone.")
        funcionarios = carregar_funcionarios()
        contatos = [f for f in funcionarios if f.get("telefone", "")]
        if contatos:
            df_cont = pd.DataFrame(contatos)
            cols_cont = ["nome", "telefone", "tipo", "status"]
            cols_ok = [c for c in cols_cont if c in df_cont.columns]
            st.dataframe(df_cont[cols_ok], use_container_width=True, hide_index=True)
            st.info("Para adicionar contatos, va em Cadastro de Funcionarios.")
        else:
            st.warning("Nenhum contato com telefone. Cadastre em Cadastro de Funcionarios.")


elif menu == "Relatorios":
    st.markdown("### Relatorios")
    funcionarios = carregar_funcionarios()
    validacoes = carregar_validacoes()
    escalas = carregar_escalas()
    motoristas = carregar_motoristas()
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Resumo Geral", "Validacoes", "Escalas", "Exportar Escalas CSV", "Motoristas"])
    with tab1:
        st.markdown("#### Resumo Geral")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total Funcionarios", len(funcionarios))
            fixos = len([f for f in funcionarios if f.get("tipo") == "Fixo"])
            free = len([f for f in funcionarios if f.get("tipo") == "Freelancer"])
            st.markdown("- Fixos: **" + str(fixos) + "**")
            st.markdown("- Freelancers: **" + str(free) + "**")
        with c2:
            st.metric("Total Validacoes", len(validacoes))
        with c3:
            st.metric("Total Escalas", len(escalas))
        with c4:
            st.metric("Total Motoristas", len(motoristas))
    with tab2:
        st.markdown("#### Relatorio de Validacoes")
        if validacoes:
            df_val = pd.DataFrame(validacoes)
            cols = ["data", "tipo", "local", "total_objetos", "validado_por"]
            cols_ok = [c for c in cols if c in df_val.columns]
            df_show = df_val[cols_ok].sort_values("data", ascending=False)
            st.dataframe(df_show, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma validacao para exibir.")
    with tab3:
        st.markdown("#### Relatorio de Escalas")
        if escalas:
            resumo = []
            for esc in escalas:
                r = {}
                r["data"] = esc.get("data", "")
                r["turno"] = esc.get("turno", "")
                r["volume"] = esc.get("volume", "")
                r["funcionarios"] = len(esc.get("escala", []))
                r["gerada_em"] = esc.get("gerada_em", "")
                resumo.append(r)
            df_r = pd.DataFrame(resumo)
            st.dataframe(df_r.sort_values("data", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma escala para exibir.")
    with tab4:
        st.markdown("#### Exportar Escalas em CSV")
        if escalas:
            st.markdown("##### Filtrar por Periodo")
            cf1, cf2 = st.columns(2)
            with cf1:
                data_ini = st.date_input("Data Inicial", value=date.today() - timedelta(days=30), key="csv_ini")
            with cf2:
                data_fim = st.date_input("Data Final", value=date.today(), key="csv_fim")
            tipo_exp = st.radio("Tipo de exportacao:", ["Consolidada (tabela unica)", "Resumo por periodo"])
            if tipo_exp == "Consolidada (tabela unica)":
                linhas_csv = []
                for esc in escalas:
                    data_esc = esc.get("data", "")
                    try:
                        dt = datetime.strptime(data_esc, "%Y-%m-%d").date()
                        if dt < data_ini or dt > data_fim:
                            continue
                    except Exception:
                        continue
                    turno_esc = esc.get("turno", "")
                    volume_esc = esc.get("volume", "")
                    gerada = esc.get("gerada_em", "")
                    for item in esc.get("escala", []):
                        linha = {}
                        linha["data"] = data_esc
                        linha["turno"] = turno_esc
                        linha["volume"] = volume_esc
                        linha["posicao"] = item.get("posicao", "")
                        linha["funcionario"] = item.get("funcionario", "")
                        linha["tipo_func"] = item.get("tipo", "")
                        linha["telefone"] = item.get("telefone", "")
                        linha["gerada_em"] = gerada
                        linhas_csv.append(linha)
                if linhas_csv:
                    df_csv = pd.DataFrame(linhas_csv)
                    st.markdown("**Previa da tabela consolidada:**")
                    st.dataframe(df_csv, use_container_width=True, hide_index=True)
                    csv_data = df_csv.to_csv(index=False)
                    nome_arq = "escalas_consolidadas_" + data_ini.strftime("%Y%m%d")
                    nome_arq += "_a_" + data_fim.strftime("%Y%m%d") + ".csv"
                    st.download_button(
                        label="Baixar CSV Consolidado",
                        data=csv_data,
                        file_name=nome_arq,
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.warning("Nenhuma escala encontrada nesse periodo.")
            else:
                resumo_csv = []
                for esc in escalas:
                    data_esc = esc.get("data", "")
                    try:
                        dt = datetime.strptime(data_esc, "%Y-%m-%d").date()
                        if dt < data_ini or dt > data_fim:
                            continue
                    except Exception:
                        continue
                    r = {}
                    r["data"] = data_esc
                    r["turno"] = esc.get("turno", "")
                    r["volume"] = esc.get("volume", "")
                    r["qtd_funcionarios"] = len(esc.get("escala", []))
                    nomes = []
                    for item in esc.get("escala", []):
                        nomes.append(item.get("funcionario", ""))
                    r["funcionarios"] = " | ".join(nomes)
                    r["gerada_em"] = esc.get("gerada_em", "")
                    resumo_csv.append(r)
                if resumo_csv:
                    df_resumo = pd.DataFrame(resumo_csv)
                    st.markdown("**Previa do resumo por periodo:**")
                    st.dataframe(df_resumo, use_container_width=True, hide_index=True)
                    csv_resumo = df_resumo.to_csv(index=False)
                    nome_arq2 = "escalas_resumo_" + data_ini.strftime("%Y%m%d")
                    nome_arq2 += "_a_" + data_fim.strftime("%Y%m%d") + ".csv"
                    st.download_button(
                        label="Baixar CSV Resumo",
                        data=csv_resumo,
                        file_name=nome_arq2,
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.warning("Nenhuma escala encontrada nesse periodo.")
        else:
            st.info("Nenhuma escala para exportar.")
    with tab5:
        st.markdown("#### Relatorio de Motoristas")
        if motoristas:
            df_m = pd.DataFrame(motoristas)
            cols_m = ["nome", "placa", "tipo_veiculo", "horario_chegada", "horario_saida", "data_registro"]
            cols_ok = [c for c in cols_m if c in df_m.columns]
            st.dataframe(df_m[cols_ok].sort_values("data_registro", ascending=False), use_container_width=True, hide_index=True)
            csv_mot = df_m[cols_ok].to_csv(index=False)
            st.download_button(
                label="Baixar CSV Motoristas",
                data=csv_mot,
                file_name="motoristas_registros.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("Nenhum motorista registrado.")


elif menu == "Configuracoes":
    st.markdown("### Configuracoes")
    tab1, tab2, tab3 = st.tabs(["Site", "Sistema", "Ajuda"])
    with tab1:
        st.markdown("#### Informacoes do Site")
        st.markdown("- **Site:** EUA8")
        st.markdown("- **Operacao:** First Mile / Cross Dock")
        st.markdown("- **Lider:** Fernando")
        st.markdown("- **Turno:** Tarde (14h - 20h)")
        st.markdown("- **Veiculos:** Carretas (28p), Trucks (16p), VUCs (6p)")
    with tab2:
        st.markdown("#### Gerenciamento de Dados")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Arquivos de Dados:**")
            st.markdown("- Funcionarios: " + ARQ_FUNCIONARIOS)
            st.markdown("- Validacoes: " + ARQ_VALIDACOES)
            st.markdown("- Escalas: " + ARQ_ESCALAS)
            st.markdown("- Motoristas: " + ARQ_MOTORISTAS)
            st.markdown("- Forecast: " + ARQ_FORECAST)
        with c2:
            st.markdown("**Limpar Dados:**")
            if st.button("Limpar Validacoes", type="secondary"):
                salvar_validacoes([])
                st.success("Validacoes limpas!")
                st.rerun()
            if st.button("Limpar Escalas", type="secondary"):
                salvar_escalas([])
                st.success("Escalas limpas!")
                st.rerun()
            if st.button("Limpar Motoristas", type="secondary"):
                salvar_motoristas([])
                st.success("Motoristas limpos!")
                st.rerun()
            if st.button("Limpar Forecasts", type="secondary"):
                salvar_forecast([])
                st.success("Forecasts limpos!")
                st.rerun()
    with tab3:
        st.markdown("#### Como usar o EUA8 Manager")
        st.markdown("1. **Cadastre seus funcionarios** - Nome, telefone, habilidades e turno")
        st.markdown("2. **Cadastre o forecast** - Volume previsto manual ou por upload")
        st.markdown("3. **Gere a escala** - Escolha data e edite antes de salvar")
        st.markdown("4. **Registre motoristas** - Chegada e saida com foto e placa")
        st.markdown("5. **Valide com fotos** - Tire fotos e a IA identifica objetos")
        st.markdown("6. **Envie por WhatsApp** - Compartilhe com o time")
        st.markdown("7. **Acompanhe nos relatorios** - Exporte em CSV")


rodape = "<div style='text-align: center; color: #666; font-size: 0.8rem;'>"
rodape += "EUA8 Manager v6.0 | First Mile Operations | Desenvolvido por Fernando"
rodape += "</div>"
st.markdown("---")
st.markdown(rodape, unsafe_allow_html=True)
