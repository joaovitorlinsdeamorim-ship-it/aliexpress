import streamlit as st
import pandas as pd
import plotly.express as px
from gspread_pandas import Spread
import os

st.set_page_config(page_title="Sistema de Importação", layout="wide")

# --- FUNÇÃO DE CONEXÃO DIRETA (SEM ST.CONNECTION) ---
def carregar_dados(aba_nome):
    try:
        # Pegamos os dados do segredo e limpamos a chave
        creds = st.secrets["connections"]["gsheets"].to_dict()
        creds["private_key"] = creds["private_key"].replace("\\n", "\n")
        
        # Conectamos usando gspread-pandas que aceita o dicionário direto
        s = Spread(st.secrets["spreadsheet_url"], config=creds, sheet=aba_nome)
        return s.df
    except Exception as e:
        return pd.DataFrame()

def salvar_dados(df_novo, aba_nome):
    try:
        creds = st.secrets["connections"]["gsheets"].to_dict()
        creds["private_key"] = creds["private_key"].replace("\\n", "\n")
        s = Spread(st.secrets["spreadsheet_url"], config=creds, sheet=aba_nome)
        s.df = df_novo
        s.save_to_sheet(index=False, replace=True)
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

# --- LÓGICA DE LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.sidebar.title("Acesso")
    opcao = st.sidebar.radio("Selecione:", ["Login", "Cadastro"])

    if opcao == "Login":
        st.title("🔐 Login")
        user = st.text_input("Usuário")
        pw = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            df_usuarios = carregar_dados("usuarios")
            if not df_usuarios.empty and user in df_usuarios['usuario'].astype(str).values:
                senha_correta = str(df_usuarios[df_usuarios['usuario'] == user]['senha'].values[0])
                if pw == senha_correta:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = user
                    st.rerun()
            st.error("Usuário ou senha inválidos.")

    else:
        st.title("📝 Cadastro")
        n = st.text_input("Nome")
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("Finalizar Cadastro"):
            df_u = carregar_dados("usuarios")
            novo = pd.DataFrame([{"nome": n, "usuario": u, "senha": p}])
            salvar_dados(pd.concat([df_u, novo], ignore_index=True), "usuarios")
            st.success("Cadastrado com sucesso! Mude para Login.")

else:
    st.sidebar.write(f"Logado como: **{st.session_state.username}**")
    if st.sidebar.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("🚢 Controle de Importações")

    # Painel de Entrada
    with st.expander("➕ Novo Item", expanded=True):
        c1, c2, c3 = st.columns([3, 1, 1])
        nome_p = c1.text_input("Produto")
        custo_u = c2.number_input("Custo (R$)", min_value=0.0)
        quant = c3.number_input("Qtd", min_value=1)
        margem = st.slider("Margem (%)", 0, 100, 25)
        
        invest = custo_u * quant
        venda_u = custo_u * (1 + margem/100)
        lucro_e = (venda_u - custo_u) * quant

        if st.button("Salvar Registro"):
            df_d = carregar_dados("dados")
            nova_l = pd.DataFrame([{
                "produto": nome_p, "custo": custo_u, "quantidade": quant,
                "margem": margem, "investimento": invest, "lucro": lucro_e,
                "usuario": st.session_state.username
            }])
            salvar_dados(pd.concat([df_d, nova_l], ignore_index=True), "dados")
            st.success("Salvo!")
            st.rerun()

    # Dashboard
    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Investimento", f"R$ {invest:,.2f}")
    m2.metric("Venda Unit.", f"R$ {venda_u:,.2f}")
    m3.metric("Lucro Est.", f"R$ {lucro_e:,.2f}")

    fig = px.pie(values=[max(0.1, invest), max(0.1, lucro_e)], names=["Custo", "Lucro"], hole=0.4)
    st.plotly_chart(fig)

    st.subheader("📋 Meus Itens")
    df_g = carregar_dados("dados")
    if not df_g.empty:
        st.dataframe(df_g[df_g['usuario'] == st.session_state.username], use_container_width=True)
