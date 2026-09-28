r"""Orquestra AB00 a AB04 (origem, classificação e Silver Parquet).

Da raiz do projeto: python -u .\src\run_pipeline_origem.py .
Uma entrada idêntica a uma execução documentada reutiliza aquela evidência.
Use --force apenas para repetir deliberadamente os mesmos dados e scripts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def resumo_entrada(raiz: Path, src: Path) -> dict:
    """SHA-256 dos bytes relevantes; saída e documentos não entram no cálculo."""
    landing = raiz / "datalake" / "00_landing"
    anual = raiz / "datalake" / "01_bronze_raw" / "A-OS_2022.xlsx"
    manual = raiz / "quality" / "AB02" / "manual-20260928_003359_127063" / "classificacao_setor_os_2022.xlsx"
    arquivos = sorted((p for p in landing.rglob("*") if p.is_file() and
                       p.suffix.lower() in {".xlsm", ".xlsx"}),
                      key=lambda p: p.relative_to(raiz).as_posix().casefold())
    arquivos += [anual, manual, src / "contar_arquivos_landing_os.py",
                 src / "gerar_anual_landing.py", src / "conferir_anual_gerado.py",
                 src / "validar_classificacao_setor_os.py",
                 src / "gerar_silver_os.py",
                 src / "run_pipeline_origem.py"]
    todos = hashlib.sha256()
    erros = []
    for arquivo in arquivos:
        nome = arquivo.relative_to(raiz).as_posix().encode("utf-8")
        todos.update(len(nome).to_bytes(4, "big"))
        todos.update(nome)
        try:
            with arquivo.open("rb") as stream:
                digest = hashlib.sha256()
                for bloco in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(bloco)
            todos.update(digest.digest())
        except OSError as exc:
            erro = f"{arquivo.relative_to(raiz)}: {type(exc).__name__}: {exc}"
            erros.append(erro)
            todos.update(erro.encode("utf-8"))
    return {"sha256": todos.hexdigest(), "arquivos_landing": len(arquivos) - 8,
            "erros_leitura": erros}


def execucao_equivalente(raiz: Path, assinatura: str) -> tuple[Path, dict] | None:
    base = raiz / "docs" / "execucoes" / "pipeline_origem"
    if not base.is_dir():
        return None
    for caminho in sorted(base.glob("*/conclusao_pipeline_origem.json"), reverse=True):
        try:
            relatorio = json.loads(caminho.read_text(encoding="utf-8"))
            if relatorio.get("entrada", {}).get("sha256") != assinatura:
                continue
            etapas = relatorio.get("etapas", [])
            if {e.get("etapa") for e in etapas} != {"AB00", "AB01", "AB02", "AB03", "AB04"}:
                continue
            if not all(e.get("concluido") and e.get("status") in
                       {"CONCLUIDO_APROVADO", "CONCLUIDO_COM_PENDENCIAS"}
                       for e in etapas):
                continue
            if not all((raiz / p).is_file() and (raiz / p).stat().st_size > 0
                       for e in etapas for p in e.get("documentacao", [])):
                continue
            ab00 = next(e for e in etapas if e["etapa"] == "AB00")
            doc = json.loads((raiz / ab00["documentacao"][0]).read_text(encoding="utf-8"))
            if doc.get("erro_leitura_anual"):
                continue  # acesso temporário ao anual: permitir nova tentativa
            return caminho, relatorio
        except (OSError, ValueError, KeyError, IndexError):
            continue
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("projeto", nargs="?", type=Path, default=Path("."))
    parser.add_argument("--force", action="store_true", help="repete entradas idênticas deliberadamente")
    args = parser.parse_args()
    raiz = args.projeto.resolve()
    src = Path(__file__).resolve().parent
    entrada = resumo_entrada(raiz, src)
    anterior = None if args.force or entrada["erros_leitura"] else execucao_equivalente(raiz, entrada["sha256"])
    if anterior:
        caminho, relatorio = anterior
        print(f"Entrada e scripts idênticos à execução {relatorio['run_id']}.", flush=True)
        print(f"Resultados já documentados: {caminho}", flush=True)
        print("Nenhum arquivo novo foi gerado.", flush=True)
        return 0 if relatorio.get("status") == "APROVADO" else 1
    if entrada["erros_leitura"]:
        print("Não foi possível verificar todos os bytes de entrada; a execução seguirá sem reutilização:", flush=True)
        for erro in entrada["erros_leitura"]:
            print(f"  {erro}", flush=True)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    saida = raiz / "docs" / "execucoes" / "pipeline_origem" / run_id
    saida.mkdir(parents=True, exist_ok=False)
    etapas = [
        ("AB00", src / "contar_arquivos_landing_os.py", ["--run-id", run_id]),
        ("AB01", src / "gerar_anual_landing.py", ["--run-id", run_id]),
        ("AB02", src / "conferir_anual_gerado.py", ["--run-id", run_id,
                 "--origem-run-id", run_id]),
        ("AB03", src / "validar_classificacao_setor_os.py", ["--run-id", run_id,
                 "--origem-run-id", run_id,
                 "--manual-id", "manual-20260928_003359_127063"]),
        ("AB04", src / "gerar_silver_os.py", ["--run-id", run_id,
                 "--origem-run-id", run_id, "--ab03-run-id", run_id,
                 "--manual-id", "manual-20260928_003359_127063"]),
    ]
    resultados = []
    for codigo, script, extras in etapas:
        if not script.is_file():
            resultados.append({"etapa": codigo, "status": "NAO_EXECUTADO", "motivo": f"Arquivo ausente: {script}"})
            print(f"[{codigo}] Arquivo ausente: {script}", flush=True)
            continue
        comando = [sys.executable, "-u", str(script), str(raiz), *extras]
        print(f"[{codigo}] Iniciando {script.name}", flush=True)
        log = saida / f"{codigo}.log"
        with log.open("w", encoding="utf-8") as arquivo:
            processo = subprocess.Popen(
                comando, cwd=raiz, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1,
            )
            assert processo.stdout is not None
            for linha in processo.stdout:
                arquivo.write(linha)
                arquivo.flush()
                print(linha, end="", flush=True)
            retorno = processo.wait()
        docs = raiz / "docs" / "execucoes" / codigo / run_id
        json_path = docs / f"conclusao_{codigo}.json"
        md_path = docs / f"conclusao_{codigo}.md"
        evidencias = [json_path, md_path]
        if codigo == "AB01":
            evidencias.append(raiz / "quality" / "AB01" / run_id / "A-OS_2022_gerado.xlsx")
        if codigo == "AB04":
            evidencias.append(raiz / "datalake" / "02_silver" / run_id / "os_2022_silver.parquet")
        documentado = all(p.is_file() and p.stat().st_size > 0 for p in evidencias)
        status_documentado = None
        if documentado:
            try:
                documento = json.loads(json_path.read_text(encoding="utf-8"))
                status_documentado = documento.get("status") if documento.get("etapa") == codigo else None
            except (OSError, ValueError):
                documentado = False
        concluido = documentado and status_documentado in {"APROVADO", "REPROVADO"}
        status = ("INCOMPLETO_SEM_DOCUMENTACAO" if not concluido else
                  "CONCLUIDO_APROVADO" if retorno == 0 and status_documentado == "APROVADO" else
                  "CONCLUIDO_COM_PENDENCIAS" if retorno == 1 and status_documentado == "REPROVADO" else
                  "INCOMPLETO_STATUS_INCONSISTENTE")
        resultados.append({
            "etapa": codigo, "status": status, "concluido": concluido,
            "status_qualidade": status_documentado,
            "exit_code": retorno, "script": str(script.relative_to(raiz)),
            "comando": comando, "log": str(log.relative_to(raiz)),
            "documentacao": [str(p.relative_to(raiz)) for p in evidencias],
        })
        print(f"[{codigo}] {status}; código {retorno}", flush=True)
    resumo = {"run_id": run_id, "projeto": str(raiz), "entrada": entrada, "etapas": resultados,
              "status": "APROVADO" if all(r["status"] == "CONCLUIDO_APROVADO" for r in resultados) else "REPROVADO"}
    destino = saida / "conclusao_pipeline_origem.json"
    destino.write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Conclusão: {resumo['status']}; evidência: {destino}", flush=True)
    return 0 if resumo["status"] == "APROVADO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
