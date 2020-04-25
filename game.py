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
		self.cycleTime = 30
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
		self.gameguildCTX = None
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

	async def checkIfAssigning(self):
		return self.phase == "Assigning"

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



############################################################# Game Setup Functions #############################################################

### Start Game ###

	async def start(self, author, channel):
		if self.isRunning:
			await channel.send('Mafia game already started in channel {}, you can stop it with !stop'.format(channel))
		else:
			self.hostname = author
			self.isRunning = True
			startgameEmbed = discord.Embed(title='A new Mafia game has been started!', description=f'Type !assign-roles when you are ready to begin', color=0x3498db)
			startgameEmbed.add_field(name='Host Name:', value=self.hostname)
			startgameEmbed.add_field(name="Players:", value="Type !in to join this game")
			startgameEmbed.set_thumbnail(url="https://pbs.twimg.com/profile_images/440209611983839232/-9-_fYB5_400x400.png")
			startgameEmbed.add_field(name="Current Setup:", value=f'Cycle Time: {self.cycleTime} seconds \n Roles: ' + ', '.join((value.name for value in roles.role_database.values())), inline=False)
			startgameEmbed.set_footer(text="Please type !change-setup to modify the setup of the game.")
			await channel.send(embed=startgameEmbed)



### Add Player to the Game ###

	async def addPlayer(self, player, channel, mention, playerIdentity, playerMention):
		if not any(x.name == player for x in self.playerlist):
			player = Player(name=player, role='Unknown', playerID = playerIdentity, playerMention = playerMention)
			self.playerlist.append(player)
			playerjoinedEmbed = discord.Embed(title=f'{player.name} has joined the game!', description="Type !assign-roles when you are ready to begin.", color=0x3498db)
			playerjoinedEmbed.add_field(name='Host Name:', value=self.hostname)
			playerjoinedEmbed.add_field(name="Players:", value='\n'.join(playerObject.name for playerObject in self.playerlist))
			playerjoinedEmbed.set_thumbnail(url="https://pbs.twimg.com/profile_images/440209611983839232/-9-_fYB5_400x400.png")
			playerjoinedEmbed.add_field(name="Current Setup:", value=f'Cycle Time: {self.cycleTime} seconds \n Roles: ' + ', '.join((value.name for value in roles.role_database.values())), inline=False)
			playerjoinedEmbed.set_footer(text="Please type !change-setup to modify the setup of the game.")
			await channel.send(embed=playerjoinedEmbed)
		else:
			playeralreadyinEmbed = discord.Embed(title=f'{player} is already in the game!')
			await channel.send(embed=playeralreadyinEmbed)



### Remove Player from the Game ###

	async def removePlayer(self, player, channel, mention):
		for x in self.playerlist:
			if x.name == player:
				self.playerlist.remove(x)
				await channel.send('{} has left the game!'.format(mention))



### Assign Roles and then PM Players - Will be reworked when custom setups get enabled###

	async def assignRoles(self, mafia:int, channel):
		self.mafiaCount = mafia
		### put code here to check if mafia players = more than 50% of town ###
		if mafia <= 0:
			await channel.send("You can't have 0 mafia players, type !assign-roles again.")
			self.phase = "Setup"
		elif mafia > len(self.playerlist):
			await channel.send("You can't have more mafia than players, type !assign-roles again.")
			self.phase = "Setup"
		elif mafia == len(self.playerlist):
			await channel.send("You can't have the same amount of mafia members as players, type !assign-roles again.")
			self.phase = "Setup"
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
			rolesassignedEmbed = discord.Embed(title="The game is about to begin!", description="Roles have been assigned. Type !begin when you want to start the game.", color=0x3498db)
			await channel.send(embed=rolesassignedEmbed)


### Send Player PMs after Roles Assigned ###

	async def sendPlayerPMs(self):
		for playerObject in self.playerlist:
				await playerObject.playerID.create_dm()
				embedThis = await self.getplayerPMEmbed(playerObject)
				await playerObject.playerID.dm_channel.send(embed=embedThis)


	async def getplayerPMEmbed(self, player):

		if player.role.alignment == "Mafia":
			playerroleEmbed = discord.Embed(title=f'You are a {player.role.alignment} {player.role.name}!', color=0xff0000)
			playerroleEmbed.add_field(name='Role Info:', value=f'{player.role.info}')
			playerroleEmbed.set_thumbnail(url="https://image.freepik.com/free-vector/mafia-logo_74829-29.jpg")
			playerroleEmbed.add_field(name='Team:', value = "\n".join("{} - {}".format(playerObject.name, playerObject.role.name) for playerObject in self.playerlist if playerObject.role.alignment == "Mafia"))
			playerroleEmbed.set_footer(text="A special mafia channel has been set up for you where you can communicate with your team. You can vote at night on who to kill.")
			return playerroleEmbed
		elif player.role.alignment == "Town":
			playerroleEmbed = discord.Embed(title=f'You are a {player.role.alignment} {player.role.name}!', color=0x7cfc00)
			playerroleEmbed.add_field(name='Role Info:', value=f'{player.role.info}')
			playerroleEmbed.set_thumbnail(url="https://previews.123rf.com/images/ljupco/ljupco1107/ljupco110700114/10105326-full-length-portrait-of-a-male-farmer-holding-a-pitchfork-and-bucket-with-vegetables-isolated-on-whi.jpg")
			playerroleEmbed.set_footer(text="You can vote by typing !vote PlayerName in the thread")
			return playerroleEmbed


