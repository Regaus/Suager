from datetime import datetime, timezone

locations = [
    {
        "id": 1,
        "name": "Leitennan Azdalat",
        "ru": "Летающие Острова",
        "en": "Floating Islands",
        "desc_en": "Somewhere behind ancient pines, huge mountains and fluffy clouds, bathing in the rays of sun lie the Soaring Heights, where newbies "
                   "set out on their long journey.",
        "desc_ru": "Где-то за древними соснами, огромными горами и пушистыми облаками, в лучах солнца купаются Парящие Вершины, "
                   "где новички начинают свой путь.",
        "energy": 10,
        "araksan": [4, 7],
        "xp": [20, 40],
        "sh": 4,
        "points": [25, 60],
        "level": 0,
        "activity": [1721, 2744, 5072, 5742, 5231, 3101, 1402, 907],  # Activity - 0 to 4 KST, etc. -- Goes up to 32 "hours" -- Midnight == morning
        "act": 30,  # Avg. level completion time
        "dr": 0.07,  # Death/Failure rate
        "ll": 90,  # Level length
    },
    {
        "id": 2,
        "name": "Haltavaidaan Kirtinnat",
        "ru": "Снежные Горы",
        "en": "Snowy Mountains",
        "desc_en": "In the far north lie the Snow Mountains. Here live the squirrels with the warmest coats. "
                   "The cold and the icy slopes are the squirrels' main enemies in the mountains.",
        "desc_ru": "На дальнем севере раскинулись Снежные Горы. Здесь обитают белки с самыми теплыми шубками. "
                   "Холод и обледенелые склоны - главные беличьи враги в горах.",
        "energy": 10,
        "araksan": [5, 7],
        "xp": [27, 50],
        "sh": 6,
        "points": [35, 70],
        "level": 7,
        "activity": [1278, 2231, 4712, 5232, 4729, 4121, 2109, 702],  # Activity: 0:00 to 4:00 IST and so on
        "act": 45,  # Avg. level completion time
        "dr": 0.15,  # Death rate
        "ll": 105,
    },
    {
        "id": 3,
        "name": "Taivead",
        "ru": "Топи",
        "en": "The Swamps",
        "desc_en": "Long ago in the place of a wonderful forest an impassable swamp had formed.",
        "desc_ru": "Когда-то давно на месте чудесного леса образовалось труднопроходимое болото.",
        "energy": 10,
        "araksan": [7, 9],
        "xp": [40, 60],
        "sh": 7,
        "points": [50, 100],
        "level": 12,
        "activity": [2037, 3662, 4039, 4794, 6078, 4282, 2103, 1002],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 50,  # Avg. level completion time
        "dr": 0.17,  # Death rate
        "ll": 120,
    },
    {
        "id": 4,
        "name": "Havastangar",
        "ru": "Хвостоград",
        "en": "Tail Town",
        "desc_en": "This is the last remaining in the squirrel world. Most business happens in here, although you wouldn't find those who choose to go the "
                   "path of adventure and decide to prepare for the upcoming catastrophe here.",
        "desc_ru": "На данный момент самый успешный беличий город. Большинство бизнеса здесь, но вряд ли ты здесь "
                   "найдешь тех, кто пошли по пути приключения, и готовятся к наступающей катастрофе.",
        "energy": 10,
        "araksan": [9, 11],
        "xp": [50, 75],
        "sh": 9,
        "points": [75, 100],
        "level": 17,
        "activity": [2742, 4932, 7932, 9251, 9742, 5821, 2174, 1210],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 60,  # Avg. level completion time
        "dr": 0.17,  # Death rate
        "ll": 130,
    },
    {
        "id": 5,
        "name": "Sennan Dailannat",
        "ru": "Солнечные Долины",
        "en": "Sunny Valleys",
        "desc_en": "The sunny valleys were created by a sudden cataclysm. It's the ideal place for young squirrels. "
                   "In the summer the grass is warm, and in the winter there's lots of snow - it can't get any better!",
        "desc_ru": "Солнечные долины были созданы внезапным катаклизмом... Идеальное место для молодых белок. Летом "
                   "теплая трава, а зимой много снега - лучше не бывает!",
        "energy": 10,
        "araksan": [11, 14],
        "xp": [60, 85],
        "sh": 11,
        "points": [100, 150],
        "level": 20,
        "activity": [2013, 3719, 6744, 7421, 5321, 3712, 1937, 871],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 65,  # Avg. level completion time
        "dr": 0.2,  # Death rate
        "ll": 140,
    },
    {
        "id": 6,
        "name": "Seina Vandaa",
        "ru": "Синее Море",
        "en": "The Blue Sea",
        "desc_en": "A lot of water, fish, seaweed and hard obstacles. The major part of the Blue Sea had dried up and "
                   "turned into a desert, and in what remains of the sea the squirrels don't have any time for rest.",
        "desc_ru": "Много-много воды, рыбки, водоросли и сложные препятствия. Большая часть Синего Моря иссохла и "
                   "превратилась в Пустыню, а в остатках белкам не до отдыха.",
        "energy": 10,
        "araksan": [14, 17],
        "xp": [70, 100],
        "sh": 13,
        "points": [150, 225],
        "level": 22,
        "activity": [1372, 2371, 3281, 3471, 2973, 2019, 938, 173],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 75,  # Avg. level completion time
        "dr": 0.22,  # Death rate
        "ll": 150,
    },
    {
        "id": 7,
        "name": "Dan Veilaran Bylkaden Peaskat",
        "ru": "Великая Беличья Пустыня",
        "en": "The Great Squirrels' Desert",
        "desc_en": "The sandy desert formed in the place of the dried up Old Sea. Only the bravest squirrels depart here on their long adventure "
                   "in search for treasure.",
        "desc_ru": "Песчаная пустыня раскинулась на месте пересохшего Синего Моря. Только самые смелые белки "
                   "отправляются сюда в долгое путешествие на поиски сокровищ.",
        "energy": 10,
        "araksan": [17, 20],
        "xp": [85, 150],
        "sh": 17,
        "points": [225, 375],
        "level": 25,
        "activity": [2479, 4789, 4482, 4672, 4272, 4102, 3121, 2377],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 90,  # Avg. level completion time
        "dr": 0.27,  # Death rate
        "ll": 160,
    },
    {
        "id": 8,
        "name": "Naitenne Heiste",
        "ru": "Дикие Земли",
        "en": "The Wild Lands",
        "desc_en": "The mystery of these lands remained unsolved for a long while. The monster guarding this place had suddenly disappeared "
                   "without a trace, and the brave ones were able to enter into the dark bowels of the red lands.",
        "desc_ru": "Тайна диких земель долго оставалась не раскрытой. Чудовище бесследно исчезло, а храбрецы смогли войти в темные недра красных земель.",
        "energy": 10,
        "araksan": [20, 25],
        "xp": [100, 175],
        "sh": 20,
        "points": [300, 500],
        "level": 28,
        "activity": [138, 526, 1411, 2011, 1824, 794, 103, 27],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 100,  # Avg. level completion time
        "dr": 0.28,  # Death rate
        "ll": 170,
    },
    {
        "id": 9,
        "name": "Pulkannat Diaran Vaitekan",
        "ru": "Равнины Штормов",
        "en": "The Plains of Storms",
        "desc_en": "Right in the center of the planet a storm started to rage. Dangers that would chill your soul await those who dare enter here.",
        "desc_ru": "В самом центре планеты разбушевался шторм. Леденящие душу опасности ожидают тех, кто осмелился сюда зайти.",
        "energy": 10,
        "araksan": [25, 30],
        "xp": [125, 190],
        "sh": 24,
        "points": [450, 750],
        "level": 32,
        "activity": [1021, 1741, 3272, 3673, 3109, 1315, 972, 748],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 110,  # Avg. level completion time
        "dr": 0.3,  # Death rate
        "ll": 180,
    },
    {
        "id": 10,
        "name": "Da Koirannat Kiiteivalladan",
        "ru": "Вершины Испытаний",
        "en": "The Challenge Heights",
        "desc_en": "Squads of the most brave and skilled squirrels head to the Challenge Heights to show what they're capable of.",
        "desc_ru": "Отряды самых смелых и умелых белок направляются в Испытания, чтобы показать, на что они способны.",
        "energy": 10,
        "araksan": [27, 35],
        "xp": [150, 210],
        "sh": 27,
        "points": [600, 900],
        "level": 37,
        "activity": [2174, 4572, 6022, 7042, 7213, 6123, 4271, 2019],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 125,  # Avg. level completion time
        "dr": 0.32,  # Death rate
        "ll": 190,
    },
    {
        "id": 11,
        "name": "Dar Lias",
        "ru": "Сосновый Бор",
        "en": "The Pine Forest",
        "desc_en": "The forest is a good place to lose yourself behind the trunks of trees, hop on branches and throw cones at each other.",
        "desc_ru": "В лесу хорошо потеряться за стволами, скакать по веткам и швырять друг в друга шишками.",
        "energy": 10,
        "araksan": [32, 40],
        "xp": [200, 300],
        "sh": 32,
        "points": [800, 1200],
        "level": 42,
        "activity": [1738, 2841, 4821, 5689, 5372, 3121, 1821, 1221],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 95,  # Avg. level completion time
        "dr": 0.33,  # Death rate
        "ll": 200,
    },
    {
        "id": 12,
        "name": "Heiste Anomaliadan",
        "ru": "Аномальная Зона",
        "en": "Anomalous Zone",
        "desc_en": "By the will of evil fate, a meteorite fell right onto the first Ship of Salvation. The anomalous zone formed in the place of the ship.",
        "desc_ru": "Волей злодейки-судьбы метеорит упал прямо на Корабль Спасения. На месте корабля образовалась Аномальная Зона.",
        "energy": 10,
        "araksan": [40, 50],
        "xp": [250, 375],
        "sh": 40,
        "points": [1000, 1500],
        "level": 50,
        "activity": [9472, 21021, 42190, 46278, 42281, 37281, 21492, 6411],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 110,  # Avg. level completion time
        "dr": 0.4,  # Death rate
        "ll": 210,
    },
    {
        "id": 13,
        "name": "Teimanheiste",
        "ru": "Пещера",
        "en": "The Cave",
        "desc_en": "It's dark and scary here, but it doesn't bother some at all.",
        "desc_ru": "Здесь темно и страшно, но некоторых это ни капли не останавливает.",
        "energy": 10,
        "araksan": [50, 70],
        "xp": [300, 450],
        "sh": 50,
        "points": [1250, 2000],
        "level": 60,
        "activity": [2714, 3052, 3265, 3752, 3252, 2912, 2711, 2411],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 100,  # Avg. level completion time
        "dr": 0.43,  # Death rate
        "ll": 220,
    },
    {
        "id": 14,
        "name": "Da Garraikirtinna Temantan",
        "ru": "Вулкан Теней",
        "en": "The Volcano of Shadows",
        "desc_en": "Although it hasn't erupted in a long while, there are legends that when it does, the entire sky will be covered in ash and you wouldn't "
                   "be able to see anything.",
        "desc_ru": "Хоть уже давно он не извергался, ходят легенды, что когда это происходит, все небо покроется пеплом и ничего не будет видно.",
        "energy": 10,
        "araksan": [60, 80],
        "xp": [400, 600],
        "sh": 60,
        "points": [1500, 2250],
        "level": 70,
        "activity": [1411, 2245, 3721, 4342, 4722, 4102, 2849, 1092],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 105,  # Avg. level completion time
        "dr": 0.44,  # Death rate
        "ll": 230,
    },
    {
        "id": 15,
        "name": "Da Neireideda Laitaa",
        "ru": "Потонувший Корабль",
        "en": "The Sunken Ship",
        "desc_en": "Once upon a time, humans invented a ship. But something went wrong and it sank. Well, what did you expect from humans?",
        "desc_ru": "Однажды люди изобрели корабль. Но что-то пошло не так, и он затонул... А что вы от людей ожидали?",
        "energy": 10,
        "araksan": [70, 90],
        "xp": [500, 750],
        "sh": 70,
        "points": [1750, 2625],
        "level": 80,
        "activity": [702, 922, 1264, 1121, 1071, 782, 597, 309],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 120,  # Avg. level completion time
        "dr": 0.43,  # Death rate
        "ll": 240,
    },
    {
        "id": 16,
        "name": "Da Seinara Teivavaidaa",
        "ru": "Южные Льды",
        "en": "The Southern Ice",
        "desc_en": "It's really cold there... Nobody knows why they do that. What are they looking for in this frozen middle of nowhere?",
        "desc_ru": "Очень холодно... Зачем они туда идут? Что им лед сделал, что они так сильно хотят узнать что находится что в этой пустоте замерзшей?",
        "energy": 10,
        "araksan": [85, 105],
        "xp": [600, 900],
        "sh": 85,
        "points": [2000, 3000],
        "level": 90,
        "activity": [1074, 1195, 1722, 2111, 2421, 1983, 1211, 673],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 115,  # Avg. level completion time
        "dr": 0.47,  # Death rate
        "ll": 250,
    },
    {
        "id": 17,
        "name": "Da Deva Laitaa Deaktanvan",
        "ru": "Корабль Спасения",
        "en": "The Second Ship of Salvation",
        "desc_en": "Scientists didn't give up and built the second Ship of Salvation to escape the planet. This is the only hope for salvation.",
        "desc_ru": "Ученые не сдались, и построили второй Корабль Спасения, чтобы сбежать с планеты. Это единственная надежда на спасение.",
        "energy": 10,
        "araksan": [100, 150],
        "xp": [750, 1000],
        "sh": 100,
        "points": [2500, 3750],
        "level": 100,
        "activity": [20729, 27134, 31453, 37422, 35242, 31221, 26311, 21422],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 120,  # Minimal completion time
        "dr": 0.27,  # Death rate
        "ll": 270,
    }
]


