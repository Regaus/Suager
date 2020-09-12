from datetime import datetime, timezone

locations = [
    {
        "id": 1,
        "name": "Dan Leitennan Azdalat",
        "en": "tbl_location01",
        "desc_en": "tbl_description01",
        "energy": 10,
        "araksan": [4, 7],
        "xp": [20, 40],
        "sh": 4,
        "points": [25, 60],
        "level": 0,
        "activity": [1721, 2744, 5072, 5742, 5231, 3101, 1402, 907],  # Activity - 0 to 4 KST, etc. -- Goes up to 32 "hours" -- Midnight == morning
        "act": 30,   # Min. pass time
        "dr": 0.07,  # Death/Failure rate
        "ll": 90     # Level length
    },
    {
        "id": 2,
        "name": "Dan Haltavaidaan Kirtinnat",
        "en": "tbl_location02",
        "desc_en": "tbl_description02",
        "energy": 10,
        "araksan": [5, 7],
        "xp": [27, 50],
        "sh": 6,
        "points": [35, 70],
        "level": 7,
        "activity": [1278, 2231, 4712, 5232, 4729, 4121, 2109, 702],  # Activity: 0:00 to 4:00 IST and so on
        "act": 45,  # Avg. level completion time
        "dr": 0.15,  # Death rate
        "ll": 105
    },
    {
        "id": 3,
        "name": "Dar Taivead",
        "en": "tbl_location03",
        "desc_en": "tbl_description03",
        "energy": 10,
        "araksan": [7, 9],
        "xp": [40, 60],
        "sh": 7,
        "points": [50, 100],
        "level": 12,
        "activity": [2037, 3662, 4039, 4794, 6078, 4282, 2103, 1002],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 50,  # Avg. level completion time
        "dr": 0.17,  # Death rate
        "ll": 120
    },
    {
        "id": 4,
        "name": "Havastangar",
        "en": "tbl_location04",
        "desc_en": "tbl_description04",
        "energy": 10,
        "araksan": [9, 11],
        "xp": [50, 75],
        "sh": 9,
        "points": [75, 100],
        "level": 20,
        "activity": [2742, 4932, 7932, 9251, 9742, 5821, 2174, 1210],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 60,  # Avg. level completion time
        "dr": 0.17,  # Death rate
        "ll": 130
    },
    {
        "id": 5,
        "name": "Dan Sennan Dailannat",
        "en": "tbl_location05",
        "desc_en": "tbl_description05",
        "energy": 10,
        "araksan": [11, 14],
        "xp": [60, 85],
        "sh": 11,
        "points": [100, 150],
        "level": 30,
        "activity": [2013, 3719, 6744, 7421, 5321, 3712, 1937, 871],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 65,  # Avg. level completion time
        "dr": 0.2,  # Death rate
        "ll": 140
    },
    {
        "id": 6,
        "name": "Da Seina Vandaa",
        "en": "tbl_location06",
        "desc_en": "tbl_description06",
        "energy": 10,
        "araksan": [14, 17],
        "xp": [70, 100],
        "sh": 13,
        "points": [150, 225],
        "level": 40,
        "activity": [1372, 2371, 3281, 3471, 2973, 2019, 938, 173],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 75,  # Avg. level completion time
        "dr": 0.22,  # Death rate
        "ll": 150
    },
    {
        "id": 7,
        "name": "Dan Veilaran Bylkadan Peaskat",
        "en": "tbl_location07",
        "desc_en": "tbl_description07",
        "energy": 10,
        "araksan": [17, 20],
        "xp": [85, 150],
        "sh": 17,
        "points": [225, 375],
        "level": 50,
        "activity": [2479, 4789, 4482, 4672, 4272, 4102, 3121, 2377],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 90,  # Avg. level completion time
        "dr": 0.27,  # Death rate
        "ll": 160
    },
    {
        "id": 8,
        "name": "Das Naitenne Heiste",
        "en": "tbl_location08",
        "desc_en": "tbl_description08",
        "energy": 10,
        "araksan": [20, 25],
        "xp": [100, 175],
        "sh": 20,
        "points": [300, 500],
        "level": 60,
        "activity": [138, 526, 1411, 2011, 1824, 794, 103, 27],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 100,  # Avg. level completion time
        "dr": 0.28,  # Death rate
        "ll": 170
    },
    {
        "id": 9,
        "name": "Dan Pulkannat Diaran Vaitekan",
        "en": "tbl_location09",
        "desc_en": "tbl_description09",
        "energy": 10,
        "araksan": [25, 30],
        "xp": [125, 190],
        "sh": 24,
        "points": [450, 750],
        "level": 70,
        "activity": [1021, 1741, 3272, 3673, 3109, 1315, 972, 748],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 110,  # Avg. level completion time
        "dr": 0.3,  # Death rate
        "ll": 180
    },
    {
        "id": 10,
        "name": "Dan Koirannat Kiiteivalladan",
        "en": "tbl_location10",
        "desc_en": "tbl_description10",
        "energy": 10,
        "araksan": [27, 35],
        "xp": [150, 210],
        "sh": 27,
        "points": [600, 900],
        "level": 80,
        "activity": [2174, 4572, 6022, 7042, 7213, 6123, 4271, 2019],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 125,  # Avg. level completion time
        "dr": 0.32,  # Death rate
        "ll": 190
    },
    {
        "id": 11,
        "name": "Dar Lias",
        "en": "tbl_location11",
        "desc_en": "tbl_description11",
        "energy": 10,
        "araksan": [32, 40],
        "xp": [200, 300],
        "sh": 32,
        "points": [800, 1200],
        "level": 90,
        "activity": [1738, 2841, 4821, 5689, 5372, 3121, 1821, 1221],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 95,  # Avg. level completion time
        "dr": 0.33,  # Death rate
        "ll": 200
    },
    {
        "id": 12,
        "name": "Das Heiste Anomaliadan",
        "en": "tbl_location12",
        "desc_en": "tbl_description12",
        "energy": 10,
        "araksan": [40, 50],
        "xp": [250, 375],
        "sh": 40,
        "points": [1000, 1500],
        "level": 110,
        "activity": [947, 2102, 4219, 4627, 4228, 3728, 2149, 641],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 110,  # Avg. level completion time
        "dr": 0.4,  # Death rate
        "ll": 210
    },
    {
        "id": 13,
        "name": "Das Teimanheiste",
        "en": "tbl_location13",
        "desc_en": "tbl_description13",
        "energy": 10,
        "araksan": [50, 70],
        "xp": [300, 450],
        "sh": 50,
        "points": [1250, 2000],
        "level": 125,
        "activity": [2714, 3052, 3265, 3752, 3252, 2912, 2711, 2411],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 100,  # Avg. level completion time
        "dr": 0.43,  # Death rate
        "ll": 220
    },
    {
        "id": 14,
        "name": "Da Garraikirtinna Temantan",
        "en": "tbl_location14",
        "desc_en": "tbl_description14",
        "energy": 10,
        "araksan": [60, 80],
        "xp": [400, 600],
        "sh": 60,
        "points": [1500, 2250],
        "level": 140,
        "activity": [1411, 2245, 3721, 4342, 4722, 4102, 2849, 1092],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 105,  # Avg. level completion time
        "dr": 0.44,  # Death rate
        "ll": 230
    },
    {
        "id": 15,
        "name": "Da Neireideda Laitaa",
        "en": "tbl_location15",
        "desc_en": "tbl_description15",
        "energy": 10,
        "araksan": [70, 90],
        "xp": [500, 750],
        "sh": 70,
        "points": [1750, 2625],
        "level": 160,
        "activity": [1402, 1958, 2741, 3091, 2711, 2238, 1794, 1381],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 120,  # Avg. level completion time
        "dr": 0.43,  # Death rate
        "ll": 240
    },
    {
        "id": 16,
        "name": "Da Seinankara Teivavaidaa",
        "en": "tbl_location16",
        "desc_en": "tbl_description16",
        "energy": 10,
        "araksan": [85, 105],
        "xp": [600, 900],
        "sh": 85,
        "points": [2000, 3000],
        "level": 180,
        "activity": [1074, 1731, 2152, 2751, 3178, 2148, 1271, 792],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 115,  # Avg. level completion time
        "dr": 0.47,  # Death rate
        "ll": 250
    },
    {
        "id": 17,
        "name": "Da Devida Laitaa Deaktanvan",
        "en": "tbl_location17",
        "desc_en": "tbl_description17",
        "energy": 10,
        "araksan": [100, 150],
        "xp": [750, 1000],
        "sh": 100,
        "points": [2500, 3750],
        "level": 190,
        "activity": [5092, 5732, 6372, 7221, 7521, 6271, 5741, 4872],  # 6am, 9am, noon, 3pm, 6pm, 9pm, midnight, 3am
        "act": 120,  # Minimal completion time
        "dr": 0.27,  # Death rate
        "ll": 270
    },
    {
        "id": 18,
        "name": "Da Neiva",
        "en": "tbl_location18",
        "desc_en": "tbl_description18",
        "energy": 10,
        "araksan": [150, 300],
        "xp": [1500, 4500],
        "sh": 225,
        "points": [5000, 12500],
        "level": 200,
        "activity": [7204, 8019, 9011, 10115, 11047, 9892, 8701, 6982],
        "act": 150,
        "dr": 0.19,
        "ll": 280
    }
]


