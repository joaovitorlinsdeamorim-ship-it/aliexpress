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

    tab1, tab2 = st.tabs(["➕ Adicionar Novo", "🗑️ Gerir Inventário"])

    with tab1:
        with st.form("form_adicionar"):
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
                
                df_d = carregar_dados("dados")
                nova_linha = pd.DataFrame([{
                    "produto": p_nome, 
                    "custo": p_custo, 
                    "quantidade": p_qtd, 
                    "venda": p_venda, 
                    "margem": f"{margem:.2f}%", 
                    "investimento": float(invest_total), 
                    "faturamento": float(faturamento_total), # Salvamos o total bruto
                    "lucro": float(lucro_total), 
                    "usuario": st.session_state.username
                }])
                if salvar_dados(pd.concat([df_d, nova_linha], ignore_index=True), "dados"):
                    st.success("Dados Gravados!")
                    st.rerun()

    with tab2:
        st.subheader("Remover Itens")
        df_g = carregar_dados("dados")
        if not df_g.empty:
            meus_itens = df_g[df_g['usuario'] == st.session_state.username]
            if not meus_itens.empty:
                item_para_deletar = st.selectbox("Escolha o item para apagar:", meus_itens['produto'].unique())
                if st.button("❌ Confirmar Exclusão", type="primary"):
                    df_final = df_g.drop(df_g[(df_g['usuario'] == st.session_state.username) & (df_g['produto'] == item_para_deletar)].index)
                    if salvar_dados(df_final, "dados"):
                        st.warning(f"Item '{item_para_deletar}' removido!")
                        st.rerun()

    st.divider()
    
    # --- EXIBIÇÃO E GRÁFICO DE CRESCIMENTO (INVESTIMENTO VS FATURAMENTO) ---
    df_visualizar = carregar_dados("dados")
    if not df_visualizar.empty:
        meus_dados = df_visualizar[df_visualizar['usuario'] == st.session_state.username]
        
        if not meus_dados.empty:
            # Garantir que são números para o gráfico não bugar
            meus_dados["investimento"] = pd.to_numeric(meus_dados["investimento"])
            # Se a coluna faturamento não existir em registros antigos, calculamos na hora:
            if "faturamento" not in meus_dados.columns:
                meus_dados["faturamento"] = meus_dados["investimento"] + pd.to_numeric(meus_dados["lucro"])
            else:
                meus_dados["faturamento"] = pd.to_numeric(meus_dados["faturamento"])

            st.subheader("📋 Teus Lançamentos")
            st.dataframe(meus_dados, use_container_width=True)

            # Criando o gráfico LADO A LADO (Vertical)
            # Comparamos o que saiu do bolso (Investimento) com o que entrou total (Faturamento)
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
                barmode="group", # Barras verticais lado a lado
                title="Crescimento Financeiro: Investimento vs. Retorno Bruto (R$)",
                labels={"Valor_RS": "Valor em Reais (R$)", "produto": "Produto"},
                color_discrete_map={"investimento": "#EF553B", "faturamento": "#00CC96"} # Vermelho vs Verde
            )
            
            fig.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=",.2f")
            st.plotly_chart(fig, use_container_width=True)
            
            st.info("💡 A barra **Vermelha** mostra o seu custo (investimento). A barra **Verde** mostra o valor total da venda (Custo + Lucro). A diferença de altura entre elas é o seu lucro real.")
        else:
            st.info("Ainda não tens dados registados.")
