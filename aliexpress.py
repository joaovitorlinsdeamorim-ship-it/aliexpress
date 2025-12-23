import streamlit as st
import pandas as pd
from gspread_pandas import Spread
import json
import base64
import re

def limpar_e_decodificar(b64_string):
    # Remove qualquer caractere que não pertença ao alfabeto Base64
    # Isso elimina espaços, aspas extras ou quebras de linha invisíveis
    b64_limpo = re.sub(r'[^a-zA-Z0-9+/=]', '', b64_string)
    
    # Decodifica e remove espaços nas extremidades da string final
    decoded_bytes = base64.b64decode(b64_limpo)
    return decoded_bytes.decode('utf-8').strip()

def carregar_dados(aba_nome):
    try:
        raw_b64 = st.secrets["gcp_base64"]
        json_str = limpar_e_decodificar(raw_b64)
        creds_dict = json.loads(json_str)
        
        s = Spread(st.secrets["spreadsheet_url"], config=creds_dict, sheet=aba_nome)
        return s.df
    except Exception as e:
        # Se for o primeiro acesso, cria colunas para evitar erros na tabela
        if aba_nome == "usuarios":
            return pd.DataFrame(columns=["nome", "usuario", "senha"])
        return pd.DataFrame()

def salvar_dados(df_novo, aba_nome):
    try:
        raw_b64 = st.secrets["gcp_base64"]
        json_str = limpar_e_decodificar(raw_b64)
        creds_dict = json.loads(json_str)
        
        s = Spread(st.secrets["spreadsheet_url"], config=creds_dict, sheet=aba_nome)
        s.df = df_novo
        s.save_to_sheet(index=False, replace=True)
        return True
    except Exception as e:
        st.error(f"Erro técnico ao salvar: {e}")
        return False
