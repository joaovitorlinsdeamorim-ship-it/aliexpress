import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px # Para os gráficos

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Controle de Importação", layout="wide")

# --- CONEXÃO COM BANCO DE DADOS (Google Sheets) ---
conn = st.connection("gsheets", type=GSheetsConnection)
URL_PLANILHA = "COLE_AQUI_A_URL_DA_SUA_PLANILHA"

# --- LÓGICA DE LOGIN (Simplificada para o exemplo) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Acesso ao Sistema")
    user = st.text_input("Usuário")
    pw = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if user == "admin" and pw == "1234": # Ajuste sua lógica aqui
            st.session_state['logged_in'] = True
            st.session_state['username'] = user
            st.rerun()
        else:
            st.error("Dados incorretos")
else:
    # --- INTERFACE DO DASHBOARD ---
    st.sidebar.write(f"Logado como: **{st.session_state.username}**")
    if st.sidebar.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("📦 Controle de Importações & Prospecção")

    # --- FORMULÁRIO DE ENTRADA (Igual à sua imagem) ---
    with st.expander("Novo Registro", expanded=True):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            nome_prod = st.text_input("Nome do Produto", placeholder="Ex: Smartwatch X8")
        with col2:
            custo_uni = st.number_input("Custo Unitário (R$)", min_value=0.0, step=0.01)
        with col3:
            qtd = st.number_input("Quantidade", min_value=1, step=1)
        
        margem = st.slider("Margem de Lucro (%)", 0, 100, 25)
        
        # Cálculos Automáticos
        investimento = custo_uni * qtd
        preco_venda = custo_uni * (1 + margem/100)
        lucro_estimado = (preco_venda - custo_uni) * qtd

        if st.button("Registrar Entrada", use_container_width=True):
            # Lógica para salvar no Google Sheets
            nova_data = pd.DataFrame([{
                "produto": nome_prod,
                "custo": custo_uni,
                "quantidade": qtd,
                "margem": margem,
                "investimento": investimento,
                "lucro": lucro_estimado,
                "usuario": st.session_state.username
            }])
            # conn.update(spreadsheet=URL_PLANILHA, data=nova_data) # Ative após configurar a API
            st.success(f"Produto {nome_prod} registrado!")

    st.divider()

    # --- DASHBOARD (VALORES E DASH) ---
    st.subheader("📊 Resumo Financeiro")
    m1, m2, m3 = st.columns(3)
    m1.metric("Investimento Total", f"R$ {investimento:,.2f}")
    m2.metric("Preço de Venda Sugerido", f"R$ {preco_venda:,.2f}")
    m3.metric("Lucro Estimado", f"R$ {lucro_estimado:,.2f}", delta=f"{margem}%")

    # --- GRÁFICO (O "DASH" que faltava) ---
    # Simulando dados para o gráfico
    chart_data = pd.DataFrame({
        "Categorias": ["Custo", "Lucro"],
        "Valores": [investimento, lucro_estimado]
    })
    fig = px.pie(chart_data, values='Valores', names='Categorias', hole=0.4,
                 color_discrete_sequence=['#EF553B', '#00CC96'])
    st.plotly_chart(fig, use_container_width=True)
