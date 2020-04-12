# bot.py
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

import game
import roles

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

bot = commands.Bot(command_prefix = '!')



@bot.event
async def on_ready():
    print(f'{bot.user} is connected to the following guild(s):\n')
    for guild in bot.guilds:
        print(f'{guild.name}(id: {guild.id})')


game = game.Game()

########### Bot Commands Start Here ###########


###Start Game###

@bot.command(name='start-game', help='Initiate the game. Players can !in to join afterwards.')
async def start_game(ctx):
    author = ctx.author.name
    channel = ctx.channel
    await game.start(author, channel)
    await roles.establishRoles()


###Join Game###

@bot.command(name='in', help='Join the currently running game.')
async def join_game(ctx):
    if await game.checkIfStarted() == False:
        await ctx.channel.send('A game has not been started! Type !start-game to begin.')
    else:
        player = ctx.author.name
        playerIdentity = ctx.author
        channel = ctx.channel
        mention = ctx.author.mention
        await game.addPlayer(player, channel, mention, playerIdentity)


###Leave the game###

@bot.command(name='out', help='Leave a currently running game that you are in.')
async def leave_game(ctx):
    if await game.checkIfStarted() == False:
        await ctx.channel.send('A game has not been started! Type !start-game to begin.')
    else:
        player = ctx.author.name
        channel = ctx.channel
        mention = ctx.author.mention
        await game.removePlayer(player, channel, mention)


###Print the player list###

@bot.command(name='playerlist', help='Prints the list of players currently in the game.')
async def playerlist(ctx):
    channel = ctx.channel
    if await game.checkIfStarted() == False:
        await ctx.channel.send('A game has not been started! Type !start-game to begin.')
    else:
        await game.printPlayerlist(channel)


###Assign roles to players in the game###

@bot.command(name='assign-roles', help='Ask how many mafia are in the game, assign the roles to players and PM them their roles.')
async def assign_roles(ctx):
    author = ctx.author
    player = ctx.author.name
    if await game.checkIfStarted() == False:
        await ctx.channel.send('A game has not been started! Type !start-game to begin.')
    elif await game.checkIfHost(player) == False:
        await ctx.channel.send('Only the host can assign roles to players! The host is {}'.format(game.hostname))
    else:
        await ctx.channel.send('How many mafiosos do you want?')
        def check(m):
            return m.author.name == player
        msg = await bot.wait_for('message', check=check)
        mafia = int(msg.content)
        channel = ctx.channel
        await game.assignRoles(mafia, channel)


###End the game early###

@bot.command(name='stop', help='Stops the currently running game.')
async def stop_game(ctx):
    player = ctx.author.name
    if await game.checkIfStarted() == False:
        await ctx.channel.send('A game has not been started! Type !start-game to begin.')
    elif await game.checkIfHost(player) == False:
        await ctx.channel.send('Only the host can stop the game! The host is {}'.format(game.hostname))
    else:
        await game.resetGame()
        await ctx.channel.send('The game has been stopped!')


bot.run(TOKEN)









### Deprecated ###
###Completed - Bot Revamp###

# @client.event
# async def on_message(message):
# ###Check if bot is sending the message###
#     if message.author == client.user:
#         return


# ###Start Game###
#     elif message.content.startswith('!start-game'):
#         author = message.author.name
#         channel = message.channel 
#         await game.start(author, channel)
#         await roles.establishRoles()



# ###Join the game###
#     elif message.content.startswith('!in'):
        # if await game.checkIfStarted() == False:
        #     await message.channel.send('A game has not been started! Type !start-game to begin.')
        # else:
        #     player = message.author.name
        #     playerIdentity = message.author
        #     channel = message.channel
        #     mention = message.author.mention
        #     await game.addPlayer(player, channel, mention, playerIdentity)

# ###Leave the game###
#     elif message.content.startswith('!out'):
#         if await game.checkIfStarted() == False:
#             await message.channel.send('A game has not been started! Type !start-game to begin.')
#         else:
#             player = message.author.name
#             channel = message.channel
#             mention = message.author.mention
#             await game.removePlayer(player, channel, mention)


# ###Print the player list###
#     elif message.content.startswith('!playerlist'):
#         channel = message.channel
#         if await game.checkIfStarted() == False:
#             await message.channel.send('A game has not been started! Type !start-game to begin.')
#         else:
#             await game.printPlayerlist(channel)




# ###Assign roles to players in the game###
#     elif message.content.startswith('!assign-roles'):
#         author = message.author
#         player = message.author.name
#         if await game.checkIfStarted() == False:
#             await message.channel.send('A game has not been started! Type !start-game to begin.')
#         elif await game.checkIfHost(player) == False:
#             await message.channel.send('Only the host can assign roles to players! The host is {}'.format(game.hostname))
#         else:
#             await message.channel.send('How many mafiosos do you want?')
#             def check(m):
#                 return m.author.name == player
#             msg = await client.wait_for('message', check=check)
#             mafia = int(msg.content)
#             channel = message.channel
#             print(mafia)
#             await game.assignRoles(mafia, channel)



# ###End the game early###
#     elif message.content.startswith('!stop'):
#         player = message.author.name
#         if await game.checkIfStarted() == False:
#             await message.channel.send('A game has not been started! Type !start-game to begin.')
#         elif await game.checkIfHost(player) == False:
#             await message.channel.send('Only the host can stop the game! The host is {}'.format(game.hostname))
#         else:
#             await game.resetGame()
#             await message.channel.send('The game has been stopped!')




### To be completed ###










            





