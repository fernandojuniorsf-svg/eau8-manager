
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
# CONEXAO COM BANCO
# ══════════════════════════════════════════════════════════════

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
    cols = [desc[0] for desc in cur.description] if cur.description else []
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(zip(cols, r)) for r in rows]

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
    cur.execute("""CREATE TABLE IF NOT EXISTS motoristas (
        id SERIAL PRIMARY KEY, nome TEXT, placa TEXT, tipo_veiculo TEXT,
        telefone TEXT, observacao TEXT, horario_chegada TEXT, horario_saida TEXT,
        observacoes TEXT, destino TEXT, data_chegada TEXT, data_registro TEXT,
        importado BOOLEAN DEFAULT FALSE, foto TEXT,
        categoria TEXT DEFAULT 'PICKUP', status_yard TEXT DEFAULT 'aguardando',
        faixa TEXT DEFAULT '')""")
    cur.execute("""CREATE TABLE IF NOT EXISTS mural (
        id SERIAL PRIMARY KEY, autor TEXT, perfil TEXT, mensagem TEXT,
        tipo TEXT DEFAULT 'info', data_hora TEXT, data TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS configuracoes (
        id SERIAL PRIMARY KEY, chave TEXT UNIQUE, valor TEXT)""")
    conn.commit()
    cur.close()
    conn.close()

try:
    init_db()
except Exception as e:
    st.error("Erro ao conectar no banco: " + str(e))
    st.stop()

# ══════════════════════════════════════════════════════════════
# FUNCOES AUXILIARES
# ══════════════════════════════════════════════════════════════

def carregar_motoristas():
    return query("SELECT * FROM motoristas ORDER BY id DESC")

