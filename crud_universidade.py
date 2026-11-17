#!/usr/bin/env python3
"""
Dependência: pip install psycopg2-binary
"""
import psycopg2
from psycopg2 import sql

CONFIG_BANCO = {
    "host": "db-postgres-atividade.ckfrhv9d0omo.us-east-1.rds.amazonaws.com",
    "port": 5432,
    "dbname": "postgres",
    "user": "app_crud",
    "password": "atividade123",
}

SCHEMA = "universidade"
MANTER = object()  

# colunas, chave primária e particularidades de cada tabela
TABELAS = {
    "usuario": {
        "colunas": ["cpf", "nome", "data_nascimento", "email", "telefone", "login", "senha"],
        "pk": ["cpf"],
        "arrays": ["email", "telefone"],  
    },
    "professor": {
        "colunas": ["mat_professor", "cpf", "departamento", "formacao",
                    "data_admissao", "tipo_jornada_trabalho", "salario"],
        "pk": ["mat_professor"],
    },
    "turma": {
        "colunas": ["id_turma", "cod_disc", "numero", "ano", "semestre"],
        "pk": ["id_turma"],
        "auto": ["id_turma"],
        "antes_insert": ("SELECT setval('universidade.seq_turma', "
                         "(SELECT COALESCE(MAX(id_turma), 0) + 1 FROM universidade.turma), false)"),
    },
    "leciona": {
        "colunas": ["id_turma", "mat_professor"],
        "pk": ["id_turma", "mat_professor"],
        "editaveis": ["id_turma", "mat_professor"],  
    },
}


def tabela_id(tabela):
    return sql.Identifier(SCHEMA, tabela)


def ler_valor(tabela, coluna, ao_vazio):
    """Enter devolve `ao_vazio`; 'NULL' devolve None; arrays viram lista."""
    dica = " [Enter = manter]" if ao_vazio is MANTER else ""
    texto = input(f"  {coluna}{dica}: ").strip()
    if texto == "":
        return ao_vazio
    if texto.upper() == "NULL":
        return None
    if coluna in TABELAS[tabela].get("arrays", []):
        return [item.strip() for item in texto.split(",") if item.strip()]
    return texto


def ler_chave(tabela):
    return [input(f"  {c}: ").strip() for c in TABELAS[tabela]["pk"]]


def where_pk(tabela):
    return sql.SQL(" AND ").join(
        sql.SQL("{} = %s").format(sql.Identifier(c)) for c in TABELAS[tabela]["pk"]
    )


def executar(conn, consulta, params=None, antes=None):
    """Roda numa transação (commit ou rollback). Devolve (colunas, linhas) ou None se der erro."""
    try:
        with conn, conn.cursor() as cur:
            if antes:
                cur.execute(antes)
            cur.execute(consulta, params)
            return [d[0] for d in cur.description], cur.fetchall()
    except psycopg2.Error as e:
        print(f"\n  Erro do banco: {e.diag.message_primary or e}")
        if e.diag.message_detail:
            print(f"  Detalhe: {e.diag.message_detail}")


def mostrar(resultado):
    if resultado is None:
        return
    colunas, linhas = resultado
    if not linhas:
        print("  (nenhum registro)")
        return
    print("\n  " + " | ".join(colunas))
    for linha in linhas:
        print("  " + " | ".join("NULL" if v is None else str(v) for v in linha))
    print(f"  ({len(linhas)} registro(s))")


# ------------------------------------------------------------------ operações
def inserir(conn, tabela):
    cfg = TABELAS[tabela]
    colunas = [c for c in cfg["colunas"] if c not in cfg.get("auto", [])]
    valores = [ler_valor(tabela, c, None) for c in colunas]
    consulta = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING *").format(
        tabela_id(tabela),
        sql.SQL(", ").join(sql.Identifier(c) for c in colunas),
        sql.SQL(", ").join([sql.Placeholder()] * len(colunas)),
    )
    mostrar(executar(conn, consulta, valores, cfg.get("antes_insert")))


def listar(conn, tabela):
    ordem = sql.SQL(", ").join(sql.Identifier(c) for c in TABELAS[tabela]["pk"])
    mostrar(executar(conn, sql.SQL("SELECT * FROM {} ORDER BY {}").format(tabela_id(tabela), ordem)))


def buscar(conn, tabela):
    chave = ler_chave(tabela)
    consulta = sql.SQL("SELECT * FROM {} WHERE {}").format(tabela_id(tabela), where_pk(tabela))
    mostrar(executar(conn, consulta, chave))


def atualizar(conn, tabela):
    cfg = TABELAS[tabela]
    print("Chave do registro a atualizar:")
    chave = ler_chave(tabela)
    editaveis = cfg.get("editaveis") or [c for c in cfg["colunas"] if c not in cfg["pk"]]
    print("Novos valores (Enter mantém, NULL apaga o valor):")
    novos = {c: ler_valor(tabela, c, MANTER) for c in editaveis}
    novos = {c: v for c, v in novos.items() if v is not MANTER}
    if not novos:
        print("  Nada a atualizar.")
        return
    consulta = sql.SQL("UPDATE {} SET {} WHERE {} RETURNING *").format(
        tabela_id(tabela),
        sql.SQL(", ").join(sql.SQL("{} = %s").format(sql.Identifier(c)) for c in novos),
        where_pk(tabela),
    )
    mostrar(executar(conn, consulta, list(novos.values()) + chave))


def remover(conn, tabela):
    print("Chave do registro a remover:")
    chave = ler_chave(tabela)
    if input("  Confirmar remoção? (s/N): ").strip().lower() != "s":
        print("  Cancelado.")
        return
    consulta = sql.SQL("DELETE FROM {} WHERE {} RETURNING *").format(tabela_id(tabela), where_pk(tabela))
    mostrar(executar(conn, consulta, chave))


# ------------------------------------------------------------------ menus
OPERACOES = {
    "Inserir": inserir,
    "Listar todos": listar,
    "Buscar por chave": buscar,
    "Atualizar": atualizar,
    "Remover": remover,
}


def escolher(titulo, opcoes):
    """Menu numerado: devolve a opção escolhida, ou None se digitar 0."""
    while True:
        print(f"\n=== {titulo} ===")
        for i, opcao in enumerate(opcoes, 1):
            print(f"  {i} - {opcao}")
        print("  0 - Voltar")
        escolha = input("Opção: ").strip()
        if escolha == "0":
            return None
        if escolha.isdigit() and 1 <= int(escolha) <= len(opcoes):
            return opcoes[int(escolha) - 1]
        print("  Opção inválida.")


def main():
    try:
        conn = psycopg2.connect(**CONFIG_BANCO, connect_timeout=10)
    except psycopg2.OperationalError as e:
        print(f"Não foi possível conectar ao banco:\n{e}")
        print("Confira CONFIG_BANCO, o acesso público do RDS e o Security Group (porta 5432).")
        return
    try:
        while True:
            tabela = escolher("TABELA", list(TABELAS))
            if tabela is None:
                break
            while True:
                operacao = escolher(f"{tabela.upper()} - OPERAÇÃO", list(OPERACOES))
                if operacao is None:
                    break
                OPERACOES[operacao](conn, tabela)
    except (KeyboardInterrupt, EOFError):
        print()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
