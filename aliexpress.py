import streamlit as st
import pandas as pd
import plotly.express as px
from gspread_pandas import Spread, Client
import json
import io

st.set_page_config(page_title="Sistema de Importação", layout="wide")

# --- FUNÇÃO DE CONEXÃO AJUSTADA ---
def carregar_dados(aba_nome):
    try:
        # Lemos a string do segredo
        creds_info = st.secrets["gcp_service_account"]
        # Transformamos a string em um dicionário real
        creds_dict = json.loads(creds_info)
        
        # Conectamos usando o dicionário diretamente
        s = Spread(st.secrets["spreadsheet_url"], config=creds_dict, sheet=aba_nome)
        return s.df
    except Exception as e:
        # Se a planilha estiver vazia, retorna DF com colunas padrão
        if aba_nome == "usuarios":
            return pd.DataFrame(columns=["nome", "usuario", "senha"])
        return pd.DataFrame()

def salvar_dados(df_novo, aba_nome):
    try:
        creds_dict = json.loads(st.secrets["gcp_service_account"])
        s = Spread(st.secrets["spreadsheet_url"], config=creds_dict, sheet=aba_nome)
        s.df = df_novo
        # Salva garantindo que substitua o conteúdo antigo
        s.save_to_sheet(index=False, replace=True)
        return True
    except Exception as e:
        st.error(f"Erro técnico ao salvar: {e}")
        return False

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
            df_u = carregar_dados("usuarios")
            if not df_u.empty and user in df_u['usuario'].astype(str).values:
                senha_correta = str(df_u[df_u['usuario'] == user]['senha'].values[0])
                if pw == senha_correta:
                    st.session_state.update({"logged_in": True, "username": user})
                    st.rerun()
            st.error("Usuário ou senha inválidos.")
    else:
        st.title("📝 Cadastro")
        n, u, p = st.text_input("Nome"), st.text_input("Usuário"), st.text_input("Senha", type="password")
        if st.button("Finalizar Cadastro"):
            df_u = carregar_dados("usuarios")
            novo_df = pd.concat([df_u, pd.DataFrame([{"nome": n, "usuario": u, "senha": p}])], ignore_index=True)
            if salvar_dados(novo_df, "usuarios"):
                st.success("Cadastrado! Mude para Login.")

else:
    # --- PAINEL PRINCIPAL ---
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logged_in": False}))
    st.title(f"🚢 Painel: {st.session_state.username}")

    with st.expander("➕ Novo Item"):
        c1, c2, c3 = st.columns(3)
        prod = c1.text_input("Produto")
        custo = c2.number_input("Custo Unit.", min_value=0.0)
        qtd = c3.number_input("Qtd", min_value=1)
        margem = st.slider("Margem %", 0, 100, 30)
        
        invest, venda = custo * qtd, custo * (1 + margem/100)
        lucro = (venda - custo) * qtd

        if st.button("Gravar"):
            df_d = carregar_dados("dados")
            nova_linha = pd.DataFrame([{"produto": prod, "custo": custo, "quantidade": qtd, "margem": margem, "investimento": invest, "lucro": lucro, "usuario": st.session_state.username}])
            if salvar_dados(pd.concat([df_d, nova_linha], ignore_index=True), "dados"):
                st.success("Gravado!")
                st.rerun()

    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Investimento", f"R$ {invest:,.2f}")
    m2.metric("Venda Unit.", f"R$ {venda:,.2f}")
    m3.metric("Lucro", f"R$ {lucro:,.2f}")

    fig = px.pie(values=[max(0.1, invest), max(0.1, lucro)], names=["Custo", "Lucro"], hole=0.4)
    st.plotly_chart(fig)

    df_g = carregar_dados("dados")
    if not df_g.empty:
        st.dataframe(df_g[df_g['usuario'] == st.session_state.username], use_container_width=True)