totems = [
    {
        "name": "Totem of Growth",
        "desc": "Provides you with **%s more Nuts**.",
        "name_ru": "Тотем Роста",
        "desc_ru": "Создает на %s больше орехов.",  # 1.08 + 0.02 * level
    },
    {
        "name": "Totem of Coolness",
        "desc": "You get **%s more XP** and become cool faster.",
        "name_ru": "Тотем Крутости",
        "desc_ru": "Получаешь на %s больше опыта - быстрее становишься крутым.",  # 1.06 + 0.04 * level
    },
    {
        "name": "Totem of Shamanery",
        "desc": "You become a cooler shaman, you get **%s more Shaman XP**",
        "name_ru": "Тотем Шаманства",
        "desc_ru": "Ты - крутой шаман. За это ты получаешь на %s больше опыта шамана.",  # 1.075 + 0.025 * level
    },
    {
        "name": "Totem of Senko",
        "desc": "Now at least one more person cares about you. No real effect.",
        "name_ru": "Тотем Сенко",
        "desc_ru": "Теперь хотя бы один человек заботится о тебе.\nНет эффекта.",
    },
    {
        "name": "Totem of Cthulhu",
        "desc": "Well, uh.. Why not? At least it makes this even weirder. No real effect.",
        "name_ru": "Тотем Ктулху",
        "desc_ru": "Ну а почему бы и нет?\nНет эффекта.",
    },
]


