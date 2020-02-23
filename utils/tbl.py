tbl_locations = [
    {
        "name": "Leidarazdallar",
        "ru": "Летающие Острова",
        "en": "Floating Islands",
        "desc_en": "Somewhere behind old pines, huge mountains and fluffy clouds, bathing in the rays of sun are the "
                   "Soaring Heights, where newbies start their adventure.",
        "desc_ru": "Где-то за древними соснами, огромными горами и пушистыми облаками, в лучах солнца купаются "
                   "Парящие Вершины, где новички начинают свой путь.",
        "energy": 10,
        "araksan": [4, 7],
        "xp": [20, 40],
        "sh": 4,
        "points": [25, 60],
        "level": 0,
        "activity": [10, 30, 75, 150, 175, 60],  # Activity: 0:00 to 4:00 IST and so on
        "act": [40, 75],  # Avg. level completion time
        "dr": 0.07,  # Death/Failure rate
        "ll": 90,  # Level length
    },
    {
        "name": "Snegangairaat",
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
        "activity": [17, 41, 100, 200, 200, 80],  # Activity: 0:00 to 4:00 IST and so on
        "act": [60, 90],  # Avg. level completion time
        "dr": 0.15,  # Death rate
        "ll": 105,
    },
    {
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
        "activity": [25, 50, 115, 220, 220, 100],  # Activity: 0:00 to 4:00 IST and so on
        "act": [80, 110],  # Avg. level completion time
        "dr": 0.17,  # Death rate
        "ll": 120,
    },
    {
        "name": "Havazdallarigar",
        "ru": "Хвостоград",
        "en": "Tail Town",
        "desc_en": "Not yet available",
        "desc_ru": "Недоступно",
        "energy": 10,
        "araksan": [9, 11],
        "xp": [50, 75],
        "sh": 9,
        "points": [75, 100],
        "level": 17,
        "activity": [30, 80, 150, 300, 300, 130],  # Activity: 0:00 to 4:00 IST and so on
        "act": [90, 135],  # Avg. level completion time
        "dr": 0.17,  # Death rate
        "ll": 150,
    },
    {
        "name": "Sunadallarat",
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
        "activity": [27, 80, 125, 270, 240, 110],  # Activity: 0:00 to 4:00 IST and so on
        "act": [90, 145],  # Avg. level completion time
        "dr": 0.2,  # Death rate
        "ll": 180,
    },
    {
        "name": "Seinemaire",
        "ru": "Синее Море",
        "en": "The Blue Sea",
        "desc_en": "A lot of water, fish, seaweed and hard obstacles. The major part of the Blue Sea had dried up and "
                   "turned into the Desert, and in the remainder the squirrels don't have any time to rest.",
        "desc_ru": "Много-много воды, рыбки, водоросли и сложные препятствия. Большая часть Синего Моря иссохла и "
                   "превратилась в Пустыню, а в остатках белкам не до отдыха.",
        "energy": 10,
        "araksan": [14, 17],
        "xp": [70, 100],
        "sh": 13,
        "points": [150, 225],
        "level": 22,
        "activity": [7, 21, 54, 127, 157, 75],  # Activity: 0:00 to 4:00 IST and so on
        "act": [120, 190],  # Avg. level completion time
        "dr": 0.22,  # Death rate
        "ll": 210,
    },
    {
        "name": "Na Veilarinne Belkaden Peaskat",
        "ru": "Великая Беличья Пустыня",
        "en": "The Great Squirrels' Desert",
        "desc_en": "The sandy desert formed in the place of the dried up Blue Sea. Only the bravest squirrels "
                   "depart here for a long adventure in search of treasure.",
        "desc_ru": "Песчаная пустыня раскинулась на месте пересохшего Синего Моря. Только самые смелые белки "
                   "отправляются сюда в долгое путешествие на поиски сокровищ.",
        "energy": 11,
        "araksan": [17, 20],
        "xp": [85, 150],
        "sh": 17,
        "points": [225, 375],
        "level": 25,
        "activity": [7, 41, 91, 175, 192, 70],  # Activity: 0:00 to 4:00 IST and so on
        "act": [180, 210],  # Avg. level completion time
        "dr": 0.27,  # Death rate
        "ll": 240,
    },
    {
        "name": "Degazemlat",
        "ru": "Дикие Земли",
        "en": "The Wild Lands",
        "desc_en": "The mystery of the wild lands remained unsolved for a long while. Then the monster disappeared "
                   "without a trace, and the brave ones were able to enter into the dark bowels of the red lands.",
        "desc_ru": "Тайна диких земель долго оставалась не раскрытой. Чудовище бесследно исчезло, а храбрецы смогли "
                   "войти в темные недра красных земель.",
        "energy": 12,
        "araksan": [20, 25],
        "xp": [100, 175],
        "sh": 20,
        "points": [300, 500],
        "level": 28,
        "activity": [4, 15, 41, 92, 102, 50],  # Activity: 0:00 to 4:00 IST and so on
        "act": [200, 250],  # Avg. level completion time
        "dr": 0.28,  # Death rate
        "ll": 270,
    },
    {
        "name": "Stormaranvannat",
        "ru": "Равнины Штормов",
        "en": "The Plains of Storms",
        "desc_en": "Right in the center of the planet a storm started to rage. Dangers that would chill your soul "
                   "await those who dare enter here.",
        "desc_ru": "В самом центре планеты разбушевался шторм. Леденящие душу опасности ожидают тех, "
                   "кто осмелился сюда зайти.",
        "energy": 13,
        "araksan": [25, 30],
        "xp": [125, 190],
        "sh": 24,
        "points": [450, 750],
        "level": 32,
        "activity": [17, 42, 91, 172, 148, 59],  # Activity: 0:00 to 4:00 IST and so on
        "act": [225, 275],  # Avg. level completion time
        "dr": 0.3,  # Death rate
        "ll": 300,
    },
    {
        "name": "Espennarversenat",
        "ru": "Вершины Испытаний",
        "en": "The Challenge Heights",
        "desc_en": "Squads of the most brave and skilled squirrels head to the Challenge Heights to show what "
                   "they're capable of.",
        "desc_ru": "Отряды самых смелых и умелых белок направляются в Испытания, чтобы показать, на что они способны.",
        "energy": 15,
        "araksan": [27, 35],
        "xp": [150, 210],
        "sh": 27,
        "points": [600, 900],
        "level": 37,
        "activity": [25, 75, 149, 343, 371, 107],  # Activity: 0:00 to 4:00 IST and so on
        "act": [275, 330],  # Avg. level completion time
        "dr": 0.37,  # Death rate
        "ll": 350,
    },
    {
        "name": "Sanzanbaira",
        "ru": "Сосновый Бор",
        "en": "The Pine Forest",
        "desc_en": "In the forest it's good to lose yourself behind the trunks of trees, hop on branches and "
                   "throw cones at each other.",
        "desc_ru": "В лесу хорошо потеряться за стволами, скакать по веткам и швырять друг в друга шишками.",
        "energy": 17,
        "araksan": [32, 40],
        "xp": [200, 300],
        "sh": 32,
        "points": [800, 1200],
        "level": 42,
        "activity": [11, 37, 100, 197, 211, 71],  # Activity: 0:00 to 4:00 IST and so on
        "act": [300, 375],  # Avg. level completion time
        "dr": 0.33,  # Death rate
        "ll": 420,
    },
    {
        "name": "Anamallzonaa",
        "ru": "Аномальная Зона",
        "en": "Anomalous Zone",
        "desc_en": "By the will of evil fate, a meteorite fell right onto the Ship of Salvation. The anomalous zone "
                   "formed in the place of the ship.",
        "desc_ru": "Волей злодейки-судьбы метеорит упал прямо на Корабль Спасения. На месте корабля "
                   "образовалась Аномальная Зона.",
        "energy": 20,
        "araksan": [40, 50],
        "xp": [250, 375],
        "sh": 40,
        "points": [1000, 1500],
        "level": 50,
        "activity": [47, 185, 284, 527, 571, 317],  # Activity: 0:00 to 4:00 IST and so on
        "act": [240, 475],  # Avg. level completion time
        "dr": 0.4,  # Death rate
        "ll": 480,
    },
    {
        "name": "Peirasta",
        "ru": "Пещера",
        "en": "The Cave",
        "desc_en": "It's dark and scary here, but it doesn't bother some at all.",
        "desc_ru": "Здесь темно и страшно, но некоторых это ни капли не останавливает.",
        "energy": 20,
        "araksan": [50, 70],
        "xp": [300, 450],
        "sh": 50,
        "points": [1250, 2000],
        "level": 60,
        "activity": [16, 42, 81, 141, 121, 47],  # Activity: 0:00 to 4:00 IST and so on
        "act": [475, 515],  # Avg. level completion time
        "dr": 0.43,  # Death rate
        "ll": 570,
    },
    {
        "name": "Saivakairella",
        "ru": "Корабль Спасения",
        "en": "The Ship of Salvation",
        "desc_en": "Scientists didn't give up and built the second Ship of Salvation to escape the planet. "
                   "This is the only hope for salvation.",
        "desc_ru": "Ученые не сдались, и построили второй Корабль Спасения, чтобы сбежать с планеты. "
                   "Это единственная надежда на спасение.",
        "energy": 25,
        "araksan": [75, 90],
        "xp": [450, 750],
        "sh": 70,
        "points": [1500, 2250],
        "level": 70,
        "activity": [75, 355, 750, 1215, 1073, 471],  # Activity: 0:00 to 4:00 IST and so on
        "act": [400, 600],  # Avg. level completion time
        "dr": 0.27,  # Death rate
        "ll": 660,
    },
    {
        "name": "<Redacted>",
        "ru": "<Засекречено>",
        "en": "<Redacted>",
        "desc_en": "Nobody knows what's going on here.",
        "desc_ru": "Никто не знает, что здесь происходит.",
        "energy": 25,
        "araksan": [100, 100],
        "xp": [700, 1000],
        "sh": 100,
        "points": [2000, 2000],
        "level": 201,
        "activity": [1, 7, 22, 121, 97, 29],  # Activity: 0:00 to 4:00 IST and so on
        "act": [500, 750],  # Avg. level completion time
        "dr": 0.07,  # Death rate
        "ll": 750,
    },
]


