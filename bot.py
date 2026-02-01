import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import os
import asyncio

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
PRECO_MAXIMO = float(os.getenv("PRECO_MAXIMO", 50))

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

URL = "https://www.gamivo.com/product-category/xbox-games"

ultimos_jogos = set()

@bot.event
async def on_ready():
    print("Bot online")
    verificar_promocoes.start()

def buscar_jogos():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    jogos = []

    for item in soup.select(".product-item"):
        try:
            nome = item.select_one(".product-title").text.strip()
            preco_texto = item.select_one(".price").text.strip()
            preco = float(preco_texto.replace("R$", "").replace(",", "."))
            link = item.select_one("a")["href"]
            imagem = item.select_one("img")["src"]

            if preco <= PRECO_MAXIMO:
                jogos.append({
                    "nome": nome,
                    "preco": preco,
                    "link": link,
                    "imagem": imagem
                })
        except:
            continue

    return jogos

def criar_embed(jogo):
    embed = discord.Embed(
        title=jogo["nome"],
        url=jogo["link"],
        description=f"💰 **Preço:** R$ {jogo['preco']:.2f}",
        color=discord.Color.green()
    )
    embed.set_image(url=jogo["imagem"])
    embed.set_footer(text="Promoção encontrada na Gamivo 🎮")
    return embed

@tasks.loop(minutes=30)
async def verificar_promocoes():
    canal = bot.get_channel(CHANNEL_ID)
    jogos = buscar_jogos()

    for jogo in jogos:
        if jogo["link"] not in ultimos_jogos:
            ultimos_jogos.add(jogo["link"])
            embed = criar_embed(jogo)
            await canal.send("@everyone 🔥 **Nova promoção Xbox!**")
            await canal.send(embed=embed)

@bot.command(name="promocoes")
async def promocoes(ctx):
    jogos = buscar_jogos()

    if not jogos:
        await ctx.send("😢 Nenhuma promoção encontrada agora.")
        return

    await ctx.send(f"@everyone 🎮 **Promoções Xbox na Gamivo:**")

    for jogo in jogos[:5]:
        embed = criar_embed(jogo)
        await ctx.send(embed=embed)
        await asyncio.sleep(1)

bot.run(TOKEN)
