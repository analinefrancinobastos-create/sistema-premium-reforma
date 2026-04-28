import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

st.set_page_config(
    page_title="Sistema Premium de Reforma",
    page_icon="🏠",
    layout="wide"
)
# LOGIN SIMPLES
USUARIO_CORRETO = "admin"
SENHA_CORRETA = "djY/4Vh3@-67"

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login do Sistema")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if usuario == USUARIO_CORRETO and senha == SENHA_CORRETA:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

    st.stop()

# conexão banco
conexao = sqlite3.connect("controle_reforma.db")
cursor = conexao.cursor()

# tabela principal
cursor.execute("""
CREATE TABLE IF NOT EXISTS gastos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    descricao TEXT,
    categoria TEXT,
    valor REAL,
    forma_pagamento TEXT,
    status TEXT,
    observacao TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS pedreiros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    servico TEXT,
    valor_combinado REAL,
    valor_pago REAL,
    data_pagamento TEXT,
    observacao TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS comprovantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    descricao TEXT,
    categoria TEXT,
    arquivo TEXT,
    observacao TEXT
)
""")
conexao.commit()

st.title("🏠 Sistema Premium de Controle de Reforma")
st.subheader("Dashboard Financeiro da Obra")

menu = st.sidebar.radio(
    "Menu",
    [
    "Dashboard",
    "Cadastrar gasto",
    "Controle do pedreiro",
    "Comprovantes",
    "Resumo geral",
    "Todos os gastos"
]
)
if st.sidebar.button("🚪 Sair do sistema"):
    st.session_state.logado = False
    st.rerun()

categorias = [
    "Material de construção",
    "Mão de obra pedreiro",
    "Mão de obra ajudante",
    "Elétrica",
    "Hidráulica",
    "Pintura",
    "Piso/Revestimento",
    "Frete",
    "Ferramentas",
    "Outros"
]

formas_pagamento = [
    "Pix",
    "Dinheiro",
    "Cartão de crédito",
    "Cartão de débito",
    "Transferência",
    "Boleto"
]

status_pagamento = [
    "Pago",
    "Pendente"
]

if menu == "Cadastrar gasto":
    st.header("➕ Novo gasto")

    data_gasto = st.date_input("Data", value=date.today())
    descricao = st.text_input("Descrição")
    categoria = st.selectbox("Categoria", categorias)
    valor = st.number_input("Valor R$", min_value=0.0, step=10.0)
    forma_pagamento = st.selectbox("Forma de pagamento", formas_pagamento)
    status = st.selectbox("Status", status_pagamento)
    observacao = st.text_area("Observação")

    if st.button("Salvar gasto"):
        cursor.execute("""
        INSERT INTO gastos
        (data, descricao, categoria, valor, forma_pagamento, status, observacao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(data_gasto),
            descricao,
            categoria,
            valor,
            forma_pagamento,
            status,
            observacao
        ))

        conexao.commit()
        st.success("Gasto salvo com sucesso!")

elif menu == "Dashboard":
    st.header("📊 Dashboard Financeiro")

    df = pd.read_sql_query("SELECT * FROM gastos", conexao)

    if df.empty:
        st.info("Nenhum gasto cadastrado ainda.")
    else:
        total_gasto = df["valor"].sum()
        total_pago = df[df["status"] == "Pago"]["valor"].sum()
        total_pendente = df[df["status"] == "Pendente"]["valor"].sum()

        col1, col2, col3 = st.columns(3)

        col1.metric("Total da obra", f"R$ {total_gasto:,.2f}")
        col2.metric("Total pago", f"R$ {total_pago:,.2f}")
        col3.metric("Total pendente", f"R$ {total_pendente:,.2f}")

        resumo = df.groupby("categoria")["valor"].sum().reset_index()

        st.subheader("Gastos por categoria")
        st.dataframe(resumo, use_container_width=True)
        st.bar_chart(resumo.set_index("categoria"))
elif menu == "Controle do pedreiro":
    st.header("👷 Controle do Pedreiro por Parcelas")

    nome = st.text_input("Nome do pedreiro")
    servico = st.text_input("Serviço contratado")
    valor_combinado = st.number_input("Valor combinado R$", min_value=0.0, step=100.0)
    valor_pago = st.number_input("Valor pago nesta parcela R$", min_value=0.0, step=100.0)
    data_pagamento = st.date_input("Data do pagamento", value=date.today())
    observacao = st.text_area("Observação do pagamento")

    if st.button("💾 Salvar pagamento do pedreiro"):
        cursor.execute("""
        INSERT INTO pedreiros
        (nome, servico, valor_combinado, valor_pago, data_pagamento, observacao)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            nome,
            servico,
            valor_combinado,
            valor_pago,
            str(data_pagamento),
            observacao
        ))

        conexao.commit()
        st.success("Pagamento do pedreiro salvo com sucesso!")

    st.subheader("📋 Histórico do pedreiro")

    df_pedreiro = pd.read_sql_query("SELECT * FROM pedreiros", conexao)

    if df_pedreiro.empty:
        st.info("Nenhum pagamento cadastrado ainda.")
    else:
        total_combinado = df_pedreiro["valor_combinado"].max()
        total_pago = df_pedreiro["valor_pago"].sum()
        saldo = total_combinado - total_pago

        col1, col2, col3 = st.columns(3)
        col1.metric("Valor combinado", f"R$ {total_combinado:,.2f}")
        col2.metric("Total pago", f"R$ {total_pago:,.2f}")
        col3.metric("Saldo restante", f"R$ {saldo:,.2f}")

        st.dataframe(df_pedreiro, use_container_width=True)


