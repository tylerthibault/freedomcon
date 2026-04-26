_CDN = "https://pub-fc470c82f793409f9e6c126deeb0387d.r2.dev/media_download"

# Each entry is a category rendered as an accordion panel in the Asset Library.
# All assets are served from the Cloudflare R2 CDN.
# Fields per asset:
#   label    – display name
#   thumb    – preview image URL
#   download – download URL
media_downloads = [
    {
        "id": "speakers",
        "label": "Speaker Graphics",
        "assets": [
            {"label": "Featured Speakers (16:9)",           "thumb": f"{_CDN}/1920x1080%20Featured%20Speakers%20(1).jpg",                "download": f"{_CDN}/1920x1080%20Featured%20Speakers%20(1).jpg"},
            {"label": "Featured Speakers Vertical",         "thumb": f"{_CDN}/1920x1080%20Featured%20Speakers%20VERTICAL%20(1).jpg",     "download": f"{_CDN}/1920x1080%20Featured%20Speakers%20VERTICAL%20(1).jpg"},
            {"label": "Gen Z Featured Speakers (16:9)",     "thumb": f"{_CDN}/1920x1080%20GEN%20Z%20Featured%20Speakers%20(1).jpg",      "download": f"{_CDN}/1920x1080%20GEN%20Z%20Featured%20Speakers%20(1).jpg"},
            {"label": "Gen Z Featured Speakers Vertical",   "thumb": f"{_CDN}/1920x1080%20GEN%20Z%20Featured%20Speakers%20VERTICAL.jpg", "download": f"{_CDN}/1920x1080%20GEN%20Z%20Featured%20Speakers%20VERTICAL.jpg"},
            {"label": "Featured Speakers + Gen Z (Print)",  "thumb": f"{_CDN}/8.5x11%20Featured%20Speakers%20PLUS%20GEN%20Z.jpg",       "download": f"{_CDN}/8.5x11%20Featured%20Speakers%20PLUS%20GEN%20Z.jpg"},
            {"label": "Featured Speakers (Square)",         "thumb": f"{_CDN}/SQUARE%20Featured%20Speakers%20(1).jpg",                   "download": f"{_CDN}/SQUARE%20Featured%20Speakers%20(1).jpg"},
            {"label": "Gen Z Featured Speakers (Square)",   "thumb": f"{_CDN}/SQUARE%20GEN%20Z%20Featured%20Speakers.jpg",               "download": f"{_CDN}/SQUARE%20GEN%20Z%20Featured%20Speakers.jpg"},
            {"label": "Adam James",                         "thumb": f"{_CDN}/Adam%20James_Flip.jpg",                                    "download": f"{_CDN}/Adam%20James_Flip.jpg"},
            {"label": "Chad Robichaux",                     "thumb": f"{_CDN}/Chad%20Robichaux_rising.jpg",                              "download": f"{_CDN}/Chad%20Robichaux_rising.jpg"},
            {"label": "Dave Barton",                        "thumb": f"{_CDN}/Dave%20Barton_freedom.jpg",                                "download": f"{_CDN}/Dave%20Barton_freedom.jpg"},
            {"label": "Eric Metaxas",                       "thumb": f"{_CDN}/Eric%20Metaxas_equipped.jpg",                              "download": f"{_CDN}/Eric%20Metaxas_equipped.jpg"},
            {"label": "Graham Allen",                       "thumb": f"{_CDN}/Graham%20Allen_where.jpg",                                 "download": f"{_CDN}/Graham%20Allen_where.jpg"},
            {"label": "John Lovell",                        "thumb": f"{_CDN}/John%20Lovell_statesman.jpg",                              "download": f"{_CDN}/John%20Lovell_statesman.jpg"},
            {"label": "Josh Howerton",                      "thumb": f"{_CDN}/Josh%20Howerton_freedom.jpg",                              "download": f"{_CDN}/Josh%20Howerton_freedom.jpg"},
            {"label": "Josh McPherson",                     "thumb": f"{_CDN}/Josh%20McPherson_we_stay.jpg",                             "download": f"{_CDN}/Josh%20McPherson_we_stay.jpg"},
            {"label": "Mark Driscoll",                      "thumb": f"{_CDN}/Mark%20Driscoll_lock.jpg",                                 "download": f"{_CDN}/Mark%20Driscoll_lock.jpg"},
            {"label": "Nate Schatzline",                    "thumb": f"{_CDN}/Nate%20Schatzline_WA.jpg",                                 "download": f"{_CDN}/Nate%20Schatzline_WA.jpg"},
            {"label": "Russell Johnson",                    "thumb": f"{_CDN}/Russell%20Johnson_join.jpg",                               "download": f"{_CDN}/Russell%20Johnson_join.jpg"},
            {"label": "Ryan Visconti",                      "thumb": f"{_CDN}/Ryan%20Visconti_obey.jpg",                                 "download": f"{_CDN}/Ryan%20Visconti_obey.jpg"},
            {"label": "Tim Barton",                         "thumb": f"{_CDN}/Time%20Barton_PNW.jpg",                                    "download": f"{_CDN}/Time%20Barton_PNW.jpg"},
        ],
    },
    {
        "id": "posters",
        "label": "Posters & Graphics",
        "assets": [
            {"label": "Make Washington America Again",      "thumb": f"{_CDN}/Make%20Washington%20America%20Again.png",        "download": f"{_CDN}/Make%20Washington%20America%20Again.png"},
            {"label": "Save The West",                      "thumb": f"{_CDN}/Save%20The%20West%201.png",                      "download": f"{_CDN}/Save%20The%20West%201.png"},
            {"label": "WA America Again",                   "thumb": f"{_CDN}/WA_america_again.png",                           "download": f"{_CDN}/WA_america_again.png"},
            {"label": "We Will Have Our Home Again",        "thumb": f"{_CDN}/We%20Will%20Have%20Our%20Home%20Again%202.png",  "download": f"{_CDN}/We%20Will%20Have%20Our%20Home%20Again%202.png"},
        ],
    },
    {
        "id": "conference_graphics",
        "label": "Conference Graphics",
        "assets": [
            # https://pub-fc470c82f793409f9e6c126deeb0387d.r2.dev/media_download/Freedom_con_front_3.png
            {"label": "Freedom Con Hero 1",      "thumb": f"{_CDN}/Freedom_con_front_3.png",        "download": f"{_CDN}/Freedom_con_front_3.png"},
            # https://pub-fc470c82f793409f9e6c126deeb0387d.r2.dev/media_download/Freedom_con_front_4.png
            {"label": "Freedom Con Hero 2",      "thumb": f"{_CDN}/Freedom_con_front_4.png",        "download": f"{_CDN}/Freedom_con_front_4.png"},
            # https://pub-fc470c82f793409f9e6c126deeb0387d.r2.dev/media_download/Freedom_con_front_5.png
            {"label": "Freedom Con Hero 3",      "thumb": f"{_CDN}/Freedom_con_front_5.png",        "download": f"{_CDN}/Freedom_con_front_5.png"},
        ],
    },
]