import streamlit as st
import pandas as pd
from gspread_pandas import Spread
import json
import base64
import re

# Configuração da página sempre no topo para evitar erros de renderização
st.set_page_config(page_title="Sistema Perigo Imports", layout="wide")

def carregar_credenciais():
    try:
        # Recupera a string Base64 do seu campo 'gcp_base64' nos secrets
        raw_b64 = st.secrets["gcp_base64"]
        
        # Limpeza pesada para garantir que nenhum caractere invisível quebre o Base64
        clean_b64 = re.sub(r'[^a-zA-Z0-9+/=]', '', raw_b64)
        
        # Decodifica de Base64 para JSON puro
        decoded_bytes = base64.b64decode(clean_b64)
        json_str = decoded_bytes.decode('utf-8')
        return json.loads(json_str)
    except Exception as e:
        st.error(f"Erro ao processar segredos: {e}")
        return None

def carregar_dados(aba_nome):
    creds = carregar_credenciais()
    if not creds:
        return pd.DataFrame()
    
    try:
        url = st.secrets["spreadsheet_url"]
        s = Spread(url, config=creds, sheet=aba_nome)
        return s.df
    except Exception as e:
        st.warning(f"Aba '{aba_nome}' não encontrada ou erro de acesso: {e}")
        return pd.DataFrame()

# --- INTERFACE ---

st.title("🚢 Painel Perigo Imports")

# Teste inicial de conexão para tirar a tela preta
if "gsheets_connected" not in st.session_state:
    with st.spinner("Conectando ao banco de dados..."):
        df_teste = carregar_dados("usuarios")
        if not df_teste.empty:
            st.session_state["gsheets_connected"] = True
            st.success("Conexão estabelecida com sucesso!")
        else:
            st.session_state["gsheets_connected"] = False

# Se a conexão falhar, mostra o motivo em vez da tela preta
if not st.session_state["gsheets_connected"]:
    st.error("⚠️ Falha na conexão inicial. Verifique se o e-mail da conta de serviço é Editor na sua planilha.")
    st.info(f"E-mail da conta: perigodata-chaves@perigodata.iam.gserviceaccount.com")
else:
    # Lógica de Login/Cadastro simplificada para teste
    st.write("### Bem-vindo! O sistema está pronto.")
    # Adicione aqui o restante do seu código de login que enviamos anteriormente
