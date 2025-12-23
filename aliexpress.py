import streamlit as st
import pandas as pd
import plotly.express as px
from gspread_pandas import Spread
import json
import base64

st.set_page_config(page_title="Sistema de Importação", layout="wide")

# --- CONEXÃO BLINDADA ---
def carregar_dados(aba_nome):
    try:
        # Decodifica o Base64 que você colou nos secrets
        encoded_creds = st.secrets["gcp_base64"]
        decoded_creds = base64.b64decode(encoded_creds).decode('utf-8')
        creds_dict = json.loads(decoded_creds)
        
        # Conecta à planilha
        s = Spread(st.secrets["spreadsheet_url"], config=creds_dict, sheet=aba_nome)
        return s.df
    except Exception as e:
        if aba_nome == "usuarios":
            return pd.DataFrame(columns=["nome", "usuario", "senha"])
        return pd.DataFrame()

def salvar_dados(df_novo, aba_nome):
    try:
        encoded_creds = st.secrets["gcp_base64"]
        decoded_creds = base64.b64decode(encoded_creds).decode('utf-8')
        creds_dict = json.loads(decoded_creds)
        
        s = Spread(st.secrets["spreadsheet_url"], config=creds_dict, sheet=aba_nome)
        s.df = df_novo
        s.save_to_sheet(index=False, replace=True)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# --- LÓGICA DO APP ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    menu = st.sidebar.radio("Navegação", ["Login", "Cadastro"])
    if menu == "Login":
        st.title("🔐 Login")
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            df_u = carregar_dados("usuarios")
            if not df_u.empty and u in df_u['usuario'].astype(str).values:
                senha = str(df_u[df_u['usuario'] == u]['senha'].values[0])
                if p == senha:
                    st.session_state.update({"logged_in": True, "username": u})
                    st.rerun()
            st.error("Dados incorretos.")
    else:
        st.title("📝 Cadastro")
        nome = st.text_input("Nome")
        user = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Cadastrar"):
            df_u = carregar_dados("usuarios")
            novo = pd.concat([df_u, pd.DataFrame([{"nome": nome, "usuario": user, "senha": senha}])], ignore_index=True)
            if salvar_dados(novo, "usuarios"):
                st.success("Sucesso! Vá para Login.")
else:
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logged_in": False}))
    st.title(f"🚢 Controle de {st.session_state.username}")

    with st.expander("➕ Novo Item"):
        c1, c2, c3 = st.columns(3)
        prod = c1.text_input("Produto")
        custo = c2.number_input("Custo Unit.", min_value=0.0)
        qtd = c3.number_input("Qtd", min_value=1)
        margem = st.slider("Margem %", 0, 100, 30)
        
        invest = custo * qtd
        lucro = (custo * (margem/100)) * qtd

        if st.button("Salvar Dados"):
            df_d = carregar_dados("dados")
            nova_f = pd.concat([df_d, pd.DataFrame([{"produto": prod, "custo": custo, "quantidade": qtd, "margem": margem, "investimento": invest, "lucro": lucro, "usuario": st.session_state.username}])], ignore_index=True)
            if salvar_dados(nova_f, "dados"):
                st.success("Salvo com sucesso!")
                st.rerun()

    st.divider()
    df_g = carregar_dados("dados")
    if not df_g.empty:
        st.subheader("📋 Seus Lançamentos")
        st.dataframe(df_g[df_g['usuario'] == st.session_state.username], use_container_width=True)
