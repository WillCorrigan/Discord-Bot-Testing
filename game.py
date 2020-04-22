# game.py
import asyncio
import random
import re
import os
import roles
import math
import operator
import time
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix = '!')

class Game:
	def __init__(self):
		self.isRunning = False
		self.phase = "Setup"
		self.cycleTime = 10
		self.playerlist = []
		self.roleslist = []
		self.hostname = "Unknown"
		self.dayNightChanger = 1
		self.cycle = 1
		self.voteCounting = {}
		self.isGoingToBeLynched = "Nobody"
		self.killedList = []
		self.cycleCounter = 0
		self.mafiaCount = 0
		self.mafiaRoleID = None
		self.gameRoleID = None
		self.mafiachannelID = None
		self.gamechannelCTX = None
		self.nightkillrequest = None
		self.emojiChoices = None
		self.nightkillTarget = None




############################################################# Checks #############################################################

	async def checkIfHost(self, player):
		return self.hostname == player

	async def checkIfStarted(self):
		return self.isRunning

	async def checkIfSetup(self):
		return self.phase == "Setup"

	async def checkIfReady(self):
		return self.phase == "Ready"

	async def checkIfDay(self):
		if "Day" in self.phase:
			return True
		else:
			return False

	async def checkIfNight(self):
		if "Night" in self.phase:
			return True
		else:
			return False

	async def checkIfCanVote(self, player, channel):
		if (next((x.isAlive for x in self.playerlist if x.name == player), None) and ("Day" in self.phase)) and any(x.name == player for x in self.playerlist):
			return True
		else:
			return False

	async def checkIfValidVoteTarget(self, player, channel, playerToVote):
		if any(x.name for x in self.playerlist if x.name == playerToVote and x.isAlive == True):
			return True
		else:
			return False

	async def checkIfInGame(self, player):
		if any(x.name == player for x in self.playerlist):
			return True
		else:
			return False


############################################################# Vote Logic #############################################################

### Update Vote ###

	async def updateVote(self, player, channel, playerToVote, mention):
		for playerObject in self.playerlist:
			if playerObject.name == player:
					if playerToVote not in self.voteCounting:
						if playerObject.voteTarget != playerToVote:
							self.voteCounting[playerObject.voteTarget].remove(playerObject)
							self.voteCounting[playerToVote] = []
							playerObject.voteTimestamp = time.time()
							playerObject.voteTarget = playerToVote
							self.voteCounting[playerToVote].append(playerObject)
							await channel.send(f'{mention} voted for {playerToVote}!')
							await self.voteLogic(channel)
							await self.voteCount(channel)
						else:
							await channel.send("You are already voting for that player.")

					elif playerToVote in self.voteCounting:
						if playerObject.voteTarget != playerToVote:
							self.voteCounting[playerObject.voteTarget].remove(playerObject)
							playerObject.voteTimestamp = time.time()
							playerObject.voteTarget = playerToVote
							self.voteCounting[playerToVote].append(playerObject)
							await channel.send(f'{mention} voted for {playerToVote}!')
							await self.voteLogic(channel)
							await self.voteCount(channel)
						else:
							await channel.send("You are already voting for that player.")


### Vote Logic - Find the highest vote total, see if there are any similar vote totals and compare the timestamps to see who was voted highest first ###

	async def voteLogic(self, channel):
		voteLogicDict = {k:len(v) for k, v in self.voteCounting.items()}
		maxVote = max(voteLogicDict.items(), key=lambda x : x[1])
		if maxVote[1] == 0:
			self.isGoingToBeLynched = "Nobody"
		else:
			countList = []
			for key, value in voteLogicDict.items():
				if value == maxVote[1]:
					countList.append(key)
			if len(countList) == 1:
				if maxVote[0] == "Not Voting":
					self.isGoingToBeLynched = "Nobody"
				else:
					self.isGoingToBeLynched = countList[0]
			elif len(countList) == 2 and "Not Voting" in countList:
				countList.remove("Not Voting")
				self.isGoingToBeLynched = countList[0]
			elif len(countList) > 2 and "Not Voting" in countList:
				countList.remove("Not Voting")
				playerTimeStampComparison = {}
				for playerstobelynched in countList:
					for key, value in self.voteCounting.items():
						if key == playerstobelynched:
							playerTimeStampComparison.setdefault(playerstobelynched, value[-1].voteTimestamp)
				lowestTime = min(playerTimeStampComparison.items(), key=lambda x: x[1])
				self.isGoingToBeLynched = lowestTime[0]


