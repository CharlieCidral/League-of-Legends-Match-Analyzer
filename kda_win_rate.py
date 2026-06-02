import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://americas.api.riotgames.com"

def gerar_estatisticas(api_key, count=10):
    with open("dados_da_partida.json", "r", encoding="utf-8") as f:
        partida = json.load(f)

    headers = {"X-Riot-Token": api_key}

    def buscar_detalhes(match_id):
        url = f"{BASE_URL}/lol/match/v5/matches/{match_id}"
        resp = requests.get(url, headers=headers)
        return resp.json() if resp.status_code == 200 else None

    def buscar_e_calcular(puuid):
        # Buscar IDs das partidas
        url = f"{BASE_URL}/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}&queue=450"
        resp = requests.get(url, headers=headers)
        partidas_ids = resp.json() if resp.status_code == 200 else []

        if not partidas_ids:
            # fallback sem filtro de fila
            url = f"{BASE_URL}/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}"
            resp = requests.get(url, headers=headers)
            partidas_ids = resp.json() if resp.status_code == 200 else []

        if not partidas_ids:
            return {}

        # Buscar detalhes de todas as partidas em paralelo
        total_kills = total_deaths = total_assists = total_wins = total_matches = 0

        with ThreadPoolExecutor(max_workers=10) as executor:
            futuros = {executor.submit(buscar_detalhes, mid): mid for mid in partidas_ids}
            for futuro in as_completed(futuros):
                detalhes = futuro.result()
                if not detalhes:
                    continue
                for p in detalhes["info"]["participants"]:
                    if p["puuid"] == puuid:
                        total_kills += p["kills"]
                        total_deaths += p["deaths"]
                        total_assists += p["assists"]
                        if p["win"]:
                            total_wins += 1
                        total_matches += 1
                        break

        if total_matches == 0:
            return {}

        return {
            "kills_avg": round(total_kills / total_matches, 2),
            "deaths_avg": round(total_deaths / total_matches, 2),
            "assists_avg": round(total_assists / total_matches, 2),
            "kda": round((total_kills + total_assists) / max(total_deaths, 1) / total_matches, 2),
            "win_rate": round((total_wins / total_matches) * 100, 2),
            "partidas_analisadas": total_matches
        }

    participantes = [
        (p.get("puuid"), p.get("riotId"))
        for p in partida["participants"]
        if p.get("puuid")
    ]

    estatisticas_jogadores = {}

    # Buscar partidas de todos os jogadores em paralelo
    with ThreadPoolExecutor(max_workers=5) as executor:
        futuros = {
            executor.submit(buscar_e_calcular, puuid): (puuid, riot_id)
            for puuid, riot_id in participantes
        }
        for futuro in as_completed(futuros):
            puuid, riot_id = futuros[futuro]
            estatisticas_jogadores[riot_id] = {
                "puuid": puuid,
                "estatisticas": futuro.result()
            }

    with open("estatisticas_jogadores.json", "w", encoding="utf-8") as f:
        json.dump(estatisticas_jogadores, f, ensure_ascii=False, indent=4)