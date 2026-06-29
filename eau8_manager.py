
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import pytz
import psycopg2

FUSO_BR = pytz.timezone("America/Sao_Paulo")
SITE = "EUA8"
TIPOS_VEICULO = ["Carreta (28 pallets)", "Truck (16 pallets)", "VUC (6 pallets)", "3/4", "Fiorino", "Van", "Bitruck", "Outro"]

# ============================================================
# TRADUCOES COMPLETAS
# ============================================================

T = {
    "PT-BR": {
        "titulo_op": "OPERACAO FIRST MILE",
        "perfil_lider": "Lider",
        "perfil_otr": "OTR",
        "perfil_yard": "Yard",
        "perfil_motorista": "Motorista",
        "atualizar": "Atualizar",
        "menu_dashboard": "Control Desk",
        "menu_add_drivers": "Add Drivers",
        "menu_yard_control": "Yard Control",
        "menu_mural": "Mural",
        "menu_historico": "Historico",
        "menu_editar": "Editar Registros",
        "status_agora": "Status Agora",
        "total_previsto": "Total Previsto",
        "chegaram": "Chegaram",
        "no_patio": "No Patio",
        "despachados": "Despachados",
        "faltam_chegar": "Faltam Chegar",
        "fora_lista": "Fora da Lista",
        "primeiro_veiculo": "PRIMEIRO VEICULO",
        "tempo_sem_chegar": "TEMPO SEM CHEGAR",
        "media_patio": "MEDIA NO PATIO",
        "progresso": "PROGRESSO DESPACHO",
        "faltam": "Faltam",
        "de": "de",
        "todos_chegaram": "Todos ja chegaram",
        "patio_vazio": "Patio vazio",
        "tab_rt": "Real-Time",
        "tab_diario": "Diario",
        "tab_semanal": "Semanal",
        "tab_mensal": "Mensal",
        "sel_data": "Data:",
        "nao_vieram": "Nao Vieram",
        "primeiro": "1o Veiculo",
        "ultimo": "Ultimo",
        "tempo_medio": "Tempo Medio",
        "exportar": "Exportar CSV",
        "sem_dados": "Sem dados.",
        "modelo_plan": "Modelo da planilha:",
        "colunas": "Colunas: nome | tipo_veiculo | placa | telefone",
        "obrigatoria": "Apenas nome e obrigatoria.",
        "categoria": "Categoria",
        "data_coleta": "Data",
        "importar": "Importar",
        "importados": "importados!",
        "registrar_chegada": "Registrar Chegada",
        "motorista_chegou": "Motorista:",
        "faixa": "Faixa",
        "hora": "Hora",
        "btn_chegou": "CHEGOU",
        "todos_yard": "Todos ja chegaram",
        "manual_titulo": "Cadastro Manual (Fora da Lista)",
        "nome": "Nome",
        "veiculo": "Veiculo",
        "telefone": "Telefone",
        "placa": "Placa",
        "obs": "Observacao",
        "registrar": "Registrar",
        "registrar_saida": "Registrar Saida",
        "motorista_saindo": "Motorista saindo:",
        "hora_saida": "Hora saida",
        "btn_saiu": "SAIU",
        "nenhum_patio": "Nenhum no patio.",
        "msg_rapida": "Mensagem:",
        "prioridade": "Prioridade",
        "enviar": "Enviar",
        "nenhuma_msg": "Nenhuma mensagem hoje.",
        "historico": "Historico",
        "nenhum_registro": "Sem registros.",
        "editar_titulo": "Editar Registro",
        "selecione": "Selecione:",
        "salvar": "Salvar",
        "salvo": "Salvo!",
        "visto_titulo": "Confirmar Presenca",
        "visto_instrucao": "Digite seu nome para dar o visto:",
        "visto_btn": "CONFIRMAR PRESENCA",
        "visto_ok": "Presenca confirmada!",
        "visto_erro": "Nome nao encontrado.",
        "visto_ja": "Ja confirmado anteriormente.",
        "desenvolvido": "Desenvolvido por Fernando Junior | Lider EUA8",
        "erro": "Erro:",
    },
    "ENG": {
        "titulo_op": "OPERATION FIRST MILE",
        "perfil_lider": "Leader",
        "perfil_otr": "OTR",
        "perfil_yard": "Yard",
        "perfil_motorista": "Driver",
        "atualizar": "Refresh",
        "menu_dashboard": "Control Desk",
        "menu_add_drivers": "Add Drivers",
        "menu_yard_control": "Yard Control",
        "menu_mural": "Board",
        "menu_historico": "History",
        "menu_editar": "Edit Records",
        "status_agora": "Current Status",
        "total_previsto": "Expected",
        "chegaram": "Arrived",
        "no_patio": "In Yard",
        "despachados": "Dispatched",
        "faltam_chegar": "Pending",
        "fora_lista": "Off-List",
        "primeiro_veiculo": "FIRST VEHICLE",
        "tempo_sem_chegar": "TIME W/O ARRIVAL",
        "media_patio": "AVG IN YARD",
        "progresso": "DISPATCH PROGRESS",
        "faltam": "Pending",
        "de": "of",
        "todos_chegaram": "All arrived",
        "patio_vazio": "Yard empty",
        "tab_rt": "Real-Time",
        "tab_diario": "Daily",
        "tab_semanal": "Weekly",
        "tab_mensal": "Monthly",
        "sel_data": "Date:",
        "nao_vieram": "No Show",
        "primeiro": "1st Vehicle",
        "ultimo": "Last",
        "tempo_medio": "Avg Time",
        "exportar": "Export CSV",
        "sem_dados": "No data.",
        "modelo_plan": "Spreadsheet template:",
        "colunas": "Columns: nome | tipo_veiculo | placa | telefone",
        "obrigatoria": "Only nome is required.",
        "categoria": "Category",
        "data_coleta": "Date",
        "importar": "Import",
        "importados": "imported!",
        "registrar_chegada": "Register Arrival",
        "motorista_chegou": "Driver:",
        "faixa": "Lane",
        "hora": "Time",
        "btn_chegou": "ARRIVED",
        "todos_yard": "All arrived",
        "manual_titulo": "Manual Entry (Off-List)",
        "nome": "Name",
        "veiculo": "Vehicle",
        "telefone": "Phone",
        "placa": "Plate",
        "obs": "Notes",
        "registrar": "Register",
        "registrar_saida": "Register Departure",
        "motorista_saindo": "Departing:",
        "hora_saida": "Departure time",
        "btn_saiu": "DEPARTED",
        "nenhum_patio": "No one in yard.",
        "msg_rapida": "Message:",
        "prioridade": "Priority",
        "enviar": "Send",
        "nenhuma_msg": "No messages today.",
        "historico": "History",
        "nenhum_registro": "No records.",
        "editar_titulo": "Edit Record",
        "selecione": "Select:",
        "salvar": "Save",
        "salvo": "Saved!",
        "visto_titulo": "Confirm Presence",
        "visto_instrucao": "Type your name to check in:",
        "visto_btn": "CONFIRM",
        "visto_ok": "Confirmed!",
        "visto_erro": "Name not found.",
        "visto_ja": "Already confirmed.",
        "desenvolvido": "Developed by Fernando Junior | Leader EUA8",
        "erro": "Error:",
    },
    "ESP": {
        "titulo_op": "OPERACION FIRST MILE",
        "perfil_lider": "Lider",
        "perfil_otr": "OTR",
        "perfil_yard": "Yard",
        "perfil_motorista": "Conductor",
        "atualizar": "Actualizar",
        "menu_dashboard": "Control Desk",
        "menu_add_drivers": "Add Drivers",
        "menu_yard_control": "Yard Control",
        "menu_mural": "Mural",
        "menu_historico": "Historial",
        "menu_editar": "Editar Registros",
        "status_agora": "Estado Actual",
        "total_previsto": "Previsto",
        "chegaram": "Llegaron",
        "no_patio": "En Patio",
        "despachados": "Despachados",
        "faltam_chegar": "Faltan",
        "fora_lista": "Fuera de Lista",
        "primeiro_veiculo": "PRIMER VEHICULO",
        "tempo_sem_chegar": "TIEMPO SIN LLEGAR",
        "media_patio": "PROMEDIO EN PATIO",
        "progresso": "PROGRESO DESPACHO",
        "faltam": "Faltan",
        "de": "de",
        "todos_chegaram": "Todos llegaron",
        "patio_vazio": "Patio vacio",
        "tab_rt": "Real-Time",
        "tab_diario": "Diario",
        "tab_semanal": "Semanal",
        "tab_mensal": "Mensual",
        "sel_data": "Fecha:",
        "nao_vieram": "No Vinieron",
        "primeiro": "1er Vehiculo",
        "ultimo": "Ultimo",
        "tempo_medio": "Tiempo Promedio",
        "exportar": "Exportar CSV",
        "sem_dados": "Sin datos.",
        "modelo_plan": "Modelo planilla:",
        "colunas": "Columnas: nome | tipo_veiculo | placa | telefone",
        "obrigatoria": "Solo nome es obligatorio.",
        "categoria": "Categoria",
        "data_coleta": "Fecha",
        "importar": "Importar",
        "importados": "importados!",
        "registrar_chegada": "Registrar Llegada",
        "motorista_chegou": "Conductor:",
        "faixa": "Carril",
        "hora": "Hora",
        "btn_chegou": "LLEGO",
        "todos_yard": "Todos llegaron",
        "manual_titulo": "Registro Manual (Fuera de Lista)",
        "nome": "Nombre",
        "veiculo": "Vehiculo",
        "telefone": "Telefono",
        "placa": "Placa",
        "obs": "Obs",
        "registrar": "Registrar",
        "registrar_saida": "Registrar Salida",
        "motorista_saindo": "Saliendo:",
        "hora_saida": "Hora salida",
        "btn_saiu": "SALIO",
        "nenhum_patio": "Nadie en patio.",
        "msg_rapida": "Mensaje:",
        "prioridade": "Prioridad",
        "enviar": "Enviar",
        "nenhuma_msg": "Sin mensajes hoy.",
        "historico": "Historial",
        "nenhum_registro": "Sin registros.",
        "editar_titulo": "Editar Registro",
        "selecione": "Seleccione:",
        "salvar": "Guardar",
        "salvo": "Guardado!",
        "visto_titulo": "Confirmar Presencia",
        "visto_instrucao": "Escriba su nombre:",
        "visto_btn": "CONFIRMAR",
        "visto_ok": "Confirmado!",
        "visto_erro": "No encontrado.",
        "visto_ja": "Ya confirmado.",
        "desenvolvido": "Desarrollado por Fernando Junior | Lider EUA8",
        "erro": "Error:",
    }
}

