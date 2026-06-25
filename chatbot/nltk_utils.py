# nltk_utils.py
from nltk.stem.porter import PorterStemmer
from nltk.tokenize import TreebankWordTokenizer
import numpy as np

stemmer = PorterStemmer()
tokenizer = TreebankWordTokenizer()

def tokenize(sentence):
    return tokenizer.tokenize(sentence)

def stem(word):
    return stemmer.stem(word.lower())

def bag_of_words(tokenized_sentence, all_words):
    tokenized = [stem(w) for w in tokenized_sentence]
    return np.array([1 if w in tokenized else 0 for w in all_words], dtype=np.float32)