totems = [
    {"name": "tbl_totem1", "desc": "tbl_totem_desc1"},  # 1.08 + 0.02 * level
    {"name": "tbl_totem2", "desc": "tbl_totem_desc2"},  # 1.06 + 0.04 * level
    {"name": "tbl_totem3", "desc": "tbl_totem_desc3"},  # 1.075 + 0.025 * level
    {"name": "tbl_totem4", "desc": "tbl_totem_desc4"},
    {"name": "tbl_totem5", "desc": "tbl_totem_desc5"}
]


leagues = [
    {"name": "generic_none", "score": 0},
    {"name": "tbl_league1", "score": 500},
    {"name": "tbl_league2", "score": 1250},
    {"name": "tbl_league3", "score": 2000},
    {"name": "tbl_league4", "score": 3000},
    {"name": "tbl_league5", "score": 4000},
    {"name": "tbl_league6", "score": 5000},
    {"name": "tbl_league7", "score": 6000},
    {"name": "tbl_league8", "score": 7000},
    {"name": "tbl_league9", "score": 8500},
    {"name": "tbl_league10", "score": 10000},
    {"name": "tbl_league11", "score": 20000},
    {"name": "tbl_league12", "score": 30000},
    {"name": "tbl_league13", "score": 40000},
    {"name": "tbl_league14", "score": 50000},
    {"name": "tbl_league15", "score": 60000},
    {"name": "tbl_league16", "score": 70000},
    {"name": "tbl_league17", "score": 80000},
    {"name": "tbl_league18", "score": 90000},
    {"name": "tbl_league19", "score": 100000},
    {"name": "tbl_league20", "score": 250000},
    {"name": "tbl_league21", "score": 500000},
    {"name": "tbl_league22", "score": 1000000},
    {"name": "tbl_league23", "score": 5000000},
    {"name": "tbl_league24", "score": 25000000}
]


