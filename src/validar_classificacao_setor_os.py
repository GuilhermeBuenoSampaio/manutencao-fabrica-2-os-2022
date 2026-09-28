"""AB03: valida a classificação manual de setor sem alterar a AB01.

Da raiz do projeto:
python -u .\\src\\validar_classificacao_setor_os.py .
Os documentos são gerados em docs/execucoes/AB03/<run_id>/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook

SETOR = "setor"
ACEITOS = {"empanados", "pão de queijo", "geral"}
ORIGEM_PADRAO = "20260928_003359_127063"
MANUAL_PADRAO = "manual-20260928_003359_127063"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def ler(path: Path) -> tuple[tuple, list[tuple], list[str]]:
    wb = load_workbook(path, read_only=True, data_only=True, keep_links=False)
    try:
        abas = wb.sheetnames[:]
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        header = tuple(next(rows))
        return header, [tuple(row) for row in rows], abas
    finally:
        wb.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("projeto", nargs="?", type=Path, default=Path("."))
    parser.add_argument("--origem-run-id", default=ORIGEM_PADRAO)
    parser.add_argument("--manual-id", default=MANUAL_PADRAO,
                        help="pasta manual dentro de quality/AB02")
    parser.add_argument("--run-id", help="identificador exclusivo da evidência AB03")
    args = parser.parse_args()
    raiz = args.projeto.resolve()
    original = raiz / "quality" / "AB01" / args.origem_run_id / "A-OS_2022_gerado.xlsx"
    manual = raiz / "quality" / "AB02" / args.manual_id / "classificacao_setor_os_2022.xlsx"
    if not original.is_file() or not manual.is_file():
        parser.error(f"Arquivo ausente. Original: {original}; manual: {manual}")
    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    docs = raiz / "docs" / "execucoes" / "AB03" / run_id
    docs.mkdir(parents=True, exist_ok=False)
    erros = []
    try:
        header_original, base, abas_original = ler(original)
        header_manual, editadas, abas_manual = ler(manual)
        if abas_original != ["OS_2022"] or abas_manual != ["OS_2022"]:
            erros.append({"erro": "abas inesperadas", "original": abas_original,
                          "manual": abas_manual})
        if header_manual.count(SETOR) != 1 or len(header_manual) != len(header_original) + 1 or tuple(
                col for col in header_manual if col != SETOR) != header_original:
            erros.append({"erro": "estrutura de colunas divergente: só setor pode ter sido acrescentado",
                          "original": header_original, "manual": header_manual})
        if "formulário" not in header_original or "formulário" not in header_manual or SETOR not in header_manual:
            erros.append({"erro": "formulário ou setor ausente; comparação impossível"})
            idx_orig = idx_manual = idx_setor = None
        else:
            idx_orig = header_original.index("formulário")
            idx_manual = header_manual.index("formulário")
            idx_setor = header_manual.index(SETOR)
        origem_chaves = defaultdict(list)
        manual_chaves = defaultdict(list)
        setores = Counter()
        if idx_orig is not None:
            for num, row in enumerate(base, 2):
                key = row[idx_orig] if idx_orig < len(row) else None
                origem_chaves[key].append((num, row))
            for num, row in enumerate(editadas, 2):
                key = row[idx_manual] if idx_manual < len(row) else None
                manual_chaves[key].append((num, row))
                setor = row[idx_setor] if idx_setor < len(row) else None
                if not isinstance(setor, str) or setor.strip().casefold() not in ACEITOS:
                    erros.append({"linha_excel": num, "formulario": key,
                                  "erro": "setor vazio ou fora das categorias", "valor": str(setor)})
                else:
                    setores[setor.strip().casefold()] += 1
                if not isinstance(key, str) or not key.strip():
                    erros.append({"linha_excel": num, "erro": "formulário vazio ou inválido"})
            for rotulo, catalogo in (("original", origem_chaves), ("manual", manual_chaves)):
                for key, occurrences in catalogo.items():
                    if len(occurrences) > 1:
                        erros.append({"erro": f"formulário repetido no {rotulo}", "formulario": key,
                                      "linhas_excel": [n for n, _ in occurrences]})
            for key, occurrences in origem_chaves.items():
                if key not in manual_chaves:
                    erros.append({"erro": "O.S. sem classificação", "formulario": key,
                                  "linha_original": occurrences[0][0]})
            for key, occurrences in manual_chaves.items():
                if key not in origem_chaves:
                    erros.append({"erro": "O.S. sem correspondência no original", "formulario": key,
                                  "linha_manual": occurrences[0][0]})
                elif len(occurrences) == 1 and len(origem_chaves[key]) == 1:
                    num, row = occurrences[0]
                    old = origem_chaves[key][0][1]
                    for col in header_original:
                        if col not in header_manual:
                            continue
                        a = old[header_original.index(col)] if header_original.index(col) < len(old) else None
                        b = row[header_manual.index(col)] if header_manual.index(col) < len(row) else None
                        if a != b:
                            erros.append({"linha_excel": num, "formulario": key, "campo": col,
                                          "erro": "campo original modificado", "antes": str(a), "depois": str(b)})
        if len(base) != len(editadas):
            erros.append({"erro": "quantidade de linhas divergente", "original": len(base), "manual": len(editadas)})
    except Exception as exc:
        erros.append({"erro": "falha ao ler as planilhas", "detalhe": f"{type(exc).__name__}: {exc}"})
        base, editadas, setores = [], [], Counter()
    status = "APROVADO" if not erros else "REPROVADO"
    registro = {"etapa": "AB03", "run_id": run_id, "data_hora": datetime.now().astimezone().isoformat(),
                "status": status, "acao_manual": "coluna setor preenchida pelo responsável por classificação de cada O.S.; uma linha por formulário",
                "categorias": sorted(ACEITOS), "planilha_origem": original.relative_to(raiz).as_posix(),
                "sha256_origem": sha256(original), "planilha_manual": manual.relative_to(raiz).as_posix(),
                "sha256_manual": sha256(manual), "linhas_origem": len(base), "linhas_manual": len(editadas),
                "setores": dict(sorted(setores.items())), "divergencias": erros,
                "limite": "Valida estrutura, integridade da cópia e domínio dos setores; a escolha de setor para cada equipamento requer conferência humana com contexto operacional."}
    (docs / "conclusao_AB03.json").write_text(json.dumps(registro, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    md = ["# AB03 — classificação manual por setor", "", f"Execução: `{run_id}`",
          f"Status: **{status}**", "", "A coluna `setor` foi preenchida manualmente pelo responsável, preservando uma linha por O.S.",
          f"Origem: `{registro['planilha_origem']}` (SHA-256 `{registro['sha256_origem']}`).",
          f"Classificação: `{registro['planilha_manual']}` (SHA-256 `{registro['sha256_manual']}`).",
          "", f"Linhas de origem: **{len(base)}**. Linhas classificadas: **{len(editadas)}**.",
          f"Divergências: **{len(erros)}**.", "", "| Setor | O.S. |", "| --- | ---: |"]
    md.extend(f"| {cat} | {setores[cat]} |" for cat in sorted(ACEITOS))
    md += ["", registro["limite"]]
    if erros:
        md += ["", "## Divergências", ""] + [f"- `{json.dumps(e, ensure_ascii=False, default=str)}`" for e in erros[:100]]
        if len(erros) > 100:
            md.append(f"- Outras {len(erros)-100} no JSON.")
    (docs / "conclusao_AB03.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"[AB03] {status}: {len(editadas)} linhas; setores {dict(setores)}; {len(erros)} divergências. {docs}", flush=True)
    return 0 if status == "APROVADO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
