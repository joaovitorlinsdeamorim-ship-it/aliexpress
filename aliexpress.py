import streamlit as st
import pandas as pd
from gspread_pandas import Spread
import hashlib

# Função para criptografar senha
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema de Importação", layout="wide")

# --- CONEXÃO COM GOOGLE SHEETS (Exemplo simplificado) ---
# Nota: Para produção, use st.connection("gsheets")
def carregar_usuarios():
    # Aqui você usaria o link da sua planilha
    # Por agora, vamos simular uma lista para você testar
    return {"admin": make_hashes("1234")}

# --- INTERFACE DE AUTENTICAÇÃO ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    menu = ["Login", "Cadastro"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Login":
        st.subheader("Login de Acesso")
        user = st.text_input("Usuário")
        password = st.text_input("Senha", type='password')
        if st.button("Entrar"):
            hashed_psw = make_hashes(password)
            # Verificação (Substituir pela consulta na planilha)
            if user == "admin" and password == "1234":
                st.session_state['logged_in'] = True
                st.success("Logado como {}".format(user))
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")

    elif choice == "Cadastro":
        st.subheader("Criar Nova Conta")
        new_user = st.text_input("Escolha um Usuário")
        new_password = st.text_input("Escolha uma Senha", type='password')
        if st.button("Cadastrar"):
            # Aqui você adicionaria uma linha na sua Planilha Google
            st.success("Conta criada com sucesso! Vá para o Login.")

# --- ÁREA DO SISTEMA (APÓS LOGIN) ---
else:
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logged_in": False}))
    st.title("🚢 Sistema de Controle de Importação")
    
    # --- COLOQUE AQUI O SEU CÓDIGO QUE ESTAVA NO LABS ---
    st.info("O seu código de lógica de importação entra aqui.")
    produto = st.text_input("Nome do Item Importado")
    if st.button("Registrar Importação"):
        st.write(f"Item {produto} registrado no banco de dados!")
