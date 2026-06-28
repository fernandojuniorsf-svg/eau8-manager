
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import pytz
import psycopg2

FUSO_BR = pytz.timezone("America/Sao_Paulo")
SITE = "EUA8"
TIPOS_VEICULO = ["Carreta (28 pallets)", "Truck (16 pallets)", "VUC (6 pallets)", "3/4", "Fiorino", "Van", "Bitruck", "Outro"]

# ══════════════════════════════════════════════════════════════
# TRADUCOES
# ══════════════════════════════════════════════════════════════

TRADUCOES = {
    "PT-BR": {
        "titulo_op": "OPERACAO FIRST MILE",
        "quem_voce": "Quem e voce?",
        "lider": "Lider",
        "otr": "OTR",
        "yard": "Yard",
        "motorista": "Motorista",
        "atualizar": "Atualizar Dados",
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
        "primeiro_veiculo": "PRIMEIRO VEICULO DO DIA",
        "tempo_sem_chegar": "TEMPO SEM CHEGAR VEICULO",
        "media_patio": "MEDIA TEMPO NO PATIO",
        "progresso_despacho": "PROGRESSO DE DESPACHO",
        "pudo_vs_pickup": "PUDO vs Pick Up Node",
        "faltam_titulo": "Faltam Chegar",
        "pct_nao_chegaram": "% dos veiculos ainda nao chegaram",
        "todos_chegaram": "Todos os veiculos previstos ja chegaram",
        "todos_pudo": "Todos PUDO chegaram",
        "todos_pickup": "Todos PICKUP chegaram",
        "no_patio_agora": "No Patio Agora",
        "patio_vazio": "Patio vazio - todos despachados",
        "concluido": "Concluido",
        "faltam": "Faltam",
        "de": "de",
        "dashboard_diario": "Dashboard Diario",
        "selecione_data": "Selecione a data:",
        "nao_vieram": "Nao Vieram",
        "primeiro": "1o Veiculo",
        "ultimo": "Ultimo Veiculo",
        "tempo_medio_patio": "TEMPO MEDIO NO PATIO",
        "todos_motoristas": "Todos os Motoristas do Dia",
        "exportar_csv": "Exportar CSV",
        "ultima_semana": "Ultima Semana",
        "total_semana": "Total Semana",
        "tempo_medio": "Tempo Medio",
        "sem_dados_semana": "Sem dados na ultima semana.",
        "ultimos_30": "Ultimos 30 Dias",
        "resumo_30": "Resumo 30 Dias",
        "total_veiculos": "Total Veiculos",
        "dias_operados": "Dias Operados",
        "media_dia": "Media/Dia",
        "tempo_medio_geral": "TEMPO MEDIO GERAL NO PATIO",
        "exportar_mensal": "Exportar Mensal CSV",
        "sem_dados_mes": "Sem dados nos ultimos 30 dias.",
        "tab_realtime": "Real-Time",
        "tab_diario": "Diario",
        "tab_semanal": "Semanal",
        "tab_mensal": "Mensal",
        "coletas_pudo": "Coletas PUDO",
        "resp_pudo": "Responsavel PUDO: importe a planilha do dia",
        "modelo_planilha": "Modelo da planilha:",
        "colunas_planilha": "A planilha deve ter as seguintes colunas:",
        "exemplo": "Exemplo:",
        "obrigatoria": "Apenas a coluna nome e obrigatoria. As demais sao opcionais.",
        "data_coletas": "Data das coletas",
        "importar": "Importar",
        "importou": "Importou",
        "motoristas_para": "motoristas para",
        "importados": "importados!",
        "hoje": "hoje:",
        "motoristas_txt": "motoristas",
        "coletas_pickup": "Coletas Pick Up Node",
        "resp_pickup": "Responsavel PICK UP NODE: importe a planilha do dia",
        "controle_yard": "Controle de Yard",
        "buscar_motorista": "Buscar Motorista",
        "registrar_chegada": "Registrar Chegada",
        "motorista_chegou": "Motorista chegou:",
        "faixa": "Faixa",
        "hora": "Hora (HH:MM)",
        "info_adicionais": "Informacoes adicionais (opcional)",
        "telefone_motorista": "Telefone do motorista",
        "placa": "Placa",
        "tipo_veiculo": "Tipo do veiculo",
        "btn_chegou": "CHEGOU",
        "todos_chegaram_yard": "Todos os motoristas previstos ja chegaram",
        "cadastro_manual": "Motorista nao esta na lista? Cadastrar manual",
        "nome": "Nome",
        "veiculo": "Veiculo",
        "categoria": "Categoria",
        "hora_chegada": "Hora chegada",
        "telefone_opc": "Telefone (opcional)",
        "placa_opc": "Placa (opcional)",
        "obs_opc": "Obs (opcional)",
        "registrar": "Registrar",
        "registrar_saida": "Registrar Saida",
        "motorista_saindo": "Motorista saindo:",
        "hora_saida": "Hora saida (HH:MM)",
        "obs_saida": "Obs saida (opcional)",
        "btn_saiu": "SAIU",
        "nenhum_patio": "Nenhum motorista no patio para despachar.",
        "avisar": "Avisar Lider/OTR",
        "msg_rapida": "Mensagem rapida:",
        "tipo": "Tipo",
        "enviar": "Enviar",
        "ultimas_msgs": "Ultimas Mensagens",
        "despachado": "Despachado",
        "aguardando": "Aguardando",
        "mural_comunicacao": "Mural de Comunicacao",
        "msgs_hoje": "Mensagens entre Lider, OTR e Yard - hoje",
        "sua_msg": "Sua mensagem:",
        "prioridade": "Prioridade",
        "nenhuma_msg": "Nenhuma mensagem hoje.",
        "historico_completo": "Historico Completo",
        "data": "Data",
        "nenhum_registro": "Nenhum registro nesta data.",
        "desenvolvido": "Desenvolvido por Fernando Junior | Lider EUA8",
        "chegou_msg": "chegou - Faixa",
        "saiu_msg": "saiu -",
        "manual": "(manual)",
        "nenhum_encontrado": "Nenhum motorista encontrado.",
        "erro": "Erro:",
        "msg_yard_lider": "Mensagem para Yard/Lider:",
        "nenhum_registro_data": "Nenhum registro para",
        "editar": "Editar",
        "salvar": "Salvar",
        "editar_motorista": "Editar Motorista",
        "selecione_motorista": "Selecione o motorista:",
        "edicao_salva": "Edicao salva com sucesso!",
        "visto_titulo": "Confirmar Chegada (Visto)",
        "visto_instrucao": "Motorista: digite seu nome para confirmar presenca",
        "visto_btn": "CONFIRMAR PRESENCA",
        "visto_sucesso": "Presenca confirmada!",
        "visto_erro": "Nome nao encontrado na lista de hoje.",
        "visto_ja": "Voce ja confirmou presenca anteriormente.",
    },
    "ENG": {
        "titulo_op": "OPERATION FIRST MILE",
        "quem_voce": "Who are you?",
        "lider": "Leader",
        "otr": "OTR",
        "yard": "Yard",
        "motorista": "Driver",
        "atualizar": "Refresh Data",
        "menu_dashboard": "Control Desk",
        "menu_add_drivers": "Add Drivers",
        "menu_yard_control": "Yard Control",
        "menu_mural": "Board",
        "menu_historico": "History",
        "menu_editar": "Edit Records",
        "status_agora": "Status Now",
        "total_previsto": "Total Expected",
        "chegaram": "Arrived",
        "no_patio": "In Yard",
        "despachados": "Dispatched",
        "faltam_chegar": "Pending Arrival",
        "fora_lista": "Off-List",
        "primeiro_veiculo": "FIRST VEHICLE OF THE DAY",
        "tempo_sem_chegar": "TIME WITHOUT VEHICLE ARRIVING",
        "media_patio": "AVERAGE TIME IN YARD",
        "progresso_despacho": "DISPATCH PROGRESS",
        "pudo_vs_pickup": "PUDO vs Pick Up Node",
        "faltam_titulo": "Pending Arrival",
        "pct_nao_chegaram": "% of vehicles not arrived yet",
        "todos_chegaram": "All expected vehicles have arrived",
        "todos_pudo": "All PUDO arrived",
        "todos_pickup": "All PICKUP arrived",
        "no_patio_agora": "In Yard Now",
        "patio_vazio": "Yard empty - all dispatched",
        "concluido": "Completed",
        "faltam": "Pending",
        "de": "of",
        "dashboard_diario": "Daily Dashboard",
        "selecione_data": "Select date:",
        "nao_vieram": "No Show",
        "primeiro": "1st Vehicle",
        "ultimo": "Last Vehicle",
        "tempo_medio_patio": "AVERAGE TIME IN YARD",
        "todos_motoristas": "All Drivers of the Day",
        "exportar_csv": "Export CSV",
        "ultima_semana": "Last Week",
        "total_semana": "Week Total",
        "tempo_medio": "Avg Time",
        "sem_dados_semana": "No data for last week.",
        "ultimos_30": "Last 30 Days",
        "resumo_30": "30 Days Summary",
        "total_veiculos": "Total Vehicles",
        "dias_operados": "Days Operated",
        "media_dia": "Avg/Day",
        "tempo_medio_geral": "OVERALL AVG TIME IN YARD",
        "exportar_mensal": "Export Monthly CSV",
        "sem_dados_mes": "No data for last 30 days.",
        "tab_realtime": "Real-Time",
        "tab_diario": "Daily",
        "tab_semanal": "Weekly",
        "tab_mensal": "Monthly",
        "coletas_pudo": "PUDO Collections",
        "resp_pudo": "PUDO: import today's spreadsheet",
        "modelo_planilha": "Spreadsheet template:",
        "colunas_planilha": "Columns:",
        "exemplo": "Example:",
        "obrigatoria": "Only nome (name) is required.",
        "data_coletas": "Collection date",
        "importar": "Import",
        "importou": "Imported",
        "motoristas_para": "drivers for",
        "importados": "imported!",
        "hoje": "today:",
        "motoristas_txt": "drivers",
        "coletas_pickup": "Pick Up Node Collections",
        "resp_pickup": "PICK UP NODE: import today's spreadsheet",
        "controle_yard": "Yard Control",
        "buscar_motorista": "Search Driver",
        "registrar_chegada": "Register Arrival",
        "motorista_chegou": "Driver arrived:",
        "faixa": "Lane",
        "hora": "Time (HH:MM)",
        "info_adicionais": "Additional info (optional)",
        "telefone_motorista": "Driver phone",
        "placa": "License plate",
        "tipo_veiculo": "Vehicle type",
        "btn_chegou": "ARRIVED",
        "todos_chegaram_yard": "All expected drivers arrived",
        "cadastro_manual": "Not on list? Manual entry",
        "nome": "Name",
        "veiculo": "Vehicle",
        "categoria": "Category",
        "hora_chegada": "Arrival time",
        "telefone_opc": "Phone (optional)",
        "placa_opc": "Plate (optional)",
        "obs_opc": "Notes (optional)",
        "registrar": "Register",
        "registrar_saida": "Register Departure",
        "motorista_saindo": "Driver departing:",
        "hora_saida": "Departure time (HH:MM)",
        "obs_saida": "Departure notes (optional)",
        "btn_saiu": "DEPARTED",
        "nenhum_patio": "No drivers in yard.",
        "avisar": "Notify Leader/OTR",
        "msg_rapida": "Quick message:",
        "tipo": "Type",
        "enviar": "Send",
        "ultimas_msgs": "Latest Messages",
        "despachado": "Dispatched",
        "aguardando": "Waiting",
        "mural_comunicacao": "Communication Board",
        "msgs_hoje": "Messages today",
        "sua_msg": "Your message:",
        "prioridade": "Priority",
        "nenhuma_msg": "No messages today.",
        "historico_completo": "Full History",
        "data": "Date",
        "nenhum_registro": "No records.",
        "desenvolvido": "Developed by Fernando Junior | Leader EUA8",
        "chegou_msg": "arrived - Lane",
        "saiu_msg": "departed -",
        "manual": "(manual)",
        "nenhum_encontrado": "No driver found.",
        "erro": "Error:",
        "msg_yard_lider": "Message to Yard/Leader:",
        "nenhum_registro_data": "No records for",
        "editar": "Edit",
        "salvar": "Save",
        "editar_motorista": "Edit Driver",
        "selecione_motorista": "Select driver:",
        "edicao_salva": "Saved!",
        "visto_titulo": "Confirm Arrival (Check-in)",
        "visto_instrucao": "Driver: type your name to confirm",
        "visto_btn": "CONFIRM PRESENCE",
        "visto_sucesso": "Presence confirmed!",
        "visto_erro": "Name not found in today's list.",
        "visto_ja": "You already confirmed.",
    },
    "ESP": {
        "titulo_op": "OPERACION FIRST MILE",
        "quem_voce": "Quien eres?",
        "lider": "Lider",
        "otr": "OTR",
        "yard": "Yard",
        "motorista": "Conductor",
        "atualizar": "Actualizar",
        "menu_dashboard": "Control Desk",
        "menu_add_drivers": "Add Drivers",
        "menu_yard_control": "Yard Control",
        "menu_mural": "Mural",
        "menu_historico": "Historial",
        "menu_editar": "Editar Registros",
        "status_agora": "Estado Actual",
        "total_previsto": "Total Previsto",
        "chegaram": "Llegaron",
        "no_patio": "En Patio",
        "despachados": "Despachados",
        "faltam_chegar": "Faltan",
        "fora_lista": "Fuera de Lista",
        "primeiro_veiculo": "PRIMER VEHICULO DEL DIA",
        "tempo_sem_chegar": "TIEMPO SIN VEHICULO",
        "media_patio": "PROMEDIO EN PATIO",
        "progresso_despacho": "PROGRESO DESPACHO",
        "pudo_vs_pickup": "PUDO vs Pick Up Node",
        "faltam_titulo": "Faltan por Llegar",
        "pct_nao_chegaram": "% no llegaron",
        "todos_chegaram": "Todos llegaron",
        "todos_pudo": "Todos PUDO llegaron",
        "todos_pickup": "Todos PICKUP llegaron",
        "no_patio_agora": "En Patio Ahora",
        "patio_vazio": "Patio vacio",
        "concluido": "Concluido",
        "faltam": "Faltan",
        "de": "de",
        "dashboard_diario": "Dashboard Diario",
        "selecione_data": "Fecha:",
        "nao_vieram": "No Vinieron",
        "primeiro": "1er Vehiculo",
        "ultimo": "Ultimo",
        "tempo_medio_patio": "TIEMPO PROMEDIO EN PATIO",
        "todos_motoristas": "Todos los Conductores",
        "exportar_csv": "Exportar CSV",
        "ultima_semana": "Ultima Semana",
        "total_semana": "Total Semana",
        "tempo_medio": "Tiempo Promedio",
        "sem_dados_semana": "Sin datos.",
        "ultimos_30": "Ultimos 30 Dias",
        "resumo_30": "Resumen 30 Dias",
        "total_veiculos": "Total Vehiculos",
        "dias_operados": "Dias Operados",
        "media_dia": "Promedio/Dia",
        "tempo_medio_geral": "PROMEDIO GENERAL EN PATIO",
        "exportar_mensal": "Exportar Mensual",
        "sem_dados_mes": "Sin datos.",
        "tab_realtime": "Real-Time",
        "tab_diario": "Diario",
        "tab_semanal": "Semanal",
        "tab_mensal": "Mensual",
        "coletas_pudo": "PUDO",
        "resp_pudo": "Importe planilla PUDO",
        "modelo_planilha": "Modelo planilla:",
        "colunas_planilha": "Columnas:",
        "exemplo": "Ejemplo:",
        "obrigatoria": "Solo nome es obligatorio.",
        "data_coletas": "Fecha",
        "importar": "Importar",
        "importou": "Importo",
        "motoristas_para": "conductores para",
        "importados": "importados!",
        "hoje": "hoy:",
        "motoristas_txt": "conductores",
        "coletas_pickup": "Pick Up Node",
        "resp_pickup": "Importe planilla PICKUP",
        "controle_yard": "Control Yard",
        "buscar_motorista": "Buscar",
        "registrar_chegada": "Registrar Llegada",
        "motorista_chegou": "Conductor llego:",
        "faixa": "Carril",
        "hora": "Hora (HH:MM)",
        "info_adicionais": "Info adicional",
        "telefone_motorista": "Telefono",
        "placa": "Placa",
        "tipo_veiculo": "Tipo vehiculo",
        "btn_chegou": "LLEGO",
        "todos_chegaram_yard": "Todos llegaron",
        "cadastro_manual": "No esta en lista? Manual",
        "nome": "Nombre",
        "veiculo": "Vehiculo",
        "categoria": "Categoria",
        "hora_chegada": "Hora llegada",
        "telefone_opc": "Telefono (opc)",
        "placa_opc": "Placa (opc)",
        "obs_opc": "Obs (opc)",
        "registrar": "Registrar",
        "registrar_saida": "Registrar Salida",
        "motorista_saindo": "Conductor saliendo:",
        "hora_saida": "Hora salida",
        "obs_saida": "Obs salida",
        "btn_saiu": "SALIO",
        "nenhum_patio": "Nadie en patio.",
        "avisar": "Avisar Lider/OTR",
        "msg_rapida": "Mensaje:",
        "tipo": "Tipo",
        "enviar": "Enviar",
        "ultimas_msgs": "Ultimos Mensajes",
        "despachado": "Despachado",
        "aguardando": "Esperando",
        "mural_comunicacao": "Mural",
        "msgs_hoje": "Mensajes hoy",
        "sua_msg": "Tu mensaje:",
        "prioridade": "Prioridad",
        "nenhuma_msg": "Sin mensajes.",
        "historico_completo": "Historial",
        "data": "Fecha",
        "nenhum_registro": "Sin registros.",
        "desenvolvido": "Desarrollado por Fernando Junior | Lider EUA8",
        "chegou_msg": "llego - Carril",
        "saiu_msg": "salio -",
        "manual": "(manual)",
        "nenhum_encontrado": "No encontrado.",
        "erro": "Error:",
        "msg_yard_lider": "Mensaje:",
        "nenhum_registro_data": "Sin registros para",
        "editar": "Editar",
        "salvar": "Guardar",
        "editar_motorista": "Editar Conductor",
        "selecione_motorista": "Seleccione:",
        "edicao_salva": "Guardado!",
        "visto_titulo": "Confirmar Llegada",
        "visto_instrucao": "Conductor: escriba su nombre",
        "visto_btn": "CONFIRMAR",
        "visto_sucesso": "Confirmado!",
        "visto_erro": "Nombre no encontrado.",
        "visto_ja": "Ya confirmado.",
    }
}

