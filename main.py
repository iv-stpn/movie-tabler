import sys, os
import time
import regex as re
import difflib
import tmdbsimple as tmdb
from csv import reader

lang_codes = {}
language_file = open("../language-codes-full_csv.csv", "r")

after_header = False
for line in reader(language_file):
    if after_header:
        if line[2] != "":
            lang_codes[line[2]] = {
                "en": line[3].split("; ")[0].title(),
                "fr": line[4].split("; ")[0].title()
            }
    after_header = True

root = ""
output = "../tableau_films.csv"
output_unp = "../non_interprété.txt"

tmdb.API_KEY = ""

all_files = []
accepted_movie_format = [".mp4", ".mov", ".avi", ".mkv", ".mpg"]
separator_not_in_title = [".", "_"]

smallest_movie_size = 300 * 1024 * 1024

exceptions_list = ["a", "and", "in", "et", "de", "le", "la", "un", "une", "al", "di", "su"]
delete_all_after_string = ["CD 1", "CD 2"]
delete_all_before_string = []

# The order matters
lang_strings = {
    "it": ["ITALIEN"],
    "en": ["ENGLISH", "VOSTFR", "VOSTENG", "VO(ENG)", "VOST(ENG)", "ENG", "VOST(FR)", "VOST-VF", "VOST"],
    "fr": ["TRUEFRENCH", "FRENCH", "VF", "FR", "VO(FR)"],
    "En": ["VO"]
}

lang_sub_strings = {
    "fr": ["VOST(ENG)", "VOST(FR)", "VOST-VF", "VOSTFR"],

}

# The order matters
combinations = [lambda _string: " - " + _string, lambda _string: _string + ")", lambda _string: " " + _string]

default_lang = "fr"

non_processed = []
processed = []


