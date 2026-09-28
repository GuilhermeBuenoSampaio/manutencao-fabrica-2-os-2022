"""AZ02: espelha datalake/ e quality/ no contêiner sem sobrescrever arquivos.

Executar da raiz: python -u .\\src\\sincronizar_datalake_azure.py .
Todos os arquivos são baixados após envio (ou quando já existem) para comparar SHA-256.
Arquivos alterados no mesmo caminho remoto geram CONFLITO; nenhuma remoção é feita.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

CONTAINER = "manutencao-fabrica-2-os-2022"
ROOTS = ("datalake", "quality")
BUILD = "AZ02_PYTHON_DIRETO_20260928_V2"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def cli(*args: str) -> dict:
    if os.name == "nt":
        launcher = shutil.which("az.cmd")
        if not launcher:
            raise RuntimeError("Azure CLI (az.cmd) não encontrado no PATH do Python.")
        python_az = Path(launcher).resolve().parent.parent / "python.exe"
        if not python_az.is_file():
            raise RuntimeError(f"Python do Azure CLI não encontrado: {python_az}")
        cmd = [str(python_az), "-IBm", "azure.cli"]
    else:
        az = shutil.which("az")
        if not az:
            raise RuntimeError("Azure CLI não encontrado no PATH do Python.")
        cmd = [az]
    p = subprocess.run([*cmd, *args, "--output", "json", "--only-show-errors"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode:
        raise RuntimeError(f"az {' '.join(args[:3])}: {p.stderr.strip() or p.stdout.strip()}")
    return json.loads(p.stdout or "{}")


def inventario(raiz: Path) -> list[dict]:
    files = []
    for root in ROOTS:
        base = raiz / root
        if not base.is_dir():
            raise ValueError(f"Pasta obrigatória ausente: {base}")
        for item in base.rglob("*"):
            if item.is_symlink():
                raise ValueError(f"Link simbólico não permitido: {item}")
            if item.is_file() and not item.name.startswith("~$"):
                files.append({"path": item.relative_to(raiz).as_posix(),
                              "bytes": item.stat().st_size, "sha256": digest(item)})
    return sorted(files, key=lambda x: x["path"].casefold())


def verificar_ab04(raiz: Path, files: list[dict]) -> None:
    mapping = {f["path"]: f["sha256"] for f in files}
    for name, sha in mapping.items():
        if not name.startswith("datalake/02_silver/") or not name.endswith("/os_2022_silver.parquet"):
            continue
        run_id = name.split("/")[2]
        report = raiz / "docs" / "execucoes" / "AB04" / run_id / "conclusao_AB04.json"
        if not report.is_file():
            raise ValueError(f"Silver sem evidência AB04: {name}")
        doc = json.loads(report.read_text(encoding="utf-8"))
        if doc.get("status") != "APROVADO" or doc.get("parquet") != name or doc.get("sha256_parquet") != sha:
            raise ValueError(f"Silver diferente da AB04 aprovada: {name}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("projeto", nargs="?", type=Path, default=Path("."))
    p.add_argument("--account-name", default="stcustomeranalyticsgb01")
    p.add_argument("--container", default=CONTAINER)
    p.add_argument("--run-id")
    args = p.parse_args()
    raiz = args.projeto.resolve()
    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    docs = raiz / "docs" / "execucoes" / "AZ02" / run_id
    docs.mkdir(parents=True, exist_ok=False)
    report = {"etapa": "AZ02", "build": BUILD, "run_id": run_id, "status": "EM_ANDAMENTO",
              "data_hora_inicio": datetime.now().astimezone().isoformat(),
              "account_name": args.account_name, "container": args.container,
              "raizes": list(ROOTS), "arquivos": [], "erro": None}
    output = docs / "conclusao_AZ02.json"

    def checkpoint() -> None:
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    try:
        files = inventario(raiz)
        verificar_ab04(raiz, files)
        if not files:
            raise ValueError("Nenhum arquivo em datalake/ ou quality/")
        signature = hashlib.sha256()
        for f in files:
            signature.update(json.dumps(f, sort_keys=True, ensure_ascii=False).encode("utf-8"))
        report["sha256_inventario"] = signature.hexdigest()
        report["arquivos_previstos"] = len(files)
        report["gold_local"] = (raiz / "datalake" / "03_gold").is_dir()
        checkpoint()
        common = ("--account-name", args.account_name, "--container-name", args.container,
                  "--auth-mode", "login")
        for n, f in enumerate(files, 1):
            item = raiz / f["path"]
            row = dict(f)
            try:
                exists = cli("storage", "blob", "exists", *common, "--name", f["path"])
                old = bool(exists.get("exists"))
                if not old:
                    cli("storage", "blob", "upload", *common, "--name", f["path"],
                        "--file", str(item), "--overwrite", "false")
                with tempfile.TemporaryDirectory(prefix="az02_") as temp:
                    copy = Path(temp) / "verificacao"
                    cli("storage", "blob", "download", *common, "--name", f["path"],
                        "--file", str(copy), "--overwrite", "false")
                    remote_sha = digest(copy)
                row["sha256_download"] = remote_sha
                if remote_sha != f["sha256"]:
                    row["status"] = "CONFLITO" if old else "DIVERGENCIA_APOS_UPLOAD"
                else:
                    row["status"] = "REUTILIZADO_VERIFICADO" if old else "ENVIADO_VERIFICADO"
            except (OSError, ValueError, RuntimeError) as exc:
                row["status"] = "ERRO"
                row["erro"] = str(exc)
            report["arquivos"].append(row)
            checkpoint()
            print(f"[AZ02] {n}/{len(files)} {row['status']}: {f['path']}", flush=True)
            if row["status"] not in ("REUTILIZADO_VERIFICADO", "ENVIADO_VERIFICADO"):
                break
        counts = Counter(x["status"] for x in report["arquivos"])
        report["contagem_status"] = dict(counts)
        report["status"] = ("APROVADO" if len(report["arquivos"]) == len(files) and
                            all(x["status"] in ("REUTILIZADO_VERIFICADO", "ENVIADO_VERIFICADO")
                                for x in report["arquivos"]) else "REPROVADO")
    except (OSError, ValueError, RuntimeError) as exc:
        report["status"] = "REPROVADO"
        report["erro"] = str(exc)
    report["data_hora_fim"] = datetime.now().astimezone().isoformat()
    checkpoint()
    (docs / "conclusao_AZ02.md").write_text(
        f"# AZ02 — Data Lake e Quality no Azure\n\nExecução: `{run_id}`; status: **{report['status']}**.\n\n"
        f"Conta/contêiner: `{args.account_name}/{args.container}`.\n"
        f"Arquivos previstos: {report.get('arquivos_previstos', 0)}; verificados: {len(report['arquivos'])}.\n"
        f"Inventário SHA-256: `{report.get('sha256_inventario', 'indisponível')}`.\n"
        f"Gold local existente: {report.get('gold_local', False)}.\n"
        f"Resultado por arquivo no JSON; erro: {report['erro'] or 'nenhum'}.\n", encoding="utf-8")
    print(f"[AZ02] {report['status']}: {len(report['arquivos'])}/{report.get('arquivos_previstos', 0)} arquivos; docs: {docs}", flush=True)
    return 0 if report["status"] == "APROVADO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
