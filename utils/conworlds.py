import random
from math import atan2, cos, radians as rad, sin, sqrt
from os import listdir
from os.path import isfile, join

import discord
import jstyleson
from numpy.random import choice
from regaus import conworlds, time
from scipy.stats import skewnorm

from utils import languages
from utils.general import random_colour

# Taken out of the citizen_generator() function so that the distribution doesn't have to be recalculated every time
# Birthday time range corresponds to 20 Oct 1963 - 12 January 2023
# Not the most realistic, but it should work better for me - not everyone is ancient
birthday_min = time.datetime(2080, 1, 1, time_class=time.Kargadia)
birthday_max = time.datetime(2153, 1, 1, time_class=time.Kargadia)
timestamp_delta = birthday_max.timestamp - birthday_min.timestamp  # Difference between earliest and latest birthdate

birthday_random = skewnorm.rvs(a=-5, loc=0, size=2500)  # 5x right skew, meaning that generated values would lean to younger age
birthday_random -= min(birthday_random)  # Make the min value 0
birthday_random /= max(birthday_random)  # Make the max value 1

# Preload names in all the available languages, since those are never going to change
# This can also be used to exclude invalid languages
path = join("languages", "names")
available_languages = [f.removesuffix(".json") for f in listdir(path) if isfile(join(path, f))]
weights = [int(open(join(path, f) + ".json", encoding="utf-8").readline().rstrip().removeprefix("// Weight: ")) for f in available_languages]
all_available_names: dict[str, dict[str, list[str]]] = {lang: jstyleson.loads(open(join(path, lang) + ".json", encoding="utf-8").read()) for lang in available_languages}


def generate_citizen(language: str = None, name_only: bool = False) -> tuple[str, str] | dict[str, str | time.datetime]:
    """ Generate a Kargadian name in the given language (or random) """
    random.seed()  # For some reason, something was interfering with the randomness, but we can fix that by calling this
    if language is None:  # If the language is not specified, use a random language that has its naming system specified
        language = random.choices(available_languages, weights)[0]
    all_names: dict[str, list[str]] = all_available_names[language]
    gender = random.choice(("male", "female"))  # 50% male, 50% female
    names = all_names[gender] + all_names["neutral"]  # Pool of names to use as a first name
    # The first name in the list is used as a first name.
    # The second and third names are parent names for a son and a daughter respectively
    name1 = random.choice(names).split("/")[0]

    def parent_name(ignore_gender: bool = False):  # Generate a parent name
        parent = random.choices(("male", "female"), (85, 15), k=1)[0]  # Parent name: 85% father, 15% mother
        _names = all_names[parent] + all_names["neutral"]
        idx = 2 if gender == "female" and not ignore_gender else 1  # The -sen name will act as the "default" for edge cases
        return random.choice(_names).split("/")[idx]

    name2 = parent_name()

    # "Origin" surnames have 0% chance of coming up, so while they do exist, they are excluded from being used (previously was 10%)
    surname_type = random.choices(("profession", "origin", "parent", "random", "trait"), (20, 0, 15, 40, 15), k=1)[0]
    if surname_type == "profession":
        idx3 = 1 if gender == "female" else 0
        name3 = random.choice(all_names["profession"]).split("/")[idx3]

    elif surname_type == "trait":
        idx3 = 1 if gender == "female" else 0
        chosen = random.choice(all_names["traits"]).split("/")
        name3 = chosen[min(idx3, len(chosen) - 1)]

    elif surname_type == "origin":
        language_cls = languages.Language(language)
        # Get the language family of the target language (but exclude the base language and English)
        # This excludes the possibility of someone non-Kargadian having such a name and
        # assumes that you come from a place that spoke a language somewhat related to your own
        language_families = language_cls.fallbacks()[:-2]
        # Central RA Nehtivian (5 fallbacks) -> Inland Nehtivian, Lintinanazdall (1 fallback) -> Volcanic Islands Kargadian
        family_idx = min(max(2, len(language_families) - 2), len(language_families) - 1)
        family = language_families[family_idx]
        # The place's modern population has to be under 250,000: it wouldn't make as much sense if everyone was from the same places
        # We look for any small enough towns/cities where the primary spoken language is related enough to our target language
        available_places = [p for p in conworlds.places if p["population"] is not None and p["population"] < 250000 and languages.Language(p["language"][0]).is_in_family(family)]
        # place_weights = [p["population"] ** 0.75 for p in available_places]  # We don't need to favour smaller villages/towns as much here
        # origin = random.choices(available_places, place_weights, k=1)[0]
        origin = random.choice(available_places)
        origin_name = conworlds.Place(origin["id"]).name_translation(language_cls)
        while len(origin_name.split()) > 2:  # Prevent extremely long names from being used
            origin = random.choice(available_places)
            origin_name = conworlds.Place(origin["id"]).name_translation(language_cls)
        if language_cls.is_in_family("re"):
            name3 = "ad " + language_cls.case(origin_name, "genitive", "singular")
        elif language_cls.is_in_family("vv"):  # "re_kv", "re_mu"
            # These languages don't yet have a proper case declension, so it will just return the raw name
            name3 = language_cls.case(origin_name, "ablative", "singular")
        else:
            # If the language in question does not yet have specific instructions on what to do with the name,
            # just use the non-declined name of the place in the target language
            name3 = origin_name

    elif surname_type == "parent":
        name3 = parent_name(ignore_gender=True)

    else:
        direction = random.random() < 0.3
        if direction:
            chosen1: None = None
            part1 = random.choice(all_names["mix_directions"])
        else:
            chosen1: str = random.choice([n for n in all_names["mix_words"] if not n.startswith("-")])  # Some words can't start the second name
            part1 = chosen1.split("/")[0]
        chosen2 = random.choice([n for n in all_names["mix_words"] if not n.endswith("-") and n != chosen1])
        part2 = chosen2.split("/")[1]
        name3 = part1 + part2

    if name_only:
        return " ".join((name1, name2, name3)), gender

    # This is slightly unrealistic because it does not include the chance that people would live in a place
    # that does not speak their native language, but whatever.
    # With a 90% chance, the citizen will live in the same place as where they were born.
    available_places = [p for p in conworlds.places if p["population"] is not None and language in p["language"] and p.get("habitability", 2) >= 2]   # 2: Valid for residence and birth
    available_places2 = [p for p in conworlds.places if p["population"] is not None and language in p["language"] and p.get("habitability", 2) >= 1]  # 1: Valid for residence only
    # place_weights = [p["population"] ** 0.5 for p in available_places]  # The sqrt of the place's population size determines the likelihood it will be used as the birthplace
    # birth = residence = random.choices(available_places, place_weights, k=1)[0]  # By default, the place of residence is the same as the place of birth
    birth = residence = random.choice(available_places)
    moved = random.random() > 0.9
    if moved:
        # residence = random.choices(available_places, place_weights, k=1)[0]
        residence = random.choice(available_places2)

    # Get the citizen's birthday
    age = choice(birthday_random)
    timestamp = birthday_min.timestamp + age * timestamp_delta  # Timestamp of the birthday
    birthday_tz = conworlds.Place(birth["id"]).tz
    birthday = time.datetime.from_timestamp(timestamp, tz=birthday_tz, time_class=time.Kargadia)  # The actual birthday

    # For the native language, the language code is provided.
    # For the birthday, a datetime of the birthdate is provided.
    # For the birthplace and residence, the place ID is provided.
    output = {
        "name": " ".join((name1, name2, name3)),
        "gender": gender,
        "language": language,
        "birthday": birthday,
        "birthplace": birth["id"],
        "residence": residence["id"],
    }
    return output


