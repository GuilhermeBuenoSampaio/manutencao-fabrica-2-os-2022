"""Publicação independente da análise de manutenção; --simular não publica.
Não executa nem altera a origem, Silver, Gold ou pipeline da EDA.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from sincronizar_datalake_azure import cli, digest
from sincronizar_github import git, ESPERADO

PBIX = "powerbi/bi_analise_manutencao_2022/analise_manutencao_2022.pbix"
SCRIPTS = ("src/run_pipeline_manutencao_2022.py", "src/finalizar_manutencao_2022.py",
           "src/sincronizar_datalake_azure.py", "src/sincronizar_github.py")
DOCS = "docs/analise/manutencao_2022"
SQL = "sql/analise_manutencao_2022"
REQUIRED = ("README.md", PBIX, *SCRIPTS,
            f"{DOCS}/README.md", f"{DOCS}/relatorio_tecnico_manutencao_2022.md",
            f"{DOCS}/relatorio_executivo_manutencao_2022.md",
            f"{SQL}/01_base_e_diagnostico.sql", f"{SQL}/08_casos_documentados.sql",
            f"{SQL}/11_natureza_intervencoes_confirmadas.sql", f"{SQL}/12_kpis_natureza_manutencao.sql")


def inventario(root: Path) -> list[dict]:
    paths = set(REQUIRED)
    for folder, suffix in ((DOCS, '.md'), (SQL, '.sql')):
        base = root / folder
        if not base.is_dir():
            raise ValueError(f"Pasta ausente: {folder}")
        for item in base.rglob('*'):
            if item.is_symlink():
                raise ValueError(f"Link simbólico não permitido: {item}")
            if item.is_file() and item.suffix.lower() == suffix:
                paths.add(item.relative_to(root).as_posix())
    result = []
    for rel in sorted(paths):
        item = root / rel
        if any(p.is_symlink() for p in [item, *item.parents] if p != root.parent):
            raise ValueError(f"Caminho com link simbólico: {rel}")
        if not item.is_file() or item.stat().st_size == 0:
            raise ValueError(f"Arquivo ausente ou vazio: {rel}")
        if item.stat().st_size >= 100 * 1024 * 1024:
            raise ValueError(f"Arquivo excede limite GitHub sem LFS: {rel}")
        result.append({'path': rel, 'bytes': item.stat().st_size, 'sha256': digest(item)})
    return result


def verificar_git(root: Path) -> None:
    remote = git(root, 'remote', 'get-url', 'origin')
    # Aceita somente as formas conhecidas do repositório, sem substring arbitrária.
    if remote not in (f'https://github.com/{ESPERADO}.git', f'https://github.com/{ESPERADO}',
                      f'git@github.com:{ESPERADO}.git'):
        raise ValueError(f"Remote inesperado: {remote}")
    if git(root, 'branch', '--show-current') != 'main':
        raise ValueError('Execute na branch main')
    if git(root, 'diff', '--cached', '--name-only'):
        raise ValueError('Há arquivos no índice. Revise-os antes desta pipeline; nada foi adicionado.')


def salvar(path: Path, doc: dict) -> None:
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(doc, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    temp.replace(path)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('projeto', nargs='?', type=Path, default=Path('.'))
    p.add_argument('--account-name', default='stcustomeranalyticsgb01')
    p.add_argument('--container', default='manutencao-fabrica-2-os-2022')
    p.add_argument('--simular', action='store_true')
    args = p.parse_args()
    root = args.projeto.resolve()
    run = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    folder = root/'docs/execucoes/analise_manutencao_2022'/run
    folder.mkdir(parents=True, exist_ok=False)
    path = folder/'conclusao_pipeline_manutencao_2022.json'
    report = {'analise': 'analise_manutencao_2022', 'run_id': run, 'status': 'EM_ANDAMENTO',
              'inicio': datetime.now().astimezone().isoformat(), 'simulacao': args.simular,
              'account_name': args.account_name, 'container': args.container,
              'arquivos': [], 'commit': None, 'erro': None,
              'limite_validacao': 'Confere arquivos, hashes, Azure e commit; não executa SQL nem recalcula DAX.'}
    salvar(path, report)
    try:
        files = inventario(root)
        verificar_git(root)
        report['arquivos'] = files
        prefix = f'analises/analise_manutencao_2022/{run}'
        report['prefixo_azure'] = prefix
        salvar(path, report)
        if args.simular:
            report['status'] = 'SIMULADO'
            for f in files:
                print(f"[SIMULAÇÃO] {f['path']}")
        else:
            common = ('--account-name', args.account_name, '--container-name', args.container,
                      '--auth-mode', 'login')
            for n, f in enumerate(files, 1):
                local = root/f['path']
                if digest(local) != f['sha256']:
                    raise ValueError(f"Arquivo alterado durante execução: {f['path']}")
                f['blob'] = prefix+'/'+f['path']
                cli('storage', 'blob', 'upload', *common, '--name', f['blob'],
                    '--file', str(local), '--overwrite', 'false')
                with tempfile.TemporaryDirectory(prefix='manutencao2022_') as temp:
                    copy = Path(temp)/'verificacao'
                    cli('storage', 'blob', 'download', *common, '--name', f['blob'],
                        '--file', str(copy), '--overwrite', 'false')
                    f['sha256_download'] = digest(copy)
                if f['sha256_download'] != f['sha256']:
                    raise ValueError(f"Divergência Azure: {f['path']}")
                salvar(path, report)
                print(f"[AZ_M02] {n}/{len(files)} VERIFICADO: {f['path']}", flush=True)
            # Revalida índice e bytes antes de preparar o commit.
            verificar_git(root)
            if inventario(root) != [{k:v for k,v in f.items() if k in ('path','bytes','sha256')} for f in files]:
                raise ValueError('Inventário mudou durante o envio; execute novamente')
            normal = [f['path'] for f in files if f['path'] != PBIX]
            git(root, 'add', '--', *normal)
            git(root, 'add', '-f', '--', PBIX)
            staged = git(root, 'diff', '--cached', '--name-only').splitlines()
            if any(x not in {f['path'] for f in files} for x in staged):
                raise ValueError('Índice fora do escopo; não foi realizado commit')
            if staged:
                git(root, 'commit', '-m', 'Documenta e publica aprofundamento de manutencao 2022')
            report['commit'] = git(root, 'rev-parse', 'HEAD')
            git(root, 'push', 'origin', 'main')
            report['github_publicado'] = True
            salvar(path, report)
            code = subprocess.run([sys.executable, '-u', str(root/'src/finalizar_manutencao_2022.py'),
                                   str(root), '--pipeline-run-id', run], check=False).returncode
            if code:
                raise ValueError('Finalizador reprovado; consulte a evidência desta execução')
            report['status'] = 'APROVADO'
    except (OSError, ValueError, RuntimeError) as exc:
        report['status'] = 'REPROVADO'
        report['erro'] = str(exc)
    report['fim'] = datetime.now().astimezone().isoformat()
    salvar(path, report)
    (folder/'conclusao_pipeline_manutencao_2022.md').write_text(
        f"# Pipeline da análise de manutenção\n\nStatus: **{report['status']}**.\n\n"
        f"Arquivos: {len(report['arquivos'])}. Commit: `{report['commit']}`.\n\n"
        f"Limite: {report['limite_validacao']}\n\nErro: {report['erro'] or 'nenhum'}.\n", encoding='utf-8')
    print(f"[M02] {report['status']}; evidência: {folder}")
    if report['erro']:
        print(report['erro'])
    return 0 if report['status'] in ('APROVADO','SIMULADO') else 1

if __name__ == '__main__':
    raise SystemExit(main())
