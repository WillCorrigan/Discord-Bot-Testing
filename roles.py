import asyncio
import random
import re
import os


role_database = {}


class Role:
    def __init__(self, name='Unknown', alignment='Town', info="none", has_night_action=False, sends_mafia_kill=False):
        self.name = name
        self.alignment = alignment
        self.info = info
        self.has_night_action = has_night_action
        self.sends_mafia_kill = sends_mafia_kill


async def establishRoles():

    role_database['Vanilla'] = Role(name='Villager',
        alignment='Town',
        info = "You are a Vanilla Townie!\nYou have no special powers.\nYou win when all the mafia are dead.",
        has_night_action = False,
        sends_mafia_kill = False,)
        # has_day_action = False,
        # number_of_targets = 0,
        # priority = 0

    role_database['Mafioso'] = Role(name='Goon',
        alignment = 'Mafia',
        info = "You are a Mafia Goon!\nYou may communicate privately with other mafia members. During the night, you (or another mafia member) may kill a player.\n"
        "You win when all the innocents are dead.",
        has_night_action = False,
        sends_mafia_kill = True,)
        # has_day_action = False,
        # number_of_targets = 0,
        # priority = 0,

