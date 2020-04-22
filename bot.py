# bot.py
import os
import discord
import asyncio
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
	guild = ctx.guild
	channelID = ctx.channel.id
	guildInstances[guildID] = {}
	guildInstances[guildID] = game.Game()
	await resetGuildToBeforeGame(ctx)
	guildInstances[guildID].gamechannelCTX = channel
	await guildInstances[guildID].start(author, channel)
	await roles.establishRoles()
	await createGuildRoles(ctx)


@bot.command(hidden=True)
async def createGuildRoles(ctx):
	guildID = ctx.guild.id
	await ctx.guild.create_role(name="MafiaGame")
	await ctx.guild.create_role(name="MafiaGame")





### Join Game ###

@bot.command(name='in', help='Join the currently running game.')
async def join_game(ctx):
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	if await guildInstances[guildID].checkIfStarted() == False:
		await ctx.channel.send('A game has not been started! Type !start-game to begin.')
	elif await guildInstances[guildID].checkIfReady() == True:
		await ctx.channel.send('The game roles have been assigned, please wait for the next game to join.')
	elif await guildInstances[guildID].checkIfSetup() == True:
		player = ctx.author.name
		playerIdentity = ctx.author
		playerMention = ctx.author.mention
		channel = ctx.channel
		mention = ctx.author.mention
		await guildInstances[guildID].addPlayer(player, channel, mention, playerIdentity, playerMention)
	else:
		await ctx.channel.send('The game is currently in progress, please wait for the next game to join.')


### Leave the game ###

@bot.command(name='out', help='Leave a currently running game that you are in.')
async def leave_game(ctx):
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	if await guildInstances[guildID].checkIfStarted() == False:
		await ctx.channel.send('A game has not been started! Type !start-game to begin.')
	else:
		player = ctx.author.name
		channel = ctx.channel
		mention = ctx.author.mention
		await guildInstances[guildID].removePlayer(player, channel, mention)


### Print the player list ###

@bot.command(name='playerlist', help='Prints the list of players currently in the game.')
async def playerlist(ctx):
	channel = ctx.channel
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	if await guildInstances[guildID].checkIfStarted() == False:
		await ctx.channel.send('A game has not been started! Type !start-game to begin.')
	else:
		await guildInstances[guildID].printPlayerlist(channel)



### Assign roles to players in the game ###

@bot.command(name='assign-roles', help='Ask how many mafia are in the game, assign the roles to players and PM them their roles.')
async def assign_roles(ctx):
	author = ctx.author
	player = ctx.author.name
	channel = ctx.channel
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	if await guildInstances[guildID].checkIfStarted() == False:
		await channel.send('A game has not been started! Type !start-game to begin.')
	elif await guildInstances[guildID].checkIfHost(player) == False:
		await channel.send('Only the host can assign roles to players! The host is {}'.format(guildInstances[guildID].hostname))
	elif await guildInstances[guildID].checkIfDay() or await guildInstances[guildID].checkIfNight() == True:
		await channel.send("The game is in progress, you can't re-assign roles.")
	else:
		await ctx.channel.send('How many mafiosos do you want?')
		def check(m):
			return m.author.name == player
		msg = await bot.wait_for('message', check=check)
		try:
			mafia = int(msg.content)
			roleSetup = [x.id for x in ctx.guild.roles if x.name=='MafiaGame']
			guildInstances[guildID].gameRoleID = roleSetup[0]
			guildInstances[guildID].mafiaRoleID = roleSetup[1]
			await guildInstances[guildID].assignRoles(mafia, channel)
			await assignGuildRoles(ctx)
		except ValueError:
			await channel.send('Please enter a valid number with !assign-roles again.')

@bot.command(hidden=True)
async def assignGuildRoles(ctx):
	guildID = ctx.guild.id
	guild = ctx.guild
	mafiarID = discord.utils.get(guild.roles, id=guildInstances[guildID].mafiaRoleID)
	gamerID = discord.utils.get(guild.roles, id=guildInstances[guildID].gameRoleID)
	for playerObject in guildInstances[guildID].playerlist:
		if playerObject.role.alignment == "Mafia":
			await playerObject.playerID.add_roles(mafiarID)
		elif playerObject.role.alignment == "Town":
			await playerObject.playerID.add_roles(gamerID)


### End the game early ###

@bot.command(name='stop', help='Stops the currently running game.')
async def stop_game(ctx):
	player = ctx.author.name
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	if await guildInstances[guildID].checkIfStarted() == False:
		await ctx.channel.send('A game has not been started! Type !start-game to begin.')
	elif await guildInstances[guildID].checkIfHost(player) == False:
		await ctx.channel.send('Only the host can stop the game! The host is {}'.format(guildInstances[guildID].hostname))
	else:
		await resetGuildToBeforeGame(ctx)
		await guildInstances[guildID].resetGame()
		await ctx.channel.send('The game has been stopped!')



@bot.command(name='purgeroles', help='Removes the created roles and channel from the server.')
async def resetGuildToBeforeGame(ctx):
	guildID = ctx.guild.id
	guild = ctx.guild
	mafiachannelDelete = discord.utils.get(guild.text_channels, name='mafia-chat')
	for role in ctx.guild.roles:
		if role.name == "MafiaGame":
			await role.delete()
	if mafiachannelDelete != None:
		await mafiachannelDelete.delete()








### Begin the game after assigning roles ###

