import streamlit as st
import pandas as pd
import plotly.express as px
from llm_classifier import integrate_category_in_df
from datetime import datetime
import os

st.set_page_config(layout='wide')

st.title("Dashboard de Finanças Pessoais")

# Seção de Upload de Arquivo
st.header("📁 Upload do Extrato")

uploaded_file = st.file_uploader(
    "Faça upload do seu arquivo de extrato (.xls ou .xlsx)", 
    type=['xls', 'xlsx'],
    help="Selecione o arquivo Excel do seu extrato bancário"
)

if uploaded_file is not None:
    # Cria a pasta extratos se não existir
    os.makedirs("extratos", exist_ok=True)
    
    # Salva o arquivo na pasta extratos
    file_path = os.path.join("extratos", "planilhaExtrato.xls")
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success("✅ Arquivo carregado com sucesso!")
    
    # Botão para processar o arquivo
    if st.button("🚀 Processar Extrato", type="primary", key="process_new"):
        with st.spinner("Processando extrato com IA..."):
            integrate_category_in_df(path_extrato=file_path)
            st.success("Extrato processado com sucesso!")
            st.rerun()

# Divisor visual
st.divider()

# Botão para reprocessar (só aparece se já existe um arquivo)
if os.path.exists("extratos/planilhaExtrato.xls"):
    if st.button("🔄 Reprocessar Categorias com IA", type="secondary"):
        with st.spinner("Reprocessando transações com IA..."):
            integrate_category_in_df(path_extrato=r'extratos\planilhaExtrato.xls')
            st.success("Categorias reprocessadas com sucesso!")
            st.rerun()

# Carrega e processa os dados
try:
    df = pd.read_csv("finances.csv")
except FileNotFoundError:
    if os.path.exists("extratos/planilhaExtrato.xls"):
        st.info("Processando extrato pela primeira vez...")
        with st.spinner("Processando..."):
            integrate_category_in_df(path_extrato=r'extratos\planilhaExtrato.xls')
            df = pd.read_csv("finances.csv")
            st.success("Processamento concluído!")
    else:
        st.warning("⚠️ Faça upload do seu arquivo de extrato acima para começar.")
        st.stop()

# Processamento dos dados
df['Data'] = df['Data'].astype(str).str.strip()
df = df[df['Data'] != ''] 
df = df[df['Data'] != 'nan'] 
df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
df = df.dropna(subset=['Data'])
df['Mês'] = df['Data'].dt.strftime('%m/%Y')
df['Data'] = df['Data'].dt.date

df = df[df['Categoria'] != "Receitas"]

def filter_data(df, mes, selected_categories):
    df_filtered = df[df['Mês'] == mes]
    if selected_categories:
        df_filtered = df_filtered[df_filtered['Categoria'].isin(selected_categories)]
    return df_filtered

# Sidebar com filtros
st.sidebar.header("🔍 Filtros")
mes = st.sidebar.selectbox("Mês", df['Mês'].unique())

categories = df['Categoria'].unique().tolist()
selected_categories = st.sidebar.multiselect("Filtrar por Categorias", categories, default=categories)

df_filtered = filter_data(df, mes, selected_categories)

# Layout principal
st.header("📊 Análise Financeira")

c1, c2 = st.columns([0.6, 0.4])

with c1:
    st.subheader("Transações")
    st.dataframe(df_filtered, use_container_width=True)

# Resumo financeiro
entradas = df_filtered[df_filtered['Valor'] > 0]['Valor'].sum()
saidas = df_filtered[df_filtered['Valor'] < 0]['Valor'].sum()

resumo_financeiro = pd.DataFrame({
    'Tipo': ['💰 Entradas', '💸 Saídas', '📈 Saldo'],
    'Valor': [f"R$ {entradas:,.2f}", f"R$ {saidas:,.2f}", f"R$ {entradas + saidas:,.2f}"]
})

st.subheader("💼 Resumo Financeiro")
st.dataframe(resumo_financeiro, use_container_width=True)

# Distribuição por categoria
category_distribution = df_filtered.groupby("Categoria")['Valor'].sum().reset_index()
category_distribution['Valor_Abs'] = category_distribution['Valor'].abs()

st.subheader("📈 Gastos por Categoria")
st.dataframe(category_distribution[['Categoria', 'Valor']], use_container_width=True)

with c2:
    fig = px.pie(category_distribution, 
                 values='Valor_Abs',
                 names='Categoria',
                 title='Distribuição de Gastos', 
                 hole=0.3)
    st.plotly_chart(fig, use_container_width=True)