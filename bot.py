# bot.py
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

import game
import roles
import json

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

bot = commands.Bot(command_prefix = '!')

gameID = 0
guildInstances = {} #### Global Variable

@bot.event
async def on_ready():
	global guildInstances
	print(f'{bot.user} is connected to the following guild(s):\n')
	for guild in bot.guilds:
		print(f'{guild.name}(id: {guild.id})')






########### Bot Commands Start Here ###########



### Start Game ###

@bot.command(name='start-game', help='Initiate the game. Players can !in to join afterwards.')
async def start_game(ctx):
	global guildInstances
	author = ctx.author.name
	channel = ctx.channel
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	guildInstances[guildID] = {}
	guildInstances[guildID][channelID] = game.Game()
	await guildInstances[guildID][channelID].start(author, channel)
	await roles.establishRoles()


### Join Game ###

@bot.command(name='in', help='Join the currently running game.')
async def join_game(ctx):
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	if await guildInstances[guildID][channelID].checkIfStarted() == False:
		await ctx.channel.send('A game has not been started! Type !start-game to begin.')
	elif await guildInstances[guildID][channelID].checkIfReady() == True:
		await ctx.channel.send('The game roles have been assigned, please wait for the next game to join.')
	elif await guildInstances[guildID][channelID].checkIfSetup() == True:
		player = ctx.author.name
		playerIdentity = ctx.author
		channel = ctx.channel
		mention = ctx.author.mention
		await guildInstances[guildID][channelID].addPlayer(player, channel, mention, playerIdentity)
	else:
		await ctx.channel.send('The game is currently in progress, please wait for the next game to join.')


### Leave the game ###

@bot.command(name='out', help='Leave a currently running game that you are in.')
async def leave_game(ctx):
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	if await guildInstances[guildID][channelID].checkIfStarted() == False:
		await ctx.channel.send('A game has not been started! Type !start-game to begin.')
	else:
		player = ctx.author.name
		channel = ctx.channel
		mention = ctx.author.mention
		await guildInstances[guildID][channelID].removePlayer(player, channel, mention)


### Print the player list ###

@bot.command(name='playerlist', help='Prints the list of players currently in the game.')
async def playerlist(ctx):
	channel = ctx.channel
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	if await guildInstances[guildID][channelID].checkIfStarted() == False:
		await ctx.channel.send('A game has not been started! Type !start-game to begin.')
	else:
		await guildInstances[guildID][channelID].printPlayerlist(channel)


### Assign roles to players in the game ###

@bot.command(name='assign-roles', help='Ask how many mafia are in the game, assign the roles to players and PM them their roles.')
async def assign_roles(ctx):
	author = ctx.author
	player = ctx.author.name
	channel = ctx.channel
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	if await guildInstances[guildID][channelID].checkIfStarted() == False:
		await channel.send('A game has not been started! Type !start-game to begin.')
	elif await guildInstances[guildID][channelID].checkIfHost(player) == False:
		await channel.send('Only the host can assign roles to players! The host is {}'.format(guildInstances[guildID][channelID].hostname))
	else:
		await ctx.channel.send('How many mafiosos do you want?')
		def check(m):
			return m.author.name == player
		msg = await bot.wait_for('message', check=check)
		try:
			mafia = int(msg.content)
			await guildInstances[guildID][channelID].assignRoles(mafia, channel)
		except ValueError:
			await channel.send('Please enter a valid number with !assign-roles again.')


### End the game early ###

@bot.command(name='stop', help='Stops the currently running game.')
async def stop_game(ctx):
	player = ctx.author.name
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	if await guildInstances[guildID][channelID].checkIfStarted() == False:
		await ctx.channel.send('A game has not been started! Type !start-game to begin.')
	elif await guildInstances[guildID][channelID].checkIfHost(player) == False:
		await ctx.channel.send('Only the host can stop the game! The host is {}'.format(guildInstances[guildID][channelID].hostname))
	else:
		await guildInstances[guildID][channelID].resetGame()
		await ctx.channel.send('The game has been stopped!')



### Begin the game after assigning roles ###

@bot.command(name='begin', help="Begin the game that's currently in setup")
async def begin_game(ctx):
	player = ctx.author.name
	channel = ctx.channel
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	if await guildInstances[guildID][channelID].checkIfStarted() == False:
		await channel.send('A game has not been started! Type !start-game to begin.')
	elif await guildInstances[guildID][channelID].checkIfHost(player) == False:
		await channel.send('Only the host can begin the game! The host is {}'.format(guildInstances[guildID][channelID].hostname))
	else:
		await guildInstances[guildID][channelID].beginGame(channel)