xp_levels = [
    {"experience": 0, "title": "tbl_rank01"},           # 001
    {"experience": 50, "title": "tbl_rank01"},          # 002
    {"experience": 110, "title": "tbl_rank01"},         # 003
    {"experience": 200, "title": "tbl_rank02"},         # 004
    {"experience": 300, "title": "tbl_rank02"},         # 005
    {"experience": 425, "title": "tbl_rank02"},         # 006
    {"experience": 590, "title": "tbl_rank03"},         # 007
    {"experience": 1090, "title": "tbl_rank03"},        # 008
    {"experience": 2565, "title": "tbl_rank03"},        # 009
    {"experience": 5015, "title": "tbl_rank04"},        # 010
    {"experience": 8640, "title": "tbl_rank04"},        # 011
    {"experience": 13340, "title": "tbl_rank04"},       # 012
    {"experience": 19115, "title": "tbl_rank05"},       # 013
    {"experience": 25965, "title": "tbl_rank05"},       # 014
    {"experience": 33890, "title": "tbl_rank05"},       # 015
    {"experience": 42890, "title": "tbl_rank06"},       # 016
    {"experience": 50640, "title": "tbl_rank06"},       # 017
    {"experience": 57230, "title": "tbl_rank06"},       # 018
    {"experience": 62840, "title": "tbl_rank07"},       # 019
    {"experience": 67610, "title": "tbl_rank07"},       # 020
    {"experience": 71670, "title": "tbl_rank07"},       # 021
    {"experience": 75125, "title": "tbl_rank08"},       # 022
    {"experience": 78065, "title": "tbl_rank08"},       # 023
    {"experience": 80565, "title": "tbl_rank08"},       # 024
    {"experience": 83065, "title": "tbl_rank09"},       # 025
    {"experience": 86055, "title": "tbl_rank09"},       # 026
    {"experience": 89635, "title": "tbl_rank09"},       # 027
    {"experience": 93915, "title": "tbl_rank10"},       # 028
    {"experience": 99035, "title": "tbl_rank10"},       # 029
    {"experience": 105165, "title": "tbl_rank10"},      # 030
    {"experience": 112500, "title": "tbl_rank11"},      # 031
    {"experience": 121275, "title": "tbl_rank11"},      # 032
    {"experience": 131775, "title": "tbl_rank11"},      # 033
    {"experience": 139515, "title": "tbl_rank12"},      # 034
    {"experience": 147580, "title": "tbl_rank12"},      # 035
    {"experience": 155985, "title": "tbl_rank12"},      # 036
    {"experience": 164740, "title": "tbl_rank13"},      # 037
    {"experience": 173860, "title": "tbl_rank13"},      # 038
    {"experience": 183360, "title": "tbl_rank13"},      # 039
    {"experience": 193260, "title": "tbl_rank14"},      # 040
    {"experience": 203575, "title": "tbl_rank14"},      # 041
    {"experience": 214325, "title": "tbl_rank14"},      # 042
    {"experience": 225525, "title": "tbl_rank15"},      # 043
    {"experience": 237195, "title": "tbl_rank15"},      # 044
    {"experience": 249350, "title": "tbl_rank15"},      # 045
    {"experience": 262015, "title": "tbl_rank16"},      # 046
    {"experience": 275210, "title": "tbl_rank16"},      # 047
    {"experience": 288955, "title": "tbl_rank16"},      # 048
    {"experience": 303275, "title": "tbl_rank17"},      # 049
    {"experience": 318195, "title": "tbl_rank17"},      # 050
    {"experience": 333740, "title": "tbl_rank17"},      # 051
    {"experience": 349935, "title": "tbl_rank18"},      # 052
    {"experience": 366805, "title": "tbl_rank18"},      # 053
    {"experience": 384385, "title": "tbl_rank18"},      # 054
    {"experience": 402700, "title": "tbl_rank19"},      # 055
    {"experience": 421780, "title": "tbl_rank19"},      # 056
    {"experience": 441660, "title": "tbl_rank19"},      # 057
    {"experience": 462370, "title": "tbl_rank20"},      # 058
    {"experience": 483950, "title": "tbl_rank20"},      # 059
    {"experience": 506430, "title": "tbl_rank20"},      # 060
    {"experience": 529850, "title": "tbl_rank21"},      # 061
    {"experience": 554250, "title": "tbl_rank21"},      # 062
    {"experience": 579670, "title": "tbl_rank21"},      # 063
    {"experience": 606160, "title": "tbl_rank22"},      # 064
    {"experience": 633755, "title": "tbl_rank22"},      # 065
    {"experience": 662505, "title": "tbl_rank22"},      # 066
    {"experience": 691255, "title": "tbl_rank23"},      # 067
    {"experience": 719795, "title": "tbl_rank23"},      # 068
    {"experience": 748130, "title": "tbl_rank23"},      # 069
    {"experience": 776260, "title": "tbl_rank24"},      # 070
    {"experience": 804185, "title": "tbl_rank24"},      # 071
    {"experience": 831905, "title": "tbl_rank24"},      # 072
    {"experience": 859425, "title": "tbl_rank25"},      # 073
    {"experience": 886745, "title": "tbl_rank25"},      # 074
    {"experience": 913865, "title": "tbl_rank25"},      # 075
    {"experience": 940790, "title": "tbl_rank26"},      # 076
    {"experience": 967520, "title": "tbl_rank26"},      # 077
    {"experience": 994055, "title": "tbl_rank26"},      # 078
    {"experience": 1020395, "title": "tbl_rank27"},     # 079
    {"experience": 1046545, "title": "tbl_rank27"},     # 080
    {"experience": 1072745, "title": "tbl_rank27"},     # 081
    {"experience": 1099120, "title": "tbl_rank28"},     # 082
    {"experience": 1125670, "title": "tbl_rank28"},     # 083
    {"experience": 1152400, "title": "tbl_rank28"},     # 084
    {"experience": 1179310, "title": "tbl_rank29"},     # 085
    {"experience": 1206400, "title": "tbl_rank29"},     # 086
    {"experience": 1233670, "title": "tbl_rank29"},     # 087
    {"experience": 1261125, "title": "tbl_rank30"},     # 088
    {"experience": 1288765, "title": "tbl_rank30"},     # 089
    {"experience": 1316590, "title": "tbl_rank30"},     # 090
    {"experience": 1344600, "title": "tbl_rank31"},     # 091
    {"experience": 1372800, "title": "tbl_rank31"},     # 092
    {"experience": 1401190, "title": "tbl_rank31"},     # 093
    {"experience": 1429770, "title": "tbl_rank32"},     # 094
    {"experience": 1458540, "title": "tbl_rank32"},     # 095
    {"experience": 1487500, "title": "tbl_rank32"},     # 096
    {"experience": 1516660, "title": "tbl_rank33"},     # 097
    {"experience": 1546010, "title": "tbl_rank33"},     # 098
    {"experience": 1575560, "title": "tbl_rank33"},     # 099
    {"experience": 1605310, "title": "tbl_rank34"},     # 100
    {"experience": 1635260, "title": "tbl_rank34"},     # 101
    {"experience": 1665410, "title": "tbl_rank34"},     # 102
    {"experience": 1695760, "title": "tbl_rank35"},     # 103
    {"experience": 1726310, "title": "tbl_rank35"},     # 104
    {"experience": 1757070, "title": "tbl_rank35"},     # 105
    {"experience": 1788035, "title": "tbl_rank36"},     # 106
    {"experience": 1819205, "title": "tbl_rank36"},     # 107
    {"experience": 1850585, "title": "tbl_rank36"},     # 108
    {"experience": 1882175, "title": "tbl_rank37"},     # 109
    {"experience": 1913975, "title": "tbl_rank37"},     # 110
    {"experience": 1945990, "title": "tbl_rank37"},     # 111
    {"experience": 1978220, "title": "tbl_rank38"},     # 112
    {"experience": 2010665, "title": "tbl_rank38"},     # 113
    {"experience": 2043330, "title": "tbl_rank38"},     # 114
    {"experience": 2076215, "title": "tbl_rank39"},     # 115
    {"experience": 2109320, "title": "tbl_rank39"},     # 116
    {"experience": 2142645, "title": "tbl_rank39"},     # 117
    {"experience": 2176195, "title": "tbl_rank40"},     # 118
    {"experience": 2209970, "title": "tbl_rank40"},     # 119
    {"experience": 2243970, "title": "tbl_rank40"},     # 120
    {"experience": 2278370, "title": "tbl_rank41"},     # 121
    {"experience": 2314270, "title": "tbl_rank41"},     # 122
    {"experience": 2351735, "title": "tbl_rank41"},     # 123
    {"experience": 2390830, "title": "tbl_rank42"},     # 124
    {"experience": 2431630, "title": "tbl_rank42"},     # 125
    {"experience": 2474210, "title": "tbl_rank42"},     # 126
    {"experience": 2518645, "title": "tbl_rank43"},     # 127
    {"experience": 2565015, "title": "tbl_rank43"},     # 128
    {"experience": 2613405, "title": "tbl_rank43"},     # 129
    {"experience": 2663905, "title": "tbl_rank44"},     # 130
    {"experience": 2716605, "title": "tbl_rank44"},     # 131
    {"experience": 2771605, "title": "tbl_rank44"},     # 132
    {"experience": 2828995, "title": "tbl_rank45"},     # 133
    {"experience": 2888890, "title": "tbl_rank45"},     # 134
    {"experience": 2951395, "title": "tbl_rank45"},     # 135
    {"experience": 3016625, "title": "tbl_rank46"},     # 136
    {"experience": 3084695, "title": "tbl_rank46"},     # 137
    {"experience": 3155735, "title": "tbl_rank46"},     # 138
    {"experience": 3229865, "title": "tbl_rank47"},     # 139
    {"experience": 3307225, "title": "tbl_rank47"},     # 140
    {"experience": 3387960, "title": "tbl_rank47"},     # 141
    {"experience": 3472210, "title": "tbl_rank48"},     # 142
    {"experience": 3560130, "title": "tbl_rank48"},     # 143
    {"experience": 3651885, "title": "tbl_rank48"},     # 144
    {"experience": 3747635, "title": "tbl_rank49"},     # 145
    {"experience": 3847560, "title": "tbl_rank49"},     # 146
    {"experience": 3951840, "title": "tbl_rank49"},     # 147
    {"experience": 4060665, "title": "tbl_rank50"},     # 148
    {"experience": 4174230, "title": "tbl_rank50"},     # 149
    {"experience": 4292745, "title": "tbl_rank50"},     # 150
    {"experience": 4416425, "title": "tbl_rank51"},     # 151
    {"experience": 4545495, "title": "tbl_rank51"},     # 152
    {"experience": 4680190, "title": "tbl_rank51"},     # 153
    {"experience": 4820755, "title": "tbl_rank52"},     # 154
    {"experience": 4967445, "title": "tbl_rank52"},     # 155
    {"experience": 5120525, "title": "tbl_rank52"},     # 156
    {"experience": 5280275, "title": "tbl_rank53"},     # 157
    {"experience": 5446985, "title": "tbl_rank53"},     # 158
    {"experience": 5620960, "title": "tbl_rank53"},     # 159
    {"experience": 5799935, "title": "tbl_rank54"},     # 160
    {"experience": 5989405, "title": "tbl_rank54"},     # 161
    {"experience": 6187135, "title": "tbl_rank54"},     # 162
    {"experience": 6393480, "title": "tbl_rank55"},     # 163
    {"experience": 6608815, "title": "tbl_rank55"},     # 164
    {"experience": 6833535, "title": "tbl_rank55"},     # 165
    {"experience": 7068045, "title": "tbl_rank56"},     # 166
    {"experience": 7312775, "title": "tbl_rank56"},     # 167
    {"experience": 7568175, "title": "tbl_rank56"},     # 168
    {"experience": 7834700, "title": "tbl_rank57"},     # 169
    {"experience": 8112840, "title": "tbl_rank57"},     # 170
    {"experience": 8403100, "title": "tbl_rank57"},     # 171
    {"experience": 8706010, "title": "tbl_rank58"},     # 172
    {"experience": 9022120, "title": "tbl_rank58"},     # 173
    {"experience": 9352005, "title": "tbl_rank58"},     # 174
    {"experience": 9696265, "title": "tbl_rank59"},     # 175
    {"experience": 10055525, "title": "tbl_rank59"},    # 176
    {"experience": 10430440, "title": "tbl_rank59"},    # 177
    {"experience": 10733350, "title": "tbl_rank60"},    # 178
    {"experience": 11084726, "title": "tbl_rank60"},    # 179
    {"experience": 11492322, "title": "tbl_rank60"},    # 180
    {"experience": 11965133, "title": "tbl_rank59"},    # 181
    {"experience": 12513594, "title": "tbl_rank59"},    # 182
    {"experience": 13149808, "title": "tbl_rank59"},    # 183
    {"experience": 13887817, "title": "tbl_rank61"},    # 184
    {"experience": 14743907, "title": "tbl_rank61"},    # 185
    {"experience": 15736972, "title": "tbl_rank61"},    # 186
    {"experience": 16888927, "title": "tbl_rank62"},    # 187
    {"experience": 18225195, "title": "tbl_rank62"},    # 188
    {"experience": 19775266, "title": "tbl_rank62"},    # 189
    {"experience": 21573348, "title": "tbl_rank63"},    # 190
    {"experience": 23659123, "title": "tbl_rank63"},    # 191
    {"experience": 26078622, "title": "tbl_rank63"},    # 192
    {"experience": 28885241, "title": "tbl_rank64"},    # 193
    {"experience": 32140919, "title": "tbl_rank64"},    # 194
    {"experience": 35917505, "title": "tbl_rank64"},    # 195
    {"experience": 40298345, "title": "tbl_rank65"},    # 196
    {"experience": 45380120, "title": "tbl_rank65"},    # 197
    {"experience": 51274979, "title": "tbl_rank65"},    # 198
    {"experience": 58113015, "title": "tbl_rank66"},    # 199
    {"experience": 66045137, "title": "tbl_rank67"},    # 200
    {"experience": 100000000, "title": "tbl_rank68"},   # 201
    {"experience": 150000000, "title": "tbl_rank68"},   # 202
    {"experience": 200000000, "title": "tbl_rank68"},   # 203
    {"experience": 250000000, "title": "tbl_rank68"},   # 204
    {"experience": 300000000, "title": "tbl_rank68"},   # 205
    {"experience": 350000000, "title": "tbl_rank68"},   # 206
    {"experience": 400000000, "title": "tbl_rank68"},   # 207
    {"experience": 450000000, "title": "tbl_rank68"},   # 208
    {"experience": 500000000, "title": "tbl_rank68"},   # 209
    {"experience": 600000000, "title": "tbl_rank68"},   # 210
    {"experience": 650000000, "title": "tbl_rank68"},   # 211
    {"experience": 700000000, "title": "tbl_rank68"},   # 212
    {"experience": 800000000, "title": "tbl_rank68"},   # 213
    {"experience": 900000000, "title": "tbl_rank68"},   # 214
    {"experience": 1000000000, "title": "tbl_rank68"},  # 215
    {"experience": 1100000000, "title": "tbl_rank68"},  # 216
    {"experience": 1200000000, "title": "tbl_rank68"},  # 217
    {"experience": 1300000000, "title": "tbl_rank68"},  # 218
    {"experience": 1400000000, "title": "tbl_rank68"},  # 219
    {"experience": 1500000000, "title": "tbl_rank68"},  # 220
    {"experience": 1600000000, "title": "tbl_rank68"},  # 221
    {"experience": 1700000000, "title": "tbl_rank68"},  # 222
    {"experience": 1800000000, "title": "tbl_rank68"},  # 223
    {"experience": 1900000000, "title": "tbl_rank68"},  # 224
    {"experience": 2000000000, "title": "tbl_rank68"}   # 225
]


