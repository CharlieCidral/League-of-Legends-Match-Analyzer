import requests
import json
import time
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, wait
from maestria import gerar_maestria
from elo import gerar_elos
from kda_win_rate import gerar_estatisticas

# ─── Configuração ────────────────────────────────────────────────────────────
load_dotenv()
API_KEY = os.getenv("API_KEY")
PUUID_SUMMONER = os.getenv("PUUID_SUMMONER")
BASE_URL = "https://br1.api.riotgames.com"

# ─── Mapeamento de elo para pontuação numérica ────────────────────────────────
ELO_PONTOS = {
    "IRON":        {"IV": 100, "III": 200, "II": 300, "I": 400},
    "BRONZE":      {"IV": 500, "III": 600, "II": 700, "I": 800},
    "SILVER":      {"IV": 900, "III": 1000, "II": 1100, "I": 1200},
    "GOLD":        {"IV": 1300, "III": 1400, "II": 1500, "I": 1600},
    "PLATINUM":    {"IV": 1700, "III": 1800, "II": 1900, "I": 2000},
    "EMERALD":     {"IV": 2100, "III": 2200, "II": 2300, "I": 2400},
    "DIAMOND":     {"IV": 2500, "III": 2600, "II": 2700, "I": 2800},
    "MASTER":      {"I": 2900},
    "GRANDMASTER": {"I": 3000},
    "CHALLENGER":  {"I": 3100},
    "Unranked":    {"": 800},   # equivalente a Silver IV
}

def tempo(label, inicio):
    print(f"  ✓ {label}: {time.time() - inicio:.2f}s")

def elo_para_pontos(elo_list):
    """Converte lista de elos para pontuação numérica. Prioriza SOLO/DUO."""
    if not elo_list:
        return ELO_PONTOS["Unranked"][""]

    # Prioridade: RANKED_SOLO > RANKED_FLEX > primeiro disponível
    ordem = ["RANKED_SOLO_5x5", "RANKED_FLEX_SR"]
    entrada = None
    for queue in ordem:
        for e in elo_list:
            if e.get("queueType") == queue:
                entrada = e
                break
        if entrada:
            break
    if not entrada:
        entrada = elo_list[0]

    tier = entrada.get("tier", "Unranked")
    rank = entrada.get("rank", "")
    lp   = entrada.get("leaguePoints", 0)

    base = ELO_PONTOS.get(tier, {}).get(rank, 800)
    return base + (lp / 100) * 25   # LP influencia levemente

def calcular_score_jogador(stats, elo_pts, maestria_champ):
    """
    Score composto por jogador:
      - win_rate (peso 35%)
      - KDA      (peso 25%)
      - elo      (peso 30%)
      - maestria no campeão atual (peso 10%)
    """
    if not stats:
        return 0

    win_rate_norm = stats.get("win_rate", 50) / 100          # 0–1
    kda           = stats.get("kda", 1.0)
    kda_norm      = min(kda / 5, 1)                          # cap em KDA 5
    elo_norm      = min(elo_pts / 3100, 1)                   # cap em Challenger
    maestria_norm = min(maestria_champ / 1_000_000, 1)       # cap em 1M de pts

    score = (
        win_rate_norm * 0.35 +
        kda_norm      * 0.25 +
        elo_norm      * 0.30 +
        maestria_norm * 0.10
    )
    return round(score, 4)

def calcular_probabilidade(resumo, partida):
    """Calcula probabilidade de vitória para Time 100 vs Time 200."""
    # Mapear puuid → teamId
    puuid_para_team = {
        p["puuid"]: p["teamId"]
        for p in partida["participants"]
        if p.get("puuid")
    }
    # Mapear puuid → championId
    puuid_para_champ = {
        p["puuid"]: p["championId"]
        for p in partida["participants"]
        if p.get("puuid")
    }

    scores = {100: [], 200: []}

    for riot_id, dados in resumo.items():
        puuid = dados["puuid"]
        team  = puuid_para_team.get(puuid)
        if not team:
            continue

        stats         = dados.get("estatisticas", {})
        elo_pts       = dados.get("_elo_pontos", 800)
        champ_id      = puuid_para_champ.get(puuid, 0)
        maestria_pts  = dados.get("_maestria_champ_pts", {}).get(champ_id, 0)

        score = calcular_score_jogador(stats, elo_pts, maestria_pts)
        scores[team].append(score)

    media_a = sum(scores[100]) / len(scores[100]) if scores[100] else 0.5
    media_b = sum(scores[200]) / len(scores[200]) if scores[200] else 0.5

    total = media_a + media_b
    if total == 0:
        return 50.0, 50.0

    prob_a = round((media_a / total) * 100, 1)
    prob_b = round(100 - prob_a, 1)
    return prob_a, prob_b

# ─── MAIN ────────────────────────────────────────────────────────────────────
total_inicio = time.time()

# 1. Buscar partida ativa
t = time.time()
url = f"{BASE_URL}/lol/spectator/v5/active-games/by-summoner/{PUUID_SUMMONER}"
headers = {"X-Riot-Token": API_KEY}
response = requests.get(url, headers=headers)

