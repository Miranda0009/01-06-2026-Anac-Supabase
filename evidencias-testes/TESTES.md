# Registro de testes

Data: 21/09/2026

## Testes locais (sem rede e sem credenciais)

```text
python -m py_compile scripts/fetch_flights.py scripts/fetch_historico_anac.py
python -m unittest discover -s tests -v

Ran 5 tests
OK
```

Cobertura verificada:

- leitura de cabeçalhos VRA com acentuação;
- conversão de data e cálculo de atraso;
- deduplicação pela chave do upsert;
- rejeição de período inválido;
- RLS e privilégios mínimos na migração;
- workflow chamando o importador histórico.

## Teste integrado

Após a migração `sql/002_historico_vra.sql`, o workflow **Importar Histórico
ANAC/VRA** será executado manualmente pelo GitHub Actions. A captura do run
concluído será incluída neste diretório como evidência do teste de ponta a ponta.