def gls(val: str, lang: str = "en"):
    if lang == "en":
        tr = {
            "Новичок": "Newbie",
            "Обаяшка": "Charming One",
            "Надежда племени": "Tribe's Hope",
            "Любитель орехов": "Araksan Lover",
            "Упрямец": "Stubborn One",
            "Исследователь": "Explorer",
            "Орехбургер": "Nut-burger",
            "Виртуоз": "Virtuoso",
            "Гордость семьи": "Family Pride",
            "Любимец племени": "Tribe's Favourite",
            "Герой": "Hero",
            "Ураган": "Hurricane",
            "Старожил": "Old Timer",
            "Чемпион": "Champion",
            "Славный воин": "Glorious Warrior",
            "Матерая белка": "Squirrel Full of Strength",
            "Рыжий зверь": "Orange Animal",
            "Избранный": "The Chosen One",
            "Красная масть": "Red Suit",
            "Звезда": "Star",
            "Огненный смерч": "Fiery Tornado",
            "Комета": "Comet",
            "Игроман": "Gamer",
            "Неуловимый": "Elusive",
            "Молниеносный": "Fulminant",
            "Властитель": "Ruler",
            "Космобелка": "Cosmo-squirrel",
            "Орехоман": "Araksan Addict",
            "Смельчак": "Daredevil",
            "Бывалый": "Experienced",
            "Весельчак": "Humorist",
            "Гончий": "Hound",
            "Неистовый": "Frantic",
            "Шумахер": "Racer",
            "Стремительный": "Swift",
            "Просветленный": "Enlightened",
            "Долгожитель": "Long-liver",
            "Знаток": "Expert",
            "Ветеран": "Veteran",
            "Непоседа": "Fidget",
            "Профессионал": "Professional",
            "Следопыт": "Pathfinder",
            "Хвастунишка": "Braggart",
            "Экстремал": "Extremal",
            "МегаБелка": "MegaSquirrel",
            "Вождь": "Leader",
            "Просвещенный": "Enlightened",
            "Царь-Белка": "Tsar-Squirrel",
            "Самая лучшая белка": "The Best Squirrel",
            "Чак Норрис": "Chuck Norris",
            "Чудесный": "Wonderful",
            "Неустрашимый": "Intrepid",
            "Терпеливый": "Patient",
            "Суровый": "Stern",
            "Созерцатель": "Contemplative",
            "Проницательный": "Insightful",
            "Обожаемый": "Adorable",
            "Неукротимый": "Indomitable",
            "Магистр": "Master",
            "Необузданный": "Unbridled",
            "Искатель": "Explorer",
            "Бесстрашный": "Fearless",
            "Неумолимый": "Inexorable",
            "Бессмертный": "Immortal",
            "Испытанный": "Challenged",
            "Божественный": "God-like",
            "Чокнутый": "Bonkers"
        }
        return tr.get(val, val.title())
    return val