if response.status_code == 200:
    dados = response.json()
    with open("dados_da_partida.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)
    tempo("Buscar partida ativa", t)
else:
    print("Erro ao buscar partida:", response.status_code, response.text)
    exit()

# 2. Rodar os 3 módulos em paralelo
t = time.time()
with ThreadPoolExecutor(max_workers=3) as executor:
    f1 = executor.submit(gerar_maestria, API_KEY)
    f2 = executor.submit(gerar_elos, API_KEY)
    f3 = executor.submit(gerar_estatisticas, API_KEY, 20)
    wait([f1, f2, f3])
    # Propagar exceções se houver
    for f in [f1, f2, f3]:
        f.result()
tempo("Maestria + Elos + Estatísticas (paralelo)", t)

# 3. Consolidar resumo
t = time.time()
with open("maestria_jogadores.json",  "r", encoding="utf-8") as f:
    maestria = json.load(f)
with open("elos_jogadores.json",      "r", encoding="utf-8") as f:
    elos = json.load(f)
with open("estatisticas_jogadores.json", "r", encoding="utf-8") as f:
    estatisticas = json.load(f)
with open("dados_da_partida.json",    "r", encoding="utf-8") as f:
    partida = json.load(f)

# Mapear championId atual por puuid
puuid_para_champ = {
    p["puuid"]: p["championId"]
    for p in partida["participants"]
    if p.get("puuid")
}
# Mapear teamId por puuid
puuid_para_team = {
    p["puuid"]: p["teamId"]
    for p in partida["participants"]
    if p.get("puuid")
}

resumo = {}
for riot_id, dados_m in maestria.items():
    puuid    = dados_m["puuid"]
    champ_id = puuid_para_champ.get(puuid, 0)
    team_id  = puuid_para_team.get(puuid, 0)

    # Campeões com grau S
    campeoes_S = [
        champ.get("championName", "Desconhecido")   # usa .get() para evitar KeyError
        for champ in dados_m["maestria"]
        if any(g in ["S-", "S", "S+"] for g in champ.get("milestoneGrades", []))
    ]

    # Pontos de maestria no campeão atual
    maestria_champ_pts = {
        champ.get("championId", 0): champ.get("championPoints", 0)
        for champ in dados_m["maestria"]
    }

    # Elo
    elo_list = elos.get(riot_id, {}).get("elo", [])
    elo_pts  = elo_para_pontos(elo_list)
    elo_str  = ""
    if elo_list and elo_list[0].get("tier") != "Unranked":
        # Pega o mesmo elo que foi usado no cálculo
        for queue in ["RANKED_SOLO_5x5", "RANKED_FLEX_SR"]:
            match = next((e for e in elo_list if e.get("queueType") == queue), None)
            if match:
                elo_str = f"{match['tier']} {match['rank']} {match['leaguePoints']}LP"
                break

    stats = estatisticas.get(riot_id, {}).get("estatisticas", {})

    resumo[riot_id] = {
        "puuid":           puuid,
        "team":            team_id,
        "campeao_id":      champ_id,
        "campeoes_com_S":  campeoes_S,
        "elo":             elo_str,
        "_elo_pontos":     elo_pts,
        "_maestria_champ_pts": maestria_champ_pts,
        "estatisticas":    stats
    }

with open("resumo_jogadores.json", "w", encoding="utf-8") as f:
    json.dump(resumo, f, ensure_ascii=False, indent=4)
tempo("Consolidar resumo", t)

# 4. Calcular probabilidade de vitória
prob_a, prob_b = calcular_probabilidade(resumo, partida)

resultado_prob = {
    "time_100": {
        "jogadores": [r for r, d in resumo.items() if d["team"] == 100],
        "probabilidade_vitoria": f"{prob_a}%"
    },
    "time_200": {
        "jogadores": [r for r, d in resumo.items() if d["team"] == 200],
        "probabilidade_vitoria": f"{prob_b}%"
    }
}

with open("probabilidade_vitoria.json", "w", encoding="utf-8") as f:
    json.dump(resultado_prob, f, ensure_ascii=False, indent=4)

# ─── Resultado final ──────────────────────────────────────────────────────────
print(f"\n⏱  Tempo total: {time.time() - total_inicio:.2f}s")
print("\n══════════════════════════════════════")
print("       PROBABILIDADE DE VITÓRIA        ")
print("══════════════════════════════════════")
print(f"  🔵 Time Azul (100): {prob_a}%")
for nome, d in resumo.items():
    if d["team"] == 100:
        wr = d["estatisticas"].get("win_rate", "?")
        print(f"      · {nome:<30} WR: {wr}%  Elo: {d['elo'] or 'Unranked'}")

print(f"\n  🔴 Time Vermelho (200): {prob_b}%")
for nome, d in resumo.items():
    if d["team"] == 200:
        wr = d["estatisticas"].get("win_rate", "?")
        print(f"      · {nome:<30} WR: {wr}%  Elo: {d['elo'] or 'Unranked'}")
print("══════════════════════════════════════")
print("Arquivos salvos: resumo_jogadores.json | probabilidade_vitoria.json")