"""Importa dados históricos VRA/ANAC para a tabela historico_vra.

O período vem de ANO_MES (AAAA-MM) ou, na ausência dela, do mês anterior.
As credenciais são recebidas exclusivamente por variáveis de ambiente.
"""

import csv
import io
import os
import sys
import unicodedata
from datetime import date, datetime, timedelta, timezone

import requests
from supabase import create_client

LOTE = 500

COLUNAS = {
    "empresa": ("SIGLA ICAO EMPRESA AÉREA", "SIGLA ICAO EMPRESA AEREA", "EMPRESA (SIGLA)", "EMPRESA SIGLA", "sg_empresa_icao"),
    "voo": ("NÚMERO VOO", "NUMERO VOO", "nr_voo"),
    "origem": ("SIGLA ICAO AEROPORTO ORIGEM", "ORIGEM", "AEROPORTO ORIGEM", "sg_icao_origem"),
    "destino": ("SIGLA ICAO AEROPORTO DESTINO", "DESTINO", "AEROPORTO DESTINO", "sg_icao_destino"),
    "data": ("REFERÊNCIA", "REFERENCIA", "DT_REFERENCIA", "DT REFERENCIA", "data_referencia"),
    "partida_prevista": ("PARTIDA PREVISTA", "dt_partida_prevista"),
    "partida_real": ("PARTIDA REAL", "dt_partida_real"),
    "chegada_prevista": ("CHEGADA PREVISTA", "dt_chegada_prevista"),
    "chegada_real": ("CHEGADA REAL", "dt_chegada_real"),
    "situacao": ("SITUAÇÃO DE VOO", "SITUACAO VOO", "situacao"),
    "motivo": ("JUSTIFICATIVA", "MOTIVO", "MOTIVO ALTERACAO", "motivo_alteracao"),
}


def chave_coluna(valor: str) -> str:
    """Normaliza cabeçalhos com acentos para suportar versões do CSV VRA."""
    sem_acentos = unicodedata.normalize("NFKD", valor or "").encode("ascii", "ignore").decode()
    return " ".join(sem_acentos.upper().replace("_", " ").split())


def valor_coluna(linha: dict, campo: str) -> str:
    normalizada = {
        chave_coluna(nome): str(valor or "").strip()
        for nome, valor in linha.items()
        if isinstance(nome, str) and not isinstance(valor, (list, dict))
    }
    for alias in COLUNAS[campo]:
        valor = normalizada.get(chave_coluna(alias))
        if valor is not None:
            return valor
    return ""


def parse_data(valor: str) -> str | None:
    for formato in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime((valor or "").strip(), formato).date().isoformat()
        except ValueError:
            pass
    return None


