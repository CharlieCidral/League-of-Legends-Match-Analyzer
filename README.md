# 🔮 League of Legends Match Analyzer



Este projeto conecta-se à \*\*Riot Games API\*\* para buscar informações de uma partida ativa de League of Legends e calcular a probabilidade de vitória de cada time com base em estatísticas dos jogadores.
\- (https://developer.riotgames.com/).


## 🚀 Funcionalidades

\- Buscar partida ativa de um invocador via \*\*PUUID\*\*

\- Coletar:

&#x20; - \*\*Maestria\*\* dos campeões

&#x20; - \*\*Elo\*\* dos jogadores

&#x20; - \*\*Estatísticas\*\* (KDA, taxa de vitória, etc.)

\- Consolidar os dados em arquivos JSON

\- Calcular a \*\*probabilidade de vitória\*\* entre os times

\- Exibir resultados no terminal



## 📂 Estrutura de Arquivos

\- `main.py` → Script principal

\- `maestria.py` → Funções para buscar maestria

\- `elo.py` → Funções para buscar elo

\- `kda\_win\_rate.py` → Funções para buscar estatísticas

\- `resumo\_jogadores.json` → Resumo consolidado dos jogadores

\- `probabilidade\_vitoria.json` → Probabilidade de vitória calculada

\- `.env` → Arquivo com credenciais (API\_KEY e PUUID)



## ⚙️ Configuração



### 1. Instalar dependências

```bash

pip install requests python-dotenv

```





### 2. Buscar puuid(\*Substitua o nome da conta, Tag e a chave API)

```bash

curl -X GET "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/NOME_DA_CONTA/_TAG_" ^
  -H "X-Riot-Token: RGAPI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

```



### 3. Criar arquivo .env

```bash

API\_KEY=RGAPI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

PUUID\_SUMMONER=seu-puuid-aqui

```



### 4. Executar o script

```bash

python main.py

```



📊 Exemplo de Saída



✓ Buscar partida ativa: 1.09s

✓ Maestria + Elos + Estatísticas (paralelo): 8.61s

✓ Consolidar resumo: 0.42s



══════════════════════════════════════

&#x20;      PROBABILIDADE DE VITÓRIA        

══════════════════════════════════════

&#x20; 🔵 Time Azul (100): 54.3%

&#x20;     · Jogador1                 WR: 52%  Elo: GOLD II 34LP

&#x20;     · Jogador2                 WR: 48%  Elo: SILVER I 12LP



&#x20; 🔴 Time Vermelho (200): 45.7%

&#x20;     · Jogador3                 WR: 50%  Elo: PLATINUM IV 80LP

&#x20;     · Jogador4                 WR: 47%  Elo: Unranked

══════════════════════════════════════

Arquivos salvos: resumo\_jogadores.json | probabilidade\_vitoria.json



Dicas extras, você pode alterar o qeueu=450(ARAM), para ver estátisticas em outros modos de jogo:

· Ranqueada Solo/Duo (Summoner’s Rift) → 420

· Ranqueada Flex (Summoner’s Rift) → 440

· Normal Draft (Summoner’s Rift) → 400



