r"""Carrega uma execução Silver AB04 aprovada no modelo dimensional SQL Server.

Da raiz do projeto, depois de executar 01_modelo_dimensional_os_2022.sql:
  python -m pip install pyarrow pyodbc
  python -u .\sql\02_carregar_silver_sql_server.py --server .\SQLEXPRESS

Informe --server com o nome da sua instância SQL Server. Usa autenticação Windows.
Não substitui dados existentes: a carga inteira é confirmada ou revertida.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

import pyarrow.parquet as pq
import pyodbc

DATABASE = "manutencao-fabrica-2-os-2022"
RUN_ID = "20260928_135101_841223"
FIELDS = (
    "formulario_os", "ano", "mes_numero", "mes", "setor",
    "prestador_solicitado", "tipo", "numero_controle", "descricao_defeito",
    "area_equipamento", "local", "descricao_servico_realizado",
    "pecas_equipamentos_necessarios", "qtd", "valor_unitario_brl", "valor_total_brl",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def choose_driver(explicit: str | None) -> str:
    if explicit:
        if explicit not in pyodbc.drivers():
            raise ValueError(f"Driver não instalado: {explicit}; disponíveis: {pyodbc.drivers()}")
        return explicit
    for candidate in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"):
        if candidate in pyodbc.drivers():
            return candidate
    raise ValueError(f"Instale ODBC Driver 18 ou 17 for SQL Server; disponíveis: {pyodbc.drivers()}")


def source(root: Path, run_id: str):
    parquet = root / "datalake" / "02_silver" / run_id / "os_2022_silver.parquet"
    evidence = root / "docs" / "execucoes" / "AB04" / run_id / "conclusao_AB04.json"
    if not parquet.is_file() or not evidence.is_file():
        raise FileNotFoundError(f"Exigidos: {parquet} e {evidence}")
    report = json.loads(evidence.read_text(encoding="utf-8"))
    if report.get("status") != "APROVADO" or report.get("run_id") != run_id:
        raise ValueError("AB04 não aprovada para esta execução")
    if report.get("parquet") != parquet.relative_to(root).as_posix():
        raise ValueError("Caminho do Parquet diferente da evidência AB04")
    if report.get("sha256_parquet") != sha256(parquet):
        raise ValueError("SHA-256 do Parquet diferente da evidência AB04")
    table = pq.read_table(parquet)
    if tuple(table.column_names) != FIELDS:
        raise ValueError("Esquema ou ordem de colunas inesperada no Parquet")
    rows = table.to_pylist()
    ids = [r["formulario_os"] for r in rows]
    if len(rows) != report["linhas"] or len(set(ids)) != report["os_distintas"]:
        raise ValueError("Contagem ou unicidade diverge da AB04")
    if any(any(r[k] is None for k in ("formulario_os", "ano", "mes_numero", "mes", "setor", "tipo", "prestador_solicitado", "area_equipamento", "local", "valor_total_brl")) for r in rows):
        raise ValueError("Nulo inesperado em coluna obrigatória")
    amount = sum((r["valor_total_brl"] for r in rows), Decimal("0.00"))
    if amount != Decimal(report["custo_total_brl"]):
        raise ValueError("Soma da Silver diverge da AB04")
    if Counter(r["setor"] for r in rows) != report["cardinalidade_setor"]:
        raise ValueError("Contagem por setor diverge da AB04")
    if Counter(r["mes"] for r in rows) != report["linhas_por_mes"]:
        raise ValueError("Contagem por mês diverge da AB04")
    for r in rows:
        if r["ano"] != 2022 or not 1 <= r["mes_numero"] <= 12:
            raise ValueError("Ano/mês inválido")
        if (r["qtd"] is None) != (r["valor_unitario_brl"] is None):
            raise ValueError("Quantidade e valor unitário devem ser nulos juntos")
        if r["qtd"] is not None and (r["qtd"] * r["valor_unitario_brl"]).quantize(Decimal("0.01")) != r["valor_total_brl"]:
            raise ValueError(f"Valor inconsistente: {r['formulario_os']}")
    return rows, report


def select_map(cursor, table: str, key: str, value: str):
    return {label: number for number, label in cursor.execute(
        f"SELECT {key}, {value} FROM dw.{table}"
    ).fetchall()}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("projeto", nargs="?", type=Path, default=Path("."))
    p.add_argument("--server", required=True, help=r"Ex.: .\SQLEXPRESS ou localhost")
    p.add_argument("--driver", help="Nome exato do driver ODBC instalado")
    p.add_argument("--run-id", default=RUN_ID)
    args = p.parse_args()
    root = args.projeto.resolve()
    rows, evidence = source(root, args.run_id)
    driver = choose_driver(args.driver)
    connection = pyodbc.connect(
        f"DRIVER={{{driver}}};SERVER={args.server};DATABASE={DATABASE};"
        "Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;",
        autocommit=False, timeout=15,
    )
    try:
        cur = connection.cursor()
        for name in ("dim_tempo", "dim_setor", "dim_tipo", "dim_prestador_solicitado", "dim_area_equipamento", "fato_os"):
            if not cur.execute("SELECT OBJECT_ID(?, 'U')", f"dw.{name}").fetchval():
                raise ValueError(f"Tabela não encontrada: dw.{name}; execute o SQL 01 primeiro")
        existing = cur.execute("SELECT COUNT(*) FROM dw.fato_os").fetchval()
        if existing:
            raise ValueError(f"dw.fato_os contém {existing} linhas. Carga bloqueada para evitar mistura de execuções.")
        for table in ("dim_tempo", "dim_setor", "dim_tipo", "dim_prestador_solicitado", "dim_area_equipamento"):
            if cur.execute(f"SELECT COUNT(*) FROM dw.{table}").fetchval():
                raise ValueError(f"dw.{table} já contém dados; carga bloqueada")
        times = sorted({(r["ano"] * 100 + r["mes_numero"], r["ano"], r["mes_numero"], r["mes"]) for r in rows})
        if len({t[0] for t in times}) != len(times):
            raise ValueError("Mês com nomes divergentes")
        cur.executemany("INSERT INTO dw.dim_tempo (mes_chave,ano,mes_numero,mes_nome) VALUES (?,?,?,?)", times)
        dimensions = (
            ("dim_setor", "setor_chave", "setor_nome", "setor"),
            ("dim_tipo", "tipo_chave", "tipo_nome", "tipo"),
            ("dim_prestador_solicitado", "prestador_chave", "prestador_nome_original", "prestador_solicitado"),
            ("dim_area_equipamento", "area_equipamento_chave", "rotulo_original", "area_equipamento"),
        )
        maps = []
        for table, key, column, field in dimensions:
            labels = sorted({r[field] for r in rows})
            cur.executemany(f"INSERT INTO dw.{table} ({column}) VALUES (?)", [(x,) for x in labels])
            maps.append(select_map(cur, table, key, column))
        insert = """INSERT INTO dw.fato_os (
            formulario_os,mes_chave,setor_chave,tipo_chave,prestador_chave,
            area_equipamento_chave,local_original,numero_controle,descricao_defeito,
            descricao_servico_realizado,pecas_equipamentos_necessarios,qtd,
            valor_unitario_brl,valor_total_brl) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        payload = [(
            r["formulario_os"], r["ano"] * 100 + r["mes_numero"],
            maps[0][r["setor"]], maps[1][r["tipo"]], maps[2][r["prestador_solicitado"]],
            maps[3][r["area_equipamento"]], r["local"], r["numero_controle"],
            r["descricao_defeito"], r["descricao_servico_realizado"],
            r["pecas_equipamentos_necessarios"], r["qtd"],
            r["valor_unitario_brl"], r["valor_total_brl"],
        ) for r in rows]
        cur.executemany(insert, payload)
        sql_rows = cur.execute("SELECT COUNT(*), COUNT(DISTINCT formulario_os), SUM(valor_total_brl) FROM dw.fato_os").fetchone()
        if tuple(sql_rows) != (evidence["linhas"], evidence["os_distintas"], Decimal(evidence["custo_total_brl"])):
            raise ValueError(f"Reconciliação geral falhou: {tuple(sql_rows)}")
        sql_counts = dict(cur.execute("SELECT t.mes_nome, COUNT(*) FROM dw.fato_os f JOIN dw.dim_tempo t ON t.mes_chave=f.mes_chave GROUP BY t.mes_nome").fetchall())
        if sql_counts != evidence["linhas_por_mes"]:
            raise ValueError("Reconciliação por mês falhou")
        sql_counts = dict(cur.execute("SELECT s.setor_nome, COUNT(*) FROM dw.fato_os f JOIN dw.dim_setor s ON s.setor_chave=f.setor_chave GROUP BY s.setor_nome").fetchall())
        if sql_counts != evidence["cardinalidade_setor"]:
            raise ValueError("Reconciliação por setor falhou")
        for table, key, field in (("dim_tipo", "tipo_chave", "tipo"), ("dim_prestador_solicitado", "prestador_chave", "prestador_solicitado"), ("dim_area_equipamento", "area_equipamento_chave", "area_equipamento")):
            if cur.execute(f"SELECT COUNT(*) FROM dw.fato_os f JOIN dw.{table} d ON d.{key}=f.{key}").fetchval() != len(rows):
                raise ValueError(f"Reconciliação de relacionamento falhou: {table}")
        connection.commit()
        print(f"[SQL] APROVADO: {sql_rows[0]} O.S.; R$ {sql_rows[2]}; AB04 {args.run_id}; commit confirmado.", flush=True)
    except Exception:
        connection.rollback()
        print("[SQL] REPROVADO: transação revertida, nenhuma carga parcial confirmada.", flush=True)
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
