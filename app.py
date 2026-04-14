import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
conn = sqlite3.connect('financas.db', check_same_thread=False)
c = conn.cursor()

def criar_tabela():
    c.execute('''CREATE TABLE IF NOT EXISTS transacoes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  data TEXT, 
                  tipo TEXT, 
                  categoria TEXT, 
                  valor REAL)''')
    conn.commit()

# --- FUNÇÕES DE LÓGICA ---
def adicionar_dados(data, tipo, categoria, valor):
    c.execute('INSERT INTO transacoes (data, tipo, categoria, valor) VALUES (?,?,?,?)', 
              (data, tipo, categoria, valor))
    conn.commit()

def carregar_dados():
    return pd.read_sql_query('SELECT * FROM transacoes', conn)

# --- INTERFACE COM STREAMLIT ---
st.set_page_config(page_title="Meu Controle Financeiro", page_icon="💰")
criar_tabela()

st.title("💰 Controle de Finanças Pessoais")

# Sidebar para Cadastro
st.sidebar.header("Nova Transação")
data = st.sidebar.date_input("Data", date.today())
tipo = st.sidebar.selectbox("Tipo", ["Receita", "Despesa"])
categoria = st.sidebar.text_input("Categoria (ex: Aluguel, Salário, Lazer)")
valor = st.sidebar.number_input("Valor (R$)", min_value=0.0, format="%.2f")

if st.sidebar.button("Salvar Transação"):
    if categoria and valor > 0:
        adicionar_dados(data, tipo, categoria, valor)
        st.sidebar.success("Registrado com sucesso!")
    else:
        st.sidebar.error("Preencha todos os campos corretamente.")

# Painel Principal
df = carregar_dados()

if not df.empty:
    # Cálculos de Saldo
    receitas = df[df['tipo'] == 'Receita']['valor'].sum()
    despesas = df[df['tipo'] == 'Despesa']['valor'].sum()
    saldo = receitas - despesas

    # Exibição de Métricas
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Receitas", f"R$ {receitas:,.2f}")
    col2.metric("Total Despesas", f"R$ {despesas:,.2f}", delta_color="inverse")
    col3.metric("Saldo Atual", f"R$ {saldo:,.2f}")

    st.divider()

    # Histórico e Gráficos
    st.subheader("📊 Histórico de Transações")
    st.dataframe(df.sort_values(by='data', ascending=False), use_container_width=True)

    # Gráfico de Categorias
    st.subheader("🔍 Gastos por Categoria")
    fig_df = df[df['tipo'] == 'Despesa'].groupby('categoria')['valor'].sum()
    st.bar_chart(fig_df)

else:
    st.info("Nenhuma transação cadastrada ainda. Use a barra lateral para começar!")
