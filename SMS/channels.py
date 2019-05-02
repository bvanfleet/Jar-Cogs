from redbot.core import commands
from enum import Enum

import discord

class Channels(commands.Cog):
    """
    Enum for channels to make it simplier to access them when needed
    """
    _channel_ids = {        
        "RULES": 494211779950411777,
        "LOG": 509041710651670548,
        "GREETINGS": 493875452046475279,
        "WELCOME": 513855964294938624,
        "SERVER_ORIENTATION": 508391802940817415,   
        "UNDER_18": 494210029294059520,
        "INTERNET_SAFETY": 508401690874085378,
        "INCIDENT": 494210087217266688
    }

    def __init__(self, bot):
        self.bot = bot       

    @property
    def rules(self):
        """
        Rules channel object
        """
        return self.bot.get_channel(self._channel_ids["RULES"])

    @property
    def log(self):
        """
        Logging channel object
        """
        return self.bot.get_channel(self._channel_ids["LOG"])

    @property
    def greetings(self):
        """
        Greetings channel object
        """
        return self.bot.get_channel(self._channel_ids["GREETINGS"])

    @property
    def welcome(self):
        """
        Welcome channel object
        """
        return self.bot.get_channel(self._channel_ids["WELCOME"])

    @property
    def server_orientation(self):
        """
        Server Orientation channel object
        """
        return self.bot.get_channel(self._channel_ids["SERVER_ORIENTATION"])

    @property
    def under_18(self):
        """
        Under 18 channel object
        """
        return self.bot.get_channel(self._channel_ids["UNDER_18"])

    @property
    def internet_safety(self):
        """
        Internet safety channel object
        """
        return self.bot.get_channel(self._channel_ids["INTERNET_SAFETY"])

    @property
    def incident(self):
        """
        Incident channel object
        """
        return self.bot.get_channel(self._channel_ids["INCIDENT"])

    def anchor(self, channel):
        """
        Formats the channel for embedding in a string
        """
        return f"<#{channel}>"