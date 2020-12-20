import sys, os
import regex as re
import difflib

root = "/films"
output = "./tableau_films.csv"

all_files = []
accepted_movie_format = [".mp4", ".mov", ".avi", ".mkv", ".mpg"]
separator_not_in_title = [".", "_"]

smallest_movie_size = 300 * 1024 * 1024

exceptions_list = ["a", "and", "in", "et", "de", "le", "la", "un", "une", "al", "di", "su"]
delete_all_after_string = ["CD"]

# The order matters
lang_strings = {
    "It": ["ITALIEN"],
    "En": ["ENGLISH", "VOSTENG", "VO(ENG)", "VOST(ENG)", "ENG", "VOST(FR)", "VOST-VF", "VOST", "VO"],
    "Fr": ["FRENCH", "VF", "FR"]
}

lang_sub_strings = {
    "Fr": ["VOST(ENG)", "VOST(FR)", "VOST-VF"],

}

# The order matters
combinations = [lambda _string: " - " + _string, lambda _string: _string + ")", lambda _string: " " + _string]


def is_roman_num(_string):
    return bool(re.search(r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$", _string))


def title_str(title, exceptions):
    exceptions = [x.lower() for x in exceptions]
    return ' '.join(
        (x.title() if not is_roman_num(
            x.upper()) else x.upper()) if nm == 0 or not x.lower() in exceptions else x.lower() for nm, x in
        enumerate(title.split(' ')))


def remove_extra_spaces(_string):
    _string = re.sub(r"^[ -)]*", "", _string)
    _string = re.sub(r"[ (-]*$", "", _string)
    _string = re.sub(r"()$", "", _string)
    _string = re.sub(r"^()", "", _string)
    _string = re.sub(r" +", " ", _string)
    _string = re.sub(r"[^\S]", " ", _string)

    return _string


for path, subdirs, files in os.walk(root):
    for name in files:
        for ext in accepted_movie_format:
            if name.endswith(ext) and os.path.getsize(os.path.join(path, name)) > smallest_movie_size:
                all_files.append(name.split(ext)[0])
                break

year_combinations = ["[ ]*-[ ]*\(([0-9]{4})\)$", "[ ]*\(([0-9]{4})\)$", "[ ]*-[ ]*([0-9]{4})$", "- *([0-9]{4})\)$", "[ ]*([0-9]{4})$"]
for movie in all_files:
    language = "Unknown"
    year = "Unknown"
    subtitles = "Unknown"

    for separator in separator_not_in_title:
        movie = movie.replace(separator, " ")

    movie = re.sub(r"^(?:(?:[^\S]|\.|-)*[0-9]*(?:[^\S]|\.|-)+)*", "", movie)
    movie = re.sub(r"^(?:\[(?:.*\]))", "", movie)
    movie = remove_extra_spaces(movie)

    movie = re.sub(r"^(?:(?:[^\S]|\.|-)*-*(?:[^\S]|\.|-)+)*", "", movie)

    movie = title_str(movie, exceptions_list)

    find = False
    for lang in lang_strings:
        find = False
        for string in lang_strings[lang]:
            string = title_str(string, exceptions_list)
            for comb in combinations:
                if comb(string) in movie:
                    language = lang
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

    for year_regex in year_combinations:
        groups = re.search(year_regex, movie)
        if groups:
            year = groups.group(1)
            movie = movie.replace(year, "")
            movie = remove_extra_spaces(movie)
            break

    print("TITLE: " + movie + ", LANGUAGE: " + language + ", YEAR: " + year + ", SUBTITLES: " + subtitles)