def parse_datahora(valor: str) -> str | None:
    for formato in (
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime((valor or "").strip(), formato).replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            pass
    return None


def atraso_minutos(previsto: str, realizado: str) -> int | None:
    for formato in ("%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            inicio = datetime.strptime(previsto.strip(), formato)
            fim = datetime.strptime(realizado.strip(), formato)
            return int((fim - inicio).total_seconds() // 60)
        except (TypeError, ValueError):
            pass
    return None


def periodo_requisitado(valor: str | None) -> str:
    if valor:
        try:
            return datetime.strptime(valor.strip(), "%Y-%m").strftime("%Y-%m")
        except ValueError as erro:
            raise ValueError("ANO_MES deve usar o formato AAAA-MM.") from erro
    primeiro_dia = date.today().replace(day=1)
    return (primeiro_dia - timedelta(days=1)).strftime("%Y-%m")


def urls_vra(ano_mes: str) -> list[str]:
    ano, mes = ano_mes.split("-")
    arquivo = f"{ano}{mes}.csv"
    return [
        f"https://siros.anac.gov.br/siros/registros/diversos/vra/{ano}/VRA_{ano}_{mes}.csv",
        "https://sistemas.anac.gov.br/dadosabertos/"
        f"Voos%20e%20opera%C3%A7%C3%B5es/VRA/{ano}/{arquivo}",
    ]


def baixar_vra(ano_mes: str) -> list[dict]:
    for url in urls_vra(ano_mes):
        print(f"GET {url}")
        try:
            resposta = requests.get(url, timeout=120)
            if resposta.status_code == 404:
                print("  Arquivo não encontrado nessa origem; tentando a próxima.")
                continue
            resposta.raise_for_status()
            try:
                texto = resposta.content.decode("utf-8-sig")
            except UnicodeDecodeError:
                # Alguns arquivos antigos do VRA foram publicados em Latin-1.
                texto = resposta.content.decode("latin-1", errors="replace")
            cabecalho = texto.splitlines()[0] if texto.splitlines() else ""
            if ";" not in cabecalho or "<html" in texto[:500].lower():
                print("  Resposta recebida não é um CSV VRA válido; tentando a próxima origem.")
                continue
            linhas = list(csv.DictReader(io.StringIO(texto), delimiter=";"))
            print(f"  VRA carregado: {len(linhas)} linhas brutas")
            return linhas
        except requests.RequestException as erro:
            print(f"  [ERRO] {erro}")
    return []


def deduplicar(registros: list[dict]) -> tuple[list[dict], int]:
    campos = ("ano_mes", "icao_empresa", "nr_voo", "icao_origem", "icao_destino", "dt_referencia")
    vistos: set[tuple] = set()
    unicos: list[dict] = []
    for registro in registros:
        chave = tuple(registro[campo] for campo in campos)
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(registro)
    return unicos, len(registros) - len(unicos)


def processar(linhas: list[dict], aeroportos: list[str], ano_mes: str) -> list[dict]:
    registros: list[dict] = []
    for linha in linhas:
        origem = valor_coluna(linha, "origem").upper()
        destino = valor_coluna(linha, "destino").upper()
        if origem not in aeroportos and destino not in aeroportos:
            continue
        empresa = valor_coluna(linha, "empresa").upper()
        voo = valor_coluna(linha, "voo").lstrip("0") or "0"
        partida_prevista = valor_coluna(linha, "partida_prevista")
        partida_real = valor_coluna(linha, "partida_real")
        chegada_prevista = valor_coluna(linha, "chegada_prevista")
        chegada_real = valor_coluna(linha, "chegada_real")
        data_referencia = parse_data(valor_coluna(linha, "data"))
        if not data_referencia:
            data_referencia = next(
                (valor[:10] for valor in (parse_datahora(partida_prevista), parse_datahora(partida_real)) if valor),
                None,
            )
        if not all((empresa, voo, origem, destino, data_referencia)):
            continue
        situacao = valor_coluna(linha, "situacao").lower() or None
        registros.append({
            "ano_mes": ano_mes,
            "icao_empresa": empresa,
            "nr_voo": voo,
            "icao_origem": origem,
            "icao_destino": destino,
            "dt_referencia": data_referencia,
            "partida_real": parse_datahora(partida_real),
            "chegada_real": parse_datahora(chegada_real),
            "atraso_partida": atraso_minutos(partida_prevista, partida_real),
            "atraso_chegada": atraso_minutos(chegada_prevista, chegada_real),
            "situacao": situacao,
            "motivo_alteracao": valor_coluna(linha, "motivo") or None,
        })
    return registros


def main() -> int:
    url = os.environ.get("SUPABASE_URL", "").strip()
    chave = os.environ.get("SUPABASE_SERVICE_KEY", "").strip()
    if not url or not chave:
        print("[ERRO CRÍTICO] SUPABASE_URL e SUPABASE_SERVICE_KEY são obrigatórios.")
        return 1
    try:
        ano_mes = periodo_requisitado(os.environ.get("ANO_MES"))
    except ValueError as erro:
        print(f"[ERRO] {erro}")
        return 1
    aeroportos = [item.strip().upper() for item in os.environ.get("AIRPORTS", "SBCA").split(",") if item.strip()]
    print(f"Período histórico: {ano_mes}")
    print(f"Aeroportos filtrados: {', '.join(aeroportos)}")
    linhas = baixar_vra(ano_mes)
    if not linhas:
        print("[AVISO] VRA indisponível para o período; nenhuma alteração foi feita.")
        return 0
    registros, duplicados = deduplicar(processar(linhas, aeroportos, ano_mes))
    print(f"Registros válidos: {len(registros)}; duplicados removidos: {duplicados}")
    banco = create_client(url, chave)
    erros = 0
    enviados = 0
    for inicio in range(0, len(registros), LOTE):
        lote = registros[inicio : inicio + LOTE]
        try:
            banco.table("historico_vra").upsert(
                lote,
                on_conflict="ano_mes,icao_empresa,nr_voo,icao_origem,icao_destino,dt_referencia",
            ).execute()
            enviados += len(lote)
            print(f"  Lote {inicio // LOTE + 1}: {len(lote)} registros enviados/processados")
        except Exception as erro:  # A execução deve falhar se a carga ficar parcial.
            erros += 1
            print(f"  [ERRO] Lote {inicio // LOTE + 1}: {erro}")
    print(f"Concluído — {enviados} registros históricos enviados/processados.")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