### Unvote a player, time stamp their unvote ###

	async def unvote(self, player, channel, mention):
		for playerObject in self.playerlist:
			if playerObject.name == player:
				if playerObject.voteTarget != "Not Voting":
					self.voteCounting[playerObject.voteTarget].remove(playerObject)
					playerObject.voteTimestamp = time.time()
					playerObject.voteTarget = "Not Voting"
					self.voteCounting["Not Voting"].append(playerObject)
					await self.voteLogic(channel)	
					await channel.send(f'{mention} has unvoted!')				
				else:
					await channel.send("You are already not voting.")


### Vote Count - if it's a deadline vote count then ### 

	async def voteCount(self, channel, deadline=False):
		content = []
		playermention = None
		for player in self.playerlist:
			if player.name == self.isGoingToBeLynched:
				playermention = player.playerMention
		for targets, voters in self.voteCounting.items():
			if len(voters) == 0:
				continue
			content.append((f"{targets} ({len(voters)}): " + ', '.join(x.name for x in voters)))
		contentjoined = '\n'.join(content)
		if deadline == True:
			voteEmbed = discord.Embed(title=f'{self.phase} Final Vote Count', description=f'This is the {self.phase} final vote count.', color=0xEE8700)
			voteEmbed.set_thumbnail(url="https://pbs.twimg.com/profile_images/440209611983839232/-9-_fYB5_400x400.png")
			voteEmbed.add_field(name="Votes:", value=contentjoined)
			voteEmbed.set_footer(text=f'There are currently {self.cycleTime - self.cycleCounter} seconds left before night ends. Make sure you send all actions to the bot!')
			if self.isGoingToBeLynched == "Nobody":
				voteEmbed.add_field(name=f'{self.phase} Result:', value=f'Nobody has been lynched!', inline=False)
			else:
				voteEmbed.add_field(name=f'{self.phase} Result:', value=f'{playermention} has been lynched, he was a ' + ' '.join([x.role.name for x in self.playerlist if x.name == self.isGoingToBeLynched]), inline=False)
		else:
			voteEmbed = discord.Embed(title=f'{self.phase} Vote Count', description=f'This is the {self.phase} vote count.', color=0xEE8700)
			voteEmbed.set_thumbnail(url="https://pbs.twimg.com/profile_images/440209611983839232/-9-_fYB5_400x400.png")
			voteEmbed.add_field(name="Votes:", value=contentjoined)
			if self.isGoingToBeLynched == "Nobody":
				voteEmbed.add_field(name="Current Lynch Target:", value=f'Nobody!', inline=False)
			else:
				voteEmbed.add_field(name="Current Lynch Target:", value=f'{playermention} is up for lynch!', inline=False)
			voteEmbed.set_footer(text=f'There are currently {self.cycleTime - self.cycleCounter} seconds left before lynch. Make sure you vote!')
		await channel.send(embed=voteEmbed)


############################################################# Game Setup Functions #############################################################

### Start Game ###

	async def start(self, author, channel):
		if self.isRunning:
			await channel.send('Mafia game already started in channel {}, you can stop it with !stop'.format(channel))
		else:
			self.hostname = author
			self.isRunning = True
			await channel.send('A new mafia game has been started in {}, type !in to join'.format(channel))



### Add Player to the Game ###

	async def addPlayer(self, player, channel, mention, playerIdentity, playerMention):
		if not any(x.name == player for x in self.playerlist):
			player = Player(name=player, role='Unknown', playerID = playerIdentity, playerMention = playerMention)
			self.playerlist.append(player)
			await channel.send('{} has joined the game!'.format(mention))
		else:
			await channel.send('{} is already in the game!'.format(mention))



### Remove Player from the Game ###

	async def removePlayer(self, player, channel, mention):
		for x in self.playerlist:
			if x.name == player:
				self.playerlist.remove(x)
				await channel.send('{} has left the game!'.format(mention))
			else:
				await channel.send('{} is not in the game'.format(mention))



### Print Player List and Roles ###

	async def printPlayerlist(self, channel):
		await channel.send([player.name for player in self.playerlist])

	async def printPlayerRoles(self, channel):
		await channel.send([f'{player.name} {player.role.name}' for player in self.playerlist])