leagues = [
    {
        "name": "None",
        "score": 0
    }, {
        "name": "Bronze I",
        "score": 500
    }, {
        "name": "Bronze II",
        "score": 1250
    }, {
        "name": "Bronze III",
        "score": 2000
    }, {
        "name": "Silver I",
        "score": 3000
    }, {
        "name": "Silver II",
        "score": 4000
    }, {
        "name": "Silver III",
        "score": 5000
    }, {
        "name": "Gold I",
        "score": 6000
    }, {
        "name": "Gold II",
        "score": 7000
    }, {
        "name": "Gold III",
        "score": 8500
    }, {
        "name": "Diamond I",
        "score": 10000
    }, {
        "name": "Diamond II",
        "score": 20000
    }, {
        "name": "Diamond III",
        "score": 30000
    }, {
        "name": "Diamond IV",
        "score": 40000
    }, {
        "name": "Master I",
        "score": 50000
    }, {
        "name": "Master II",
        "score": 60000
    }, {
        "name": "Master III",
        "score": 70000
    }, {
        "name": "Master IV",
        "score": 80000
    }, {
        "name": "Master V",
        "score": 90000
    }, {
        "name": "Champion I",
        "score": 100000
    }, {
        "name": "Champion II",
        "score": 250000
    }, {
        "name": "Champion III",
        "score": 500000
    }, {
        "name": "Champion IV",
        "score": 1000000
    }, {
        "name": "Champion V",
        "score": 5000000
    },  {
        "name": "Ultimate Champion",
        "score": 25000000
    }
]


