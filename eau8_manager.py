
import streamlit as st
import pandas as pd
import json
import hashlib
from datetime import datetime, date, timedelta
import pytz
import psycopg2

# ============================================================
# EUA8 YARD - DASHBOARD DO MOTORISTA (SEM LOGIN)
# PostgreSQL mantido - mesmo banco do EUA8 Manager
# ============================================================

FUSO_BR = pytz.timezone("America/Sao_Paulo")
SITE = "EUA8"
TIPOS_VEICULO = ["Carreta (28 pallets)", "Truck (16 pallets)", "VUC (6 pallets)", "3/4", "Fiorino", "Van", "Bitruck", "Outro"]

# ============================================================
# CONEXAO POSTGRESQL (mesma do EUA8 Manager)
# ============================================================

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

def get_config_valor(chave, default="0"):
    r = query_one("SELECT valor FROM configuracoes WHERE chave=%s", (chave,))
    return r["valor"] if r else default

def salvar_config(chave, valor):
    execute("INSERT INTO configuracoes (chave, valor) VALUES (%s, %s) ON CONFLICT (chave) DO UPDATE SET valor = EXCLUDED.valor", (chave, valor))

def carregar_motoristas():
    return query("SELECT * FROM motoristas ORDER BY id DESC")

def salvar_motorista(m):
    execute("INSERT INTO motoristas (nome, placa, tipo_veiculo, telefone, observacao, horario_chegada, horario_saida, observacoes, destino, data_chegada, data_registro, importado, foto) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (m["nome"], m.get("placa",""), m.get("tipo_veiculo",""), m.get("telefone",""), m.get("observacao",""), m.get("horario_chegada",""), m.get("horario_saida",""), m.get("observacoes",""), m.get("destino",""), m.get("data_chegada",""), m.get("data_registro",""), m.get("importado", False), m.get("foto","")))

def atualizar_motorista(mid, dados):
    sets = ", ".join([k + "=%s" for k in dados.keys()])
    execute("UPDATE motoristas SET " + sets + " WHERE id=%s", list(dados.values()) + [mid])

# ============================================================
# CONFIGURACAO DA PAGINA
# ============================================================

st.set_page_config(page_title=SITE + " Yard", page_icon="🚛", layout="wide")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&display=swap');
* {font-family: 'Inter', sans-serif !important;}
.stApp {background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #0a0a0a 100%); color: #e0e0e0;}
[data-testid="stSidebar"] {display: none !important;}
div[data-testid="stMetric"] {background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3a 100%); padding: 18px; border-radius: 14px; border: 1px solid #333; box-shadow: 0 4px 20px rgba(0,0,0,0.3);}
div[data-testid="stMetric"] label {color: #888 !important; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {color: #FF9900 !important; font-weight: 700;}
div[data-testid="stForm"] {background: linear-gradient(135deg, #1a1a2a 0%, #222233 100%); padding: 20px; border-radius: 14px; border: 1px solid #333;}
.stButton > button {background: linear-gradient(135deg, #FF9900 0%, #e68a00 100%); color: #000; font-weight: 600; border: none; border-radius: 10px; padding: 10px 24px; transition: all 0.3s; font-size: 15px;}
.stButton > button:hover {background: linear-gradient(135deg, #ffad33 0%, #FF9900 100%); transform: translateY(-1px); box-shadow: 0 4px 12px rgba(255,153,0,0.3);}
.success-box {background: linear-gradient(135deg, #0a2a0a 0%, #1a3a1a 100%); border: 1px solid #00C853; border-radius: 10px; padding: 14px; color: #a5d6a7;}
.warning-box {background: linear-gradient(135deg, #2a2a0a 0%, #3a3a1a 100%); border: 1px solid #FF9900; border-radius: 10px; padding: 14px; color: #ffe082;}
h1, h2, h3 {color: #FF9900 !important; font-weight: 700;}
.stSelectbox > div > div {background: #1e1e2e; border: 1px solid #333; border-radius: 8px;}
.stTextInput > div > div > input {background: #1e1e2e; border: 1px solid #333; border-radius: 8px; color: #e0e0e0;}
.yard-card {background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3a 100%); border-radius: 14px; padding: 20px; border: 1px solid #333; margin-bottom: 12px;}
</style>""", unsafe_allow_html=True)

# ============================================================
# VARIAVEIS GLOBAIS
# ============================================================

agora_dt = datetime.now(FUSO_BR)
agora = agora_dt.strftime("%d/%m/%Y %H:%M")
hoje_str = agora_dt.strftime("%Y-%m-%d")

# ============================================================
# HEADER
# ============================================================

st.markdown("<h1 style='text-align:center; margin:0;'>🚛 EUA8 Yard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#999; margin:0 0 20px 0;'>Controle de Patio | " + agora + "</p>", unsafe_allow_html=True)

# ============================================================
# NAVEGACAO POR BOTOES (sem sidebar, sem login)
# ============================================================

if "pagina" not in st.session_state:
    st.session_state["pagina"] = "Dashboard"

nav1, nav2, nav3, nav4 = st.columns(4)
with nav1:
    if st.button("📊 Dashboard", use_container_width=True, key="nav_dash"):
        st.session_state["pagina"] = "Dashboard"
        st.rerun()
with nav2:
    if st.button("🟢 Entrada", use_container_width=True, key="nav_entrada"):
        st.session_state["pagina"] = "Entrada"
        st.rerun()
with nav3:
    if st.button("🔴 Saida", use_container_width=True, key="nav_saida"):
        st.session_state["pagina"] = "Saida"
        st.rerun()
with nav4:
    if st.button("📱 Comunicacao", use_container_width=True, key="nav_com"):
        st.session_state["pagina"] = "Comunicacao"
        st.rerun()

st.markdown("---")
pagina = st.session_state["pagina"]

# ============================================================
# PAGINA: DASHBOARD
# ============================================================

if pagina == "Dashboard":
    motoristas = carregar_motoristas()
    mot_hoje = [m for m in motoristas if m.get("data_chegada","")[:10] == hoje_str]
    mot_pendentes = [m for m in mot_hoje if not m.get("horario_saida", "")]
    mot_liberados = [m for m in mot_hoje if m.get("horario_saida", "")]

    # Metricas
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Hoje", len(mot_hoje))
    with m2:
        st.metric("Aguardando", len(mot_pendentes))
    with m3:
        st.metric("Liberados", len(mot_liberados))

    # Progresso
    pct = int((len(mot_liberados) / len(mot_hoje)) * 100) if mot_hoje else 0
    cor = "#00C853" if pct >= 80 else "#FF9900" if pct >= 50 else "#EF4444"
    st.markdown("<div style='background:#2d2d2d; border-radius:12px; padding:16px; text-align:center; border:1px solid #444; margin:16px 0;'><p style='font-size:36px; font-weight:900; color:" + cor + "; margin:0;'>" + str(pct) + "%</p><p style='color:#999; font-size:12px; margin:4px 0 0 0;'>PROGRESSO DO DIA</p><div style='width:100%; height:8px; background:#222; border-radius:4px; margin:10px 0; overflow:hidden;'><div style='height:100%; width:" + str(pct) + "%; background:" + cor + "; border-radius:4px;'></div></div></div>", unsafe_allow_html=True)

    # Lista de pendentes
    if mot_pendentes:
        st.markdown("### Aguardando no Patio")
        for m in mot_pendentes:
            st.markdown("<div class='yard-card'><strong>" + m["nome"] + "</strong> | " + m.get("placa","") + " | " + m.get("tipo_veiculo","") + "<br><span style='color:#888; font-size:12px;'>Chegou: " + m.get("horario_chegada","--:--") + " | Destino: " + m.get("destino","--") + "</span></div>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="success-box">Nenhum motorista aguardando no patio!</div>', unsafe_allow_html=True)

    # Ultimos liberados
    if mot_liberados:
        st.markdown("### Ultimos Liberados")
        for m in mot_liberados[:5]:
            st.markdown("<div class='yard-card' style='border-color:#00C853;'><strong>" + m["nome"] + "</strong> | " + m.get("placa","") + "<br><span style='color:#00C853; font-size:12px;'>Saiu: " + m.get("horario_saida","") + "</span></div>", unsafe_allow_html=True)

# ============================================================
# PAGINA: ENTRADA (registrar chegada)
# ============================================================

elif pagina == "Entrada":
    st.markdown("### Registrar Chegada")
    with st.form("form_entrada"):
        nome_mot = st.text_input("Nome do Motorista")
        c1, c2 = st.columns(2)
        with c1:
            placa_mot = st.text_input("Placa")
            tipo_veic = st.selectbox("Tipo de Veiculo", TIPOS_VEICULO)
        with c2:
            tel_mot = st.text_input("Telefone (opcional)")
            dest_mot = st.selectbox("Destino", ["ELP8", "ESA8", "DSP4", "Outro"])
        obs_mot = st.text_input("Observacao (opcional)")
        h_chegada = st.text_input("Horario de Chegada", value=agora_dt.strftime("%H:%M"))
        btn_registrar = st.form_submit_button("Registrar Entrada", use_container_width=True)
        if btn_registrar:
            if nome_mot:
                salvar_motorista({
                    "nome": nome_mot,
                    "placa": placa_mot,
                    "tipo_veiculo": tipo_veic,
                    "telefone": tel_mot,
                    "observacao": "",
                    "horario_chegada": h_chegada,
                    "horario_saida": "",
                    "observacoes": obs_mot,
                    "destino": dest_mot,
                    "data_chegada": hoje_str,
                    "data_registro": agora_dt.strftime("%d/%m/%Y %H:%M"),
                    "importado": False,
                    "foto": ""
                })
                st.markdown('<div class="success-box">' + nome_mot + ' registrado com sucesso!</div>', unsafe_allow_html=True)
                st.rerun()
            else:
                st.error("Informe o nome do motorista.")

    # Lista rapida dos que chegaram hoje
    st.markdown("---")
    st.markdown("### Chegadas de Hoje")
    motoristas = carregar_motoristas()
    mot_hoje = [m for m in motoristas if m.get("data_chegada","")[:10] == hoje_str]
    if mot_hoje:
        df = pd.DataFrame(mot_hoje)
        cols = ["nome", "placa", "tipo_veiculo", "horario_chegada", "destino", "horario_saida"]
        cols_ok = [c for c in cols if c in df.columns]
        st.dataframe(df[cols_ok], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma chegada registrada hoje.")

# ============================================================
# PAGINA: SAIDA (dar baixa / liberar motorista)
# ============================================================

elif pagina == "Saida":
    st.markdown("### Liberar Motorista (Saida)")
    motoristas = carregar_motoristas()
    mot_hoje = [m for m in motoristas if m.get("data_chegada","")[:10] == hoje_str]
    mot_pendentes = [m for m in mot_hoje if not m.get("horario_saida", "")]

    if mot_pendentes:
        st.markdown("**" + str(len(mot_pendentes)) + " motoristas aguardando liberacao:**")
        for mi in mot_pendentes:
            with st.expander(mi["nome"] + " | " + mi.get("placa","") + " | " + mi.get("tipo_veiculo","") + " | Dest: " + mi.get("destino","")):
                with st.form("form_saida_" + str(mi["id"])):
                    sc1, sc2 = st.columns(2)
                    with sc1:
                        h_saida = st.text_input("Horario de Saida", value=agora_dt.strftime("%H:%M"), key="hs_" + str(mi["id"]))
                    with sc2:
                        obs_saida = st.text_input("Observacao", value=mi.get("observacoes",""), key="obs_" + str(mi["id"]))
                    btn_liberar = st.form_submit_button("Liberar", use_container_width=True)
                    if btn_liberar:
                        atualizar_motorista(mi["id"], {"horario_saida": h_saida, "observacoes": obs_saida})
                        st.rerun()
    else:
        st.markdown('<div class="success-box">Todos os motoristas do dia ja foram liberados!</div>', unsafe_allow_html=True)

    # Liberados hoje
    mot_liberados = [m for m in mot_hoje if m.get("horario_saida", "")]
    if mot_liberados:
        st.markdown("---")
        st.markdown("### Liberados Hoje (" + str(len(mot_liberados)) + ")")
        df_lib = pd.DataFrame(mot_liberados)
        cols_lib = ["nome", "placa", "tipo_veiculo", "horario_chegada", "horario_saida", "destino"]
        cols_ok = [c for c in cols_lib if c in df_lib.columns]
        st.dataframe(df_lib[cols_ok], use_container_width=True, hide_index=True)

# ============================================================
# PAGINA: COMUNICACAO (mensagem rapida pro yard / WhatsApp)
# ============================================================

elif pagina == "Comunicacao":
    st.markdown("### Comunicacao Rapida")
    import urllib.parse

    motoristas = carregar_motoristas()
    mot_hoje = [m for m in motoristas if m.get("data_chegada","")[:10] == hoje_str]
    mot_pendentes = [m for m in mot_hoje if not m.get("horario_saida", "")]
    mot_liberados = [m for m in mot_hoje if m.get("horario_saida", "")]

    msg_tipo = st.selectbox("Tipo de mensagem:", [
        "Status do Patio",
        "Motorista Chegou",
        "Motorista Liberado",
        "Patio Lotado",
        "Mensagem Livre"
    ])

    numero_yard = st.text_input("Numero do Yard Marshall / Operacao (com DDD)", placeholder="11999999999")

    if msg_tipo == "Status do Patio":
        texto = "PATIO " + SITE + " - " + agora_dt.strftime("%d/%m/%Y %H:%M") + chr(10)
        texto += "Total hoje: " + str(len(mot_hoje)) + chr(10)
        texto += "Aguardando: " + str(len(mot_pendentes)) + chr(10)
        texto += "Liberados: " + str(len(mot_liberados)) + chr(10)
        if mot_pendentes:
            texto += chr(10) + "AGUARDANDO:" + chr(10)
            for mp in mot_pendentes:
                texto += "- " + mp["nome"] + " | " + mp.get("placa","") + " | " + mp.get("destino","") + chr(10)

    elif msg_tipo == "Motorista Chegou":
        if mot_pendentes:
            ultimo = mot_pendentes[0]
            texto = "CHEGADA " + SITE + " - " + agora_dt.strftime("%H:%M") + chr(10)
            texto += "Motorista: " + ultimo["nome"] + chr(10)
            texto += "Placa: " + ultimo.get("placa","") + chr(10)
            texto += "Veiculo: " + ultimo.get("tipo_veiculo","") + chr(10)
            texto += "Destino: " + ultimo.get("destino","")
        else:
            texto = "Nenhum motorista pendente."

    elif msg_tipo == "Motorista Liberado":
        if mot_liberados:
            ultimo_lib = mot_liberados[0]
            texto = "LIBERADO " + SITE + " - " + agora_dt.strftime("%H:%M") + chr(10)
            texto += "Motorista: " + ultimo_lib["nome"] + chr(10)
            texto += "Placa: " + ultimo_lib.get("placa","") + chr(10)
            texto += "Saiu: " + ultimo_lib.get("horario_saida","")
        else:
            texto = "Nenhum motorista liberado hoje."

    elif msg_tipo == "Patio Lotado":
        texto = "ALERTA " + SITE + " - PATIO LOTADO" + chr(10)
        texto += agora_dt.strftime("%d/%m/%Y %H:%M") + chr(10)
        texto += "Veiculos aguardando: " + str(len(mot_pendentes)) + chr(10)
        texto += "Solicitar apoio para liberacao!"

    else:
        texto = st.text_area("Digite sua mensagem:", height=100)

    st.markdown("---")
    st.markdown("**Preview:**")
    st.code(texto, language=None)

    if st.button("Enviar via WhatsApp", type="primary", use_container_width=True, key="btn_wpp"):
        texto_encoded = urllib.parse.quote(texto)
        if numero_yard.strip():
            num_limpo = numero_yard.strip().replace("-","").replace(" ","")
            link = "https://wa.me/55" + num_limpo + "?text=" + texto_encoded
        else:
            link = "https://wa.me/?text=" + texto_encoded
        st.markdown("[Abrir WhatsApp](" + link + ")")

# ============================================================
# RODAPE
# ============================================================

st.markdown("---")
st.markdown("<div style='text-align:center; padding:10px 0;'><p style='color:#555; font-size:10px;'>" + SITE + " Yard | First Mile Operations</p></div>", unsafe_allow_html=True)