### Assign Roles and then PM Players - Will be reworked when custom setups get enabled###

	async def assignRoles(self, mafia:int, channel):
		self.mafiaCount = mafia
		##re-enable to stop games having over 50% mafia
		# if mafia >= math.floor(len(self.playerlist)/2):
		#     await channel.send("You can't have more mafia than players/townies! Try !assign-roles again or get more people.")
		# else:
		if mafia > len(self.playerlist):
			await channel.send("You can't have more mafia than players!")
		else:
			for z in self.playerlist:
				z.role = "Unknown"
			mafiacount = 0
			while mafiacount < mafia:
				randPlayer = self.playerlist[random.randint(0,len(self.playerlist)-1)]
				if randPlayer.role == "Unknown":
					randPlayer.role = roles.role_database['Mafioso']
					mafiacount += 1
				else:
					continue
			for y in self.playerlist:
				if y.role == "Unknown":
					y.role = roles.role_database['Vanilla']
				else:
					continue
			await self.sendPlayerPMs()
			self.phase = "Ready"
			await channel.send('Roles have been assigned, let the host know if you have not received a PM. Start the game with !begin')



### Send Player PMs after Roles Assigned ###

	async def sendPlayerPMs(self):
		if self.mafiaCount >= 2:
			for x in self.playerlist:
				if x.role.alignment == "Mafia":
					await x.playerID.create_dm()
					await x.playerID.dm_channel.send(x.role.info + 'Your team is ' + ', '.join([x.name for x in self.playerlist if x.role.alignment == 'Mafia']))
				else:
					await x.playerID.create_dm()
					await x.playerID.dm_channel.send(x.role.info)
		else:
			for x in self.playerlist:
				await x.playerID.create_dm()
				await x.playerID.dm_channel.send(x.role.info)



### Reset Game ###

	async def resetGame(self):
		self.isRunning = False
		self.phase = "Setup"
		self.cycleTime = 10
		self.playerlist = []
		self.roleslist = []
		self.hostname = "Unknown"
		self.dayNightChanger = 1
		self.cycle = 1
		self.voteCounting = {}
		self.isGoingToBeLynched = "Nobody"
		self.killedList = []
		self.cycleCounter = 0
		self.mafiaCount = 0
		self.mafiaRoleID = None
		self.gameRoleID = None
		self.mafiachannelID = None
		self.gamechannelCTX = None



### Begin the Game ###

	async def beginGame(self, channel):
		if self.phase != "Ready":
			await channel.send('The game cannot be started until all roles have been assigned.')
		else:
			await self.phaseChange(channel)
			self.voteCounting["Not Voting"] = []
			for x in self.playerlist:
				self.voteCounting["Not Voting"].append(x)
			mafiarolesEmbed = discord.Embed(title="Mafia Team", description=f'The current mafia team members are as follows:', color=0xEE8700)
			value = "\n".join("{} - {}".format(playerObject.name, playerObject.role.name) for playerObject in self.playerlist if playerObject.role.alignment == "Mafia") 
			mafiarolesEmbed.add_field(name="Role List", value=value, inline=True)
			await self.mafiachannelID.send(embed=mafiarolesEmbed)
			
			await self.cycleFunctionsAuto(channel, self.phase)


	async def phaseChange(self, channel):
		self.phase = "{}".format(await self.phaseCounter(self.dayNightChanger))
		self.dayNightChanger += 1
		await channel.send(f'The current phase is {self.phase}')


### Phase Counter ###

	async def phaseCounter(self, dayNightChanger):
		if self.phase == "Ready":
			return "Day 1"
		elif dayNightChanger % 2 == 0:
			self.cycle +=1
			return f'Night {self.cycle -1}'
		else:
			return f'Day {self.cycle}'


### End of Day ###

	async def deadlineWrapUp(self, channel):
		await self.voteCount(channel, True)
		for toBeKilledPlayer in self.playerlist:
			if toBeKilledPlayer.name == self.isGoingToBeLynched:
				toBeKilledPlayer.isAlive = False
				self.killedList.append(toBeKilledPlayer)
				

	async def resetVotingRecords(self):
		self.voteCounting = {}
		self.voteCounting["Not Voting"] = []
		for playerObject in self.playerlist:
			if playerObject.isAlive == True:
				self.voteCounting["Not Voting"].append(playerObject)
				playerObject.voteTarget = "Not Voting"


### Send night action reminder to players ###
	# async def getNightActionPlayers(self):
	# 	for playerObject in self.playerlist:
	# 		if playerObject.role.has_night_action == True:
	# 			sendNightPMs(playerObject)


	# async def sendNightPMs(self, player):
	# 	await player.playerID.create_dm()

	# 	if player.role.has_night_action and player.role.sends_mafia_kill == False:
	# 		await channel.send("Please type !Action targetname to pick a target for your action")
	# 		def check(m):
	# 					return "!Action" in m.content and player.name == m.author.name and channel == player.playerID.dm_channel
	# 		msg = await bot.wait_for('message', check=check)
	# 		try:
	# 			mafia = int(msg.content)
	# 			await guildInstances[guildID][channelID].assignRoles(mafia, channel)
	# 		except ValueError:
	# 			await channel.send('Please enter a valid number with !assign-roles again.') 






	# 	if player.role.sends_mafia_kill == True:
	# 		await player.playerID.dm_channel.send("Please type !NK playername to pick a target to use your mafia night kill on.")

	# 	await playerObject.playerID.dm_channel.send(f'It is currently {self.phase}. ')



