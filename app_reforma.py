import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

st.set_page_config(page_title="Controle da Reforma", page_icon="🏠", layout="wide")

conexao = sqlite3.connect("controle_reforma.db")
cursor = conexao.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS gastos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    descricao TEXT,
    categoria TEXT,
    valor REAL,
    forma_pagamento TEXT,
    observacao TEXT
)
""")
conexao.commit()

st.title("🏠 Controle da Reforma")
st.write("Sistema simples para controlar materiais, mão de obra e outros gastos.")

menu = st.sidebar.radio(
    "Menu",
    ["Cadastrar gasto", "Resumo", "Ver todos os gastos"]
)

categorias = [
    "Material de construção",
    "Mão de obra pedreiro",
    "Mão de obra ajudante",
    "Elétrica",
    "Hidráulica",
    "Pintura",
    "Piso/Revestimento",
    "Ferramentas",
    "Frete/Entrega",
    "Outros"
]

formas_pagamento = [
    "Pix",
    "Dinheiro",
    "Cartão de crédito",
    "Cartão de débito",
    "Boleto",
    "Transferência",
    "Outros"
]

if menu == "Cadastrar gasto":
    st.header("➕ Cadastrar novo gasto")

    data_gasto = st.date_input("Data do gasto", value=date.today())
    descricao = st.text_input("Descrição", placeholder="Ex: Cimento, areia, diária do pedreiro")
    categoria = st.selectbox("Categoria", categorias)
    valor = st.number_input("Valor R$", min_value=0.0, step=10.0, format="%.2f")
    forma_pagamento = st.selectbox("Forma de pagamento", formas_pagamento)
    observacao = st.text_area("Observação", placeholder="Ex: parcelado em 10x, compra para banheiro...")

    if st.button("💾 Salvar gasto", use_container_width=True):
        if descricao == "" or valor <= 0:
            st.warning("Preencha a descrição e o valor.")
        else:
            cursor.execute("""
            INSERT INTO gastos
            (data, descricao, categoria, valor, forma_pagamento, observacao)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(data_gasto),
                descricao,
                categoria,
                valor,
                forma_pagamento,
                observacao
            ))

            conexao.commit()
            st.success("Gasto cadastrado com sucesso!")

elif menu == "Resumo":
    st.header("📊 Resumo da Reforma")

    df = pd.read_sql_query("SELECT * FROM gastos", conexao)

    if df.empty:
        st.info("Nenhum gasto cadastrado ainda.")
    else:
        total = df["valor"].sum()
        st.metric("Total gasto na reforma", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        resumo = df.groupby("categoria")["valor"].sum().reset_index()
        resumo["valor"] = resumo["valor"].round(2)

        st.subheader("Total por categoria")
        st.dataframe(resumo, use_container_width=True)

        st.bar_chart(resumo.set_index("categoria"))

elif menu == "Ver todos os gastos":
    st.header("📋 Todos os gastos cadastrados")

    df = pd.read_sql_query("SELECT * FROM gastos ORDER BY data DESC", conexao)

    if df.empty:
        st.info("Nenhum gasto cadastrado ainda.")
    else:
        st.dataframe(df, use_container_width=True)

        arquivo_excel = "gastos_reforma.xlsx"
        df.to_excel(arquivo_excel, index=False)

        with open(arquivo_excel, "rb") as arquivo:
            st.download_button(
                label="📥 Baixar relatório em Excel",
                data=arquivo,
                file_name="gastos_reforma.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

conexao.close()
