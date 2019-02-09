from redbot.core import Config, commands, checks
from redbot.core.utils.chat_formatting import error, info, warning
from enum import Enum
import logging

# create log with 'spam_application'
logger = logging.getLogger("OnStudy")
logger.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
formatter = logging.Formatter(
    "%(asctime)s - %(name)s::%(funcName)s::%(lineno)d"
    "- %(levelname)s - %(message)s"
)

# create console handler
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)
consoleHandler.setFormatter(formatter)

# add the handlers to the log
print('adding handler-')
# allows to add only one instance of file handler and stream handler
if logger.handlers:
    print('making sure we do not add duplicate handlers')
    for handler in logger.handlers:
        # add the handlers to the log
        # makes sure no duplicate handlers are added

        if not isinstance(handler, logging.StreamHandler):
            logger.addHandler(consoleHandler)
            print('added stream handler')
else:
    logger.addHandler(consoleHandler)
    print('added handler for the first time')


class LogLevel(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 4


class Logger(commands.Cog):
    properties = {
        "guild": None,
        "log_channel": None
    }

    # # Guild_Id = 481613220550017036guild_id = 481613220550017036

    def __init__(self, bot, p_guild_id):
        self.bot = bot
        self.db = Config.get_conf(self, identifier=174211339,
                                  force_registration=True)
        # self.properties["guild"] = self.bot.get_guild(self.guild_id)
        self.properties["guild"] = self.bot.get_guild(p_guild_id)
        default_guild = {
            "settings": {
                "logging_channel_id": None
            }
        }

        self.db.register_guild(**default_guild)

    def get_guild(self):
        """
        Gets the guild from the property collection.
        """
        if self.properties["guild"] is None:
            logger.error("Guild not set.")
            return None
        return self.properties["guild"]

    async def set_guild(self, guild):
        """
        Sets guild property collection
        """
        self.properties["guild"] = guild

    async def get_logging_channel(self):
        """
        Gets the logging channel from the local object or from the database
        """
        channel = self.properties["log_channel"]
        settings = await self.db.guild(self.properties['guild']).settings()
        logging_channel_id = settings["logging_channel_id"]

        # if both the local and remote copy of the log channel are not set
        if channel is None and logging_channel_id is None:
            msg = f"Logging channel is not set for guild {self.properties['guild'].id}"
            logger.error(msg)
            return None

        # if just the remote copy of the log channel is not set
        if logging_channel_id is None:
            settings["logging_channel_id"] = channel.id
            await self.db.guild(self.properties["guild"]).settings.set(settings)

        # if just the lccal copy of the log channel is not set
        if channel is None:
            channel = self.properties["log_channel"] = self.bot.get_channel(logging_channel_id)

        return channel

    @commands.group(name="logger", aliases=["Logger"])
    @checks.admin()
    async def _logger(self, ctx):
        """
        A group of commands for to help with logging events
        """
        pass

    @_logger.group(name="settings", aliases=["set"])
    async def _logger_settings(self, ctx):
        """
        A group of commands for managing the settings for the karma cog
        """
        pass

    @_logger_settings.command(name="log")
    async def _logger_settings_log_channel(self, ctx, logging_channel_id: int):
        """
        Sets which channel should be used on this server for logging purposes.
        """
        channel_log = self.bot.get_channel(logging_channel_id)

        if channel_log is None:
            self.log(ctx, msg="No channel found", level=LogLevel.WARNING)
            return

        # register with database
        settings = await self.db.guild(self.properties['guild']).settings()
        settings["logging_channel_id"] = logging_channel_id
        await self.db.guild(self.properties["guild"]).settings.set(settings)
        await ctx.send("Channel registered with database.")

        # register locally
        self.properties["log_channel"] = channel_log
        await ctx.send("Channel registered locally.")

        # let user know success
        await ctx.send("Channel is loaded.")
        pass

    async def log(self, msg: str, *, level: LogLevel = LogLevel.DEBUG, exc_info, p_guild = None):
        """
        Logs to the configured logging channel if possible.

        Otherwise, warns the user in channel the command
        was sent that the logging channel as not been set yet.
        """
        guild = self.get_guild()

        if guild is None and p_guild:
            guild = p_guild
            self.set_guild(p_guild)

        if not msg.strip() or guild is None:
            return

        channel_log = self.get_logging_channel()
        if channel_log is None:
            return

        if level == LogLevel.DEBUG:
            logger.debug(msg)
        elif level == LogLevel.INFO:
            logger.info(msg)
            msg = info(msg)
        elif level == LogLevel.WARNING:
            logger.warn(msg)
            msg = warning(msg)
        elif level == LogLevel.ERROR:
            logger.error(msg, exc_info=exc_info)
            msg = error(msg)

        await channel_log.send(msg)