### Mafia NK reminders ### 



	async def sendMafiaKillRequest(self):
		channel = self.mafiachannelID
		emojiList = [u"\U0001F1E6", u"\U0001F1E7", u"\U0001F1E8", u"\U0001F1E9", u"\U0001F1EA", u"\U0001F1EB", u"\U0001F1EC", u"\U0001F1ED", u"\U0001F1EE", u"\U0001F1EF", u"\U0001F1F0"]
		mafiachannelEmbed = discord.Embed(title=f'{self.phase} Night Kill', description=f'Please react to this post to kill someone', color=0xEE8700)
		choices = [playerObject.name for playerObject in self.playerlist if playerObject.isAlive == True]
		self.emojiChoices = dict(zip(emojiList, choices))
		value = "\n".join("{} - {}".format(*item) for item in self.emojiChoices.items())
		mafiachannelEmbed.add_field(name="Please vote for who you want to lynch", value=value, inline=True)
		message_1 = await channel.send(embed=mafiachannelEmbed)
		self.nightkillrequest = message_1.id

		for emojireaction in self.emojiChoices.keys():
			await message_1.add_reaction(emojireaction)


	async def assessMafiaKillRequest(self):
		channel = self.mafiachannelID
		message_1_get = await channel.fetch_message(self.nightkillrequest)
		counts = {react.emoji: react.count for react in message_1_get.reactions}
		winner = max(self.emojiChoices, key=counts.get)
		await channel.send(f'{self.emojiChoices[winner]} is the kill')
		self.nightkillTarget = self.emojiChoices[winner]





	async def checkIfGameOver(self, channel):
		mafiacount = 0
		towncount = 0
		for playerObject in self.playerlist:
			if playerObject.isAlive == True:
				if playerObject.role.alignment == "Town":
					towncount += 1
				elif playerObject.role.alignment == "Mafia":
					mafiacount += 1
			else:
				continue
		if mafiacount >= towncount:
			await channel.send("The game has ended, Mafia wins!")
			await channel.send("The mafia team was: " + ', '.join(x.name for x in self.playerlist if x.role.alignment == "Mafia"))
			self.isRunning = False
			await self.resetGame()
		elif mafiacount == 0:
			await channel.send("The game has ended, Town wins!")
			await channel.send("The mafia team was: " + ', '.join(x for x in self.playerlist if x.role.alignment == "Mafia"))
			self.isRunning = False
			await resetGame()
		else:
			return False




### End of Night Actions ###

	async def nightActionsWrapUp(self, channel):
		for playerObject in self.playerlist:
			if playerObject.name == self.nightkillTarget:
				playerObject.isAlive = False
				self.killedList.append(playerObject)
				await channel.send(f'{playerObject.name} has been killed, he was {playerObject.role.name}!')
				await self.resetVotingRecords()




### Combine phase functions ###

	async def cycleFunctionsAuto(self, channel, phase):
		while self.isRunning == True:
			await asyncio.sleep(1)
			self.cycleCounter += 1
			print(self.cycleCounter)
			if "Night" in self.phase and self.cycleCounter == (self.cycleTime - 5):
				await self.assessMafiaKillRequest()
			if self.cycleCounter == self.cycleTime:
				if "Night" in self.phase:
					await self.nightActionsWrapUp(channel)
					await self.phaseChange(channel)
					if await self.checkIfGameOver(channel) == False:
						self.cycleCounter = 0
				elif "Day" in self.phase:
					await self.deadlineWrapUp(channel)
					await self.phaseChange(channel)
					if await self.checkIfGameOver(channel) == False:
						await self.sendMafiaKillRequest()
						self.cycleCounter = 0
			else:
				continue





				



############################################################# Player Class #############################################################

class Player:
	def __init__(self, name='Unknown', role='Unknown', playerID='Unknown', playerMention = 'Unknown'):
		self.name = name
		self.role = role
		self.playerID = playerID
		self.voteTarget = "Not Voting"
		self.voteTimestamp = 0
		self.isAlive = True
		self.playerMention = playerMention

	async def __str__(self):
		return(self.name + ": " + self.role)