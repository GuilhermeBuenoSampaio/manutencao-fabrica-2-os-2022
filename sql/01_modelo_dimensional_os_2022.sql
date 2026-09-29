/*
Modelo proposto para a Silver AB04 20260928_135101_841223.
Grão de dw.fato_os: exatamente uma linha por formulario_os.
Este script cria apenas estruturas: não apaga tabelas e não carrega dados.
Execute no SSMS conectado à instância em que o banco já foi criado.
*/
USE [manutencao-fabrica-2-os-2022];
GO

IF SCHEMA_ID(N'dw') IS NULL EXEC(N'CREATE SCHEMA dw');
GO

IF OBJECT_ID(N'dw.dim_tempo', N'U') IS NULL
CREATE TABLE dw.dim_tempo (
    mes_chave INT NOT NULL PRIMARY KEY, -- 202201 ... 202212
    ano SMALLINT NOT NULL,
    mes_numero TINYINT NOT NULL,
    mes_nome NVARCHAR(20) NOT NULL,
    CONSTRAINT UQ_dim_tempo_ano_mes UNIQUE (ano, mes_numero),
    CONSTRAINT CK_dim_tempo_mes_numero CHECK (mes_numero BETWEEN 1 AND 12),
    CONSTRAINT CK_dim_tempo_chave CHECK (mes_chave = ano * 100 + mes_numero)
);
GO

IF OBJECT_ID(N'dw.dim_setor', N'U') IS NULL
CREATE TABLE dw.dim_setor (
    setor_chave INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    setor_nome NVARCHAR(80) COLLATE Latin1_General_100_BIN2 NOT NULL,
    CONSTRAINT UQ_dim_setor_nome UNIQUE (setor_nome)
);
GO

IF OBJECT_ID(N'dw.dim_tipo', N'U') IS NULL
CREATE TABLE dw.dim_tipo (
    tipo_chave INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    tipo_nome NVARCHAR(80) COLLATE Latin1_General_100_BIN2 NOT NULL,
    CONSTRAINT UQ_dim_tipo_nome UNIQUE (tipo_nome)
);
GO

IF OBJECT_ID(N'dw.dim_prestador_solicitado', N'U') IS NULL
CREATE TABLE dw.dim_prestador_solicitado (
    prestador_chave INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    prestador_nome_original NVARCHAR(200) COLLATE Latin1_General_100_BIN2 NOT NULL,
    CONSTRAINT UQ_dim_prestador_nome UNIQUE (prestador_nome_original)
);
GO

IF OBJECT_ID(N'dw.dim_area_equipamento', N'U') IS NULL
CREATE TABLE dw.dim_area_equipamento (
    area_equipamento_chave INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    rotulo_original NVARCHAR(200) COLLATE Latin1_General_100_BIN2 NOT NULL,
    CONSTRAINT UQ_dim_area_equipamento_rotulo UNIQUE (rotulo_original)
);
GO

IF OBJECT_ID(N'dw.fato_os', N'U') IS NULL
CREATE TABLE dw.fato_os (
    formulario_os NVARCHAR(30) COLLATE Latin1_General_100_BIN2 NOT NULL PRIMARY KEY,
    mes_chave INT NOT NULL REFERENCES dw.dim_tempo(mes_chave),
    setor_chave INT NOT NULL REFERENCES dw.dim_setor(setor_chave),
    tipo_chave INT NOT NULL REFERENCES dw.dim_tipo(tipo_chave),
    prestador_chave INT NOT NULL REFERENCES dw.dim_prestador_solicitado(prestador_chave),
    area_equipamento_chave INT NOT NULL REFERENCES dw.dim_area_equipamento(area_equipamento_chave),
    local_original NVARCHAR(80) NOT NULL,
    numero_controle NVARCHAR(80) NULL,
    descricao_defeito NVARCHAR(1000) NULL,
    descricao_servico_realizado NVARCHAR(1000) NULL,
    pecas_equipamentos_necessarios NVARCHAR(1000) NULL,
    qtd DECIMAL(18,3) NULL,
    valor_unitario_brl DECIMAL(18,2) NULL,
    valor_total_brl DECIMAL(18,2) NOT NULL,
    CONSTRAINT CK_fato_os_valor_total CHECK (valor_total_brl >= 0),
    CONSTRAINT CK_fato_os_qtd CHECK (qtd IS NULL OR qtd >= 0),
    CONSTRAINT CK_fato_os_par_qtd_valor CHECK
        ((qtd IS NULL AND valor_unitario_brl IS NULL)
         OR (qtd IS NOT NULL AND valor_unitario_brl IS NOT NULL))
);
GO

/*
Próximo script: carga de uma única execução Silver com verificação de SHA-256,
contagem e soma, mantendo as grafias originais. Não agrupar rótulos semelhantes
sem uma tabela de equivalência aprovada. A chave numero_controle se repete.
*/
