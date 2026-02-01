
import discord
from discord.ext import tasks
import requests
from bs4 import BeautifulSoup
import json
import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

URL = "https://www.gamivo.com/store/games/xbox"
PRECO_MAXIMO = float(os.getenv("PRECO_MAXIMO", 50))
INTERVALO_MINUTOS = 30
CACHE = "cache.json"

intents = discord.Intents.default()
client = discord.Client(intents=intents)

if os.path.exists(CACHE):
    with open(CACHE, "r") as f:
        postados = set(json.load(f))
else:
    postados = set()

def salvar():
    with open(CACHE, "w") as f:
        json.dump(list(postados), f)

def preco(texto):
    try:
        return float(texto.replace("€", "").replace(",", ".").strip())
    except:
        return None

def buscar():
    r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    jogos = []

    for item in soup.select("li.product-tile"):
        titulo = item.select_one(".product-tile__title")
        preco_el = item.select_one(".price-current")
        link = item.select_one("a")

        if not titulo or not preco_el or not link:
            continue

        valor = preco(preco_el.text)
        if not valor or valor > PRECO_MAXIMO:
            continue

        url = "https://www.gamivo.com" + link["href"]
        chave = f"{titulo.text}|{valor}"

        jogos.append((chave, titulo.text, valor, url))

    return jogos

@client.event
async def on_ready():
    print("Bot online")
    checar.start()

@tasks.loop(minutes=INTERVALO_MINUTOS)
async def checar():
    canal = client.get_channel(CHANNEL_ID)
    for chave, titulo, valor, url in buscar():
        if chave in postados:
            continue

        embed = discord.Embed(
            title="🔥 Promoção Xbox no Gamivo",
            description=titulo,
            color=0x2ecc71
        )
        embed.add_field(name="Preço", value=f"€ {valor}", inline=True)
        embed.add_field(name="Link", value=f"[Ver oferta]({url})", inline=True)

        await canal.send(embed=embed)

        postados.add(chave)
        salvar()

client.run(DISCORD_TOKEN)
