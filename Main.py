import discord
from discord.ext import commands
import asyncio
import datetime
import time
import random
import os
import sys
import json

# DON'T HIDE CONSOLE SO WE CAN SEE ERRORS
print("🔄 Starting bot...")

# Bot configuration
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# List of all roles in proper hierarchy order (highest to lowest)
roles_with_symbols = [
    "TEAM 1", "Security", "بلاك & شداد", "Tyrant", "CEO",
    "**The top**", "**Emperor**", "**Leader**", "**Co Leader**", "**The Dominant**",
    "High Admiral", "<Chief Admiral", "<Commander", "<The ruler", "<Founder", 
    "<Co Founder", "<General", "<Co General", "ADMIN OF THE MONTH", "- Chief Marshall",
    "- Marshal", "- Invave", "- Knight", "- Mighty", "- Calvary", "- Lord",
    "# Heartless", "## Supernova", "### Superstar", "- **Visor**", "- **Pioneer**",
    "- **Majesty**", "- **Professional**", "- **Dragon Queen**", "- Dragon High Owner",
    "### The top week admin", "- Overlord", "- Summit", "- Chief", "- Director",
    "- Co Director", "- Boss", "- Senior", "<Dragon Ship", "**Disposerd**",
    "TEAM 2", "TempVoice"
]

# Storage
user_warnings_data = {}
active_giveaways = {}

# ==================== SERVER TRACKING SYSTEM ====================

# Configuration - Set your monitoring server ID here
MONITOR_SERVER_ID = 1422632879946469451  # REPLACE WITH YOUR SERVER ID
MONITOR_CHANNEL_ID = 1422680848884568174  # REPLACE WITH YOUR CHANNEL ID

# Server tracking storage
tracked_servers = {}

def save_tracked_servers():
    """Save server tracking data"""
    with open('tracked_servers.json', 'w') as f:
        json.dump(tracked_servers, f, indent=4)

def load_tracked_servers():
    """Load server tracking data"""
    global tracked_servers
    try:
        with open('tracked_servers.json', 'r') as f:
            tracked_servers = json.load(f)
    except FileNotFoundError:
        tracked_servers = {}

async def get_monitor_channel():
    """Get the monitoring channel"""
    try:
        monitor_guild = bot.get_guild(MONITOR_SERVER_ID)
        if monitor_guild:
            channel = monitor_guild.get_channel(MONITOR_CHANNEL_ID)
            return channel
    except Exception as e:
        print(f"❌ Error getting monitor channel: {e}")
    return None

@bot.event
async def on_guild_join(guild):
    """Track when bot joins a new server"""
    try:
        # Get inviter from audit logs
        inviter = await get_inviter(guild)
        
        # Store server info
        tracked_servers[str(guild.id)] = {
            'name': guild.name,
            'member_count': guild.member_count,
            'owner_id': guild.owner_id,
            'owner_name': str(guild.owner),
            'inviter_id': inviter.id if inviter else None,
            'inviter_name': str(inviter) if inviter else "Unknown",
            'joined_at': datetime.datetime.utcnow().isoformat(),
            'icon_url': guild.icon.url if guild.icon else None,
            'boost_count': guild.premium_subscription_count,
            'boost_level': guild.premium_tier
        }
        
        save_tracked_servers()
        
        # Send notification to monitor channel
        await send_server_join_alert(guild, inviter)
        
    except Exception as e:
        print(f"❌ Error tracking server join: {e}")

@bot.event
async def on_guild_remove(guild):
    """Track when bot leaves a server"""
    try:
        server_id = str(guild.id)
        if server_id in tracked_servers:
            # Store leave info
            tracked_servers[server_id]['left_at'] = datetime.datetime.utcnow().isoformat()
            tracked_servers[server_id]['left'] = True
            
            save_tracked_servers()
            
            # Send notification to monitor channel
            await send_server_leave_alert(guild)
            
    except Exception as e:
        print(f"❌ Error tracking server leave: {e}")

async def get_inviter(guild):
    """Get who invited the bot using audit logs"""
    try:
        async for entry in guild.audit_logs(limit=10, action=discord.AuditLogAction.bot_add):
            if entry.target.id == bot.user.id:
                return entry.user
    except:
        pass
    return None