def gls(val: str):
    lang = "en"
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


tbl_leagues = [
    {
        "name": "Нет",
        "en": "None",
        "min_scores": 0
    }, {
        "name": "Бронза",
        "en": "Bronze",
        "min_scores": 500
    }, {
        "name": "Серебро",
        "en": "Silver",
        "min_scores": 2500
    }, {
        "name": "Золото",
        "en": "Gold",
        "min_scores": 6000
    }, {
        "name": "Мастер",
        "en": "Master",
        "min_scores": 10000
    }, {
        "name": "Алмаз",
        "en": "Diamond",
        "min_scores": 50000
    }, {
        "name": "Чемпион",
        "en": "Champion",
        "min_scores": 100000
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


tbl_player = {
    "level": 1,
    "xp": 0,
    "araksan": 150,
    "coins": 5,
    "sh_level": 1,
    "sh_xp": 0,
    "mana": 0,
    "dr_day": 0,  # Daily Reward Day
    "dr_ll": 0,   # Daily Reward Last Login
    "energy": 0,
    "time": 0,
    "potion_energy": 0,
    "potion_mana": 0,
    "secret_mode": 0,
    "league": 0,
    "used": 0,
    "sh": 0,
}
tbl_clan = {
    "level": 1,
    "xp": 0,
    "temples": [0, 0, 0],
    "expiry": [0, 0, 0],
    "skill_points": 0,
    "araksan": 0,
    "coins": 0,
    "temple_levels": [],
    "bcd": 0,  # Black Shaman (Reincarnation) сooldown
}
