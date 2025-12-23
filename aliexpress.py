import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Sistema de Importação", layout="wide")

# Conexão com o Banco de Dados
conn = st.connection("gsheets", type=GSheetsConnection)
URL_PLANILHA = "SUA_URL_DA_PLANILHA_AQUI" # <--- COLOQUE SUA URL AQUI

# --- FUNÇÕES AUXILIARES ---
def carregar_dados(aba):
    try:
        return conn.read(spreadsheet=URL_PLANILHA, worksheet=aba)
    except:
        return pd.DataFrame()

# --- SISTEMA DE LOGIN E CADASTRO ---
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
        st.title("📝 Cadastro de Novo Usuário")
        novo_nome = st.text_input("Nome Completo")
        novo_user = st.text_input("Nome de Usuário (Login)")
        nova_pw = st.text_input("Senha", type="password")
        if st.button("Finalizar Cadastro"):
            df_usuarios = carregar_dados("usuarios")
            novo_registro = pd.DataFrame([{"nome": novo_nome, "usuario": novo_user, "senha": nova_pw}])
            df_final = pd.concat([df_usuarios, novo_registro], ignore_index=True)
            conn.update(spreadsheet=URL_PLANILHA, worksheet="usuarios", data=df_final)
            st.success("Cadastro realizado! Mude para 'Login' na barra lateral.")

# --- ÁREA DO SISTEMA (APÓS LOGIN) ---
else:
    st.sidebar.write(f"Bem-vindo, **{st.session_state.username}**")
    if st.sidebar.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("🚢 Controle de Importações")

    # --- FORMULÁRIO DE ENTRADA ---
    with st.expander("➕ Registrar Novo Item", expanded=True):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            nome_prod = st.text_input("Nome do Produto")
        with col2:
            custo_uni = st.number_input("Custo Unitário (R$)", min_value=0.0, step=0.01)
        with col3:
            qtd = st.number_input("Quantidade", min_value=1, step=1)
        
        margem = st.slider("Margem de Lucro (%)", 0, 100, 25)
        
        investimento = custo_uni * qtd
        preco_venda = custo_uni * (1 + margem/100)
        lucro_estimado = (preco_venda - custo_uni) * qtd

        if st.button("Registrar Entrada"):
            df_vendas = carregar_dados("dados")
            nova_venda = pd.DataFrame([{
                "produto": nome_prod, "custo": custo_uni, "quantidade": qtd,
                "margem": margem, "investimento": investimento, "lucro": lucro_estimado,
                "usuario": st.session_state.username
            }])
            df_vendas_atualizado = pd.concat([df_vendas, nova_venda], ignore_index=True)
            conn.update(spreadsheet=URL_PLANILHA, worksheet="dados", data=df_vendas_atualizado)
            st.success("Registrado na planilha!")
            st.rerun()

    # --- DASHBOARD ---
    st.divider()
    st.subheader("📊 Resumo Financeiro")
    m1, m2, m3 = st.columns(3)
    m1.metric("Investimento Total", f"R$ {investimento:,.2f}")
    m2.metric("Preço de Venda Unitário", f"R$ {preco_venda:,.2f}")
    m3.metric("Lucro Estimado", f"R$ {lucro_estimado:,.2f}")

    # Gráfico
    chart_data = pd.DataFrame({"Cat": ["Custo", "Lucro"], "Val": [investimento, lucro_estimado]})
    fig = px.pie(chart_data, values='Val', names='Cat', hole=0.4, color_discrete_sequence=['#EF553B', '#00CC96'])
    st.plotly_chart(fig)

    # --- LISTAGEM DE ITENS (O que estava faltando) ---
    st.divider()
    st.subheader("📋 Meus Itens Adicionados")
    df_geral = carregar_dados("dados")
    if not df_geral.empty:
        # Filtra para mostrar apenas o que o usuário logado cadastrou
        meus_dados = df_geral[df_geral['usuario'] == st.session_state.username]
        st.dataframe(meus_dados, use_container_width=True)
    else:
        st.info("Nenhum item cadastrado ainda.")