### Force cycle change, testing only ###

@bot.command(name='force-cycle', help='Force a cycle change.')
async def force_cycle(ctx):
	channel = ctx.channel
	player = ctx.author.name
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	if await guildInstances[guildID][channelID].checkIfStarted() == False:
		await channel.send('A game has not been started! Type !start-game to begin.')
	elif await guildInstances[guildID][channelID].checkIfHost(player) == False:
		await channel.send('Only the host can force the cycle! The host is {}'.format(guildInstances[guildID][channelID].hostname))
	elif await guildInstances[guildID][channelID].checkIfReady() == True:
		await channel.send("The game is ready to start, you can't force the cycle until it begins.")
	else:
		await guildInstances[guildID][channelID].phaseChange(channel)



### vote for a player ###

@bot.command(name='vote', help='Vote for a player with !vote playername')
async def vote_player(ctx, playerToVote):
	player = ctx.author.name
	mention = ctx.author.mention
	channel = ctx.channel
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	if await guildInstances[guildID][channelID].checkIfStarted() == False:
		await channel.send('A game has not been started! Type !start-game to begin.')
	elif await guildInstances[guildID][channelID].checkIfInGame(player) == False:
		await channel.send('You are not in the game. Type !in to join the game before it starts.')
	elif await guildInstances[guildID][channelID].checkIfSetup() == True:
		await channel.send('The game is being set up, please wait before voting.')
	elif await guildInstances[guildID][channelID].checkIfReady() == True:
		await channel.send('The game is about to begin, please wait before voting.')
	elif await guildInstances[guildID][channelID].checkIfCanVote(player, channel) == False:
		await channel.send("You are either dead or it is night and you can't vote.")
	elif await guildInstances[guildID][channelID].checkIfValidVoteTarget(player, channel, playerToVote) == True:
		await guildInstances[guildID][channelID].updateVote(player, channel, playerToVote, mention)
	else:
		await channel.send("That is not a valid vote target.")



### get the bot to post a vote count ###

@bot.command(name='votecount', help='Vote count for current cycle.')
async def vote_count(ctx):
	channel = ctx.channel
	player = ctx.author.name
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	if await guildInstances[guildID][channelID].checkIfStarted() == False:
		await channel.send('A game has not been started! Type !start-game to begin.')
	elif await guildInstances[guildID][channelID].checkIfInGame(player) == False:
		await channel.send('You are not in the game. Type !in to join the game before it starts.')
	elif await guildInstances[guildID][channelID].checkIfDay() == False:
		await channel.send('It is not currently day time.')
	else:
		await guildInstances[guildID][channelID].voteCount(channel)
		# await guildInstances[guildID][channelID].printVoteCount(channel)



### unvote a player ###

@bot.command(name='unvote', help='Unvote the current player.')
async def unvote_player(ctx):
	player = ctx.author.name
	mention = ctx.author.mention
	channel = ctx.channel
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	if await guildInstances[guildID][channelID].checkIfStarted() == False:
		await channel.send('A game has not been started! Type !start-game to begin.')
	elif await guildInstances[guildID][channelID].checkIfInGame(player) == False:
		await channel.send('You are not in the game. Type !in to join the game before it starts.')
	elif await guildInstances[guildID][channelID].checkIfSetup() == True:
		await channel.send('The game is being set up, please wait before unvoting.')
	elif await guildInstances[guildID][channelID].checkIfReady() == True:
		await channel.send('The game is about to begin, please wait before unvoting.')
	elif await guildInstances[guildID][channelID].checkIfCanVote(player, channel) == False:
		await channel.send("You are either dead or it is night and you can't vote.")
	else:
		await guildInstances[guildID][channelID].unvote(player, channel, mention)
		


### test a deadline function ###

@bot.command(name='deadlinetest')
async def deadline_test(ctx):
	player = ctx.author.name
	mention = ctx.author.mention
	channel = ctx.channel
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	await guildInstances[guildID][channelID].deadlineWrapUp(channel)

@bot.command(name='votelogic')
async def vote_logic(ctx):
	channel = ctx.channel
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	await guildInstances[guildID][channelID].voteLogic(channel)


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










			