# ══════════════════════════════════════════════════════════════
# CONEXAO BANCO
# ══════════════════════════════════════════════════════════════

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

def db_execute(sql, params=None):
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
        importado BOOLEAN DEFAULT FALSE, foto TEXT,
        categoria TEXT DEFAULT 'PICKUP', status_yard TEXT DEFAULT 'aguardando',
        faixa TEXT DEFAULT '', visto BOOLEAN DEFAULT FALSE)""")
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

# ══════════════════════════════════════════════════════════════
# FUNCOES AUXILIARES
# ══════════════════════════════════════════════════════════════

def carregar_motoristas():
    try:
        return db_query("SELECT * FROM motoristas ORDER BY id DESC")
    except Exception:
        return []

def salvar_motorista(m):
    db_execute("""INSERT INTO motoristas (nome, placa, tipo_veiculo, telefone, observacao,
        horario_chegada, horario_saida, observacoes, destino, data_chegada,
        data_registro, importado, foto, categoria, status_yard, faixa, visto)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (str(m.get("nome","")), str(m.get("placa","")), str(m.get("tipo_veiculo","")),
         str(m.get("telefone","")), str(m.get("observacao","")), str(m.get("horario_chegada","")),
         str(m.get("horario_saida","")), str(m.get("observacoes","")), str(m.get("destino","")),
         str(m.get("data_chegada","")), str(m.get("data_registro","")),
         bool(m.get("importado", False)), str(m.get("foto","")),
         str(m.get("categoria","PICKUP")), str(m.get("status_yard","aguardando")),
         str(m.get("faixa","")), bool(m.get("visto", False))))

