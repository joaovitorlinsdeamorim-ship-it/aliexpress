import streamlit as st
import pandas as pd
import plotly.express as px
from gspread_pandas import Spread
import json
import base64
import re

# 1. Configuração Inicial da Página
st.set_page_config(page_title="Painel Perigo Imports", layout="wide")

# --- FUNÇÕES DE CONEXÃO ---

def conectar_google_sheets(aba_nome):
    """Decodifica o segredo Base64 e estabelece a conexão com a planilha."""
    try:
        # Recupera a string Base64 dos secrets e limpa caracteres invisíveis
        raw_b64 = st.secrets["gcp_base64"]
        clean_b64 = re.sub(r'[^a-zA-Z0-9+/=]', '', raw_b64)
        
        # Decodifica de Base64 para dicionário JSON
        decoded_bytes = base64.b64decode(clean_b64)
        json_str = decoded_bytes.decode('utf-8')
        creds_dict = json.loads(json_str)
        
        # Conecta à planilha usando a URL definida nos secrets
        url = st.secrets["spreadsheet_url"]
        return Spread(url, config=creds_dict, sheet=aba_nome)
    except Exception as e:
        st.error(f"Erro crítico de conexão: {e}")
        return None

def carregar_dados(aba_nome):
    """Carrega dados de uma aba específica e transforma em DataFrame."""
    s = conectar_google_sheets(aba_nome)
    if s:
        try:
            # CORREÇÃO: Método correto para converter aba em DataFrame
            return s.sheet_to_df(index=None)
        except Exception:
            # Se a aba estiver vazia, define colunas padrão
            if aba_nome == "usuarios":
                return pd.DataFrame(columns=["nome", "usuario", "senha"])
            return pd.DataFrame()
    return pd.DataFrame()

def salvar_dados(df_novo, aba_nome):
    """Grava o DataFrame atualizado de volta na planilha Google."""
    s = conectar_google_sheets(aba_nome)
    if s:
        try:
            s.df = df_novo
            # Substitui o conteúdo da aba pelo novo DataFrame
            s.save_to_sheet(index=False, replace=True)
            return True
        except Exception as e:
            st.error(f"Erro ao salvar na planilha: {e}")
            return False
    return False

# --- LOGICA DE ACESSO (LOGIN / CADASTRO) ---

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
                # Localiza a senha do usuário
                senha_db = str(df_u[df_u['usuario'] == u]['senha'].values[0])
                if p == senha_db:
                    st.session_state.update({"logged_in": True, "username": u})
                    st.rerun()
            st.error("Dados inválidos. Verifique usuário e senha.")
            
    else:
        st.title("📝 Cadastro de Novo Usuário")
        nome = st.text_input("Nome Completo")
        user = st.text_input("Nome de Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Finalizar Cadastro"):
            df_u = carregar_dados("usuarios")
            novo_u = pd.concat([df_u, pd.DataFrame([{"nome": nome, "usuario": user, "senha": senha}])], ignore_index=True)
            if salvar_dados(novo_u, "usuarios"):
                st.success("Cadastro realizado com sucesso! Vá para a tela de Login.")

else:
    # --- ÁREA LOGADA: DASHBOARD ---
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logged_in": False}))
    st.title(f"🚢 Painel Perigo Imports: {st.session_state.username}")

    with st.expander("➕ Registrar Nova Importação", expanded=True):
        c1, c2, c3 = st.columns(3)
        p_nome = c1.text_input("Nome do Produto")
        p_custo = c2.number_input("Custo Unitário (R$)", min_value=0.0)
        p_qtd = c3.number_input("Quantidade", min_value=1)
        p_margem = st.slider("Margem de Lucro (%)", 0, 100, 30)
        
        # Cálculos Automáticos
        investimento = p_custo * p_qtd
        venda_sugerida = p_custo * (1 + p_margem/100)
        lucro_estimado = (venda_sugerida - p_custo) * p_qtd

        if st.button("Gravar Dados"):
            df_d = carregar_dados("dados")
            nova_linha = pd.DataFrame([{
                "produto": p_nome, "custo": p_custo, "quantidade": p_qtd, 
                "margem": p_margem, "investimento": investimento, 
                "lucro": lucro_estimado, "usuario": st.session_state.username
            }])
            if salvar_dados(pd.concat([df_d, nova_linha], ignore_index=True), "dados"):
                st.success("Lançamento gravado!")
                st.rerun()

    # Resumo do Dashboard
    st.divider()
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Investimento", f"R$ {investimento:,.2f}")
    col_m2.metric("Venda Unitária", f"R$ {venda_sugerida:,.2f}")
    col_m3.metric("Lucro Estimado", f"R$ {lucro_estimado:,.2f}")

    # Gráfico de Distribuição
    fig = px.pie(
        values=[max(0.1, investimento), max(0.1, lucro_estimado)], 
        names=["Custo de Aquisição", "Margem de Lucro"], 
        hole=0.4,
        color_discrete_sequence=['#EF553B', '#00CC96']
    )
    st.plotly_chart(fig)

    # Listagem de itens do usuário
    st.subheader("📋 Meus Itens Cadastrados")
    df_g = carregar_dados("dados")
    if not df_g.empty:
        meus_dados = df_g[df_g['usuario'] == st.session_state.username]
        st.dataframe(meus_dados, use_container_width=True)
    else:
        st.info("Nenhum dado encontrado.")