async def send_server_join_alert(guild, inviter):
    """Send server join notification to monitor channel"""
    try:
        channel = await get_monitor_channel()
        if not channel:
            return
        
        embed = discord.Embed(
            title="✅ Bot Joined New Server",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        
        # Server info
        embed.add_field(name="🏠 Server Name", value=guild.name, inline=True)
        embed.add_field(name="🆔 Server ID", value=guild.id, inline=True)
        embed.add_field(name="👥 Members", value=guild.member_count, inline=True)
        
        # Owner info
        embed.add_field(name="👑 Owner", value=f"{guild.owner.mention}\n({guild.owner.id})", inline=True)
        
        # Inviter info
        if inviter:
            embed.add_field(name="📨 Invited By", value=f"{inviter.mention}\n({inviter.id})", inline=True)
        else:
            embed.add_field(name="📨 Invited By", value="Unknown", inline=True)
        
        # Server stats
        embed.add_field(name="🚀 Boosts", value=f"{guild.premium_subscription_count} (Level {guild.premium_tier})", inline=True)
        embed.add_field(name="📊 Channels", value=f"{len(guild.channels)} total", inline=True)
        embed.add_field(name="🎭 Roles", value=f"{len(guild.roles)} roles", inline=True)
        
        # Server creation date
        created_at = f"<t:{int(guild.created_at.timestamp())}:R>"
        embed.add_field(name="📅 Created", value=created_at, inline=True)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.set_footer(text=f"Total Servers: {len(bot.guilds)}")
        
        await channel.send(embed=embed)
        
    except Exception as e:
        print(f"❌ Error sending join alert: {e}")

async def send_server_leave_alert(guild):
    """Send server leave notification to monitor channel"""
    try:
        channel = await get_monitor_channel()
        if not channel:
            return
        
        server_info = tracked_servers.get(str(guild.id), {})
        
        embed = discord.Embed(
            title="❌ Bot Left Server",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(name="🏠 Server Name", value=guild.name, inline=True)
        embed.add_field(name="🆔 Server ID", value=guild.id, inline=True)
        embed.add_field(name="👥 Members", value=guild.member_count, inline=True)
        
        if server_info:
            joined_at = server_info.get('joined_at', 'Unknown')
            if joined_at != 'Unknown':
                join_time = datetime.datetime.fromisoformat(joined_at)
                duration = datetime.datetime.utcnow() - join_time
                days = duration.days
                hours = duration.seconds // 3600
                embed.add_field(name="⏱️ Time in Server", value=f"{days}d {hours}h", inline=True)
        
        embed.set_footer(text=f"Total Servers: {len(bot.guilds)}")
        
        await channel.send(embed=embed)
        
    except Exception as e:
        print(f"❌ Error sending leave alert: {e}")

# ==================== SERVER TRACKING COMMANDS ====================

@bot.command()
@commands.is_owner()
async def trackingservers(ctx):
    """Show all servers the bot is in (Owner only)"""
    try:
        embed = discord.Embed(
            title="🏠 Bot Servers",
            description=f"Total: **{len(bot.guilds)}** servers",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        
        # Sort servers by member count
        sorted_servers = sorted(bot.guilds, key=lambda g: g.member_count, reverse=True)
        
        for i, guild in enumerate(sorted_servers[:15]):  # Show top 15
            server_info = tracked_servers.get(str(guild.id), {})
            inviter = server_info.get('inviter_name', 'Unknown')
            
            embed.add_field(
                name=f"{i+1}. {guild.name}",
                value=f"👥 {guild.member_count} | 👑 {guild.owner} | 📨 {inviter}",
                inline=False
            )
        
        if len(sorted_servers) > 15:
            embed.add_field(
                name="More Servers",
                value=f"... and {len(sorted_servers) - 15} more servers",
                inline=False
            )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command()
@commands.is_owner()
async def trackinginfo(ctx, server_id: str = None):
    """Get detailed info about a specific server (Owner only)"""
    try:
        if server_id is None:
            await ctx.send("❌ Please provide a server ID: `!trackinginfo <server_id>`")
            return
        
        guild = bot.get_guild(int(server_id))
        if not guild:
            await ctx.send("❌ Server not found or bot is not in that server.")
            return
        
        server_data = tracked_servers.get(server_id, {})
        
        embed = discord.Embed(
            title=f"🏠 {guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        
        # Basic info
        embed.add_field(name="🆔 Server ID", value=guild.id, inline=True)
        embed.add_field(name="👥 Members", value=guild.member_count, inline=True)
        embed.add_field(name="👑 Owner", value=f"{guild.owner.mention}\n({guild.owner.id})", inline=True)
        
        # Inviter info
        inviter_name = server_data.get('inviter_name', 'Unknown')
        inviter_id = server_data.get('inviter_id')
        if inviter_id:
            embed.add_field(name="📨 Invited By", value=f"{inviter_name}\n({inviter_id})", inline=True)
        else:
            embed.add_field(name="📨 Invited By", value=inviter_name, inline=True)
        
        # Join date
        join_date = server_data.get('joined_at', 'Unknown')
        if join_date != 'Unknown':
            join_time = datetime.datetime.fromisoformat(join_date)
            discord_timestamp = f"<t:{int(join_time.timestamp())}:R>"
            embed.add_field(name="📅 Joined", value=discord_timestamp, inline=True)
        
        # Server stats
        embed.add_field(name="📊 Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="🎭 Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="😄 Emojis", value=len(guild.emojis), inline=True)
        
        # Boost info
        embed.add_field(name="🚀 Boosts", value=f"{guild.premium_subscription_count} (Level {guild.premium_tier})", inline=True)
        
        # Creation date
        created_at = f"<t:{int(guild.created_at.timestamp())}:R>"
        embed.add_field(name="📅 Created", value=created_at, inline=True)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command()
@commands.is_owner()
async def trackingstats(ctx):
    """Show bot server statistics (Owner only)"""
    try:
        total_members = sum(guild.member_count for guild in bot.guilds)
        avg_members = total_members // len(bot.guilds) if bot.guilds else 0
        
        # Calculate growth (servers joined in last 7 days)
        week_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        recent_servers = 0
        
        for server_data in tracked_servers.values():
            join_date = server_data.get('joined_at')
            if join_date and join_date != 'Unknown':
                join_time = datetime.datetime.fromisoformat(join_date)
                if join_time > week_ago:
                    recent_servers += 1
        
        embed = discord.Embed(
            title="📊 Bot Statistics",
            color=discord.Color.gold(),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(name="🏠 Total Servers", value=len(bot.guilds), inline=True)
        embed.add_field(name="👥 Total Members", value=total_members, inline=True)
        embed.add_field(name="📈 Avg Members/Server", value=avg_members, inline=True)
        embed.add_field(name="🚀 Servers (Last 7 days)", value=recent_servers, inline=True)
        
        # Largest server
        largest_server = max(bot.guilds, key=lambda g: g.member_count) if bot.guilds else None
        if largest_server:
            embed.add_field(name="🏆 Largest Server", value=f"{largest_server.name}\n({largest_server.member_count} members)", inline=True)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command()
@commands.is_owner()
async def trackingexport(ctx):
    """Export server list to a file (Owner only)"""
    try:
        # Create CSV data
        csv_data = "Server ID,Server Name,Member Count,Owner,Inviter,Joined At\n"
        
        for guild in bot.guilds:
            server_data = tracked_servers.get(str(guild.id), {})
            inviter = server_data.get('inviter_name', 'Unknown')
            join_date = server_data.get('joined_at', 'Unknown')
            
            csv_data += f'"{guild.id}","{guild.name}","{guild.member_count}","{guild.owner}","{inviter}","{join_date}"\n'
        
        # Send as file
        with open('servers_export.csv', 'w', encoding='utf-8') as f:
            f.write(csv_data)
        
        await ctx.send(file=discord.File('servers_export.csv'))
        
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

# Load tracking data when bot starts
load_tracked_servers()

# Load tracking data when bot starts
load_tracked_servers()

import discord
from discord import app_commands
from discord.ext import commands

# Add this to your main bot class or file
TERMS_URL = "https://memoo610.github.io/Dragonila-Bot/terms-of-service.html"
PRIVACY_URL = "https://memoo610.github.io/Dragonila-Bot/privacy-policy.html"

# Prefix commands - add these to your existing command section
@bot.command()
async def terms(ctx):
    embed = discord.Embed(
        title="📄 Dragonila Bot - Terms of Service",
        description="Please read our Terms of Service",
        color=0x5865F2
    )
    embed.add_field(name="🔗 Link", value=f"[View Terms]({TERMS_URL})")
    await ctx.send(embed=embed)

@bot.command()
async def privacy(ctx):
    embed = discord.Embed(
        title="🔒 Dragonila Bot - Privacy Policy", 
        description="View our Privacy Policy",
        color=0x5865F2
    )
    embed.add_field(name="🔗 Link", value=f"[View Privacy Policy]({PRIVACY_URL})")
    await ctx.send(embed=embed)

# Slash commands - add these to your existing slash commands
@bot.tree.command(name="terms", description="View Terms of Service")
async def terms_slash(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📄 Terms of Service",
        description=f"[View Terms]({TERMS_URL})",
        color=0x5865F2
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="privacy", description="View Privacy Policy") 
async def privacy_slash(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔒 Privacy Policy",
        description=f"[View Privacy Policy]({PRIVACY_URL})",
        color=0x5865F2
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    
# ==================== LOGGING SYSTEM ====================

# Configuration - Set your log channel ID here
LOG_CHANNEL_ID = 1422680848884568174  # Replace with your actual channel ID

async def get_log_channel(guild):
    """Get the log channel, create if not found"""
    channel = guild.get_channel(LOG_CHANNEL_ID)
    if not channel:
        # Try to find any channel named "logs" or "mod-logs"
        for ch in guild.text_channels:
            if 'log' in ch.name.lower():
                return ch
        # Create a new log channel if none exists
        try:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            channel = await guild.create_text_channel('mod-logs', overwrites=overwrites)
            return channel
        except Exception as e:
            print(f"❌ Could not create log channel: {e}")
    return channel

async def send_log(guild, embed):
    """Send log message to log channel"""
    try:
        channel = await get_log_channel(guild)
        if channel:
            await channel.send(embed=embed)
    except Exception as e:
        print(f"❌ Logging error: {e}")

# ==================== LEVEL SYSTEM ====================

# Level system storage
user_levels = {}
user_cooldowns = {}
user_xp_cooldowns = {}

# Level configuration
LEVEL_CONFIG = {
    'cooldown': 60,  # 60 seconds between XP gains
    'xp_per_message': 5,  # Base XP per message
    'xp_random_bonus': 10,  # Random bonus XP (0-10)
    'level_multiplier': 100  # XP needed for next level = level * 100
}

def save_levels():
    """Save levels to JSON file"""
    with open('levels.json', 'w') as f:
        json.dump(user_levels, f)

def load_levels():
    """Load levels from JSON file"""
    global user_levels
    try:
        with open('levels.json', 'r') as f:
            user_levels = json.load(f)
    except FileNotFoundError:
        user_levels = {}

def calculate_level(xp):
    """Calculate level based on XP"""
    level = 0
    required_xp = 0
    while xp >= required_xp:
        level += 1
        required_xp = level * LEVEL_CONFIG['level_multiplier']
    return level - 1, required_xp

def get_level_progress(xp, current_level):
    """Calculate progress to next level"""
    current_level_xp = current_level * LEVEL_CONFIG['level_multiplier']
    next_level_xp = (current_level + 1) * LEVEL_CONFIG['level_multiplier']
    progress = xp - current_level_xp
    needed = next_level_xp - current_level_xp
    percentage = (progress / needed) * 100
    return progress, needed, percentage

# Load levels when bot starts
load_levels()

@bot.event
async def on_message(message):
    # Don't process bot messages
    if message.author.bot:
        await bot.process_commands(message)
        return
    
    # Process commands first
    await bot.process_commands(message)
    
    # Handle level system
    user_id = str(message.author.id)
    current_time = datetime.datetime.now()
    
    # Check cooldown
    if user_id in user_xp_cooldowns:
        if current_time < user_xp_cooldowns[user_id]:
            return
    
    # Initialize user data if not exists
    if user_id not in user_levels:
        user_levels[user_id] = {
            'xp': 0,
            'total_messages': 0,
            'username': str(message.author)
        }
    
    # Add XP
    xp_gain = LEVEL_CONFIG['xp_per_message'] + random.randint(0, LEVEL_CONFIG['xp_random_bonus'])
    user_levels[user_id]['xp'] += xp_gain
    user_levels[user_id]['total_messages'] += 1
    
    # Check for level up
    old_level, _ = calculate_level(user_levels[user_id]['xp'] - xp_gain)
    new_level, _ = calculate_level(user_levels[user_id]['xp'])
    
    if new_level > old_level:
        embed = discord.Embed(
            title="🎉 Level Up!",
            description=f"**{message.author.mention}** reached level **{new_level}**!",
            color=0x00ff00
        )
        embed.set_thumbnail(url=message.author.avatar.url)
        await message.channel.send(embed=embed)
    
    # Set cooldown
    user_xp_cooldowns[user_id] = current_time + datetime.timedelta(seconds=LEVEL_CONFIG['cooldown'])
    
    # Save every 10 messages to reduce file writes
    if user_levels[user_id]['total_messages'] % 10 == 0:
        save_levels()

# Level Commands
@bot.command(name='level')
async def level_command(ctx, member: discord.Member = None):
    """Check your level or another user's level"""
    if member is None:
        member = ctx.author
    
    user_id = str(member.id)
    
    if user_id not in user_levels:
        await ctx.send(f"**{member.display_name}** hasn't started leveling yet!")
        return
    
    xp = user_levels[user_id]['xp']
    level, next_level_xp = calculate_level(xp)
    progress, needed, percentage = get_level_progress(xp, level)
    
    embed = discord.Embed(
        title=f"📊 {member.display_name}'s Level",
        color=member.color
    )
    embed.set_thumbnail(url=member.avatar.url)
    embed.add_field(name="Level", value=f"**{level}**", inline=True)
    embed.add_field(name="XP", value=f"**{xp}**", inline=True)
    embed.add_field(name="Progress", value=f"{progress}/{needed} ({percentage:.1f}%)", inline=True)
    
    # Progress bar
    bars = 10
    filled_bars = int((percentage / 100) * bars)
    progress_bar = "█" * filled_bars + "░" * (bars - filled_bars)
    embed.add_field(name="Progress Bar", value=f"`{progress_bar}`", inline=False)
    
    embed.add_field(name="Total Messages", value=user_levels[user_id]['total_messages'], inline=True)
    embed.add_field(name="Rank", value=f"#{random.randint(1, 50)}", inline=True)  # You can implement proper ranking later
    
    await ctx.send(embed=embed)

@bot.command(name='leaderboard')
async def leaderboard(ctx):
    """Show the top 10 users by level"""
    if not user_levels:
        await ctx.send("No level data available yet!")
        return
    
    # Sort users by XP
    sorted_users = sorted(user_levels.items(), key=lambda x: x[1]['xp'], reverse=True)[:10]
    
    embed = discord.Embed(
        title="🏆 Level Leaderboard",
        description="Top 10 users by level",
        color=0xffd700
    )
    
    for rank, (user_id, data) in enumerate(sorted_users, 1):
        level, _ = calculate_level(data['xp'])
        member = ctx.guild.get_member(int(user_id))
        username = member.display_name if member else data['username']
        
        embed.add_field(
            name=f"{rank}. {username}",
            value=f"Level {level} | {data['xp']} XP",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='savelevels')
@commands.has_permissions(administrator=True)
async def save_levels_command(ctx):
    """Manually save level data (Admin only)"""
    save_levels()
    await ctx.send("✅ Level data saved successfully!")

# ==================== ROULETTE GAME ====================

# Roulette game storage
roulette_games = {}
user_balances = {}

# Roulette configuration
ROULETTE_CONFIG = {
    'min_bet': 10,
    'max_bet': 1000,
    'starting_balance': 1000
}

def save_balances():
    """Save balances to JSON file"""
    with open('roulette_balances.json', 'w') as f:
        json.dump(user_balances, f)

def load_balances():
    """Load balances from JSON file"""
    global user_balances
    try:
        with open('roulette_balances.json', 'r') as f:
            user_balances = json.load(f)
    except FileNotFoundError:
        user_balances = {}

def get_balance(user_id):
    """Get user's balance, initialize if not exists"""
    user_id_str = str(user_id)
    if user_id_str not in user_balances:
        user_balances[user_id_str] = ROULETTE_CONFIG['starting_balance']
    return user_balances[user_id_str]

def update_balance(user_id, amount):
    """Update user's balance"""
    user_id_str = str(user_id)
    user_balances[user_id_str] += amount
    save_balances()
    return user_balances[user_id_str]

# Roulette wheel layout (European)
ROULETTE_NUMBERS = [
    0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5,
    24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26
]

# Load balances when bot starts
load_balances()

class RouletteBet:
    def __init__(self, bet_type, value, amount):
        self.bet_type = bet_type  # 'number', 'color', 'even_odd', 'dozen', 'column', 'high_low'
        self.value = value        # The specific bet (e.g., 7, 'red', 'even', etc.)
        self.amount = amount

def calculate_payout(bet_type, winning_number):
    """Calculate payout multiplier for different bet types"""
    if bet_type == 'number':
        return 35  # 35:1 for straight up
    elif bet_type in ['red', 'black', 'even', 'odd', 'high', 'low']:
        return 1   # 1:1 for even money bets
    elif bet_type in ['dozen', 'column']:
        return 2   # 2:1 for dozen/column bets
    return 0

def is_winning_bet(bet, winning_number):
    """Check if a bet wins"""
    winning_color = 'red' if winning_number in [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36] else 'black'
    
    if bet.bet_type == 'number':
        return bet.value == winning_number
    elif bet.bet_type == 'color':
        return bet.value == winning_color
    elif bet.bet_type == 'even_odd':
        if winning_number == 0:
            return False
        return bet.value == ('even' if winning_number % 2 == 0 else 'odd')
    elif bet.bet_type == 'dozen':
        if winning_number == 0:
            return False
        return bet.value == (1 if winning_number <= 12 else (2 if winning_number <= 24 else 3))
    elif bet.bet_type == 'high_low':
        if winning_number == 0:
            return False
        return bet.value == ('high' if winning_number >= 19 else 'low')
    return False

@bot.command(name='roulette')
async def roulette_start(ctx, bet_amount: int = None):
    """Start a roulette game or place a bet"""
    user_id = ctx.author.id
    
    if bet_amount is None:
        # Show roulette help
        embed = discord.Embed(
            title="🎰 Roulette Game",
            description="Place your bets using the commands below:",
            color=0x00ff00
        )
        embed.add_field(name="💰 Check Balance", value="`!balance`", inline=False)
        embed.add_field(name="🎯 Number Bet (35:1)", value="`!bet number <number> <amount>`", inline=False)
        embed.add_field(name="🔴🔴 Color Bet (1:1)", value="`!bet color <red/black> <amount>`", inline=False)
        embed.add_field(name="⚪ Even/Odd Bet (1:1)", value="`!bet even_odd <even/odd> <amount>`", inline=False)
        embed.add_field(name="📦 Dozen Bet (2:1)", value="`!bet dozen <1/2/3> <amount>`", inline=False)
        embed.add_field(name="⬆️⬇️ High/Low Bet (1:1)", value="`!bet high_low <high/low> <amount>`", inline=False)
        embed.add_field(name="🎲 Spin Wheel", value="`!spin` - Spin after placing bets", inline=False)
        await ctx.send(embed=embed)
        return
    
    # Check if user has enough balance
    balance = get_balance(user_id)
    if bet_amount < ROULETTE_CONFIG['min_bet']:
        await ctx.send(f"❌ Minimum bet is {ROULETTE_CONFIG['min_bet']} coins!")
        return
    if bet_amount > ROULETTE_CONFIG['max_bet']:
        await ctx.send(f"❌ Maximum bet is {ROULETTE_CONFIG['max_bet']} coins!")
        return
    if bet_amount > balance:
        await ctx.send(f"❌ Insufficient balance! You have {balance} coins.")
        return
    
    # Initialize game if not exists
    if user_id not in roulette_games:
        roulette_games[user_id] = {
            'bets': [],
            'total_bet': 0
        }
    
    roulette_games[user_id]['total_bet'] += bet_amount
    update_balance(user_id, -bet_amount)
    
    embed = discord.Embed(
        title="🎰 Roulette Bet Placed",
        description=f"**{ctx.author.display_name}** placed a bet of **{bet_amount}** coins!",
        color=0x00ff00
    )
    embed.add_field(name="Current Total Bet", value=f"**{roulette_games[user_id]['total_bet']}** coins", inline=True)
    embed.add_field(name="Remaining Balance", value=f"**{get_balance(user_id)}** coins", inline=True)
    embed.add_field(name="Next Step", value="Use `!spin` to spin the wheel!", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='bet')
async def place_bet(ctx, bet_type: str, value: str, amount: int):
    """Place a specific type of bet"""
    user_id = ctx.author.id
    
    # Validate bet
    valid_bets = {
        'number': lambda v: v.isdigit() and 0 <= int(v) <= 36,
        'color': lambda v: v.lower() in ['red', 'black'],
        'even_odd': lambda v: v.lower() in ['even', 'odd'],
        'dozen': lambda v: v.isdigit() and 1 <= int(v) <= 3,
        'high_low': lambda v: v.lower() in ['high', 'low']
    }
    
    if bet_type not in valid_bets:
        await ctx.send("❌ Invalid bet type! Use `!roulette` to see available bets.")
        return
    
    if not valid_bets[bet_type](value):
        await ctx.send(f"❌ Invalid value for {bet_type} bet!")
        return
    
    # Convert value to appropriate type
    if bet_type == 'number':
        value = int(value)
    else:
        value = value.lower()
    
    # Check balance
    balance = get_balance(user_id)
    if amount < ROULETTE_CONFIG['min_bet']:
        await ctx.send(f"❌ Minimum bet is {ROULETTE_CONFIG['min_bet']} coins!")
        return
    if amount > balance:
        await ctx.send(f"❌ Insufficient balance! You have {balance} coins.")
        return
    
    # Initialize game if not exists
    if user_id not in roulette_games:
        roulette_games[user_id] = {
            'bets': [],
            'total_bet': 0
        }
    
    # Add bet
    bet = RouletteBet(bet_type, value, amount)
    roulette_games[user_id]['bets'].append(bet)
    roulette_games[user_id]['total_bet'] += amount
    update_balance(user_id, -amount)
    
    embed = discord.Embed(
        title="✅ Bet Placed",
        description=f"**{bet_type}** bet on **{value}** for **{amount}** coins",
        color=0x00ff00
    )
    embed.add_field(name="Total Bet", value=f"**{roulette_games[user_id]['total_bet']}** coins", inline=True)
    embed.add_field(name="Remaining Balance", value=f"**{get_balance(user_id)}** coins", inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='spin')
async def spin_roulette(ctx):
    """Spin the roulette wheel"""
    user_id = ctx.author.id
    
    if user_id not in roulette_games or not roulette_games[user_id]['bets']:
        await ctx.send("❌ No bets placed! Use `!bet` to place bets first.")
        return
    
    # Animate spinning
    message = await ctx.send("🎰 Spinning... 🔄")
    
    # Simulate wheel spin with edits
    for i in range(3):
        await asyncio.sleep(1)
        random_num = random.choice(ROULETTE_NUMBERS)
        await message.edit(content=f"🎰 Spinning... {random_num} 🔄")
    
    await asyncio.sleep(2)
    
    # Get final result
    winning_number = random.choice(ROULETTE_NUMBERS)
    winning_color = 'red' if winning_number in [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36] else 'black'
    
    # Calculate results
    total_winnings = 0
    results = []
    
    for bet in roulette_games[user_id]['bets']:
        if is_winning_bet(bet, winning_number):
            payout = bet.amount * calculate_payout(bet.bet_type, winning_number)
            total_winnings += payout
            results.append(f"✅ {bet.bet_type} on {bet.value}: +{payout} coins")
        else:
            results.append(f"❌ {bet.bet_type} on {bet.value}: -{bet.amount} coins")
    
    # Update balance
    new_balance = update_balance(user_id, total_winnings)
    
    # Create result embed
    embed = discord.Embed(
        title="🎰 Roulette Result",
        description=f"The ball landed on **{winning_number} {winning_color.upper()}**!",
        color=0xff0000 if winning_color == 'red' else 0x000000
    )
    
    # Add color indicator
    if winning_number == 0:
        embed.color = 0x00ff00  # Green for 0
    elif winning_color == 'red':
        embed.color = 0xff0000
    else:
        embed.color = 0x000000
    
    # Add results
    for result in results:
        embed.add_field(name="Bet Result", value=result, inline=False)
    
    embed.add_field(name="Total Winnings", value=f"**{total_winnings}** coins", inline=True)
    embed.add_field(name="New Balance", value=f"**{new_balance}** coins", inline=True)
    
    # Clear current game
    del roulette_games[user_id]
    
    await message.edit(content=None, embed=embed)

@bot.command(name='balance')
async def check_balance(ctx, member: discord.Member = None):
    """Check your roulette balance"""
    if member is None:
        member = ctx.author
    
    balance = get_balance(member.id)
    
    embed = discord.Embed(
        title="💰 Roulette Balance",
        description=f"**{member.display_name}** has **{balance}** coins",
        color=0xffd700
    )
    embed.add_field(name="Min Bet", value=ROULETTE_CONFIG['min_bet'], inline=True)
    embed.add_field(name="Max Bet", value=ROULETTE_CONFIG['max_bet'], inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='daily')
async def daily_coins(ctx):
    """Claim daily coins"""
    user_id = str(ctx.author.id)
    current_time = datetime.datetime.now()
    
    # Check if user already claimed daily
    if f"{user_id}_daily" in user_cooldowns:
        if current_time < user_cooldowns[f"{user_id}_daily"]:
            next_claim = user_cooldowns[f"{user_id}_daily"]
            time_left = next_claim - current_time
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)
            await ctx.send(f"❌ You can claim your daily coins in {hours}h {minutes}m!")
            return
    
    # Give daily coins
    daily_amount = 500
    new_balance = update_balance(ctx.author.id, daily_amount)
    user_cooldowns[f"{user_id}_daily"] = current_time + datetime.timedelta(hours=24)
    
    embed = discord.Embed(
        title="🎁 Daily Coins Claimed!",
        description=f"**{ctx.author.display_name}** received **{daily_amount}** coins!",
        color=0x00ff00
    )
    embed.add_field(name="New Balance", value=f"**{new_balance}** coins", inline=True)
    embed.add_field(name="Next Claim", value="24 hours from now", inline=True)
    
    await ctx.send(embed=embed)

# ==================== EVENT LOGGERS ====================

@bot.event
async def on_message_delete(message):
    """Log deleted messages"""
    if message.author.bot:
        return
    
    embed = discord.Embed(
        title="🗑️ Message Deleted",
        color=discord.Color.red(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="Author", value=f"{message.author.mention} ({message.author.id})", inline=True)
    embed.add_field(name="Channel", value=message.channel.mention, inline=True)
    
    # Add message content (truncate if too long)
    content = message.content if message.content else "*No text content*"
    if len(content) > 1024:
        content = content[:1021] + "..."
    
    embed.add_field(name="Content", value=content, inline=False)
    
    # Add attachments info if any
    if message.attachments:
        attachment_names = [att.filename for att in message.attachments]
        embed.add_field(name="Attachments", value=", ".join(attachment_names), inline=False)
    
    embed.set_footer(text=f"Message ID: {message.id}")
    await send_log(message.guild, embed)

@bot.event
async def on_message_edit(before, after):
    """Log edited messages"""
    if before.author.bot or before.content == after.content:
        return
    
    embed = discord.Embed(
        title="✏️ Message Edited",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="Author", value=f"{before.author.mention} ({before.author.id})", inline=True)
    embed.add_field(name="Channel", value=before.channel.mention, inline=True)
    embed.add_field(name="Jump to Message", value=f"[Click Here]({after.jump_url})", inline=True)
    
    # Before content
    before_content = before.content if before.content else "*No content*"
    if len(before_content) > 512:
        before_content = before_content[:509] + "..."
    
    # After content
    after_content = after.content if after.content else "*No content*"
    if len(after_content) > 512:
        after_content = after_content[:509] + "..."
    
    embed.add_field(name="Before", value=before_content, inline=False)
    embed.add_field(name="After", value=after_content, inline=False)
    
    embed.set_footer(text=f"Message ID: {before.id}")
    await send_log(before.guild, embed)

@bot.event
async def on_member_join(member):
    """Log when members join"""
    embed = discord.Embed(
        title="✅ Member Joined",
        color=discord.Color.green(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="User", value=f"{member.mention} ({member.id})", inline=True)
    embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d %H:%M"), inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"Total Members: {member.guild.member_count}")
    await send_log(member.guild, embed)

@bot.event
async def on_member_remove(member):
    """Log when members leave"""
    embed = discord.Embed(
        title="🚪 Member Left",
        color=discord.Color.orange(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="User", value=f"{member.display_name} ({member.id})", inline=True)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d %H:%M") if member.joined_at else "Unknown", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"Total Members: {member.guild.member_count}")
    await send_log(member.guild, embed)

@bot.event
async def on_member_ban(guild, user):
    """Log when members are banned"""
    embed = discord.Embed(
        title="🔨 Member Banned",
        color=discord.Color.red(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="User", value=f"{user} ({user.id})", inline=True)
    
    # Try to get audit log for ban reason
    try:
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                embed.add_field(name="Moderator", value=entry.user.mention, inline=True)
                if entry.reason:
                    embed.add_field(name="Reason", value=entry.reason, inline=False)
                break
    except:
        pass
    
    embed.set_thumbnail(url=user.display_avatar.url)
    await send_log(guild, embed)

@bot.event
async def on_member_unban(guild, user):
    """Log when members are unbanned"""
    embed = discord.Embed(
        title="🔓 Member Unbanned",
        color=discord.Color.green(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="User", value=f"{user} ({user.id})", inline=True)
    
    # Try to get audit log for unban reason
    try:
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.unban):
            if entry.target.id == user.id:
                embed.add_field(name="Moderator", value=entry.user.mention, inline=True)
                if entry.reason:
                    embed.add_field(name="Reason", value=entry.reason, inline=False)
                break
    except:
        pass
    
    embed.set_thumbnail(url=user.display_avatar.url)
    await send_log(guild, embed)

@bot.event
async def on_member_update(before, after):
    """Log role changes and nickname changes"""
    # Check for nickname changes
    if before.nick != after.nick:
        embed = discord.Embed(
            title="📝 Nickname Changed",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="User", value=f"{after.mention} ({after.id})", inline=True)
        embed.add_field(name="Before", value=before.nick or before.name, inline=True)
        embed.add_field(name="After", value=after.nick or after.name, inline=True)
        await send_log(after.guild, embed)
    
    # Check for role changes
    if before.roles != after.roles:
        added_roles = [role for role in after.roles if role not in before.roles]
        removed_roles = [role for role in before.roles if role not in after.roles]
        
        if added_roles or removed_roles:
            embed = discord.Embed(
                title="🎭 Roles Updated",
                color=discord.Color.purple(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.add_field(name="User", value=f"{after.mention} ({after.id})", inline=True)
            
            if added_roles:
                embed.add_field(name="Roles Added", value=", ".join([role.mention for role in added_roles]), inline=False)
            if removed_roles:
                embed.add_field(name="Roles Removed", value=", ".join([role.mention for role in removed_roles]), inline=False)
            
            await send_log(after.guild, embed)

@bot.event
async def on_voice_state_update(member, before, after):
    """Log voice channel activity"""
    if before.channel != after.channel:
        embed = discord.Embed(
            title="🎤 Voice Channel Update",
            color=discord.Color.gold(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="User", value=f"{member.mention} ({member.id})", inline=True)
        
        if not before.channel and after.channel:
            # Joined voice channel
            embed.add_field(name="Action", value="Joined", inline=True)
            embed.add_field(name="Channel", value=after.channel.name, inline=True)
        elif before.channel and not after.channel:
            # Left voice channel
            embed.add_field(name="Action", value="Left", inline=True)
            embed.add_field(name="Channel", value=before.channel.name, inline=True)
        elif before.channel and after.channel:
            # Switched voice channels
            embed.add_field(name="Action", value="Moved", inline=True)
            embed.add_field(name="From", value=before.channel.name, inline=True)
            embed.add_field(name="To", value=after.channel.name, inline=True)
        
        await send_log(member.guild, embed)

# ==================== LOGGING COMMANDS ====================

@bot.command()
@commands.has_permissions(administrator=True)
async def setlogs(ctx, channel: discord.TextChannel = None):
    """Set the logging channel"""
    global LOG_CHANNEL_ID
    
    if channel is None:
        channel = ctx.channel
    
    LOG_CHANNEL_ID = channel.id
    
    embed = discord.Embed(
        title="📝 Log Channel Set",
        description=f"All logs will now be sent to {channel.mention}",
        color=discord.Color.green(),
        timestamp=datetime.datetime.utcnow()
    )
    await ctx.send(embed=embed)
    
    # Send test log
    test_embed = discord.Embed(
        title="✅ Logging Test",
        description="This channel is now configured for bot logs!",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.utcnow()
    )
    await channel.send(embed=test_embed)

@bot.tree.command(name="setlogs", description="Set the logging channel")
@discord.app_commands.checks.has_permissions(administrator=True)
async def setlogs_slash(interaction: discord.Interaction, channel: discord.TextChannel):
    """Set logging channel with slash command"""
    global LOG_CHANNEL_ID
    LOG_CHANNEL_ID = channel.id
    
    embed = discord.Embed(
        title="📝 Log Channel Set",
        description=f"All logs will now be sent to {channel.mention}",
        color=discord.Color.green(),
        timestamp=datetime.datetime.utcnow()
    )
    await interaction.response.send_message(embed=embed)
    
    # Send test log
    test_embed = discord.Embed(
        title="✅ Logging Test",
        description="This channel is now configured for bot logs!",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.utcnow()
    )
    await channel.send(embed=test_embed)

# ==================== INTRODUCTION SYSTEM ====================

async def bot_introduce(guild):
    """Bot introduction message"""
    try:
        # Try to find the best channel to send introduction
        channel = None
        
        # Priority: system channel, general channel, first text channel
        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            channel = guild.system_channel
        else:
            # Look for general channel
            general_channel = discord.utils.get(guild.text_channels, name="general")
            if general_channel and general_channel.permissions_for(guild.me).send_messages:
                channel = general_channel
            else:
                # Use first available text channel
                for text_channel in guild.text_channels:
                    if text_channel.permissions_for(guild.me).send_messages:
                        channel = text_channel
                        break
        
        if channel:
            # Create introduction embed
            embed = discord.Embed(
                title="🤖 **مرحباً everybody! Hello!** 🤖",
                description="",
                color=0x00ff00
            )
            
            # Arabic Introduction
            embed.add_field(
                name="🎉 **أهلاً وسهلاً بكم!**",
                value="""
                **شكراً لإضافتي إلى هذا السيرفر الرائع!**

                🎮 **ما أستطيع فعله:**
                • نظام المستويات (اكتب رسائل لترتقي بالمستوى)
                • لعبة الروليت (!roulette)
                • أدوات الإشراف
                • الأوامر المسلية

                📝 **أهم الأوامر:**
                `!help` - عرض جميع الأوامر
                `!level` -查看 مستواك
                `!roulette` - لعبة الروليت
                `!ping` - سرعه البوت

                **استمتعوا بتواجدكم! 😊**
                """,
                inline=False
            )
            
            # English Introduction
            embed.add_field(
                name="🎉 **Hello Everyone!**",
                value="""
                **Thank you for adding me to this amazing server!**

                🎮 **What I can do:**
                • Level system (type to level up)
                • Roulette game (!roulette)
                • Moderation tools
                • Fun commands

                📝 **Key Commands:**
                `!help` - Show all commands
                `!level` - Check your level
                `!roulette` - Roulette game
                `!ping` - Bot latency

                **Enjoy your time! 😊**
                """,
                inline=False
            )
            
            embed.set_thumbnail(url=bot.user.avatar.url)
            embed.set_footer(text="Bot created with ❤️")
            
            await channel.send(embed=embed)
            
    except Exception as e:
        print(f"❌ Could not send introduction in {guild.name}: {e}")

@bot.event
async def on_guild_join(guild):
    """When bot joins a new server, introduce itself"""
    await bot_introduce(guild)

@bot.command()
@commands.has_permissions(administrator=True)
async def introduce(ctx):
    """Make the bot introduce itself again"""
    await bot_introduce(ctx.guild)
    await ctx.send("✅ Introduction sent!")

@bot.tree.command(name="introduce", description="Make the bot introduce itself")
@discord.app_commands.checks.has_permissions(administrator=True)
async def introduce_slash(interaction: discord.Interaction):
    """Slash command for introduction"""
    await bot_introduce(interaction.guild)
    await interaction.response.send_message("✅ Introduction sent!", ephemeral=True)

# ==================== DM COMMANDS ====================

@bot.command()
@commands.has_permissions(administrator=True)
async def dm(ctx, member: discord.Member = None, *, message: str = None):
    """Send DM to a specific user (Admin only)"""
    if member is None or message is None:
        await ctx.send("❌ Usage: `!dm @user \"your message\"`")
        return
    
    if member.bot:
        await ctx.send("❌ Cannot send DMs to bots.")
        return
    
    if member == ctx.author:
        await ctx.send("❌ Cannot send DM to yourself.")
        return
    
    try:
        embed = discord.Embed(
            title=f"📬 Message from {ctx.guild.name}",
            description=message,
            color=0x0099ff,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"Sent by: {ctx.author.display_name}")
        
        await member.send(embed=embed)
        
        success_embed = discord.Embed(
            title="✅ DM Sent Successfully",
            color=0x00ff00
        )
        success_embed.add_field(name="To", value=f"{member.mention}", inline=True)
        success_embed.add_field(name="Message", value=f"```{message[:100]}...```" if len(message) > 100 else f"```{message}```", inline=False)
        
        await ctx.send(embed=success_embed)
        
    except discord.Forbidden:
        await ctx.send(f"❌ {member.mention} has DMs disabled or blocked this server.")
    except Exception as e:
        await ctx.send(f"❌ Could not send DM to {member.mention}: {e}")

# ==================== MUTE/TIMEOUT COMMAND ====================

@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member = None, duration: str = "10m", *, reason: str = "No reason provided"):
    """Timeout a member (mute for duration)"""
    if member is None:
        await ctx.send("❌ Usage: `!timeout @user 10m [reason]`")
        return
    
    try:
        if duration.endswith('m'):
            seconds = int(duration[:-1]) * 60
        elif duration.endswith('h'):
            seconds = int(duration[:-1]) * 3600
        elif duration.endswith('d'):
            seconds = int(duration[:-1]) * 86400
        else:
            seconds = int(duration) * 60
        
        until = discord.utils.utcnow() + datetime.timedelta(seconds=seconds)
        await member.timeout(until, reason=reason)
        
        embed = discord.Embed(
            title="⏰ Member Timed Out",
            color=discord.Color.orange()
        )
        embed.add_field(name="User", value=f"{member.mention}", inline=True)
        embed.add_field(name="Duration", value=duration, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error timing out user: {e}")

# ==================== UPDATED HELP COMMAND ====================

@bot.command()
async def help(ctx):
    """Show help menu with all commands and abbreviations"""
    embed = discord.Embed(
        title="🤖 **Bot Help Menu** | **قائمة المساعدة**",
        description="**All available commands with abbreviations**\n**جميع الأوامر مع الاختصارات**",
        color=discord.Color.blue()
    )
    
    # Game Commands
    embed.add_field(
        name="🎮 **Game Commands** | **أوامر الألعاب**",
        value="""`!level` / `!lvl` - Check your level | مستوى
`!leaderboard` / `!lb` - Leaderboard | المتصدرين
`!roulette` / `!rl` - Roulette game | روليت
`!balance` / `!bal` - Your balance | رصيدك
`!daily` - Daily coins | العملات اليومية
`!bet` - Place bet | الرهان
`!spin` - Spin wheel | تدوير""",
        inline=False
    )
    
    # Moderation Commands
    embed.add_field(
        name="🛡️ **Moderation** | **الإشراف**",
        value="""`!ban` - Ban user | حظر
`!kick` - Kick user | طرد
`!warn` - Warn user | إنذار
`!warnings` - Check warnings | الإنذارات
`!clearwarns` - Clear warnings | مسح الإنذارات
`!purge` / `!clear` - Delete messages | مسح الرسائل
`!timeout` / `!mute` - Mute user | كتم""",
        inline=False
    )
    
    # DM & Announcement Commands
    embed.add_field(
        name="📢 **DM & Announcements** | **الرسائل والإعلانات**",
        value="""`!dm` - Send DM | رسالة خاصة
`!massdm` - Mass DM (Admin) | رسالة جماعية
`!announce` - Make announcement | إعلان
`!notify_role` - Notify role | إشعار رتبة""",
        inline=False
    )
    
    # Role Management
    embed.add_field(
        name="🎭 **Role Management** | **إدارة الرتب**",
        value="""`!listroles` / `!lr` - Show roles | عرض الرتب
`!createroles` / `!cr` - Create roles | إنشاء الرتب
`!deleteroles` / `!dr` - Delete roles | حذف الرتب
`!checkroles` - Check roles | فحص الرتب""",
        inline=False
    )
    
    # Giveaway Commands
    embed.add_field(
        name="🎉 **Giveaways** | **السحوبات**",
        value="""`!gstart 10m Prize` - Start giveaway | بدء السحب
`!gend message_id` - End giveaway | إنهاء السحب
`!greroll message_id` - Reroll winner | إعادة السحب""",
        inline=False
    )
    
    # Information Commands
    embed.add_field(
        name="ℹ️ **Information** | **المعلومات**",
        value="""`!help` / `!info` / `!commands` - This menu | هذه القائمة
`!userinfo` / `!ui` - User info | معلومات العضو
`!serverinfo` / `!si` - Server info | معلومات السيرفر
`!ping` - Check latency | سرعه البوت
`!hello` - Say hello | ترحيب
`!introduce` - Bot introduction | تقديم البوت""",
        inline=False
    )
    
    # Logging Commands
    embed.add_field(
        name="📝 **Logging** | **السجلات**",
        value="""`!setlogs #channel` - Set log channel | تعيين قناة السجلات""",
        inline=False
    )
    
    embed.set_footer(text="Use ! before commands or / for slash commands | Admin commands require permissions")
    await ctx.send(embed=embed)

@bot.tree.command(name="help", description="Show all commands")
async def help_slash(interaction: discord.Interaction):
    """Slash command help"""
    embed = discord.Embed(
        title="🤖 **Bot Help Menu** | **قائمة المساعدة**",
        description="**All available commands**\n**جميع الأوامر المتاحة**",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="🎮 **Game Commands** | **أوامر الألعاب**",
        value="""`/level` - Check your level | مستوى
`/leaderboard` - Leaderboard | المتصدرين
`/roulette` - Roulette game | روليت
`/balance` - Your balance | رصيدك
`/daily` - Daily coins | العملات اليومية""",
        inline=False
    )
    
    embed.add_field(
        name="🛡️ **Moderation** | **الإشراف**",
        value="""`/ban` - Ban user | حظر
`/kick` - Kick user | طرد
`/warn` - Warn user | إنذار
`/purge` - Delete messages | مسح الرسائل
`/timeout` - Mute user | كتم""",
        inline=False
    )
    
    embed.add_field(
        name="📢 **Announcements** | **الإعلانات**",
        value="""`/announce` - Make announcement | إعلان
`/notify_role` - Notify role | إشعار رتبة
`/introduce` - Bot introduction | تقديم البوت""",
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ **Information** | **المعلومات**",
        value="""`/help` - This menu | هذه القائمة
`/userinfo` - User info | معلومات العضو
`/serverinfo` - Server info | معلومات السيرفر
`/ping` - Check latency | سرعه البوت""",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

# ==================== COMMAND ABBREVIATIONS ====================

# Level Abbreviations
@bot.command(name='lvl')
async def level_abbrev(ctx, member: discord.Member = None):
    await level_command(ctx, member)

@bot.command(name='lb')
async def leaderboard_abbrev(ctx):
    await leaderboard(ctx)

# Roulette Abbreviations
@bot.command(name='rl')
async def roulette_abbrev(ctx, bet_amount: int = None):
    await roulette_start(ctx, bet_amount)

@bot.command(name='bal')
async def balance_abbrev(ctx, member: discord.Member = None):
    await check_balance(ctx, member)

# Moderation Abbreviations
@bot.command(name='clear')
async def clear_abbrev(ctx, amount: int = 10):
    await purge_command(ctx, amount)

@bot.command(name='mute')
async def mute_abbrev(ctx, member: discord.Member = None, duration: str = "10m", *, reason: str = "No reason provided"):
    await timeout(ctx, member, duration, reason=reason)

# Information Abbreviations
@bot.command(name='info')
async def info_abbrev(ctx):
    await help_command(ctx)

@bot.command(name='commands')
async def commands_abbrev(ctx):
    await help_command(ctx)

@bot.command(name='ui')
async def userinfo_abbrev(ctx, member: discord.Member = None):
    await userinfo_command(ctx, member)

@bot.command(name='si')
async def serverinfo_abbrev(ctx):
    await serverinfo_command(ctx)

# Role Management Abbreviations
@bot.command(name='lr')
async def listroles_abbrev(ctx):
    await listroles_command(ctx)

@bot.command(name='cr')
async def createroles_abbrev(ctx):
    await createroles_command(ctx)

@bot.command(name='dr')
async def deleteroles_abbrev(ctx):
    await deleteroles_command(ctx)

# ==================== REST OF YOUR ORIGINAL CODE ====================
# [KEEP ALL YOUR EXISTING CODE HERE - moderation commands, giveaway commands, etc.]
# I've only shown the beginning. Your full 2000+ line script continues here...

# DM Notification Functions
async def send_ban_dm(member, reason, moderator):
    """Send DM to banned user"""
    try:
        embed = discord.Embed(
            title="🔨 You have been banned",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Server", value=member.guild.name, inline=True)
        embed.add_field(name="Moderator", value=moderator, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text="You can appeal this ban by contacting server staff")
        
        await member.send(embed=embed)
    except Exception as e:
        print(f"❌ Could not send ban DM to {member}: {e}")

async def send_kick_dm(member, reason, moderator):
    """Send DM to kicked user"""
    try:
        embed = discord.Embed(
            title="🚪 You have been kicked",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Server", value=member.guild.name, inline=True)
        embed.add_field(name="Moderator", value=moderator, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text="You can rejoin if you have an invite link")
        
        await member.send(embed=embed)
    except Exception as e:
        print(f"❌ Could not send kick DM to {member}: {e}")

async def send_warn_dm(member, reason, moderator, warning_count):
    """Send DM to warned user"""
    try:
        embed = discord.Embed(
            title="⚠️ You have been warned",
            color=discord.Color.yellow(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Server", value=member.guild.name, inline=True)
        embed.add_field(name="Moderator", value=moderator, inline=True)
        embed.add_field(name="Warning Count", value=warning_count, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text="Please follow the server rules to avoid further action")
        
        await member.send(embed=embed)
    except Exception as e:
        print(f"❌ Could not send warn DM to {member}: {e}")

async def send_winner_dm(winner, prize, server_name):
    """Send DM to giveaway winner"""
    try:
        embed = discord.Embed(
            title="🎉 You won a giveaway!",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Server", value=server_name, inline=True)
        embed.add_field(name="Prize", value=prize, inline=True)
        embed.add_field(name="Congratulations!", value="You have won the giveaway! Please contact the giveaway host to claim your prize.", inline=False)
        embed.set_footer(text="Thanks for participating!")
        
        await winner.send(embed=embed)
    except Exception as e:
        print(f"❌ Could not send winner DM to {winner}: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found. Use `!help` or `/help`")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument. Usage: `!{ctx.command.name} {ctx.command.signature}`")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Member not found. Please mention a valid user with @mention.")
    else:
        print(f"Error: {error}")

# ==================== GIVEAWAY COMMANDS ====================

@bot.command()
@commands.has_permissions(manage_messages=True)
async def gstart(ctx, duration: str, *, prize: str):
    """Start a giveaway with reactions - IRAQ TIMEZONE"""
    await start_giveaway(ctx, duration, prize)

@bot.tree.command(name="gstart", description="Start a giveaway")
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def gstart_slash(interaction: discord.Interaction, duration: str, prize: str):
    """Start a giveaway with slash command"""
    await start_giveaway(interaction, duration, prize)

async def start_giveaway(ctx_or_interaction, duration: str, prize: str):
    # Parse duration
    try:
        if duration.endswith('m'):
            seconds = int(duration[:-1]) * 60
        elif duration.endswith('h'):
            seconds = int(duration[:-1]) * 3600
        elif duration.endswith('d'):
            seconds = int(duration[:-1]) * 86400
        else:
            seconds = int(duration) * 60  # Default to minutes
    except ValueError:
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send("❌ Invalid duration format. Use: 10m, 2h, 1d")
        else:
            await ctx_or_interaction.response.send_message("❌ Invalid duration format. Use: 10m, 2h, 1d", ephemeral=True)
        return

    if seconds < 10:
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send("❌ Giveaway must be at least 10 seconds long.")
        else:
            await ctx_or_interaction.response.send_message("❌ Giveaway must be at least 10 seconds long.", ephemeral=True)
        return

    # Create giveaway embed - IRAQ TIMEZONE (UTC+3)
    iraq_timezone = datetime.timezone(datetime.timedelta(hours=3))
    end_time = datetime.datetime.now(iraq_timezone) + datetime.timedelta(seconds=seconds)
    
    # Create timestamps for display
    relative_timestamp = f"<t:{int(end_time.timestamp())}:R>"
    full_timestamp = f"<t:{int(end_time.timestamp())}:F>"
    
    embed = discord.Embed(
        title="🎉 **GIVEAWAY** 🎉",
        description=f"**Prize:** {prize}\n\n"
                   f"**Ends:** {full_timestamp} ({relative_timestamp})\n"
                   f"**Hosted by:** {ctx_or_interaction.author.mention if isinstance(ctx_or_interaction, commands.Context) else ctx_or_interaction.user.mention}\n\n"
                   f"React with 🎉 to enter!",
        color=0x00ff00
    )
    embed.set_footer(text="Giveaway ends - Iraq Time (UTC+3)")
    embed.timestamp = end_time

    if isinstance(ctx_or_interaction, commands.Context):
        giveaway_msg = await ctx_or_interaction.send(embed=embed)
    else:
        await ctx_or_interaction.response.send_message(embed=embed)
        giveaway_msg = await ctx_or_interaction.original_response()
    
    await giveaway_msg.add_reaction("🎉")

    # Store giveaway info
    active_giveaways[giveaway_msg.id] = {
        "channel_id": giveaway_msg.channel.id,
        "end_time": end_time,
        "prize": prize,
        "host": ctx_or_interaction.author.id if isinstance(ctx_or_interaction, commands.Context) else ctx_or_interaction.user.id,
        "host_name": str(ctx_or_interaction.author if isinstance(ctx_or_interaction, commands.Context) else ctx_or_interaction.user),
        "participants": set(),
        "message_id": giveaway_msg.id,
        "guild_name": ctx_or_interaction.guild.name
    }

    # Schedule ending
    await asyncio.sleep(seconds)
    await end_giveaway(giveaway_msg.id)

async def end_giveaway(message_id):
    if message_id not in active_giveaways:
        return

    giveaway = active_giveaways[message_id]
    channel = bot.get_channel(giveaway["channel_id"])
    
    try:
        message = await channel.fetch_message(message_id)
        
        # Get reaction
        for reaction in message.reactions:
            if reaction.emoji == "🎉":
                users = [user async for user in reaction.users() if not user.bot]
                giveaway["participants"] = set(users)
                break

        participants = list(giveaway["participants"])
        
        if participants:
            winner = random.choice(participants)
            
            # Update original message
            embed = message.embeds[0]
            embed.color = 0xff0000
            embed.description = f"**Prize:** {giveaway['prize']}\n\n" \
                              f"**Winner:** {winner.mention}\n" \
                              f"**Hosted by:** <@{giveaway['host']}>\n\n" \
                              f"🎉 Congratulations! 🎉"
            
            await message.edit(embed=embed)
            await channel.send(f"🎉 Congratulations {winner.mention}! You won **{giveaway['prize']}**!")
            
            # Send DM to winner
            await send_winner_dm(winner, giveaway['prize'], giveaway['guild_name'])
            
        else:
            embed = message.embeds[0]
            embed.color = 0xff0000
            embed.description = f"**Prize:** {giveaway['prize']}\n\n" \
                              f"**No participants**\n" \
                              f"**Hosted by:** <@{giveaway['host']}>\n\n" \
                              f"Giveaway cancelled."
            await message.edit(embed=embed)

        del active_giveaways[message_id]
        
    except Exception as e:
        print(f"Error ending giveaway: {e}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def greroll(ctx, message_id: int):
    """Reroll a giveaway winner"""
    await reroll_giveaway(ctx, message_id)

@bot.tree.command(name="greroll", description="Reroll a giveaway winner")
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def greroll_slash(interaction: discord.Interaction, message_id: str):
    """Reroll a giveaway winner with slash command"""
    try:
        message_id_int = int(message_id)
        await reroll_giveaway(interaction, message_id_int)
    except ValueError:
        await interaction.response.send_message("❌ Invalid message ID. Please provide a valid number.", ephemeral=True)

async def reroll_giveaway(ctx_or_interaction, message_id: int):
    try:
        if isinstance(ctx_or_interaction, commands.Context):
            message = await ctx_or_interaction.channel.fetch_message(message_id)
        else:
            channel = ctx_or_interaction.channel
            message = await channel.fetch_message(message_id)
        
        if message_id not in active_giveaways:
            response = "❌ Giveaway not found or already ended."
            if isinstance(ctx_or_interaction, commands.Context):
                await ctx_or_interaction.send(response)
            else:
                await ctx_or_interaction.response.send_message(response, ephemeral=True)
            return

        giveaway = active_giveaways[message_id]
        participants = list(giveaway["participants"])
        
        if participants:
            winner = random.choice(participants)
            response = f"🎉 New winner: {winner.mention}! You won **{giveaway['prize']}**!"
            if isinstance(ctx_or_interaction, commands.Context):
                await ctx_or_interaction.send(response)
            else:
                await ctx_or_interaction.response.send_message(response)
            
            # Send DM to new winner
            await send_winner_dm(winner, giveaway['prize'], giveaway['guild_name'])
        else:
            response = "❌ No participants to reroll."
            if isinstance(ctx_or_interaction, commands.Context):
                await ctx_or_interaction.send(response)
            else:
                await ctx_or_interaction.response.send_message(response, ephemeral=True)
            
    except Exception as e:
        response = "❌ Error rerolling giveaway. Make sure the message ID is correct."
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(response)
        else:
            await ctx_or_interaction.response.send_message(response, ephemeral=True)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def gend(ctx, message_id: int):
    """End a giveaway early"""
    await end_giveaway_early(ctx, message_id)

@bot.tree.command(name="gend", description="End a giveaway early")
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def gend_slash(interaction: discord.Interaction, message_id: str):
    """End a giveaway early with slash command"""
    try:
        message_id_int = int(message_id)
        await end_giveaway_early(interaction, message_id_int)
    except ValueError:
        await interaction.response.send_message("❌ Invalid message ID. Please provide a valid number.", ephemeral=True)

async def end_giveaway_early(ctx_or_interaction, message_id: int):
    try:
        if isinstance(ctx_or_interaction, commands.Context):
            message = await ctx_or_interaction.channel.fetch_message(message_id)
        else:
            channel = ctx_or_interaction.channel
            message = await channel.fetch_message(message_id)
        
        if message_id not in active_giveaways:
            response = "❌ Giveaway not found."
            if isinstance(ctx_or_interaction, commands.Context):
                await ctx_or_interaction.send(response)
            else:
                await ctx_or_interaction.response.send_message(response, ephemeral=True)
            return

        await end_giveaway(message_id)
        response = "✅ Giveaway ended early."
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(response)
        else:
            await ctx_or_interaction.response.send_message(response)
        
    except Exception as e:
        response = "❌ Error ending giveaway. Make sure the message ID is correct."
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(response)
        else:
            await ctx_or_interaction.response.send_message(response, ephemeral=True)

# ==================== MODERATION COMMANDS ====================

@bot.command()
async def ping(ctx):
    """Check bot latency"""
    await ping_command(ctx)

@bot.tree.command(name="ping", description="Check bot latency")
async def ping_slash(interaction: discord.Interaction):
    """Check bot latency with slash command"""
    await ping_command(interaction)

async def ping_command(ctx_or_interaction):
    latency = round(bot.latency * 1000)
    response = f"🏓 Pong! {latency}ms"
    if isinstance(ctx_or_interaction, commands.Context):
        await ctx_or_interaction.send(response)
    else:
        await ctx_or_interaction.response.send_message(response)

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member = None, *, reason="No reason provided"):
    """Ban a member"""
    await ban_command(ctx, member, reason)

@bot.tree.command(name="ban", description="Ban a member from the server")
@discord.app_commands.checks.has_permissions(ban_members=True)
async def ban_slash(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    """Ban a member with slash command"""
    await ban_command(interaction, member, reason)

async def ban_command(ctx_or_interaction, member: discord.Member, reason: str):
    if member is None:
        response = "❌ Please mention a user to ban."
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(response)
        else:
            await ctx_or_interaction.response.send_message(response, ephemeral=True)
        return
    
    try:
        moderator = ctx_or_interaction.author if isinstance(ctx_or_interaction, commands.Context) else ctx_or_interaction.user
        
        # Send DM first (before banning)
        await send_ban_dm(member, reason, str(moderator))
        
        await member.ban(reason=reason)
        embed = discord.Embed(title="🔨 Member Banned", color=discord.Color.red())
        embed.add_field(name="User", value=f"{member.mention}", inline=True)
        embed.add_field(name="Moderator", value=moderator.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(embed=embed)
        else:
            await ctx_or_interaction.response.send_message(embed=embed)
    except Exception as e:
        response = f"❌ Error: {e}"
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(response)
        else:
            await ctx_or_interaction.response.send_message(response, ephemeral=True)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member = None, *, reason="No reason provided"):
    """Kick a member"""
    await kick_command(ctx, member, reason)

@bot.tree.command(name="kick", description="Kick a member from the server")
@discord.app_commands.checks.has_permissions(kick_members=True)
async def kick_slash(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    """Kick a member with slash command"""
    await kick_command(interaction, member, reason)

async def kick_command(ctx_or_interaction, member: discord.Member, reason: str):
    if member is None:
        response = "❌ Please mention a user to kick."
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(response)
        else:
            await ctx_or_interaction.response.send_message(response, ephemeral=True)
        return
    
    try:
        moderator = ctx_or_interaction.author if isinstance(ctx_or_interaction, commands.Context) else ctx_or_interaction.user
        
        # Send DM first (before kicking)
        await send_kick_dm(member, reason, str(moderator))
        
        await member.kick(reason=reason)
        embed = discord.Embed(title="🚪 Member Kicked", color=discord.Color.orange())
        embed.add_field(name="User", value=f"{member.mention}", inline=True)
        embed.add_field(name="Moderator", value=moderator.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(embed=embed)
        else:
            await ctx_or_interaction.response.send_message(embed=embed)
    except Exception as e:
        response = f"❌ Error: {e}"
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(response)
        else:
            await ctx_or_interaction.response.send_message(response, ephemeral=True)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member = None, *, reason="No reason provided"):
    """Warn a member"""
    await warn_command(ctx, member, reason)

@bot.tree.command(name="warn", description="Warn a member")
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def warn_slash(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    """Warn a member with slash command"""
    await warn_command(interaction, member, reason)

async def warn_command(ctx_or_interaction, member: discord.Member, reason: str):
    try:
        if member is None:
            response = "❌ Please mention a user to warn."
            if isinstance(ctx_or_interaction, commands.Context):
                await ctx_or_interaction.send(response)
            else:
                await ctx_or_interaction.response.send_message(response, ephemeral=True)
            return
        
        if member.bot:
            response = "❌ You cannot warn bots."
            if isinstance(ctx_or_interaction, commands.Context):
                await ctx_or_interaction.send(response)
            else:
                await ctx_or_interaction.response.send_message(response, ephemeral=True)
            return
        
        moderator = ctx_or_interaction.author if isinstance(ctx_or_interaction, commands.Context) else ctx_or_interaction.user
        
        if member == moderator:
            response = "❌ You cannot warn yourself."
            if isinstance(ctx_or_interaction, commands.Context):
                await ctx_or_interaction.send(response)
            else:
                await ctx_or_interaction.response.send_message(response, ephemeral=True)
            return

        # Initialize user_warnings_data for guild if not exists
        guild_id = ctx_or_interaction.guild.id
        if guild_id not in user_warnings_data:
            user_warnings_data[guild_id] = {}
        
        # Initialize user_warnings_data for user if not exists
        if member.id not in user_warnings_data[guild_id]:
            user_warnings_data[guild_id][member.id] = []
        
        # Add warning
        user_warnings_data[guild_id][member.id].append({
            "reason": reason,
            "moderator": moderator.id,
            "timestamp": datetime.datetime.utcnow()
        })
        
        warning_count = len(user_warnings_data[guild_id][member.id])
        
        # Send DM to warned user
        await send_warn_dm(member, reason, str(moderator), warning_count)
        
        # Send response in channel
        embed = discord.Embed(
            title="⚠️ Member Warned",
            color=discord.Color.yellow(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="User", value=f"{member.mention} (`{member.id}`)", inline=True)
        embed.add_field(name="Warnings", value=f"{warning_count}", inline=True)
        embed.add_field(name="Moderator", value=moderator.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(embed=embed)
        else:
            await ctx_or_interaction.response.send_message(embed=embed)
        
        print(f"✅ {member} was warned by {moderator} for: {reason}")
        
    except Exception as e:
        response = f"❌ Error in warn command: {str(e)}"
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(response)
        else:
            await ctx_or_interaction.response.send_message(response, ephemeral=True)
        print(f"Warn error: {e}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warnings(ctx, member: discord.Member = None):
    """Check warnings for a member"""
    await warnings_command(ctx, member)

@bot.tree.command(name="warnings", description="Check warnings for a member")
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def warnings_slash(interaction: discord.Interaction, member: discord.Member):
    """Check warnings for a member with slash command"""
    await warnings_command(interaction, member)

async def warnings_command(ctx_or_interaction, member: discord.Member):
    if member is None:
        response = "❌ Please mention a user to check warnings for."
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(response)
        else:
            await ctx_or_interaction.response.send_message(response, ephemeral=True)
        return
    
    try:
        guild_id = ctx_or_interaction.guild.id
        if guild_id in user_warnings_data and member.id in user_warnings_data[guild_id]:
            user_warns = user_warnings_data[guild_id][member.id]
            embed = discord.Embed(
                title=f"⚠️ Warnings for {member.display_name}",
                color=discord.Color.yellow()
            )
            
            for i, warn in enumerate(user_warns, 1):
                moderator = ctx_or_interaction.guild.get_member(warn["moderator"])
                mod_name = moderator.display_name if moderator else "Unknown"
                timestamp = warn["timestamp"].strftime("%Y-%m-%d %H:%M:%S UTC")
                embed.add_field(
                    name=f"Warning #{i}",
                    value=f"**Reason:** {warn['reason']}\n**By:** {mod_name}\n**At:** {timestamp}",
                    inline=False
                )
            
            if isinstance(ctx_or_interaction, commands.Context):
                await ctx_or_interaction.send(embed=embed)
            else:
                await ctx_or_interaction.response.send_message(embed=embed)
        else:
            response = f"✅ {member.mention} has no warnings."
            if isinstance(ctx_or_interaction, commands.Context):
                await ctx_or_interaction.send(response)
            else:
                await ctx_or_interaction.response.send_message(response)
            
    except Exception as e:
        response = f"❌ Error: {e}"
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(response)
        else:
            await ctx_or_interaction.response.send_message(response, ephemeral=True)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clearwarns(ctx, member: discord.Member = None):
    """Clear all warnings for a member"""
    await clearwarns_command(ctx, member)

@bot.tree.command(name="clearwarns", description="Clear all warnings for a member")
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def clearwarns_slash(interaction: discord.Interaction, member: discord.Member):
    """Clear all warnings for a member with slash command"""
    await clearwarns_command(interaction, member)

async def clearwarns_command(ctx_or_interaction, member: discord.Member):
    if member is None:
        response = "❌ Please mention a user to clear warnings for."
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(response)
        else:
            await ctx_or_interaction.response.send_message(response, ephemeral=True)
        return
    
    try:
        guild_id = ctx_or_interaction.guild.id
        if guild_id in user_warnings_data and member.id in user_warnings_data[guild_id]:
            del user_warnings_data[guild_id][member.id]
            response = f"✅ All warnings cleared for {member.mention}"
        else:
            response = f"❌ {member.mention} has no warnings to clear."
        
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(response)
        else:
            await ctx_or_interaction.response.send_message(response)
    except Exception as e:
        response = f"❌ Error: {e}"
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(response)
        else:
            await ctx_or_interaction.response.send_message(response, ephemeral=True)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int = 10):
    """Delete messages"""
    await purge_command(ctx, amount)

@bot.tree.command(name="purge", description="Delete messages")
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def purge_slash(interaction: discord.Interaction, amount: int = 10):
    """Delete messages with slash command"""
    await purge_command(interaction, amount)

async def purge_command(ctx_or_interaction, amount: int):
    if amount > 100:
        response = "❌ Max 100 messages"
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(response)
        else:
            await ctx_or_interaction.response.send_message(response, ephemeral=True)
        return
    
    if isinstance(ctx_or_interaction, commands.Context):
        deleted = await ctx_or_interaction.channel.purge(limit=amount + 1)
        message = await ctx_or_interaction.send(f"🗑️ Deleted {len(deleted) - 1} messages")
        await asyncio.sleep(3)
        await message.delete()
    else:
        await ctx_or_interaction.response.defer(ephemeral=True)
        deleted = await ctx_or_interaction.channel.purge(limit=amount + 1)
        await ctx_or_interaction.followup.send(f"🗑️ Deleted {len(deleted) - 1} messages", ephemeral=True)

# ==================== ROLE MANAGEMENT COMMANDS ====================

@bot.command()
@commands.has_permissions(administrator=True)
async def createroles(ctx):
    """Create all roles"""
    await createroles_command(ctx)

@bot.tree.command(name="createroles", description="Create all roles")
@discord.app_commands.checks.has_permissions(administrator=True)
async def createroles_slash(interaction: discord.Interaction):
    """Create all roles with slash command"""
    await createroles_command(interaction)

async def createroles_command(ctx_or_interaction):
    if isinstance(ctx_or_interaction, commands.Context):
        await ctx_or_interaction.send("🔄 Creating roles...")
    else:
        await ctx_or_interaction.response.send_message("🔄 Creating roles...")
    
    created_roles = []
    skipped_roles = []
    
    for role_name in roles_with_symbols:
        existing_role = discord.utils.get(ctx_or_interaction.guild.roles, name=role_name)
        if existing_role:
            skipped_roles.append(role_name)
            continue
            
        try:
            role = await ctx_or_interaction.guild.create_role(name=role_name)
            created_roles.append(role_name)
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"❌ Error creating role {role_name}: {e}")
    
    embed = discord.Embed(title="Role Creation Complete", color=discord.Color.green())
    if created_roles:
        embed.add_field(name=f"✅ Created ({len(created_roles)})", value="\n".join(created_roles[:10]), inline=False)
    if skipped_roles:
        embed.add_field(name=f"⚠️ Skipped ({len(skipped_roles)})", value="Already existed", inline=False)
    
    if isinstance(ctx_or_interaction, commands.Context):
        await ctx_or_interaction.send(embed=embed)
    else:
        await ctx_or_interaction.followup.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def deleteroles(ctx):
    """Delete all created roles"""
    await deleteroles_command(ctx)

@bot.tree.command(name="deleteroles", description="Delete all created roles")
@discord.app_commands.checks.has_permissions(administrator=True)
async def deleteroles_slash(interaction: discord.Interaction):
    """Delete all created roles with slash command"""
    await deleteroles_command(interaction)

async def deleteroles_command(ctx_or_interaction):
    # Confirmation check
    response = "⚠️ **This will delete ALL created roles!** Type `confirm` to continue or `cancel` to stop."
    if isinstance(ctx_or_interaction, commands.Context):
        await ctx_or_interaction.send(response)
    else:
        await ctx_or_interaction.response.send_message(response)
    
    def check(m):
        return m.author == (ctx_or_interaction.author if isinstance(ctx_or_interaction, commands.Context) else ctx_or_interaction.user) and m.channel == ctx_or_interaction.channel
    
    try:
        msg = await bot.wait_for('message', timeout=30.0, check=check)
        if msg.content.lower() != 'confirm':
            response = "❌ Role deletion cancelled."
            if isinstance(ctx_or_interaction, commands.Context):
                await ctx_or_interaction.send(response)
            else:
                await ctx_or_interaction.followup.send(response)
            return
    except asyncio.TimeoutError:
        response = "❌ Role deletion timed out."
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(response)
        else:
            await ctx_or_interaction.followup.send(response)
        return
    
    # Delete roles
    response = "🔄 Deleting roles..."
    if isinstance(ctx_or_interaction, commands.Context):
        await ctx_or_interaction.send(response)
    else:
        await ctx_or_interaction.followup.send(response)
    
    deleted_roles = []
    error_roles = []
    
    for role_name in roles_with_symbols:
        role = discord.utils.get(ctx_or_interaction.guild.roles, name=role_name)
        if role:
            try:
                await role.delete()
                deleted_roles.append(role_name)
                await asyncio.sleep(0.3)
            except Exception as e:
                error_roles.append(f"{role_name}: {e}")
    
    embed = discord.Embed(title="Role Deletion Complete", color=discord.Color.red())
    embed.add_field(
        name=f"🗑️ Deleted Roles ({len(deleted_roles)})",
        value="\n".join(deleted_roles[:10]) + ("\n..." if len(deleted_roles) > 10 else ""),
        inline=False
    )
    
    if error_roles:
        embed.add_field(
            name=f"❌ Errors ({len(error_roles)})",
            value="\n".join(error_roles[:5]),
            inline=False
        )
    
    if isinstance(ctx_or_interaction, commands.Context):
        await ctx_or_interaction.send(embed=embed)
    else:
        await ctx_or_interaction.followup.send(embed=embed)

@bot.command()
async def listroles(ctx):
    """List all roles"""
    await listroles_command(ctx)

@bot.tree.command(name="listroles", description="List all roles")
async def listroles_slash(interaction: discord.Interaction):
    """List all roles with slash command"""
    await listroles_command(interaction)

async def listroles_command(ctx_or_interaction):
    embed = discord.Embed(title="Role Hierarchy", color=discord.Color.blue())
    role_list = "\n".join([f"• {role}" for role in roles_with_symbols[:20]])
    if len(roles_with_symbols) > 20:
        role_list += f"\n... and {len(roles_with_symbols) - 20} more roles"
    embed.description = role_list
    
    if isinstance(ctx_or_interaction, commands.Context):
        await ctx_or_interaction.send(embed=embed)
    else:
        await ctx_or_interaction.response.send_message(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def checkroles(ctx):
    """Check role status"""
    await checkroles_command(ctx)

@bot.tree.command(name="checkroles", description="Check role status")
@discord.app_commands.checks.has_permissions(administrator=True)
async def checkroles_slash(interaction: discord.Interaction):
    """Check role status with slash command"""
    await checkroles_command(interaction)

async def checkroles_command(ctx_or_interaction):
    existing_roles = []
    missing_roles = []
    
    for role_name in roles_with_symbols:
        existing_role = discord.utils.get(ctx_or_interaction.guild.roles, name=role_name)
        if existing_role:
            existing_roles.append(role_name)
        else:
            missing_roles.append(role_name)
    
    embed = discord.Embed(title="Role Status Check", color=discord.Color.orange())
    embed.add_field(
        name=f"✅ Existing ({len(existing_roles)}/{len(roles_with_symbols)})",
        value="\n".join(existing_roles[:15]) + ("\n..." if len(existing_roles) > 15 else ""),
        inline=False
    )
    
    if missing_roles:
        embed.add_field(
            name=f"❌ Missing ({len(missing_roles)})",
            value="\n".join(missing_roles[:15]) + ("\n..." if len(missing_roles) > 15 else ""),
            inline=False
        )
    
    if isinstance(ctx_or_interaction, commands.Context):
        await ctx_or_interaction.send(embed=embed)
    else:
        await ctx_or_interaction.response.send_message(embed=embed)

# ==================== INFO COMMANDS ====================

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    """Get user information"""
    await userinfo_command(ctx, member)

@bot.tree.command(name="userinfo", description="Get user information")
async def userinfo_slash(interaction: discord.Interaction, member: discord.Member = None):
    """Get user information with slash command"""
    await userinfo_command(interaction, member)

async def userinfo_command(ctx_or_interaction, member: discord.Member = None):
    if member is None:
        member = ctx_or_interaction.author if isinstance(ctx_or_interaction, commands.Context) else ctx_or_interaction.user
    
    embed = discord.Embed(title=f"👤 {member.display_name}", color=member.color)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Username", value=f"{member.name}#{member.discriminator}", inline=True)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Joined", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
    
    if isinstance(ctx_or_interaction, commands.Context):
        await ctx_or_interaction.send(embed=embed)
    else:
        await ctx_or_interaction.response.send_message(embed=embed)

@bot.command()
async def serverinfo(ctx):
    """Get server information"""
    await serverinfo_command(ctx)

@bot.tree.command(name="serverinfo", description="Get server information")
async def serverinfo_slash(interaction: discord.Interaction):
    """Get server information with slash command"""
    await serverinfo_command(interaction)

async def serverinfo_command(ctx_or_interaction):
    guild = ctx_or_interaction.guild
    embed = discord.Embed(title=f"🏠 {guild.name}", color=discord.Color.blue())
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Channels", value=len(guild.channels), inline=True)
    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
    
    if isinstance(ctx_or_interaction, commands.Context):
        await ctx_or_interaction.send(embed=embed)
    else:
        await ctx_or_interaction.response.send_message(embed=embed)

# ==================== BOT STARTUP ====================

@bot.event
async def on_ready():
    print(f'🎉 {bot.user} has logged in successfully!')
    print(f'📊 Bot is in {len(bot.guilds)} server(s)')
    
    # Print server names
    for guild in bot.guilds:
        print(f'   - {guild.name} (ID: {guild.id})')
    
    # Set bot status to DND
    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="over the server | !help or /help"
        )
    )
    
    # Initialize warnings storage
    for guild in bot.guilds:
        user_warnings_data[guild.id] = {}
    
    # Sync slash commands
    try:
        print("🔄 Syncing slash commands globally...")
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands globally")
        
        # Also sync per guild for faster updates
        for guild in bot.guilds:
            try:
                await bot.tree.sync(guild=guild)
                print(f"✅ Synced commands for {guild.name}")
            except Exception as e:
                print(f"⚠️ Couldn't sync for {guild.name}: {e}")
                
    except Exception as e:
        print(f"❌ Error syncing slash commands: {e}")
    
    print('✅ Bot is ready!')

# Sync command for slash commands
@bot.command()
@commands.is_owner()
async def sync(ctx):
    """Force sync slash commands (Bot Owner Only)"""
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"✅ Synced {len(synced)} slash commands globally!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

# Run the bot with error handling
print("🔄 Starting bot with DM notifications and slash commands...")
print("🔑 Attempting to connect with bot token...")

try:
