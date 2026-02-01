import discord
from discord.ext import tasks, commands
import requests
from bs4 import BeautifulSoup
import os
import json
import asyncio

# ================= CONFIGURAÇÃO =================
TOKEN = os.getenv("DISCORD_TOKEN")         # Token do bot Discord
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # ID do canal Discord
URL = "https://www.rockstargames.com/newswire"
ARQUIVO_NOTICIAS = "noticias_rdr2.json"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= FUNÇÕES DE ARMAZENAMENTO =================
def carregar_noticias_enviadas():
    if os.path.exists(ARQUIVO_NOTICIAS):
        with open(ARQUIVO_NOTICIAS, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def salvar_noticia_enviada(url):
    enviadas = carregar_noticias_enviadas()
    enviadas.add(url)
    with open(ARQUIVO_NOTICIAS, "w", encoding="utf-8") as f:
        json.dump(list(enviadas), f, ensure_ascii=False, indent=4)

# ================= FUNÇÃO DE BUSCA =================
def buscar_noticias_rdr2():
    try:
        r = requests.get(URL, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print("Erro ao acessar Rockstar Newswire:", e)
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    noticias = []

    # Seleciona todas as notícias
    for card in soup.select("div.NewsCardstyles__Card-sc"):
        try:
            titulo_tag = card.select_one("h3")
            if not titulo_tag:
                continue
            titulo = titulo_tag.text.strip()

            # Filtra apenas notícias de Red Dead Online
            if "Red Dead Online" not in titulo:
                continue

            link_tag = card.select_one("a")
            link = link_tag["href"]
            if not link.startswith("http"):
                link = "https://www.rockstargames.com" + link

            descricao_tag = card.select_one("p")
            descricao = descricao_tag.text.strip() if descricao_tag else "Sem descrição"

            imagem_tag = card.select_one("img")
            imagem = imagem_tag["src"] if imagem_tag else None

            noticias.append({
                "titulo": titulo,
                "descricao": descricao,
                "link": link,
                "imagem": imagem
            })
        except:
            continue

    return noticias

# ================= FUNÇÃO DE EMBED =================
def criar_embed(noticia):
    embed = discord.Embed(
        title=noticia["titulo"],
        url=noticia["link"],
        description=noticia["descricao"],
        color=discord.Color.from_rgb(184, 134, 11)
    )
    if noticia["imagem"]:
        embed.set_image(url=noticia["imagem"])
    embed.set_footer(text="Red Dead Online • Rockstar Newswire")
    return embed

# ================= LOOP AUTOMÁTICO =================
@tasks.loop(minutes=15)
async def enviar_novas_noticias():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)

    noticias = buscar_noticias_rdr2()
    enviadas = carregar_noticias_enviadas()
    novas = [n for n in noticias if n["link"] not in enviadas]

    if not novas:
        return

    await channel.send("@everyone 🎮 **Novas notícias de Red Dead Online!**")
    for noticia in novas:
        await channel.send(embed=criar_embed(noticia))
        salvar_noticia_enviada(noticia["link"])
        await asyncio.sleep(1)

# ================= COMANDO MANUAL COM GATILHO =================
@bot.command(name="red")
async def noticias_rdr2(ctx):
    noticias = buscar_noticias_rdr2()
    enviadas = carregar_noticias_enviadas()
    novas = [n for n in noticias if n["link"] not in enviadas]

    if not novas:
        await ctx.send("😢 Nenhuma notícia nova de Red Dead Online encontrada.")
        return

    await ctx.send("@everyone 🎮 **Novas notícias de Red Dead Online!**")
    for noticia in novas:
        await ctx.send(embed=criar_embed(noticia))
        salvar_noticia_enviada(noticia["link"])
        await asyncio.sleep(1)

# ================= INÍCIO DO BOT =================
@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    enviar_novas_noticias.start()

bot.run(TOKEN)
