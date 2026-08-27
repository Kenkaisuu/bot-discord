import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from datetime import datetime, timezone
import json
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ==========================================
# ⚙️ CONFIGURATION & CUSTOM EMOJIS
# ==========================================
GUILD_ID             = 1499785130183491684  # 👑 ID Server Discord
CATEGORY_MARKET_ID   = 1499815599650377850  # 🛒 ID Kategori MARKET
VOUCH_CHANNEL_ID     = 1516750837706129448  # 💬 ID Channel Vouch / Testimoni Form
ORDER_LOG_CHANNEL_ID = 1517536348301688872  # 📜 ID Channel History / Order Log
TESTIMONY_CHANNEL_ID = 1499815827015471195  # 📸 ID Channel Upload Testimoni Slash Command

# 🎨 Custom Emoji Static IDs
EMOJI_USER      = "<:user:1542204894914805760>"
EMOJI_PRODUCT   = "<:product:1542204911096303716>"
EMOJI_STATUS    = "<:status:1542204878074552430>"
EMOJI_PRICE     = "<:price:1542204860999672019>"
EMOJI_CATEGORY  = "<:category:1542204841550413844>"
EMOJI_RATING    = "<:rating:1542387435701534830>"   # 🔎 Emoji Label Rating Kustom
EMOJI_STAR      = "<:star:1542377983279632434>"     # ⭐ Emoji Logo Bintang Kustom

# 💎 Custom Emoji Panel & Buttons
EMOJI_ROBUX     = "<:robux:1542377946352713810>"
EMOJI_PRICELIST = "<:pricelist:1542377965386735647>"
EMOJI_MIDDLEMAN = "<:middleman:1542381608588550144>"

# 🎬 Custom GIF Emoji Status IDs
STATUS_FAILED   = "<a:failed:1542206572208332870>"
STATUS_PENDING  = "<a:pending:1542206602898051102>"
STATUS_SUCCESS  = "<a:success:1542206629380890685>"


# ==========================================
# MODAL POP-UP & VIEW VOUCH UNTUK DM PEMBELI
# ==========================================
class VouchModal(discord.ui.Modal, title="⭐ Form Ulasan Pembeli"):
    product_name = discord.ui.TextInput(
        label="Nama Produk / Layanan",
        placeholder="Contoh: Robux Visend / Jasa Middleman",
        required=True
    )
    rating = discord.ui.TextInput(
        label="Rating (1 - 5 Bintang)",
        placeholder="5",
        min_length=1,
        max_length=1,
        required=True
    )
    review = discord.ui.TextInput(
        label="Ulasan Anda",
        style=discord.TextStyle.paragraph,
        placeholder="Tuliskan pengalaman belanja/rekber kamu di sini...",
        required=True
    )

    def __init__(self, guild_id: int):
        super().__init__()
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.client.get_guild(self.guild_id)
        if not guild:
            await interaction.response.send_message("❌ Server tidak ditemukan.", ephemeral=True)
            return

        vouch_channel = guild.get_channel(VOUCH_CHANNEL_ID)

        try:
            with open("vouch_counter.json", "r") as f:
                v_data = json.load(f)
                vouch_num = v_data.get("count", 4048)
        except FileNotFoundError:
            vouch_num = 4048

        r_val = self.rating.value.strip()
        num_stars = int(r_val) if r_val.isdigit() and 1 <= int(r_val) <= 5 else 5
        stars_str = EMOJI_STAR * num_stars

        embed_vouch = discord.Embed(
            title=f"{EMOJI_STAR} BUYER VOUCH! #{vouch_num}",
            description=(
                f"{EMOJI_USER} **User :** {interaction.user.mention}\n"
                f"{EMOJI_PRODUCT} **Product :** `{self.product_name.value}`\n"
                f"{EMOJI_RATING} **Rating :** {stars_str}\n\n"
                f"```\n{self.review.value}\n```"
            ),
            color=0x2b2d31
        )
        if interaction.user.display_avatar:
            embed_vouch.set_thumbnail(url=interaction.user.display_avatar.url)

        if vouch_channel:
            await vouch_channel.send(embed=embed_vouch)

        with open("vouch_counter.json", "w") as f:
            json.dump({"count": vouch_num + 1}, f)

        await interaction.response.send_message("✅ Terima kasih! Ulasan kamu berhasil dikirim ke server. 🎉", ephemeral=True)


