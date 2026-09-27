# Output font naming, shared by the FontForge stage's actions.
from os import path

COPYRIGHT = """
Programming ligatures added by Ilya Skriblovsky from FiraCode
FiraCode Copyright (c) 2015 by Nikita Prokopov"""


def replace_sfnt(font, key, value):
    font.sfnt_names = tuple(
        (row[0], key, value) if row[1] == key else row for row in font.sfnt_names
    )


def update_font_metadata(font, new_name):
    # Figure out the input font's real name (i.e. without a hyphenated suffix)
    # and hyphenated suffix (if present)
    old_name = font.familyname
    try:
        suffix = font.fontname.split("-")[1]
    except IndexError:
        suffix = None

    # Replace the old name with the new name whether or not a suffix was present.
    # If a suffix was present, append it accordingly.
    font.familyname = new_name
    if suffix:
        font.fullname = f"{new_name} {suffix}"
        font.fontname = "{}-{}".format(new_name.replace(" ", ""), suffix)
    else:
        font.fullname = new_name
        font.fontname = new_name.replace(" ", "")

    print(f"Ligaturizing font {path.basename(font.path)} ({old_name}) as '{new_name}'")

    font.copyright = (font.copyright or "") + COPYRIGHT
    replace_sfnt(font, "UniqueID", f"{font.fullname}; Ligaturized")
    replace_sfnt(font, "Preferred Family", new_name)
    replace_sfnt(font, "Compatible Full", new_name)
    replace_sfnt(font, "Family", new_name)
    replace_sfnt(font, "WWS Family", new_name)
