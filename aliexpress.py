import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Sistema de Importação", layout="wide")

if "connections" in st.secrets and "gsheets" in st.secrets.connections:
    st.secrets.connections.gsheets["private_key"] = st.secrets.connections.gsheets["private_key"].replace("\\n", "\n")

conn = st.connection("gsheets", type=GSheetsConnection)
URL_PLANILHA = "SUA_URL_DA_PLANILHA_AQUI"

def carregar_dados(aba):
    try:
        return conn.read(spreadsheet=URL_PLANILHA, worksheet=aba)
    except:
        return pd.DataFrame()

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
                senha_correta = str(df_usuarios[df_usuarios['usuario'] == user]['senha'].values[0])
                if pw == senha_correta:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = user
                    st.rerun()
            st.error("Usuário ou senha inválidos.")

    else:
        st.title("📝 Cadastro")
        novo_nome = st.text_input("Nome Completo")
        novo_user = st.text_input("Usuário (Login)")
        nova_pw = st.text_input("Senha", type="password")
        if st.button("Finalizar Cadastro"):
            df_usuarios = carregar_dados("usuarios")
            novo_registro = pd.DataFrame([{"nome": novo_nome, "usuario": novo_user, "senha": nova_pw}])
            df_final = pd.concat([df_usuarios, novo_registro], ignore_index=True)
            conn.update(spreadsheet=URL_PLANILHA, worksheet="usuarios", data=df_final)
            st.success("Cadastro realizado!")

else:
    st.sidebar.write(f"Usuário: **{st.session_state.username}**")
    if st.sidebar.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("🚢 Controle de Importações")

    with st.expander("➕ Registrar Novo Item", expanded=True):
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
            df_at = pd.concat([df_d, nova_l], ignore_index=True)
            conn.update(spreadsheet=URL_PLANILHA, worksheet="dados", data=df_at)
            st.success("Salvo!")
            st.rerun()

    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Investimento", f"R$ {invest:,.2f}")
    m2.metric("Venda Unit.", f"R$ {venda_u:,.2f}")
    m3.metric("Lucro Est.", f"R$ {lucro_e:,.2f}")

    c_data = pd.DataFrame({"Cat": ["Custo", "Lucro"], "Val": [invest, lucro_e]})
    fig = px.pie(c_data, values='Val', names='Cat', hole=0.4, color_discrete_sequence=['#EF553B', '#00CC96'])
    st.plotly_chart(fig)

    st.subheader("📋 Meus Itens")
    df_g = carregar_dados("dados")
    if not df_g.empty:
        st.dataframe(df_g[df_g['usuario'] == st.session_state.username], use_container_width=True)
