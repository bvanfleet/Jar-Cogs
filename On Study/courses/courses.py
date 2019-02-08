from redbot.core import commands, Config, checks
from redbot.core.utils.chat_formatting import error, info, warning
from redbot.core.utils.predicates import MessagePredicate
import discord
import re
import logging
import random

# create logger with 'spam_application'
log = logging.getLogger("courses.py")
log.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
formatter = logging.Formatter(
    "%(asctime)s - %(name)s::%(funcName)s::%(lineno)d"
    "- %(levelname)s - %(message)s"
)

# create console handler
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)
consoleHandler.setFormatter(formatter)

# add the handlers to the logger
print('adding handler-')
# allows to add only one instance of file handler and stream handler
if log.handlers:
    print('making sure we do not add duplicate handlers')
    for handler in log.handlers:
        # add the handlers to the logger
        # makes sure no duplicate handlers are added

        if not isinstance(handler, logging.StreamHandler):
            log.addHandler(consoleHandler)
            print('added stream handler')
else:
    log.addHandler(consoleHandler)
    print('added handler for the first time')


class Courses(commands.Cog):
    """Manages courses for Server McServerface."""
    guild_id = 481613220550017036
    utility_roles = {
        "staff": {
            "id": 492382906241777678,
            "ref": None
        }
    }

    def __init__(self, bot):
        """
        Initialize the CourseAssignment object
        """
        self.bot = bot
        self.guild = self.bot.get_guild(self.guild_id)
        self.db = Config.get_conf(self, identifier=8748107325)
        self.log = self.bot.get_channel(485218362272645120)
        self.course_list = self.bot.get_channel(514518408122073116)
        self.emoji = "\N{WHITE HEAVY CHECK MARK}"
        self.utility_roles["staff"]["ref"] = self.guild.get_role(
            self.utility_roles["staff"]["id"]
        )

        default_guild = {
            "registered_courses": {}
        }

        self.db.register_guild(**default_guild)
        pass

    async def debug(self, *, msg: str, channel):
        """
        Combines logging to the logger and to the discord channel
        """
        log.debug(msg)
        if channel:
            await channel.send(msg)

    async def info(self, *, msg: str, channel):
        """
        Combines logging to the logger and to the discord channel
        """
        log.info(msg)
        if channel:
            await channel.send(info(msg))

    async def warning(self, *, msg: str, channel):
        """
        Combines logging to the logger and to the discord channel
        """
        log.warning(msg)
        if channel:
            await channel.send(warning(msg))

    async def error(self, *, msg: str, channel):
        """
        Combines logging to the logger and to the discord channel
        """
        log.error(msg)
        if channel:
            await channel.send(error(msg))

    @commands.group(name="courses")
    @checks.admin()
    async def _courses(self, ctx):
        """
        The course group of commands.
        """
        pass

    def _courses_create_record(self, course_role: discord.Role, course_category: discord.CategoryChannel):
        """
        Builds a course dictionary object
        """
        return {
            "course_name": course_role.name,
            "role_id": course_role.id,
            "category_id": course_category.id
        }
        pass

    @_courses.command(name="create", aliases=["add"])
    @checks.admin()
    async def _courses_create(self, ctx,
                              role: str, *, sections_num: int = 0):
        """
        Creates a category based on the course name supplied.

        If the role for the course doesn't exist it will
        query to user if it should be created as well.
        """
        if role == "":
            return await ctx.send(error("Role cannot be blank"))

        role = role.lower()

        sections_num = max(sections_num, 0)

        # regisiter the course with the database
        await self._courses_register(ctx, role, sort=True)

        await ctx.channel.send("Done.")
        pass

    async def _course_create_channel(self, ctx, course_role, *, sections_num: int = 0):
        """
        Creates a course channel group if it doesn't already exists
        """
        # this point on needs to be updated
        for course_category in self.guild.categories:
            if course_category.name.lower() == course_role.name.lower():
                await self.info(msg=f"Skipping channel creation for {course_role.name} as it already exists.", channel=ctx)
                return course_category

        await self.info(msg=f"Creating channel for {course_role.name}.", channel=ctx)
        # sets permissions for role objects
        overwrites = {
            self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            course_role: discord.PermissionOverwrite(read_messages=True),
            self.utility_roles["staff"]["ref"]: discord.PermissionOverwrite(read_messages=True)
        }

        # create the category
        course_category = await self.guild.create_category(name=f"{course_role.name.upper()}", overwrites=overwrites)
        # create the general chat for the course
        await self.guild.create_text_channel(name=course_role.name, category=course_category)
        # create any requested section channels
        for i in range(1, sections_num):
            await self.guild.create_text_channel(name=f"section-00{i}", category=course_category)
        # create the voice channels
        voice_channel_name = re.sub(
            r"^[A-Za-z]+(?P<courseNum>[\d]+)$",
            r"\g<courseNum>",
            course_role.name
        )

        await self.guild.create_voice_channel(name=f"{voice_channel_name}-gen", category=course_category)
        await self.guild.create_voice_channel(name=f"{voice_channel_name}-school", category=course_category)

        return course_category

    @_courses.command(name="create_section", aliases=["cs"])
    async def _courses_create_section(self, ctx, section_number: str, *, topic: str = ""):
        """
        Creates a course section for the parent course

        section_number **required**: The section number of the course.
        topic: if supplied, will set the topic of the channel to this
        """
        if not section_number:
            return

        parent_course = self.guild.get_channel(ctx.channel.category_id)
        channel = await self.guild.create_text_channel(name=f"section-{section_number}", category=parent_course)

        if topic:
            await channel.edit(topic=topic)
        pass

    async def _courses_create_course_list_entry(self, ctx, course_role):
        """
        Creates the message and applies the emoji for the users click on
        """

        # check to make sure that the course isn't already in the course list
        async for message in self.course_list.history():
            if message.content == course_role.name:
                self.warning(msg=f"Skipping creation course list entry for {course_role.name} as it already exists.", channel=ctx)
                return message.id

        # create the course role message
        message = await self.course_list.send(f"{course_role.name}")
        await self.add_reaction_to_message(ctx, message, self.emoji)

        self.info(msg=f"Created course list entry for {course_role.name}", channel=ctx)

        return message.id

    @_courses.command(name="delete", aliases=["del"])
    async def _courses_delete(self, ctx, msg_id: int):
        """
        Removes a course. **NO UNDO!**

        msg_id: the id of the course you want to remove
        """
        confirm = await self.confirm(ctx, msg="Are you sure you wish to delete this course? There is no undo.")
        if not confirm:
            return await ctx.send("Canceling.")

        async with self.db.guild(ctx.guild).registered_courses() as courses:
            course = courses.pop(str(msg_id), None)
            await self.remove_course_channel(course["category_id"])
            await self.remove_course_role(course["role_id"])
            await self.remove_course_list_entry(msg_id)
        await ctx.channel.send("Done.")
        pass

    async def remove_course_channel(self, category_id):
        """
        Removes the category and it's children that matches the 'category_id' from the server.
        """
        category = self.guild.get_channel(category_id)
        if category is None:
            return log.error("category is empty.")

        for channel in category.channels:
            await channel.delete(reason=f"removing parent category")

        await category.delete()
        pass

    async def remove_course_role(self, role_id):
        """
        Removes the role that matches the 'role_id' from the server.
        """
        role = self.guild.get_role(role_id)
        if role is None:
            return log.error("role is empty.")

        await role.delete()
        pass

    async def remove_course_list_entry(self, msg_id):
        """
        Removes the course list entry that matches the 'msg_id' from the course_list channel.
        """
        msg = await self.course_list.get_message(msg_id)
        if msg is None:
            return log.error("msg is empty.")

        await msg.delete()
        pass

    async def _courses_does_course_exist(self, course_role_name: str):
        """
        Checks to see if the course exists on the server
        """
        course_role_found = None
        # get the role from the list of server roles
        for guild_role in self.guild.roles:
            if (guild_role.name == course_role_name):
                course_role_found = guild_role
                break
        return course_role_found

    async def _courses_register_from_course_listing(self, ctx, message: discord.Message, create_interaction: bool = False):
        """
        Registers a course from a course listing in the course_list channel.
        """
        await self._courses_register(ctx, message.content, create_interaction=create_interaction, message_id=message.id)

    async def _courses_register(self, ctx, role_name: str, *, sections_num: int = 0, create_interaction: bool = True, message_id: int = 0, sort: bool = False):
        """
        Registers a course.
        msg_id: the id of the message which will trigger the course to be applied.
        course: a dict object in format of {"course_name": str, "role_id": int}
        """

        # get the role from the list of server roles
        course_role = await self._courses_does_course_exist(role_name)

        if course_role is None:
            new_role = await self._courses_roles_create(ctx, role_name)
            if new_role is not None:
                course_role = new_role

        course_channel = await self._course_create_channel(ctx, course_role, sections_num=sections_num)

        if create_interaction:
            # create the message that users will react to
            message_id = await self._courses_create_course_list_entry(
                ctx, course_role
            )

        if message_id == 0:
            return await self.error(msg="Invalid message id", channel=ctx)

        course_record = self._courses_create_record(
            course_role,
            course_channel
        )

        async with self.db.guild(ctx.guild).registered_courses() as courses:
            courses.update({
                str(message_id): course_record
            })

        if sort:
            await ctx.invoke(self._courses_sort)

        pass

    @_courses.command(name="remove_member", aliases=["rm"])
    async def _courses_remove_member(self, ctx, member: discord.Member):
        """
        Removes a member's reactions for the courses in course list.
        """
        async with ctx.channel.typing():
            try:
                await ctx.send("Removing member from courses.")
                async for message in self.course_list.history():
                    await message.remove_reaction(self.emoji, member)
                await ctx.send("Done.")
            except discord.Forbidden:
                log.exception("Insufficient permissions to remove reaction.")
                self.log.send(error(f"I don't have permission for remove reactions in {self.course_list.name}."))
            except discord.HTTPException:
                log.exception("Removing the reaction failed.")
                self.log.send(error("Removing the reaction failed."))
            except discord.NotFound:
                log.exception("The member or emoji you specified was not found.")
                self.log.send(error("The member or emoji you specified was not found."))
            except discord.InvalidArgument:
                log.exception("The emoji parameter is invalid.")
                self.log.send(error("The emoji parameter is invalid."))
        pass

    @_courses.command(name="reset")
    async def _courses_reset(self, ctx):
        """
        Clears all registered courses. **NO UNDO**!
        """
        pred = await self.confirm("Are you sure you wish to clear all registered courses? There is **no undo option**.")
        if pred is False:
            return await ctx.channel.send("Canceling.")

        async with ctx.channel.typing():
            await ctx.channel.send("Clearing registered courses.")
            async with self.db.guild(ctx.guild).registered_courses() as courses:
                courses.clear()
        await ctx.channel.send("Done.")
        pass

    @_courses.command(name="show")
    async def _courses_show(self, ctx):
        """
        Displays each course known to the bot.
        """
        courses = await self.db.guild(ctx.guild).get_raw("registered_courses")
        await ctx.channel.send(f"Displaying {len(courses)} courses.")
        courseNum = 1
        async with ctx.channel.typing():
            for key, val in courses.items():
                await ctx.channel.send(
                    f"Course {courseNum}:\n"
                    "```\n"
                    f"msg_id: {key}\n"
                    f"course: {val}\n"
                    "```"
                )
                courseNum += 1
        pass

    @_courses.command(name="sort")
    async def _courses_sort(self, ctx):
        """
        Sorts the course channels in alphabetical order
        """
        await ctx.send("Sorting courses.")

        start_index = 4

        category_list = self.guild.categories[start_index:]

        def take_name(elem):
            return elem.name.upper()

        category_list.sort(key=take_name)

        async with ctx.typing():
            for index, category in enumerate(category_list):
                new_position = index + start_index
                try:
                    await category.edit(name=category.name.upper(), position=new_position)
                except discord.InvalidArgument:
                    log.exception(f"Invalid attempt to change the position of category {category.name} to position {new_position}")
                    await ctx.send(error(f"Invalid attempt to change the position of category {category.name} to position {new_position}"))
                except discord.Forbidden:
                    log.exception(f"Forbidden from modifying category {category.name}")
                    await ctx.send(error(f"Forbidden from modifying category {category.name}"))
                except discord.HTTPException:
                    log.exception(f"Failed to edit category {category.name}")
                    await ctx.send(error(f"Failed to edit category {category.name}"))

        await ctx.send("Done.")

        pass

    @_courses.command(name="sync")
    async def _courses_sync(self, ctx):
        """
        Syncs the course list channel with the bot and the users.

        **Warning:** May take some time to complete.
        """
        async with ctx.channel.typing():
            try:
                await ctx.send("Syncing courses. This may take a while. Please be patient.")
                async for message in self.course_list.history():
                    # syncs courses with the bot's database
                    await self._courses_register_from_course_listing(ctx, message, create_interaction=False)

                    # syncs users with the courses they have signed up for
                    await self._courses_sync_roles(ctx, message)
                await ctx.send("Done.")
            except discord.Forbidden:
                log.exception("discord.Forbidden error.")
                self.log.send(error(f"I don't have permission for `read message history` in {self.course_list.name}."))
            except discord.HTTPException:
                log.exception("discord.HTTPException error.")
                self.log.send(error(f"Message history request failed!"))
        pass

    async def _courses_sync_roles(self, ctx, message: discord.Message):
        """
        Updates users and courses in #course-list to make sure they match
        """
        for react in message.reactions:
            if str(react.emoji) == self.emoji:
                has_bot_reacted = False
                async for user in react.users():
                    if user.bot and user == self.guild.me:
                        has_bot_reacted = True
                    continue
                    await self.process_course_assignment_from_call(react, user)

                if not has_bot_reacted:
                    await self.add_reaction_to_message(ctx, message, self.emoji)
        pass

    @_courses.group(name="roles")
    async def _courses_roles(self, ctx):
        """
        Commands that revolve around creating and managing course roles.
        """
        pass

    @_courses_roles.command(name="add")
    @checks.mod_or_permissions(manage_roles=True)
    async def _courses_roles_add(self, ctx, user: discord.Member = None, *, requested_roles):
        """
        Adds any number of roles to a user
        """
        if user is None:
            return

        requested_roles = requested_roles.split(" ")

        # save a copy of the guild reols so that we're not calling it a lot
        guild_roles = ctx.guild.roles

        # create a list of the roles that are already roles in the guild
        roles_to_add = [role for role in guild_roles if role.name in requested_roles]

        # create a list of roles which are not found in the guild.
        # compare the list of requested_roles against a list of the names of the roles from the guild roles
        roles_not_found = [requested_role for requested_role in requested_roles if requested_role not in [role.name for role in guild_roles]]

        # Ask if the missing riles should be created
        for role in roles_not_found:
            new_role = await self._courses_roles_create(ctx, role)
            if new_role is not None:
                roles_to_add.append(new_role)

                # create channel group
                self._courses_create(ctx, new_role.name)

        if roles_to_add:
            await user.add_roles(*roles_to_add, reason=f"{ctx.message.author} requested it.")

        await ctx.channel.send("Done.")
        pass

    @_courses_roles.command(name="check")
    @checks.mod()
    async def _courses_roles_check(self, ctx, user: discord.Member = None):
        """
        Shows the roles the user has
        Defaults to author
        """
        if user is None:
            user = ctx.author
        roles = self.getRoleList(user)
        formattedRoles = "\n".join(roles)
        await ctx.send(f"User: **{user.display_name}** has the following roles: \n{formattedRoles}")
        pass

    async def _courses_roles_create(self, ctx, role_name: str):
        """
        Confirms that the user wants to create the role.
        If so the role is created and returned to the calling function.
        Otherwise, NoneType is returned.
        """
        createRole = await self.confirm(ctx, msg=f"Role `{role_name}` does not exist. Would you like to create it?")
        if (createRole):
            color = self.get_role_color()
            try:
                # create the role in the guild
                role_obj = await ctx.guild.create_role(name=role_name, color=color)
            except discord.InvalidArgument:
                log.exception("InvalidArgument")
            except discord.Forbidden:
                log.exception(f"Bot lacks permission to add roles to the server.")
            except discord.HTTPException:
                log.exception(f"Creating the role failed.")
            else:
                await self.info(msg=f"Creating role for {role_name}.", channel=ctx)
                return role_obj
        return None

    def get_role_color(self):
        """
        Generates a random color for a role between 0xaaaaaa and 0xfffffe
        """
        def gen_color_segment():
            # 153 == 99
            # 255 == ff
            return random.randint(153, 255)

        while True:
            color = discord.Color.from_rgb(gen_color_segment(), gen_color_segment(), gen_color_segment())

            # prevent white (0xffffff) from being a role color.
            if color.value != 16777215:
                break

        return color

    async def add_reaction_to_message(self, ctx, message: discord.Message, emoji):
        """
        Adds the specified emoji as a reaction to the specified message
        """
        try:
            # add initial reaction to the course to make it easier on users to add it
            await message.add_reaction(emoji)
        except discord.InvalidArgument:
            log.exception(f"Emoji was not a valid emoji.")
        except discord.Forbidden:
            log.exception("Forbidden action")
        except discord.NotFound:
            log.exception(f"The requested emoji was not found on the server.")
        except discord.HTTPException:
            log.exception(f"There was an issue with the webserver.")
        pass

    async def confirm(self, ctx, *, msg="Are you sure?"):
        """
        Handles confirmations for commands.
        Optionally can supply a message that is displayed to the user. Defaults to 'Are you sure?'.
        """
        await ctx.channel.send(f"{msg} (y/n)")
        pred = MessagePredicate.yes_or_no(ctx)
        await self.bot.wait_for("message", check=pred)
        return pred.result

    async def on_raw_reaction_add(self, payload):
        """
        Member agrees to the rules.
        """
        await self.process_course_assignment_from_trigger(payload, add=True)
        pass

    async def on_raw_reaction_remove(self, payload):
        """
        Member no longer agrees to the rules.
        """
        await self.process_course_assignment_from_trigger(payload, add=False)
        pass

    async def process_course_assignment(self, member: discord.Member, emoji, message_id: int, add: bool):
        """
        Handles building the required products to register a student with a course
        """
        if member is None:
            return log.debug("member is None!")
        elif member.bot:
            return log.debug("member is bot")
        elif str(emoji) != self.emoji:
            return log.debug("incorrect emoji")

        # get the dict courses from the db
        courses = await self.db.guild(self.guild).get_raw("registered_courses")

        # default course to None so that we know for sure if we found something
        course = None

        # get the course that has a msg_id which matches our payload
        # then set its value to course
        for key, val in courses.items():
            if key == str(message_id):
                course = val
                break

        # ensure that we actually got a course
        if course is None:
            log.error("course is None!")
            return

        # get the role from the guild that matches the course
        role = self.guild.get_role(course["role_id"])

        # update the status of the role for the member
        await self.update_role_for_member(member, role, add)
        pass

    async def process_course_assignment_from_call(self, reaction: discord.Reaction, member: discord.Member):
        """
        Handles the processing of the reaction from an internal call.
        """
        await self.process_course_assignment(member, reaction.emoji, reaction.message.id, True)
        pass

    async def process_course_assignment_from_trigger(self, payload, *, add: bool):
        """
        Handles the processing of the reaction from a trigger.
        """
        # get the member from the guild using the user_id in the payload
        member = self.guild.get_member(payload.user_id)
        log.debug(f"user_id: {payload.user_id}")
        await self.process_course_assignment(member, payload.emoji, payload.message_id, add)
        pass

    async def update_role_for_member(self, member: discord.Member, role: discord.Role, add: bool):
        """
        Handles the rule agreement reaction.
        """
        if add:
            await member.add_roles(role)
            action = "added"
        else:
            await member.remove_roles(role)
            action = "removed"
        self.debug(msg=f"{action} role: {role.name} to member: {member.name}", channel=self.log)
        pass
