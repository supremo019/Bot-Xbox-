import discord
from discord.ext import tasks, commands
import feedparser
import os
import json
import asyncio

# ================= CONFIGURAÇÃO =================
TOKEN = os.getenv("DISCORD_TOKEN")         # Token do bot Discord
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # ID do canal Discord
RSS_URL = "https://www.rockstargames.com/newswire/rss.xml"
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

def salvar_noticia_enviada(link):
    enviadas = carregar_noticias_enviadas()
    enviadas.add(link)
    with open(ARQUIVO_NOTICIAS, "w", encoding="utf-8") as f:
        json.dump(list(enviadas), f, ensure_ascii=False, indent=4)

# ================= FUNÇÃO DE BUSCA =================
def buscar_noticias_rdr2():
    feed = feedparser.parse(RSS_URL)
    noticias = []

    for entry in feed.entries:
        titulo = entry.title
        descricao = entry.summary if hasattr(entry, 'summary') else "Sem descrição"
        link = entry.link
        imagem = None

        # Algumas entradas do RSS podem ter imagem
        if 'media_content' in entry:
            imagem = entry.media_content[0]['url']

        # Filtrar apenas notícias de Red Dead Online
        if "Red Dead Online" in titulo or "Red Dead Online" in descricao:
            noticias.append({
                "titulo": titulo,
                "descricao": descricao,
                "link": link,
                "imagem": imagem
            })

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
