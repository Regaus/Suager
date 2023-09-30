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
    "pat":       671891617723973652,  # images-2-01
    "hug":       671895023503278080,  # images-2-02
    "cuddle":    675769002613669918,  # images-2-03
    "slap":      671897418589143051,  # images-2-04
    "bite":      675771077057839104,  # images-2-05
    "feed":      838566965689581628,  # images-2-06
    "nibble":    977870365764243516,  # images-2-07
    "kiss":      672097261710475294,  # images-2-08
    "lick":      672098660418584586,  # images-2-09
    "sleepy":    683486714873905171,  # images-2-10
    "sniff":     690573072536961075,  # images-2-11
    "cry":       691739503160852591,  # images-2-12
    "blush":     694148497766875186,  # images-2-13
    "smile":     694151734603415632,  # images-2-14
    "highfive":  696485411869950003,  # images-2-15
    "poke":      702280684907003986,  # images-2-16
    "boop":      702280732755624469,  # images-2-17
    "smug":      746166363890122782,  # images-2-18
    "tickle":    746167543290527764,  # images-2-19
    "laugh":     777697466287259679,  # images-2-20
    "dance":     856636461101482014,  # images-2-21
    "handhold":  978747000948408371,  # images-2-22
    "tuck":     1093570818803499038,  # images-2-23
    "wave":     1095379952091803751,  # images-2-24
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


# Lists of users, channels, and servers that are trusted with access to my bot's resources
# List of trusted people last updated 30/09/2023, list of trusted servers last updated 05/05/2023
# Users:         Regaus,             Leitoxz,             Alex Five,           Potato,             Mid,                Noodle
# Users:         Miyamura,           Ash (British),       1337xp,              novanai,            Aya,                Maza,
# Users:         Steir,              PandaBoi,            Suager,              CommanderClicker,   Wight,              Back,
# Users:         Ash/Kollu,          Bvbpig,              Rexy,                Shadow Bread,       Wobbe,              Girlypop,
# Users:         Kyomi,              Mew,                 Humuscular,          Gelleon,            Goomle,             Spliten
# Users:         Mammon,             Zaigou,              Incredulous,         Angelplease1,       Kgaim,              Mocha
# Users:         Jordanbits/Leopill, Tourmaline,          Mikkael_xd,          Johnmiki,           Falou,              Thesolitare
trusted_users = [302851022790066185,  291665491221807104,  430891116318031872, 374853432168808448, 581206591051923466,  411925326780825602,
                 236884090651934721,  499038637631995906,  679819572278198272, 942829514457755738, 527729196688998415,  735902817151090691,
                 230313032956248064,  301091858354929674,  517012611573743621, 660639108674224158, 505486500314611717,  454599329232191488,
                 690895816914763866, 1031347496015904828, 1007129674704498708, 443363116504580117, 808934830171488318,  269971643953184778,
                 417390734690484224,  959193762582634527,  817238112316555265, 472008174195703810, 621204490133176321, 1040772149117452288,
                 302779740542992385,  167474515075399680,  763251241286893568, 591293411961864201, 393401882858487808,  848438776753946624,
                 748842847993724990,  713251686671581225, 1127356589037334628, 680193021593124906, 133614193898291200,  224046307533258752]
# Bad Users:       neppkun,            bowser
untrusted_users = [350199484246130690,  94762492923748352]
# Channels:         rsl-1,              hidden-commands,    secretive-commands, secretive-cmds-2,   Ka. commands,       Ka. discussion,     Ka. lang. disc.
# Channels:         secret-room-1,      secret-room-2,      secret-room-8,      secret-room-10,     secret-room-14,     secret-room-15,     secret-room-17,
# Channels:         secret-room-18,     secret-room-22,     secret-room-24
trusted_channels = [787340111963881472, 610482988123422750, 742885168997466196, 753000962297299005, 938582514166034514, 938587178680864788, 938587585415086140,
                    671520521174777869, 672535025698209821, 725835449502924901, 798513492697153536, 965801985716666428, 969720792457822219, 972112792624726036,
                    999750177181147246, 999750252775084122, 999750295095623753]
# Servers:         Senko Lair,         Regaus'tar Koankadu, Kargadia,          3tk4
trusted_servers = [568148147457490954, 738425418637639775, 928745963877720144, 430945139142426634]