xp_levels = [
    {
        "experience": 0,
        "title": gls("Новичок")
    }, {
        "experience": 50,
        "title": gls("Новичок")
    }, {
        "experience": 110,
        "title": gls("Новичок")
    }, {
        "experience": 200,
        "title": gls("Обаяшка")
    }, {
        "experience": 300,
        "title": gls("Обаяшка")
    }, {
        "experience": 425,
        "title": gls("Обаяшка")
    }, {
        "experience": 590,
        "title": gls("Надежда племени")
    }, {
        "experience": 1090,
        "title": gls("Надежда племени")
    }, {
        "experience": 2565,
        "title": gls("Надежда племени")
    }, {
        "experience": 5015,
        "title": gls("Любитель орехов")
    }, {
        "experience": 8640,
        "title": gls("Любитель орехов")
    }, {
        "experience": 13340,
        "title": gls("Любитель орехов")
    }, {
        "experience": 19115,
        "title": gls("Упрямец")
    }, {
        "experience": 25965,
        "title": gls("Упрямец")
    }, {
        "experience": 33890,
        "title": gls("Упрямец")
    }, {
        "experience": 42890,
        "title": gls("Исследователь")
    }, {
        "experience": 50640,
        "title": gls("Исследователь")
    }, {
        "experience": 57230,
        "title": gls("Исследователь")
    }, {
        "experience": 62840,
        "title": gls("Орехбургер")
    }, {
        "experience": 67610,
        "title": gls("Орехбургер")
    }, {
        "experience": 71670,
        "title": gls("Орехбургер")
    }, {
        "experience": 75125,
        "title": gls("Виртуоз")
    }, {
        "experience": 78065,
        "title": gls("Виртуоз")
    }, {
        "experience": 80565,
        "title": gls("Виртуоз")
    }, {
        "experience": 83065,
        "title": gls("Гордость семьи")
    }, {
        "experience": 86055,
        "title": gls("Гордость семьи")
    }, {
        "experience": 89635,
        "title": gls("Гордость семьи")
    }, {
        "experience": 93915,
        "title": gls("Любимец племени")
    }, {
        "experience": 99035,
        "title": gls("Любимец племени")
    }, {
        "experience": 105165,
        "title": gls("Любимец племени")
    }, {
        "experience": 112500,
        "title": gls("Герой")
    }, {
        "experience": 121275,
        "title": gls("Герой")
    }, {
        "experience": 131775,
        "title": gls("Герой")
    }, {
        "experience": 139515,
        "title": gls("Ураган")
    }, {
        "experience": 147580,
        "title": gls("Ураган")
    }, {
        "experience": 155985,
        "title": gls("Ураган")
    }, {
        "experience": 164740,
        "title": gls("Старожил")
    }, {
        "experience": 173860,
        "title": gls("Старожил")
    }, {
        "experience": 183360,
        "title": gls("Старожил")
    }, {
        "experience": 193260,
        "title": gls("Чемпион")
    }, {
        "experience": 203575,
        "title": gls("Чемпион")
    }, {
        "experience": 214325,
        "title": gls("Чемпион")
    }, {
        "experience": 225525,
        "title": gls("Славный воин")
    }, {
        "experience": 237195,
        "title": gls("Славный воин")
    }, {
        "experience": 249350,
        "title": gls("Славный воин")
    }, {
        "experience": 262015,
        "title": gls("Матерая белка")
    }, {
        "experience": 275210,
        "title": gls("Матерая белка")
    }, {
        "experience": 288955,
        "title": gls("Матерая белка")
    }, {
        "experience": 303275,
        "title": gls("Рыжий зверь")
    }, {
        "experience": 318195,
        "title": gls("Рыжий зверь")
    }, {
        "experience": 333740,
        "title": gls("Рыжий зверь")
    }, {
        "experience": 349935,
        "title": gls("Избранный")
    }, {
        "experience": 366805,
        "title": gls("Избранный")
    }, {
        "experience": 384385,
        "title": gls("Избранный")
    }, {
        "experience": 402700,
        "title": gls("Красная масть")
    }, {
        "experience": 421780,
        "title": gls("Красная масть")
    }, {
        "experience": 441660,
        "title": gls("Красная масть")
    }, {
        "experience": 462370,
        "title": gls("Звезда")
    }, {
        "experience": 483950,
        "title": gls("Звезда")
    }, {
        "experience": 506430,
        "title": gls("Звезда")
    }, {
        "experience": 529850,
        "title": gls("Огненный смерч")
    }, {
        "experience": 554250,
        "title": gls("Огненный смерч")
    }, {
        "experience": 579670,
        "title": gls("Огненный смерч")
    }, {
        "experience": 606160,
        "title": gls("Комета")
    }, {
        "experience": 633755,
        "title": gls("Комета")
    }, {
        "experience": 662505,
        "title": gls("Комета")
    }, {
        "experience": 691255,
        "title": gls("Игроман")
    }, {
        "experience": 719795,
        "title": gls("Игроман")
    }, {
        "experience": 748130,
        "title": gls("Игроман")
    }, {
        "experience": 776260,
        "title": gls("Неуловимый")
    }, {
        "experience": 804185,
        "title": gls("Неуловимый")
    }, {
        "experience": 831905,
        "title": gls("Неуловимый")
    }, {
        "experience": 859425,
        "title": gls("Молниеносный")
    }, {
        "experience": 886745,
        "title": gls("Молниеносный")
    }, {
        "experience": 913865,
        "title": gls("Молниеносный")
    }, {
        "experience": 940790,
        "title": gls("Властитель")
    }, {
        "experience": 967520,
        "title": gls("Властитель")
    }, {
        "experience": 994055,
        "title": gls("Властитель")
    }, {
        "experience": 1020395,
        "title": gls("Космобелка")
    }, {
        "experience": 1046545,
        "title": gls("Космобелка")
    }, {
        "experience": 1072745,
        "title": gls("Космобелка")
    }, {
        "experience": 1099120,
        "title": gls("Орехоман")
    }, {
        "experience": 1125670,
        "title": gls("Орехоман")
    }, {
        "experience": 1152400,
        "title": gls("Орехоман")
    }, {
        "experience": 1179310,
        "title": gls("Смельчак")
    }, {
        "experience": 1206400,
        "title": gls("Смельчак")
    }, {
        "experience": 1233670,
        "title": gls("Смельчак")
    }, {
        "experience": 1261125,
        "title": gls("Бывалый")
    }, {
        "experience": 1288765,
        "title": gls("Бывалый")
    }, {
        "experience": 1316590,
        "title": gls("Бывалый")
    }, {
        "experience": 1344600,
        "title": gls("Весельчак")
    }, {
        "experience": 1372800,
        "title": gls("Весельчак")
    }, {
        "experience": 1401190,
        "title": gls("Весельчак")
    }, {
        "experience": 1429770,
        "title": gls("Гончий")
    }, {
        "experience": 1458540,
        "title": gls("Гончий")
    }, {
        "experience": 1487500,
        "title": gls("Гончий")
    }, {
        "experience": 1516660,
        "title": gls("Неистовый")
    }, {
        "experience": 1546010,
        "title": gls("Неистовый")
    }, {
        "experience": 1575560,
        "title": gls("Неистовый")
    }, {
        "experience": 1605310,
        "title": gls("Шумахер")
    }, {
        "experience": 1635260,
        "title": gls("Шумахер")
    }, {
        "experience": 1665410,
        "title": gls("Шумахер")
    }, {
        "experience": 1695760,
        "title": gls("Стремительный")
    }, {
        "experience": 1726310,
        "title": gls("Стремительный")
    }, {
        "experience": 1757070,
        "title": gls("Стремительный")
    }, {
        "experience": 1788035,
        "title": gls("Просветленный")
    }, {
        "experience": 1819205,
        "title": gls("Просветленный")
    }, {
        "experience": 1850585,
        "title": gls("Просветленный")
    }, {
        "experience": 1882175,
        "title": gls("Долгожитель")
    }, {
        "experience": 1913975,
        "title": gls("Долгожитель")
    }, {
        "experience": 1945990,
        "title": gls("Долгожитель")
    }, {
        "experience": 1978220,
        "title": gls("Знаток")
    }, {
        "experience": 2010665,
        "title": gls("Знаток")
    }, {
        "experience": 2043330,
        "title": gls("Знаток")
    }, {
        "experience": 2076215,
        "title": gls("Ветеран")
    }, {
        "experience": 2109320,
        "title": gls("Ветеран")
    }, {
        "experience": 2142645,
        "title": gls("Ветеран")
    }, {
        "experience": 2176195,
        "title": gls("Непоседа")
    }, {
        "experience": 2209970,
        "title": gls("Непоседа")
    }, {
        "experience": 2243970,
        "title": gls("Непоседа")
    }, {
        "experience": 2278370,
        "title": gls("Профессионал")
    }, {
        "experience": 2314270,
        "title": gls("Профессионал")
    }, {
        "experience": 2351735,
        "title": gls("Профессионал")
    }, {
        "experience": 2390830,
        "title": gls("Следопыт")
    }, {
        "experience": 2431630,
        "title": gls("Следопыт")
    }, {
        "experience": 2474210,
        "title": gls("Следопыт")
    }, {
        "experience": 2518645,
        "title": gls("Хвастунишка")
    }, {
        "experience": 2565015,
        "title": gls("Хвастунишка")
    }, {
        "experience": 2613405,
        "title": gls("Хвастунишка")
    }, {
        "experience": 2663905,
        "title": gls("Экстремал")
    }, {
        "experience": 2716605,
        "title": gls("Экстремал")
    }, {
        "experience": 2771605,
        "title": gls("Экстремал")
    }, {
        "experience": 2828995,
        "title": gls("МегаБелка")
    }, {
        "experience": 2888890,
        "title": gls("МегаБелка")
    }, {
        "experience": 2951395,
        "title": gls("МегаБелка")
    }, {
        "experience": 3016625,
        "title": gls("Вождь")
    }, {
        "experience": 3084695,
        "title": gls("Вождь")
    }, {
        "experience": 3155735,
        "title": gls("Вождь")
    }, {
        "experience": 3229865,
        "title": gls("Просвещенный")
    }, {
        "experience": 3307225,
        "title": gls("Просвещенный")
    }, {
        "experience": 3387960,
        "title": gls("Просвещенный")
    }, {
        "experience": 3472210,
        "title": gls("Царь-Белка")
    }, {
        "experience": 3560130,
        "title": gls("Царь-Белка")
    }, {
        "experience": 3651885,
        "title": gls("Царь-Белка")
    }, {
        "experience": 3747635,
        "title": gls("Самая лучшая белка")
    }, {
        "experience": 3847560,
        "title": gls("Самая лучшая белка")
    }, {
        "experience": 3951840,
        "title": gls("Самая лучшая белка")
    }, {
        "experience": 4060665,
        "title": gls("Чак Норрис")
    }, {
        "experience": 4174230,
        "title": gls("Чак Норрис")
    }, {
        "experience": 4292745,
        "title": gls("Чак Норрис")
    }, {
        "experience": 4416425,
        "title": gls("Чудесный")
    }, {
        "experience": 4545495,
        "title": gls("Чудесный")
    }, {
        "experience": 4680190,
        "title": gls("Чудесный")
    }, {
        "experience": 4820755,
        "title": gls("Неустрашимый")
    }, {
        "experience": 4967445,
        "title": gls("Неустрашимый")
    }, {
        "experience": 5120525,
        "title": gls("Неустрашимый")
    }, {
        "experience": 5280275,
        "title": gls("Терпеливый")
    }, {
        "experience": 5446985,
        "title": gls("Терпеливый")
    }, {
        "experience": 5620960,
        "title": gls("Терпеливый")
    }, {
        "experience": 5799935,
        "title": gls("Суровый")
    }, {
        "experience": 5989405,
        "title": gls("Суровый")
    }, {
        "experience": 6187135,
        "title": gls("Суровый")
    }, {
        "experience": 6393480,
        "title": gls("Созерцатель")
    }, {
        "experience": 6608815,
        "title": gls("Созерцатель")
    }, {
        "experience": 6833535,
        "title": gls("Созерцатель")
    }, {
        "experience": 7068045,
        "title": gls("Проницательный")
    }, {
        "experience": 7312775,
        "title": gls("Проницательный")
    }, {
        "experience": 7568175,
        "title": gls("Проницательный")
    }, {
        "experience": 7834700,
        "title": gls("Обожаемый")
    }, {
        "experience": 8112840,
        "title": gls("Обожаемый")
    }, {
        "experience": 8403100,
        "title": gls("Обожаемый")
    }, {
        "experience": 8706010,
        "title": gls("Неукротимый")
    }, {
        "experience": 9022120,
        "title": gls("Неукротимый")
    }, {
        "experience": 9352005,
        "title": gls("Неукротимый")
    }, {
        "experience": 9696265,
        "title": gls("Магистр")
    }, {
        "experience": 10055525,
        "title": gls("Магистр")
    }, {
        "experience": 10430440,
        "title": gls("Магистр")
    }, {
        "experience": 10733350,
        "title": gls("Необузданный")
    }, {
        "experience": 11084726,
        "title": gls("Необузданный")
    }, {
        "experience": 11492322,
        "title": gls("Необузданный")
    }, {
        "experience": 11965133,
        "title": gls("Магистр")
    }, {
        "experience": 12513594,
        "title": gls("Магистр")
    }, {
        "experience": 13149808,
        "title": gls("Магистр")
    }, {
        "experience": 13887817,
        "title": gls("Искатель")
    }, {
        "experience": 14743907,
        "title": gls("Искатель")
    }, {
        "experience": 15736972,
        "title": gls("Искатель")
    }, {
        "experience": 16888927,
        "title": gls("Бесстрашный")
    }, {
        "experience": 18225195,
        "title": gls("Бесстрашный")
    }, {
        "experience": 19775266,
        "title": gls("Бесстрашный")
    }, {
        "experience": 21573348,
        "title": gls("Неумолимый")
    }, {
        "experience": 23659123,
        "title": gls("Неумолимый")
    }, {
        "experience": 26078622,
        "title": gls("Неумолимый")
    }, {
        "experience": 28885241,
        "title": gls("Бессмертный")
    }, {
        "experience": 32140919,
        "title": gls("Бессмертный")
    }, {
        "experience": 35917505,
        "title": gls("Бессмертный")
    }, {
        "experience": 40298345,
        "title": gls("Испытанный")
    }, {
        "experience": 45380120,
        "title": gls("Испытанный")
    }, {
        "experience": 51274979,
        "title": gls("Испытанный")
    }, {
        "experience": 58113015,
        "title": gls("Божественный")
    }, {
        "experience": 66045137,
        "title": gls("Чокнутый")
    }
]


