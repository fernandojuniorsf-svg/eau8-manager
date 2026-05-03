
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

for p in ["dados_eau8", "fotos_validacao", "fotos_motoristas"]:
    if not os.path.exists(p):
        os.makedirs(p)

PASTA_DADOS = "dados_eau8"
PASTA_FOTOS = "fotos_validacao"
PASTA_MOTORISTAS = "fotos_motoristas"

yolo_ok = False
try:
    from ultralytics import YOLO
    yolo_ok = True
except ImportError:
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


def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def carregar_usuarios():
    if os.path.exists(ARQ_USUARIOS):
        with open(ARQ_USUARIOS, "r", encoding="utf-8") as f:
            return json.load(f)
    admin = {"usuario": "fernando", "senha": hash_senha("eau8"), "nome": "Fernando Junior", "perfil": "Admin", "status": "Ativo", "criado_em": "2026-05-03"}
    salvar_usuarios([admin])
    return [admin]


def salvar_usuarios(u):
    with open(ARQ_USUARIOS, "w", encoding="utf-8") as f:
        json.dump(u, f, ensure_ascii=False, indent=2)


def carregar_funcionarios():
    if os.path.exists(ARQ_FUNCIONARIOS):
        with open(ARQ_FUNCIONARIOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salvar_funcionarios(d):
    with open(ARQ_FUNCIONARIOS, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def carregar_escalas():
    if os.path.exists(ARQ_ESCALAS):
        with open(ARQ_ESCALAS, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salvar_escalas(d):
    with open(ARQ_ESCALAS, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def carregar_motoristas():
    if os.path.exists(ARQ_MOTORISTAS):
        with open(ARQ_MOTORISTAS, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salvar_motoristas(d):
    with open(ARQ_MOTORISTAS, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def carregar_forecast():
    if os.path.exists(ARQ_FORECAST):
        with open(ARQ_FORECAST, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salvar_forecast(d):
    with open(ARQ_FORECAST, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def carregar_validacoes():
    if os.path.exists(ARQ_VALIDACOES):
        with open(ARQ_VALIDACOES, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salvar_validacoes(d):
    with open(ARQ_VALIDACOES, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def carregar_absenteismo():
    if os.path.exists(ARQ_ABSENTEISMO):
        with open(ARQ_ABSENTEISMO, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salvar_absenteismo(d):
    with open(ARQ_ABSENTEISMO, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def carregar_desempenho():
    if os.path.exists(ARQ_DESEMPENHO):
        with open(ARQ_DESEMPENHO, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salvar_desempenho(d):
    with open(ARQ_DESEMPENHO, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


PERFIS_ACESSO = {
    "Admin": ["Dashboard", "Cadastro de Funcionarios", "Gerador de Escala", "Registro de Motorista", "Absenteismo", "Desempenho por Funcao", "Forecast / Volume", "Validacao por Foto (IA)", "Scanner QR/Barcode", "Enviar por WhatsApp", "Relatorios", "Configuracoes", "Gerenciar Usuarios"],
    "Supervisor": ["Dashboard", "Cadastro de Funcionarios", "Gerador de Escala", "Registro de Motorista", "Absenteismo", "Desempenho por Funcao", "Forecast / Volume", "Validacao por Foto (IA)", "Scanner QR/Barcode", "Enviar por WhatsApp", "Relatorios"],
    "Operador": ["Dashboard", "Registro de Motorista", "Validacao por Foto (IA)", "Scanner QR/Barcode"],
    "Visualizador": ["Dashboard", "Relatorios"]
}

st.set_page_config(page_title="EUA8 Manager", page_icon="F", layout="wide")

if "logado" not in st.session_state:
    st.session_state["logado"] = False
    st.session_state["usuario_logado"] = None
    st.session_state["perfil_logado"] = None
    st.session_state["nome_logado"] = None

if not st.session_state["logado"]:
    col_e, col_c, col_d = st.columns([1, 2, 1])
    with col_c:
        st.markdown("# EUA8 Manager")
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
                        if u["usuario"] == usuario_input.lower().strip() and u["senha"] == hash_senha(senha_input):
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
st.sidebar.markdown("## EUA8 Manager")
st.sidebar.markdown("*First Mile | Amazon Logistics*")
st.sidebar.markdown("Bem-vindo, **" + nome_logado + "** (" + perfil_logado + ")")
st.sidebar.markdown("---")

menus_permitidos = PERFIS_ACESSO.get(perfil_logado, [])
todos_menus = ["Dashboard", "Cadastro de Funcionarios", "Gerador de Escala", "Registro de Motorista", "Absenteismo", "Desempenho por Funcao", "Forecast / Volume", "Validacao por Foto (IA)", "Scanner QR/Barcode", "Enviar por WhatsApp", "Relatorios", "Configuracoes", "Gerenciar Usuarios"]
menus_visiveis = [m for m in todos_menus if m in menus_permitidos]
menu = st.sidebar.radio("Menu Principal", menus_visiveis)

st.sidebar.markdown("---")
agora = datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M")
st.sidebar.markdown("Data: **" + agora + "**")
st.sidebar.markdown("Site: **EUA8**")
st.sidebar.markdown("Turno: **Tarde (14h-20h)**")
st.sidebar.markdown("---")
if st.sidebar.button("Sair", use_container_width=True):
    for k in ["logado", "usuario_logado", "perfil_logado", "nome_logado"]:
        st.session_state[k] = None
    st.session_state["logado"] = False
    st.rerun()

st.markdown("# EUA8 Manager")
st.markdown("*First Mile Operations | Amazon Logistics*")

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
    volume_hoje = fc_hoje[0].get("volume", 0) if fc_hoje else 0
    abs_hoje = [a for a in absenteismo if a.get("data", "") == hoje_str]
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
        obj_ia_h = sum(v.get("total_objetos_ia", v.get("total_objetos", 0)) for v in val_hoje)
        obj_eq_h = sum(v.get("total_objetos_manual", 0) for v in val_hoje)
        st.metric("Objetos Validados", "IA: " + str(obj_ia_h) + " | Eq: " + str(obj_eq_h))
    with c7:
        st.metric("Faltas Hoje", len(abs_hoje))
    st.markdown("---")
    st.markdown("### Graficos")
    tg1, tg2, tg3, tg4, tg5 = st.tabs(["Validacoes", "Forecast", "Motoristas", "Absenteismo", "Equipe"])
    with tg1:
        d7 = []
        ia7 = []
        eq7 = []
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
        dfc7 = []
        vfc7 = []
        for i in range(6, -1, -1):
            dd = (datetime.now(FUSO_BR) - timedelta(days=i)).strftime("%Y-%m-%d")
            dl = (datetime.now(FUSO_BR) - timedelta(days=i)).strftime("%d/%m")
            dfc7.append(dl)
            fd = [f for f in forecasts if f.get("data", "") == dd]
            vfc7.append(fd[0].get("volume", 0) if fd else 0)
        dff7 = pd.DataFrame({"Data": dfc7, "Volume": vfc7})
        st.dataframe(dff7, use_container_width=True, hide_index=True)
        st.line_chart(dff7.set_index("Data"))
    with tg3:
        dm7 = []
        qm7 = []
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
        dab7 = []
        qab7 = []
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
            pt = {}
            pst = {}
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
    tab1, tab2 = st.tabs(["Novo Funcionario", "Lista"])
    with tab1:
        with st.form("form_func"):
            cf1, cf2 = st.columns(2)
            with cf1:
                nome = st.text_input("Nome Completo")
                tipo = st.selectbox("Tipo", ["Fixo", "Freelancer"])
                telefone = st.text_input("Telefone (com DDD)", placeholder="11999999999")
            with cf2:
                qualidades = st.multiselect("Qualidades / Posicoes", POSICOES)
                obs_func = st.text_input("Observacoes")
            btn_func = st.form_submit_button("Cadastrar", use_container_width=True)
            if btn_func:
                if nome:
                    nv = {"nome": nome, "tipo": tipo, "telefone": telefone, "qualidades": qualidades, "observacoes": obs_func, "status": "Ativo", "cadastrado_em": datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M")}
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
                    bsf = st.form_submit_button("Salvar", use_container_width=True)
                with cef:
                    bef = st.form_submit_button("Excluir", use_container_width=True)
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
            st.info("Nenhum funcionario.")


elif menu == "Gerador de Escala":
    st.markdown("### Gerador de Escala")
    funcionarios = carregar_funcionarios()
    absenteismo = carregar_absenteismo()
    desempenho = carregar_desempenho()
    ativos = [f for f in funcionarios if f.get("status") == "Ativo"]
    tab1, tab2 = st.tabs(["Gerar Escala", "Anteriores"])
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
            st.warning("Com falta: **" + ", ".join(faltas_dia) + "**")
        st.markdown("Disponiveis: **" + str(len(disponiveis)) + "** de " + str(len(ativos)))
        usar_desemp = st.checkbox("Priorizar por nota de desempenho", value=False)
        if st.button("Sortear / Gerar Escala", type="primary", use_container_width=True):
            escala = []
            usados = []
            for pos in POSICOES:
                cands = [f for f in disponiveis if f["nome"] not in usados]
                if usar_desemp:
                    cn = []
                    for c in cands:
                        nota = 0
                        for d in desempenho:
                            if d.get("funcionario") == c["nome"] and d.get("posicao") == pos:
                                nota = d.get("nota", 0)
                                break
                        cn.append((c, nota))
                    cn.sort(key=lambda x: x[1], reverse=True)
                    cands = [c[0] for c in cn]
                else:
                    random.shuffle(cands)
                if cands:
                    ei = {"posicao": pos, "funcionario": cands[0]["nome"], "telefone": cands[0].get("telefone", ""), "tipo": cands[0].get("tipo", "")}
                    escala.append(ei)
                    usados.append(cands[0]["nome"])
            st.session_state["escala_temp"] = escala
        if "escala_temp" in st.session_state and st.session_state["escala_temp"]:
            esc = st.session_state["escala_temp"]
            st.markdown("---")
            st.markdown("#### Escala (editavel)")
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
                    tw = "*ESCALA EUA8 - " + data_esc_str + "*" + NL
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
            st.dataframe(pd.DataFrame(esel.get("escala", [])), use_container_width=True, hide_index=True)
            if st.button("Excluir Escala", type="secondary"):
                todas = carregar_escalas()
                todas = [x for x in todas if not (x.get("data") == esel.get("data") and x.get("gerada_em") == esel.get("gerada_em"))]
                salvar_escalas(todas)
                st.success("Excluida!")
                st.rerun()
        else:
            st.info("Nenhuma escala.")


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
                tipo_veic = st.selectbox("Tipo de Veiculo", TIPOS_VEICULO)
            with rm2:
                h_chegada = st.text_input("Horario Chegada (HH:MM)", placeholder="14:30")
                h_saida = st.text_input("Horario Saida (HH:MM)", placeholder="16:00")
                obs_mot = st.text_input("Observacoes", placeholder="Ex: 28 pallets, doca 3")
            foto_mot = st.camera_input("Foto do Veiculo (opcional)")
            btn_mot = st.form_submit_button("Registrar", use_container_width=True)
            if btn_mot:
                if nome_mot and placa_mot:
                    nm = {"nome": nome_mot, "placa": placa_mot.upper(), "tipo_veiculo": tipo_veic, "horario_chegada": h_chegada, "horario_saida": h_saida, "observacoes": obs_mot, "data_chegada": datetime.now(FUSO_BR).strftime("%Y-%m-%d"), "data_registro": datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M")}
                    if foto_mot:
                        nf = "mot_" + datetime.now(FUSO_BR).strftime("%Y%m%d_%H%M%S") + ".jpg"
                        cf = os.path.join(PASTA_MOTORISTAS, nf)
                        img = Image.open(foto_mot)
                        img.save(cf)
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
            ops_m = [m.get("nome", "") + " - " + m.get("placa", "") + " - " + m.get("data_chegada", "")[:10] for m in motoristas]
            sel_m = st.selectbox("Selecione", ops_m, key="sel_m_edit")
            idx_m = ops_m.index(sel_m)
            me = motoristas[idx_m]
            with st.form("form_edit_mot"):
                em1, em2 = st.columns(2)
                with em1:
                    enm = st.text_input("Nome", value=me.get("nome", ""))
                    epm = st.text_input("Placa", value=me.get("placa", ""))
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
                    motoristas[idx_m]["nome"] = enm
                    motoristas[idx_m]["placa"] = epm.upper()
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


elif menu == "Absenteismo":
    st.markdown("### Controle de Absenteismo")
    funcionarios = carregar_funcionarios()
    absenteismo = carregar_absenteismo()
    ativos = [f for f in funcionarios if f.get("status") == "Ativo"]
    tab1, tab2, tab3 = st.tabs(["Registrar Falta", "Historico", "Resumo"])
    with tab1:
        if ativos:
            with st.form("form_falta"):
                nomes_at = [f["nome"] for f in ativos]
                fa1, fa2 = st.columns(2)
                with fa1:
                    func_falta = st.selectbox("Funcionario", nomes_at)
                    data_falta = st.date_input("Data", value=date.today())
                with fa2:
                    motivo_falta = st.selectbox("Motivo", ["Falta sem justificativa", "Falta justificada", "Atestado medico", "Atraso", "Afastamento", "Ferias", "Folga", "Outro"])
                    obs_falta = st.text_input("Observacao")
                btn_falta = st.form_submit_button("Registrar Falta", use_container_width=True)
                if btn_falta:
                    ja = any(a.get("funcionario") == func_falta and a.get("data") == data_falta.strftime("%Y-%m-%d") for a in absenteismo)
                    if ja:
                        st.warning("Falta ja registrada.")
                    else:
                        nf = {"funcionario": func_falta, "data": data_falta.strftime("%Y-%m-%d"), "motivo": motivo_falta, "observacao": obs_falta, "registrado_em": datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M"), "registrado_por": st.session_state.get("nome_logado", "Admin")}
                        absenteismo.append(nf)
                        salvar_absenteismo(absenteismo)
                        st.success("Falta registrada: " + func_falta)
                        st.rerun()
        else:
            st.info("Cadastre funcionarios primeiro.")
    with tab2:
        if absenteismo:
            df_abs = pd.DataFrame(absenteismo)
            cols_a = ["funcionario", "data", "motivo", "observacao", "registrado_em"]
            cols_ok = [c for c in cols_a if c in df_abs.columns]
            st.dataframe(df_abs[cols_ok], use_container_width=True, hide_index=True)
            ops_a = [a.get("funcionario", "") + " - " + a.get("data", "") + " - " + a.get("motivo", "") for a in absenteismo]
            sel_a = st.selectbox("Selecione para excluir", ops_a, key="sel_a_edit")
            idx_a = ops_a.index(sel_a)
            if st.button("Excluir falta", type="secondary"):
                absenteismo.pop(idx_a)
                salvar_absenteismo(absenteismo)
                st.success("Excluido!")
                st.rerun()
        else:
            st.info("Nenhuma falta.")
    with tab3:
        if absenteismo and ativos:
            cont = {}
            for a in absenteismo:
                n = a.get("funcionario", "")
                cont[n] = cont.get(n, 0) + 1
            linhas = [{"Funcionario": f["nome"], "Total Faltas": cont.get(f["nome"], 0), "Tipo": f.get("tipo", "")} for f in ativos]
            df_res = pd.DataFrame(linhas).sort_values("Total Faltas", ascending=False)
            st.dataframe(df_res, use_container_width=True, hide_index=True)
            st.bar_chart(df_res.set_index("Funcionario")["Total Faltas"])
        else:
            st.info("Sem dados.")


elif menu == "Desempenho por Funcao":
    st.markdown("### Desempenho por Funcao")
    funcionarios = carregar_funcionarios()
    desempenho = carregar_desempenho()
    ativos = [f for f in funcionarios if f.get("status") == "Ativo"]
    tab1, tab2, tab3 = st.tabs(["Avaliar", "Ranking", "Historico"])
    with tab1:
        if ativos:
            with st.form("form_desemp"):
                dp1, dp2 = st.columns(2)
                with dp1:
                    func_aval = st.selectbox("Funcionario", [f["nome"] for f in ativos])
                    posicao_aval = st.selectbox("Posicao", POSICOES)
                with dp2:
                    nota_aval = st.slider("Nota (1 a 5)", min_value=1, max_value=5, value=3)
                    obs_aval = st.text_input("Observacao")
                st.markdown("**1**=Iniciante | **2**=Desenvolvimento | **3**=Bom | **4**=Muito bom | **5**=Excelente")
                btn_aval = st.form_submit_button("Salvar", use_container_width=True)
                if btn_aval:
                    encontrou = False
                    for i, d in enumerate(desempenho):
                        if d.get("funcionario") == func_aval and d.get("posicao") == posicao_aval:
                            desempenho[i]["nota"] = nota_aval
                            desempenho[i]["observacao"] = obs_aval
                            desempenho[i]["atualizado_em"] = datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M")
                            encontrou = True
                            break
                    if not encontrou:
                        na = {"funcionario": func_aval, "posicao": posicao_aval, "nota": nota_aval, "observacao": obs_aval, "atualizado_em": datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M")}
                        desempenho.append(na)
                    salvar_desempenho(desempenho)
                    st.success(func_aval + " nota " + str(nota_aval) + " em " + posicao_aval)
                    st.rerun()
        else:
            st.info("Cadastre funcionarios.")
    with tab2:
        if desempenho:
            pos_sel = st.selectbox("Funcao", POSICOES)
            np_ = [d for d in desempenho if d.get("posicao") == pos_sel]
            if np_:
                np_ = sorted(np_, key=lambda x: x.get("nota", 0), reverse=True)
                lr = [{"#": i+1, "Funcionario": n.get("funcionario", ""), "Nota": n.get("nota", 0), "Obs": n.get("observacao", "")} for i, n in enumerate(np_)]
                df_r = pd.DataFrame(lr)
                st.dataframe(df_r, use_container_width=True, hide_index=True)
                st.bar_chart(df_r.set_index("Funcionario")["Nota"])
            else:
                st.info("Nenhuma avaliacao para " + pos_sel)
        else:
            st.info("Nenhuma avaliacao.")
    with tab3:
        if desempenho:
            df_d = pd.DataFrame(desempenho)
            st.dataframe(df_d, use_container_width=True, hide_index=True)
            ops_d = [d.get("funcionario", "") + " - " + d.get("posicao", "") + " - " + str(d.get("nota", 0)) for d in desempenho]
            sel_d = st.selectbox("Excluir", ops_d, key="sel_d_ex")
            idx_d = ops_d.index(sel_d)
            if st.button("Excluir", type="secondary", key="btn_ex_d"):
                desempenho.pop(idx_d)
                salvar_desempenho(desempenho)
                st.success("Excluido!")
                st.rerun()
        else:
            st.info("Nenhuma avaliacao.")


elif menu == "Forecast / Volume":
    st.markdown("### Forecast / Volume")
    forecasts = carregar_forecast()
    tab1, tab2, tab3 = st.tabs(["Manual", "Upload", "Historico"])
    with tab1:
        with st.form("form_fc"):
            fc1, fc2 = st.columns(2)
            with fc1:
                data_fc = st.date_input("Data", value=date.today())
                volume_fc = st.number_input("Volume Previsto", min_value=0, max_value=50000, value=0, step=100)
            with fc2:
                obs_fc = st.text_input("Observacao", placeholder="Ex: Pico de segunda")
            btn_fc = st.form_submit_button("Salvar", use_container_width=True)
            if btn_fc:
                nfc = {"data": data_fc.strftime("%Y-%m-%d"), "volume": volume_fc, "observacao": obs_fc, "origem": "Manual", "cadastrado_em": datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M")}
                forecasts.append(nfc)
                salvar_forecast(forecasts)
                st.success("Forecast salvo!")
                st.rerun()
    with tab2:
        st.markdown("Formato: colunas **data** e **volume**")
        arq_fc = st.file_uploader("Arquivo CSV ou Excel", type=["csv", "xlsx"])
        if arq_fc:
            try:
                if arq_fc.name.endswith(".csv"):
                    df_up = pd.read_csv(arq_fc)
                else:
                    df_up = pd.read_excel(arq_fc)
                st.dataframe(df_up, use_container_width=True, hide_index=True)
                if st.button("Importar", type="primary"):
                    for _, row in df_up.iterrows():
                        nfc = {"data": str(row.get("data", "")), "volume": int(row.get("volume", 0)), "observacao": str(row.get("observacao", "")), "origem": "Upload", "cadastrado_em": datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M")}
                        forecasts.append(nfc)
                    salvar_forecast(forecasts)
                    st.success(str(len(df_up)) + " importados!")
                    st.rerun()
            except Exception as e:
                st.error("Erro: " + str(e))
    with tab3:
        if forecasts:
            df_fc = pd.DataFrame(forecasts)
            cols_fc = ["data", "volume", "observacao", "origem"]
            cols_ok = [c for c in cols_fc if c in df_fc.columns]
            st.dataframe(df_fc[cols_ok], use_container_width=True, hide_index=True)
            ops_fc = [f.get("data", "") + " - " + str(f.get("volume", 0)) + " pac" for f in forecasts]
            sel_fc = st.selectbox("Selecione", ops_fc, key="sel_fc_ex")
            idx_fc = ops_fc.index(sel_fc)
            if st.button("Excluir forecast", type="secondary"):
                forecasts.pop(idx_fc)
                salvar_forecast(forecasts)
                st.success("Excluido!")
                st.rerun()
        else:
            st.info("Nenhum forecast.")


elif menu == "Validacao por Foto (IA)":
    st.markdown("### Validacao por Foto (IA)")
    validacoes = carregar_validacoes()
    tab1, tab2, tab3 = st.tabs(["Nova Validacao", "Contagem Manual + Comparativo", "Historico"])
    with tab1:
        tipo_val = st.selectbox("Tipo de Validacao", TIPOS_VALIDACAO)
        foto_val = st.camera_input("Tirar Foto")
        if foto_val:
            img = Image.open(foto_val)
            st.image(img, caption="Foto capturada", use_container_width=True)
            if yolo_ok:
                try:
                    modelo = YOLO("yolov8x.pt")
                    temp_path = os.path.join(PASTA_FOTOS, "temp_val.jpg")
                    img.save(temp_path)
                    resultados = modelo(temp_path)
                    r = resultados
                    img_result = Image.fromarray(r.plot()[:, :, ::-1])
                    st.image(img_result, caption="Resultado IA", use_container_width=True)
                    contagem_ia = {}
                    for box in r.boxes:
                        cls_id = int(box.cls)
                        cls_name = r.names[cls_id]
                        contagem_ia[cls_name] = contagem_ia.get(cls_name, 0) + 1
                    total_ia = sum(contagem_ia.values())
                    st.markdown("**Total objetos (IA): " + str(total_ia) + "**")
                    if contagem_ia:
                        df_ia = pd.DataFrame(list(contagem_ia.items()), columns=["Objeto", "Quantidade"])
                        st.dataframe(df_ia, use_container_width=True, hide_index=True)
                    if st.button("Salvar Validacao IA", type="primary"):
                        nv = {"tipo": tipo_val, "data": datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M"), "total_objetos_ia": total_ia, "detalhes_ia": contagem_ia, "total_objetos_manual": 0, "detalhes_manual": {}, "registrado_por": st.session_state.get("nome_logado", "Admin")}
                        validacoes.append(nv)
                        salvar_validacoes(validacoes)
                        st.success("Validacao salva!")
                        st.rerun()
                except Exception as e:
                    st.error("Erro IA: " + str(e))
            else:
                st.warning("YOLO nao instalado. Modo demonstracao ativo.")
                st.info("Para IA real, rode: pip install ultralytics")
                demo_objs = {"caixa": random.randint(15, 40), "pallet": random.randint(1, 5)}
                total_demo = sum(demo_objs.values())
                st.markdown("**" + str(total_demo) + " objeto(s) (simulacao)**")
                df_demo = pd.DataFrame(list(demo_objs.items()), columns=["Objeto", "Quantidade"])
                st.dataframe(df_demo, use_container_width=True, hide_index=True)
                if st.button("Salvar (demo)", type="primary"):
                    nv = {"tipo": tipo_val, "data": datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M"), "total_objetos_ia": total_demo, "detalhes_ia": demo_objs, "total_objetos_manual": 0, "detalhes_manual": {}, "modo": "demo", "registrado_por": st.session_state.get("nome_logado", "Admin")}
                    validacoes.append(nv)
                    salvar_validacoes(validacoes)
                    st.success("Salvo (demo)!")
                    st.rerun()
    with tab2:
        st.markdown("#### Contagem Manual da Equipe")
        with st.form("form_manual_val"):
            tipo_val_m = st.selectbox("Tipo", TIPOS_VALIDACAO, key="tipo_val_m")
            st.markdown("Preencha a contagem real da equipe:")
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                qt_caixa = st.number_input("Caixas", min_value=0, value=0, step=1)
            with mc2:
                qt_pallet = st.number_input("Pallets", min_value=0, value=0, step=1)
            with mc3:
                qt_outros = st.number_input("Outros", min_value=0, value=0, step=1)
            obs_val = st.text_input("Observacao")
            btn_manual = st.form_submit_button("Salvar Contagem Manual", use_container_width=True)
            if btn_manual:
                det_m = {"caixa": qt_caixa, "pallet": qt_pallet, "outros": qt_outros}
                tot_m = qt_caixa + qt_pallet + qt_outros
                nv = {"tipo": tipo_val_m, "data": datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M"), "total_objetos_ia": 0, "detalhes_ia": {}, "total_objetos_manual": tot_m, "detalhes_manual": det_m, "observacao": obs_val, "registrado_por": st.session_state.get("nome_logado", "Admin")}
                validacoes.append(nv)
                salvar_validacoes(validacoes)
                st.success("Contagem manual salva: " + str(tot_m) + " objetos")
                st.rerun()
        st.markdown("---")
        st.markdown("#### Comparativo IA vs Equipe")
        if validacoes:
            uv = sorted(validacoes, key=lambda x: x.get("data", ""), reverse=True)[:10]
            linhas_comp = []
            for v in uv:
                lc = {"Tipo": v.get("tipo", ""), "Data": v.get("data", "")[:16], "IA": v.get("total_objetos_ia", 0), "Equipe": v.get("total_objetos_manual", 0)}
                lc["Diferenca"] = lc["IA"] - lc["Equipe"]
                linhas_comp.append(lc)
            df_comp = pd.DataFrame(linhas_comp)
            st.dataframe(df_comp, use_container_width=True, hide_index=True)
            st.markdown("**Detalhamento por item (ultima validacao):**")
            if uv:
                ult = uv
                di = ult.get("detalhes_ia", {})
                dm = ult.get("detalhes_manual", {})
                todos_itens = set(list(di.keys()) + list(dm.keys()))
                if todos_itens:
                    ld = [{"Item": it, "IA": di.get(it, 0), "Equipe": dm.get(it, 0), "Diferenca": di.get(it, 0) - dm.get(it, 0)} for it in sorted(todos_itens)]
                    st.dataframe(pd.DataFrame(ld), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma validacao.")
    with tab3:
        if validacoes:
            vs = sorted(validacoes, key=lambda x: x.get("data", ""), reverse=True)
            lh = []
            for v in vs:
                lh.append({"Tipo": v.get("tipo", ""), "Data": v.get("data", "")[:16], "IA": v.get("total_objetos_ia", 0), "Equipe": v.get("total_objetos_manual", 0), "Por": v.get("registrado_por", "")})
            st.dataframe(pd.DataFrame(lh), use_container_width=True, hide_index=True)
            ops_v = [v.get("tipo", "") + " - " + v.get("data", "")[:16] for v in vs]
            sel_v = st.selectbox("Excluir", ops_v, key="sel_v_ex")
            idx_v = ops_v.index(sel_v)
            if st.button("Excluir validacao", type="secondary"):
                todas_v = carregar_validacoes()
                todas_v_s = sorted(todas_v, key=lambda x: x.get("data", ""), reverse=True)
                if idx_v < len(todas_v_s):
                    todas_v_s.pop(idx_v)
                    salvar_validacoes(todas_v_s)
                    st.success("Excluido!")
                    st.rerun()
        else:
            st.info("Nenhuma validacao.")


elif menu == "Scanner QR/Barcode":
    st.markdown("### Scanner QR / Codigo de Barras")
    if "scan_lista" not in st.session_state:
        st.session_state["scan_lista"] = []
    tab1, tab2 = st.tabs(["Escanear", "Lista / Exportar"])
    with tab1:
        st.markdown("Use a camera ou digite o codigo manualmente:")
        with st.form("form_scan"):
            sc1, sc2 = st.columns(2)
            with sc1:
                codigo = st.text_input("Codigo (manual ou scanner)", placeholder="Escaneie ou digite aqui")
            with sc2:
                destino = st.text_input("Destino", placeholder="Ex: Doca 3, Rua A")
            obs_scan = st.text_input("Observacao")
            btn_scan = st.form_submit_button("Registrar", use_container_width=True)
            if btn_scan:
                if codigo:
                    item = {"codigo": codigo, "destino": destino, "observacao": obs_scan, "horario": datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M:%S"), "registrado_por": st.session_state.get("nome_logado", "Admin")}
                    st.session_state["scan_lista"].append(item)
                    st.success("Registrado: " + codigo)
                else:
                    st.error("Digite um codigo!")
        st.markdown("**Total escaneados:** " + str(len(st.session_state["scan_lista"])))
    with tab2:
        if st.session_state["scan_lista"]:
            df_scan = pd.DataFrame(st.session_state["scan_lista"])
            st.dataframe(df_scan, use_container_width=True, hide_index=True)
            buf = io.BytesIO()
            df_scan.to_excel(buf, index=False, engine="openpyxl")
            buf.seek(0)
            st.download_button("Baixar Excel", data=buf, file_name="scan_eau8_" + datetime.now(FUSO_BR).strftime("%Y%m%d_%H%M") + ".xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            if st.button("Limpar Lista", type="secondary"):
                st.session_state["scan_lista"] = []
                st.rerun()
        else:
            st.info("Nenhum item escaneado.")


elif menu == "Enviar por WhatsApp":
    st.markdown("### Enviar por WhatsApp")
    tab1, tab2 = st.tabs(["Enviar Mensagem", "Enviar Escala"])
    with tab1:
        st.markdown("#### Enviar mensagem personalizada")
        with st.form("form_wpp"):
            telefone_wpp = st.text_input("Telefone (com DDD e DDI)", placeholder="5511999999999")
            msg_wpp = st.text_area("Mensagem", height=150)
            btn_wpp = st.form_submit_button("Gerar Link WhatsApp", use_container_width=True)
            if btn_wpp:
                if telefone_wpp and msg_wpp:
                    tel_limpo = telefone_wpp.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                    link = "https://wa.me/" + tel_limpo + "?text=" + msg_wpp.replace(" ", "%20").replace(chr(10), "%0A")
                    st.markdown("**Clique no link para enviar:**")
                    st.markdown("[Abrir WhatsApp](" + link + ")")
                    st.code(link)
                else:
                    st.error("Preencha telefone e mensagem!")
    with tab2:
        st.markdown("#### Enviar ultima escala")
        texto_esc = st.session_state.get("ultima_escala_wpp", "")
        if texto_esc:
            st.text_area("Texto da escala", value=texto_esc, height=200, disabled=True)
            tel_esc = st.text_input("Telefone destino", placeholder="5511999999999", key="tel_esc_wpp")
            if st.button("Gerar Link", type="primary"):
                if tel_esc:
                    tel_l = tel_esc.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                    link_e = "https://wa.me/" + tel_l + "?text=" + texto_esc.replace(" ", "%20").replace(chr(10), "%0A")
                    st.markdown("[Abrir WhatsApp](" + link_e + ")")
                    st.code(link_e)
                else:
                    st.error("Preencha o telefone!")
        else:
            st.info("Gere uma escala primeiro.")


elif menu == "Relatorios":
    st.markdown("### Relatorios")
    tab1, tab2, tab3 = st.tabs(["Consolidado", "Por Periodo", "Exportar"])
    with tab1:
        st.markdown("#### Relatorio Consolidado")
        funcionarios = carregar_funcionarios()
        validacoes = carregar_validacoes()
        escalas = carregar_escalas()
        motoristas = carregar_motoristas()
        forecasts = carregar_forecast()
        absenteismo = carregar_absenteismo()
        st.markdown("- **Funcionarios:** " + str(len(funcionarios)))
        st.markdown("- **Escalas:** " + str(len(escalas)))
        st.markdown("- **Motoristas:** " + str(len(motoristas)))
        st.markdown("- **Validacoes:** " + str(len(validacoes)))
        st.markdown("- **Forecasts:** " + str(len(forecasts)))
        st.markdown("- **Faltas registradas:** " + str(len(absenteismo)))
    with tab2:
        st.markdown("#### Filtrar por Periodo")
        rp1, rp2 = st.columns(2)
        with rp1:
            dt_ini = st.date_input("Data Inicio", value=date.today() - timedelta(days=7), key="dt_ini_rel")
        with rp2:
            dt_fim = st.date_input("Data Fim", value=date.today(), key="dt_fim_rel")
        di = dt_ini.strftime("%Y-%m-%d")
        df_ = dt_fim.strftime("%Y-%m-%d")
        validacoes = carregar_validacoes()
        val_per = [v for v in validacoes if di <= v.get("data", "")[:10] <= df_]
        motoristas = carregar_motoristas()
        mot_per = [m for m in motoristas if di <= m.get("data_chegada", "")[:10] <= df_ or di <= m.get("data_registro", "")[:10] <= df_]
        absenteismo = carregar_absenteismo()
        abs_per = [a for a in absenteismo if di <= a.get("data", "") <= df_]
        st.markdown("**Periodo:** " + dt_ini.strftime("%d/%m/%Y") + " a " + dt_fim.strftime("%d/%m/%Y"))
        st.markdown("- Validacoes: " + str(len(val_per)))
        st.markdown("- Motoristas: " + str(len(mot_per)))
        st.markdown("- Faltas: " + str(len(abs_per)))
        if val_per:
            st.markdown("**Validacoes:**")
            lv = [{"Tipo": v.get("tipo", ""), "Data": v.get("data", "")[:16], "IA": v.get("total_objetos_ia", 0), "Equipe": v.get("total_objetos_manual", 0)} for v in val_per]
            st.dataframe(pd.DataFrame(lv), use_container_width=True, hide_index=True)
        if mot_per:
            st.markdown("**Motoristas:**")
            lm = [{"Nome": m.get("nome", ""), "Placa": m.get("placa", ""), "Veiculo": m.get("tipo_veiculo", ""), "Chegada": m.get("horario_chegada", "")} for m in mot_per]
            st.dataframe(pd.DataFrame(lm), use_container_width=True, hide_index=True)
    with tab3:
        st.markdown("#### Exportar Dados")
        tipo_exp = st.selectbox("Selecione", ["Funcionarios", "Escalas", "Motoristas", "Validacoes", "Forecast", "Absenteismo"])
        if st.button("Gerar Excel", type="primary"):
            dados_map = {"Funcionarios": carregar_funcionarios(), "Escalas": carregar_escalas(), "Motoristas": carregar_motoristas(), "Validacoes": carregar_validacoes(), "Forecast": carregar_forecast(), "Absenteismo": carregar_absenteismo()}
            dados = dados_map.get(tipo_exp, [])
            if dados:
                df_exp = pd.DataFrame(dados)
                buf = io.BytesIO()
                df_exp.to_excel(buf, index=False, engine="openpyxl")
                buf.seek(0)
                st.download_button("Baixar " + tipo_exp, data=buf, file_name=tipo_exp.lower() + "_eau8.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.info("Sem dados para exportar.")


elif menu == "Configuracoes":
    st.markdown("### Configuracoes")
    tab1, tab2, tab3 = st.tabs(["Site", "Sistema", "Ajuda"])
    with tab1:
        st.markdown("#### Informacoes do Site")
        st.markdown("- **Site:** EUA8")
        st.markdown("- **Operacao:** First Mile / Cross Dock")
        st.markdown("- **Turno:** Tarde (14h-20h)")
        st.markdown("- **Regiao:** Sao Paulo")
    with tab2:
        st.markdown("#### Sobre o Sistema")
        st.markdown("- **App:** EUA8 Manager")
        st.markdown("- **Versao:** 7.0")
        st.markdown("- **Desenvolvido por:** Fernando Junior")
        st.markdown("- **Stack:** Python + Streamlit")
    with tab3:
        st.markdown("#### Ajuda")
        st.markdown("Duvidas? Fale com o administrador.")
        st.markdown("**Funcionalidades:**")
        st.markdown("- Dashboard com metricas e graficos")
        st.markdown("- Cadastro e gestao de funcionarios")
        st.markdown("- Gerador de escala automatico")
        st.markdown("- Registro de motoristas com foto")
        st.markdown("- Forecast / Volume previsto")
        st.markdown("- Validacao por foto com IA (YOLO)")
        st.markdown("- Scanner QR Code / Codigo de barras")
        st.markdown("- Envio por WhatsApp")
        st.markdown("- Controle de absenteismo")
        st.markdown("- Desempenho por funcao")
        st.markdown("- Relatorios e exportacao")
        st.markdown("- Gerenciamento de usuarios")


elif menu == "Gerenciar Usuarios":
    st.markdown("### Gerenciar Usuarios")
    usuarios = carregar_usuarios()
    tab1, tab2, tab3 = st.tabs(["Novo Usuario", "Lista", "Remover"])
    with tab1:
        with st.form("form_new_user"):
            nu1, nu2 = st.columns(2)
            with nu1:
                new_user = st.text_input("Usuario (login)")
                new_nome = st.text_input("Nome Completo")
            with nu2:
                new_senha = st.text_input("Senha", type="password")
                new_perfil = st.selectbox("Perfil", ["Admin", "Supervisor", "Operador", "Visualizador"])
            btn_nu = st.form_submit_button("Criar Usuario", use_container_width=True)
            if btn_nu:
                if new_user and new_nome and new_senha:
                    ja_tem = any(u["usuario"] == new_user.lower().strip() for u in usuarios)
                    if ja_tem:
                        st.warning("Usuario ja existe!")
                    else:
                        nvu = {"usuario": new_user.lower().strip(), "senha": hash_senha(new_senha), "nome": new_nome, "perfil": new_perfil, "status": "Ativo", "criado_em": datetime.now(FUSO_BR).strftime("%Y-%m-%d")}
                        usuarios.append(nvu)
                        salvar_usuarios(usuarios)
                        st.success("Usuario " + new_user + " criado!")
                        st.rerun()
                else:
                    st.error("Preencha todos os campos!")
    with tab2:
        if usuarios:
            lu = [{"Usuario": u["usuario"], "Nome": u["nome"], "Perfil": u["perfil"], "Status": u.get("status", "Ativo")} for u in usuarios]
            st.dataframe(pd.DataFrame(lu), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum usuario.")
    with tab3:
        if len(usuarios) > 1:
            outros = [u["usuario"] + " - " + u["nome"] + " (" + u["perfil"] + ")" for u in usuarios if u["usuario"] != st.session_state.get("usuario_logado", "")]
            if outros:
                sel_rem = st.selectbox("Selecione usuario para remover", outros, key="sel_rem_u")
                if st.button("Remover Usuario", type="secondary"):
                    user_rem = sel_rem.split(" - ")
                    usuarios = [u for u in usuarios if u["usuario"] != user_rem]
                    salvar_usuarios(usuarios)
                    st.success("Removido!")
                    st.rerun()
            else:
                st.info("Nenhum usuario para remover.")
        else:
            st.warning("Voce e o unico admin.")


st.markdown("---")
st.markdown("<div style='text-align:center;color:#666;font-size:0.8rem;'>EUA8 Manager v7.0 | First Mile Operations | Amazon Logistics | " + datetime.now(FUSO_BR).strftime("%Y") + "</div>", unsafe_allow_html=True)


            st.info("Nenhum motorista.")

