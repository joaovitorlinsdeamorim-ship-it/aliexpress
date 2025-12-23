import streamlit as st
import pandas as pd
import plotly.express as px
from gspread_pandas import Spread
import json
import base64
import re

# 1. Configuração da Página
st.set_page_config(page_title="Painel Perigo Imports", layout="wide")

# --- FUNÇÕES DE CONEXÃO ---

def conectar_google_sheets(aba_nome):
    try:
        # Recupera e limpa a string Base64 dos secrets
        raw_b64 = st.secrets["gcp_base64"]
        clean_b64 = re.sub(r'[^a-zA-Z0-9+/=]', '', raw_b64)
        
        # Decodifica de Base64 para JSON
        decoded_bytes = base64.b64decode(clean_b64)
        json_str = decoded_bytes.decode('utf-8')
        creds_dict = json.loads(json_str)
        
        url = st.secrets["spreadsheet_url"]
        # Retorna o objeto Spread configurado para a aba desejada
        return Spread(url, config=creds_dict, sheet=aba_nome)
    except Exception as e:
        st.error(f"Erro crítico de conexão: {e}")
        return None

def carregar_dados(aba_nome):
    s = conectar_google_sheets(aba_nome)
    if s:
        try:
            # MÉTODO CORRETO PARA LEITURA: sheet_to_df
            return s.sheet_to_df(index=None)
        except Exception:
            # Caso a aba esteja vazia ou não exista, cria estrutura básica
            if aba_nome == "usuarios":
                return pd.DataFrame(columns=["nome", "usuario", "senha"])
            return pd.DataFrame()
    return pd.DataFrame()

def salvar_dados(df_novo, aba_nome):
    s = conectar_google_sheets(aba_nome)
    if s:
        try:
            # MÉTODO CORRETO PARA ESCRITA: df_to_sheet
            # index=False: não cria coluna de índice na planilha
            # replace=True: limpa a aba antes de colar os novos dados
            s.df_to_sheet(df=df_novo, index=False, replace=True)
            return True
        except Exception as e:
            st.error(f"Erro ao salvar na planilha: {e}")
            return False
    return False

# --- LÓGICA DE ACESSO (LOGIN / CADASTRO) ---

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.sidebar.title("Navegação")
    menu = st.sidebar.radio("Selecione:", ["Login", "Cadastro"])
    
    if menu == "Login":
        st.title("🔐 Login do Sistema")
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            df_u = carregar_dados("usuarios")
            if not df_u.empty and u in df_u['usuario'].astype(str).values:
                usuario_row = df_u[df_u['usuario'] == u]
                senha_db = str(usuario_row['senha'].values[0])
                if p == senha_db:
                    st.session_state.update({"logged_in": True, "username": u})
                    st.rerun()
            st.error("Usuário ou senha incorretos.")
            
    else:
        st.title("📝 Cadastro")
        nome = st.text_input("Nome Completo")
        user = st.text_input("Nome de Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Finalizar Cadastro"):
            df_u = carregar_dados("usuarios")
            # Adiciona o novo registro ao DataFrame existente
            novo_u = pd.concat([df_u, pd.DataFrame([{"nome": nome, "usuario": user, "senha": senha}])], ignore_index=True)
            if salvar_dados(novo_u, "usuarios"):
                st.success("Usuário cadastrado com sucesso! Volte para a tela de Login.")

else:
    # --- DASHBOARD LOGADO ---
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logged_in": False}))
    st.title(f"🚢 Controle de Importações: {st.session_state.username}")

    with st.expander("➕ Registrar Novo Item", expanded=True):
        c1, c2, c3 = st.columns(3)
        p_nome = c1.text_input("Produto")
        p_custo = c2.number_input("Custo Unitário (R$)", min_value=0.0)
        p_qtd = c3.number_input("Quantidade", min_value=1)
        p_margem = st.slider("Margem de Lucro (%)", 0, 100, 30)
        
        invest = p_custo * p_qtd
        lucro = (p_custo * (p_margem/100)) * p_qtd

        if st.button("Gravar na Planilha"):
            df_d = carregar_dados("dados")
            nova_linha = pd.DataFrame([{
                "produto": p_nome, "custo": p_custo, "quantidade": p_qtd, 
                "margem": p_margem, "investimento": invest, 
                "lucro": lucro, "usuario": st.session_state.username
            }])
            if salvar_dados(pd.concat([df_d, nova_linha], ignore_index=True), "dados"):
                st.success("Lançamento salvo com sucesso!")
                st.rerun()

    st.divider()
    
    # Exibição dos dados salvos
    df_g = carregar_dados("dados")
    if not df_g.empty:
        # Filtra para mostrar apenas os dados do usuário logado
        meus_dados = df_g[df_g['usuario'] == st.session_state.username]
        st.subheader("📋 Histórico de Lançamentos")
        st.dataframe(meus_dados, use_container_width=True)
        
        if not meus_dados.empty:
            fig = px.bar(meus_dados, x="produto", y=["investimento", "lucro"], 
                         barmode="group", title="Resumo Financeiro por Produto")
            st.plotly_chart(fig)
    else:
        st.info("Nenhum dado cadastrado até o momento.")
