"""AZ01: cria/verifica contêiner ADLS Gen2 privado e documenta resultado.

Da raiz: python -u .\\src\\provisionar_container_azure.py . --account-name NOME_DA_CONTA
Requer Azure CLI autenticado (az login) com permissão sobre a conta.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

CONTAINER = "manutencao-fabrica-2-os-2022"


def comando(*args: str) -> dict:
    process = subprocess.run(["az", *args, "--output", "json"], capture_output=True,
                             text=True, encoding="utf-8", errors="replace")
    if process.returncode:
        raise RuntimeError(f"az {args[0]} {args[1]}: {process.stderr.strip()}")
    return json.loads(process.stdout or "{}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("projeto", nargs="?", type=Path, default=Path("."))
    p.add_argument("--account-name", required=True)
    p.add_argument("--container", default=CONTAINER)
    p.add_argument("--run-id")
    args = p.parse_args()
    if not re.fullmatch(r"[a-z0-9]{3,24}", args.account_name):
        p.error("Nome de conta Azure inválido")
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?", args.container):
        p.error("Nome de contêiner inválido")
    raiz = args.projeto.resolve()
    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    docs = raiz / "docs" / "execucoes" / "AZ01" / run_id
    docs.mkdir(parents=True, exist_ok=False)
    error = None
    try:
        before = None
        try:
            before = comando("storage", "fs", "show", "--name", args.container,
                             "--account-name", args.account_name, "--auth-mode", "login")
        except RuntimeError:
            # Tentar criação; se for erro de permissão, a própria criação falhará e será documentada.
            pass
        created = False
        if before is None:
            comando("storage", "fs", "create", "--name", args.container,
                    "--account-name", args.account_name, "--auth-mode", "login")
            created = True
        after = comando("storage", "fs", "show", "--name", args.container,
                        "--account-name", args.account_name, "--auth-mode", "login")
        public = after.get("properties", {}).get("publicAccess") or after.get("publicAccess")
        if public not in (None, "", "None"):
            raise RuntimeError(f"Contêiner com acesso público inesperado: {public}")
        status = "APROVADO"
    except (RuntimeError, OSError, ValueError) as exc:
        created, after, status, error = False, {}, "REPROVADO", str(exc)
    r = {"etapa": "AZ01", "run_id": run_id, "status": status,
         "account_name": args.account_name, "container": args.container,
         "criado_nesta_execucao": created, "verificacao": after, "erro": error,
         "data_hora": datetime.now().astimezone().isoformat()}
    (docs / "conclusao_AZ01.json").write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    (docs / "conclusao_AZ01.md").write_text(
        f"# AZ01 — contêiner ADLS Gen2\n\nExecução: `{run_id}`. Status: **{status}**.\n"
        f"Conta: `{args.account_name}`. Contêiner: `{args.container}`.\n"
        f"Criado nesta execução: {created}.\nErro: {error or 'nenhum'}.\n", encoding="utf-8")
    print(f"[AZ01] {status}: {args.account_name}/{args.container}; docs: {docs}", flush=True)
    return 0 if status == "APROVADO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
