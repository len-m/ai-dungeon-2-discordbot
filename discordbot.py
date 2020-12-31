import random
import sys
import time
import discord
import os
from generator.gpt2.gpt2_generator import *
from story import grammars
from story.story_manager import *
from story.utils import *
from dotenv import load_dotenv
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
load_dotenv()

client = discord.Client();

# global vars

isIngame = False
currentChannelID = None
userID = None
prefix = "µ"

async def executeCommand(commandName, argc, argv):
    #argc = amount of arguments
    #argv = array of arguments

    commands = {
        #"discordcommand" : [functionName, accepted argc]
        "play": [play, 1],
        "quit": [quit, 1],
        "revert": [revert, 1],
        "reset": [reset, 1],
        "restart": [restart, 1],
        "help": [help, 1]
    }
    #check if command exists
    if commandName in commands:
        commandData = commands.get(commandName)
        #check if argc is valid
        if argc == commandData[1]:
            #will throw error if function doesnt exist
            await commandData[0](argv)
        else:
            print("invalid argc")
    else:
        print("invalid command")
        
######################### commands #########################

#   text += '\n  "/revert"   Reverts the last action allowing you to pick a different action.'
#   text += '\n  "/quit"     Quits the game and saves'
#   text += '\n  "/reset"    Starts a new game and saves your current one'
#   text += '\n  "/restart"  Starts the game from beginning with same settings'

async def revert(argv):
    print("command: revert")
async def reset(argv):
    print("command: reset")
async def restart(argv):
    print("command: restart")
async def help(argv):
    print("command: help")
async def quit(argv):
    print("command: quit")

async def play(argv):
    global isIngame
    if isIngame == False:
        await play_aidungeon_2()
    else:
        isIngame = True
        print("already ingame")



############################################################
@client.event
async def on_ready():
    print("ready")

@client.event
async def on_message(message):
    if message.author.bot:
        return
    
    #check if message starts with prefix
    global prefix
    if message.content.startswith(prefix):
        
        #cut off prefix
        argsString = message.content[1:].lower()
    
        if argsString == "":
            return

        # real command
        global userID
        userID = message.author.id
        global currentChannelID
        currentChannelID = message.channel.id


        print('Message from {0.author}: {0.content}'.format(message))

        #split into args
        argv = argsString.split()
        #check what command
        await executeCommand(argv[0], len(argv), argv)


################################################

def checkForValidInput(num, input):
    try:
        int_input = int(input)
        if int_input >= 0 and int_input < num:
            return True
        else:
            return False            
    except ValueError:
        return False


async def getNumInput(channel, user, num):
    while True:
        msg = await client.wait_for('message', check = lambda message: message.channel == channel and message.author == user)
        content = msg.content
        if checkForValidInput(num, content) == True:
            return int(content)
        else:
            print("invalid input")


async def getUserInput(channel, user, displayMessage=None):
    if displayMessage != None:
        await channel.send(displayMessage)
    msg = await client.wait_for('message', check = lambda message: message.channel == channel and message.author == user)
    return msg.content






def random_story(story_data):
    # random setting
    settings = story_data["settings"].keys()
    n_settings = len(settings)
    n_settings = 2
    rand_n = random.randint(0, n_settings - 1)
    for i, setting in enumerate(settings):
        if i == rand_n:
            setting_key = setting

    # random character
    characters = story_data["settings"][setting_key]["characters"]
    n_characters = len(characters)
    rand_n = random.randint(0, n_characters - 1)
    for i, character in enumerate(characters):
        if i == rand_n:
            character_key = character

    # random name
    name = grammars.direct(setting_key, "character_name")

    return setting_key, character_key, name, None, None





async def select_game():
    with open(YAML_FILE, "r") as stream:
        data = yaml.safe_load(stream)

    # Random story?
    global currentChannelID
    global userID
    channel = client.get_channel(currentChannelID)
    user = client.get_user(userID)
    await channel.send("Random story? \n0) yes \n1) no")

    choice = await getNumInput(channel, user, 2)

    if choice == 0:
        return random_story(data)

    # User-selected story...
    setting_string = "Pick a setting."
    settings = data["settings"].keys()
    for i, setting in enumerate(settings):
        setting_string += "\n" + str(i) + ") " + setting
        if setting == "fantasy":
            setting_string += " (recommended)"

    setting_string += "\n" + str(len(settings)) + ") custom"
    await channel.send(setting_string)
    choice = await getNumInput(channel, user, len(settings) + 1)
    if choice == len(settings):
        return "custom", None, None, None, None

    setting_key = list(settings)[choice]

    # User-selected character
    character_pick_string = "Pick a character"
    characters = data["settings"][setting_key]["characters"]
    for i, character in enumerate(characters):
        character_pick_string += "\n" + str(i) + ") " + character

    await channel.send(character_pick_string)

    character_key = list(characters)[await getNumInput(channel, user, len(characters))]

    name = await getUserInput(channel, user, displayMessage="What is your name?")

    setting_description = data["settings"][setting_key]["description"]
    character = data["settings"][setting_key]["characters"][character_key]

    return setting_key, character_key, name, character, setting_description