def generate_citizen_names(language: str) -> tuple[str, bool]:
    """ Generate a string with some Kargadian names """
    try:
        names = []
        for i in range(10):
            name, gender = generate_citizen(language, name_only=True)
            names.append(f"`{name}` ({gender.title()})")
        return "Here are some Kargadian names for you:\n" + "\n".join(names), False
    except KeyError:
        return f"Invalid language specified: `{language}`.", True


def generate_citizen_embed(citizen_language: str) -> tuple[discord.Embed | str, bool]:
    """ Generate an Embed with a Kargadian citizen """
    try:
        citizen = generate_citizen(citizen_language, name_only=False)
    except KeyError:
        # Technically this can be called by the button Interaction and fail by AttError,
        # but I think we can just ignore this for now
        return f"Invalid language specified: `{citizen_language}`.", True

    embed = discord.Embed(colour=random_colour())

    language = languages.Language("en")

    embed.title = "Kargadia Random Citizen Generator"
    # embed.add_field(name="Citizen ID", value=data["id"], inline=True)
    embed.add_field(name="Full Name", value=citizen["name"], inline=True)
    embed.add_field(name="Gender", value=citizen["gender"].title(), inline=True)

    embed.add_field(name="Date of Birth", value=language.time(citizen["birthday"], short=0, dow=False, seconds=True, tz=True, at=True), inline=False)
    embed.add_field(name="Age (in Kargadian time)", value=language.delta_dt(citizen["birthday"], accuracy=3, brief=False, affix=False), inline=False)

    embed.add_field(name="Native Language", value=language.data("_languages").get(citizen["language"]), inline=False)
    birth = conworlds.Place(citizen["birthplace"])
    embed.add_field(name="Place of Birth", value=f"{birth.name_translation(language)}, {birth.state}", inline=True)
    residence = conworlds.Place(citizen["residence"])
    embed.add_field(name="Place of Residence", value=f"{residence.name_translation(language)}, {residence.state}", inline=True)
    return embed, False


def distance_between_places(lat1: float, long1: float, lat2: float, long2: float, planet: str = "Kargadia") -> float:
    """ Return the distance between two coordinates on the given planet, in kilometres.

     The formula used here assumes the planet is a perfect sphere, and as such can result in errors of up to 0.5%,
     however I don't think this is a particularly big deal at the moment. """
    # TODO: Consider updating the formula used here to a more accurate one (or put it as an optional separate function)
    # https://stackoverflow.com/questions/19412462/getting-distance-between-two-points-based-on-latitude-longitude/43211266#43211266
    # https://en.wikipedia.org/wiki/Vincenty%27s_formulae
    radii = {
        "Earth": 6378.137,

        "Virkada": 5224.22,
        "Zeivela": 7008.10,
        "Kargadia": 7326.65,
        "Qevenerus": 14016.20,
    }
    try:
        radius = radii[planet]
    except KeyError:
        raise ValueError(f"{planet!r} is not a valid planet.") from None

    la1, la2 = rad(lat1), rad(lat2)  # Latitudes expressed in radians
    dla, dlo = rad(lat2 - lat1), rad(long2 - long1)  # Delta of latitudes, delta of longitudes expressed in radians
    a = sin(dla / 2) ** 2 + cos(la1) * cos(la2) * (sin(dlo / 2) ** 2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = radius * c  # km
    return distance
