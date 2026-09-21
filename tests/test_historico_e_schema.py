"""Testes locais: não acessam a ANAC nem usam credenciais do Supabase."""

import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# O módulo só precisa da assinatura create_client nos testes de funções puras.
sys.modules.setdefault("supabase", types.SimpleNamespace(create_client=lambda *_: None))
sys.modules.setdefault("requests", types.SimpleNamespace(RequestException=Exception))
spec = importlib.util.spec_from_file_location(
    "fetch_historico_anac", ROOT / "scripts" / "fetch_historico_anac.py"
)
historico = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(historico)


class HistoricoAnacTests(unittest.TestCase):
    def test_processa_linha_com_cabecalhos_acentuados(self):
        linhas = [{
            "EMPRESA (SIGLA)": "GLO",
            "NÚMERO VOO": "01234",
            "ORIGEM": "SBCA",
            "DESTINO": "SBGR",
            "DT_REFERENCIA": "02/05/2026",
            "PARTIDA PREVISTA": "02/05/2026 10:00",
            "PARTIDA REAL": "02/05/2026 10:17",
            "CHEGADA PREVISTA": "02/05/2026 11:00",
            "CHEGADA REAL": "02/05/2026 11:08",
            "SITUAÇÃO DE VOO": "REALIZADO",
            "MOTIVO": "",
        }]
        registros = historico.processar(linhas, ["SBCA"], "2026-05")
        self.assertEqual(1, len(registros))
        self.assertEqual("1234", registros[0]["nr_voo"])
        self.assertEqual("2026-05-02", registros[0]["dt_referencia"])
        self.assertEqual(17, registros[0]["atraso_partida"])
        self.assertEqual(8, registros[0]["atraso_chegada"])

    def test_deduplicacao_usa_chave_do_upsert(self):
        base = {
            "ano_mes": "2026-05", "icao_empresa": "GLO", "nr_voo": "1234",
            "icao_origem": "SBCA", "icao_destino": "SBGR", "dt_referencia": "2026-05-02",
        }
        unicos, removidos = historico.deduplicar([base, {**base, "situacao": "realizado"}])
        self.assertEqual(1, len(unicos))
        self.assertEqual(1, removidos)

    def test_periodo_invalido_e_rejeitado(self):
        with self.assertRaises(ValueError):
            historico.periodo_requisitado("maio-2026")


class SchemaTests(unittest.TestCase):
    def test_migracao_tem_rls_e_privilegios_minimos(self):
        sql = (ROOT / "sql" / "002_historico_vra.sql").read_text(encoding="utf-8").lower()
        self.assertIn("enable row level security", sql)
        self.assertIn("grant select on table public.historico_vra to anon", sql)
        self.assertIn("grant all on table public.historico_vra to service_role", sql)
        self.assertNotIn("grant all on table public.historico_vra to anon", sql)

    def test_workflow_historico_chama_importador(self):
        workflow = (ROOT / ".github" / "workflows" / "importar-historico.yml").read_text(encoding="utf-8")
        self.assertIn("python scripts/fetch_historico_anac.py", workflow)
        self.assertIn("SUPABASE_SERVICE_KEY", workflow)


if __name__ == "__main__":
    unittest.main()