# sh_levels = [80, 300, 720, 1400, 2400, 3780, 5600, 7920, 10800, 14300, 18480, 23400, 29120, 35700, 40044, 45408, 52152, 60636, 71220, 84264, 100128, 119172,
#              141756, 168240, 198984, 234348, 274692, 320376, 371760, 403274, 436469, 471883, 510058, 551532, 596846, 646541, 701155, 761230, 827304, 899918,
#              979613, 1066927, 1162402, 1266576, 1330905, 1399713, 1474442, 1556531, 1647419, 1748548]
sh_levels = [int(0.25 * x ** 4 + 2 * x ** 3 + 10 * x ** 2 + 200 * x + 80) for x in range(125)]
clan_levels = [int(0.2 * x ** 3 + 3 * x ** 2 + 250 * x + 400) for x in range(200)]


def dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


events = {
    "nuts": [
        [dt(2020, 7, 18), dt(2020, 7, 20), 1.5]
    ],
    "xp": [
        [dt(2020, 7, 24, 12), dt(2020, 7, 27), 1.5]
    ]
}
seasons = {
    # 0: [dt(2020, 7, 1), dt(2020, 7, 17, 19, 27)],
    1: [dt(2020, 7, 17), dt(2020, 9, 1)],
    2: [dt(2020, 9, 1), dt(2020, 10, 1)],
    3: [dt(2020, 10, 1), dt(2020, 10, 30)],
    4: [dt(2020, 10, 30), dt(2020, 11, 30)],
    5: [dt(2020, 11, 30), dt(2020, 12, 25)],
    6: [dt(2020, 12, 25), dt(2021, 1, 27)],
    7: [dt(2021, 1, 27), dt(2021, 2, 23)],
    8: [dt(2021, 2, 23), dt(2021, 3, 17)],
    9: [dt(2021, 3, 17), dt(2021, 4, 18)],
    10: [dt(2021, 4, 18), dt(2021, 5, 19)],
    11: [dt(2021, 5, 19), dt(2021, 6, 16)],
    12: [dt(2021, 6, 16), dt(2021, 7, 13)],
    13: [dt(2021, 7, 13), dt(2021, 8, 21)],
    14: [dt(2021, 8, 21), dt(2021, 10, 1)],
    15: [dt(2021, 10, 1), dt(2021, 10, 30)],
    16: [dt(2021, 10, 30), dt(2021, 11, 30)],
    17: [dt(2021, 11, 30), dt(2021, 12, 25)],
    18: [dt(2021, 12, 25), dt(2022, 1, 27)],
    19: [dt(2022, 1, 27), dt(2022, 3, 1)],
    20: [dt(2022, 3, 1), dt(2022, 4, 2)],
    21: [dt(2022, 4, 2), dt(2022, 5, 1)],
    22: [dt(2022, 5, 1), dt(2022, 6, 1)],
    23: [dt(2022, 6, 1), dt(2022, 7, 1)],
    24: [dt(2022, 7, 1), dt(2022, 8, 1)]
}
