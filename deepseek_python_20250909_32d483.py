import discord
import aiohttp
import os
from discord.ext import commands, tasks

TOKEN = os.environ['MTM3MDUxOTA1MDYxODQwOTAxMg.GaZJAx.MVr3JCiZd4LlUFsuxF7u5w7RcslY20JXqMM17E']
CHANNEL_ID = 1414364162079068263
API_URL = "http://95.141.32.116:8704/api/live-timings/leaderboard.json"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

last_best_time = None

async def get_best_lap():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    best_time = None
                    best_driver = "Sconosciuto"
                    best_lap_str = None
                    
                    # Cerca in tutti i piloti
                    drivers = data.get('ConnectedDrivers', []) or []
                    for driver in drivers:
                        cars = driver.get('Cars', {})
                        for car_model, car_data in cars.items():
                            lap_ns = car_data.get('BestLap')
                            if lap_ns and lap_ns > 0:
                                lap_sec = lap_ns / 1000000000
                                if best_time is None or lap_sec < best_time:
                                    best_time = lap_sec
                                    best_driver = driver.get('CarInfo', {}).get('DriverName', 'Sconosciuto')
                                    minutes = int(lap_sec // 60)
                                    seconds = lap_sec % 60
                                    best_lap_str = f"{minutes:01d}:{seconds:06.3f}"
                    
                    return best_driver, best_lap_str, best_time
    except:
        pass
    return None, None, None

@bot.event
async def on_ready():
    print(f'✅ Bot online!')
    check_laps.start()

@tasks.loop(seconds=30)
async def check_laps():
    global last_best_time
    
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return
    
    driver, lap_str, lap_time = await get_best_lap()
    
    if driver and lap_str and lap_time:
        if last_best_time is None:
            last_best_time = lap_time
            await channel.send(f"🏁 **Giro più veloce!**\n👤 {driver}\n⏱️ {lap_str}")
        elif lap_time < last_best_time:
            delta = last_best_time - lap_time
            last_best_time = lap_time
            await channel.send(f"🚀 **NUOVO RECORD!**\n👤 {driver}\n⏱️ {lap_str}\n📉 -{delta:.3f}s")

@bot.command()
async def fastest(ctx):
    driver, lap_str, _ = await get_best_lap()
    if driver and lap_str:
        await ctx.send(f"🏆 **Giro più veloce:** {driver} - {lap_str}")
    else:
        await ctx.send("⚠️ Nessun tempo trovato")

@bot.command()
async def ping(ctx):
    await ctx.send("✅ Bot attivo!")

if __name__ == "__main__":
    bot.run(TOKEN)
