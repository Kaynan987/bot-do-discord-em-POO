from abc import ABC, abstractmethod

class Command(ABC):
    @abstractmethod
    async def execute(self, ctx):
        pass

class PlayCommand(Command):
    def __init__(self, command_handler, url):
        self.command_handler = command_handler
        self.url = url

    async def execute(self, ctx):
        await self.command_handler.process_url(ctx, self.url)

class PauseCommand(Command):
    def __init__(self, command_handler):
        self.command_handler = command_handler

    async def execute(self, ctx):
        await self.command_handler.pause_music(ctx)

class ResumeCommand(Command):
    def __init__(self, command_handler):
        self.command_handler = command_handler

    async def execute(self, ctx):
        await self.command_handler.resume_music(ctx)

class SkipCommand(Command):
    def __init__(self, command_handler):
        self.command_handler = command_handler

    async def execute(self, ctx):
        await self.command_handler.force_skip(ctx)
