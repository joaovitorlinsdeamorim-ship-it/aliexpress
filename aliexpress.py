import streamlit as st
import pandas as pd
import plotly.express as px
from gspread_pandas import Spread
import re

st.set_page_config(page_title="Sistema de Importação", layout="wide")

# --- FUNÇÃO DE LIMPEZA DE CHAVE (O PULO DO GATO) ---
def limpar_chave(pk_suja):
    # Extrai apenas o miolo entre os cabeçalhos
    if "-----BEGIN PRIVATE KEY-----" in pk_suja:
        # Remove cabeçalhos e rodapés para limpar o conteúdo
        miolo = pk_suja.replace("-----BEGIN PRIVATE KEY-----", "")
        miolo = miolo.replace("-----END PRIVATE KEY-----", "")
        # Remove quebras de linha, espaços e barras invertidas (\n literal)
        miolo = re.sub(r"[\s\\n]", "", miolo)
        
        # Corrige o preenchimento (padding) do Base64 se necessário
        missing_padding = len(miolo) % 4
        if missing_padding:
            miolo += "=" * (4 - missing_padding)
            
        # Remonta no formato oficial
        return f"-----BEGIN PRIVATE KEY-----\n{miolo}\n-----END PRIVATE KEY-----\n"
    return pk_suja

def carregar_dados(aba_nome):
    try:
        creds = st.secrets["connections"]["gsheets"].to_dict()
        creds["private_key"] = limpar_chave(creds["private_key"])
        s = Spread(st.secrets["spreadsheet_url"], config=creds, sheet=aba_nome)
        return s.df
    except Exception as e:
        # Não exibe erro se a planilha estiver apenas vazia
        return pd.DataFrame()

def salvar_dados(df_novo, aba_nome):
    try:
        creds = st.secrets["connections"]["gsheets"].to_dict()
        creds["private_key"] = limpar_chave(creds["private_key"])
        s = Spread(st.secrets["spreadsheet_url"], config=creds, sheet=aba_nome)
        s.df = df_novo
        # Salva sem o índice e substitui o conteúdo
        s.save_to_sheet(index=False, replace=True)
        return True
    except Exception as e:
        st.error(f"Erro técnico ao salvar: {e}")
        return False

# --- LÓGICA DE ESTADO E LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.sidebar.title("Navegação")
    opcao = st.sidebar.radio("Selecione:", ["Login", "Cadastro"])

    if opcao == "Login":
        st.title("🔐 Login do Sistema")
        user = st.text_input("Usuário")
        pw = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            df_usuarios = carregar_dados("usuarios")
            if not df_usuarios.empty and user in df_usuarios['usuario'].astype(str).values:
                senha_correta = str(df_usuarios[df_usuarios['usuario'] == user]['senha'].values[0])
                if pw == senha_correta:
                    st.session_state.update({"logged_in": True, "username": user})
                    st.rerun()
            st.error("Usuário ou senha inválidos.")

    else:
        st.title("📝 Cadastro de Usuário")
        n = st.text_input("Nome")
        u = st.text_input("Novo Usuário")
        p = st.text_input("Nova Senha", type="password")
        if st.button("Finalizar Cadastro"):
            df_u = carregar_dados("usuarios")
            novo = pd.DataFrame([{"nome": n, "usuario": u, "senha": p}])
            if salvar_dados(pd.concat([df_u, novo], ignore_index=True), "usuarios"):
                st.success("Cadastrado com sucesso! Mude para a tela de Login.")

else:
    # --- ÁREA LOGADA ---
    st.sidebar.write(f"Usuário atual: **{st.session_state.username}**")
    if st.sidebar.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("🚢 Painel de Importações")

    with st.expander("➕ Adicionar Novo Produto", expanded=True):
        c1, c2, c3 = st.columns([3, 1, 1])
        nome_p = c1.text_input("Nome do Produto")
        custo_u = c2.number_input("Custo Unitário (R$)", min_value=0.0, step=0.1)
        quant = c3.number_input("Quantidade", min_value=1, step=1)
        margem = st.slider("Margem de Lucro (%)", 0, 100, 30)
        
        invest = custo_u * quant
        venda_u = custo_u * (1 + margem/100)
        lucro_e = (venda_u - custo_u) * quant

        if st.button("Gravar na Planilha"):
            df_d = carregar_dados("dados")
            nova_l = pd.DataFrame([{
                "produto": nome_p, "custo": custo_u, "quantidade": quant,
                "margem": margem, "investimento": invest, "lucro": lucro_e,
                "usuario": st.session_state.username
            }])
            if salvar_dados(pd.concat([df_d, nova_l], ignore_index=True), "dados"):
                st.success("Dados gravados com sucesso!")
                st.rerun()

    # Dashboard Financeiro
    st.divider()
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Investimento Total", f"R$ {invest:,.2f}")
    col_m2.metric("Venda Unitária", f"R$ {venda_u:,.2f}")
    col_m3.metric("Lucro Estimado", f"R$ {lucro_e:,.2f}")

    # Gráfico de Pizza
    fig = px.pie(
        values=[max(0.1, invest), max(0.1, lucro_e)], 
        names=["Custo Total", "Lucro Esperado"], 
        hole=0.4,
        color_discrete_sequence=['#EF553B', '#00CC96']
    )
    st.plotly_chart(fig)

    # Tabela de Dados
    st.subheader("📋 Meus Itens Registrados")
    df_g = carregar_dados("dados")
    if not df_g.empty:
        # Filtra para mostrar apenas o que o usuário logado cadastrou
        filtro = df_g[df_g['usuario'] == st.session_state.username]
        st.dataframe(filtro, use_container_width=True)
    else:
        st.info("Nenhum dado encontrado para este usuário.")