# ============================================================
# BANCO DE DADOS
# ============================================================

def get_conn():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        port=st.secrets["DB_PORT"],
        dbname=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASS"]
    )

def db_query(sql, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    cols = [desc[0] for desc in cur.description] if cur.description else []
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(zip(cols, r)) for r in rows]

def db_exec(sql, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    conn.commit()
    cur.close()
    conn.close()

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS motoristas (
        id SERIAL PRIMARY KEY, nome TEXT, placa TEXT, tipo_veiculo TEXT,
        telefone TEXT, observacao TEXT, horario_chegada TEXT, horario_saida TEXT,
        observacoes TEXT, destino TEXT, data_chegada TEXT, data_registro TEXT,
        importado BOOLEAN DEFAULT FALSE, categoria TEXT DEFAULT 'PICKUP',
        status_yard TEXT DEFAULT 'aguardando', faixa TEXT DEFAULT '',
        visto BOOLEAN DEFAULT FALSE)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS mural (
        id SERIAL PRIMARY KEY, autor TEXT, perfil TEXT, mensagem TEXT,
        tipo TEXT DEFAULT 'info', data_hora TEXT, data TEXT)""")
    conn.commit()
    cur.close()
    conn.close()

try:
    init_db()
except Exception:
    pass

# ============================================================
# FUNCOES AUXILIARES
# ============================================================

def carregar_motoristas():
    try:
        return db_query("SELECT * FROM motoristas ORDER BY id DESC")
    except Exception:
        return []

def salvar_motorista(m):
    db_exec("""INSERT INTO motoristas (nome,placa,tipo_veiculo,telefone,observacao,
        horario_chegada,horario_saida,observacoes,destino,data_chegada,
        data_registro,importado,categoria,status_yard,faixa,visto)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (str(m.get("nome","")), str(m.get("placa","")), str(m.get("tipo_veiculo","")),
         str(m.get("telefone","")), str(m.get("observacao","")),
         str(m.get("horario_chegada","")), str(m.get("horario_saida","")),
         str(m.get("observacoes","")), str(m.get("destino","")),
         str(m.get("data_chegada","")), str(m.get("data_registro","")),
         bool(m.get("importado",False)), str(m.get("categoria","PICKUP")),
         str(m.get("status_yard","aguardando")), str(m.get("faixa","")),
         bool(m.get("visto",False))))

