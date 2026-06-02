import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://br1.api.riotgames.com"

def gerar_maestria(api_key):
    with open("dados_da_partida.json", "r", encoding="utf-8") as f:
        partida = json.load(f)

    headers = {"X-Riot-Token": api_key}

    def buscar_maestria(puuid):
        url = f"{BASE_URL}/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/top?count=10"
        resp = requests.get(url, headers=headers)
        return resp.json() if resp.status_code == 200 else []

    participantes = [
        (p.get("puuid"), p.get("riotId"))
        for p in partida["participants"]
        if p.get("puuid")
    ]

    dados_maestria = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        futuros = {
            executor.submit(buscar_maestria, puuid): (puuid, riot_id)
            for puuid, riot_id in participantes
        }
        for futuro in as_completed(futuros):
            puuid, riot_id = futuros[futuro]
            dados_maestria[riot_id] = {
                "puuid": puuid,
                "maestria": futuro.result()
            }

    with open("maestria_jogadores.json", "w", encoding="utf-8") as f:
        json.dump(dados_maestria, f, ensure_ascii=False, indent=4)