def salvar_motorista(m):
    execute("""INSERT INTO motoristas (nome, placa, tipo_veiculo, telefone, observacao,
        horario_chegada, horario_saida, observacoes, destino, data_chegada,
        data_registro, importado, foto, categoria, status_yard, faixa)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (m["nome"], m.get("placa",""), m.get("tipo_veiculo",""), m.get("telefone",""),
         m.get("observacao",""), m.get("horario_chegada",""), m.get("horario_saida",""),
         m.get("observacoes",""), m.get("destino",""), m.get("data_chegada",""),
         m.get("data_registro",""), m.get("importado", False), m.get("foto",""),
         m.get("categoria","PICKUP"), m.get("status_yard","aguardando"), m.get("faixa","")))

def atualizar_motorista(mid, dados):
    sets = ", ".join([k + "=%s" for k in dados.keys()])
    execute("UPDATE motoristas SET " + sets + " WHERE id=%s", list(dados.values()) + [mid])

def salvar_mural(msg):
    execute("INSERT INTO mural (autor, perfil, mensagem, tipo, data_hora, data) VALUES (%s,%s,%s,%s,%s,%s)",
        (msg["autor"], msg["perfil"], msg["mensagem"], msg.get("tipo","info"), msg["data_hora"], msg["data"]))

def carregar_mural(data_str):
    return query("SELECT * FROM mural WHERE data=%s ORDER BY id DESC", (data_str,))

# ══════════════════════════════════════════════════════════════
# CONFIG DA PAGINA + CSS
# ══════════════════════════════════════════════════════════════

st.set_page_config(page_title=SITE + " Manager", page_icon="", layout="wide")

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
.success-box {background: linear-gradient(135deg, #0a2a0a 0%, #1a3a1a 100%); border: 1px solid #00C853; border-radius: 10px; padding: 14px; color: #a5d6a7;}
.warning-box {background: linear-gradient(135deg, #2a2a0a 0%, #3a3a1a 100%); border: 1px solid #FF9900; border-radius: 10px; padding: 14px; color: #ffe082;}
.error-box {background: linear-gradient(135deg, #2a0a0a 0%, #3a1a1a 100%); border: 1px solid #EF4444; border-radius: 10px; padding: 14px; color: #ef9a9a;}
.progress-bar {width: 100%; height: 10px; background: #222; border-radius: 6px; margin: 10px 0; overflow: hidden;}
.progress-fill {height: 100%; border-radius: 6px; transition: width 0.8s ease;}
h1, h2, h3 {color: #FF9900 !important; font-weight: 700;}
.stDataFrame {border-radius: 12px; overflow: hidden;}
.stSelectbox > div > div {background: #1e1e2e; border: 1px solid #333; border-radius: 8px;}
.stTextInput > div > div > input {background: #1e1e2e; border: 1px solid #333; border-radius: 8px; color: #e0e0e0;}
.mural-msg {background: #1e1e2e; border-radius: 10px; padding: 12px 16px; margin: 8px 0; border-left: 4px solid #FF9900;}
.mural-msg-urgente {background: #2a1a1a; border-radius: 10px; padding: 12px 16px; margin: 8px 0; border-left: 4px solid #EF4444;}
.mural-msg-yard {background: #1a2a1a; border-radius: 10px; padding: 12px 16px; margin: 8px 0; border-left: 4px solid #00C853;}
.yard-card-ativo {background: linear-gradient(135deg, #1a2a1a 0%, #2a3a2a 100%); border-radius: 14px; padding: 16px; margin: 8px 0; border: 1px solid #00C853;}
.kpi-box {background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3a 100%); padding: 16px; border-radius: 12px; border: 1px solid #333; text-align: center;}
.faltam-card {background: linear-gradient(135deg, #2a1a1a 0%, #3a2222 100%); padding: 12px 16px; border-radius: 10px; border: 1px solid #EF4444; margin: 4px 0;}
.modelo-box {background: linear-gradient(135deg, #1a1a2e 0%, #2a2a3e 100%); border: 1px solid #444; border-radius: 10px; padding: 16px; margin: 10px 0;}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# VARIAVEIS GLOBAIS
# ══════════════════════════════════════════════════════════════

agora_dt = datetime.now(FUSO_BR)
agora = agora_dt.strftime("%d/%m/%Y %H:%M")
hoje_str = agora_dt.strftime("%Y-%m-%d")

# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════

st.sidebar.markdown("## " + SITE + " Manager")
st.sidebar.markdown("*First Mile Operations*")
st.sidebar.markdown("---")

perfil = st.sidebar.radio("Quem e voce?", ["Lider", "OTR", "Yard"], index=0)

st.sidebar.markdown("---")
st.sidebar.markdown(agora)
st.sidebar.markdown(SITE)
st.sidebar.markdown("---")

if st.sidebar.button("Atualizar Dados", use_container_width=True):
    st.rerun()

st.markdown("# " + SITE + " Manager")
st.markdown("*First Mile Operations | Amazon Logistics*")
st.markdown("---")


# ══════════════════════════════════════════════════════════════
# FUNCOES DE DASHBOARD
# ══════════════════════════════════════════════════════════════

def render_dashboard_realtime(motoristas, hoje_str):
    mot_hoje = [m for m in motoristas if m.get("data_chegada","")[:10] == hoje_str]

    total = len(mot_hoje)
    chegaram = [m for m in mot_hoje if m.get("horario_chegada","")]
    despachados = [m for m in mot_hoje if m.get("horario_saida","")]
    no_patio = [m for m in mot_hoje if m.get("horario_chegada","") and not m.get("horario_saida","")]
    faltam_chegar = [m for m in mot_hoje if not m.get("horario_chegada","")]

    pudo_total = [m for m in mot_hoje if m.get("categoria","") == "PUDO"]
    pickup_total = [m for m in mot_hoje if m.get("categoria","") == "PICKUP"]
    pudo_faltam = [m for m in faltam_chegar if m.get("categoria","") == "PUDO"]
    pickup_faltam = [m for m in faltam_chegar if m.get("categoria","") == "PICKUP"]
    pudo_desp = [m for m in despachados if m.get("categoria","") == "PUDO"]
    pickup_desp = [m for m in despachados if m.get("categoria","") == "PICKUP"]

    # Primeiro veiculo do dia
    horarios_chegada = [m["horario_chegada"] for m in chegaram if m.get("horario_chegada","")]
    primeiro_veiculo = min(horarios_chegada) if horarios_chegada else "—"

    # Tempo desde ultimo veiculo
    ultimo_chegou = max(horarios_chegada) if horarios_chegada else None
    tempo_sem_veiculo = "—"
    mins_sem = 0
    if ultimo_chegou:
        try:
            h_ultimo = datetime.strptime(ultimo_chegou, "%H:%M").replace(
                year=agora_dt.year, month=agora_dt.month, day=agora_dt.day)
            delta_ultimo = agora_dt.replace(tzinfo=None) - h_ultimo
            mins_sem = int(delta_ultimo.total_seconds() / 60)
            if mins_sem >= 0:
                tempo_sem_veiculo = str(mins_sem) + " min"
        except:
            pass

    # Tempo medio no patio (dos que ja sairam hoje)
    tempos_hoje = []
    for m in mot_hoje:
        if m.get("horario_chegada","") and m.get("horario_saida",""):
            try:
                h1 = datetime.strptime(m["horario_chegada"], "%H:%M")
                h2 = datetime.strptime(m["horario_saida"], "%H:%M")
                delta = (h2 - h1).total_seconds() / 60
                if delta > 0:
                    tempos_hoje.append(delta)
            except:
                pass
    media_patio = str(int(np.mean(tempos_hoje))) + " min" if tempos_hoje else "—"

    # KPIs PRINCIPAIS
    st.markdown("### Status Agora")
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.metric("Total Previsto", total)
    with k2:
        st.metric("Chegaram", len(chegaram))
    with k3:
        st.metric("No Patio", len(no_patio))
    with k4:
        st.metric("Despachados", len(despachados))
    with k5:
        st.metric("Faltam Chegar", len(faltam_chegar))

    st.markdown("---")

    # SEGUNDO BLOCO: Primeiro veiculo + tempo sem chegar + media patio
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown('<div class="kpi-box"><p style="color:#888; font-size:11px; margin:0;">PRIMEIRO VEICULO DO DIA</p><p style="font-size:32px; font-weight:900; color:#00BCD4; margin:0;">' + primeiro_veiculo + '</p></div>', unsafe_allow_html=True)
    with col_b:
        cor_sem = "#EF4444" if ultimo_chegou and mins_sem > 30 else "#FF9900" if ultimo_chegou and mins_sem > 15 else "#00C853"
        st.markdown('<div class="kpi-box"><p style="color:#888; font-size:11px; margin:0;">TEMPO SEM CHEGAR VEICULO</p><p style="font-size:32px; font-weight:900; color:' + cor_sem + '; margin:0;">' + tempo_sem_veiculo + '</p></div>', unsafe_allow_html=True)
    with col_c:
        cor_media = "#00C853"
        if tempos_hoje:
            media_val = int(np.mean(tempos_hoje))
            cor_media = "#00C853" if media_val <= 20 else "#FF9900" if media_val <= 30 else "#EF4444"
        st.markdown('<div class="kpi-box"><p style="color:#888; font-size:11px; margin:0;">MEDIA TEMPO NO PATIO</p><p style="font-size:32px; font-weight:900; color:' + cor_media + '; margin:0;">' + media_patio + '</p><p style="color:#666; font-size:10px; margin:0;">SLA: 20 min</p></div>', unsafe_allow_html=True)

    st.markdown("---")

    # PROGRESSO
    pct = int((len(despachados) / total) * 100) if total > 0 else 0
    cor = "#00C853" if pct >= 80 else "#FF9900" if pct >= 50 else "#EF4444"
    st.markdown('<div class="kpi-box"><p style="color:#888; font-size:11px; margin:0;">PROGRESSO DE DESPACHO</p><p style="font-size:42px; font-weight:900; color:' + cor + '; margin:0;">' + str(pct) + '%</p><div class="progress-bar"><div class="progress-fill" style="width:' + str(min(pct,100)) + '%; background:' + cor + ';"></div></div><p style="color:#666; font-size:11px; margin:0;">' + str(len(despachados)) + ' de ' + str(total) + ' despachados</p></div>', unsafe_allow_html=True)

    st.markdown("---")

    # PUDO vs PICKUP
    st.markdown("### PUDO vs Pick Up Node")
    col_p, col_pk = st.columns(2)
    with col_p:
        pudo_pct = int((len(pudo_desp) / len(pudo_total)) * 100) if pudo_total else 0
        st.markdown('<div class="kpi-box" style="border-left: 4px solid #8B5CF6;"><p style="color:#8B5CF6; font-size:13px; font-weight:700; margin:0;">PUDO</p><p style="font-size:28px; font-weight:900; color:#e0e0e0; margin:4px 0;">' + str(len(pudo_desp)) + ' / ' + str(len(pudo_total)) + '</p><p style="color:#888; font-size:11px; margin:0;">Faltam: <strong style="color:#EF4444;">' + str(len(pudo_faltam)) + '</strong> | Concluido: ' + str(pudo_pct) + '%</p></div>', unsafe_allow_html=True)
    with col_pk:
        pickup_pct = int((len(pickup_desp) / len(pickup_total)) * 100) if pickup_total else 0
        st.markdown('<div class="kpi-box" style="border-left: 4px solid #00BCD4;"><p style="color:#00BCD4; font-size:13px; font-weight:700; margin:0;">PICK UP NODE</p><p style="font-size:28px; font-weight:900; color:#e0e0e0; margin:4px 0;">' + str(len(pickup_desp)) + ' / ' + str(len(pickup_total)) + '</p><p style="color:#888; font-size:11px; margin:0;">Faltam: <strong style="color:#EF4444;">' + str(len(pickup_faltam)) + '</strong> | Concluido: ' + str(pickup_pct) + '%</p></div>', unsafe_allow_html=True)

    st.markdown("---")

    # QUEM FALTA CHEGAR
    if faltam_chegar:
        st.markdown("### Faltam Chegar (" + str(len(faltam_chegar)) + ")")
        pct_faltam = int((len(faltam_chegar) / total) * 100) if total > 0 else 0
        st.markdown('<div class="warning-box">' + str(pct_faltam) + '% dos veiculos ainda nao chegaram</div>', unsafe_allow_html=True)

        col_fp, col_fpk = st.columns(2)
        with col_fp:
            st.markdown("**PUDO faltam (" + str(len(pudo_faltam)) + "):**")
            if pudo_faltam:
                for m in pudo_faltam:
                    st.markdown('<div class="faltam-card">' + m["nome"] + ' <span style="color:#666;">| ' + m.get("tipo_veiculo","") + '</span></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="success-box">Todos PUDO chegaram</div>', unsafe_allow_html=True)
        with col_fpk:
            st.markdown("**PICKUP faltam (" + str(len(pickup_faltam)) + "):**")
            if pickup_faltam:
                for m in pickup_faltam:
                    st.markdown('<div class="faltam-card">' + m["nome"] + ' <span style="color:#666;">| ' + m.get("tipo_veiculo","") + '</span></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="success-box">Todos PICKUP chegaram</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="success-box">Todos os veiculos previstos ja chegaram</div>', unsafe_allow_html=True)

    st.markdown("---")

    # NO PATIO AGORA
    if no_patio:
        st.markdown("### No Patio Agora (" + str(len(no_patio)) + ")")
        for mp in no_patio:
            tempo_str = "—"
            alerta = ""
            try:
                h_cheg = datetime.strptime(mp["horario_chegada"], "%H:%M").replace(
                    year=agora_dt.year, month=agora_dt.month, day=agora_dt.day)
                delta = agora_dt.replace(tzinfo=None) - h_cheg
                mins = int(delta.total_seconds() / 60)
                if mins > 20:
                    tempo_str = str(mins) + " min"
                    alerta = ' style="color:#EF4444; font-weight:700;"'
                else:
                    tempo_str = str(mins) + " min"
                    alerta = ' style="color:#00C853;"'
            except:
                pass
            st.markdown('<div class="yard-card-ativo"><strong>' + mp["nome"] + '</strong> ' + mp.get("categoria","") + ' | ' + mp.get("tipo_veiculo","") + ' | Faixa: ' + mp.get("faixa","—") + ' | Chegou: ' + mp.get("horario_chegada","") + ' | <span' + alerta + '>' + tempo_str + '</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="success-box">Patio vazio — todos despachados</div>', unsafe_allow_html=True)


def render_dashboard_diario(motoristas, data_sel):
    data_str = data_sel.strftime("%Y-%m-%d")
    mot_dia = [m for m in motoristas if m.get("data_chegada","")[:10] == data_str]

    if not mot_dia:
        st.info("Nenhum registro para " + data_sel.strftime("%d/%m/%Y"))
        return

    total = len(mot_dia)
    chegaram = [m for m in mot_dia if m.get("horario_chegada","")]
    despachados = [m for m in mot_dia if m.get("horario_saida","")]
    faltam = [m for m in mot_dia if not m.get("horario_chegada","")]
    pudo_total = [m for m in mot_dia if m.get("categoria","") == "PUDO"]
    pickup_total = [m for m in mot_dia if m.get("categoria","") == "PICKUP"]

    horarios = [m["horario_chegada"] for m in chegaram if m.get("horario_chegada","")]
    primeiro = min(horarios) if horarios else "—"
    ultimo = max(horarios) if horarios else "—"

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.metric("Total", total)
    with k2:
        st.metric("Despachados", len(despachados))
    with k3:
        st.metric("Nao Vieram", len(faltam))
    with k4:
        st.metric("1o Veiculo", primeiro)
    with k5:
        st.metric("Ultimo Veiculo", ultimo)

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        pudo_desp = len([m for m in pudo_total if m.get("horario_saida","")])
        st.markdown('<div class="kpi-box" style="border-left:4px solid #8B5CF6;"><p style="color:#8B5CF6; font-weight:700; margin:0;">PUDO</p><p style="font-size:24px; font-weight:900; color:#e0e0e0; margin:0;">' + str(pudo_desp) + ' / ' + str(len(pudo_total)) + '</p></div>', unsafe_allow_html=True)
    with col2:
        pickup_desp = len([m for m in pickup_total if m.get("horario_saida","")])
        st.markdown('<div class="kpi-box" style="border-left:4px solid #00BCD4;"><p style="color:#00BCD4; font-weight:700; margin:0;">PICK UP NODE</p><p style="font-size:24px; font-weight:900; color:#e0e0e0; margin:0;">' + str(pickup_desp) + ' / ' + str(len(pickup_total)) + '</p></div>', unsafe_allow_html=True)

    st.markdown("---")

    tempos = []
    for m in mot_dia:
        if m.get("horario_chegada","") and m.get("horario_saida",""):
            try:
                h1 = datetime.strptime(m["horario_chegada"], "%H:%M")
                h2 = datetime.strptime(m["horario_saida"], "%H:%M")
                delta = (h2 - h1).total_seconds() / 60
                if delta > 0:
                    tempos.append(delta)
            except:
                pass
    if tempos:
        media = int(np.mean(tempos))
        maximo = int(max(tempos))
        minimo = int(min(tempos))
        cor_media = "#00C853" if media <= 20 else "#FF9900" if media <= 30 else "#EF4444"
        st.markdown('<div class="kpi-box"><p style="color:#888; font-size:11px; margin:0;">TEMPO MEDIO NO PATIO</p><p style="font-size:36px; font-weight:900; color:' + cor_media + '; margin:0;">' + str(media) + ' min</p><p style="color:#666; font-size:11px; margin:0;">SLA: 20 min | Min: ' + str(minimo) + ' min | Max: ' + str(maximo) + ' min</p></div>', unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### Todos os Motoristas do Dia")
    df = pd.DataFrame(mot_dia)
    cols_show = ["nome", "categoria", "tipo_veiculo", "placa", "telefone", "horario_chegada", "horario_saida", "faixa", "observacoes"]
    cols_ok = [c for c in cols_show if c in df.columns]
    st.dataframe(df[cols_ok], use_container_width=True, hide_index=True)

    csv_data = df[cols_ok].to_csv(index=False)
    st.download_button("Exportar CSV", data=csv_data, file_name="motoristas_" + data_str + ".csv", mime="text/csv")


def render_dashboard_semanal(motoristas):
    st.markdown("### Ultima Semana")

    dias = []
    for i in range(6, -1, -1):
        d = (agora_dt - timedelta(days=i)).strftime("%Y-%m-%d")
        dias.append(d)

    dados_semana = []
    for d in dias:
        mot_d = [m for m in motoristas if m.get("data_chegada","")[:10] == d]
        desp = [m for m in mot_d if m.get("horario_saida","")]
        pudo = len([m for m in mot_d if m.get("categoria","") == "PUDO"])
        pickup = len([m for m in mot_d if m.get("categoria","") == "PICKUP"])

        tempos = []
        for m in mot_d:
            if m.get("horario_chegada","") and m.get("horario_saida",""):
                try:
                    h1 = datetime.strptime(m["horario_chegada"], "%H:%M")
                    h2 = datetime.strptime(m["horario_saida"], "%H:%M")
                    delta = (h2 - h1).total_seconds() / 60
                    if delta > 0:
                        tempos.append(delta)
                except:
                    pass
        media_t = int(np.mean(tempos)) if tempos else 0

        horarios = [m["horario_chegada"] for m in mot_d if m.get("horario_chegada","")]
        primeiro = min(horarios) if horarios else "—"

        d_fmt = datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m")
        dia_semana = ["Seg","Ter","Qua","Qui","Sex","Sab","Dom"][datetime.strptime(d, "%Y-%m-%d").weekday()]

        dados_semana.append({
            "Dia": dia_semana + " " + d_fmt,
            "Total": len(mot_d),
            "Despachados": len(desp),
            "PUDO": pudo,
            "PICKUP": pickup,
            "1o Veiculo": primeiro,
            "Tempo Medio (min)": media_t
        })

    if any(r["Total"] > 0 for r in dados_semana):
        df_sem = pd.DataFrame(dados_semana)
        st.dataframe(df_sem, use_container_width=True, hide_index=True)

        total_sem = sum(r["Total"] for r in dados_semana)
        desp_sem = sum(r["Despachados"] for r in dados_semana)
        pudo_sem = sum(r["PUDO"] for r in dados_semana)
        pickup_sem = sum(r["PICKUP"] for r in dados_semana)
        medias = [r["Tempo Medio (min)"] for r in dados_semana if r["Tempo Medio (min)"] > 0]
        media_sem = int(np.mean(medias)) if medias else 0

        st.markdown("---")
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            st.metric("Total Semana", total_sem)
        with k2:
            st.metric("Despachados", desp_sem)
        with k3:
            st.metric("PUDO", pudo_sem)
        with k4:
            st.metric("PICKUP", pickup_sem)
        with k5:
            st.metric("Tempo Medio", str(media_sem) + " min")
    else:
        st.info("Sem dados na ultima semana.")


def render_dashboard_mensal(motoristas):
    st.markdown("### Ultimos 30 Dias")

    dados_mes = []
    for i in range(29, -1, -1):
        d = (agora_dt - timedelta(days=i)).strftime("%Y-%m-%d")
        mot_d = [m for m in motoristas if m.get("data_chegada","")[:10] == d]
        if mot_d:
            desp = len([m for m in mot_d if m.get("horario_saida","")])
            pudo = len([m for m in mot_d if m.get("categoria","") == "PUDO"])
            pickup = len([m for m in mot_d if m.get("categoria","") == "PICKUP"])
            tempos = []
            for m in mot_d:
                if m.get("horario_chegada","") and m.get("horario_saida",""):
                    try:
                        h1 = datetime.strptime(m["horario_chegada"], "%H:%M")
                        h2 = datetime.strptime(m["horario_saida"], "%H:%M")
                        delta = (h2 - h1).total_seconds() / 60
                        if delta > 0:
                            tempos.append(delta)
                    except:
                        pass
            media_t = int(np.mean(tempos)) if tempos else 0
            d_fmt = datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m")
            dados_mes.append({"Dia": d_fmt, "Total": len(mot_d), "Despachados": desp, "PUDO": pudo, "PICKUP": pickup, "Tempo Medio": media_t})

    if dados_mes:
        df_mes = pd.DataFrame(dados_mes)
        st.dataframe(df_mes, use_container_width=True, hide_index=True)

        total_m = sum(r["Total"] for r in dados_mes)
        pudo_m = sum(r["PUDO"] for r in dados_mes)
        pickup_m = sum(r["PICKUP"] for r in dados_mes)
        dias_op = len(dados_mes)
        media_dia = int(total_m / dias_op) if dias_op else 0
        medias_m = [r["Tempo Medio"] for r in dados_mes if r["Tempo Medio"] > 0]
        media_geral = int(np.mean(medias_m)) if medias_m else 0

        st.markdown("---")
        st.markdown("### Resumo 30 Dias")
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            st.metric("Total Veiculos", total_m)
        with k2:
            st.metric("Dias Operados", dias_op)
        with k3:
            st.metric("Media/Dia", media_dia)
        with k4:
            st.metric("PUDO Total", pudo_m)
        with k5:
            st.metric("PICKUP Total", pickup_m)

        cor_mg = "#00C853" if media_geral <= 20 else "#FF9900" if media_geral <= 30 else "#EF4444"
        st.markdown('<div class="kpi-box"><p style="color:#888; font-size:11px; margin:0;">TEMPO MEDIO GERAL NO PATIO</p><p style="font-size:42px; font-weight:900; color:' + cor_mg + '; margin:0;">' + str(media_geral) + ' min</p><p style="color:#666; font-size:11px;">SLA: 20 min</p></div>', unsafe_allow_html=True)

        csv_data = df_mes.to_csv(index=False)
        st.download_button("Exportar Mensal CSV", data=csv_data, file_name="mensal_" + hoje_str + ".csv", mime="text/csv")
    else:
        st.info("Sem dados nos ultimos 30 dias.")


# ══════════════════════════════════════════════════════════════
# PERFIL: LIDER
# ══════════════════════════════════════════════════════════════

if perfil == "Lider":
    tab_rt, tab_diario, tab_semanal, tab_mensal, tab_mural, tab_hist = st.tabs([
        "Real-Time", "Diario", "Semanal", "Mensal", "Mural", "Historico"
    ])

    motoristas = carregar_motoristas()

    with tab_rt:
        render_dashboard_realtime(motoristas, hoje_str)

    with tab_diario:
        st.markdown("### Dashboard Diario")
        data_sel = st.date_input("Selecione a data:", value=date.today(), key="dt_diario")
        render_dashboard_diario(motoristas, data_sel)

    with tab_semanal:
        render_dashboard_semanal(motoristas)

    with tab_mensal:
        render_dashboard_mensal(motoristas)

    with tab_mural:
        st.markdown("### Mural de Comunicacao")
        st.markdown("*Mensagens entre Lider, OTR e Yard — hoje*")
        with st.form("form_mural_lider"):
            msg_lider = st.text_input("Sua mensagem:", placeholder="Ex: Proximo veiculo e prioridade, dockar na D3")
            tipo_msg = st.selectbox("Prioridade", ["info", "urgente"], index=0)
            btn_msg = st.form_submit_button("Enviar", use_container_width=True)
            if btn_msg and msg_lider:
                salvar_mural({"autor": "Lider", "perfil": "lider", "mensagem": msg_lider, "tipo": tipo_msg, "data_hora": agora, "data": hoje_str})
                st.rerun()
        st.markdown("---")
        mensagens = carregar_mural(hoje_str)
        if mensagens:
            for msg in mensagens:
                css_class = "mural-msg-urgente" if msg.get("tipo") == "urgente" else "mural-msg-yard" if msg.get("perfil") == "yard" else "mural-msg"
                st.markdown('<div class="' + css_class + '"><strong>' + msg.get("autor","") + '</strong> <span style="color:#666; font-size:11px;">' + msg.get("data_hora","") + '</span><br>' + msg.get("mensagem","") + '</div>', unsafe_allow_html=True)
        else:
            st.info("Nenhuma mensagem hoje.")

    with tab_hist:
        st.markdown("### Historico Completo")
        data_hist = st.date_input("Data", value=date.today(), key="dt_hist_lider")
        data_hist_str = data_hist.strftime("%Y-%m-%d")
        mot_hist = [m for m in motoristas if m.get("data_chegada","")[:10] == data_hist_str]
        if mot_hist:
            df_hist = pd.DataFrame(mot_hist)
            cols_hist = ["nome", "categoria", "tipo_veiculo", "placa", "telefone", "horario_chegada", "horario_saida", "faixa", "observacoes"]
            cols_ok = [c for c in cols_hist if c in df_hist.columns]
            st.dataframe(df_hist[cols_ok], use_container_width=True, hide_index=True)
            csv_data = df_hist[cols_ok].to_csv(index=False)
            st.download_button("Exportar CSV", data=csv_data, file_name="motoristas_" + data_hist_str + ".csv", mime="text/csv")
        else:
            st.info("Nenhum registro nesta data.")


# ══════════════════════════════════════════════════════════════
# PERFIL: OTR
# ══════════════════════════════════════════════════════════════

elif perfil == "OTR":
    tab_pudo, tab_pickup, tab_mural_otr = st.tabs(["PUDO", "Pick Up Node", "Mural"])

    with tab_pudo:
        st.markdown("### Coletas PUDO")
        st.markdown("*Responsavel PUDO: importe a planilha do dia*")

        # MODELO DA PLANILHA
        st.markdown('<div class="modelo-box"><strong>Modelo da planilha PUDO:</strong><br><br>A planilha deve ter as seguintes colunas:<br><code>nome | tipo_veiculo | placa | telefone | destino</code><br><br>Exemplo:<br><code>Joao Silva | Truck (16 pallets) | ABC1234 | 11999998888 | PUDO Centro</code><br><br>* Apenas a coluna <strong>nome</strong> e obrigatoria. As demais sao opcionais.</div>', unsafe_allow_html=True)

        data_pudo = st.date_input("Data das coletas", value=date.today(), key="dt_pudo")
        data_pudo_str = data_pudo.strftime("%Y-%m-%d")

        arq_pudo = st.file_uploader("Planilha PUDO (.xlsx ou .csv)", type=["xlsx", "csv"], key="up_pudo")
        if arq_pudo:
            try:
                if arq_pudo.name.endswith(".csv"):
                    df_pudo = pd.read_csv(arq_pudo)
                else:
                    df_pudo = pd.read_excel(arq_pudo)
                st.dataframe(df_pudo, use_container_width=True, hide_index=True)
                if st.button("Importar PUDO", type="primary", use_container_width=True, key="btn_imp_pudo"):
                    qtd = 0
                    for _, row in df_pudo.iterrows():
                        nome_r = str(row.get("nome", "")).strip()
                        if nome_r and nome_r != "nan":
                            salvar_motorista({"nome": nome_r,
                                "placa": str(row.get("placa","")).strip() if str(row.get("placa","")) != "nan" else "",
                                "tipo_veiculo": str(row.get("tipo_veiculo","")).strip() if str(row.get("tipo_veiculo","")) != "nan" else "",
                                "telefone": str(row.get("telefone","")).strip() if str(row.get("telefone","")) != "nan" else "",
                                "observacao": "", "horario_chegada": "", "horario_saida": "",
                                "observacoes": "", "destino": str(row.get("destino","")).strip() if str(row.get("destino","")) != "nan" else "PUDO",
                                "data_chegada": data_pudo_str, "data_registro": agora,
                                "importado": True, "foto": "", "categoria": "PUDO",
                                "status_yard": "aguardando", "faixa": ""})
                            qtd += 1
                    salvar_mural({"autor": "OTR", "perfil": "otr",
                        "mensagem": "Importou " + str(qtd) + " motoristas PUDO para " + data_pudo.strftime("%d/%m"),
                        "tipo": "info", "data_hora": agora, "data": hoje_str})
                    st.success(str(qtd) + " motoristas PUDO importados!")
                    st.rerun()
            except Exception as ex:
                st.error("Erro: " + str(ex))

        motoristas = carregar_motoristas()
        pudo_dia = [m for m in motoristas if m.get("data_chegada","")[:10] == data_pudo_str and m.get("categoria","") == "PUDO"]
        if pudo_dia:
            st.markdown("---")
            st.markdown("**PUDO hoje:** " + str(len(pudo_dia)) + " motoristas")
            df_p = pd.DataFrame(pudo_dia)
            cols_p = ["nome", "tipo_veiculo", "placa", "telefone", "horario_chegada", "horario_saida", "faixa"]
            cols_ok = [c for c in cols_p if c in df_p.columns]
            st.dataframe(df_p[cols_ok], use_container_width=True, hide_index=True)

    with tab_pickup:
        st.markdown("### Coletas Pick Up Node")
        st.markdown("*Responsavel PICK UP NODE: importe a planilha do dia*")

        # MODELO DA PLANILHA
        st.markdown('<div class="modelo-box"><strong>Modelo da planilha PICK UP NODE:</strong><br><br>A planilha deve ter as seguintes colunas:<br><code>nome | tipo_veiculo | placa | telefone | destino</code><br><br>Exemplo:<br><code>Maria Santos | Carreta (28 pallets) | XYZ5678 | 11988887777 | Node SP01</code><br><br>* Apenas a coluna <strong>nome</strong> e obrigatoria. As demais sao opcionais.</div>', unsafe_allow_html=True)

        data_pickup = st.date_input("Data das coletas", value=date.today(), key="dt_pickup")
        data_pickup_str = data_pickup.strftime("%Y-%m-%d")

        arq_pickup = st.file_uploader("Planilha Pick Up Node (.xlsx ou .csv)", type=["xlsx", "csv"], key="up_pickup")
        if arq_pickup:
            try:
                if arq_pickup.name.endswith(".csv"):
                    df_pickup = pd.read_csv(arq_pickup)
                else:
                    df_pickup = pd.read_excel(arq_pickup)
                st.dataframe(df_pickup, use_container_width=True, hide_index=True)
                if st.button("Importar Pick Up Node", type="primary", use_container_width=True, key="btn_imp_pickup"):
                    qtd = 0
                    for _, row in df_pickup.iterrows():
                        nome_r = str(row.get("nome", "")).strip()
                        if nome_r and nome_r != "nan":
                            salvar_motorista({"nome": nome_r,
                                "placa": str(row.get("placa","")).strip() if str(row.get("placa","")) != "nan" else "",
                                "tipo_veiculo": str(row.get("tipo_veiculo","")).strip() if str(row.get("tipo_veiculo","")) != "nan" else "",
                                "telefone": str(row.get("telefone","")).strip() if str(row.get("telefone","")) != "nan" else "",
                                "observacao": "", "horario_chegada": "", "horario_saida": "",
                                "observacoes": "", "destino": str(row.get("destino","")).strip() if str(row.get("destino","")) != "nan" else "",
                                "data_chegada": data_pickup_str, "data_registro": agora,
                                "importado": True, "foto": "", "categoria": "PICKUP",
                                "status_yard": "aguardando", "faixa": ""})
                            qtd += 1
                    salvar_mural({"autor": "OTR", "perfil": "otr",
                        "mensagem": "Importou " + str(qtd) + " motoristas PICK UP NODE para " + data_pickup.strftime("%d/%m"),
                        "tipo": "info", "data_hora": agora, "data": hoje_str})
                    st.success(str(qtd) + " motoristas Pick Up Node importados!")
                    st.rerun()
            except Exception as ex:
                st.error("Erro: " + str(ex))

        motoristas = carregar_motoristas()
        pickup_dia = [m for m in motoristas if m.get("data_chegada","")[:10] == data_pickup_str and m.get("categoria","") == "PICKUP"]
        if pickup_dia:
            st.markdown("---")
            st.markdown("**Pick Up Node hoje:** " + str(len(pickup_dia)) + " motoristas")
            df_pk = pd.DataFrame(pickup_dia)
            cols_pk = ["nome", "tipo_veiculo", "placa", "telefone", "destino", "horario_chegada", "horario_saida", "faixa"]
            cols_ok = [c for c in cols_pk if c in df_pk.columns]
            st.dataframe(df_pk[cols_ok], use_container_width=True, hide_index=True)

    with tab_mural_otr:
        st.markdown("### Mural")
        with st.form("form_mural_otr"):
            msg_otr = st.text_input("Mensagem para Yard/Lider:", placeholder="Ex: Carreta VIN123 vai chegar 17:30, dockar D5")
            btn_msg_otr = st.form_submit_button("Enviar", use_container_width=True)
            if btn_msg_otr and msg_otr:
                salvar_mural({"autor": "OTR", "perfil": "otr", "mensagem": msg_otr, "tipo": "info", "data_hora": agora, "data": hoje_str})
                st.rerun()
        st.markdown("---")
        mensagens = carregar_mural(hoje_str)
        if mensagens:
            for msg in mensagens:
                css_class = "mural-msg-urgente" if msg.get("tipo") == "urgente" else "mural-msg-yard" if msg.get("perfil") == "yard" else "mural-msg"
                st.markdown('<div class="' + css_class + '"><strong>' + msg.get("autor","") + '</strong> <span style="color:#666; font-size:11px;">' + msg.get("data_hora","") + '</span><br>' + msg.get("mensagem","") + '</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# PERFIL: YARD
# ══════════════════════════════════════════════════════════════

elif perfil == "Yard":
    st.markdown("### Controle de Yard")

    motoristas = carregar_motoristas()
    mot_hoje = [m for m in motoristas if m.get("data_chegada","")[:10] == hoje_str]

    # BUSCA RAPIDA
    st.markdown("#### Buscar Motorista")
    busca = st.text_input("Nome:", placeholder="Ex: Vinicius", key="busca_yard", label_visibility="collapsed")

    if busca:
        busca_lower = busca.lower()
        resultados = [m for m in mot_hoje if busca_lower in m.get("nome","").lower()]
        if resultados:
            for r in resultados:
                status = "Despachado" if r.get("horario_saida","") else "No patio" if r.get("horario_chegada","") else "Aguardando"
                st.markdown('<div class="yard-card-ativo"><strong>' + r["nome"] + '</strong> ' + r.get("categoria","") + ' | ' + status + ' | Faixa: ' + r.get("faixa","—") + ' | Chegou: ' + r.get("horario_chegada","—") + ' | Saiu: ' + r.get("horario_saida","—") + '</div>', unsafe_allow_html=True)
        else:
            st.warning("Nenhum motorista encontrado.")

    # REGISTRO DE CHEGADA
    st.markdown("---")
    st.markdown("#### Registrar Chegada")

    mot_aguardando = [m for m in mot_hoje if not m.get("horario_chegada","")]

    if mot_aguardando:
        nomes_aguardando = [m["nome"] + " | " + m.get("categoria","") + " | " + m.get("tipo_veiculo","") for m in mot_aguardando]
        sel_chegada = st.selectbox("Motorista chegou:", nomes_aguardando, key="sel_chegada_yard")
        idx_sel = nomes_aguardando.index(sel_chegada)
        mot_selecionado = mot_aguardando[idx_sel]

        col_faixa, col_hora = st.columns(2)
        with col_faixa:
            faixa_chegada = st.selectbox("Faixa", ["1", "2", "3", "Doca"], key="faixa_yard")
        with col_hora:
            hora_chegada = st.text_input("Hora (HH:MM)", value=agora_dt.strftime("%H:%M"), key="hora_chegada_yard")

        # Campos opcionais para Yard preencher
        with st.expander("Informacoes adicionais (opcional)"):
            tel_yard = st.text_input("Telefone do motorista", value=mot_selecionado.get("telefone",""), key="tel_yard")
            placa_yard = st.text_input("Placa", value=mot_selecionado.get("placa",""), key="placa_yard")
            tipo_yard_veiculo = st.selectbox("Tipo do veiculo", [""] + TIPOS_VEICULO, index=0, key="tipo_veiculo_yard")

        if st.button("CHEGOU", type="primary", use_container_width=True, key="btn_chegou"):
            dados_update = {"horario_chegada": hora_chegada, "faixa": faixa_chegada, "status_yard": "no_patio"}
            if tel_yard:
                dados_update["telefone"] = tel_yard
            if placa_yard:
                dados_update["placa"] = placa_yard
            if tipo_yard_veiculo:
                dados_update["tipo_veiculo"] = tipo_yard_veiculo
            atualizar_motorista(mot_selecionado["id"], dados_update)
            salvar_mural({"autor": "Yard", "perfil": "yard",
                "mensagem": mot_selecionado["nome"] + " chegou — Faixa " + faixa_chegada + " (" + mot_selecionado.get("categoria","") + ")",
                "tipo": "info", "data_hora": agora, "data": hoje_str})
            st.rerun()
    else:
        st.markdown('<div class="success-box">Todos os motoristas previstos ja chegaram</div>', unsafe_allow_html=True)

    # Cadastro manual
    with st.expander("Motorista nao esta na lista? Cadastrar manual"):
        with st.form("form_manual_yard"):
            nome_manual = st.text_input("Nome")
            cm1, cm2 = st.columns(2)
            with cm1:
                tipo_manual = st.selectbox("Veiculo", TIPOS_VEICULO, key="tipo_manual_yard")
                cat_manual = st.selectbox("Categoria", ["PICKUP", "PUDO"], key="cat_manual_yard")
            with cm2:
                faixa_manual = st.selectbox("Faixa", ["1", "2", "3", "Doca"], key="faixa_manual_yard")
                hora_manual = st.text_input("Hora chegada", value=agora_dt.strftime("%H:%M"), key="hora_manual_yard")
            tel_manual = st.text_input("Telefone (opcional)", key="tel_manual_yard")
            placa_manual = st.text_input("Placa (opcional)", key="placa_manual_yard")
            obs_manual = st.text_input("Obs (opcional)", key="obs_manual_yard")
            btn_manual = st.form_submit_button("Registrar", use_container_width=True)
            if btn_manual and nome_manual:
                salvar_motorista({"nome": nome_manual, "placa": placa_manual, "tipo_veiculo": tipo_manual,
                    "telefone": tel_manual, "observacao": "", "horario_chegada": hora_manual,
                    "horario_saida": "", "observacoes": obs_manual, "destino": "",
                    "data_chegada": hoje_str, "data_registro": agora, "importado": False,
                    "foto": "", "categoria": cat_manual, "status_yard": "no_patio", "faixa": faixa_manual})
                salvar_mural({"autor": "Yard", "perfil": "yard",
                    "mensagem": nome_manual + " chegou (manual) — Faixa " + faixa_manual + " (" + cat_manual + ")",
                    "tipo": "info", "data_hora": agora, "data": hoje_str})
                st.rerun()

    # REGISTRO DE SAIDA
    st.markdown("---")
    st.markdown("#### Registrar Saida")

    mot_no_patio = [m for m in mot_hoje if m.get("horario_chegada","") and not m.get("horario_saida","")]

    if mot_no_patio:
        nomes_patio = [m["nome"] + " | " + m.get("categoria","") + " | Faixa " + m.get("faixa","?") + " | Chegou " + m.get("horario_chegada","") for m in mot_no_patio]
        sel_saida = st.selectbox("Motorista saindo:", nomes_patio, key="sel_saida_yard")
        idx_saida = nomes_patio.index(sel_saida)
        mot_saindo = mot_no_patio[idx_saida]

        hora_saida = st.text_input("Hora saida (HH:MM)", value=agora_dt.strftime("%H:%M"), key="hora_saida_yard")
        obs_saida = st.text_input("Obs saida (opcional)", value=mot_saindo.get("observacoes",""), key="obs_saida_yard")

        if st.button("SAIU", type="primary", use_container_width=True, key="btn_saiu"):
            atualizar_motorista(mot_saindo["id"], {"horario_saida": hora_saida, "observacoes": obs_saida, "status_yard": "despachado"})
            salvar_mural({"autor": "Yard", "perfil": "yard",
                "mensagem": mot_saindo["nome"] + " saiu — " + hora_saida + " (" + mot_saindo.get("categoria","") + ")",
                "tipo": "info", "data_hora": agora, "data": hoje_str})
            st.rerun()
    else:
        st.info("Nenhum motorista no patio para despachar.")

    # MURAL RAPIDO
    st.markdown("---")
    st.markdown("#### Avisar Lider/OTR")
    with st.form("form_mural_yard"):
        msg_yard = st.text_input("Mensagem rapida:", placeholder="Ex: Veiculo com problema no assoalho")
        col_tipo, col_btn = st.columns([1,1])
        with col_tipo:
            tipo_yard_msg = st.selectbox("Tipo", ["info", "urgente"], key="tipo_yard_msg")
        with col_btn:
            btn_yard_msg = st.form_submit_button("Enviar", use_container_width=True)
        if btn_yard_msg and msg_yard:
            salvar_mural({"autor": "Yard", "perfil": "yard", "mensagem": msg_yard, "tipo": tipo_yard_msg, "data_hora": agora, "data": hoje_str})
            st.rerun()

    # Ultimas mensagens
    st.markdown("---")
    st.markdown("#### Ultimas Mensagens")
    mensagens = carregar_mural(hoje_str)
    if mensagens:
        for msg in mensagens[:5]:
            css_class = "mural-msg-urgente" if msg.get("tipo") == "urgente" else "mural-msg-yard" if msg.get("perfil") == "yard" else "mural-msg"
            st.markdown('<div class="' + css_class + '"><strong>' + msg.get("autor","") + '</strong> <span style="color:#666; font-size:11px;">' + msg.get("data_hora","") + '</span><br>' + msg.get("mensagem","") + '</div>', unsafe_allow_html=True)
            # ══════════════════════════════════════════════════════════════
# RODAPE
# ══════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown('<div style="text-align:center; padding:20px 0;"><p style="color:#666; font-size:11px;">' + SITE + ' Manager | First Mile Operations | Amazon Logistics</p></div>', unsafe_allow_html=True)
