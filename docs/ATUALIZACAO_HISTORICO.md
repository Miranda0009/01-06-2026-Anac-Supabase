# Atualização: dados históricos ANAC/VRA

## O que foi adicionado

1. Importador `scripts/fetch_historico_anac.py` para o arquivo mensal VRA.
2. Workflow `importar-historico.yml`, com agenda mensal e disparo manual por
   `ano_mes` no formato `YYYY-MM`.
3. Tabela `historico_vra`, índices de origem/destino e período, RLS e política
   pública de leitura.
4. Métricas detalhadas no log `execucoes`: voos processados, lotes enviados e
   erros.

## Ajuste do pipeline diário

`fetch_flights.py` continua removendo duplicados antes do upsert. O script agora
registra `concluido`, `erro_parcial` ou `erro_critico`; qualquer lote com erro
encerra o workflow com código diferente de zero, tornando a falha visível no
GitHub Actions.

## Fonte VRA atualizada

O importador histórico prioriza o diretório oficial da ANAC para 2026, usando a
estrutura `Voo Regular Ativo (VRA)/AAAA/MM - Mês/VRA_AAAAM.csv`. A origem SIROS
permanece como alternativa para períodos que ainda usem o formato anterior.

## Segurança

- A chave de escrita permanece apenas em GitHub Secrets.
- As tabelas expostas têm RLS habilitado.
- O navegador tem somente `SELECT` como `anon`; inserção e atualização usam
  `service_role` dentro dos workflows.

## Pré-requisito de implantação

Execute `sql/002_historico_vra.sql` no SQL Editor do Supabase uma única vez.
Depois, execute manualmente o workflow histórico com um mês que já possua VRA.
