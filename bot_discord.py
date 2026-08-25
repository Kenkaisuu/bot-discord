import discord
from discord.ext import commands
import aiohttp
from datetime import datetime, timezone
import json # Tambahan modul untuk menyimpan data angka testimoni

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ==========================================
# KOMPONEN UI UNTUK COMMAND PING
# ==========================================
class PingView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Uji Ulang Latensi", style=discord.ButtonStyle.primary, emoji="🔄")
    async def refresh_ping(self, interaction: discord.Interaction, button: discord.ui.Button):
        ws_latency = round(self.bot.latency * 1000)

        if ws_latency < 100:
            status = "🟢 Sangat Lancar"
            color = discord.Color.green()
        elif ws_latency < 200:
            status = "🟡 Cukup Baik"
            color = discord.Color.gold()
        else:
            status = "🔴 Lambat"
            color = discord.Color.red()

        embed = discord.Embed(
            title="🏓 Pong! Status Koneksi Bot",
            description="Berikut adalah latensi koneksi bot secara *real-time*:",
            color=color
        )
        embed.add_field(name="⚡ Websocket Latency", value=f"`{ws_latency} ms`", inline=True)
        embed.add_field(name="📡 Status Server", value=f"`{status}`", inline=True)
        embed.set_footer(
            text=f"Diperbarui oleh {interaction.user.name}",
            icon_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None
        )

        await interaction.response.edit_message(embed=embed, view=self)

# ==========================================
# KOMPONEN UI UNTUK COMMAND ROBLOX
# ==========================================
class RobloxView(discord.ui.View):
    def __init__(self, profile_url):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Buka Profil", url=profile_url, emoji="🎮"))

    @discord.ui.button(label="Perbarui", style=discord.ButtonStyle.primary, emoji="🔄")
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🔄 Gunakan perintah `!roblox <username>` kembali untuk memperbarui data terbaru!", 
            ephemeral=True
        )

# ==========================================
# EVENT & COMMANDS
# ==========================================
@bot.event
async def on_ready():
    print(f'Bot {bot.user} berhasil online! 🚀')

@bot.command()
async def ping(ctx):
    ws_latency = round(bot.latency * 1000)

    if ws_latency < 100:
        status = "🟢 Sangat Lancar"
        color = discord.Color.green()
    elif ws_latency < 200:
        status = "🟡 Cukup Baik"
        color = discord.Color.gold()
    else:
        status = "🔴 Lambat"
        color = discord.Color.red()

    embed = discord.Embed(
        title="🏓 Pong! Status Koneksi Bot",
        description="Berikut adalah latensi koneksi bot saat ini:",
        color=color
    )
    embed.add_field(name="⚡ Websocket Latency", value=f"`{ws_latency} ms`", inline=True)
    embed.add_field(name="📡 Status Server", value=f"`{status}`", inline=True)
    embed.set_footer(
        text=f"Diminta oleh {ctx.author.name}",
        icon_url=ctx.author.display_avatar.url if ctx.author.display_avatar else None
    )

    view = PingView(bot)
    await ctx.send(embed=embed, view=view)