class DMVouchView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    @discord.ui.button(label="Beri Ulasan / Feedback", style=discord.ButtonStyle.primary, emoji="📝", custom_id="btn_dm_vouch")
    async def btn_vouch(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VouchModal(guild_id=self.guild_id))


# ==========================================
# TOMBOL TUTUP TIKET (AUTO-UPDATE STATUS FAILED GIF)
# ==========================================
class CloseTicketView(discord.ui.View):
    def __init__(self, buyer: discord.User):
        super().__init__(timeout=None)
        self.buyer = buyer

    @discord.ui.button(label="Tutup Tiket", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel_id_str = str(interaction.channel.id)

        try:
            with open("active_orders.json", "r") as f:
                active_orders = json.load(f)

            if channel_id_str in active_orders:
                order_info = active_orders[channel_id_str]

                if order_info.get("status") != "Success":
                    log_channel = interaction.guild.get_channel(ORDER_LOG_CHANNEL_ID)
                    if log_channel:
                        try:
                            log_msg = await log_channel.fetch_message(order_info["msg_id"])
                            buyer = interaction.guild.get_member(order_info["buyer_id"]) or await interaction.client.fetch_user(order_info["buyer_id"])
                            buyer_mention = buyer.mention if buyer else f"<@{order_info['buyer_id']}>"

                            embed_failed = discord.Embed(
                                title="🛒 ORDER LOGS 🛒",
                                description=(
                                    f"Order logs ke #{order_info['log_num']}\n\n"
                                    f"{EMOJI_USER} **User :** {buyer_mention}\n"
                                    f"{EMOJI_PRODUCT} **Product :** `{order_info['product']}`\n"
                                    f"{EMOJI_STATUS} **Status :** `Failed` {STATUS_FAILED}\n"
                                    f"{EMOJI_PRICE} **Price :** `Cancelled`\n"
                                    f"{EMOJI_CATEGORY} **Category :** `{order_info['category']}`"
                                ),
                                color=0x2b2d31
                            )
                            embed_failed.set_footer(text="Thankyou for shopping in KENKAISUU STORE!")
                            if buyer and buyer.display_avatar:
                                embed_failed.set_thumbnail(url=buyer.display_avatar.url)

                            await log_msg.edit(embed=embed_failed)
                        except Exception as e:
                            print(f"Gagal update log ke Failed: {e}")

                del active_orders[channel_id_str]
                with open("active_orders.json", "w") as f:
                    json.dump(active_orders, f)
        except FileNotFoundError:
            pass

        try:
            view = DMVouchView(guild_id=interaction.guild.id)
            await self.buyer.send(
                "💬 **Terima kasih telah berbelanja!**\n"
                "Transaksi kamu telah selesai. Silakan klik tombol di bawah ini untuk memberikan ulasan kamu ya: ✨",
                view=view
            )
        except discord.Forbidden:
            pass

        await interaction.response.send_message("🔒 Tiket telah ditutup. Channel ini akan dihapus dalam 3 detik...", ephemeral=True)
        await asyncio.sleep(3)
        await interaction.channel.delete()


# ==========================================
# KOMPONEN UI UNTUK PING & ROBLOX
# ==========================================
class PingView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Uji Ulang Latensi", style=discord.ButtonStyle.primary, emoji="🔄")
    async def refresh_ping(self, interaction: discord.Interaction, button: discord.ui.Button):
        ws_latency = round(self.bot.latency * 1000)
        status = "🟢 Sangat Lancar" if ws_latency < 100 else ("🟡 Cukup Baik" if ws_latency < 200 else "🔴 Lambat")
        color = discord.Color.green() if ws_latency < 100 else (discord.Color.gold() if ws_latency < 200 else discord.Color.red())

        embed = discord.Embed(
            title="🏓 Pong! Status Koneksi Bot",
            description="Berikut adalah latensi koneksi bot secara *real-time*:",
            color=color
        )
        embed.add_field(name="⚡ Websocket Latency", value=f"`{ws_latency} ms`", inline=True)
        embed.add_field(name="📡 Status Server", value=f"`{status}`", inline=True)

        await interaction.response.edit_message(embed=embed, view=self)


class RobloxView(discord.ui.View):
    def __init__(self, profile_url):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Buka Profil", url=profile_url, emoji="🎮"))


# ==========================================
# PANEL TIKET (ORDER LOG INITIAL STATUS: PENDING GIF)
# ==========================================
class TicketMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def create_ticket_channel(self, interaction: discord.Interaction, tipe: str):
        guild = interaction.guild
        user = interaction.user
        category = guild.get_channel(CATEGORY_MARKET_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        if tipe == "middleman":
            channel_name = f"🤝・ticket-{user.name}-midman"
            prod_name = "Jasa Middleman"
            cat_name = "Manual"
            embed_welcome = discord.Embed(
                title="🤝 TIKET JASA MIDDLEMAN / REKBER",
                description=(
                    f"Halo {user.mention}!\n"
                    f"Silakan cantumkan format transaksi di bawah ini:\n\n"
                    f"• **Penjual & Pembeli:**\n"
                    f"• **Barang / Nominal:**\n"
                    f"• **Nominal Transaksi:**\n\n"
                    f"Admin / Middleman akan segera merespons.\n\n"
                    f"⚠️ *Jika transaksi sudah selesai, klik tombol di bawah untuk menutup tiket.*"
                ),
                color=0x2ecc71
            )
        else:
            channel_name = f"🛒・ticket-{user.name}-visend"
            prod_name = "Robux Visend"
            cat_name = "Manual"
            embed_welcome = discord.Embed(
                title="🎫 TIKET ORDER ROBUX VISEND",
                description=(
                    f"Halo {user.mention}!\n"
                    f"Silakan ketik **Username Roblox** dan nominal Robux yang ingin kamu beli di sini. Admin akan segera merespons.\n\n"
                    f"⚠️ *Jika transaksi sudah selesai, klik tombol di bawah untuk menutup tiket.*"
                ),
                color=0x3498db
            )

        ticket_channel = await guild.create_text_channel(
            name=channel_name, 
            category=category, 
            overwrites=overwrites
        )

        await interaction.response.send_message(
            f"✅ Tiket berhasil dibuat! Silakan buka {ticket_channel.mention} untuk melanjutkan.", 
            ephemeral=True
        )

        view_close = CloseTicketView(buyer=user)
        await ticket_channel.send(f"{user.mention}", embed=embed_welcome, view=view_close)

        try:
            with open("order_log_counter.json", "r") as f:
                data = json.load(f)
                log_num = data.get("count", 4048)
        except FileNotFoundError:
            log_num = 4048

        log_channel = guild.get_channel(ORDER_LOG_CHANNEL_ID)

        embed_log = discord.Embed(
            title="🛒 ORDER LOGS 🛒",
            description=(
                f"Order logs ke #{log_num}\n\n"
                f"{EMOJI_USER} **User :** {user.mention}\n"
                f"{EMOJI_PRODUCT} **Product :** `{prod_name}`\n"
                f"{EMOJI_STATUS} **Status :** `Pending` {STATUS_PENDING}\n"
                f"{EMOJI_PRICE} **Price :** `Pending`\n"
                f"{EMOJI_CATEGORY} **Category :** `{cat_name}`"
            ),
            color=0x2b2d31
        )
        embed_log.set_footer(text="Thankyou for shopping in KENKAISUU STORE!")
        if user.display_avatar:
            embed_log.set_thumbnail(url=user.display_avatar.url)

        if log_channel:
            log_msg = await log_channel.send(embed=embed_log)

            try:
                with open("active_orders.json", "r") as f:
                    active_orders = json.load(f)
            except FileNotFoundError:
                active_orders = {}

            active_orders[str(ticket_channel.id)] = {
                "msg_id": log_msg.id,
                "buyer_id": user.id,
                "product": prod_name,
                "category": cat_name,
                "log_num": log_num,
                "status": "Pending"
            }

            with open("active_orders.json", "w") as f:
                json.dump(active_orders, f)

        with open("order_log_counter.json", "w") as f:
            json.dump({"count": log_num + 1}, f)

    @discord.ui.button(label="Robux Visend", style=discord.ButtonStyle.primary, custom_id="btn_visend", emoji=EMOJI_ROBUX)
    async def btn_visend(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket_channel(interaction, "visend")

    @discord.ui.button(label="Middleman", style=discord.ButtonStyle.primary, custom_id="btn_middleman", emoji=EMOJI_MIDDLEMAN)
    async def btn_middleman(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket_channel(interaction, "middleman")


# ==========================================
# EVENT & SLASH COMMAND SYNC
# ==========================================
@bot.event
async def on_ready():
    bot.add_view(TicketMenu())
    try:
        guild = discord.Object(id=GUILD_ID)

        bot.tree.copy_global_to(guild=guild)
        bot.tree.clear_commands(guild=None)

        await bot.tree.sync(guild=None)
        synced = await bot.tree.sync(guild=guild)

        print(f"✅ Berhasil! {len(synced)} Slash Command aktif tepat 1 di server! 🚀")
    except Exception as e:
        print(f"❌ Gagal Sync Slash Command: {e}")
    print(f'🤖 Bot {bot.user} berhasil online! ✨')


# ==========================================
# SLASH COMMAND (/TESTI) - HIGH RES GRID EMBED
# ==========================================
@bot.tree.command(name="testi", description="Kirim testimoni transaksi baru ke channel testimoni")
@app_commands.describe(
    buyer="Pilih Pembeli/Customer",
    produk="Nama Produk (contoh: Robux Visend / Middleman)",
    harga="Harga (contoh: 150.000)",
    foto_1="Foto Bukti 1 (Utama)",
    foto_2="Foto Bukti 2 (Opsional)",
    vouch="Vouch / Catatan Tambahan (Opsional)"
)
async def slash_testi(
    interaction: discord.Interaction,
    buyer: discord.Member,
    produk: str,
    harga: str,
    foto_1: discord.Attachment,
    foto_2: discord.Attachment = None,
    vouch: str = "-"
):
    await interaction.response.defer(ephemeral=True)

    testi_channel = interaction.guild.get_channel(TESTIMONY_CHANNEL_ID)
    if not testi_channel:
        await interaction.followup.send("❌ Channel testimoni tidak ditemukan! Pastikan ID channel sudah benar.", ephemeral=True)
        return

    try:
        with open("testi_data.json", "r") as f:
            testi_num = json.load(f).get("count", 1684)
    except FileNotFoundError:
        testi_num = 1684

    formatted_price = harga if harga.lower().startswith("rp") else f"Rp {harga}"
    vouch_display = f"`{vouch}`" if vouch != "-" else "-"

    GRID_URL = "https://discord.com"

    embed1 = discord.Embed(
        url=GRID_URL,
        description=(
            f"# `TESTIMONI #{testi_num}`\n\n"
            f"{EMOJI_USER} **Buyer :** {buyer.mention}\n"
            f"{EMOJI_PRODUCT} **Product :** {produk}\n"
            f"{EMOJI_PRICE} **Price :** `{formatted_price}`\n"
            f"🌸 **Vouch :** {vouch_display}\n"
            f"{EMOJI_RATING} **Reviews :** `#{testi_num}`"
        ),
        color=0x2b2d31
    )

    file1 = await foto_1.to_file(filename="bukti1.png")
    files = [file1]
    embed1.set_image(url="attachment://bukti1.png")

    embeds = [embed1]

    if foto_2:
        file2 = await foto_2.to_file(filename="bukti2.png")
        files.append(file2)
        
        embed2 = discord.Embed(url=GRID_URL, color=0x2b2d31)
        embed2.set_image(url="attachment://bukti2.png")
        embeds.append(embed2)

    await testi_channel.send(embeds=embeds, files=files)

    with open("testi_data.json", "w") as f:
        json.dump({"count": testi_num + 1}, f)

    await interaction.followup.send(f"✅ Testimoni berhasil dikirim dengan gambar jernih ke {testi_channel.mention}! 🎉", ephemeral=True)


# ==========================================
# PREFIX COMMANDS (!done, !ping, !roblox, !setuptiket)
# ==========================================
@bot.command(name="done")
@commands.has_permissions(administrator=True)
async def done_command(ctx, *, harga: str = None):
    if not harga:
        await ctx.send("❌ Format salah! Ketik seperti ini: `!done 16.000` atau `!done Rp 16.000`")
        return

    channel_id_str = str(ctx.channel.id)

    try:
        with open("active_orders.json", "r") as f:
            active_orders = json.load(f)
    except FileNotFoundError:
        active_orders = {}

    if channel_id_str not in active_orders:
        await ctx.send("❌ Perintah ini hanya bisa digunakan di dalam channel tiket yang masih aktif!")
        return

    order_info = active_orders[channel_id_str]
    log_channel = ctx.guild.get_channel(ORDER_LOG_CHANNEL_ID)

    if not log_channel:
        await ctx.send("❌ Channel Order Log tidak ditemukan!")
        return

    try:
        log_msg = await log_channel.fetch_message(order_info["msg_id"])
        buyer = ctx.guild.get_member(order_info["buyer_id"]) or await bot.fetch_user(order_info["buyer_id"])

        formatted_price = harga if harga.lower().startswith("rp") else f"Rp {harga}"
        buyer_mention = buyer.mention if buyer else f"<@{order_info['buyer_id']}>"

        embed_updated = discord.Embed(
            title="🛒 ORDER LOGS 🛒",
            description=(
                f"Order logs ke #{order_info['log_num']}\n\n"
                f"{EMOJI_USER} **User :** {buyer_mention}\n"
                f"{EMOJI_PRODUCT} **Product :** `{order_info['product']}`\n"
                f"{EMOJI_STATUS} **Status :** `Succes` {STATUS_SUCCESS}\n"
                f"{EMOJI_PRICE} **Price :** `{formatted_price}`\n"
                f"{EMOJI_CATEGORY} **Category :** `{order_info['category']}`"
            ),
            color=0x2b2d31
        )
        embed_updated.set_footer(text="Thankyou for shopping in KENKAISUU STORE!")
        if buyer and buyer.display_avatar:
            embed_updated.set_thumbnail(url=buyer.display_avatar.url)

        await log_msg.edit(embed=embed_updated)

        active_orders[channel_id_str]["status"] = "Success"
        with open("active_orders.json", "w") as f:
            json.dump(active_orders, f)

        await ctx.send(f"✅ Order log berhasil diperbarui menjadi **Succes** {STATUS_SUCCESS} dengan harga **{formatted_price}**! ✨")

    except discord.NotFound:
        await ctx.send("❌ Pesan Order Log awal tidak ditemukan di channel history!")
    except Exception as e:
        await ctx.send(f"❌ Terjadi kesalahan: {e}")

@bot.command()
async def ping(ctx):
    ws_latency = round(bot.latency * 1000)
    status = "🟢 Sangat Lancar" if ws_latency < 100 else ("🟡 Cukup Baik" if ws_latency < 200 else "🔴 Lambat")
    color = discord.Color.green() if ws_latency < 100 else (discord.Color.gold() if ws_latency < 200 else discord.Color.red())

    embed = discord.Embed(title="🏓 Pong! Status Koneksi Bot", description="Berikut adalah latensi koneksi bot saat ini:", color=color)
    embed.add_field(name="⚡ Websocket Latency", value=f"`{ws_latency} ms`", inline=True)
    embed.add_field(name="📡 Status Server", value=f"`{status}`", inline=True)

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

    created_raw = details.get("created", "")
    if created_raw:
        created_dt = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - created_dt
        years, remaining_days = delta.days // 365, delta.days % 365
        months, days = remaining_days // 30, remaining_days % 30
        usia_str = f"{years} Tahun {months} Bulan {days} Hari"
        created_fmt = created_dt.strftime("%m/%d/%Y jam %H:%M:%S")
    else:
        usia_str = created_fmt = "Tidak diketahui"

    profile_url = f"https://www.roblox.com/users/{user_id}/profile"

    embed = discord.Embed(title="🎮 Profil Roblox", description="📋 **Informasi Akun Roblox**", color=0x2b2d31)
    embed.add_field(name="#️⃣ Nama Pengguna", value=name, inline=True)
    embed.add_field(name="🏷️ Nama Tampilan", value=display_name, inline=True)
    embed.add_field(name="🆔 ID Pengguna", value=str(user_id), inline=True)
    embed.add_field(name="✅ Status", value=status_str, inline=True)
    embed.add_field(name="👤 Pengikut", value=str(followers), inline=True)
    embed.add_field(name="🤝 Teman", value=str(friends), inline=True)
    embed.add_field(name="➡️ Mengikuti", value=str(following), inline=True)
    embed.add_field(name="🏰 Grup", value=str(groups_count), inline=True)
    embed.add_field(name="🥇 Lencana", value="0", inline=True)
    embed.add_field(name="⏳ Usia Akun", value=usia_str, inline=False)
    embed.add_field(name="📅 Tanggal Dibuat", value=created_fmt, inline=False)
    embed.add_field(name="📝 Deskripsi", value=f"> {bio}", inline=False)

    if avatar_url:
        embed.set_thumbnail(url=avatar_url)

    embed.set_footer(text=f"Dibuat oleh {ctx.author.name} • {datetime.now().strftime('%m/%d/%y, %I:%M %p')}")

    view = RobloxView(profile_url)
    await ctx.send(embed=embed, view=view)

@bot.command()
@commands.has_permissions(administrator=True)
async def setuptiket(ctx):
    embed = discord.Embed(
        title=f"{EMOJI_ROBUX} ROBUX VIA USERNAME", 
        color=0x2b2d31
    )
    embed.add_field(
        name=f"{EMOJI_PRICELIST} __PRICELIST ROBUX VIA USERNAME__",
        value=(
            f"• 100 {EMOJI_ROBUX} — `Rp16.000`\n"
            f"• 200 {EMOJI_ROBUX} — `Rp32.000`\n"
            f"• 300 {EMOJI_ROBUX} — `Rp48.000`\n"
            f"• 400 {EMOJI_ROBUX} — `Rp64.000`\n"
            f"• 500 {EMOJI_ROBUX} — `Rp80.000`\n"
            f"• 1000 {EMOJI_ROBUX} — `Rp160.000`"
        ),
        inline=False
    )
    embed.add_field(
        name="\u200b",
        value="✦ *Rate 160 / Robux*\n✦ *Proses cepat, cukup cantumkan Username Roblox*",
        inline=False
    )

    await ctx.send(embed=embed, view=TicketMenu())
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

# Token Bot
bot.run('MTU0MTYzMzg4MDk1MDMwODk2NA.GCxSOm.5qZuaoUECiaFd3lvMm9q4RedVcy4wbaq_tOQ8M')