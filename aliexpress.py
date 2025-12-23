import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Sistema de Importação", layout="wide")

# --- FUNÇÃO DE CONEXÃO ROBUSTA ---
def conectar():
    # Pegamos os dados do segredo e transformamos em um dicionário comum
    creds = st.secrets["connections"]["gsheets"].to_dict()
    # Limpeza profunda da chave privada
    if "private_key" in creds:
        # Remove caracteres de escape de texto e garante quebras de linha reais
        cleaned_key = creds["private_key"].replace("\\n", "\n").strip()
        creds["private_key"] = cleaned_key
    
    # Injetamos as credenciais limpas diretamente na conexão
    return st.connection("gsheets", type=GSheetsConnection, **creds)

# Inicializa a conexão corrigida
conn = conectar()

# --- COLOQUE SUA URL ABAIXO ---
URL_PLANILHA = "SUA_URL_DA_PLANILHA_AQUI"

def carregar_dados(aba):
    try:
        return conn.read(spreadsheet=URL_PLANILHA, worksheet=aba, ttl=0)
    except:
        return pd.DataFrame()

# --- LÓGICA DE LOGIN / SISTEMA ---
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
            if not df_usuarios.empty and user in df_usuarios['usuario'].values:
                linha = df_usuarios[df_usuarios['usuario'] == user]
                if pw == str(linha['senha'].values[0]):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = user
                    st.rerun()
            st.error("Dados incorretos.")
    else:
        st.title("📝 Cadastro")
        n_nome = st.text_input("Nome")
        n_user = st.text_input("Usuário")
        n_pw = st.text_input("Senha", type="password")
        if st.button("Cadastrar"):
            df_u = carregar_dados("usuarios")
            novo = pd.DataFrame([{"nome": n_nome, "usuario": n_user, "senha": n_pw}])
            df_f = pd.concat([df_u, novo], ignore_index=True)
            conn.update(spreadsheet=URL_PLANILHA, worksheet="usuarios", data=df_f)
            st.success("Sucesso! Vá para Login.")
else:
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logged_in": False}))
    st.title(f"🚢 Painel de {st.session_state.username}")

    # Formulário
    with st.expander("Novo Registro"):
        c1, c2, c3 = st.columns(3)
        prod = c1.text_input("Produto")
        custo = c2.number_input("Custo Unit.", min_value=0.0)
        qtd = c3.number_input("Qtd", min_value=1)
        margem = st.slider("Margem %", 0, 100, 25)
        
        invest = custo * qtd
        venda = custo * (1 + margem/100)
        lucro = (venda - custo) * qtd

        if st.button("Salvar"):
            df_d = carregar_dados("dados")
            nova_l = pd.DataFrame([{"produto": prod, "custo": custo, "quantidade": qtd, "margem": margem, "investimento": invest, "lucro": lucro, "usuario": st.session_state.username}])
            conn.update(spreadsheet=URL_PLANILHA, worksheet="dados", data=pd.concat([df_d, nova_l], ignore_index=True))
            st.rerun()

    # Dashboard
    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Investimento", f"R$ {invest:,.2f}")
    m2.metric("Venda Unit.", f"R$ {venda:,.2f}")
    m3.metric("Lucro", f"R$ {lucro:,.2f}")

    fig = px.pie(values=[max(0.1, invest), max(0.1, lucro)], names=["Custo", "Lucro"], hole=0.4)
    st.plotly_chart(fig)

    st.subheader("📋 Meus Itens")
    df_g = carregar_dados("dados")
    if not df_g.empty:
        st.dataframe(df_g[df_g['usuario'] == st.session_state.username], use_container_width=True)