### Begin the Game ###

	async def beginGame(self, channel):
		if self.phase != "Ready":
			await channel.send('The game cannot be started until all roles have been assigned.')
		else:
			await self.phaseChange(channel)
			self.voteCounting["Not Voting"] = []
			for x in self.playerlist:
				self.voteCounting["Not Voting"].append(x)
			mafiarolesEmbed = discord.Embed(title="Mafia Team", description=f'The current mafia team members are as follows:', color=0x3498db)
			value = "\n".join("{} - {}".format(playerObject.name, playerObject.role.name) for playerObject in self.playerlist if playerObject.role.alignment == "Mafia") 
			mafiarolesEmbed.add_field(name="Role List", value=value, inline=True)
			await self.mafiachannelID.send(embed=mafiarolesEmbed)
			await self.cycleFunctionsAuto(channel, self.phase)




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
		voteLogicDict = {k:len(v) for k, v in self.voteCounting.items() if k != "Not Voting"}
		maxVote = max(voteLogicDict.items(), key=lambda x : x[1])
		if maxVote[1] == 0:
			self.isGoingToBeLynched = "Nobody"
		elif bool(voteLogicDict) == False:
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


### Vote Count - if it's a deadline vote count then embed becomes final day vote count ### 

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



### Reset Game ###

	async def resetGame(self):
		self.isRunning = False
		self.phase = "Setup"
		self.cycleTime = 30
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
		self.gameguildCTX = None
		self.nightkillrequest = None
		self.emojiChoices = None
		self.nightkillTarget = None



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
			mafiawinsEmbed = discord.Embed(title=f'Game Over! Mafia Wins!', color=0xff0000)
			mafiawinsEmbed.add_field(name='Mafia Team:', value="\n".join("{} - {}".format(playerObject.name, playerObject.role.name) for playerObject in self.playerlist if playerObject.role.alignment == "Mafia"))
			mafiawinsEmbed.add_field(name="Town:", value="\n".join("{} - {}".format(playerObject.name, playerObject.role.name) for playerObject in self.playerlist if playerObject.role.alignment == "Town"))
			mafiawinsEmbed.set_thumbnail(url="https://image.freepik.com/free-vector/mafia-logo_74829-29.jpg")
			mafiawinsEmbed.set_footer(text="The game has now ended, thank you for playing!")
			await channel.send(embed=mafiawinsEmbed)
			self.isRunning = False
			await self.resetGuildToBeforeGame()
			await self.resetGame()

		elif mafiacount == 0:
			townwinsEmbed = discord.Embed(title=f'Game Over! Town Wins!', color=0x7cfc00)
			townwinsEmbed.add_field(name="Town:", value="\n".join("{} - {}".format(playerObject.name, playerObject.role.name) for playerObject in self.playerlist if playerObject.role.alignment == "Town"))
			townwinsEmbed.add_field(name='Mafia Team:', value="\n".join("{} - {}".format(playerObject.name, playerObject.role.name) for playerObject in self.playerlist if playerObject.role.alignment == "Mafia"))
			townwinsEmbed.set_thumbnail(url="https://i.ytimg.com/vi/kM2ac85_Fqc/hqdefault.jpg")
			townwinsEmbed.set_footer(text="The game has now ended, thank you for playing!")
			await channel.send(embed=townwinsEmbed)
			self.isRunning = False
			await self.resetGuildToBeforeGame()
			await self.resetGame()
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
			if "Night" in self.phase and self.cycleCounter == (self.cycleTime - 5):
				await self.assessMafiaKillRequest()
			if self.cycleCounter == self.cycleTime:
				if "Night" in self.phase:
					await self.nightActionsWrapUp(channel)
					if await self.checkIfGameOver(channel) == False:
						self.cycleCounter = 0
						await self.phaseChange(channel)
				elif "Day" in self.phase:
					await self.deadlineWrapUp(channel)
					if await self.checkIfGameOver(channel) == False:
						await self.phaseChange(channel)
						await self.sendMafiaKillRequest()
						self.cycleCounter = 0
			else:
				continue



	async def resetGuildToBeforeGame(self):
		mafiachannelDelete = discord.utils.get(self.gameguildCTX.text_channels, name='mafia-chat')
		for role in self.gameguildCTX.roles:
			if role.name == "MafiaGame":
				await role.delete()
		if mafiachannelDelete != None:
			await mafiachannelDelete.delete()

				



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