def atualizar_motorista(mid, dados):
    sets = ", ".join([k + "=%s" for k in dados.keys()])
    db_execute("UPDATE motoristas SET " + sets + " WHERE id=%s", list(dados.values()) + [mid])

def salvar_mural(msg):
    db_execute("INSERT INTO mural (autor, perfil, mensagem, tipo, data_hora, data) VALUES (%s,%s,%s,%s,%s,%s)",
        (msg["autor"], msg["perfil"], msg["mensagem"], msg.get("tipo","info"), msg["data_hora"], msg["data"]))

def carregar_mural(data_str):
    try:
        return db_query("SELECT * FROM mural WHERE data=%s ORDER BY id DESC", (data_str,))
    except Exception:
        return []

# ══════════════════════════════════════════════════════════════
# CONFIG PAGINA + CSS
# ══════════════════════════════════════════════════════════════

st.set_page_config(page_title="Yard Manager", page_icon=None, layout="wide")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&display=swap');
* {font-family: 'Inter', sans-serif;}
.stApp {background: #0F1111; color: #e0e0e0;}
[data-testid="stSidebar"] {background: #131A22 !important; border-right: 1px solid #232F3E; min-width: 300px !important;}
[data-testid="stSidebar"] .stRadio > div > label {font-size: 16px !important; padding: 10px 14px !important;}
div[data-testid="stMetric"] {background: #232F3E; padding: 18px; border-radius: 12px; border: 1px solid #37475A;}
div[data-testid="stMetric"] label {color: #888 !important; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {color: #FF9900 !important; font-weight: 700;}
div[data-testid="stForm"] {background: #1A2332; padding: 20px; border-radius: 12px; border: 1px solid #37475A;}
.stButton > button {background: #FF9900; color: #0F1111; font-weight: 700; border: none; border-radius: 8px; padding: 10px 24px; font-size: 14px;}
.stButton > button:hover {background: #FFAD33;}
.success-box {background: #0a2a0a; border: 1px solid #00C853; border-radius: 8px; padding: 12px; color: #a5d6a7;}
.warning-box {background: #2a2a0a; border: 1px solid #FF9900; border-radius: 8px; padding: 12px; color: #ffe082;}
.progress-bar {width: 100%; height: 12px; background: #37475A; border-radius: 6px; margin: 8px 0; overflow: hidden;}
.progress-fill {height: 100%; border-radius: 6px;}
h1 {color: #FF9900 !important; font-weight: 900;}
h2, h3 {color: #FFFFFF !important; font-weight: 700;}
.mural-msg {background: #232F3E; border-radius: 8px; padding: 12px 16px; margin: 6px 0; border-left: 4px solid #FF9900;}
.mural-msg-urgente {background: #2a1a1a; border-radius: 8px; padding: 12px 16px; margin: 6px 0; border-left: 4px solid #EF4444;}
.mural-msg-yard {background: #1a2a1a; border-radius: 8px; padding: 12px 16px; margin: 6px 0; border-left: 4px solid #00C853;}
.yard-card {background: #1a2a1a; border-radius: 10px; padding: 14px; margin: 6px 0; border: 1px solid #00C853;}
.kpi-box {background: #232F3E; padding: 18px; border-radius: 12px; border: 1px solid #37475A; text-align: center;}
.faltam-card {background: #2a1a1a; padding: 10px 14px; border-radius: 8px; border: 1px solid #EF4444; margin: 4px 0;}
.modelo-box {background: #1A2332; border: 1px solid #37475A; border-radius: 10px; padding: 14px; margin: 10px 0;}
.amazon-header {background: #232F3E; padding: 16px 24px; border-radius: 12px; margin-bottom: 16px; border-bottom: 3px solid #FF9900;}
.rodape {text-align: center; padding: 20px 0; border-top: 1px solid #37475A; margin-top: 30px;}
.visto-box {background: #1a2a1a; border: 2px solid #00C853; border-radius: 12px; padding: 20px; margin: 10px 0; text-align: center;}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# VARIAVEIS
# ══════════════════════════════════════════════════════════════

agora_dt = datetime.now(FUSO_BR)
agora = agora_dt.strftime("%d/%m/%Y %H:%M")
hoje_str = agora_dt.strftime("%Y-%m-%d")

# Manter aba ao atualizar
if "perfil_idx" not in st.session_state:
    st.session_state.perfil_idx = 0

# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════

st.sidebar.markdown('<p style="font-size:28px; font-weight:900; color:#FFFFFF; margin:0;">amazon</p>', unsafe_allow_html=True)
st.sidebar.markdown('<p style="font-size:14px; color:#FF9900; font-weight:700; letter-spacing:2px; margin:0 0 4px 0;">YARD MANAGER</p>', unsafe_allow_html=True)
st.sidebar.markdown('<p style="font-size:11px; color:#888; margin:0 0 12px 0;">' + SITE + '</p>', unsafe_allow_html=True)
st.sidebar.markdown("---")

idioma = st.sidebar.selectbox("PT-BR / ENG / ESP", ["PT-BR", "ENG", "ESP"], index=0, key="idioma")
t = TRADUCOES[idioma]

st.sidebar.markdown("---")
perfil = st.sidebar.radio(t["quem_voce"], [t["lider"], t["otr"], t["yard"], t["motorista"]], index=st.session_state.perfil_idx, key="perfil_radio")
st.session_state.perfil_idx = [t["lider"], t["otr"], t["yard"], t["motorista"]].index(perfil)

st.sidebar.markdown("---")
st.sidebar.markdown('<p style="color:#888; font-size:12px;">' + agora + '</p>', unsafe_allow_html=True)
st.sidebar.markdown("---")
if st.sidebar.button(t["atualizar"], use_container_width=True):
    st.rerun()

# ══════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════

st.markdown('<div class="amazon-header"><p style="font-size:28px; font-weight:900; color:#FFFFFF; margin:0;">amazon</p><p style="font-size:13px; color:#FF9900; font-weight:700; letter-spacing:3px; margin:4px 0 0 0;">' + t["titulo_op"] + '</p></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# DASHBOARD FUNCTIONS
# ══════════════════════════════════════════════════════════════

def render_realtime(motoristas_list):
    mot_hoje = [m for m in motoristas_list if m.get("data_chegada","")[:10] == hoje_str]
    total = len(mot_hoje)
    chegaram = [m for m in mot_hoje if m.get("horario_chegada","")]
    despachados = [m for m in mot_hoje if m.get("horario_saida","")]
    no_patio = [m for m in mot_hoje if m.get("horario_chegada","") and not m.get("horario_saida","")]
    faltam_chegar = [m for m in mot_hoje if not m.get("horario_chegada","")]
    fora_lista = [m for m in mot_hoje if not m.get("importado", True)]
    pudo_total = [m for m in mot_hoje if m.get("categoria","") == "PUDO"]
    pickup_total = [m for m in mot_hoje if m.get("categoria","") == "PICKUP"]
    pudo_faltam = [m for m in faltam_chegar if m.get("categoria","") == "PUDO"]
    pickup_faltam = [m for m in faltam_chegar if m.get("categoria","") == "PICKUP"]
    pudo_desp = [m for m in despachados if m.get("categoria","") == "PUDO"]
    pickup_desp = [m for m in despachados if m.get("categoria","") == "PICKUP"]

    horarios_c = [m["horario_chegada"] for m in chegaram if m.get("horario_chegada","")]
    primeiro_v = min(horarios_c) if horarios_c else "-"
    ultimo_c = max(horarios_c) if horarios_c else None
    tempo_sem = "-"
    mins_sem = 0
    if ultimo_c:
        try:
            h_u = datetime.strptime(ultimo_c, "%H:%M").replace(year=agora_dt.year, month=agora_dt.month, day=agora_dt.day)
            mins_sem = int((agora_dt.replace(tzinfo=None) - h_u).total_seconds() / 60)
            if mins_sem >= 0:
                tempo_sem = str(mins_sem) + " min"
        except Exception:
            pass

    tempos_h = []
    for m in mot_hoje:
        if m.get("horario_chegada","") and m.get("horario_saida",""):
            try:
                h1 = datetime.strptime(m["horario_chegada"], "%H:%M")
                h2 = datetime.strptime(m["horario_saida"], "%H:%M")
                d = (h2 - h1).total_seconds() / 60
                if d > 0:
                    tempos_h.append(d)
            except Exception:
                pass
    media_p = str(int(np.mean(tempos_h))) + " min" if tempos_h else "-"

    st.markdown("### " + t["status_agora"])
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1:
        st.metric(t["total_previsto"], total)
    with k2:
        st.metric(t["chegaram"], len(chegaram))
    with k3:
        st.metric(t["no_patio"], len(no_patio))
    with k4:
        st.metric(t["despachados"], len(despachados))
    with k5:
        st.metric(t["faltam_chegar"], len(faltam_chegar))
    with k6:
        st.metric(t["fora_lista"], len(fora_lista))
    st.markdown("---")

    ca, cb, cc = st.columns(3)
    with ca:
        st.markdown('<div class="kpi-box"><p style="color:#888; font-size:11px; margin:0;">' + t["primeiro_veiculo"] + '</p><p style="font-size:30px; font-weight:900; color:#00BCD4; margin:0;">' + primeiro_v + '</p></div>', unsafe_allow_html=True)
    with cb:
        cor_s = "#EF4444" if ultimo_c and mins_sem > 30 else "#FF9900" if ultimo_c and mins_sem > 15 else "#00C853"
        st.markdown('<div class="kpi-box"><p style="color:#888; font-size:11px; margin:0;">' + t["tempo_sem_chegar"] + '</p><p style="font-size:30px; font-weight:900; color:' + cor_s + '; margin:0;">' + tempo_sem + '</p></div>', unsafe_allow_html=True)
    with cc:
        cor_m = "#00C853"
        if tempos_h:
            mv = int(np.mean(tempos_h))
            cor_m = "#00C853" if mv <= 20 else "#FF9900" if mv <= 30 else "#EF4444"
        st.markdown('<div class="kpi-box"><p style="color:#888; font-size:11px; margin:0;">' + t["media_patio"] + '</p><p style="font-size:30px; font-weight:900; color:' + cor_m + '; margin:0;">' + media_p + '</p><p style="color:#666; font-size:10px; margin:0;">SLA: 20 min</p></div>', unsafe_allow_html=True)
    st.markdown("---")

    pct = int((len(despachados) / total) * 100) if total > 0 else 0
    cor = "#00C853" if pct >= 80 else "#FF9900" if pct >= 50 else "#EF4444"
    st.markdown('<div class="kpi-box"><p style="color:#888; font-size:11px; margin:0;">' + t["progresso_despacho"] + '</p><p style="font-size:40px; font-weight:900; color:' + cor + '; margin:0;">' + str(pct) + '%</p><div class="progress-bar"><div class="progress-fill" style="width:' + str(min(pct,100)) + '%; background:' + cor + ';"></div></div><p style="color:#666; font-size:11px; margin:0;">' + str(len(despachados)) + ' ' + t["de"] + ' ' + str(total) + '</p></div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### " + t["pudo_vs_pickup"])
    cp, cpk = st.columns(2)
    with cp:
        pp = int((len(pudo_desp)/len(pudo_total))*100) if pudo_total else 0
        st.markdown('<div class="kpi-box" style="border-left:4px solid #8B5CF6;"><p style="color:#8B5CF6; font-weight:700; margin:0;">PUDO</p><p style="font-size:26px; font-weight:900; color:#e0e0e0; margin:4px 0;">' + str(len(pudo_desp)) + '/' + str(len(pudo_total)) + '</p><p style="color:#888; font-size:11px; margin:0;">' + t["faltam"] + ': ' + str(len(pudo_faltam)) + ' | ' + str(pp) + '%</p></div>', unsafe_allow_html=True)
    with cpk:
        pkp = int((len(pickup_desp)/len(pickup_total))*100) if pickup_total else 0
        st.markdown('<div class="kpi-box" style="border-left:4px solid #00BCD4;"><p style="color:#00BCD4; font-weight:700; margin:0;">PICKUP</p><p style="font-size:26px; font-weight:900; color:#e0e0e0; margin:4px 0;">' + str(len(pickup_desp)) + '/' + str(len(pickup_total)) + '</p><p style="color:#888; font-size:11px; margin:0;">' + t["faltam"] + ': ' + str(len(pickup_faltam)) + ' | ' + str(pkp) + '%</p></div>', unsafe_allow_html=True)
    st.markdown("---")

    if fora_lista:
        st.markdown("### " + t["fora_lista"] + " (" + str(len(fora_lista)) + ")")
        for fl in fora_lista:
            st.markdown('<div class="faltam-card">' + fl["nome"] + ' | ' + fl.get("categoria","") + ' | ' + fl.get("tipo_veiculo","") + '</div>', unsafe_allow_html=True)
        st.markdown("---")

    if faltam_chegar:
        st.markdown("### " + t["faltam_titulo"] + " (" + str(len(faltam_chegar)) + ")")
        for fc in faltam_chegar:
            st.markdown('<div class="faltam-card">' + fc["nome"] + ' | ' + fc.get("categoria","") + ' | ' + fc.get("tipo_veiculo","") + '</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="success-box">' + t["todos_chegaram"] + '</div>', unsafe_allow_html=True)
    st.markdown("---")

    if no_patio:
        st.markdown("### " + t["no_patio_agora"] + " (" + str(len(no_patio)) + ")")
        for mp in no_patio:
            ts = "-"
            al = ""
            try:
                hc = datetime.strptime(mp["horario_chegada"], "%H:%M").replace(year=agora_dt.year, month=agora_dt.month, day=agora_dt.day)
                mi = int((agora_dt.replace(tzinfo=None) - hc).total_seconds() / 60)
                ts = str(mi) + " min"
                al = ' style="color:#EF4444; font-weight:700;"' if mi > 20 else ' style="color:#00C853;"'
            except Exception:
                pass
            st.markdown('<div class="yard-card"><strong>' + mp["nome"] + '</strong> | ' + mp.get("categoria","") + ' | ' + mp.get("tipo_veiculo","") + ' | ' + t["faixa"] + ': ' + mp.get("faixa","-") + ' | <span' + al + '>' + ts + '</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="success-box">' + t["patio_vazio"] + '</div>', unsafe_allow_html=True)


def render_diario(motoristas_list, data_sel):
    ds = data_sel.strftime("%Y-%m-%d")
    mot_d = [m for m in motoristas_list if m.get("data_chegada","")[:10] == ds]
    if not mot_d:
        st.info(t["nenhum_registro_data"] + " " + data_sel.strftime("%d/%m/%Y"))
        return
    total = len(mot_d)
    desp = [m for m in mot_d if m.get("horario_saida","")]
    fora = [m for m in mot_d if not m.get("importado", True)]
    horarios = [m["horario_chegada"] for m in mot_d if m.get("horario_chegada","")]
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.metric("Total", total)
    with k2:
        st.metric(t["despachados"], len(desp))
    with k3:
        st.metric(t["fora_lista"], len(fora))
    with k4:
        st.metric(t["primeiro"], min(horarios) if horarios else "-")
    with k5:
        st.metric(t["ultimo"], max(horarios) if horarios else "-")
    st.markdown("---")
    tempos = []
    for m in mot_d:
        if m.get("horario_chegada","") and m.get("horario_saida",""):
            try:
                h1 = datetime.strptime(m["horario_chegada"], "%H:%M")
                h2 = datetime.strptime(m["horario_saida"], "%H:%M")
                d = (h2 - h1).total_seconds() / 60
                if d > 0:
                    tempos.append(d)
            except Exception:
                pass
    if tempos:
        med = int(np.mean(tempos))
        cor = "#00C853" if med <= 20 else "#FF9900" if med <= 30 else "#EF4444"
        st.markdown('<div class="kpi-box"><p style="color:#888; font-size:11px; margin:0;">' + t["tempo_medio_patio"] + '</p><p style="font-size:34px; font-weight:900; color:' + cor + '; margin:0;">' + str(med) + ' min</p></div>', unsafe_allow_html=True)
    st.markdown("---")
    df = pd.DataFrame(mot_d)
    cols = ["nome","categoria","tipo_veiculo","placa","telefone","horario_chegada","horario_saida","faixa","importado","observacoes"]
    cols_ok = [c for c in cols if c in df.columns]
    st.dataframe(df[cols_ok], use_container_width=True, hide_index=True)
    st.download_button(t["exportar_csv"], data=df[cols_ok].to_csv(index=False), file_name="motoristas_" + ds + ".csv", mime="text/csv")


def render_semanal(motoristas_list):
    st.markdown("### " + t["ultima_semana"])
    dados = []
    for i in range(6, -1, -1):
        d = (agora_dt - timedelta(days=i)).strftime("%Y-%m-%d")
        md = [m for m in motoristas_list if m.get("data_chegada","")[:10] == d]
        desp = len([m for m in md if m.get("horario_saida","")])
        fora = len([m for m in md if not m.get("importado", True)])
        df_fmt = datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m")
        dados.append({"Dia": df_fmt, "Total": len(md), t["despachados"]: desp, t["fora_lista"]: fora, "PUDO": len([m for m in md if m.get("categoria","")=="PUDO"]), "PICKUP": len([m for m in md if m.get("categoria","")=="PICKUP"])})
    if any(r["Total"] > 0 for r in dados):
        st.dataframe(pd.DataFrame(dados), use_container_width=True, hide_index=True)
    else:
        st.info(t["sem_dados_semana"])


def render_mensal(motoristas_list):
    st.markdown("### " + t["ultimos_30"])
    dados = []
    for i in range(29, -1, -1):
        d = (agora_dt - timedelta(days=i)).strftime("%Y-%m-%d")
        md = [m for m in motoristas_list if m.get("data_chegada","")[:10] == d]
        if md:
            desp = len([m for m in md if m.get("horario_saida","")])
            fora = len([m for m in md if not m.get("importado", True)])
            dados.append({"Dia": datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m"), "Total": len(md), t["despachados"]: desp, t["fora_lista"]: fora})
    if dados:
        st.dataframe(pd.DataFrame(dados), use_container_width=True, hide_index=True)
        tot = sum(r["Total"] for r in dados)
        st.metric(t["total_veiculos"], tot)
    else:
        st.info(t["sem_dados_mes"])


# ══════════════════════════════════════════════════════════════
# PERFIL: LIDER
# ══════════════════════════════════════════════════════════════

if perfil == t["lider"]:
    tab_dash, tab_add, tab_yard, tab_mural, tab_hist, tab_edit = st.tabs([
        t["menu_dashboard"], t["menu_add_drivers"], t["menu_yard_control"],
        t["menu_mural"], t["menu_historico"], t["menu_editar"]
    ])
    motoristas = carregar_motoristas()

    with tab_dash:
        sub_rt, sub_d, sub_s, sub_m = st.tabs([t["tab_realtime"], t["tab_diario"], t["tab_semanal"], t["tab_mensal"]])
        with sub_rt:
            render_realtime(motoristas)
        with sub_d:
            dt = st.date_input(t["selecione_data"], value=date.today(), key="ld_dt")
            render_diario(motoristas, dt)
        with sub_s:
            render_semanal(motoristas)
        with sub_m:
            render_mensal(motoristas)

    with tab_add:
        st.markdown("### " + t["menu_add_drivers"])
        st.markdown('<div class="modelo-box"><strong>' + t["modelo_planilha"] + '</strong><br>' + t["colunas_planilha"] + '<br><code>nome | tipo_veiculo | placa | telefone | destino</code><br>' + t["exemplo"] + '<br><code>Joao Silva | Truck (16 pallets) | ABC1234 | 11999998888 | PUDO</code><br>' + t["obrigatoria"] + '</div>', unsafe_allow_html=True)
        cat_imp = st.selectbox(t["categoria"], ["PUDO", "PICKUP"], key="l_cat")
        dt_imp = st.date_input(t["data_coletas"], value=date.today(), key="l_dt_imp")
        arq = st.file_uploader(t["importar"], type=["xlsx","csv"], key="l_up")
        if arq:
            try:
                df_i = pd.read_csv(arq) if arq.name.endswith(".csv") else pd.read_excel(arq)
                st.dataframe(df_i, use_container_width=True, hide_index=True)
                if st.button(t["importar"], type="primary", use_container_width=True, key="l_btn_imp"):
                    qtd = 0
                    for _, row in df_i.iterrows():
                        nm = str(row.get("nome","")).strip()
                        if nm and nm != "nan":
                            salvar_motorista({"nome": nm, "placa": str(row.get("placa","")) if str(row.get("placa","")) != "nan" else "", "tipo_veiculo": str(row.get("tipo_veiculo","")) if str(row.get("tipo_veiculo","")) != "nan" else "", "telefone": str(row.get("telefone","")) if str(row.get("telefone","")) != "nan" else "", "observacao": "", "horario_chegada": "", "horario_saida": "", "observacoes": "", "destino": str(row.get("destino","")) if str(row.get("destino","")) != "nan" else "", "data_chegada": dt_imp.strftime("%Y-%m-%d"), "data_registro": agora, "importado": True, "foto": "", "categoria": cat_imp, "status_yard": "aguardando", "faixa": "", "visto": False})
                            qtd += 1
                    st.success(str(qtd) + " " + t["importados"])
                    st.rerun()
            except Exception as ex:
                st.error(t["erro"] + " " + str(ex))

    with tab_yard:
        st.markdown("### " + t["menu_yard_control"])
        mot_hoje = [m for m in motoristas if m.get("data_chegada","")[:10] == hoje_str]
        mot_aguard = [m for m in mot_hoje if not m.get("horario_chegada","")]
        mot_patio = [m for m in mot_hoje if m.get("horario_chegada","") and not m.get("horario_saida","")]

        st.markdown("#### " + t["registrar_chegada"])
        if mot_aguard:
            nomes_a = [m["nome"] + " | " + m.get("categoria","") for m in mot_aguard]
            sel_c = st.selectbox(t["motorista_chegou"], nomes_a, key="l_sel_c")
            idx_c = nomes_a.index(sel_c)
            mot_c = mot_aguard[idx_c]
            c1, c2 = st.columns(2)
            with c1:
                fx = st.selectbox(t["faixa"], ["1","2","3","Doca"], key="l_fx")
            with c2:
                hr = st.text_input(t["hora"], value=agora_dt.strftime("%H:%M"), key="l_hr")
            if st.button(t["btn_chegou"], type="primary", use_container_width=True, key="l_btn_c"):
                atualizar_motorista(mot_c["id"], {"horario_chegada": hr, "faixa": fx, "status_yard": "no_patio"})
                st.rerun()
        else:
            st.markdown('<div class="success-box">' + t["todos_chegaram_yard"] + '</div>', unsafe_allow_html=True)

        with st.expander(t["cadastro_manual"]):
            with st.form("lider_manual"):
                mn = st.text_input(t["nome"], key="l_mn")
                lc1, lc2 = st.columns(2)
                with lc1:
                    mt = st.selectbox(t["veiculo"], TIPOS_VEICULO, key="l_mt")
                    mc = st.selectbox(t["categoria"], ["PICKUP","PUDO"], key="l_mc")
                with lc2:
                    mf = st.selectbox(t["faixa"], ["1","2","3","Doca"], key="l_mf")
                    mh = st.text_input(t["hora_chegada"], value=agora_dt.strftime("%H:%M"), key="l_mh")
                mtel = st.text_input(t["telefone_opc"], key="l_mtel")
                mpl = st.text_input(t["placa_opc"], key="l_mpl")
                mob = st.text_input(t["obs_opc"], key="l_mob")
                if st.form_submit_button(t["registrar"], use_container_width=True):
                    if mn.strip():
                        salvar_motorista({"nome": mn.strip(), "placa": mpl, "tipo_veiculo": mt, "telefone": mtel, "observacao": "", "horario_chegada": mh, "horario_saida": "", "observacoes": mob, "destino": "", "data_chegada": hoje_str, "data_registro": agora, "importado": False, "foto": "", "categoria": mc, "status_yard": "no_patio", "faixa": mf, "visto": False})
                        st.rerun()

        st.markdown("---")
        st.markdown("#### " + t["registrar_saida"])
        if mot_patio:
            nomes_p = [m["nome"] + " | " + m.get("categoria","") + " | " + t["faixa"] + " " + m.get("faixa","") for m in mot_patio]
            sel_s = st.selectbox(t["motorista_saindo"], nomes_p, key="l_sel_s")
            idx_s = nomes_p.index(sel_s)
            mot_s = mot_patio[idx_s]
            hs = st.text_input(t["hora_saida"], value=agora_dt.strftime("%H:%M"), key="l_hs")
            if st.button(t["btn_saiu"], type="primary", use_container_width=True, key="l_btn_s"):
                atualizar_motorista(mot_s["id"], {"horario_saida": hs, "status_yard": "despachado"})
                st.rerun()
        else:
            st.info(t["nenhum_patio"])

    with tab_mural:
        st.markdown("### " + t["mural_comunicacao"])
