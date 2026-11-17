# Trabalho Prático de Engenharia de Dados — Parte 1: CRUD Relacional

Programa em Python, com menu de terminal, que faz o CRUD (inserir, ler, atualizar e remover) nas tabelas **usuario**, **professor**, **turma** e **leciona** do esquema relacional `universidade`, em um banco PostgreSQL hospedado no AWS RDS.

- **Disciplina:** Engenharia de Dados
- **Professor:** André Britto de Carvalho
- **Integrantes:**  JOAO VICTOR POLVORA MAYNART CUNHA, FRANCIELY REBECA VERAS DOS SANTOS, RYAN JEFERSON OLIVEIRA MENEZES

## Como funciona

O programa se conecta ao banco e mostra um menu em duas etapas: primeiro a tabela, depois a operação.

| Operação | O que faz |
|---|---|
| Inserir | Pede os campos da tabela e grava um novo registro |
| Listar todos | Mostra todos os registros da tabela |
| Buscar por chave | Mostra o registro com a chave primária informada |
| Atualizar | Altera campos de um registro (Enter mantém o valor atual, `NULL` apaga o valor) |
| Remover | Apaga um registro, após confirmação |

Detalhes de implementação:

- As cinco operações são genéricas: as particularidades de cada tabela (colunas, chave primária, colunas de array) ficam descritas no dicionário `TABELAS`.
- Os valores são enviados ao banco como parâmetros (`%s`), e nomes de tabela e coluna passam por `psycopg2.sql.Identifier`, o que evita SQL injection.
- Cada operação roda em uma transação: *commit* em caso de sucesso e *rollback* em caso de erro. Erros do banco (chave estrangeira, chave duplicada, tipo inválido) são mostrados na tela sem encerrar o programa.
- Os comandos usam `RETURNING *` para mostrar o registro inserido, alterado ou removido.

## Requisitos

- Python 3.8 ou superior
- Driver do PostgreSQL:

```bash
pip install psycopg2-binary
```

## Execução

```bash
python crud_universidade.py
```


## Observações sobre o esquema

- **Ordem de inserção:** para cadastrar um professor, o `usuario` (CPF) precisa existir antes. Para `leciona`, a turma e o professor precisam existir. Para `turma`, a disciplina e o par `ano`/`semestre` precisam existir (no dump há os semestres 2017/2 e 2019/1).
- **Remoção em cascata:** remover um professor apaga as linhas dele em `leciona`; remover uma turma apaga as linhas dela em `leciona` e `cursa`; remover um usuário deixa o `cpf` do professor ou estudante vinculado como `NULL`.
- **Valores de enum:** `formacao` aceita `Graduação`, `Especialização`, `Mestrado` ou `Doutorado`; `tipo_jornada_trabalho` aceita `20h`, `40h` ou `DE`.
- **Campos de array:** `email` e `telefone` são digitados separados por vírgula (ex.: `a@x.com, b@x.com`).
- **Sequence da turma:** o dump insere turmas com `id_turma` explícito (1 a 27) sem avançar a sequence; por isso o programa a alinha ao maior id antes de cada inserção.