@bot.command(name='begin', help="Begin the game that's currently in setup")
async def begin_game(ctx):
	player = ctx.author.name
	channel = ctx.channel
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	guild = ctx.message.guild
	if await guildInstances[guildID].checkIfStarted() == False:
		await channel.send('A game has not been started! Type !start-game to begin.')
	elif await guildInstances[guildID].checkIfHost(player) == False:
		await channel.send('Only the host can begin the game! The host is {}'.format(guildInstances[guildID].hostname))
	elif await guildInstances[guildID].checkIfDay() or await guildInstances[guildID].checkIfNight() == True:
		await channel.send("The game is in progress, you can't begin the game again.")
	else:
		await guild.create_text_channel(name=f'Mafia Chat', overwrites=await text_permissions(ctx))
		mafiachannel = discord.utils.get(guild.text_channels, name='mafia-chat')
		guildInstances[guildID].mafiachannelID = mafiachannel
		await guildInstances[guildID].beginGame(channel)

		



### Force cycle change, testing only ###

@bot.command(name='force-cycle', help='Force a cycle change.')
async def force_cycle(ctx):
	channel = ctx.channel
	player = ctx.author.name
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	if await guildInstances[guildID].checkIfStarted() == False:
		await channel.send('A game has not been started! Type !start-game to begin.')
	elif await guildInstances[guildID].checkIfHost(player) == False:
		await channel.send('Only the host can force the cycle! The host is {}'.format(guildInstances[guildID].hostname))
	elif await guildInstances[guildID].checkIfReady() == True:
		await channel.send("The game is ready to start, you can't force the cycle until it begins.")
	else:
		await guildInstances[guildID].phaseChange(channel)



### vote for a player ###

@bot.command(name='vote', help='Vote for a player with !vote playername')
async def vote_player(ctx, playerToVote):
	player = ctx.author.name
	mention = ctx.author.mention
	channel = ctx.channel
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	if await guildInstances[guildID].checkIfStarted() == False:
		await channel.send('A game has not been started! Type !start-game to begin.')
	elif await guildInstances[guildID].checkIfInGame(player) == False:
		await channel.send('You are not in the game. Type !in to join the game before it starts.')
	elif await guildInstances[guildID].checkIfSetup() == True:
		await channel.send('The game is being set up, please wait before voting.')
	elif await guildInstances[guildID].checkIfReady() == True:
		await channel.send('The game is about to begin, please wait before voting.')
	elif await guildInstances[guildID].checkIfCanVote(player, channel) == False:
		await channel.send("You are either dead or it is night and you can't vote.")
	elif await guildInstances[guildID].checkIfValidVoteTarget(player, channel, playerToVote) == True:
		await guildInstances[guildID].updateVote(player, channel, playerToVote, mention)
	else:
		await channel.send("That is not a valid vote target.")



### get the bot to post a vote count ###

@bot.command(name='votecount', help='Vote count for current cycle.')
async def vote_count(ctx):
	channel = ctx.channel
	player = ctx.author.name
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	if await guildInstances[guildID].checkIfStarted() == False:
		await channel.send('A game has not been started! Type !start-game to begin.')
	elif await guildInstances[guildID].checkIfInGame(player) == False:
		await channel.send('You are not in the game. Type !in to join the game before it starts.')
	elif await guildInstances[guildID].checkIfDay() == False:
		await channel.send('It is not currently day time.')
	else:
		await guildInstances[guildID].voteCount(channel)



### unvote a player ###

@bot.command(name='unvote', help='Unvote the current player.')
async def unvote_player(ctx):
	player = ctx.author.name
	mention = ctx.author.mention
	channel = ctx.channel
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	if await guildInstances[guildID].checkIfStarted() == False:
		await channel.send('A game has not been started! Type !start-game to begin.')
	elif await guildInstances[guildID].checkIfInGame(player) == False:
		await channel.send('You are not in the game. Type !in to join the game before it starts.')
	elif await guildInstances[guildID].checkIfSetup() == True:
		await channel.send('The game is being set up, please wait before unvoting.')
	elif await guildInstances[guildID].checkIfReady() == True:
		await channel.send('The game is about to begin, please wait before unvoting.')
	elif await guildInstances[guildID].checkIfCanVote(player, channel) == False:
		await channel.send("You are either dead or it is night and you can't vote.")
	else:
		await guildInstances[guildID].unvote(player, channel, mention)
		


### test a deadline function ###

@bot.command(name='deadlinetest', hidden=True)
async def deadline_test(ctx):
	player = ctx.author.name
	mention = ctx.author.mention
	channel = ctx.channel
	guildID = ctx.guild.id
	channelID = ctx.channel.id
	await guildInstances[guildID].deadlineWrapUp(channel)


@bot.command(name='Action')
async def actions_test(ctx, target):
	player = ctx.author.name
	mention = ctx.author.mention
	channel = ctx.channel
	channelID = ctx.channel.id
	print(channel, target, channelID)




@bot.command(hidden=True)
async def text_permissions(ctx):
	guild = ctx.message.guild
	guildID = ctx.guild.id
	textChannelOverwrites = {guild.get_role(guildInstances[guildID].gameRoleID): discord.PermissionOverwrite(read_messages=False,
		manage_channels=False,
		manage_permissions=False, 
		manage_webhooks=True,
		send_messages=False,
		send_tts_messages=False,
		manage_messages=False,
		embed_links=False,
		attach_files=False,
		read_message_history=False,
		use_external_emojis=False,
		add_reactions=False),

	guild.default_role: discord.PermissionOverwrite(read_messages=False,
		manage_channels=False,
		manage_permissions=False, 
		manage_webhooks=True,
		send_messages=False,
		send_tts_messages=False,
		manage_messages=False,
		embed_links=False,
		attach_files=False,
		read_message_history=False,
		use_external_emojis=False,
		add_reactions=False),

	guild.get_role(guildInstances[guildID].mafiaRoleID): discord.PermissionOverwrite(read_messages=True, 
		send_messages=True,
		read_message_history=True,
		add_reactions=True)
}
	return textChannelOverwrites


bot.run(TOKEN)
			





