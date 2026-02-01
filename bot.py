import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import os
import asyncio

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

PRECO_MINIMO = 10
PRECO_MAXIMO = 180

URL = "https://www.gamivo.com/product-category/xbox-games"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

ultimos_jogos = set()

@bot.event
async def on_ready():
    print("Bot online")
    verificar_promocoes.start()

# ===== BUSCA DETALHADA =====
def buscar_jogos():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    jogos = []

    for item in soup.select(".product-item"):
        try:
            nome = item.select_one(".product-title").text.strip()
            link = item.select_one("a")["href"]
            imagem = item.select_one("img")["src"]

            # 🔎 ABRE A PÁGINA DO JOGO
            pagina = requests.get(link, headers=headers)
            soup_jogo = BeautifulSoup(pagina.text, "html.parser")

            texto_pagina = soup_jogo.text.lower()

            # 🇧🇷 FILTRO REGIÃO REAL
            if "brazil" not in texto_pagina and "global" not in texto_pagina:
                continue

            preco_tag = soup_jogo.select_one(".price")
            if not preco_tag:
                continue

            preco = float(
                preco_tag.text.replace("R$", "")
                .replace("$", "")
                .replace(",", ".")
            )

            if not (PRECO_MINIMO <= preco <= PRECO_MAXIMO):
                continue

            preco_antigo_tag = soup_jogo.select_one(".price del")
            if preco_antigo_tag:
                preco_antigo = float(
                    preco_antigo_tag.text.replace("R$", "")
                    .replace("$", "")
                    .replace(",", ".")
                )
                desconto = int(((preco_antigo - preco) / preco_antigo) * 100)
            else:
                preco_antigo = None
                desconto = 0

            jogos.append({
                "nome": nome,
                "preco": preco,
                "preco_antigo": preco_antigo,
                "desconto": desconto,
                "link": link,
                "imagem": imagem
            })

        except:
            continue

    return jogos

# ===== EMBED =====
def criar_embed(jogo):
    embed = discord.Embed(
        title=f"🎮 {jogo['nome']}",
        url=jogo["link"],
        description="🔥 **Xbox • Resgatável no Brasil 🇧🇷**",
        color=discord.Color.from_rgb(16, 124, 16)
    )

    embed.add_field(name="💰 Preço", value=f"**$ {jogo['preco']:.2f}**", inline=True)

    if jogo["preco_antigo"]:
        embed.add_field(name="🏷️ Antes", value=f"$ {jogo['preco_antigo']:.2f}", inline=True)
        embed.add_field(name="📉 Desconto", value=f"🔥 **-{jogo['desconto']}%**", inline=True)

    embed.add_field(name="🕹️ Plataforma", value="Xbox", inline=True)
    embed.add_field(name="🌎 Região", value="Brasil / Global 🇧🇷", inline=True)

    embed.set_image(url=jogo["imagem"])
    embed.set_thumbnail(
        url="https://upload.wikimedia.org/wikipedia/commons/4/43/Xbox_one_logo.svg"
    )

    embed.set_footer(text="Catálogo Xbox • Bot Gamivo")

    return embed

# ===== LOOP =====
@tasks.loop(minutes=30)
async def verificar_promocoes():
    canal = bot.get_channel(CHANNEL_ID)
    jogos = buscar_jogos()

    for jogo in jogos:
        if jogo["link"] not in ultimos_jogos:
            ultimos_jogos.add(jogo["link"])
            await canal.send("@everyone 🔥 **Nova promoção Xbox!**")
            await canal.send(embed=criar_embed(jogo))
            await asyncio.sleep(2)

# ===== COMANDO =====
@bot.command(name="catalogo")
async def catalogo(ctx):
    jogos = buscar_jogos()

    if not jogos:
        await ctx.send("😢 Nenhum jogo entre $10 e $180 agora.")
        return

    await ctx.send("@everyone 🎮 **Catálogo Xbox ($10–$180)**")

    for jogo in jogos[:10]:
        await ctx.send(embed=criar_embed(jogo))
        await asyncio.sleep(1)

bot.run(TOKEN)
