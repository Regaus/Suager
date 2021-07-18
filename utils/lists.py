hearts = list("❤️🧡💛💚💙💜🖤🤎🤍")

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
# avatars = ["https://media.discordapp.net/attachments/753000962297299005/826960062928388116/Teletubbies_Square_2.png"]  # Regaus

image_channels = {'p': 671891617723973652, 'h': 671895023503278080, 'k': 672097261710475294, 'l': 672098660418584586,
                  'c': 675769002613669918, 'b': 675771077057839104, 's': 683486714873905171, 'n': 690573072536961075,
                  'r': 691739503160852591, 'v': 671897418589143051, 'u': 694148497766875186, 'm': 694151734603415632,
                  'i': 696485411869950003, 'P': 702280684907003986, 'B': 702280732755624469, 'L': 777697466287259679,
                  't': 746167543290527764, 'd': 856636461101482014}
error = "https://cdn.discordapp.com/attachments/673650596913479710/673650677528133649/error.png"
kl = [
    "https://cdn.discordapp.com/attachments/672097261710475294/672098089233940490/HJce2pdv-.gif",
    "https://cdn.discordapp.com/attachments/672097261710475294/672098116232544256/Bkk_hpdv-.gif",
    "https://cdn.discordapp.com/attachments/672097261710475294/672098207224037406/S1y-4l5Jf.gif",
    "https://cdn.discordapp.com/attachments/672097261710475294/672098272214646805/Byh57gqkz.gif",
    "https://cdn.discordapp.com/attachments/672097261710475294/672098278887784486/ry9uXAFKb.gif",
    "https://cdn.discordapp.com/attachments/672097261710475294/672098365798088704/ryFdQRtF-.gif",
    "https://cdn.discordapp.com/attachments/672097261710475294/673187538424561714/B1NwJg9Jz.gif",
    "https://cdn.discordapp.com/attachments/672097261710475294/675781175687643189/rkde2aODb.gif"
]


async def get_images(bot, what: str):
    """ Get images of a channel """
    channel = bot.get_channel(image_channels[what])
    if channel is None:
        return [error]
    images = []
    async for message in channel.history(limit=None):
        images.append(message.attachments[0].url)
    return images
