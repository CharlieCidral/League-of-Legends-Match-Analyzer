import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://br1.api.riotgames.com"

def gerar_elos(api_key):
    with open("dados_da_partida.json", "r", encoding="utf-8") as f:
        partida = json.load(f)

    headers = {"X-Riot-Token": api_key}

    def buscar_elo(puuid):
        url = f"{BASE_URL}/lol/league/v4/entries/by-puuid/{puuid}"
        resp = requests.get(url, headers=headers)
        return resp.json() if resp.status_code == 200 else []

    participantes = [
        (p.get("puuid"), p.get("riotId"))
        for p in partida["participants"]
        if p.get("puuid")
    ]

    dados_elos = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        futuros = {
            executor.submit(buscar_elo, puuid): (puuid, riot_id)
            for puuid, riot_id in participantes
        }
        for futuro in as_completed(futuros):
            puuid, riot_id = futuros[futuro]
            elo_info = futuro.result()
            if not elo_info:
                elo_info = [{"tier": "Unranked", "rank": ""}]
            dados_elos[riot_id] = {
                "puuid": puuid,
                "elo": elo_info
            }

    with open("elos_jogadores.json", "w", encoding="utf-8") as f:
        json.dump(dados_elos, f, ensure_ascii=False, indent=4)