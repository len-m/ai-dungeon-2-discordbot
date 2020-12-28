import discord
import os
from dotenv import load_dotenv
load_dotenv()

client = discord.Client();

def commands(commandName, argc, argv):
    #argc = amount of arguments
    #argv = array of arguments

    commands = {
        #"discordcommand" : [functionName, accepted argc]
        "test": [test, 2]
    }
    #check if command exists
    if commandName in commands:
        commandData = commands.get(commandName)
        #check if argc is valid
        if argc == commandData[1]:
            #will throw error if function doesnt exist
            commandData[0](argv)
        else:
            print("invalid argc")
    else:
        print("invalid command")
        
######################### commands #########################

def test(argv):
    #wantedArgc = 2
    #commandName = "test"
    #if checkForValidity(wantedArgc, argc, commandName) == true:
    print("valid command")
    
############################################################
@client.event
async def on_ready():
    print("ready")

@client.event
async def on_message(message):
    if message.author.bot:
        return
    
    #define a prefix
    prefix = "!"

    #check if message starts with prefix
    if message.content.startswith(prefix):
        
        #cut off prefix
        argsString = message.content[1:].lower()
    
        if argsString == "":
            return

        print('Message from {0.author}: {0.content}'.format(message))

        #split into args
        argv = argsString.split()
        
        commands(argv[0], len(argv), argv)




        #for i in argv:
         #   print('{0}'.format(i))


client.run(os.getenv("TOKEN"))