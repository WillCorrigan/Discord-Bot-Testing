# bot.py
import os
import discord
from dotenv import load_dotenv

import game
import roles
client = discord.Client()
game = game.Game(client)


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )


@client.event
async def on_message(message):
###Check if bot is sending the message###
    if message.author == client.user:
        return

###Start Game###
    elif message.content.startswith('!start-game'):
        author = message.author.name
        channel = message.channel 
        await game.start(author, channel)
        await roles.establishRoles()


###Join the game###
    elif message.content.startswith('!in'):
        if await game.checkIfStarted() == False:
            await message.channel.send('A game has not been started! Type !start-game to begin.')
        else:
            player = message.author.name
            playerIdentity = message.author
            channel = message.channel
            mention = message.author.mention
            await game.addPlayer(player, channel, mention, playerIdentity)

###Leave the game###
    elif message.content.startswith('!out'):
        if await game.checkIfStarted() == False:
            await message.channel.send('A game has not been started! Type !start-game to begin.')
        else:
            player = message.author.name
            channel = message.channel
            mention = message.author.mention
            await game.removePlayer(player, channel, mention)

###Print the player list###
    elif message.content.startswith('!playerlist'):
        channel = message.channel
        if await game.checkIfStarted() == False:
            await message.channel.send('A game has not been started! Type !start-game to begin.')
        else:
            await game.printPlayerlist(channel)


###Assign roles to players in the game###
    elif message.content.startswith('!assign-roles'):
        author = message.author
        player = message.author.name
        if await game.checkIfStarted() == False:
            await message.channel.send('A game has not been started! Type !start-game to begin.')
        elif await game.checkIfHost(player) == False:
            await message.channel.send('Only the host can assign roles to players! The host is {}'.format(game.hostname))
        else:
            await message.channel.send('How many mafiosos do you want?')
            def check(m):
                return m.author.name == player
            msg = await client.wait_for('message', check=check)
            mafia = int(msg.content)
            channel = message.channel
            print(mafia)
            await game.assignRoles(mafia, channel)
            await message.channel.send('Roles have been assigned, let the host know if you have not received a PM.')

###End the game early###
    elif message.content.startswith('!stop'):
        player = message.author.name
        if await game.checkIfStarted() == False:
            await message.channel.send('A game has not been started! Type !start-game to begin.')
        elif await game.checkIfHost(player) == False:
            await message.channel.send('Only the host can stop the game! The host is {}'.format(game.hostname))
        else:
            await game.resetGame()
            await message.channel.send('The game has been stopped!')


client.run(TOKEN)