def is_roman_num(_string):
    return bool(re.search(r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$", _string))


def convert_roman_num(s):
    rom_val = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    int_val = 0
    for i in range(len(s)):
        if i > 0 and rom_val[s[i]] > rom_val[s[i - 1]]:
            int_val += rom_val[s[i]] - 2 * rom_val[s[i - 1]]
        else:
            int_val += rom_val[s[i]]

    return int_val


def title_str(_t, exceptions):
    exceptions = [x.lower() for x in exceptions]
    return ' '.join(
        (x.title() if not is_roman_num(
            x.upper()) else x.upper()) if nm == 0 or not x.lower() in exceptions else x.lower() for nm, x in
        enumerate(_t.split(' ')))


def remove_extra_spaces(_string):
    _string = re.sub(r"\([^\S]*\)$", "", _string)
    _string = re.sub(r"^\([^\S]*\)", "", _string)
    _string = re.sub(r"^[ -]*", "", _string)
    _string = re.sub(r"[ -]*$", "", _string)
    _string = re.sub(r" +", " ", _string)
    _string = re.sub(r"[^\S]", " ", _string)

    return _string


for path, subdirs, files in os.walk(root):
    for name in files:
        for ext in accepted_movie_format:
            if name.endswith(ext) and os.path.getsize(os.path.join(path, name)) > smallest_movie_size:
                all_files.append([name.split(ext)[0]])
                if path != root:
                    all_files[-1].append(path.split("/")[-1])

                break

lang_searchers = {
    "fr": tmdb.Search(),
    "en": tmdb.Search(),
    "it": tmdb.Search()
}

year_combinations = ["(?:[ ]*-[ ]*\(([0-9]{4})\)){1}$", "(?:[ ]*\(([0-9]{4})\)){1}$", "(?:[ ]*-[ ]*([0-9]{4})){1}$",
                     "(?:- *([0-9]{4})\)){1}$",
                     "(?:[ ]*([0-9]{4})){1}$"]

prefix = "$"
remove_at_start = [r"^(([^\S]|\.|-)*[0-9]*([^\S]|\.|-)+)*", r"^(\[(.*\]))",
                   r"(\([0-9]{1,3}\))$", r"^" + prefix + "(?=[A-Z])"]

csv_file = open(output, 'w')
csv_file.write('"TITRE VF","TITRE ORIGINAL","LANGUE ORIGINALE","LANGUE SUR DISQUE","LANGUE SOUS-TITRES",\
                "ANNEE DE SORTIE","LIEN TMDB","VOTE MOYEN","POPULARITE","REALISATEUR PRINCIPAL","REALISATEUR SECONDAIRE",\
                "SCENARTISTE PRINCIPAL","SCENARTISTE SECONDAIRE", "ACTEUR PRINCIPAL",\
                "ACTEUR SECONDAIRE 1","ACTEUR SECONDAIRE 2","ACTEUR SECONDAIRE 3","ACTEUR SECONDAIRE 4",\
                "ACTEUR SECONDAIRE 5","ACTEUR SECONDAIRE 6","ACTEUR SECONDAIRE 7"')

unp_file = open(output_unp, "w")

target_language = "fr"

curr_mov = 0
for variants in all_files:
    curr_mov += 1
    for movie in variants:
        original_file_name = movie

        movie_id = None
        original_language = "Inconnue"
        original_title = "Inconnu"
        language = "Inconnue"
        year = "Inconnue"
        subtitles = "Inconnus"

        for separator in separator_not_in_title:
            movie = movie.replace(separator, " ")

        for reg in remove_at_start:
            movie = re.sub(reg, "", movie)

        movie = remove_extra_spaces(movie)
        movie = title_str(movie, exceptions_list)

        find = False
        for lang in lang_strings:
            find = False
            for string in lang_strings[lang]:
                string = title_str(string, exceptions_list)
                for comb in combinations:
                    if comb(string) in movie:
                        language = lang.lower()
                        for _lang in lang_sub_strings:
                            for subtitle_string in lang_sub_strings[_lang]:
                                if string == title_str(subtitle_string, exceptions_list):
                                    subtitles = _lang

                        movie = movie.replace(comb(string), "")
                        movie = remove_extra_spaces(movie)
                        find = True
                        break
                if find:
                    break
            if find:
                break

        for string in delete_all_after_string:
            string = title_str(string, exceptions_list)
            if string in movie:
                movie = movie.split(string)[0][:-1]

        for string in delete_all_before_string:
            string = title_str(string, exceptions_list)
            if string in movie:
                movie = movie.split(string)[1]

        previous_title = movie
        for year_regex in year_combinations:
            groups = re.search(year_regex, movie)
            if groups:
                year = groups.group(1)
                movie = re.sub(year_regex, "", movie)
                movie = remove_extra_spaces(movie)
                break

        titles = []

        for _lang in lang_searchers:
            response = lang_searchers[_lang].movie(query=movie, language=_lang)
            for s in lang_searchers[_lang].results[:4]:
                titles.append((s["title"], s["id"], s["popularity"],
                               s["release_date"][:4] if "release_date" in s else "Inconnue", _lang, s))

            if previous_title != movie:
                response = lang_searchers[_lang].movie(query=previous_title, language=_lang)
                for s in lang_searchers[_lang].results[:4]:
                    titles.append((s["title"], s["id"], s["popularity"],
                                   s["release_date"][:4] if "release_date" in s else "Inconnue", _lang, s))

        roman = [[is_roman_num(s), s] for s in previous_title.split(" ")]
        if any(r[0] for r in roman):
            for r in roman:
                if r[0]:
                    r[1] = str(convert_roman_num(r[1]))

            title_without_roman = " ".join([r[1] for r in roman])
            for _lang in lang_searchers:
                response = lang_searchers[_lang].movie(query=title_without_roman, language=_lang)
                for s in lang_searchers[_lang].results[:4]:
                    titles.append((s["title"], s["id"], s["popularity"],
                                   s["release_date"][:4] if "release_date" in s else "Inconnue", _lang, s))

        if len(titles) != 0:
            title = difflib.get_close_matches(title_without_roman if any(r[0] for r in roman) else movie, [t[0] for t in titles])[:1]
            if len(title) == 1:
                title = title[0]
            else:
                title = titles[0][0]

            movies_with_title = [t for t in titles if t[0] == title]
            find = False

            for _movie in movies_with_title:
                if _movie[3] == year and year != "Inconnue":
                    find = True
                    break

            if not find:
                title = difflib.get_close_matches(title_without_roman if any(r[0] for r in roman) else movie,
                                                  [t[0] for t in titles])[:1]
                if len(title) == 1:
                    title = title[0]
                else:
                    title = titles[0][0]

                movies_with_title = [t for t in titles if t[0] == title]
                find = False

                for _movie in movies_with_title:
                    if _movie[3] == year and year != "Inconnue":
                        find = True
                        break

                if not find:
                    _movie = max(movies_with_title, key=lambda t: t[2])

                year = _movie[3]

            if _movie[0] in processed:
                break
            else:
                processed.append(_movie[0])

            if language == "Unknown":
                language = _movie[4]

            original_language = _movie[5]['original_language']
            original_title = _movie[5]['original_title']
            vote = _movie[5]['vote_average']

            target_language_title = [t for t in titles if t[1] == _movie[1] and t[4] == target_language][0][0]

            csv_line = ['"' + target_language_title + '"', '"' + original_title + '"',
                        lang_codes[original_language][
                            target_language] if original_language in lang_codes else original_language,
                        lang_codes[language][target_language] if language in lang_codes else language,
                        lang_codes[subtitles][target_language] if subtitles in lang_codes else subtitles, year,
                        "https://www.themoviedb.org/movie/" + str(_movie[1]),
                        str(vote) + "/10", str(_movie[2])]

            movie_tmdb = tmdb.Movies(_movie[1])
            credits = movie_tmdb.credits()

            actors = [actor["name"] for actor in credits["cast"][:8]]
            directors = [c["name"] for c in credits["crew"] if c["department"] == "Directing"][:2]
            writers = [c["name"] for c in credits["crew"] if c["department"] == "Writing"][:2]

            n_actors = len(actors)
            n_directors = len(directors)
            n_writers = len(writers)

            for i in range(n_directors):
                csv_line.append(directors[i])

            for i in range(2 - n_directors):
                csv_line.append("")

            for i in range(n_writers):
                csv_line.append(writers[i])

            for i in range(2 - n_writers):
                csv_line.append("")

            for i in range(n_actors):
                csv_line.append(actors[i])

            for i in range(8 - n_actors):
                csv_line.append("")

            csv_file.write("\n" + ",".join(csv_line))
            break

        elif variants[-1] == original_file_name:
            non_processed.append(original_file_name)

csv_file.close()

for unp in non_processed:
    unp_file.write(unp + "\n")

unp_file.close()