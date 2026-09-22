# Painel ANAC — SIROS e histórico VRA

Painel estático publicado no GitHub Pages, alimentado por dois pipelines Python
que gravam dados oficiais da ANAC no Supabase.

## Componentes

- `scripts/fetch_flights.py`: importa os voos programados do dia pela API SIROS,
  remove duplicados e registra métricas da execução.
- `scripts/fetch_historico_anac.py`: importa o VRA (Voo Regular Ativo) de um
  mês histórico, filtrando os aeroportos definidos em `AIRPORTS`.
- `.github/workflows/update-flights.yml`: executa a carga SIROS quatro vezes ao dia.
- `.github/workflows/importar-historico.yml`: executa a carga VRA mensalmente ou
  sob demanda para um período `YYYY-MM`.
- `sql/setup.sql`: schema completo para instalações novas.
- `sql/002_historico_vra.sql`: migração segura para o projeto Supabase já criado.
- `docs/CONSULTAS_BANCO.md`: consultas realizadas no Supabase e resultados de validação.

## Configuração no GitHub

Crie estes Secrets em **Settings → Secrets and variables → Actions**:

| Nome | Conteúdo |
| --- | --- |
| `SUPABASE_URL` | URL do projeto Supabase |
| `SUPABASE_SERVICE_KEY` | Chave secreta/service-role, usada somente nos workflows |

Crie a variável `AIRPORTS` com ICAOs separados por vírgula, por exemplo:

```text
SBCA,SBGR,SBSP,SBCT,SBGL,SBBR,SBFL,SBPA
```

Nunca coloque a chave secreta no `index.html`, em commits, logs ou capturas.
O painel público usa somente a chave publishable para leitura.

## Preparação do Supabase

Em um projeto novo, execute `sql/setup.sql` no SQL Editor. Para o projeto já
existente, execute uma vez `sql/002_historico_vra.sql` antes de disparar a carga
histórica. A migração cria `historico_vra`, seus índices, RLS, uma política
pública exclusiva para SELECT e escrita reservada ao `service_role`.

## Testes locais

```bash
pip install requests supabase
python -m py_compile scripts/fetch_flights.py scripts/fetch_historico_anac.py
python -m unittest discover -s tests -v
```

Os testes não usam credenciais nem escrevem no Supabase. A validação completa é
feita pelo GitHub Actions após a migração ser aplicada.

## Execução manual

1. Em **Actions**, execute **Pipeline SIROS → Supabase**.
2. Para histórico, execute **Importar Histórico ANAC/VRA**, informando
   opcionalmente `ano_mes` como `YYYY-MM`.
3. Confira `voos`, `historico_vra` e `execucoes` no Supabase.

## Evidências

Os resultados e capturas dos testes ficam em [`evidencias-testes/`](evidencias-testes/).
