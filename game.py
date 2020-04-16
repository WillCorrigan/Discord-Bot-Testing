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

		voteEmbed = discord.Embed(title=f'{self.phase} Vote Count', description=f'This is the {self.phase} vote count.', color=0xEE8700)
		voteEmbed.set_thumbnail(url="https://pbs.twimg.com/profile_images/440209611983839232/-9-_fYB5_400x400.png")
		voteEmbed.add_field(name="Votes:", value=contentjoined)
		if deadline == True:
			voteEmbed.add_field(name=f'{self.phase} Result:',value=f'{playerMention} has been lynched, he was a ' + ' '.join([x.role.name for x in self.playerlist if x.name == self.isGoingToBeLynched]), inline=False)
		else:
			voteEmbed.add_field(name="Current Lynch Target:", value=f'{playermention} is up for lynch!', inline=False)
		voteEmbed.set_footer(text=f'There is currently <inserttimeremaining> left before lynch. Make sure you vote!')
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



### Assign Roles and then PM Players ###

	async def assignRoles(self, mafia:int, channel):
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
		mafiaCount = 0
		for y in self.playerlist:
			if y.role.alignment == 'Mafia':
				mafiaCount += 1
		if mafiaCount >= 2:
			for x in self.playerlist:
				await x.playerID.create_dm()
				await x.playerID.dm_channel.send(x.role.info + 'Your team is ' + ', '.join([x.name for x in self.playerlist if x.role.alignment == 'Mafia']))
		else:
			for x in self.playerlist:
				await x.playerID.create_dm()
				await x.playerID.dm_channel.send(x.role.info)



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



### Begin the Game ###

	async def beginGame(self, channel):
		if self.phase != "Ready":
			await channel.send('The game cannot be started until all roles have been assigned.')
		else:
			await self.phaseChange(channel)
			self.voteCounting["Not Voting"] = []
			for x in self.playerlist:
				self.voteCounting["Not Voting"].append(x)


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
				self.playerlist.remove(toBeKilledPlayer)
				



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



















########## deprecated ###################






### When someone votes, append their name to target in dictionary and then delete them from their previous vote ###

#     async def updateVote(self, player, channel, playerToVote, mention):
#         for x in self.playerlist:
#             if x.name == player:
#                 if playerToVote not in self.voteCounting:
#                     if x.voteTarget != playerToVote:
#                         self.voteCounting[playerToVote] = []
#                         tempTimestampDict = {}
#                         tempTimestampDict = tempTimestampDict.setdefault(x.name, time.time())
#                         self.voteCounting["Not Voting"].append(tempTimestampDict)
#                         self.voteCounting[x.voteTarget].remove(x.name)
#                         x.voteTarget = playerToVote
#                         await channel.send(f'{mention} voted for {playerToVote}!')
#                         await self.voteLogic(channel)
#                         await self.voteCount(channel)
#                     else:
#                         await channel.send("You are already voting for that player.")
#                 else:
#                     if x.voteTarget != playerToVote:
#                         tempTimestampDict = {}
#                         tempTimestampDict = tempTimestampDict.setdefault(x.name, time.time())
#                         self.voteCounting["Not Voting"].append(tempTimestampDict)
#                         self.voteCounting[x.voteTarget].remove(x.name)
#                         x.voteTarget = playerToVote
#                         await channel.send(f'{mention} voted for {playerToVote}!')
#                         await self.voteLogic(channel)
#                         await self.voteCount(channel)
#                     else:
#                         await channel.send("You are already voting for that player.")




# ### When someone unvotes, remove their name from target in dictionary (names are stored in a list in the dictionary) ###
# ### Append to "Not Voting" dictionary ###

#     async def unvote(self, player, channel, mention):
#         for x in self.playerlist:
#             if x.name == player:
#                 if x.voteTarget != "Not Voting":
#                     self.voteCounting[x.voteTarget].remove(x.name)
#                     x.voteTarget = "Not Voting"
#                     if "Not Voting" not in self.voteCounting:
#                         self.voteCounting["Not Voting"] = []
#                         tempTimestampDict = {}
#                         tempTimestampDict = tempTimestampDict.setdefault(x.name, time.time())
#                         self.voteCounting["Not Voting"].append(tempTimestampDict)
#                     else:
#                         tempTimestampDict = {}
#                         tempTimestampDict = tempTimestampDict.setdefault(x.name, time.time())
#                         self.voteCounting["Not Voting"].append(tempTimestampDict)
#                     await channel.send(f'{mention} has unvoted!')
#                     await self.voteLogic(channel)
#                 else:
#                     await channel.send("You are already not voting.")



# ### Do a vote count ###

#     async def voteCount(self, channel, deadline=False):
#         for targets, voters, voteStamps in self.voteCounting.items():
#             if len(voters) == 0:
#                 continue
#             await channel.send(f"{targets} ({len(voters)}): " + ', '.join(y for x, y in voters[x][y]))
#         if deadline == True:
#             await channel.send(f'{self.isGoingToBeLynched} has been lynched, he was a ' + ' '.join([x.role.name for x in self.playerlist if x.name == self.isGoingToBeLynched]))
#         else:
#             await channel.send(f'{self.isGoingToBeLynched} is up for lynch!')


# ### Vote logic??? ###

#     async def voteLogic(self, channel):
#         votingLogicDict = {k:len(v) for k, v in self.voteCounting.items()}
#         maxVote = max(votingLogicDict.items(), key=lambda x : x[1])
#         if maxVote[1] == 0:
#             self.isGoingToBeLynched = "Nobody"
#         else:
#             countList = []
#             for key, value in votingLogicDict.items():
#                 if value == maxVote[1]:
#                     countList.append(key)
#             if len(countList) == 1 and maxVote[0] == "Not Voting":
#                 self.isGoingToBeLynched = "Nobody"
#             elif len(countList) == 1:
#                 self.isGoingToBeLynched = maxVote[0]
#             elif len(countList) == 2 and "Not Voting" in countList:
#                 countList.remove("Not Voting")
#                 self.isGoingToBeLynched = countList[0]
#             # else:
#             #     for playerVoteHistory in countList:
#             #         for playerVoteName, playerVoteTime in playerVoteHistory.items():