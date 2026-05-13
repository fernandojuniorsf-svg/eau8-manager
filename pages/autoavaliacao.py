
import streamlit as st
import pandas as pd
import datetime
import os
import json

# ============================================
# CONFIGURAÇÃO INICIAL
# ============================================

st.set_page_config(page_title="EUA8 - Autoavaliação", page_icon="📋", layout="centered")

# Pasta para salvar dados
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

RESPOSTAS_FILE = os.path.join(DATA_DIR, "respostas_autoavaliacao.csv")
PERGUNTAS_FILE = os.path.join(DATA_DIR, "perguntas.json")

# ============================================
# USUÁRIOS E SENHAS
# ============================================

USUARIOS = {
    "fernando": {"senha":[PASSWORD]26", "nome": "Fernando Júnior", "role": "admin"},
    "mayra": {"senha":[PASSWORD]ra", "nome": "Mayra", "role": "associado"},
    "carol": {"senha":[PASSWORD]ol", "nome": "Carol", "role": "associado"},
    "amanda": {"senha":[PASSWORD]da", "nome": "Amanda", "role": "associado"},
    "helen": {"senha":[PASSWORD]en", "nome": "Helen", "role": "associado"},
    "nicole": {"senha":[PASSWORD]le", "nome": "Nicole", "role": "associado"},
    "fernanda": {"senha":[PASSWORD]da", "nome": "Fernanda", "role": "associado"},
    "byanca": {"senha":[PASSWORD]ca", "nome": "Byanca", "role": "associado"},
    "kalebe": {"senha":[PASSWORD]be", "nome": "Kalebe", "role": "associado"},
}

# ============================================
# PERGUNTAS PADRÃO (editáveis pelo admin)
# ============================================

PERGUNTAS_PADRAO = {
    "texto": [
        {"id": "pontos_fortes", "pergunta": "Quais são seus 3 pontos fortes na operação?", "hint": "O que você faz bem? No que se destaca?"},
        {"id": "pontos_melhorar", "pergunta": "O que você sente que precisa melhorar?", "hint": "Seja honesto. Isso me ajuda a te apoiar."},
        {"id": "acao_melhorar", "pergunta": "O que VOCÊ pode fazer pra melhorar nesses pontos?", "hint": "Pense em ações concretas que dependem de você."},
        {"id": "equipe_melhorar", "pergunta": "O que a equipe/operação pode melhorar no geral?", "hint": "O que você enxerga que poderia ser diferente?"},
        {"id": "feedback_lider", "pergunta": "O que eu (Fernando) posso fazer pra te ajudar?", "hint": "Pode ser qualquer coisa: treinamento, posicionamento, feedback..."},
        {"id": "mensagem_time", "pergunta": "Mensagem pro time (opcional)", "hint": "Algo que queira compartilhar com todos..."},
    ],
    "escala": [
        {"id": "comunicacao", "pergunta": "Comunicação com o time"},
        {"id": "urgencia", "pergunta": "Senso de urgência"},
        {"id": "qualidade", "pergunta": "Qualidade (atenção a erros)"},
        {"id": "trabalho_equipe", "pergunta": "Trabalho em equipe"},
    ],
    "selecao": [
        {"id": "posicao_aprender", "pergunta": "Posição que gostaria de aprender", "opcoes": [
            "Pick to Buffer", "Stow", "Receiver", "Unloader",
            "Yard Marshall", "Spider", "Carregamento", "Todas!",
            "Estou bem na minha posição atual"
        ]}
    ]
}


def carregar_perguntas():
    """Carrega perguntas do arquivo JSON ou usa padrão"""
    if os.path.exists(PERGUNTAS_FILE):
        with open(PERGUNTAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return PERGUNTAS_PADRAO


def salvar_perguntas(perguntas):
    """Salva perguntas editadas no JSON"""
    with open(PERGUNTAS_FILE, "w", encoding="utf-8") as f:
        json.dump(perguntas, f, ensure_ascii=False, indent=2)


def salvar_resposta(dados):
    """Salva resposta no CSV"""
    df_novo = pd.DataFrame([dados])
    if os.path.exists(RESPOSTAS_FILE):
        df_existente = pd.read_csv(RESPOSTAS_FILE)
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
    else:
        df_final = df_novo
    df_final.to_csv(RESPOSTAS_FILE, index=False)


def carregar_respostas():
    """Carrega todas as respostas"""
    if os.path.exists(RESPOSTAS_FILE):
        return pd.read_csv(RESPOSTAS_FILE)
    return pd.DataFrame()


# ============================================
# TELA DE LOGIN
# ============================================

def tela_login():
    st.markdown("## 🔐 Login — EUA8")
    st.caption("Digite seu usuário e senha fornecidos pelo Fernando.")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        usuario = st.text_input("Usuário", placeholder="Ex: mayra").lower().strip()
        senha = st.text_input("Senha", type="password", placeholder="Sua senha")

        if st.button("Entrar", use_container_width=True):
            if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
                st.session_state["logado"] = True
                st.session_state["usuario"] = usuario
                st.session_state["nome"] = USUARIOS[usuario]["nome"]
                st.session_state["role"] = USUARIOS[usuario]["role"]
                st.rerun()
            else:
                st.error("❌ Usuário ou senha incorretos.")


# ============================================
# FORMULÁRIO DO ASSOCIADO
# ============================================

def tela_formulario():
    perguntas = carregar_perguntas()

    st.markdown("## 📋 Autoavaliação — EUA8")
    st.markdown(f"**Olá, {st.session_state['nome']}!** 👋")
    st.caption("Responda com sinceridade. Não existe resposta certa ou errada. Suas respostas são confidenciais.")

    st.divider()

    with st.form("form_autoavaliacao"):
        respostas = {}
        respostas["nome"] = st.session_state["nome"]
        respostas["data"] = str(datetime.date.today())
        respostas["hora"] = datetime.datetime.now().strftime("%H:%M")

        # Perguntas de texto
        st.subheader("✍️ Suas Respostas")
        for p in perguntas["texto"]:
            respostas[p["id"]] = st.text_area(
                p["pergunta"],
                placeholder=p.get("hint", ""),
                height=100
            )

        st.divider()

        # Perguntas de seleção
        st.subheader("🎯 Posição")
        for p in perguntas["selecao"]:
            respostas[p["id"]] = st.selectbox(p["pergunta"], p["opcoes"])

        st.divider()

        # Perguntas de escala
        st.subheader("⭐ Autoavaliação (1 a 5)")
        for p in perguntas["escala"]:
            respostas[p["id"]] = st.slider(p["pergunta"], 1, 5, 3)

        st.divider()

        enviado = st.form_submit_button("✅ Enviar Respostas", use_container_width=True)

        if enviado:
            if not respostas.get("pontos_fortes"):
                st.error("Por favor, preencha pelo menos os pontos fortes.")
            else:
                salvar_resposta(respostas)
                st.success("✅ Resposta enviada com sucesso! Obrigado! 🎉")
                st.balloons()

    st.divider()
    if st.button("🚪 Sair"):
        st.session_state.clear()
        st.rerun()


# ============================================
# PAINEL ADMIN (Fernando)
# ============================================

def tela_admin():
    st.markdown("## 🎯 Painel Admin — EUA8")
    st.markdown(f"**Bem-vindo, {st.session_state['nome']}!**")

    tab1, tab2, tab3 = st.tabs(["📊 Respostas", "✏️ Editar Perguntas", "👥 Usuários"])

    # --- ABA 1: VER RESPOSTAS ---
    with tab1:
        df = carregar_respostas()
        if df.empty:
            st.info("Nenhuma resposta ainda. Aguardando o time preencher! 📝")
        else:
            st.metric("Total de Respostas", len(df))

            # Filtro por nome
            nomes = ["Todos"] + sorted(df["nome"].unique().tolist())
            filtro = st.selectbox("Filtrar por nome:", nomes)

            if filtro != "Todos":
                df = df[df["nome"] == filtro]

            st.dataframe(df, use_container_width=True)

            # Botão de exportar
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Exportar para Excel/CSV",
                csv,
                f"autoavaliacao_eua8_{datetime.date.today()}.csv",
                "text/csv",
                use_container_width=True
            )

    # --- ABA 2: EDITAR PERGUNTAS ---
    with tab2:
        st.caption("Edite as perguntas que aparecem pro time. Clique em Salvar quando terminar.")
        perguntas = carregar_perguntas()

        st.subheader("📝 Perguntas de Texto")
        novas_texto = []
        for i, p in enumerate(perguntas["texto"]):
            with st.expander(f"Pergunta {i+1}: {p['pergunta'][:50]}..."):
                nova_pergunta = st.text_input(f"Pergunta {i+1}", value=p["pergunta"], key=f"pt_{i}")
                novo_hint = st.text_input(f"Dica {i+1}", value=p.get("hint", ""), key=f"ph_{i}")
                novas_texto.append({"id": p["id"], "pergunta": nova_pergunta, "hint": novo_hint})

        st.subheader("⭐ Perguntas de Escala (1-5)")
        novas_escala = []
        for i, p in enumerate(perguntas["escala"]):
            nova = st.text_input(f"Escala {i+1}", value=p["pergunta"], key=f"pe_{i}")
            novas_escala.append({"id": p["id"], "pergunta": nova})

        if st.button("💾 Salvar Perguntas", use_container_width=True):
            perguntas["texto"] = novas_texto
            perguntas["escala"] = novas_escala
            salvar_perguntas(perguntas)
            st.success("✅ Perguntas atualizadas!")

    # --- ABA 3: VER USUÁRIOS ---
    with tab3:
        st.caption("Usuários cadastrados no sistema:")
        dados_users = []
        for user, info in USUARIOS.items():
            dados_users.append({
                "Usuário": user,
                "Nome": info["nome"],
                "Senha": info["senha"],
                "Tipo": info["role"]
            })
        st.dataframe(pd.DataFrame(dados_users), use_container_width=True)
        st.info("💡 Para adicionar/remover usuários, edite o dicionário USUARIOS no código.")

    st.divider()
    if st.button("🚪 Sair"):
        st.session_state.clear()
        st.rerun()


# ============================================
# APP PRINCIPAL
# ============================================

def main():
    if "logado" not in st.session_state:
        tela_login()
    elif st.session_state["role"] == "admin":
        tela_admin()
    else:
        tela_formulario()


if __name__ == "__main__":
    main()

