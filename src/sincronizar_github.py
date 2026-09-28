"""GH01: versiona apenas código e documentação pública, com evidência local.

Da raiz: python -u .\\src\\sincronizar_github.py .
Nunca usa git add . nem inclui datalake/, quality/ ou docs/execucoes/.
Inclui somente arquivos Markdown diretamente em docs/analise/.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path


PUBLICOS = (".gitignore", "README.md", "GITHUB_E_AZURE.md")
SCRIPTS = ("conferir_anual_gerado.py", "contar_arquivos_landing_os.py",
           "gerar_anual_landing.py", "gerar_silver_os.py",
           "provisionar_container_azure.py", "run_pipeline_azure.py",
           "run_pipeline_origem.py", "run_pipeline_projeto.py",
           "sincronizar_datalake_azure.py", "sincronizar_github.py",
           "validar_classificacao_setor_os.py")
ESPERADO = "GuilhermeBuenoSampaio/manutencao-fabrica-2-os-2022"


def git(raiz: Path, *args: str) -> str:
    p = subprocess.run(["git", *args], cwd=raiz, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if p.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {p.stderr.strip() or p.stdout.strip()}")
    return p.stdout.strip()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("projeto", nargs="?", type=Path, default=Path("."))
    p.add_argument("--run-id")
    args = p.parse_args()
    raiz = args.projeto.resolve()
    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    docs = raiz / "docs" / "execucoes" / "GH01" / run_id
    docs.mkdir(parents=True, exist_ok=False)
    report = {"etapa": "GH01", "run_id": run_id, "status": "REPROVADO",
              "data_hora": datetime.now().astimezone().isoformat(), "arquivos": [],
              "commit": None, "remote": None, "erro": None}
    try:
        remote = git(raiz, "remote", "get-url", "origin")
        report["remote"] = remote
        if ESPERADO.lower() not in remote.lower():
            raise ValueError(f"Remote origin inesperado: {remote}")
        if git(raiz, "branch", "--show-current") != "main":
            raise ValueError("A branch local precisa ser main")
        rastreados = git(raiz, "ls-files", "--", "datalake", "quality", "docs/execucoes")
        if rastreados:
            raise ValueError("Há dados ou evidências sensíveis rastreados pelo Git; revise antes do push")
        antes = git(raiz, "diff", "--cached", "--name-only")
        if antes:
            raise ValueError("Existem alterações já preparadas no Git; revise o índice antes de executar GH01")
        caminhos = [x for x in PUBLICOS if (raiz / x).is_file()]
        caminhos += [f"src/{nome}" for nome in SCRIPTS if (raiz / "src" / nome).is_file()]
        pasta_analise = raiz / "docs" / "analise"
        if pasta_analise.is_dir() and not pasta_analise.is_symlink():
            caminhos += [arquivo.relative_to(raiz).as_posix()
                         for arquivo in sorted(pasta_analise.glob("*.md"))
                         if arquivo.is_file() and not arquivo.is_symlink()]
        if not caminhos:
            raise ValueError("Nenhum código ou documento público encontrado")
        # Adiciona somente a lista explícita; dados de origem nunca entram no índice.
        git(raiz, "add", "--", *caminhos)
        preparados = git(raiz, "diff", "--cached", "--name-only").splitlines()
        if any(x not in caminhos for x in preparados):
            raise ValueError("Índice contém arquivo fora da lista pública")
        report["arquivos"] = preparados
        if preparados:
            git(raiz, "commit", "-m", "Atualiza codigo e documentacao analitica")
        report["commit"] = git(raiz, "rev-parse", "HEAD")
        # Push sem force: divergência remota reprova a etapa e preserva ambos os históricos.
        git(raiz, "push", "origin", "main")
        report["status"] = "APROVADO"
    except (OSError, RuntimeError, ValueError) as exc:
        report["erro"] = str(exc)
    (docs / "conclusao_GH01.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (docs / "conclusao_GH01.md").write_text(
        f"# GH01 — versionamento GitHub\n\nStatus: **{report['status']}**.\n\n"
        f"Commit: `{report['commit']}`. Arquivos no commit: {len(report['arquivos'])}.\n"
        f"Remote: `{report['remote']}`. Erro: {report['erro'] or 'nenhum'}.\n",
        encoding="utf-8")
    print(f"[GH01] {report['status']}; commit: {report['commit']}; docs: {docs}", flush=True)
    if report["erro"]:
        print(f"[GH01] {report['erro']}", flush=True)
    return 0 if report["status"] == "APROVADO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
