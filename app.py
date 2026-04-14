import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta
import io

# --- CONFIGURAÇÃO VISUAL (LAYOUT ROSA) ---
st.set_page_config(page_title="Costinha Finance", page_icon="🌸", layout="wide")

def aplicar_estilo_rosa():
    st.markdown("""
        <style>
        .stApp {
            background-color: #FFF0F5;
        }
        .stButton>button {
            background-color: #FF69B4;
            color: white;
            border-radius: 20px;
            border: none;
        }
        .stButton>button:hover {
            background-color: #FF1493;
            color: white;
        }
        h1, h2, h3 {
            color: #C71585;
        }
        .css-10trblm { 
            color: #C71585;
        }
        </style>
    """, unsafe_allow_stdio=True)

aplicar_estilo_rosa()

# --- BANCO DE DADOS ---
conn = sqlite3.connect('costinha_finance.db', check_same_thread=False)
c = conn.cursor()

def inicializar_db():
    c.execute('''CREATE TABLE IF NOT EXISTS transacoes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  data TEXT, tipo TEXT, categoria TEXT, valor REAL)''')
    conn.commit()

inicializar_db()

# --- LÓGICA DE AUTENTICAÇÃO SIMPLES ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

def login():
    st.title("🌸 Bem-vinda ao Costinha Finance")
    senha = st.text_input("Digite sua senha de acesso:", type="password")
    if st.button("Entrar"):
        if senha == "1234": # Você pode alterar sua senha aqui
            st.session_state['autenticado'] = True
            st.rerun()
        else:
            st.error("Senha incorreta.")

# --- APP PRINCIPAL ---
if not st.session_state['autenticado']:
    login()
else:
    st.title("🌸 Costinha Finance")
    
    # --- SIDEBAR: CADASTRO E FILTROS ---
    st.sidebar.header("🎀 Nova Transação")
    data_input = st.sidebar.date_input("Data", date.today())
    tipo_input = st.sidebar.selectbox("Tipo", ["Receita", "Despesa"])
    categoria_input = st.sidebar.text_input("Categoria")
    valor_input = st.sidebar.number_input("Valor (R$)", min_value=0.0, format="%.2f")

    if st.sidebar.button("Salvar Registro"):
        if categoria_input and valor_input > 0:
            c.execute('INSERT INTO transacoes (data, tipo, categoria, valor) VALUES (?,?,?,?)', 
                      (data_input, tipo_input, categoria_input, valor_input))
            conn.commit()
            st.sidebar.success("Salvo com sucesso!")
        else:
            st.sidebar.warning("Preencha todos os campos.")

    st.sidebar.divider()
    st.sidebar.header("🔍 Filtros de Visualização")
    df = pd.read_sql_query('SELECT * FROM transacoes', conn)
    df['data'] = pd.to_datetime(df['data'])

    if not df.empty:
        meses = df['data'].dt.strftime('%m/%Y').unique().tolist()
        filtro_mes = st.sidebar.multiselect("Filtrar por Mês/Ano", meses, default=meses)
        
        # Aplicar Filtro
        df_filtrado = df[df['data'].dt.strftime('%m/%Y').isin(filtro_mes)]
        
        # --- PAINEL DE MÉTRICAS ---
        receitas = df_filtrado[df_filtrado['tipo'] == 'Receita']['valor'].sum()
        despesas = df_filtrado[df_filtrado['tipo'] == 'Despesa']['valor'].sum()
        saldo = receitas - despesas

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Receitas", f"R$ {receitas:,.2f}")
        col2.metric("Total Despesas", f"R$ {despesas:,.2f}")
        col3.metric("Saldo no Período", f"R$ {saldo:,.2f}")

        st.divider()

        # --- EXPORTAÇÃO (EXCEL) ---
        st.subheader("📥 Exportar Dados")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_filtrado.to_excel(writer, index=False, sheet_name='Financeiro')
        
        st.download_button(
            label="Baixar Relatório em Excel",
            data=output.getvalue(),
            file_name=f"costinha_finance_{date.today()}.xlsx",
            mime="application/vnd.ms-excel"
        )

        # --- HISTÓRICO E GRÁFICOS ---
        tab1, tab2, tab3 = st.tabs(["📋 Histórico", "📊 Gastos", "🔮 Previsão Próximo Mês"])
        
        with tab1:
            st.dataframe(df_filtrado.sort_values(by='data', ascending=False), use_container_width=True)

        with tab2:
            fig_gastos = df_filtrado[df_filtrado['tipo'] == 'Despesa'].groupby('categoria')['valor'].sum()
            st.bar_chart(fig_gastos)

        with tab3:
            # Lógica simples de previsão: média dos últimos meses
            media_gastos = df[df['tipo'] == 'Despesa']['valor'].sum() / len(df['data'].dt.month.unique()) if not df.empty else 0
            st.write(f"### Estimativa de Gastos para o próximo mês:")
            st.info(f"Com base no seu histórico, a tendência é que você gaste aproximadamente **R$ {media_gastos:,.2f}**.")
            st.caption("Nota: Esta é uma média simples baseada nos meses anteriores.")

    else:
        st.info("Bem-vinda! Comece adicionando transações na barra lateral esquerda.")

    if st.sidebar.button("Sair"):
        st.session_state['autenticado'] = False
        st.rerun()
