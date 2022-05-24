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

image_channels = {
    "pat":      671891617723973652,  # images-2-1
    "hug":      671895023503278080,  # images-2-2a
    "cuddle":   675769002613669918,  # images-2-2b
    "slap":     671897418589143051,  # images-2-3a
    "bite":     675771077057839104,  # images-2-3b
    "feed":     838566965689581628,  # images-2-3c
    "nibble":   977870365764243516,  # images-2-3d
    "kiss":     672097261710475294,  # images-2-4
    "lick":     672098660418584586,  # images-2-5
    "sleepy":   683486714873905171,  # images-2-6
    "sniff":    690573072536961075,  # images-2-7
    "cry":      691739503160852591,  # images-2-8
    "blush":    694148497766875186,  # images-2-9
    "smile":    694151734603415632,  # images-2-10
    "highfive": 696485411869950003,  # images-2-11
    "poke":     702280684907003986,  # images-2-12
    "boop":     702280732755624469,  # images-2-13
    "smug":     746166363890122782,  # images-2-14
    "tickle":   746167543290527764,  # images-2-15
    "laugh":    777697466287259679,  # images-2-16
    "dance":    856636461101482014,  # images-2-17
    "handhold": 978747000948408371,  # images-2-18
}


async def get_images(bot, what: str):
    """ Get images of a channel """
    channel = bot.get_channel(image_channels[what])
    if channel is None:
        return [error]
    images = []
    async for message in channel.history(limit=None):
        images.append(message.attachments[0].url)
    return images
