import streamlit as st
import pandas as pd
from gspread_pandas import Spread
import json
import base64
import re

def carregar_dados(aba_nome):
    try:
        # Pega a string do segredo
        raw_b64 = st.secrets["gcp_base64"]
        
        # Limpeza pesada: remove espaços, quebras de linha ou aspas acidentais
        # que possam ter vindo na colagem do código gigante
        clean_b64 = re.sub(r'[^a-zA-Z0-9+/=]', '', raw_b64)
        
        # Decodifica de Base64 para Texto (JSON)
        decoded_bytes = base64.b64decode(clean_b64)
        json_str = decoded_bytes.decode('utf-8')
        
        # Transforma o texto em dicionário para o Google
        creds_dict = json.loads(json_str)
        
        s = Spread(st.secrets["spreadsheet_url"], config=creds_dict, sheet=aba_nome)
        return s.df
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        # Retorna estrutura mínima para não travar o Login/Cadastro
        if aba_nome == "usuarios":
            return pd.DataFrame(columns=["nome", "usuario", "senha"])
        return pd.DataFrame()

# A função de salvar segue a mesma lógica de decodificação
def salvar_dados(df_novo, aba_nome):
    try:
        raw_b64 = st.secrets["gcp_base64"]
        clean_b64 = re.sub(r'[^a-zA-Z0-9+/=]', '', raw_b64)
        json_str = base64.b64decode(clean_b64).decode('utf-8')
        creds_dict = json.loads(json_str)
        
        s = Spread(st.secrets["spreadsheet_url"], config=creds_dict, sheet=aba_nome)
        s.df = df_novo
        s.save_to_sheet(index=False, replace=True)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False
