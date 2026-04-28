import sqlite3

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

def cadastrar_gasto():
    data_gasto = input("Data do gasto: ")
    descricao = input("Descrição: ")
    categoria = input("Categoria: ")

    valor_texto = input("Valor: R$ ")
    valor = float(valor_texto.replace(",", "."))

    forma_pagamento = input("Forma de pagamento: ")
    observacao = input("Observação: ")

    cursor.execute("""
    INSERT INTO gastos
    (data, descricao, categoria, valor, forma_pagamento, observacao)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (data_gasto, descricao, categoria, valor, forma_pagamento, observacao))

    conexao.commit()
    print("Gasto cadastrado com sucesso!")

def resumo_por_categoria():
    cursor.execute("""
    SELECT categoria, SUM(valor)
    FROM gastos
    GROUP BY categoria
    """)

    print("\nResumo por categoria:")
    resultados = cursor.fetchall()

    if not resultados:
        print("Nenhum gasto cadastrado ainda.")
    else:
        for categoria, total in resultados:
            print(f"{categoria}: R$ {total:.2f}")

while True:
    print("\n--- Controle da Reforma ---")
    print("1 - Cadastrar gasto")
    print("2 - Resumo por categoria")
    print("0 - Sair")

    opcao = input("Escolha uma opção: ")

    if opcao == "1":
        cadastrar_gasto()
    elif opcao == "2":
        resumo_por_categoria()
    elif opcao == "0":
        print("Sistema finalizado.")
        break
    else:
        print("Opção inválida.")

conexao.close()