@bot.command()
async def roblox(ctx, username: str = None):
    if username is None:
        await ctx.send('❌ Harap masukkan username Roblox! Contoh: `!roblox divineakids1`')
        return

    async with aiohttp.ClientSession() as session:
        search_url = "https://users.roblox.com/v1/usernames/users"
        payload = {"usernames": [username], "excludeBannedUsers": False}
        
        async with session.post(search_url, json=payload) as resp:
            data = await resp.json()
            if not data.get("data"):
                await ctx.send(f'❌ Akun Roblox dengan username **{username}** tidak ditemukan!')
                return
            user_id = data["data"][0]["id"]

        async with session.get(f"https://users.roblox.com/v1/users/{user_id}") as resp:
            details = await resp.json()
            
        async with session.get(f"https://friends.roblox.com/v1/users/{user_id}/followers/count") as resp:
            followers = (await resp.json()).get("count", 0)
            
        async with session.get(f"https://friends.roblox.com/v1/users/{user_id}/followings/count") as resp:
            following = (await resp.json()).get("count", 0)

        async with session.get(f"https://friends.roblox.com/v1/users/{user_id}/friends/count") as resp:
            friends = (await resp.json()).get("count", 0)

        async with session.get(f"https://groups.roblox.com/v1/users/{user_id}/groups/roles") as resp:
            groups_data = await resp.json()
            groups_count = len(groups_data.get("data", []))

        thumb_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=352x352&format=Png&isCircular=false"
        async with session.get(thumb_url) as resp:
            thumb_data = await resp.json()
            avatar_url = thumb_data["data"][0]["imageUrl"] if thumb_data.get("data") else None

    name = details.get("name", username)
    display_name = details.get("displayName", name)
    bio = details.get("description", "").strip() or "Pengguna belum mengisi deskripsi."
    is_verified = details.get("hasVerifiedBadge", False)
    status_str = "✅ Verified" if is_verified else "❌ Belum Verified"
    badges_count = 0  

    created_raw = details.get("created", "")
    if created_raw:
        created_dt = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - created_dt
        
        years = delta.days // 365
        remaining_days = delta.days % 365
        months = remaining_days // 30
        days = remaining_days % 30
        
        usia_str = f"{years} Tahun {months} Bulan {days} Hari"
        created_fmt = created_dt.strftime("%m/%d/%Y jam %H:%M:%S")
    else:
        usia_str = "Tidak diketahui"
        created_fmt = "Tidak diketahui"

    profile_url = f"https://www.roblox.com/users/{user_id}/profile"

    embed = discord.Embed(
        title="🎮 Profil Roblox",
        description="📋 **Informasi Akun Roblox**",
        color=0x2b2d31
    )
    
    embed.add_field(name="#️⃣ Nama Pengguna", value=name, inline=True)
    embed.add_field(name="🏷️ Nama Tampilan", value=display_name, inline=True)
    embed.add_field(name="🆔 ID Pengguna", value=str(user_id), inline=True)
    
    embed.add_field(name="✅ Status", value=status_str, inline=True)
    embed.add_field(name="👤 Pengikut", value=str(followers), inline=True)
    embed.add_field(name="🤝 Teman", value=str(friends), inline=True)
    
    embed.add_field(name="➡️ Mengikuti", value=str(following), inline=True)
    embed.add_field(name="🏰 Grup", value=str(groups_count), inline=True)
    embed.add_field(name="🥇 Lencana", value=str(badges_count), inline=True)
    
    embed.add_field(name="⏳ Usia Akun", value=usia_str, inline=False)
    embed.add_field(name="📅 Tanggal Dibuat", value=created_fmt, inline=False)
    embed.add_field(name="📝 Deskripsi", value=f"> {bio}", inline=False)

    if avatar_url:
        embed.set_thumbnail(url=avatar_url)

    now_str = datetime.now().strftime("%m/%d/%y, %I:%M %p")
    embed.set_footer(text=f"Dibuat oleh {ctx.author.name} • {now_str}")

    view = RobloxView(profile_url)
    await ctx.send(embed=embed, view=view)

# ==========================================
# COMMAND UP TESTIMONI (Bisa 2 Foto)
# ==========================================
@bot.command()
async def uptesti(ctx, customer: discord.Member = None, harga: str = None, *, produk: str = None):
    # Cek kelengkapan pesannya
    if not customer or not harga or not produk:
        await ctx.send("❌ Format salah! Ketik seperti ini:\n`!uptesti @Customer 35000 Nama Produk`")
        return

    # Mengecek apakah ada gambar yang dilampirkan
    if not ctx.message.attachments:
        await ctx.send("❌ Kamu belum mengunggah gambar bukti pembayarannya! Ulangi perintah dan lampirkan gambar ya.")
        return
        
    # 1. Membaca nomor urut dari file JSON (Mulai dari 47)
    try:
        with open("testi_data.json", "r") as f:
            data = json.load(f)
            testi_num = data.get("count", 47)
    except FileNotFoundError:
        # Jika file belum ada, bot akan memulainya dari angka 47
        testi_num = 47

    # 2. Membuat Embed
    embed = discord.Embed(
        title=f"👥 __TESTIMONI #{testi_num}__",
        description=(
            f"👤 Customer : {customer.mention}\n"
            f"📦 Produk : {produk}\n"
            f"🏷️ Price : {harga}\n"
            f"🔔 Status : Berhasil"
        ),
        color=0x3498db # Warna garis biru 
    )

    # 3. Menata Gambar Profil & Gambar Utama
    if customer.display_avatar:
        embed.set_thumbnail(url=customer.display_avatar.url)

    # 4. Memproses Foto (Maksimal 2 foto)
    lampiran_foto = []
    for indeks, attachment in enumerate(ctx.message.attachments):
        if indeks >= 2: # Membatasi hanya memproses 2 foto pertama
            break
            
        foto = await attachment.to_file()
        lampiran_foto.append(foto)
        
        # Menjadikan foto pertama sebagai gambar utama di dalam embed
        if indeks == 0:
            embed.set_image(url=f"attachment://{attachment.filename}")

    # 5. Mengirim embed dan kumpulan file gambarnya
    await ctx.send(embed=embed, files=lampiran_foto)

    # 6. Menyimpan angka urutan berikutnya (ditambah 1)
    with open("testi_data.json", "w") as f:
        json.dump({"count": testi_num + 1}, f)

    # 7. Menghapus perintah yang diketik agar rapi
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

# Token Bot (PASTIKAN MENGGANTI INI DENGAN TOKEN ASLIMU)
bot.run('MTU0MTYzMzg4MDk1MDMwODk2NA.GCxSOm.5qZuaoUECiaFd3lvMm9q4RedVcy4wbaq_tOQ8M')
