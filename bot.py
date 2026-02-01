import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import asyncio
import json
import os

# ================= CONFIGURAÇÃO =================
TOKEN = os.getenv("DISCORD_TOKEN")         # Token do bot Discord
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # ID do canal Discord
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")  # Chave ScraperAPI

PRECO_MIN = 10
PRECO_MAX = 180
URL = "https://www.nuuvem.com/br-pt/catalog/platforms/xbox"
ARQUIVO_JOGOS_ENVIADOS = "jogos_enviados.json"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= FUNÇÕES DE ARMAZENAMENTO =================
def carregar_jogos_enviados():
    if os.path.exists(ARQUIVO_JOGOS_ENVIADOS):
        with open(ARQUIVO_JOGOS_ENVIADOS, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def salvar_jogo_enviado(link):
    enviados = carregar_jogos_enviados()
    enviados.add(link)
    with open(ARQUIVO_JOGOS_ENVIADOS, "w", encoding="utf-8") as f:
        json.dump(list(enviados), f, ensure_ascii=False, indent=4)

# ================= FUNÇÃO DE BUSCA =================
def buscar_jogos():
    params = {
        "api_key": SCRAPERAPI_KEY,
        "url": URL,
        "render": "true"
    }
    try:
        r = requests.get("http://api.scraperapi.com", params=params, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print("Erro na requisição:", e)
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    jogos = []

    # Atualize seletores se a Nuuvem mudar o layout
    for card in soup.select("div.product-card"):
        try:
            nome = card.select_one("h3.product-title").text.strip()
            link = card.select_one("a")["href"]
            if not link.startswith("http"):
                link = "https://www.nuuvem.com" + link
            imagem = card.select_one("img")["src"]

            preco_texto = card.select_one("span.product-price--val").text
            preco = float(preco_texto.replace("R$", "").replace(".", "").replace(",", ".").strip())

            if not (PRECO_MIN <= preco <= PRECO_MAX):
                continue

            desconto = 0
            desconto_tag = card.select_one("span.product-discount")
            if desconto_tag:
                desconto = int(desconto_tag.text.replace("%","").replace("-","").strip())

            jogos.append({
                "nome": nome,
                "preco": preco,
                "desconto": desconto,
                "link": link,
                "imagem": imagem
            })
        except:
            continue

    return jogos

# ================= FUNÇÃO DE EMBED =================
def criar_embed(jogo):
    embed = discord.Embed(
        title=f"🎮 {jogo['nome']}",
        url=jogo["link"],
        description="🔥 **Jogo Xbox em promoção na Nuuvem**",
        color=discord.Color.from_rgb(16, 124, 16)
    )
    embed.add_field(name="💰 Preço", value=f"**R$ {jogo['preco']:.2f}**", inline=True)
    if jogo["desconto"] > 0:
        embed.add_field(name="📉 Desconto", value=f"🔥 **-{jogo['desconto']}%**", inline=True)
    embed.add_field(name="🕹️ Plataforma", value="Xbox", inline=True)
    embed.add_field(name="🇧🇷 Região", value="Brasil", inline=True)
    embed.add_field(name="🛒 Loja", value="Nuuvem", inline=True)
    embed.set_image(url=jogo["imagem"])
    embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/4/43/Xbox_one_logo.svg")
    embed.set_footer(text="Catálogo Xbox • Nuuvem")
    return embed

# ================= LOOP AUTOMÁTICO =================
@tasks.loop(minutes=30)
async def enviar_novos_jogos():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    jogos = buscar_jogos()
    enviados = carregar_jogos_enviados()
    novos_jogos = [j for j in jogos if j["link"] not in enviados]

    if not novos_jogos:
        return

    await channel.send("@everyone 🎮 **Novos jogos Xbox na Nuuvem!**")
    for jogo in novos_jogos[:10]:
        await channel.send(embed=criar_embed(jogo))
        salvar_jogo_enviado(jogo["link"])
        await asyncio.sleep(1)

# ================= COMANDO MANUAL =================
@bot.command(name="jogos")
async def jogos(ctx):
    jogos_encontrados = buscar_jogos()
    enviados = carregar_jogos_enviados()
    novos_jogos = [j for j in jogos_encontrados if j["link"] not in enviados]

    if not novos_jogos:
        await ctx.send("😢 Nenhum jogo novo encontrado entre R$10 e R$180.")
        return

    await ctx.send("@everyone 🎮 **Novos jogos Xbox na Nuuvem!**")
    for jogo in novos_jogos[:10]:
        await ctx.send(embed=criar_embed(jogo))
        salvar_jogo_enviado(jogo["link"])
        await asyncio.sleep(1)

# ================= INÍCIO DO BOT =================
@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    enviar_novos_jogos.start()

bot.run(TOKEN)
    