def atualizar_mot(mid, dados):
    sets = ", ".join([k+"=%s" for k in dados.keys()])
    db_exec("UPDATE motoristas SET "+sets+" WHERE id=%s", list(dados.values())+[mid])

def salvar_msg(msg):
    db_exec("INSERT INTO mural (autor,perfil,mensagem,tipo,data_hora,data) VALUES (%s,%s,%s,%s,%s,%s)",
        (msg["autor"],msg["perfil"],msg["mensagem"],msg.get("tipo","info"),msg["data_hora"],msg["data"]))

def carregar_mural(d):
    try:
        return db_query("SELECT * FROM mural WHERE data=%s ORDER BY id DESC",(d,))
    except Exception:
        return []

# ============================================================
# PAGINA CONFIG + CSS MODERNO AMAZON
# ============================================================

st.set_page_config(page_title="Yard Manager", page_icon=None, layout="wide")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&display=swap');
*{font-family:'Inter',sans-serif;}
.stApp{background:#0F1111;color:#e0e0e0;}
[data-testid="stSidebar"]{background:#131A22!important;border-right:1px solid #232F3E;min-width:280px!important;}
[data-testid="stSidebar"] .stRadio>div>label{font-size:15px!important;padding:10px 14px!important;border-radius:8px;transition:all .2s;}
[data-testid="stSidebar"] .stRadio>div>label:hover{background:#232F3E;}
div[data-testid="stMetric"]{background:#232F3E;padding:16px;border-radius:10px;border:1px solid #37475A;}
div[data-testid="stMetric"] label{color:#999!important;font-size:10px;text-transform:uppercase;letter-spacing:1px;}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{color:#FF9900!important;font-weight:700;}
div[data-testid="stForm"]{background:#1A2332;padding:20px;border-radius:10px;border:1px solid #37475A;}
.stButton>button{background:#FF9900;color:#0F1111;font-weight:700;border:none;border-radius:8px;padding:10px 24px;font-size:14px;transition:all .2s;}
.stButton>button:hover{background:#FFAD33;transform:scale(1.02);}
.box-ok{background:#0a2a0a;border:1px solid #00C853;border-radius:8px;padding:12px;color:#a5d6a7;}
.box-warn{background:#2a2a0a;border:1px solid #FF9900;border-radius:8px;padding:12px;color:#ffe082;}
.prog-bar{width:100%;height:10px;background:#37475A;border-radius:5px;margin:8px 0;overflow:hidden;}
.prog-fill{height:100%;border-radius:5px;}
h1{color:#FF9900!important;font-weight:900;}
h2,h3{color:#FFF!important;font-weight:700;}
.kpi{background:#232F3E;padding:16px;border-radius:10px;border:1px solid #37475A;text-align:center;}
.card-yard{background:#1a2a1a;border-radius:8px;padding:12px;margin:6px 0;border:1px solid #00C853;}
.card-falta{background:#2a1a1a;padding:10px 12px;border-radius:8px;border:1px solid #EF4444;margin:4px 0;}
.modelo{background:#1A2332;border:1px solid #37475A;border-radius:8px;padding:14px;margin:8px 0;}
.header-az{background:linear-gradient(135deg,#232F3E,#1A2332);padding:16px 24px;border-radius:10px;margin-bottom:16px;border-bottom:3px solid #FF9900;}
.mural-card{background:#232F3E;border-radius:8px;padding:10px 14px;margin:6px 0;border-left:4px solid #FF9900;}
.mural-urg{background:#2a1a1a;border-radius:8px;padding:10px 14px;margin:6px 0;border-left:4px solid #EF4444;}
.visto-box{background:linear-gradient(135deg,#1a2a1a,#0a2a0a);border:2px solid #00C853;border-radius:12px;padding:24px;margin:12px 0;text-align:center;}
.rodape{text-align:center;padding:20px 0;border-top:1px solid #37475A;margin-top:30px;}
</style>""", unsafe_allow_html=True)

# ============================================================
# VARIAVEIS
# ============================================================

agora_dt = datetime.now(FUSO_BR)
agora = agora_dt.strftime("%d/%m/%Y %H:%M")
hoje_str = agora_dt.strftime("%Y-%m-%d")

if "perfil_idx" not in st.session_state:
    st.session_state.perfil_idx = 0

# ============================================================
# SIDEBAR MODERNA
# ============================================================

st.sidebar.markdown('<p style="font-size:26px;font-weight:900;color:#FFF;margin:0;">amazon</p>', unsafe_allow_html=True)
st.sidebar.markdown('<p style="font-size:13px;color:#FF9900;font-weight:700;letter-spacing:2px;margin:0 0 2px 0;">YARD MANAGER</p>', unsafe_allow_html=True)
st.sidebar.markdown('<p style="font-size:10px;color:#666;margin:0 0 10px 0;">' + SITE + ' | ' + agora + '</p>', unsafe_allow_html=True)
st.sidebar.markdown("---")

idioma = st.sidebar.selectbox("Idioma / Language", ["PT-BR","ENG","ESP"], index=0, key="lang")
t = T[idioma]

st.sidebar.markdown("---")

perfis = [t["perfil_lider"], t["perfil_otr"], t["perfil_yard"], t["perfil_motorista"]]
perfil = st.sidebar.radio("Perfil", perfis, index=st.session_state.perfil_idx, key="pf", label_visibility="collapsed")
st.session_state.perfil_idx = perfis.index(perfil)

st.sidebar.markdown("---")
if st.sidebar.button(t["atualizar"], use_container_width=True):
    st.rerun()

# ============================================================
# HEADER
# ============================================================

st.markdown('<div class="header-az"><p style="font-size:26px;font-weight:900;color:#FFF;margin:0;">amazon</p><p style="font-size:12px;color:#FF9900;font-weight:700;letter-spacing:3px;margin:4px 0 0 0;">' + t["titulo_op"] + '</p></div>', unsafe_allow_html=True)

# ============================================================
# FUNCOES DASHBOARD
# ============================================================

def dash_realtime(mots):
    mh = [m for m in mots if m.get("data_chegada","")[:10]==hoje_str]
    total = len(mh)
    chegaram = [m for m in mh if m.get("horario_chegada","")]
    desp = [m for m in mh if m.get("horario_saida","")]
    patio = [m for m in mh if m.get("horario_chegada","") and not m.get("horario_saida","")]
    faltam = [m for m in mh if not m.get("horario_chegada","")]
    fora = [m for m in mh if not m.get("importado",True)]

    hrs = [m["horario_chegada"] for m in chegaram if m.get("horario_chegada","")]
    prim = min(hrs) if hrs else "-"
    ult = max(hrs) if hrs else None
    t_sem = "-"
    ms = 0
    if ult:
        try:
            hu = datetime.strptime(ult,"%H:%M").replace(year=agora_dt.year,month=agora_dt.month,day=agora_dt.day)
            ms = int((agora_dt.replace(tzinfo=None)-hu).total_seconds()/60)
            if ms >= 0:
                t_sem = str(ms)+" min"
        except Exception:
            pass

    tempos = []
    for m in mh:
        if m.get("horario_chegada","") and m.get("horario_saida",""):
            try:
                h1=datetime.strptime(m["horario_chegada"],"%H:%M")
                h2=datetime.strptime(m["horario_saida"],"%H:%M")
                d=(h2-h1).total_seconds()/60
                if d>0:
                    tempos.append(d)
            except Exception:
                pass
    med_p = str(int(np.mean(tempos)))+" min" if tempos else "-"

    st.markdown("### "+t["status_agora"])
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: st.metric(t["total_previsto"],total)
    with c2: st.metric(t["chegaram"],len(chegaram))
    with c3: st.metric(t["no_patio"],len(patio))
    with c4: st.metric(t["despachados"],len(desp))
    with c5: st.metric(t["faltam_chegar"],len(faltam))
    with c6: st.metric(t["fora_lista"],len(fora))
    st.markdown("---")

    ca,cb,cc = st.columns(3)
    with ca:
        st.markdown('<div class="kpi"><p style="color:#888;font-size:10px;margin:0;">'+t["primeiro_veiculo"]+'</p><p style="font-size:28px;font-weight:900;color:#00BCD4;margin:0;">'+prim+'</p></div>', unsafe_allow_html=True)
    with cb:
        cs = "#EF4444" if ult and ms>30 else "#FF9900" if ult and ms>15 else "#00C853"
        st.markdown('<div class="kpi"><p style="color:#888;font-size:10px;margin:0;">'+t["tempo_sem_chegar"]+'</p><p style="font-size:28px;font-weight:900;color:'+cs+';margin:0;">'+t_sem+'</p></div>', unsafe_allow_html=True)
    with cc:
        cm = "#00C853"
        if tempos:
            vm=int(np.mean(tempos))
            cm = "#00C853" if vm<=20 else "#FF9900" if vm<=30 else "#EF4444"
        st.markdown('<div class="kpi"><p style="color:#888;font-size:10px;margin:0;">'+t["media_patio"]+'</p><p style="font-size:28px;font-weight:900;color:'+cm+';margin:0;">'+med_p+'</p><p style="color:#555;font-size:9px;margin:0;">SLA: 20 min</p></div>', unsafe_allow_html=True)
    st.markdown("---")

    pct = int((len(desp)/total)*100) if total>0 else 0
    cor = "#00C853" if pct>=80 else "#FF9900" if pct>=50 else "#EF4444"
    st.markdown('<div class="kpi"><p style="color:#888;font-size:10px;margin:0;">'+t["progresso"]+'</p><p style="font-size:38px;font-weight:900;color:'+cor+';margin:0;">'+str(pct)+'%</p><div class="prog-bar"><div class="prog-fill" style="width:'+str(min(pct,100))+'%;background:'+cor+';"></div></div><p style="color:#555;font-size:10px;margin:0;">'+str(len(desp))+' '+t["de"]+' '+str(total)+'</p></div>', unsafe_allow_html=True)
    st.markdown("---")

    pudo_t = [m for m in mh if m.get("categoria","")=="PUDO"]
    pick_t = [m for m in mh if m.get("categoria","")=="PICKUP"]
    pudo_d = [m for m in desp if m.get("categoria","")=="PUDO"]
    pick_d = [m for m in desp if m.get("categoria","")=="PICKUP"]
    col1,col2 = st.columns(2)
    with col1:
        pp = int((len(pudo_d)/len(pudo_t))*100) if pudo_t else 0
        st.markdown('<div class="kpi" style="border-left:4px solid #8B5CF6;"><p style="color:#8B5CF6;font-weight:700;margin:0;">PUDO</p><p style="font-size:24px;font-weight:900;color:#e0e0e0;margin:4px 0;">'+str(len(pudo_d))+'/'+str(len(pudo_t))+'</p><p style="color:#888;font-size:10px;margin:0;">'+str(pp)+'%</p></div>', unsafe_allow_html=True)
    with col2:
        pkp = int((len(pick_d)/len(pick_t))*100) if pick_t else 0
        st.markdown('<div class="kpi" style="border-left:4px solid #00BCD4;"><p style="color:#00BCD4;font-weight:700;margin:0;">PICKUP</p><p style="font-size:24px;font-weight:900;color:#e0e0e0;margin:4px 0;">'+str(len(pick_d))+'/'+str(len(pick_t))+'</p><p style="color:#888;font-size:10px;margin:0;">'+str(pkp)+'%</p></div>', unsafe_allow_html=True)
    st.markdown("---")

    if fora:
        st.markdown("### "+t["fora_lista"]+" ("+str(len(fora))+")")
        for fl in fora:
            st.markdown('<div class="card-falta">'+fl["nome"]+' | '+fl.get("categoria","")+' | '+fl.get("tipo_veiculo","")+'</div>', unsafe_allow_html=True)
        st.markdown("---")

    if faltam:
        st.markdown("### "+t["faltam"]+" ("+str(len(faltam))+")")
        for f in faltam:
            st.markdown('<div class="card-falta">'+f["nome"]+' | '+f.get("categoria","")+' | '+f.get("tipo_veiculo","")+'</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="box-ok">'+t["todos_chegaram"]+'</div>', unsafe_allow_html=True)
    st.markdown("---")

    if patio:
        st.markdown("### "+t["no_patio"]+" ("+str(len(patio))+")")
        for p in patio:
            ts="-"
            al=""
            try:
                hc=datetime.strptime(p["horario_chegada"],"%H:%M").replace(year=agora_dt.year,month=agora_dt.month,day=agora_dt.day)
                mi=int((agora_dt.replace(tzinfo=None)-hc).total_seconds()/60)
                ts=str(mi)+" min"
                al=' style="color:#EF4444;font-weight:700;"' if mi>20 else ' style="color:#00C853;"'
            except Exception:
                pass
            fora_tag = " [FORA DA LISTA]" if not p.get("importado",True) else ""
            st.markdown('<div class="card-yard"><strong>'+p["nome"]+'</strong>'+fora_tag+' | '+p.get("categoria","")+' | '+p.get("tipo_veiculo","")+' | '+t["faixa"]+': '+p.get("faixa","-")+' | <span'+al+'>'+ts+'</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="box-ok">'+t["patio_vazio"]+'</div>', unsafe_allow_html=True)


def dash_diario(mots, dt):
    ds = dt.strftime("%Y-%m-%d")
    md = [m for m in mots if m.get("data_chegada","")[:10]==ds]
    if not md:
        st.info(t["sem_dados"])
        return
    total=len(md)
    desp=len([m for m in md if m.get("horario_saida","")])
    fora=len([m for m in md if not m.get("importado",True)])
    hrs=[m["horario_chegada"] for m in md if m.get("horario_chegada","")]
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.metric("Total",total)
    with c2: st.metric(t["despachados"],desp)
    with c3: st.metric(t["fora_lista"],fora)
    with c4: st.metric(t["primeiro"],min(hrs) if hrs else "-")
    with c5: st.metric(t["ultimo"],max(hrs) if hrs else "-")
    st.markdown("---")
    tempos=[]
    for m in md:
        if m.get("horario_chegada","") and m.get("horario_saida",""):
            try:
                h1=datetime.strptime(m["horario_chegada"],"%H:%M")
                h2=datetime.strptime(m["horario_saida"],"%H:%M")
                d=(h2-h1).total_seconds()/60
                if d>0:
                    tempos.append(d)
            except Exception:
                pass
    if tempos:
        med=int(np.mean(tempos))
        cor="#00C853" if med<=20 else "#FF9900" if med<=30 else "#EF4444"
        st.markdown('<div class="kpi"><p style="color:#888;font-size:10px;margin:0;">'+t["tempo_medio"]+'</p><p style="font-size:32px;font-weight:900;color:'+cor+';margin:0;">'+str(med)+' min</p></div>', unsafe_allow_html=True)
    st.markdown("---")
    df=pd.DataFrame(md)
    cols=["nome","categoria","tipo_veiculo","placa","telefone","horario_chegada","horario_saida","faixa","importado"]
    cols_ok=[c for c in cols if c in df.columns]
    st.dataframe(df[cols_ok],use_container_width=True,hide_index=True)
    st.download_button(t["exportar"],data=df[cols_ok].to_csv(index=False),file_name="motoristas_"+ds+".csv",mime="text/csv")


def dash_semanal(mots):
    dados=[]
    for i in range(6,-1,-1):
        d=(agora_dt-timedelta(days=i)).strftime("%Y-%m-%d")
        md=[m for m in mots if m.get("data_chegada","")[:10]==d]
        desp=len([m for m in md if m.get("horario_saida","")])
        fora=len([m for m in md if not m.get("importado",True)])
        dados.append({"Dia":datetime.strptime(d,"%Y-%m-%d").strftime("%d/%m"),"Total":len(md),t["despachados"]:desp,t["fora_lista"]:fora,"PUDO":len([m for m in md if m.get("categoria","")=="PUDO"]),"PICKUP":len([m for m in md if m.get("categoria","")=="PICKUP"])})
    if any(r["Total"]>0 for r in dados):
        st.dataframe(pd.DataFrame(dados),use_container_width=True,hide_index=True)
    else:
        st.info(t["sem_dados"])


def dash_mensal(mots):
    dados=[]
    for i in range(29,-1,-1):
        d=(agora_dt-timedelta(days=i)).strftime("%Y-%m-%d")
        md=[m for m in mots if m.get("data_chegada","")[:10]==d]
        if md:
            desp=len([m for m in md if m.get("horario_saida","")])
            fora=len([m for m in md if not m.get("importado",True)])
            dados.append({"Dia":datetime.strptime(d,"%Y-%m-%d").strftime("%d/%m"),"Total":len(md),t["despachados"]:desp,t["fora_lista"]:fora})
    if dados:
        st.dataframe(pd.DataFrame(dados),use_container_width=True,hide_index=True)
        tot=sum(r["Total"] for r in dados)
        st.metric(t["total_previsto"],tot)
    else:
        st.info(t["sem_dados"])


# ============================================================
# PERFIL LIDER
# ============================================================

if perfil == t["perfil_lider"]:
    tabs = st.tabs([t["menu_dashboard"],t["menu_add_drivers"],t["menu_yard_control"],t["menu_mural"],t["menu_historico"],t["menu_editar"]])
    motoristas = carregar_motoristas()

    with tabs[0]:
        sub = st.tabs([t["tab_rt"],t["tab_diario"],t["tab_semanal"],t["tab_mensal"]])
        with sub[0]:
            dash_realtime(motoristas)
        with sub[1]:
            dt=st.date_input(t["sel_data"],value=date.today(),key="ld")
            dash_diario(motoristas,dt)
        with sub[2]:
            dash_semanal(motoristas)
        with sub[3]:
            dash_mensal(motoristas)

    with tabs[1]:
        st.markdown("### "+t["menu_add_drivers"])
        st.markdown('<div class="modelo"><strong>'+t["modelo_plan"]+'</strong><br>'+t["colunas"]+'<br><small>'+t["obrigatoria"]+'</small></div>', unsafe_allow_html=True)
        cat_i = st.selectbox(t["categoria"],["PUDO","PICKUP"],key="lci")
        dt_i = st.date_input(t["data_coleta"],value=date.today(),key="ldi")
        arq = st.file_uploader(t["importar"],type=["xlsx","csv"],key="lup")
        if arq:
            try:
                df_i = pd.read_csv(arq) if arq.name.endswith(".csv") else pd.read_excel(arq)
                st.dataframe(df_i,use_container_width=True,hide_index=True)
                if st.button(t["importar"]+" OK",type="primary",use_container_width=True,key="lbi"):
                    qtd=0
                    for _,row in df_i.iterrows():
                        nm=str(row.get("nome","")).strip()
                        if nm and nm!="nan":
                            salvar_motorista({"nome":nm,"placa":str(row.get("placa","")) if str(row.get("placa",""))!="nan" else "","tipo_veiculo":str(row.get("tipo_veiculo","")) if str(row.get("tipo_veiculo",""))!="nan" else "","telefone":str(row.get("telefone","")) if str(row.get("telefone",""))!="nan" else "","observacao":"","horario_chegada":"","horario_saida":"","observacoes":"","destino":"","data_chegada":dt_i.strftime("%Y-%m-%d"),"data_registro":agora,"importado":True,"categoria":cat_i,"status_yard":"aguardando","faixa":"","visto":False})
                            qtd+=1
                    st.success(str(qtd)+" "+t["importados"])
                    st.rerun()
            except Exception as ex:
                st.error(t["erro"]+" "+str(ex))

    with tabs[2]:
        st.markdown("### "+t["menu_yard_control"])
        mh=[m for m in motoristas if m.get("data_chegada","")[:10]==hoje_str]
        aguard=[m for m in mh if not m.get("horario_chegada","")]
        patio=[m for m in mh if m.get("horario_chegada","") and not m.get("horario_saida","")]

        st.markdown("#### "+t["registrar_chegada"])
        if aguard:
            nms=[m["nome"]+" | "+m.get("categoria","") for m in aguard]
            sel=st.selectbox(t["motorista_chegou"],nms,key="lsc")
            idx=nms.index(sel)
            mot=aguard[idx]
            cc1,cc2=st.columns(2)
            with cc1:
                fx=st.selectbox(t["faixa"],["1","2","3","Doca"],key="lfx")
            with cc2:
                hr=st.text_input(t["hora"],value=agora_dt.strftime("%H:%M"),key="lhr")
            if st.button(t["btn_chegou"],type="primary",use_container_width=True,key="lbc"):
                atualizar_mot(mot["id"],{"horario_chegada":hr,"faixa":fx,"status_yard":"no_patio"})
                st.rerun()
        else:
            st.markdown('<div class="box-ok">'+t["todos_yard"]+'</div>', unsafe_allow_html=True)

        with st.expander(t["manual_titulo"]):
            with st.form("frm_manual_l"):
                mn=st.text_input(t["nome"],key="lmn")
                fc1,fc2=st.columns(2)
                with fc1:
                    mv=st.selectbox(t["veiculo"],TIPOS_VEICULO,key="lmv")
                    mc=st.selectbox(t["categoria"],["PICKUP","PUDO"],key="lmc")
                with fc2:
                    mf=st.selectbox(t["faixa"],["1","2","3","Doca"],key="lmf")
                    mhr=st.text_input(t["hora"],value=agora_dt.strftime("%H:%M"),key="lmhr")
                mtel=st.text_input(t["telefone"],key="lmtel")
                mpl=st.text_input(t["placa"],key="lmpl")
                mob=st.text_input(t["obs"],key="lmob")
                if st.form_submit_button(t["registrar"],use_container_width=True):
                    if mn.strip():
                        salvar_motorista({"nome":mn.strip(),"placa":mpl,"tipo_veiculo":mv,"telefone":mtel,"observacao":"","horario_chegada":mhr,"horario_saida":"","observacoes":mob,"destino":"","data_chegada":hoje_str,"data_registro":agora,"importado":False,"categoria":mc,"status_yard":"no_patio","faixa":mf,"visto":False})
                        st.rerun()

        st.markdown("---")
        st.markdown("#### "+t["registrar_saida"])
        if patio:
            nps=[m["nome"]+" | "+m.get("categoria","")+" | "+t["faixa"]+" "+m.get("faixa","") for m in patio]
            sels=st.selectbox(t["motorista_saindo"],nps,key="lss")
            idxs=nps.index(sels)
            mots=patio[idxs]
            hs=st.text_input(t["hora_saida"],value=agora_dt.strftime("%H:%M"),key="lhs")
            if st.button(t["btn_saiu"],type="primary",use_container_width=True,key="lbs"):
                atualizar_mot(mots["id"],{"horario_saida":hs,"status_yard":"despachado"})
                st.rerun()
        else:
            st.info(t["nenhum_patio"])

    with tabs[3]:
        st.markdown("### "+t["menu_mural"])
        with st.form("frm_mural_l"):
            msg_t=st.text_area(t["msg_rapida"],key="lmsg")
            pri=st.selectbox(t["prioridade"],["info","urgente"],key="lpri")
            if st.form_submit_button(t["enviar"],use_container_width=True):
                if msg_t.strip():
                    salvar_msg({"autor":t["perfil_lider"],"perfil":"lider","mensagem":msg_t.strip(),"tipo":pri,"data_hora":agora,"data":hoje_str})
                    st.rerun()
        msgs=carregar_mural(hoje_str)
        if msgs:
            for mg in msgs:
                cls="mural-urg" if mg.get("tipo","")=="urgente" else "mural-card"
                st.markdown('<div class="'+cls+'"><strong>'+mg["autor"]+'</strong> <span style="color:#666;font-size:11px;">'+mg.get("data_hora","")+'</span><br>'+mg["mensagem"]+'</div>', unsafe_allow_html=True)
        else:
            st.info(t["nenhuma_msg"])

    with tabs[4]:
        st.markdown("### "+t["historico"])
        dt_h=st.date_input(t["sel_data"],value=date.today(),key="ldth")
        dash_diario(motoristas,dt_h)

    with tabs[5]:
        st.markdown("### "+t["editar_titulo"])
        mh_ed=[m for m in motoristas if m.get("data_chegada","")[:10]==hoje_str]
        if mh_ed:
            nms_ed=[m["nome"]+" | "+m.get("categoria","")+" | "+m.get("horario_chegada","-") for m in mh_ed]
            sel_ed=st.selectbox(t["selecione"],nms_ed,key="led")
            idx_ed=nms_ed.index(sel_ed)
            mot_ed=mh_ed[idx_ed]
            with st.form("frm_edit"):
                e1,e2=st.columns(2)
                with e1:
                    en=st.text_input(t["nome"],value=mot_ed.get("nome",""),key="en")
                    ep=st.text_input(t["placa"],value=mot_ed.get("placa",""),key="ep")
                    et=st.text_input(t["telefone"],value=mot_ed.get("telefone",""),key="et")
                with e2:
                    ev=st.selectbox(t["veiculo"],[""]+ TIPOS_VEICULO,index=0,key="ev")
                    ef=st.text_input(t["faixa"],value=mot_ed.get("faixa",""),key="ef")
                    ec=st.selectbox(t["categoria"],["PICKUP","PUDO"],index=0 if mot_ed.get("categoria","")=="PICKUP" else 1,key="ec")
                ehc=st.text_input(t["hora"],value=mot_ed.get("horario_chegada",""),key="ehc")
                ehs=st.text_input(t["hora_saida"],value=mot_ed.get("horario_saida",""),key="ehs")
                eob=st.text_input(t["obs"],value=mot_ed.get("observacoes",""),key="eob")
                if st.form_submit_button(t["salvar"],use_container_width=True):
                    dados={"nome":en,"placa":ep,"telefone":et,"faixa":ef,"categoria":ec,"horario_chegada":ehc,"horario_saida":ehs,"observacoes":eob}
                    if ev:
                        dados["tipo_veiculo"]=ev
                    atualizar_mot(mot_ed["id"],dados)
                    st.success(t["salvo"])
                    st.rerun()
        else:
            st.info(t["nenhum_registro"])


# ============================================================
# PERFIL OTR
# ============================================================

elif perfil == t["perfil_otr"]:
    tabs_o = st.tabs([t["menu_add_drivers"],t["menu_dashboard"],t["menu_mural"]])
    motoristas = carregar_motoristas()

    with tabs_o[0]:
        st.markdown("### "+t["menu_add_drivers"])
        st.markdown('<div class="modelo"><strong>'+t["modelo_plan"]+'</strong><br>'+t["colunas"]+'<br><small>'+t["obrigatoria"]+'</small></div>', unsafe_allow_html=True)
        cat_o=st.selectbox(t["categoria"],["PUDO","PICKUP"],key="oci")
        dt_o=st.date_input(t["data_coleta"],value=date.today(),key="odi")
        arq_o=st.file_uploader(t["importar"],type=["xlsx","csv"],key="oup")
        if arq_o:
            try:
                df_o=pd.read_csv(arq_o) if arq_o.name.endswith(".csv") else pd.read_excel(arq_o)
                st.dataframe(df_o,use_container_width=True,hide_index=True)
                if st.button(t["importar"]+" OK",type="primary",use_container_width=True,key="obi"):
                    qtd=0
                    for _,row in df_o.iterrows():
                        nm=str(row.get("nome","")).strip()
                        if nm and nm!="nan":
                            salvar_motorista({"nome":nm,"placa":str(row.get("placa","")) if str(row.get("placa",""))!="nan" else "","tipo_veiculo":str(row.get("tipo_veiculo","")) if str(row.get("tipo_veiculo",""))!="nan" else "","telefone":str(row.get("telefone","")) if str(row.get("telefone",""))!="nan" else "","observacao":"","horario_chegada":"","horario_saida":"","observacoes":"","destino":"","data_chegada":dt_o.strftime("%Y-%m-%d"),"data_registro":agora,"importado":True,"categoria":cat_o,"status_yard":"aguardando","faixa":"","visto":False})
                            qtd+=1
                    st.success(str(qtd)+" "+t["importados"])
                    st.rerun()
            except Exception as ex:
                st.error(t["erro"]+" "+str(ex))

    with tabs_o[1]:
        sub_o=st.tabs([t["tab_rt"],t["tab_diario"]])
        with sub_o[0]:
            dash_realtime(motoristas)
        with sub_o[1]:
            dt_od=st.date_input(t["sel_data"],value=date.today(),key="odd")
            dash_diario(motoristas,dt_od)

    with tabs_o[2]:
        st.markdown("### "+t["menu_mural"])
        with st.form("frm_mural_o"):
            msg_o=st.text_area(t["msg_rapida"],key="omsg")
            pri_o=st.selectbox(t["prioridade"],["info","urgente"],key="opri")
            if st.form_submit_button(t["enviar"],use_container_width=True):
                if msg_o.strip():
                    salvar_msg({"autor":t["perfil_otr"],"perfil":"otr","mensagem":msg_o.strip(),"tipo":pri_o,"data_hora":agora,"data":hoje_str})
                    st.rerun()
        msgs_o=carregar_mural(hoje_str)
        if msgs_o:
            for mg in msgs_o:
                cls="mural-urg" if mg.get("tipo","")=="urgente" else "mural-card"
                st.markdown('<div class="'+cls+'"><strong>'+mg["autor"]+'</strong> <span style="color:#666;font-size:11px;">'+mg.get("data_hora","")+'</span><br>'+mg["mensagem"]+'</div>', unsafe_allow_html=True)
        else:
            st.info(t["nenhuma_msg"])


# ============================================================
# PERFIL YARD
# ============================================================

elif perfil == t["perfil_yard"]:
    tabs_y = st.tabs([t["menu_yard_control"],t["menu_mural"]])
    motoristas = carregar_motoristas()

    with tabs_y[0]:
        st.markdown("### "+t["menu_yard_control"])
        mh=[m for m in motoristas if m.get("data_chegada","")[:10]==hoje_str]
        aguard=[m for m in mh if not m.get("horario_chegada","")]
        patio=[m for m in mh if m.get("horario_chegada","") and not m.get("horario_saida","")]

        st.markdown("#### "+t["registrar_chegada"])
        if aguard:
            nms=[m["nome"]+" | "+m.get("categoria","") for m in aguard]
            sel=st.selectbox(t["motorista_chegou"],nms,key="ysc")
            idx=nms.index(sel)
            mot=aguard[idx]
            yc1,yc2=st.columns(2)
            with yc1:
                fx=st.selectbox(t["faixa"],["1","2","3","Doca"],key="yfx")
            with yc2:
                hr=st.text_input(t["hora"],value=agora_dt.strftime("%H:%M"),key="yhr")
            if st.button(t["btn_chegou"],type="primary",use_container_width=True,key="ybc"):
                atualizar_mot(mot["id"],{"horario_chegada":hr,"faixa":fx,"status_yard":"no_patio"})
                st.rerun()
        else:
            st.markdown('<div class="box-ok">'+t["todos_yard"]+'</div>', unsafe_allow_html=True)

        with st.expander(t["manual_titulo"]):
            with st.form("frm_manual_y"):
                yn=st.text_input(t["nome"],key="ymn")
                yfc1,yfc2=st.columns(2)
                with yfc1:
                    yv=st.selectbox(t["veiculo"],TIPOS_VEICULO,key="ymv")
                    yc=st.selectbox(t["categoria"],["PICKUP","PUDO"],key="ymc")
                with yfc2:
                    yf=st.selectbox(t["faixa"],["1","2","3","Doca"],key="ymf")
                    yhr2=st.text_input(t["hora"],value=agora_dt.strftime("%H:%M"),key="ymhr")
                ytel=st.text_input(t["telefone"],key="ymtel")
                ypl=st.text_input(t["placa"],key="ympl")
                yob=st.text_input(t["obs"],key="ymob")
                if st.form_submit_button(t["registrar"],use_container_width=True):
                    if yn.strip():
                        salvar_motorista({"nome":yn.strip(),"placa":ypl,"tipo_veiculo":yv,"telefone":ytel,"observacao":"","horario_chegada":yhr2,"horario_saida":"","observacoes":yob,"destino":"","data_chegada":hoje_str,"data_registro":agora,"importado":False,"categoria":yc,"status_yard":"no_patio","faixa":yf,"visto":False})
                        st.rerun()

        st.markdown("---")
        st.markdown("#### "+t["registrar_saida"])
        if patio:
            nps=[m["nome"]+" | "+m.get("categoria","")+" | "+t["faixa"]+" "+m.get("faixa","") for m in patio]
            sels=st.selectbox(t["motorista_saindo"],nps,key="yss")
            idxs=nps.index(sels)
            mots=patio[idxs]
            yhs=st.text_input(t["hora_saida"],value=agora_dt.strftime("%H:%M"),key="yhs")
            if st.button(t["btn_saiu"],type="primary",use_container_width=True,key="ybs"):
                atualizar_mot(mots["id"],{"horario_saida":yhs,"status_yard":"despachado"})
                st.rerun()
        else:
            st.info(t["nenhum_patio"])

    with tabs_y[1]:
        st.markdown("### "+t["menu_mural"])
        with st.form("frm_mural_y"):
            msg_y=st.text_area(t["msg_rapida"],key="ymsg")
            pri_y=st.selectbox(t["prioridade"],["info","urgente"],key="ypri")
            if st.form_submit_button(t["enviar"],use_container_width=True):
                if msg_y.strip():
                    salvar_msg({"autor":t["perfil_yard"],"perfil":"yard","mensagem":msg_y.strip(),"tipo":pri_y,"data_hora":agora,"data":hoje_str})
                    st.rerun()
        msgs_y=carregar_mural(hoje_str)
        if msgs_y:
            for mg in msgs_y:
                cls="mural-urg" if mg.get("tipo","")=="urgente" else "mural-card"
                st.markdown('<div class="'+cls+'"><strong>'+mg["autor"]+'</strong> <span style="color:#666;font-size:11px;">'+mg.get("data_hora","")+'</span><br>'+mg["mensagem"]+'</div>', unsafe_allow_html=True)
        else:
            st.info(t["nenhuma_msg"])


# ============================================================
# PERFIL MOTORISTA (VISTO)
# ============================================================

elif perfil == t["perfil_motorista"]:
    st.markdown('<div class="visto-box"><h2 style="color:#00C853!important;">'+t["visto_titulo"]+'</h2><p style="color:#ccc;">'+t["visto_instrucao"]+'</p></div>', unsafe_allow_html=True)
    motoristas = carregar_motoristas()
    mh=[m for m in motoristas if m.get("data_chegada","")[:10]==hoje_str]

    with st.form("frm_visto"):
        nome_v=st.text_input(t["nome"],key="vnome")
        if st.form_submit_button(t["visto_btn"],type="primary",use_container_width=True):
            if nome_v.strip():
                encontrado=None
                for m in mh:
                    if m["nome"].strip().lower()==nome_v.strip().lower():
                        encontrado=m
                        break
                if encontrado:
                    if encontrado.get("visto",False):
                        st.warning(t["visto_ja"])
                    else:
                        atualizar_mot(encontrado["id"],{"visto":True})
                        st.success(t["visto_ok"])
                        st.rerun()
                else:
                    st.error(t["visto_erro"])

    st.markdown("---")
    vistos=[m for m in mh if m.get("visto",False)]
    if vistos:
        st.markdown("### Confirmados ("+str(len(vistos))+")")
        for v in vistos:
            st.markdown('<div class="card-yard">'+v["nome"]+' | '+v.get("categoria","")+' | '+v.get("tipo_veiculo","")+'</div>', unsafe_allow_html=True)


# ============================================================
# RODAPE
# ============================================================

st.markdown("---")
st.markdown('<div class="rodape"><p style="color:#FF9900;font-size:11px;font-weight:600;margin:0;">'+t["desenvolvido"]+'</p><p style="color:#555;font-size:10px;margin:4px 0 0 0;">Yard Manager | First Mile Operations | Amazon Logistics</p></div>', unsafe_allow_html=True)
