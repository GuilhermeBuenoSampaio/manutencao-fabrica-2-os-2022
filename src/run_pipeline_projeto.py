"""Orquestra origem, Azure e GitHub; registra evidência de cada execução.

Da raiz: python -u .\\src\\run_pipeline_projeto.py .
AB00 pode registrar a divergência do anual legado; AB01–AB04 devem aprovar.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from run_pipeline_origem import execucao_equivalente, resumo_entrada


def executar(raiz: Path, script: Path, extras: list[str], log: Path) -> int:
    ambiente = os.environ.copy()
    # O console do Windows pode usar cp1252; toda a cadeia de processos usa
    # UTF-8 para preservar caracteres das planilhas e evitar UnicodeEncodeError.
    ambiente["PYTHONIOENCODING"] = "utf-8"
    with log.open("w", encoding="utf-8") as out:
        p = subprocess.Popen([sys.executable, "-u", str(script), str(raiz), *extras],
                             cwd=raiz, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, encoding="utf-8", errors="replace", env=ambiente)
        assert p.stdout is not None
        for linha in p.stdout:
            out.write(linha)
            out.flush()
            print(linha, end="", flush=True)
        return p.wait()


def ler_etapa(raiz: Path, codigo: str, run_id: str) -> dict:
    path = raiz / "docs" / "execucoes" / codigo / run_id / f"conclusao_{codigo}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def validar_origem(raiz: Path, origem: dict) -> tuple[bool, str]:
    etapas = {e["etapa"]: e for e in origem.get("etapas", [])}
    if set(etapas) != {"AB00", "AB01", "AB02", "AB03", "AB04"}:
        return False, "Etapas AB00–AB04 incompletas"
    if any(etapas[c].get("status") != "CONCLUIDO_APROVADO" for c in
           ("AB01", "AB02", "AB03", "AB04")):
        return False, "AB01, AB02, AB03 ou AB04 não aprovada"
    if etapas["AB00"].get("status") not in ("CONCLUIDO_APROVADO", "CONCLUIDO_COM_PENDENCIAS"):
        return False, "AB00 sem conclusão documentada"
    run_id = origem["run_id"]
    try:
        a, b, c, d, e = (ler_etapa(raiz, x, run_id) for x in
                         ("AB00", "AB01", "AB02", "AB03", "AB04"))
        if a["status"] == "REPROVADO":
            # Só aceita diferença de contagem com o anual legado. Toda a
            # reconstrução é conferida separadamente pelo AB02.
            if (a.get("erro_leitura_anual") or a.get("arquivos_invalidos") or
                a.get("codigos_repetidos") or a.get("arquivos_sem_codigo") or
                a.get("nomes_repetidos") or a.get("linhas_anual") is None or
                a.get("linhas_anual") == a.get("documentos_validos")):
                return False, "AB00 reprovada por motivo além da divergência do anual legado"
        elif a["status"] != "APROVADO":
            return False, "Status AB00 inesperado"
        n = a["documentos_validos"]
        if not (n == b["linhas_geradas"] == c["documentos_landing"] ==
                c["linhas_geradas"] == d["linhas_manual"] == e["linhas"] == e["os_distintas"]):
            return False, "Contagens de O.S. divergentes entre AB00 e AB04"
        if (c["planilha_sha256"] != d["sha256_origem"] or
            d["sha256_manual"] != e["sha256_classificacao"]):
            return False, "SHA-256 de linhagem divergente"
        if not (raiz / e["parquet"]).is_file():
            return False, "Parquet Silver ausente"
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return False, f"Evidência local inválida: {exc}"
    return True, ("AB00: diferença histórica do anual legado documentada" if
                  a["status"] == "REPROVADO" else "AB00–AB04 aprovadas")


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
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    docs = raiz / "docs" / "execucoes" / "pipeline_projeto" / run_id
    docs.mkdir(parents=True, exist_ok=False)
    report = {"etapa": "pipeline_projeto", "run_id": run_id,
              "data_hora_inicio": datetime.now().astimezone().isoformat(),
              "status": "EM_ANDAMENTO", "etapas": [], "erro": None}

    def salvar() -> None:
        (docs / "conclusao_pipeline_projeto.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    salvar()
    try:
        azure_script = src / "run_pipeline_azure.py"
        if "enviar_silver_azure" in azure_script.read_text(encoding="utf-8"):
            raise ValueError("run_pipeline_azure.py ainda contém enviar_silver_azure; substitua pelo arquivo corrigido")
        if not (src / "sincronizar_datalake_azure.py").is_file():
            raise ValueError("sincronizar_datalake_azure.py ausente em src/")
        codigo = executar(raiz, src / "run_pipeline_origem.py", [], docs / "origem.log")
        if codigo not in (0, 1):
            raise ValueError(f"Execução local interrompida com código inesperado: {codigo}")
        assinatura = resumo_entrada(raiz, src)["sha256"]
        anterior = execucao_equivalente(raiz, assinatura)
        if not anterior:
            raise ValueError("Execução da origem sem evidência equivalente e completa")
        caminho, origem = anterior
        ok, detalhe = validar_origem(raiz, origem)
        report["etapas"].append({"etapa": "origem", "exit_code": codigo,
                                 "evidencia": str(caminho.relative_to(raiz)),
                                 "status": "APROVADO" if ok else "REPROVADO", "detalhe": detalhe})
        salvar()
        if not ok:
            raise ValueError(detalhe)
        codigo = executar(raiz, src / "gerar_gold_os.py",
                          ["--source-run", origem["run_id"]], docs / "gold.log")
        report["etapas"].append({"etapa": "gold", "exit_code": codigo,
                                 "status": "APROVADO" if codigo == 0 else "REPROVADO"})
        salvar()
        if codigo:
            raise ValueError("Materialização Gold reprovada; consulte gold.log")
        codigo = executar(raiz, src / "run_pipeline_azure.py",
                          ["--account-name", args.account_name, "--container", args.container],
                          docs / "azure.log")
        report["etapas"].append({"etapa": "azure", "exit_code": codigo,
                                 "status": "APROVADO" if codigo == 0 else "REPROVADO"})
        salvar()
        if codigo:
            raise ValueError("Sincronização Azure reprovada; consulte azure.log")
        codigo = executar(raiz, src / "sincronizar_github.py", [], docs / "github.log")
        report["etapas"].append({"etapa": "github", "exit_code": codigo,
                                 "status": "APROVADO" if codigo == 0 else "REPROVADO"})
        salvar()
        if codigo:
            raise ValueError("Versionamento GitHub reprovado; consulte github.log")
        codigo = executar(raiz, src / "finalizar_projeto.py",
                          ["--pipeline-run-id", run_id,
                           "--account-name", args.account_name,
                           "--container", args.container], docs / "finalizador.log")
        report["etapas"].append({"etapa": "finalizador", "exit_code": codigo,
                                 "status": "APROVADO" if codigo == 0 else "REPROVADO"})
        salvar()
        if codigo:
            raise ValueError("Finalização reprovada; consulte finalizador.log e a evidência FINAL01")
        report["status"] = "APROVADO"
    except (OSError, ValueError, RuntimeError) as exc:
        report["status"] = "REPROVADO"
        report["erro"] = str(exc)
    report["data_hora_fim"] = datetime.now().astimezone().isoformat()
    salvar()
    (docs / "conclusao_pipeline_projeto.md").write_text(
        f"# Pipeline do projeto\n\nExecução: `{run_id}`. Status: **{report['status']}**.\n\n"
        + "\n".join(f"- {e['etapa']}: {e['status']} — {e.get('detalhe', '')}" for e in report["etapas"])
        + f"\n\nErro: {report['erro'] or 'nenhum'}.\n", encoding="utf-8")
    print(f"[pipeline_projeto] {report['status']}; evidência: {docs}", flush=True)
    if report["erro"]:
        print(f"[pipeline_projeto] {report['erro']}", flush=True)
    return 0 if report["status"] == "APROVADO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
