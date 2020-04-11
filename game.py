# game.py 
import asyncio
import random
import re
import os
import roles
import math

class Game:
    def __init__(self, client, cycle_time=30):
        self.isRunning = False
        self.phase = "Setup"
        self.cycleTime = cycle_time
        self.client = client
        self.playerlist = []
        self.roleslist = []
        self.hostname = "Unknown"

    async def checkIfHost(self, player):
        return self.hostname == player

    async def checkIfStarted(self):
        return self.isRunning

    async def checkIfSetup(self):
        return self.phase

    async def start(self, author, channel):
        if self.isRunning:
            await channel.send('Mafia game already started in channel {}, you can stop it with !stop'.format(channel))
        else:
            self.hostname = author
            self.isRunning = True
            await channel.send('A new mafia game has been started in {}, type !in to join'.format(channel))



    async def addPlayer(self, player, channel, mention, playerIdentity):
        if not any(x.name ==player for x in self.playerlist):
            playerAdd = Player(name=player, role='Unknown', playerID = playerIdentity)
            self.playerlist.append(playerAdd)
            await channel.send('{} has joined the game!'.format(mention))
        else:
            await channel.send('{} is already in the game!'.format(mention))

    async def removePlayer(self, player, channel, mention):
        for x in self.playerlist:
            if x.name == player:
                self.playerlist.remove(x)
                await channel.send('{} has left the game!'.format(mention))
            else:
                await channel.send('{} is not in the game'.format(mention))


    async def printPlayerlist(self, channel):
        await channel.send([player.name for player in self.playerlist])

    async def printPlayerRoles(self, channel):
        await channel.send([f'{player.name} {player.role.name}' for player in self.playerlist])

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
            

            


        # elif len(self.roleslist) >= len(self.playerlist):

        # else:
        #     for x in range(mafia):
        #         if len(self.roleslist) >= len(self.playerlist):
        #             await channel.send("You can't have more mafia than players!")
        #             break
        #         else:
        #             self.roleslist.append("Mafia")
        #     for y in range(len(self.playerlist)):
        #         if self.roleslist > self.playerlist
        #             break
        #         else:
        #             self.roleslist.append("Town")
        # await channel.send('The current role list is: {}'.format(self.roleslist))


    async def resetGame(self):
        self.isRunning = False
        self.playerlist = []
        self.roleslist = []



    async def __str__(self):
        return("Players: " +str(self.playerlist))




class Player:
    def __init__(self, name='Unknown', role='Unknown', playerID='Unknown'):
        self.name = name
        self.role = role
        self.playerID = playerID

    async def __str__(self):
        return(self.name + ": " + self.role)


