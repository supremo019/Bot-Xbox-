import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import os
import asyncio

# ===== CONFIG =====
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

PRECO_MINIMO = 10
PRECO_MAXIMO = 180

URL = "https://www.gamivo.com/product-category/xbox-games"

# ===== DISCORD =====
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

ultimos_links = set()

@bot.event
async def on_ready():
    print("Bot online")
    verificar_promocoes.start()

# ===== BUSCAR JOGOS (SIMPLES E FUNCIONAL) =====
def buscar_jogos():
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(URL, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    jogos = []

    for item in soup.select(".product-item"):
        try:
            nome = item.select_one(".product-title").text.strip()
            link = item.select_one("a")["href"]
            imagem = item.select_one("img")["src"]

            preco_tag = item.select_one(".price")
            if not preco_tag:
                continue

            preco = float(
                preco_tag.text.replace("$", "")
                .replace("R$", "")
                .replace(",", ".")
            )

            if not (PRECO_MINIMO <= preco <= PRECO_MAXIMO):
                continue

            preco_antigo_tag = item.select_one(".price del")
            if preco_antigo_tag:
                preco_antigo = float(
                    preco_antigo_tag.text.replace("$", "")
                    .replace("R$", "")
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
        description="🔥 **Jogo Xbox em promoção na Gamivo**",
        color=discord.Color.from_rgb(16, 124, 16)  # Verde Xbox
    )

    embed.add_field(
        name="💰 Preço",
        value=f"**$ {jogo['preco']:.2f}**",
        inline=True
    )

    if jogo["preco_antigo"]:
        embed.add_field(
            name="🏷️ Antes",
            value=f"$ {jogo['preco_antigo']:.2f}",
            inline=True
        )
        embed.add_field(
            name="📉 Desconto",
            value=f"🔥 **-{jogo['desconto']}%**",
            inline=True
        )

    embed.add_field(name="🕹️ Plataforma", value="Xbox", inline=True)
    embed.add_field(name="🛒 Loja", value="Gamivo", inline=True)

    embed.set_image(url=jogo["imagem"])
    embed.set_thumbnail(
        url="https://upload.wikimedia.org/wikipedia/commons/4/43/Xbox_one_logo.svg"
    )

    embed.set_footer(text="Catálogo Xbox • Bot Gamivo")

    return embed

# ===== LOOP AUTOMÁTICO =====
@tasks.loop(minutes=30)
async def verificar_promocoes():
    canal = bot.get_channel(CHANNEL_ID)
    jogos = buscar_jogos()

    for jogo in jogos:
        if jogo["link"] not in ultimos_links:
            ultimos_links.add(jogo["link"])
            await canal.send("@everyone 🔥 **Nova promoção Xbox!**")
            await canal.send(embed=criar_embed(jogo))
            await asyncio.sleep(2)

# ===== COMANDO !catalogo =====
@bot.command(name="catalogo")
async def catalogo(ctx):
    jogos = buscar_jogos()

    if not jogos:
        await ctx.send("😢 Nenhum jogo entre $10 e $180 agora.")
        return

    await ctx.send("@everyone 🎮 **Catálogo Xbox ($10 – $180)**")

    for jogo in jogos[:10]:
        await ctx.send(embed=criar_embed(jogo))
        await asyncio.sleep(1)

# ===== START =====
bot.run(TOKEN)
