# Consultas de validação do banco

Consultas executadas no SQL Editor do Supabase em 21/09/2026, após a execução
do pipeline SIROS.

## 1. Total de registros em `voos`

```sql
SELECT COUNT(*) AS total_registros FROM voos;
```

Resultado: **2.123** registros.

## 2. Datas disponíveis

```sql
SELECT data_referencia, COUNT(*) AS total
FROM voos
GROUP BY data_referencia
ORDER BY data_referencia DESC;
```

| data_referencia | total |
| --- | ---: |
| 2026-09-21 | 2.123 |

## 3. Cinco registros mais recentes

```sql
SELECT id, data_referencia, icao_origem, icao_destino,
       icao_empresa, numero_voo, criado_em
FROM voos
ORDER BY criado_em DESC
LIMIT 5;
```

| id | data | origem | destino | empresa | voo | criado_em (UTC) |
| ---: | --- | --- | --- | --- | ---: | --- |
| 2021 | 2026-09-21 | SAEZ | SBGL | GLO | 7655 | 2026-09-21 17:36:15.225248+00 |
| 2022 | 2026-09-21 | SBGL | SABE | GLO | 7656 | 2026-09-21 17:36:15.225248+00 |
| 2019 | 2026-09-21 | SAEZ | SBGL | GLO | 7653 | 2026-09-21 17:36:15.225248+00 |
| 2020 | 2026-09-21 | SBGL | SAEZ | GLO | 7654 | 2026-09-21 17:36:15.225248+00 |
| 2023 | 2026-09-21 | SABE | SBBR | GLO | 7657 | 2026-09-21 17:36:15.225248+00 |

## 4. Log de execuções

```sql
SELECT concluido_em, voos_processados, lotes_enviados,
       erros, status, observacao
FROM execucoes
ORDER BY concluido_em DESC
LIMIT 5;
```

Foram retornadas três execuções registradas. As duas mais recentes concluíram
com **2.123 voos processados**, **5 lotes enviados** e **0 erros**.

| concluido_em (UTC) | voos | lotes | erros | status |
| --- | ---: | ---: | ---: | --- |
| 2026-09-21 23:48:00.208057+00 | 2.123 | 5 | 0 | concluido |
| 2026-09-21 18:44:52.657168+00 | 2.123 | 5 | 0 | concluido |
| 2026-09-21 17:36:15.787015+00 | 0 | 0 | 0 | concluido |

O último registro confirma que a deduplicação ocorreu antes do envio e que a
carga não apresentou falhas de lote.
