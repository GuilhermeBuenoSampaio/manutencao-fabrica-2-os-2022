r"""Reconciliação independente e somente leitura entre Silver AB04 e SQL Server.

Da raiz do projeto:
  python -u .\sql\03_reconciliar_silver_sql_server.py --server ".\SQLEXPRESS"
Gera docs/execucoes/SQL01/<run_id>/conclusao_SQL01.json e .md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pyarrow.parquet as pq
import pyodbc

DATABASE = "manutencao-fabrica-2-os-2022"
SOURCE_RUN = "20260928_135101_841223"
COLUMNS = (
    "formulario_os", "ano", "mes_numero", "mes", "setor", "prestador_solicitado",
    "tipo", "numero_controle", "descricao_defeito", "area_equipamento", "local",
    "descricao_servico_realizado", "pecas_equipamentos_necessarios", "qtd",
    "valor_unitario_brl", "valor_total_brl",
)
QUERY = """
SELECT f.formulario_os, t.ano, t.mes_numero, t.mes_nome, s.setor_nome,
       p.prestador_nome_original, y.tipo_nome, f.numero_controle,
       f.descricao_defeito, a.rotulo_original, f.local_original,
       f.descricao_servico_realizado, f.pecas_equipamentos_necessarios,
       f.qtd, f.valor_unitario_brl, f.valor_total_brl
FROM dw.fato_os AS f
JOIN dw.dim_tempo AS t ON t.mes_chave = f.mes_chave
JOIN dw.dim_setor AS s ON s.setor_chave = f.setor_chave
JOIN dw.dim_prestador_solicitado AS p ON p.prestador_chave = f.prestador_chave
JOIN dw.dim_tipo AS y ON y.tipo_chave = f.tipo_chave
JOIN dw.dim_area_equipamento AS a ON a.area_equipamento_chave = f.area_equipamento_chave
"""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize(row: dict) -> dict:
    return {k: (str(v) if isinstance(v, Decimal) else v) for k, v in row.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("projeto", nargs="?", type=Path, default=Path("."))
    parser.add_argument("--server", required=True)
    parser.add_argument("--driver")
    parser.add_argument("--source-run", default=SOURCE_RUN)
    args = parser.parse_args()
    root = args.projeto.resolve()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    docs = root / "docs" / "execucoes" / "SQL01" / run_id
    docs.mkdir(parents=True, exist_ok=False)
    result = {"etapa": "SQL01", "run_id": run_id, "source_run": args.source_run,
              "status": "REPROVADO", "server": args.server, "database": DATABASE,
              "divergencias": [], "erro": None}
    try:
        parquet = root / "datalake" / "02_silver" / args.source_run / "os_2022_silver.parquet"
        evidence = root / "docs" / "execucoes" / "AB04" / args.source_run / "conclusao_AB04.json"
        ab04 = json.loads(evidence.read_text(encoding="utf-8"))
        if ab04.get("status") != "APROVADO" or ab04.get("sha256_parquet") != sha256(parquet):
            raise ValueError("Parquet ou evidência AB04 inválida")
        local = pq.read_table(parquet)
        if tuple(local.column_names) != COLUMNS:
            raise ValueError("Esquema Parquet diferente do esperado")
        local_rows = local.to_pylist()
        local_map = {r["formulario_os"]: r for r in local_rows}
        if len(local_map) != len(local_rows):
            raise ValueError("Chave formulario_os duplicada no Parquet")
        driver = args.driver or next((d for d in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server") if d in pyodbc.drivers()), None)
        if driver not in pyodbc.drivers():
            raise ValueError(f"Driver SQL Server indisponível: {driver}; disponíveis: {pyodbc.drivers()}")
        with pyodbc.connect(
            f"DRIVER={{{driver}}};SERVER={args.server};DATABASE={DATABASE};"
            "Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;",
            timeout=15, autocommit=True,
        ) as conn:
            sql_rows = [dict(zip(COLUMNS, row)) for row in conn.cursor().execute(QUERY).fetchall()]
            fact_count = conn.cursor().execute("SELECT COUNT(*) FROM dw.fato_os").fetchval()
        sql_map = {r["formulario_os"]: r for r in sql_rows}
        result["linhas_silver"] = len(local_rows)
        result["linhas_fato"] = fact_count
        result["linhas_join"] = len(sql_rows)
        result["os_distintas_sql"] = len(sql_map)
        result["soma_silver_brl"] = str(sum((r["valor_total_brl"] for r in local_rows), Decimal(0)))
        result["soma_sql_brl"] = str(sum((r["valor_total_brl"] for r in sql_rows), Decimal(0)))
        result["setores_silver"] = dict(Counter(r["setor"] for r in local_rows))
        result["setores_sql"] = dict(Counter(r["setor"] for r in sql_rows))
        result["tipos_silver"] = dict(Counter(r["tipo"] for r in local_rows))
        result["tipos_sql"] = dict(Counter(r["tipo"] for r in sql_rows))
        result["meses_silver"] = dict(Counter(r["mes"] for r in local_rows))
        result["meses_sql"] = dict(Counter(r["mes"] for r in sql_rows))
        diffs = result["divergencias"]
        if fact_count != len(sql_rows) or len(sql_rows) != len(sql_map):
            diffs.append("Contagem da fato, join ou chaves distintas diferente")
        for name in ("soma", "setores", "tipos", "meses"):
            left = name + ("_silver_brl" if name == "soma" else "_silver")
            right = name + ("_sql_brl" if name == "soma" else "_sql")
            if result[left] != result[right]:
                diffs.append(f"Agregado divergente: {name}")
        for key in sorted(local_map.keys() | sql_map.keys()):
            if key not in local_map or key not in sql_map:
                diffs.append(f"O.S. ausente em um dos lados: {key}")
                continue
            for column in COLUMNS:
                if local_map[key][column] != sql_map[key][column]:
                    diffs.append(f"{key}: {column}: Silver={local_map[key][column]!s}, SQL={sql_map[key][column]!s}")
        result["status"] = "APROVADO" if not diffs and len(local_rows) == ab04["linhas"] else "REPROVADO"
    except Exception as exc:
        result["erro"] = f"{type(exc).__name__}: {exc}"
    result["data_hora"] = datetime.now().astimezone().isoformat()
    (docs / "conclusao_SQL01.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (docs / "conclusao_SQL01.md").write_text(
        f"# SQL01 — Reconciliação Silver × SQL Server\n\n"
        f"Status: **{result['status']}**. Execução Silver: `{args.source_run}`.\n\n"
        f"O.S. Silver/fato/join: {result.get('linhas_silver', '—')}/"
        f"{result.get('linhas_fato', '—')}/{result.get('linhas_join', '—')}.\n\n"
        f"Soma Silver/SQL (R$): {result.get('soma_silver_brl', '—')}/"
        f"{result.get('soma_sql_brl', '—')}.\n\n"
        f"Divergências: {len(result['divergencias'])}; erro: {result['erro'] or 'nenhum'}. "
        "Detalhes no JSON.\n", encoding="utf-8",
    )
    print(f"[SQL01] {result['status']}: {len(result['divergencias'])} divergências; docs: {docs}", flush=True)
    if result["erro"]:
        print(f"[SQL01] {result['erro']}", flush=True)
    return 0 if result["status"] == "APROVADO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
