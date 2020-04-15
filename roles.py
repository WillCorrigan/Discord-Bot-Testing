import asyncio
import random
import re
import os
import game


role_database = {}


class Role:
    def __init__(self, name='Unknown', alignment='Town', info="none"):
        self.name = name
        self.alignment = alignment
        self.info = info


async def establishRoles():

    role_database['Vanilla'] = Role(name='VT',
        alignment='Town',
        info = "You are a Vanilla Innocent!\nYou have no special powers.\nYou win when all the mafiosi are dead.")
        # has_night_action = False,
        # has_day_action = False,
        # number_of_targets = 0,
        # priority = 0,
        # sends_mafia_kill = False)

    role_database['Mafioso'] = Role(name='Goon',
        alignment = 'Mafia',
        info = "You are a Mafia Goon!\nYou may communicate privately with other mafia members. During the night, you (or another mafia member) may kill a player.\n"
        "You win when all the innocents are dead.")
        # has_night_action = False,
        # has_day_action = False,
        # number_of_targets = 0,
        # priority = 0,
        # sends_mafia_kill = True