async def get_custom_prompt():
    context = ""
    global currentChannelID
    channel = client.get_channel(currentChannelID)

    await channel.send(
        "\nEnter a prompt that describes who you are and the first couple sentences of where you start "
        + "out ex:\n 'You are a knight in the kingdom of Larion. You are hunting the evil dragon who has been "
        + "terrorizing the kingdom. You enter the forest searching for the dragon and see' "
    )
    prompt = input("Starting Prompt: ")
    return context, prompt


def get_curated_exposition(setting_key, character_key, name, character, setting_description):
    name_token = "<NAME>"
    try:
        context = grammars.generate(setting_key, character_key, "context") + "\n\n"
        context = context.replace(name_token, name)
        prompt = grammars.generate(setting_key, character_key, "prompt")
        prompt = prompt.replace(name_token, name)
    except:
        context = ("You are " + name + ", a " + character_key + " " + setting_description + "You have a " + character["item1"] + " and a " + character["item2"] + ". ")
        prompt_num = np.random.randint(0, len(character["prompts"]))
        prompt = character["prompts"][prompt_num]

    return context, prompt


async def play_aidungeon_2():

    global currentChannelID
    global userID
    channel = client.get_channel(currentChannelID)
    user = client.get_user(userID)
    await channel.send("Initializing AI Dungeon! (This might take a few minutes)")

    generator = GPT2Generator()
    story_manager = UnconstrainedStoryManager(generator)

    while True:
        if story_manager.story != None:
            story_manager.story = None

        while story_manager.story is None:

            (setting_key, character_key, name, character, setting_description) = await select_game()

            if setting_key == "custom":
                context, prompt = await get_custom_prompt()
            else:
                context, prompt = get_curated_exposition(setting_key, character_key, name, character, setting_description)

            await channel.send("Generating story...")

            result = story_manager.start_new_story(prompt, context=context, upload_story=False)
            await channel.send(result)

        while True:
            sys.stdin.flush()
            rawAction = await getUserInput(channel, user)
            action = rawAction.strip()
            
            global prefix
            if len(action) > 0 and action[0] == prefix:

                # TODO: change to discord code, this is still default AI Dungeon 2 code

                split = action[1:].split(" ")  # removes preceding slash
                command = split[0].lower()
                args = split[1:]
                if command == "reset":
                    story_manager.story.get_rating()
                    break

                elif command == "restart":
                    story_manager.story.actions = []
                    story_manager.story.results = []
                    await channel.send("Game restarted.\n" + story_manager.story.story_start)
                    continue

                elif command == "quit":
                    story_manager.story.get_rating()
                    exit()

                elif command == "revert":
                    if len(story_manager.story.actions) == 0:
                        await channel.send("You can't go back any farther.")
                        continue

                    story_manager.story.actions = story_manager.story.actions[:-1]
                    story_manager.story.results = story_manager.story.results[:-1]
                    await channel.send("Last action reverted.")
                    if len(story_manager.story.results) > 0:
                        await channel.send(story_manager.story.results[-1])
                    else:
                        await channel.send(story_manager.story.story_start)
                    continue

                else:
                    await channel.send("Unknown command: {}".format(command))

            else:
                if action == "":
                    action = ""
                    result = story_manager.act(action)
                    await channel.send(result)

                elif action[0] == '"':
                    action = "You say " + action

                else:
                    action = action.strip()

                    if "you" not in action[:6].lower() and "I" not in action[:6]:
                        action = action[0].lower() + action[1:]
                        action = "You " + action

                    if action[-1] not in [".", "?", "!"]:
                        action = action + "."

                    action = first_to_second_person(action)

                    action = "\n> " + action + "\n"

                result = "\n" + story_manager.act(action)
                if len(story_manager.story.results) >= 2:
                    similarity = get_similarity(
                        story_manager.story.results[-1], story_manager.story.results[-2]
                    )
                    if similarity > 0.9:
                        story_manager.story.actions = story_manager.story.actions[:-1]
                        story_manager.story.results = story_manager.story.results[:-1]
                        await channel.send("Woops that action caused the model to start looping. Try a different action to prevent that.")
                        continue

                if player_won(result):
                    await channel.send(result + "\n CONGRATS YOU WIN")
                    story_manager.story.get_rating()
                    break
                elif player_died(result):
                    await channel.send(
                        result
                        + "\nYOU DIED. GAME OVER" 
                        + "\n\nOptions:" 
                        + "\n0) Start a new game" 
                        + "\n1) \"I'm not dead yet!\" (If you didn't actually die)" 
                        + "\nWhich do you choose?"
                    )
                    choice = get_num_options(2)
                    choice = getNumInput(channel, user, 2)
                    if choice == 0:
                        story_manager.story.get_rating()
                        break
                    else:
                        await channel.send("Sorry about that...where were we?\n" + result)

                else:
                    await channel.send(result)


client.run(os.getenv("TOKEN"))