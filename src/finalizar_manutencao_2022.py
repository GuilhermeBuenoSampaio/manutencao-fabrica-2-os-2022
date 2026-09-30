"""Última etapa da pipeline de manutenção; exige seu run_id de publicação.
Não valida conexão SQL, métricas internas do PBIX ou natureza operacional das O.S.
"""
import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from sincronizar_datalake_azure import cli, digest
from sincronizar_github import git
from run_pipeline_manutencao_2022 import inventario, salvar


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('projeto', nargs='?', type=Path, default=Path('.'))
    p.add_argument('--pipeline-run-id', required=True)
    args = p.parse_args()
    if not args.pipeline_run_id or any(c not in '0123456789_' for c in args.pipeline_run_id):
        p.error('run_id inválido')
    root = args.projeto.resolve()
    folder = root/'docs/execucoes/analise_manutencao_2022'/args.pipeline_run_id
    result = {'etapa':'FINAL_M02', 'status':'REPROVADO', 'verificacoes':[], 'erro':None,
              'data_hora':datetime.now().astimezone().isoformat(),
              'limite':'Publicação de artefatos; conferências de SQL/DAX registradas como manuais.'}
    try:
        report = json.loads((folder/'conclusao_pipeline_manutencao_2022.json').read_text(encoding='utf-8'))
        if report.get('simulacao') or not report.get('github_publicado') or report.get('analise') != 'analise_manutencao_2022':
            raise ValueError('Publicação desta pipeline ainda não concluída')
        files = inventario(root)
        expected = [{k:v for k,v in f.items() if k in ('path','bytes','sha256')} for f in report['arquivos']]
        if files != expected:
            raise ValueError('Arquivos locais diferentes do inventário publicado')
        commit = report['commit']
        if git(root,'rev-parse','HEAD') != commit:
            raise ValueError('HEAD mudou após publicação')
        remote = git(root,'ls-remote','origin','refs/heads/main').split()[0]
        if remote != commit:
            raise ValueError('Commit remoto diferente do commit documentado')
        common = ('--account-name',report['account_name'],'--container-name',report['container'],'--auth-mode','login')
        import tempfile
        for f in report['arquivos']:
            # Arquivos texto podem passar pela normalização CRLF/LF do Git.
            # Compara os bytes do índice contra o objeto, e Azure contra os bytes locais.
            indexed = git(root,'rev-parse',f"{commit}:{f['path']}")
            local_blob = git(root,'hash-object','--path',f['path'],'--',f['path'])
            if indexed != local_blob:
                raise ValueError(f"Conteúdo Git divergente: {f['path']}")
            with tempfile.TemporaryDirectory(prefix='finalm02_') as temp:
                downloaded=Path(temp)/'arquivo'
                cli('storage','blob','download',*common,'--name',f['blob'],'--file',str(downloaded),'--overwrite','false')
                if digest(downloaded) != f['sha256']:
                    raise ValueError(f"Conteúdo Azure divergente: {f['path']}")
            result['verificacoes'].append({'arquivo':f['path'],'git':'VERIFICADO','azure':'VERIFICADO'})
        result['status']='APROVADO'
    except (OSError,ValueError,RuntimeError,KeyError,subprocess.CalledProcessError) as exc:
        result['erro']=str(exc)
    folder.mkdir(parents=True,exist_ok=True)
    salvar(folder/'conclusao_FINAL_M02.json',result)
    (folder/'conclusao_FINAL_M02.md').write_text(
        f"# Finalização da análise de manutenção\n\nStatus: **{result['status']}**.\n\n"
        f"{result['limite']}\n\nErro: {result['erro'] or 'nenhum'}.\n",encoding='utf-8')
    print(f"[FINAL_M02] {result['status']}; {result['erro'] or folder}")
    return 0 if result['status']=='APROVADO' else 1

if __name__=='__main__':
    raise SystemExit(main())