elif menu == "Comprovantes":
    st.header("📎 Upload de Comprovantes e Notas Fiscais")

    data_comp = st.date_input("Data do comprovante", value=date.today())
    descricao_comp = st.text_input("Descrição do comprovante")
    categoria_comp = st.selectbox("Categoria do comprovante", categorias)
    arquivo = st.file_uploader(
        "Anexar comprovante, nota fiscal ou recibo",
        type=["pdf", "png", "jpg", "jpeg"]
    )
    observacao_comp = st.text_area("Observação do comprovante")

    if st.button("💾 Salvar comprovante"):
        if arquivo is None:
            st.warning("Anexe um arquivo antes de salvar.")
        else:
            import os

            pasta = "comprovantes"
            os.makedirs(pasta, exist_ok=True)

            caminho_arquivo = os.path.join(pasta, arquivo.name)

            with open(caminho_arquivo, "wb") as f:
                f.write(arquivo.getbuffer())

            cursor.execute("""
            INSERT INTO comprovantes
            (data, descricao, categoria, arquivo, observacao)
            VALUES (?, ?, ?, ?, ?)
            """, (
                str(data_comp),
                descricao_comp,
                categoria_comp,
                caminho_arquivo,
                observacao_comp
            ))

            conexao.commit()
            st.success("Comprovante salvo com sucesso!")

    st.subheader("📁 Comprovantes salvos")

    df_comprovantes = pd.read_sql_query("SELECT * FROM comprovantes ORDER BY data DESC", conexao)

    if df_comprovantes.empty:
        st.info("Nenhum comprovante cadastrado ainda.")
    else:
        st.dataframe(df_comprovantes, use_container_width=True)        
elif menu == "Controle do pedreiro":
    st.header("👷 Controle do Pedreiro por Parcelas")

    nome = st.text_input("Nome do pedreiro")
    servico = st.text_input("Serviço contratado")
    valor_combinado = st.number_input("Valor combinado R$", min_value=0.0, step=100.0)
    valor_pago = st.number_input("Valor pago nesta parcela R$", min_value=0.0, step=100.0)
    data_pagamento = st.date_input("Data do pagamento", value=date.today())
    observacao = st.text_area("Observação do pagamento")

    if st.button("💾 Salvar pagamento do pedreiro"):
        cursor.execute("""
        INSERT INTO pedreiros
        (nome, servico, valor_combinado, valor_pago, data_pagamento, observacao)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            nome,
            servico,
            valor_combinado,
            valor_pago,
            str(data_pagamento),
            observacao
        ))

        conexao.commit()
        st.success("Pagamento do pedreiro salvo com sucesso!")

    st.subheader("📋 Histórico do pedreiro")

    df_pedreiro = pd.read_sql_query("SELECT * FROM pedreiros", conexao)

    if df_pedreiro.empty:
        st.info("Nenhum pagamento cadastrado ainda.")
    else:
        total_combinado = df_pedreiro["valor_combinado"].max()
        total_pago = df_pedreiro["valor_pago"].sum()
        saldo = total_combinado - total_pago

        col1, col2, col3 = st.columns(3)
        col1.metric("Valor combinado", f"R$ {total_combinado:,.2f}")
        col2.metric("Total pago", f"R$ {total_pago:,.2f}")
        col3.metric("Saldo restante", f"R$ {saldo:,.2f}")

        st.dataframe(df_pedreiro, use_container_width=True)


elif menu == "Comprovantes":
    st.header("📎 Upload de Comprovantes e Notas Fiscais")

    data_comp = st.date_input("Data do comprovante", value=date.today())
    descricao_comp = st.text_input("Descrição do comprovante")
    categoria_comp = st.selectbox("Categoria do comprovante", categorias)
    arquivo = st.file_uploader(
        "Anexar comprovante, nota fiscal ou recibo",
        type=["pdf", "png", "jpg", "jpeg"]
    )
    observacao_comp = st.text_area("Observação do comprovante")

    if st.button("💾 Salvar comprovante"):
        if arquivo is None:
            st.warning("Anexe um arquivo antes de salvar.")
        else:
            import os

            pasta = "comprovantes"
            os.makedirs(pasta, exist_ok=True)

            caminho_arquivo = os.path.join(pasta, arquivo.name)

            with open(caminho_arquivo, "wb") as f:
                f.write(arquivo.getbuffer())

            cursor.execute("""
            INSERT INTO comprovantes
            (data, descricao, categoria, arquivo, observacao)
            VALUES (?, ?, ?, ?, ?)
            """, (
                str(data_comp),
                descricao_comp,
                categoria_comp,
                caminho_arquivo,
                observacao_comp
            ))

            conexao.commit()
            st.success("Comprovante salvo com sucesso!")

    st.subheader("📁 Comprovantes salvos")

    df_comprovantes = pd.read_sql_query("SELECT * FROM comprovantes ORDER BY data DESC", conexao)

    if df_comprovantes.empty:
        st.info("Nenhum comprovante cadastrado ainda.")
    else:
        st.dataframe(df_comprovantes, use_container_width=True)
elif menu == "Resumo geral":
    st.header("📋 Resumo Geral")

    df = pd.read_sql_query("SELECT * FROM gastos", conexao)

    if df.empty:
        st.info("Nenhum gasto cadastrado.")
    else:
        st.dataframe(df, use_container_width=True)

elif menu == "Todos os gastos":
    st.header("📄 Todos os gastos cadastrados")

    df = pd.read_sql_query("SELECT * FROM gastos ORDER BY data DESC", conexao)

    if df.empty:
        st.info("Nenhum gasto encontrado.")
    else:
        st.dataframe(df, use_container_width=True)

conexao.close()