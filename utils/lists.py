avatars = ["https://cdn.discordapp.com/attachments/622949625204047872/622949729558593546/00.jpg",
           "https://cdn.discordapp.com/attachments/622949625204047872/622949783165730878/01.png",
           "https://cdn.discordapp.com/attachments/622949625204047872/622949803592122389/02.png",
           "https://cdn.discordapp.com/attachments/622949625204047872/622949821057073182/03.png",
           "https://cdn.discordapp.com/attachments/622949625204047872/622949843026968577/04.png",
           "https://cdn.discordapp.com/attachments/622949625204047872/622949863101038653/05.png",
           "https://cdn.discordapp.com/attachments/622949625204047872/622949882835238913/06.png",
           "https://cdn.discordapp.com/attachments/622949625204047872/622949902753988614/07.png",
           "https://cdn.discordapp.com/attachments/622949625204047872/622949921556922388/08.png",
           "https://cdn.discordapp.com/attachments/622949625204047872/622949928938766336/09.png",
           "https://cdn.discordapp.com/attachments/622949625204047872/622949934144028682/10.png",
           "https://cdn.discordapp.com/attachments/622949625204047872/622949940049477663/11.png"]
server_icons = ["https://cdn.discordapp.com/attachments/642139397386534912/642139449320407040/00.png",
                "https://cdn.discordapp.com/attachments/642139397386534912/642139460028596224/01.png",
                "https://cdn.discordapp.com/attachments/642139397386534912/642139473106305034/02.png",
                "https://cdn.discordapp.com/attachments/642139397386534912/642139487488704542/03.png",
                "https://cdn.discordapp.com/attachments/642139397386534912/642139499769626635/04.png",
                "https://cdn.discordapp.com/attachments/642139397386534912/642139513904431104/05.png",
                "https://cdn.discordapp.com/attachments/642139397386534912/642139533223264266/06.png",
                "https://cdn.discordapp.com/attachments/642139397386534912/642139545214779393/07.png",
                "https://cdn.discordapp.com/attachments/642139397386534912/642139558397345810/08.png",
                "https://cdn.discordapp.com/attachments/642139397386534912/642139570569347102/09.png",
                "https://cdn.discordapp.com/attachments/642139397386534912/642139584326533130/10.png",
                "https://cdn.discordapp.com/attachments/642139397386534912/642139596947193864/11.png"]
playing = ["CobbleCobble", "with Regaus", "with myself", "TBL", "Custom Status", "with the Nuriki Cult", "Aqos",
           "a game", "Русские Вперёд!", ",/help"]
phrases = ["Being a bot is hard sometimes.", "Hey, at least I'm not LIDL xelA!",
           "Hey, how's your day going?", "Ever wanted to take a break from all this hard work? I can't.",
           "xelA is a meanie :(", "Reminder that AlexFlipnote is a furry", "Русские Вперёд!"]
image_channels = {'p': 671891617723973652, 'h': 671895023503278080, 'k': 672097261710475294, 'l': 672098660418584586,
                  'c': 675769002613669918, 'b': 675771077057839104, 's': 683486714873905171}
error = "https://cdn.discordapp.com/attachments/673650596913479710/673650677528133649/error.png"
ball_response = [
    'Yes', 'No', 'Take a wild guess...', 'Very doubtful',
    'Sure', 'Without a doubt', 'Most likely', 'Might be possible',
    "You'll be the judge", 'no... (╯°□°）╯︵ ┻━┻', 'no... baka',
    'senpai, pls no ;-;'
]
demons_response = [
    '*wind blows*', 'Go to hell with your stupid questions', 'Well what do you think, huh?',
    'That is very doubtful',
    'Yes, surely', 'Without a doubt', 'Well I guess, most likely', 'That may or may not be possible',
    "I guess you'll be the judge here", 'no... (╯°□°）╯︵ ┻━┻', 'No.',
    'Bruh what the hell? ;-;', 'I guess, yes', "What are you friggin' gay?"
]
hearts = [":heart:", ":orange_heart:", ":yellow_heart:", ":green_heart:", ":blue_heart:", ":purple_heart:",
          ":black_heart:", ":brown_heart:", ":white_heart:"]
hello = ["Good aftermidnight", "Good morning", "Good afternoon", "Good evening"]


async def get_images(bot, what: str):
    """ Get images of a channel """
    channel = bot.get_channel(image_channels[what])
    if channel is None:
        return error
    images = []
    async for message in channel.history(limit=None):
        images.append(message.attachments[0].url)
    return images
