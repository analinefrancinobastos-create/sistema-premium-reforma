import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import os

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
CREATE TABLE IF NOT EXISTS comprovantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    descricao TEXT,
    categoria TEXT,
    arquivo TEXT,
    observacao TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS contratos_pedreiro (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    servico TEXT,
    valor_contratado REAL,
    observacao TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS pagamentos_pedreiro (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contrato_id INTEGER,
    valor_pago REAL,
    data_pagamento TEXT,
    forma_pagamento TEXT,
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

    parcelado = "Não"
    quantidade_parcelas = 1
    valor_parcela = valor

    if forma_pagamento == "Cartão de crédito":
        parcelado = st.selectbox("Compra parcelada?", ["Não", "Sim"])

        if parcelado == "Sim":
            quantidade_parcelas = st.number_input(
                "Quantidade de parcelas",
                min_value=1,
                max_value=36,
                step=1
            )

            valor_parcela = valor / quantidade_parcelas if quantidade_parcelas > 0 else 0
            st.info(f"Valor de cada parcela: R$ {valor_parcela:,.2f}")
            st.subheader("📅 Meses das parcelas")

            meses = []
            for i in range(int(quantidade_parcelas)):
                mes_parcela = pd.to_datetime(data_gasto) + pd.DateOffset(months=i)
                meses.append({
                    "Parcela": f"{i + 1}/{int(quantidade_parcelas)}",
                    "Mês": mes_parcela.strftime("%m/%Y"),
                    "Valor": valor_parcela
                })

            st.dataframe(pd.DataFrame(meses), use_container_width=True)

    observacao = st.text_area("Observação")

    if st.button("Salvar gasto"):
        if descricao == "" or valor <= 0:
            st.warning("Preencha a descrição e o valor do gasto.")
        else:
            cursor.execute("""
            INSERT INTO gastos
            (data, descricao, categoria, valor, forma_pagamento, status, observacao)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(data_gasto),
                f"{descricao} | Parcelado: {parcelado} | Parcelas: {quantidade_parcelas}x | Valor parcela: R$ {valor_parcela:.2f}",
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
    df_contratos = pd.read_sql_query("SELECT * FROM contratos_pedreiro", conexao)
    df_pagamentos = pd.read_sql_query("SELECT * FROM pagamentos_pedreiro", conexao)

    if df.empty:
        st.info("Nenhum gasto cadastrado ainda.")
    else:
        df["data"] = pd.to_datetime(df["data"])

        total_gasto = df["valor"].sum()
        total_pendente = df[df["status"] == "Pendente"]["valor"].sum()

        parcelas = df[df["descricao"].str.contains("Parcelado: Sim", na=False)].copy()
        lista_parcelas = []

        if not parcelas.empty:
            parcelas["valor_parcela"] = parcelas["descricao"].str.extract(
                r"Valor parcela: R\$ ([0-9.]+)"
            )[0].astype(float)

            parcelas["qtd_parcelas"] = parcelas["descricao"].str.extract(
                r"Parcelas: ([0-9]+)x"
            )[0].astype(int)

            for _, row in parcelas.iterrows():
                for i in range(int(row["qtd_parcelas"])):
                    mes_parcela = row["data"] + pd.DateOffset(months=i)
                    lista_parcelas.append({
                        "Descrição": row["descricao"].split("|")[0],
                        "Categoria": row["categoria"],
                        "Parcela": f"{i + 1}/{int(row['qtd_parcelas'])}",
                        "Mês": mes_parcela.strftime("%m/%Y"),
                        "Valor": row["valor_parcela"]
                    })

        df_parcelas = pd.DataFrame(lista_parcelas)

        gastos_avista = df[
            ~df["descricao"].str.contains("Parcelado: Sim", na=False)
        ].copy()

        gastos_avista["Mês"] = gastos_avista["data"].dt.strftime("%m/%Y")
        gastos_avista["Valor"] = gastos_avista["valor"]
        gastos_avista["Descrição"] = gastos_avista["descricao"]
        gastos_avista["Parcela"] = "À vista"

        meses_gastos = list(gastos_avista["Mês"].unique())

        if not df_parcelas.empty:
            meses_parcelas = list(df_parcelas["Mês"].unique())
        else:
            meses_parcelas = []

        meses_disponiveis = sorted(set(meses_gastos + meses_parcelas))

        mes_selecionado = st.selectbox(
            "Selecione o mês para análise",
            meses_disponiveis
        )

        total_avista_mes = gastos_avista[
            gastos_avista["Mês"] == mes_selecionado
        ]["Valor"].sum()

        if not df_parcelas.empty:
            total_parcelas_mes = df_parcelas[
                df_parcelas["Mês"] == mes_selecionado
            ]["Valor"].sum()
        else:
            total_parcelas_mes = 0

        total_pago_mes = total_avista_mes + total_parcelas_mes

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Total da obra", f"R$ {total_gasto:,.2f}")
        col2.metric(f"✅ Pago em {mes_selecionado}", f"R$ {total_pago_mes:,.2f}")
        col3.metric("⚠️ Total pendente", f"R$ {total_pendente:,.2f}")

        st.divider()
        st.subheader("💳 Parcelas por mês")

        if df_parcelas.empty:
            st.info("Nenhuma compra parcelada cadastrada.")
        else:
            mes_parcela_selecionado = st.selectbox(
                "Ver parcelas do mês",
                sorted(df_parcelas["Mês"].unique())
            )

            df_parcelas_mes = df_parcelas[
                df_parcelas["Mês"] == mes_parcela_selecionado
            ]

            st.metric(
                f"Total de parcelas em {mes_parcela_selecionado}",
                f"R$ {df_parcelas_mes['Valor'].sum():,.2f}"
            )

            st.dataframe(df_parcelas_mes, use_container_width=True)

    st.divider()
    st.subheader("👷 Resumo do Pedreiro")

    if df_contratos.empty:
        st.info("Nenhum contrato de pedreiro cadastrado ainda.")
    else:
        if df_pagamentos.empty:
            total_pago_pedreiro = 0
        else:
            total_pago_pedreiro = df_pagamentos["valor_pago"].sum()

        valor_contratado = df_contratos["valor_contratado"].sum()
        saldo_pedreiro = valor_contratado - total_pago_pedreiro

        p1, p2, p3 = st.columns(3)
        p1.metric("Valor contratado", f"R$ {valor_contratado:,.2f}")
        p2.metric("Pago ao pedreiro", f"R$ {total_pago_pedreiro:,.2f}")
        p3.metric("Saldo restante", f"R$ {saldo_pedreiro:,.2f}")

elif menu == "Controle do pedreiro":
    st.header("👷 Controle do Pedreiro")

    aba1, aba2, aba3 = st.tabs([
        "📌 Cadastrar contrato",
        "💰 Registrar pagamento",
        "📊 Resumo"
    ])

    with aba1:
        st.subheader("Cadastrar contrato do pedreiro")

        nome = st.text_input("Nome do pedreiro")
        servico = st.text_input("Serviço contratado")
        valor_contratado = st.number_input("Valor total contratado R$", min_value=0.0, step=100.0)
        observacao_contrato = st.text_area("Observação do contrato")

        if st.button("💾 Salvar contrato"):
            if nome == "" or servico == "" or valor_contratado <= 0:
                st.warning("Preencha nome, serviço e valor contratado.")
            else:
                cursor.execute("""
                INSERT INTO contratos_pedreiro
                (nome, servico, valor_contratado, observacao)
                VALUES (?, ?, ?, ?)
                """, (
                    nome,
                    servico,
                    valor_contratado,
                    observacao_contrato
                ))

                conexao.commit()
                st.success("Contrato cadastrado com sucesso!")

    with aba2:
        st.subheader("Registrar pagamento")

        contratos = pd.read_sql_query("SELECT * FROM contratos_pedreiro", conexao)

        if contratos.empty:
            st.info("Cadastre um contrato primeiro.")
        else:
            contratos["contrato_nome"] = (
                contratos["nome"] + " - " +
                contratos["servico"] + " - R$ " +
                contratos["valor_contratado"].astype(str)
            )

            contrato_escolhido = st.selectbox(
                "Selecione o contrato",
                contratos["contrato_nome"]
            )

            contrato_id = contratos.loc[
                contratos["contrato_nome"] == contrato_escolhido,
                "id"
            ].values[0]

            valor_pago = st.number_input("Valor pago R$", min_value=0.0, step=100.0)
            data_pagamento = st.date_input("Data do pagamento", value=date.today())
            forma_pagamento = st.selectbox(
                "Forma de pagamento",
                formas_pagamento
            )
            observacao_pagamento = st.text_area("Observação do pagamento")

            if st.button("💾 Salvar pagamento"):
                if valor_pago <= 0:
                    st.warning("Informe o valor pago.")
                else:
                    cursor.execute("""
                    INSERT INTO pagamentos_pedreiro
                    (contrato_id, valor_pago, data_pagamento, forma_pagamento, observacao)
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        int(contrato_id),
                        valor_pago,
                        str(data_pagamento),
                        forma_pagamento,
                        observacao_pagamento
                    ))

                    conexao.commit()
                    st.success("Pagamento registrado com sucesso!")

    with aba3:
        st.subheader("Resumo dos contratos")

        contratos = pd.read_sql_query("SELECT * FROM contratos_pedreiro", conexao)
        pagamentos = pd.read_sql_query("SELECT * FROM pagamentos_pedreiro", conexao)

        if contratos.empty:
            st.info("Nenhum contrato cadastrado.")
        else:
            if pagamentos.empty:
                contratos["total_pago"] = 0
            else:
                total_pago = pagamentos.groupby("contrato_id")["valor_pago"].sum().reset_index()
                contratos = contratos.merge(
                    total_pago,
                    left_on="id",
                    right_on="contrato_id",
                    how="left"
                )
                contratos["valor_pago"] = contratos["valor_pago"].fillna(0)
                contratos["total_pago"] = contratos["valor_pago"]

            contratos["saldo_restante"] = contratos["valor_contratado"] - contratos["total_pago"]

            st.dataframe(
                contratos[["nome", "servico", "valor_contratado", "total_pago", "saldo_restante"]],
                use_container_width=True
            )

            st.subheader("Histórico de pagamentos")

            if pagamentos.empty:
                st.info("Nenhum pagamento registrado.")
            else:
                historico = pagamentos.merge(
                    contratos[["id", "nome", "servico"]],
                    left_on="contrato_id",
                    right_on="id",
                    how="left"
                )

                st.dataframe(
                    historico[["nome", "servico", "data_pagamento", "valor_pago", "forma_pagamento", "observacao"]],
                    use_container_width=True
                )

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
    for _, row in df_comprovantes.iterrows():
        st.markdown("---")
        st.write(f"📅 Data: {row['data']}")
        st.write(f"📝 Descrição: {row['descricao']}")
        st.write(f"📂 Categoria: {row['categoria']}")
        st.write(f"📌 Observação: {row['observacao']}")

        try:
            with open(row["arquivo"], "rb") as file:
                st.download_button(
                    label="📄 Baixar comprovante",
                    data=file,
                    file_name=row["arquivo"].split("/")[-1],
                    mime="application/octet-stream"
                )
        except:
            st.warning("Arquivo não encontrado.")

elif menu == "Todos os gastos":
    st.header("📄 Todos os gastos cadastrados")

    df = pd.read_sql_query("SELECT * FROM gastos ORDER BY data DESC", conexao)

    if df.empty:
        st.info("Nenhum gasto encontrado.")
    else:
        st.dataframe(df, use_container_width=True)

conexao.close()