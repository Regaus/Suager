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
server_icons = ["https://cdn.discordapp.com/attachments/714583916706791494/714583957785673879/0.png",
                "https://cdn.discordapp.com/attachments/714583916706791494/714584123485978736/1.png",
                "https://cdn.discordapp.com/attachments/714583916706791494/714584148387430491/2.png",
                "https://cdn.discordapp.com/attachments/714583916706791494/714584179949436949/3.png",
                "https://cdn.discordapp.com/attachments/714583916706791494/714584188397027440/4.png",
                "https://cdn.discordapp.com/attachments/714583916706791494/714584195703504926/5.png",
                "https://cdn.discordapp.com/attachments/714583916706791494/714584202611392542/6.png",
                "https://cdn.discordapp.com/attachments/714583916706791494/714584211360841738/7.png",
                "https://cdn.discordapp.com/attachments/714583916706791494/714584222051991552/8.png",
                "https://cdn.discordapp.com/attachments/714583916706791494/714584228150640721/9.png",
                "https://cdn.discordapp.com/attachments/714583916706791494/714584238686732319/10.png",
                "https://cdn.discordapp.com/attachments/714583916706791494/714584244940439593/11.png"]
playing = ["with Regaus", "without you", "with nobody", "alone", "Custom Status", "with the Nuriki Cult", "PyCharm", "Русские Вперёд!", ",/help", "nothing"]
phrases = ["Imagine not being forced to work 24/7", "Reminder that AlexFlipnote is a furry", "Русские Вперёд!", "Imagine using decimal"]
image_channels = {'p': 671891617723973652, 'h': 671895023503278080, 'k': 672097261710475294, 'l': 672098660418584586,
                  'c': 675769002613669918, 'b': 675771077057839104, 's': 683486714873905171, 'n': 690573072536961075,
                  'r': 691739503160852591, 'v': 671897418589143051, 'u': 694148497766875186, 'm': 694151734603415632,
                  'i': 696485411869950003, 'P': 702280684907003986, 'B': 702280732755624469}
error = "https://cdn.discordapp.com/attachments/673650596913479710/673650677528133649/error.png"
ball_response = ['Yes', 'No', 'Take a wild guess...', 'Very doubtful', 'Sure', 'Without a doubt', 'Most likely', 'Might be possible',
                 "You'll be the judge", 'No. (╯°□°）╯︵ ┻━┻', 'Highly unlikely', 'You really think so?', 'Why would you think that?',
                 "Isn't the answer obvious?", 'Of course not!', 'Of course, yes!']
hearts = list("❤️🧡💛💚💙💜🖤🤎🤍")
hello = ["Good aftermidnight", "Good morning", "Good afternoon", "Good evening"]


async def get_images(bot, what: str):
    """ Get images of a channel """
    channel = bot.get_channel(image_channels[what])
    if channel is None:
        return [error]
    images = []
    async for message in channel.history(limit=None):
        images.append(message.attachments[0].url)
    return images
