"""FINAL01: audita a execução completa, sem gerar dados nem publicar arquivos.

Chamado somente no fim de run_pipeline_projeto.py, com --pipeline-run-id.
Gera docs/execucoes/FINAL01/<run_id>/conclusao_FINAL01.json e .md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


SILVER = "os_2022_silver.parquet"
PBIX = "Power BI/manutencao_fabrica_2_os_2022.pbix"
DOCS = ("README.md", "docs/analise/EDA_Silver_OS_2022_20260928.md",
        "docs/analise/painel_power_bi_os_2022.md")
SQL = ("sql/01_modelo_dimensional_os_2022.sql",
       "sql/02_carregar_silver_sql_server.py",
       "sql/03_reconciliar_silver_sql_server.py",
       "sql/04_kpis_os_2022.sql")
CODE = ("src/finalizar_projeto.py", "src/gerar_gold_os.py", "src/run_pipeline_projeto.py",
        "src/sincronizar_github.py")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def evidence(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Evidência não é objeto JSON: {path}")
    return data


def latest_approved(root: Path, stage: str, predicate) -> tuple[Path, dict] | None:
    base = root / "docs" / "execucoes" / stage
    for path in sorted(base.glob(f"*/conclusao_{stage}.json"), reverse=True):
        try:
            data = evidence(path)
            if data.get("status") == "APROVADO" and predicate(data):
                return path, data
        except (OSError, ValueError, TypeError):
            continue
    return None


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True,
                            text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("projeto", nargs="?", type=Path, default=Path("."))
    parser.add_argument("--pipeline-run-id", required=True)
    parser.add_argument("--account-name", required=True)
    parser.add_argument("--container", required=True)
    args = parser.parse_args()
    root = args.projeto.resolve()
    run_id = args.pipeline_run_id
    if not run_id.isdigit() and not all(c.isdigit() or c == "_" for c in run_id):
        parser.error("--pipeline-run-id inválido")
    base = root / "docs" / "execucoes"
    output = base / "FINAL01" / run_id
    output.mkdir(parents=True, exist_ok=False)
    report = {"etapa": "FINAL01", "run_id": run_id, "status": "REPROVADO",
              "data_hora_inicio": datetime.now().astimezone().isoformat(),
              "checagens": [], "erro": None}

    def check(name: str, ok: bool, detail: str) -> None:
        report["checagens"].append({"item": name, "status": "APROVADO" if ok else "REPROVADO",
                                    "detalhe": detail})

    try:
        parent_path = base / "pipeline_projeto" / run_id / "conclusao_pipeline_projeto.json"
        parent = evidence(parent_path)
        stages = {x.get("etapa"): x for x in parent.get("etapas", [])}
        # A origem pode sair com código 1 quando AB00 registra a divergência
        # histórica do anual legado. O orquestrador só aprova essa etapa após
        # validar a evidência AB00–AB04; preservar essa decisão aqui.
        gate = (parent.get("run_id") == run_id and parent.get("status") == "EM_ANDAMENTO"
                and stages.get("origem", {}).get("status") == "APROVADO"
                and stages["origem"].get("exit_code") in (0, 1)
                and bool(stages["origem"].get("evidencia"))
                and all(stages.get(k, {}).get("status") == "APROVADO" and
                        stages[k].get("exit_code") == 0 for k in ("gold", "azure", "github")))
        check("ordem_pipeline", gate, "Origem validada pelo orquestrador; Gold, Azure e GitHub aprovados nesta execução")
        if not gate:
            raise ValueError("Finalizador só roda depois de origem, Gold, Azure e GitHub aprovados")

        origin_path = root / stages["origem"]["evidencia"]
        origin = evidence(origin_path)
        source_run = origin.get("run_id")
        ab04 = evidence(base / "AB04" / source_run / "conclusao_AB04.json")
        silver_rel = ab04.get("parquet")
        silver = root / silver_rel
        silver_ok = (ab04.get("status") == "APROVADO" and silver.is_file()
                     and sha256(silver) == ab04.get("sha256_parquet")
                     and ab04.get("linhas") == ab04.get("os_distintas"))
        check("silver_ab04", silver_ok, f"Execução {source_run}; arquivo {silver_rel}")

        gold_path = base / "GO01" / source_run / "conclusao_GO01.json"
        gold = evidence(gold_path)
        gold_file = root / gold["parquet"]
        gold_ok = (gold.get("status") == "APROVADO" and gold.get("source_run") == source_run
                   and gold_file.is_file() and sha256(gold_file) == gold.get("sha256_parquet")
                   and gold.get("os_registradas") == ab04.get("linhas")
                   and gold.get("valor_registrado_brl") == ab04.get("custo_total_brl"))
        check("gold_go01", gold_ok, f"Arquivo local {gold['parquet']} aprovado e reconciliado")

        azure_ref = latest_approved(
            root, "pipeline_azure",
            lambda x: x.get("account_name") == args.account_name and
            x.get("container") == args.container)
        azure_ok = azure_ref is not None
        if azure_ok:
            az = azure_ref[1]
            az02_path = root / az["AZ02"]
            az02 = evidence(az02_path)
            from sincronizar_datalake_azure import inventario
            files = inventario(root)
            signature = hashlib.sha256()
            for f in files:
                signature.update(json.dumps(f, sort_keys=True, ensure_ascii=False).encode("utf-8"))
            azure_ok = (az02.get("status") == "APROVADO" and
                        az02.get("account_name") == az.get("account_name") and
                        az02.get("container") == az.get("container") and
                        az02.get("sha256_inventario") == signature.hexdigest() and
                        az02.get("arquivos_previstos") == len(files) and
                        len(az02.get("arquivos", [])) == len(files) and
                        all(f.get("status") in ("ENVIADO_VERIFICADO", "REUTILIZADO_VERIFICADO")
                            for f in az02.get("arquivos", [])))
        check("azure_az02", azure_ok,
              "Inventário local datalake/ (incluindo 03_gold/) + quality/ igual ao AZ02 aprovado")

        sql_ref = latest_approved(root, "SQL01", lambda d: d.get("source_run") == source_run)
        sql_ok = sql_ref is not None and (
            not sql_ref[1].get("divergencias") and not sql_ref[1].get("erro") and
            sql_ref[1].get("linhas_silver") == ab04.get("linhas") == sql_ref[1].get("linhas_fato")
            == sql_ref[1].get("linhas_join") == sql_ref[1].get("os_distintas_sql") and
            sql_ref[1].get("soma_silver_brl") == sql_ref[1].get("soma_sql_brl"))
        check("sql_sql01", sql_ok,
              f"Reconciliação aprovada vinculada à Silver {source_run}; não substitui nova consulta SQL")

        required = DOCS + SQL + CODE + (PBIX,)
        for rel in required:
            path = root / rel
            check("arquivo_local", path.is_file() and path.stat().st_size > 0 if path.is_file() else False,
                  rel)
        panel = root / DOCS[2]
        if panel.is_file():
            content = panel.read_text(encoding="utf-8")
            check("documentacao_painel", PBIX in content and "337" in content and
                  "449.367,51" in content and "75.780,00" in content and
                  "limites" in content.lower(),
                  "Caminho, KPIs e limitações documentados; não verifica medidas internas do PBIX")

        gh_ref = latest_approved(root, "GH01", lambda d: d.get("commit") == git(root, "rev-parse", "HEAD"))
        gh_ok = gh_ref is not None
        if gh_ok:
            paths = set(git(root, "ls-tree", "-r", "--name-only", "HEAD").splitlines())
            gh_ok = all(rel in paths for rel in required)
        check("github_commit", gh_ok, "HEAD da etapa GH01 contém código, SQL, documentação e PBIX")
        report["origem_run_id"] = source_run
        report["evidencias"] = {"pipeline_origem": str(origin_path.relative_to(root)),
                                "AB04": f"docs/execucoes/AB04/{source_run}/conclusao_AB04.json",
                                "GO01": str(gold_path.relative_to(root)),
                                "AZ02": str(az02_path.relative_to(root)) if azure_ref else None,
                                "SQL01": str(sql_ref[0].relative_to(root)) if sql_ref else None,
                                "GH01": str(gh_ref[0].relative_to(root)) if gh_ref else None}
        report["status"] = ("APROVADO" if all(c["status"] == "APROVADO"
                                                for c in report["checagens"]) else "REPROVADO")
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, ImportError) as exc:
        report["erro"] = f"{type(exc).__name__}: {exc}"
    report["data_hora_fim"] = datetime.now().astimezone().isoformat()
    (output / "conclusao_FINAL01.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# FINAL01 — Encerramento do projeto", "", f"Status: **{report['status']}**.", "",
             f"Execução: `{run_id}`; Silver: `{report.get('origem_run_id', 'indisponível')}`.", "",
             "## Checagens", ""]
    lines += [f"- {x['status']}: {x['item']} — {x['detalhe']}" for x in report["checagens"]]
    lines += ["", f"Erro: {report['erro'] or 'nenhum'}.", "",
              "O PBIX é verificado como arquivo versionado; sua atualização e seus visuais não são lidos automaticamente."]
    (output / "conclusao_FINAL01.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[FINAL01] {report['status']}; evidência: {output}", flush=True)
    for item in report["checagens"]:
        if item["status"] == "REPROVADO":
            print(f"[FINAL01] REPROVADO: {item['detalhe']}", flush=True)
    if report["erro"]:
        print(f"[FINAL01] {report['erro']}", flush=True)
    return 0 if report["status"] == "APROVADO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
