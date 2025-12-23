import streamlit as st
import pandas as pd
import plotly.express as px
from gspread_pandas import Spread
import json
import base64
import re

# 1. Configuração da Página
st.set_page_config(page_title="Painel Perigo Imports", layout="wide")

# --- FUNÇÕES DE CONEXÃO ---

def conectar_google_sheets(aba_nome):
    try:
        raw_b64 = st.secrets["gcp_base64"]
        clean_b64 = re.sub(r'[^a-zA-Z0-9+/=]', '', raw_b64)
        decoded_bytes = base64.b64decode(clean_b64)
        json_str = decoded_bytes.decode('utf-8')
        creds_dict = json.loads(json_str)
        url = st.secrets["spreadsheet_url"]
        return Spread(url, config=creds_dict, sheet=aba_nome)
    except Exception as e:
        st.error(f"Erro crítico de conexão: {e}")
        return None

def carregar_dados(aba_nome):
    s = conectar_google_sheets(aba_nome)
    if s:
        try:
            return s.sheet_to_df(index=None)
        except Exception:
            if aba_nome == "usuarios":
                return pd.DataFrame(columns=["nome", "usuario", "senha"])
            return pd.DataFrame()
    return pd.DataFrame()

def salvar_dados(df_novo, aba_nome):
    s = conectar_google_sheets(aba_nome)
    if s:
        try:
            s.df_to_sheet(df=df_novo, index=False, replace=True)
            return True
        except Exception as e:
            st.error(f"Erro ao salvar na planilha: {e}")
            return False
    return False

# --- LÓGICA DE ACESSO ---

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
                usuario_row = df_u[df_u['usuario'] == u]
                senha_db = str(usuario_row['senha'].values[0])
                if p == senha_db:
                    st.session_state.update({"logged_in": True, "username": u})
                    st.rerun()
            st.error("Usuário ou senha incorretos.")
    else:
        st.title("📝 Cadastro")
        nome = st.text_input("Nome Completo")
        user = st.text_input("Nome de Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Finalizar Cadastro"):
            df_u = carregar_dados("usuarios")
            novo_u = pd.concat([df_u, pd.DataFrame([{"nome": nome, "usuario": user, "senha": senha}])], ignore_index=True)
            if salvar_dados(novo_u, "usuarios"):
                st.success("Cadastrado com sucesso! Faça o login.")

else:
    # --- ÁREA LOGADA ---
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logged_in": False}))
    st.title(f"🚢 Controle de Importações: {st.session_state.username}")

    # ADICIONADA A ABA DE RESUMO GERAL
    tab1, tab2, tab3 = st.tabs(["📊 Resumo Geral", "➕ Adicionar Novo", "🗑️ Gerir Inventário"])

    # Carregar dados uma vez para todas as abas
    df_global = carregar_dados("dados")
    meus_dados = pd.DataFrame()
    if not df_global.empty:
        meus_dados = df_global[df_global['usuario'] == st.session_state.username].copy()
        if not meus_dados.empty:
            meus_dados["investimento"] = pd.to_numeric(meus_dados["investimento"])
            meus_dados["lucro"] = pd.to_numeric(meus_dados["lucro"])
            if "faturamento" not in meus_dados.columns:
                meus_dados["faturamento"] = meus_dados["investimento"] + meus_dados["lucro"]
            else:
                meus_dados["faturamento"] = pd.to_numeric(meus_dados["faturamento"])

    with tab1:
        st.subheader("💰 Performance Financeira Acumulada")
        if not meus_dados.empty:
            total_investido = meus_dados["investimento"].sum()
            total_retorno = meus_dados["faturamento"].sum()
            total_lucro = meus_dados["lucro"].sum()
            roi = (total_lucro / total_investido * 100) if total_investido > 0 else 0

            # Exibição em Cards
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Investido", f"R$ {total_investido:,.2f}")
            m2.metric("Retorno Esperado", f"R$ {total_retorno:,.2f}", delta=f"R$ {total_lucro:,.2f}")
            m3.metric("Lucro Líquido", f"R$ {total_lucro:,.2f}")
            m4.metric("ROI Geral", f"{roi:.1f}%")

            st.divider()
            
            # Gráfico de Crescimento (Azul Escuro vs Azul Claro)
            df_plot = meus_dados.melt(
                id_vars=["produto"], 
                value_vars=["investimento", "faturamento"],
                var_name="Tipo", 
                value_name="Valor_RS"
            )

            fig = px.bar(
                df_plot, 
                x="produto", 
                y="Valor_RS", 
                color="Tipo", 
                barmode="group",
                title="Investimento vs. Faturamento por Produto",
                labels={"Valor_RS": "Valor (R$)", "produto": "Produto"},
                color_discrete_map={"investimento": "#1A237E", "faturamento": "#4FC3F7"}
            )
            fig.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=",.2f")
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📋 Detalhes do Inventário")
            st.dataframe(meus_dados, use_container_width=True)
        else:
            st.info("Nenhum dado cadastrado para gerar o resumo.")

    with tab2:
        with st.form("form_adicionar"):
            st.subheader("Cadastrar Nova Compra")
            c1, c2, c3 = st.columns(3)
            p_nome = c1.text_input("Produto")
            p_custo = c2.number_input("Custo Unitário (R$)", min_value=0.0, format="%.2f")
            p_qtd = c3.number_input("Quantidade", min_value=1)
            p_venda = st.number_input("Preço de Venda Unitário (R$)", min_value=0.0, format="%.2f")
            
            submit = st.form_submit_button("Gravar na Planilha")
            
            if submit:
                invest_total = p_custo * p_qtd
                faturamento_total = p_venda * p_qtd
                lucro_total = faturamento_total - invest_total
                margem = (lucro_total / faturamento_total * 100) if faturamento_total > 0 else 0
                
                nova_linha = pd.DataFrame([{
                    "produto": p_nome, 
                    "custo": p_custo, 
                    "quantidade": p_qtd, 
                    "venda": p_venda, 
                    "margem": f"{margem:.2f}%", 
                    "investimento": float(invest_total), 
                    "faturamento": float(faturamento_total),
                    "lucro": float(lucro_total), 
                    "usuario": st.session_state.username
                }])
                if salvar_dados(pd.concat([df_global, nova_linha], ignore_index=True), "dados"):
                    st.success("Dados Gravados!")
                    st.rerun()

    with tab3:
        st.subheader("Remover Itens")
        if not meus_dados.empty:
            item_para_deletar = st.selectbox("Escolha o item para apagar:", meus_itens_lista := meus_dados['produto'].unique())
            if st.button("❌ Confirmar Exclusão", type="primary"):
                df_final = df_global.drop(df_global[(df_global['usuario'] == st.session_state.username) & (df_global['produto'] == item_para_deletar)].index)
                if salvar_dados(df_final, "dados"):
                    st.warning(f"Item '{item_para_deletar}' removido!")
                    st.rerun()
        else:
            st.info("Nada para apagar.")
