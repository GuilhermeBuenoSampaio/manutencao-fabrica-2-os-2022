"""GO01: materializa indicadores Gold a partir de uma Silver AB04 aprovada.

Arquivo: datalake/03_gold/<source-run>/kpis_mes_tipo_setor.parquet.
Não sobrescreve execução existente e preserva valores decimais em centavos.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("projeto", nargs="?", type=Path, default=Path("."))
    parser.add_argument("--source-run", required=True)
    args = parser.parse_args()
    root = args.projeto.resolve()
    run = args.source_run
    if not run or any(c not in "0123456789_" for c in run):
        parser.error("--source-run inválido")
    docs = root / "docs" / "execucoes" / "GO01" / run
    docs.mkdir(parents=True, exist_ok=True)
    output = docs / "conclusao_GO01.json"
    target = root / "datalake" / "03_gold" / run / "kpis_mes_tipo_setor.parquet"
    result = {"etapa": "GO01", "run_id": run, "source_run": run,
              "status": "REPROVADO", "parquet": target.relative_to(root).as_posix(),
              "erro": None}
    try:
        silver = root / "datalake" / "02_silver" / run / "os_2022_silver.parquet"
        ab04 = json.loads((root / "docs" / "execucoes" / "AB04" / run /
                           "conclusao_AB04.json").read_text(encoding="utf-8"))
        if ab04.get("status") != "APROVADO" or sha256(silver) != ab04.get("sha256_parquet"):
            raise ValueError("Silver não corresponde ao AB04 aprovado")
        rows = pq.read_table(silver, columns=["formulario_os", "ano", "mes_numero", "mes",
                                              "tipo", "setor", "valor_total_brl"]).to_pylist()
        if len(rows) != ab04.get("linhas") or len({r["formulario_os"] for r in rows}) != len(rows):
            raise ValueError("Linhas ou chaves da Silver divergentes")
        groups = defaultdict(lambda: [0, Decimal("0.00")])
        for r in rows:
            key = (r["ano"], r["mes_numero"], r["mes"], r["tipo"], r["setor"])
            groups[key][0] += 1
            groups[key][1] += r["valor_total_brl"]
        items = [{"ano": k[0], "mes_numero": k[1], "mes": k[2], "tipo": k[3],
                  "setor": k[4], "os_registradas": v[0], "valor_registrado_brl": v[1]}
                 for k, v in sorted(groups.items())]
        if sum(x["os_registradas"] for x in items) != ab04["linhas"] or sum(
                (x["valor_registrado_brl"] for x in items), Decimal("0.00")) != Decimal(
                ab04["custo_total_brl"]):
            raise ValueError("Agregação Gold diverge da Silver")
        if target.exists():
            prior = json.loads(output.read_text(encoding="utf-8")) if output.is_file() else {}
            if prior.get("status") != "APROVADO" or prior.get("sha256_parquet") != sha256(target):
                raise ValueError("Gold existente sem evidência válida; revisão manual necessária")
            current = pq.read_table(target).to_pylist()
            if current != items:
                raise ValueError("Gold existente diverge dos dados atuais")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            schema = pa.schema([("ano", pa.int64()), ("mes_numero", pa.int64()),
                                ("mes", pa.string()), ("tipo", pa.string()),
                                ("setor", pa.string()), ("os_registradas", pa.int64()),
                                ("valor_registrado_brl", pa.decimal128(18, 2))])
            pq.write_table(pa.Table.from_pylist(items, schema=schema), target)
            if pq.read_table(target).to_pylist() != items:
                raise ValueError("Leitura da Gold gravada diverge da agregação")
        result.update(status="APROVADO", sha256_parquet=sha256(target),
                      grupos=len(items), os_registradas=len(rows),
                      valor_registrado_brl=str(sum((r["valor_total_brl"] for r in rows),
                                                     Decimal("0.00"))))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result["erro"] = f"{type(exc).__name__}: {exc}"
    result["data_hora"] = datetime.now().astimezone().isoformat()
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (docs / "conclusao_GO01.md").write_text(
        f"# GO01 — Gold de O.S.\n\nStatus: **{result['status']}**.\n\n"
        f"Fonte: `{run}`; Gold: `{result['parquet']}`.\n\n"
        f"O.S.: {result.get('os_registradas', '—')}; valor (R$): "
        f"{result.get('valor_registrado_brl', '—')}.\n\nErro: {result['erro'] or 'nenhum'}.\n",
        encoding="utf-8")
    print(f"[GO01] {result['status']}; evidência: {docs}", flush=True)
    return 0 if result["status"] == "APROVADO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
