import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import os
import asyncio
import re

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

PRECO_MINIMO = 10
PRECO_MAXIMO = 180

URL = "https://www.eneba.com/store/xbox-games"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

ultimos_links = set()

@bot.event
async def on_ready():
    print("Bot online")
    verificar_promocoes.start()

# ===== BUSCA ROBUSTA =====
def buscar_jogos():
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(URL, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    jogos = []

    # Cada jogo é um link para /xbox-*
    for a in soup.find_all("a", href=True):
        href = a["href"]

        if not href.startswith("/xbox"):
            continue

        link = "https://www.eneba.com" + href

        img = a.find("img")
        if not img or not img.get("src"):
            continue

        imagem = img["src"]

        texto = a.get_text(" ", strip=True)

        preco_match = re.search(r"\$\s?(\d+[\.,]?\d*)", texto)
        if not preco_match:
            continue

        preco = float(preco_match.group(1).replace(",", "."))

        if not (PRECO_MINIMO <= preco <= PRECO_MAXIMO):
            continue

        nome = texto.split("$")[0].strip()

        jogos.append({
            "nome": nome,
            "preco": preco,
            "link": link,
            "imagem": imagem,
            "desconto": 0
        })

    return jogos

# ===== EMBED =====
def criar_embed(jogo):
    embed = discord.Embed(
        title=f"🎮 {jogo['nome']}",
        url=jogo["link"],
        description="🔥 **Jogo Xbox na Eneba**",
        color=discord.Color.from_rgb(16, 124, 16)
    )

    embed.add_field(
        name="💰 Preço",
        value=f"**$ {jogo['preco']:.2f}**",
        inline=True
    )

    embed.add_field(name="🕹️ Plataforma", value="Xbox", inline=True)
    embed.add_field(name="🛒 Loja", value="Eneba", inline=True)

    embed.set_image(url=jogo["imagem"])
    embed.set_thumbnail(
        url="https://upload.wikimedia.org/wikipedia/commons/4/43/Xbox_one_logo.svg"
    )

    embed.set_footer(text="Catálogo Xbox • Bot Eneba")

    return embed

# ===== LOOP =====
@tasks.loop(minutes=30)
async def verificar_promocoes():
    canal = bot.get_channel(CHANNEL_ID)
    jogos = buscar_jogos()

    for jogo in jogos:
        if jogo["link"] not in ultimos_links:
            ultimos_links.add(jogo["link"])
            await canal.send("@everyone 🔥 **Jogo Xbox encontrado!**")
            await canal.send(embed=criar_embed(jogo))
            await asyncio.sleep(2)

# ===== COMANDO =====
@bot.command(name="catalogo")
async def catalogo(ctx):
    jogos = buscar_jogos()

    if not jogos:
        await ctx.send("😢 Nenhum jogo encontrado agora.")
        return

    await ctx.send("@everyone 🎮 **Catálogo Xbox ($10–$180)**")

    for jogo in jogos[:10]:
        await ctx.send(embed=criar_embed(jogo))
        await asyncio.sleep(1)

bot.run(TOKEN)
    
