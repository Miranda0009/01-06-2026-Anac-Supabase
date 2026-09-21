# Registro de testes

Data: 21/09/2026

## Testes locais (sem rede e sem credenciais)

```text
python -m py_compile scripts/fetch_flights.py scripts/fetch_historico_anac.py
python -m unittest discover -s tests -v

Ran 6 tests
OK
```

Cobertura verificada:

- leitura de cabeçalhos VRA com acentuação;
- conversão de data e cálculo de atraso;
- deduplicação pela chave do upsert;
- rejeição de período inválido;
- RLS e privilégios mínimos na migração;
- workflow chamando o importador histórico.

## Testes integrados no GitHub Actions

| Pipeline | Resultado | Evidência |
| --- | --- | --- |
| Importar Histórico ANAC/VRA | Concluído com êxito | [run 35639852321](https://github.com/Miranda0009/01-06-2026-Anac-Supabase/actions/runs/35639852321) |
| Pipeline SIROS → Supabase | Concluído com êxito | [run 35640338602](https://github.com/Miranda0009/01-06-2026-Anac-Supabase/actions/runs/35640338602) |

## Capturas das execuções

| Arquivo | Conteúdo |
| --- | --- |
| [importar-historico-sucesso.png](importar-historico-sucesso.png) | Execução `Importar Histórico ANAC/VRA #4` com status **Success**. |
| [siros-sucesso.png](siros-sucesso.png) | Execução `Pipeline SIROS → Supabase #227` com status **Success**. |

### Resultado VRA (2025-08)

- CSV oficial lido: 84.584 linhas brutas.
- Registros válidos enviados/processados: **61.412** em 123 lotes.
- Contagem confirmada no Supabase: **61.412** registros em `historico_vra`.

### Resultado SIROS

- API retornou 3.056 voos.
- 2.123 voos dos aeroportos configurados foram processados em 5 lotes.
- 1 duplicado foi removido antes do upsert.

As telas de cada execução podem ser abertas diretamente pelos links dos runs,
e também foram anexadas neste diretório como PNG. Nenhuma chave ou segredo
aparece nas evidências.