# sh_levels = [80, 300, 720, 1400, 2400, 3780, 5600, 7920, 10800, 14300, 18480, 23400, 29120, 35700, 40044, 45408, 52152, 60636, 71220, 84264, 100128, 119172,
#              141756, 168240, 198984, 234348, 274692, 320376, 371760, 403274, 436469, 471883, 510058, 551532, 596846, 646541, 701155, 761230, 827304, 899918,
#              979613, 1066927, 1162402, 1266576, 1330905, 1399713, 1474442, 1556531, 1647419, 1748548]
sh_levels = [int(0.25 * x ** 4 + 2 * x ** 3 + 10 * x ** 2 + 200 * x + 80) for x in range(1, 175)]
sh_levels += [250000000, 300000000, 350000000, 400000000, 500000000, 600000000, 700000000, 800000000, 900000000, 1000000000, 1250000000, 1500000000,
              1750000000, 2000000000, 2500000000, 3000000000, 4000000000, 5000000000, 7500000000, 10000000000, 12500000000, 15000000000, 20000000000,
              30000000000, 100000000000]
clan_levels = [int(0.2 * x ** 3 + 3 * x ** 2 + 250 * x + 400) for x in range(174)]


def dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


events = {
    "nuts": [
        [dt(2020, 7, 18), dt(2020, 7, 20, 12), 1.5],
        [dt(2020, 8, 1), dt(2020, 8, 3), 1.75],
        [dt(2020, 9, 1), dt(2020, 9, 5), 2],
        [dt(2020, 9, 19), dt(2020, 9, 21), 1.5],
        [dt(2020, 9, 26), dt(2020, 9, 28), 1.25],
        [dt(2020, 9, 30), dt(2020, 10, 2), 1.33],
        [dt(2020, 10, 24), dt(2020, 10, 26), 1.75],
        [dt(2020, 10, 29), dt(2020, 10, 31), 1.5],
        [dt(2020, 10, 31), dt(2020, 11, 1), 2.25],
        [dt(2020, 11, 1), dt(2020, 11, 2), 1.5],
        [dt(2020, 11, 14), dt(2020, 11, 16), 1.5],
        [dt(2020, 11, 28), dt(2020, 12, 2), 1.75],
        [dt(2020, 12, 5), dt(2020, 12, 7), 1.5],
        [dt(2020, 12, 19), dt(2020, 12, 21), 1.5],
        [dt(2020, 12, 24), dt(2020, 12, 27), 2.5],
        [dt(2020, 12, 31), dt(2021, 1, 8), 1.75],
        [dt(2021, 1, 16), dt(2021, 1, 18), 1.5],
        [dt(2021, 1, 27), dt(2021, 1, 28), 2.5],
        [dt(2021, 1, 30), dt(2021, 2, 1), 1.5]
    ],
    "xp": [
        [dt(2020, 7, 24, 12), dt(2020, 7, 27), 1.5],
        [dt(2020, 8, 15), dt(2020, 8, 17), 1.75],
        [dt(2020, 9, 1), dt(2020, 9, 5), 2],
        [dt(2020, 9, 12), dt(2020, 9, 14), 1.5],
        [dt(2020, 9, 30), dt(2020, 10, 2), 1.33],
        [dt(2020, 10, 2), dt(2020, 10, 5), 1.25],
        [dt(2020, 10, 10), dt(2020, 10, 12), 1.5],
        [dt(2020, 10, 17), dt(2020, 10, 19), 1.75],
        [dt(2020, 10, 29), dt(2020, 11, 1), 1.5],
        [dt(2020, 11, 7), dt(2020, 11, 9), 1.5],
        [dt(2020, 11, 21), dt(2020, 11, 23), 1.5],
        [dt(2020, 11, 29), dt(2020, 12, 2), 2],
        [dt(2020, 12, 12), dt(2020, 12, 14), 1.5],
        [dt(2020, 12, 24), dt(2020, 12, 26), 2.5],
        [dt(2020, 12, 26), dt(2020, 12, 27), 3.25],
        [dt(2020, 12, 27), dt(2020, 12, 28), 2.5],
        [dt(2020, 12, 31), dt(2021, 1, 8), 1.75],
        [dt(2021, 1, 23), dt(2021, 1, 25), 1.5],
        [dt(2021, 1, 27), dt(2021, 1, 28), 2.5]
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
