from core.languages import TOP_50_LANGUAGES


class TestLanguages:
    def test_includes_european_national_languages(self):
        required = {
            "Albanian",
            "Armenian",
            "Azerbaijani",
            "Belarusian",
            "Bosnian",
            "Bulgarian",
            "Catalan",
            "Croatian",
            "Czech",
            "Danish",
            "Dutch",
            "English",
            "Estonian",
            "Finnish",
            "French",
            "Georgian",
            "German",
            "Greek",
            "Hungarian",
            "Icelandic",
            "Irish",
            "Italian",
            "Latvian",
            "Lithuanian",
            "Luxembourgish",
            "Macedonian",
            "Maltese",
            "Montenegrin",
            "Norwegian",
            "Polish",
            "Portuguese",
            "Romanian",
            "Romansh",
            "Russian",
            "Serbian",
            "Slovak",
            "Slovene",
            "Spanish",
            "Swedish",
            "Turkish",
            "Ukrainian",
        }

        assert required.issubset(set(TOP_50_LANGUAGES))

    def test_includes_historical_indo_european_languages(self):
        required = {
            "Proto-Indo-European (reconstructed)",
            "Anatolian: Hittite",
            "Anatolian: Luwian",
            "Anatolian: Lycian",
            "Avestan",
            "Classical Armenian",
            "Classical Sanskrit",
            "Vedic Sanskrit",
            "Pali",
            "Old Persian",
            "Ancient Greek",
            "Mycenaean Greek",
            "Latin",
            "Old Italic: Oscan",
            "Old Italic: Umbrian",
            "Gothic",
            "Old Norse",
            "Old English",
            "Old High German",
            "Old Saxon",
            "Old Irish",
            "Gaulish",
            "Celtiberian",
            "Old Church Slavonic",
            "Old East Slavic",
            "Tocharian A",
            "Tocharian B",
            "Phrygian",
            "Messapic",
        }

        assert required.issubset(set(TOP_50_LANGUAGES))

    def test_includes_historical_east_asian_languages(self):
        required = {
            "Old Japanese",
            "Classical Japanese",
            "Kanbun",
            "Old Chinese",
            "Middle Chinese",
            "Classical Chinese",
            "Literary Chinese",
            "Old Korean",
            "Middle Korean",
            "Old Tibetan",
            "Classical Tibetan",
            "Tangut",
            "Khitan",
            "Jurchen",
            "Classical Mongolian",
            "Old Vietnamese",
        }

        assert required.issubset(set(TOP_50_LANGUAGES))

    def test_has_no_duplicates(self):
        assert len(TOP_50_LANGUAGES) == len(set(TOP_50_LANGUAGES))
