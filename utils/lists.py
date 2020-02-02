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
playing = ["with Regaus", "Custom Status", "Aqos", "TBL", ",/help"]
image_channels = {'p': 671891617723973652, 'h': 671895023503278080, 'k': 671890334065885184, 'l': 672098660418584586}
error = ["https://cdn.discordapp.com/attachments/603309239884185647/673638035321258004/error.png"]


async def get_images(bot, what: str):
    """ Get images of a channel """
    channel = bot.get_channel(image_channels[what])
    if channel is None:
        return error
    images = []
    async for message in channel.history(limit=None):
        images.append(attachment.url for attachment in message.attachments)
    return images
