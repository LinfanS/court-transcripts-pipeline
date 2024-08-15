import nltk
nltk.download('wordnet')
from nltk.corpus import wordnet
from Levenshtein import jaro_winkler

def synonym_extractor(phrase:str)-> set[str]:
    synonyms = []
    for syn in wordnet.synsets(phrase):
        for l in syn.lemmas():
            synonyms.append(l.name())
    synonyms = set(synonyms)
    if phrase in synonyms:
        synonyms.remove(str(phrase))
    return synonyms

def remove_synonyms(words:list[str]) -> list[str]:
    for word in words: #replace any synonyms
        synonyms = synonym_extractor(word)
        if synonyms:
            for syn in synonyms:
                if str(syn) in set(words):
                    words = list(map(lambda x: x.replace(word, syn), words))
                    #print(syn, 'has been replaced with', word, 'as found to be synonymous')
        
        for word2 in words: #replace any too-similar words
            if not word == word2:
                jw = jaro_winkler(word,word2)
                if jw > 0.9:
                    words = list(map(lambda x: x.replace(word, word2), words))
                    #print(word2, 'has been replaced with', word, 'as found to have a jw >0.9')
    return words

tags = [
                (
                    "judicial review",
                    "planning policy",
                    "local government",
                    "public consultation",
                    "transportation",
                    "legitimate expectation",
                    "development plan",
                    "administrative law",
                    "court ruling",
                ),
                (
                    "equal pay",)]
all_tags = []
for case in tags:
    for tag in case:
        all_tags.append(tag)
temp_tags = remove_synonyms(all_tags)
reconstruct = []
i = 0
for case in tags:
    group = []
    for tag in case:
        group.append(temp_tags[i])
        i+=1
    reconstruct.append(tuple(group))
print(reconstruct)