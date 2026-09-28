"""Orquestra AZ01 e AZ02 para datalake/ e quality/ com evidência por execução.

Da raiz: python -u .\\src\\run_pipeline_azure.py . --account-name stcustomeranalyticsgb01
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from sincronizar_datalake_azure import digest as sha256, inventario


def anterior(base: Path, etapa: str, criterio) -> Path | None:
    for p in sorted(base.glob(f"*/conclusao_{etapa}.json"), reverse=True):
        try:
            if criterio(json.loads(p.read_text(encoding="utf-8"))):
                return p
        except (OSError, ValueError):
            continue
    return None


def executar(script: Path, raiz: Path, parametros: list[str], log: Path) -> int:
    ambiente = os.environ.copy()
    ambiente["PYTHONIOENCODING"] = "utf-8"
    with log.open("w", encoding="utf-8") as out:
        p = subprocess.Popen([sys.executable, "-u", str(script), str(raiz), *parametros],
                             cwd=raiz, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, encoding="utf-8", errors="replace", env=ambiente)
        assert p.stdout is not None
        for linha in p.stdout:
            out.write(linha)
            out.flush()
            print(linha, end="", flush=True)
        return p.wait()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("projeto", nargs="?", type=Path, default=Path("."))
    p.add_argument("--account-name", default="stcustomeranalyticsgb01")
    p.add_argument("--container", default="manutencao-fabrica-2-os-2022")
    args = p.parse_args()
    raiz = args.projeto.resolve()
    src = Path(__file__).resolve().parent
    files = inventario(raiz)
    if not files:
        p.error("Nenhum arquivo encontrado em datalake/ e quality/")
    signature = hashlib.sha256()
    for entry in files:
        signature.update(json.dumps(entry, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    for item in (src / "sincronizar_datalake_azure.py", src / "provisionar_container_azure.py"):
        signature.update(sha256(item).encode("ascii"))
    signature.update(f"{args.account_name}/{args.container}".encode("utf-8"))
    digest = signature.hexdigest()
    base = raiz / "docs" / "execucoes"
    prev = anterior(base / "pipeline_azure", "pipeline_azure",
                    lambda r: r.get("status") == "APROVADO" and r.get("sha256_entrada") == digest)
    if prev:
        print(f"[pipeline_azure] APROVADO anteriormente: {prev}; nenhum arquivo novo gerado.", flush=True)
        return 0
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    docs = base / "pipeline_azure" / run_id
    docs.mkdir(parents=True, exist_ok=False)
    az01 = anterior(base / "AZ01", "AZ01",
                    lambda r: r.get("status") == "APROVADO" and r.get("account_name") == args.account_name
                    and r.get("container") == args.container)
    if az01:
        print(f"[AZ01] Evidência aprovada reutilizada: {az01}", flush=True)
        code01 = 0
    else:
        code01 = executar(src / "provisionar_container_azure.py", raiz,
                          ["--account-name", args.account_name, "--container", args.container],
                          docs / "AZ01.log")
        az01 = anterior(base / "AZ01", "AZ01",
                        lambda r: r.get("status") == "APROVADO" and r.get("account_name") == args.account_name
                        and r.get("container") == args.container)
    az02 = None
    code02 = None
    if code01 == 0 and az01:
        code02 = executar(src / "sincronizar_datalake_azure.py", raiz,
                          ["--account-name", args.account_name, "--container", args.container], docs / "AZ02.log")
        az02 = anterior(base / "AZ02", "AZ02",
                        lambda r: r.get("status") == "APROVADO" and
                        r.get("arquivos_previstos") == len(files) and
                        r.get("account_name") == args.account_name and r.get("container") == args.container)
    status = "APROVADO" if code01 == 0 and code02 == 0 and az01 and az02 else "REPROVADO"
    report = {"etapa": "pipeline_azure", "run_id": run_id, "status": status,
              "sha256_entrada": digest, "account_name": args.account_name,
              "container": args.container, "arquivos_inventariados": len(files),
              "AZ01": str(az01.relative_to(raiz)) if az01 else None,
              "AZ02": str(az02.relative_to(raiz)) if az02 else None,
              "exit_codes": {"AZ01": code01, "AZ02": code02},
              "data_hora": datetime.now().astimezone().isoformat()}
    (docs / "conclusao_pipeline_azure.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (docs / "conclusao_pipeline_azure.md").write_text(
        f"# Pipeline Azure\n\nExecução: `{run_id}`; status: **{status}**.\n\n"
        f"Arquivos inventariados: {len(files)}; AZ01: `{report['AZ01']}`; AZ02: `{report['AZ02']}`.\n",
        encoding="utf-8")
    print(f"[pipeline_azure] {status}; docs: {docs}", flush=True)
    return 0 if status == "APROVADO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
