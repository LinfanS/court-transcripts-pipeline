import nltk
from nltk.corpus import wordnet
from Levenshtein import jaro_winkler
from judge_matching import match_judge, get_judges
from judges_seed import seed_judges

nltk.download("wordnet")


def synonym_extractor(phrase: str) -> set[str]:
    """Uses the wordnet module from the nltk library to find synonyms of a word"""
    synonyms = []
    for syn in wordnet.synsets(phrase):
        for l in syn.lemmas():
            synonyms.append(l.name())
    synonyms = set([word.capitalize() for word in synonyms])
    if phrase in synonyms:
        synonyms.remove(str(phrase))
    return synonyms


def replace_word_in_list(
    all_words: list[str], good_word: str, bad_word: str
) -> list[str]:
    """Function to replace words in a list with others"""
    return list(map(lambda x: x.replace(good_word, bad_word), all_words))


def replace_synonyms(words: list[str]) -> list[str]:
    """Replaces any synonym in a list of words with its original word.
    Based on the above synonym function or if it has a high jaro winkler match"""
    for word in words:  # replace any synonyms
        synonyms = synonym_extractor(word)
        if synonyms:
            for syn in synonyms:
                if str(syn) in set(words):
                    words = replace_word_in_list(words, word, syn)

        for word2 in words:  # replace any too-similar words
            if not word == word2:
                jw = jaro_winkler(word, word2)
                if jw > 0.9:
                    words = replace_word_in_list(words, word, word2)
    return words


if __name__ == "__main__":
    print(synonym_extractor("Claim"))
    print(replace_synonyms(["somalian", "Somali", "appellee", "appeal"]))
