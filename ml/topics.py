import warnings
from pathlib import Path

import pymorphy2
import re
import nltk
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from gensim.models import KeyedVectors, LdaModel
from typing import List
from gensim.models import Phrases
from gensim.corpora import Dictionary

W2V_PATH = str(Path(__file__).parent.parent / 'add_data' / 'word2vec_moretech.bin')
PHRASES_PATH = str(Path(__file__).parent.parent / 'add_data' / 'phrases_model_last.txt')
LDA_PATH = str(Path(__file__).parent.parent / 'add_data' / 'lda_last.txt')
DICTIONARY_PATH = str(Path(__file__).parent.parent / 'add_data' / 'dictionary_last.txt')

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)


class Preparator():
    def __init__(self):
        self.morph = pymorphy2.MorphAnalyzer()
        self.tokenizer = nltk.WordPunctTokenizer()
        self.regexp = re.compile('[-%-,_\.\n\\\t\r/\W]')  # оставляет только буквы и цифры
        self.pos_decoder = {"ADJF": "ADJ",
                            'ADJS': 'ADJ',
                            'COMP': 'ADJ',
                            'INFN': 'VERB',
                            'PRTF': 'VERB'}

    def norm_word(self, word: str) -> str:
        w = str(re.sub(' +', ' ', self.regexp.sub(' ', word.lower()))).strip()
        if len(w) > 1 and w[0].isalpha():
            parsed = self.morph.parse(w)[0]
            tag = str(parsed.tag.POS)
            if tag not in ['NPRO', 'PRED', 'PREP', 'CONJ', 'PRCL', 'INTJ', 'VERB']:
                tag = tag if tag not in self.pos_decoder else self.pos_decoder[tag]
                return parsed.normal_form.replace('ё', 'e')
        return ''

    def norm_sentence(self, sentence: str):
        tokens = list(
            filter(lambda x: len(x), [self.norm_word(word) for word in self.tokenizer.tokenize(sentence.lower())]))
        # bigrams = ['_'.join(w) for w in  ngrams(tokens,n=2)]
        return tokens


def extract_keywords(tokens: List[str],
                     embeddings: KeyedVectors,
                     top_n: int = 5,
                     diversity: float = 0.5,
                     nr_candidates: int = 20) -> str:
    candidates = []
    doc_embedding = text2vec(tokens, embeddings).reshape(1, -1)
    candidate_embeddings = []
    for candidate in tokens:
        if candidate in embeddings:
            candidates.append(candidate)
            candidate_embeddings.append(embeddings[candidate])

    if len(candidates) == 0:
        return tokens

    # Calculate distances and extract keywords
    distances = cosine_similarity(np.nan_to_num(doc_embedding), np.nan_to_num(candidate_embeddings))
    keywords = [candidates[index] for index in distances.argsort()[0][-top_n:]][::-1]

    return list(set(keywords))


def text2vec(tokens: List[str], embeddings: KeyedVectors) -> np.ndarray:
    relevant = 0
    words_vecs = np.zeros((embeddings.vector_size,))
    for word in tokens:
        if word in embeddings:
            words_vecs += embeddings.word_vec(word, True)
            relevant += 1

    if relevant:
        words_vecs /= relevant
    return words_vecs


class TopicGetter():
    def __init__(self,
                 W2V_PATH=W2V_PATH,
                 PHRASES_PATH=PHRASES_PATH,
                 LDA_PATH=LDA_PATH,
                 DICTIONARY_PATH=DICTIONARY_PATH):
        self.topics = [
            'нормативные проверки',
            'поставки',
            'законы',
            'налоги и проверки',
            'валюта',
            'банки',
            'судебные дела',
            'инвестиции',
            'торговля',
            'недвижимость'
        ]
        self.prep = Preparator()
        self.w2v = KeyedVectors.load_word2vec_format(W2V_PATH, binary=True, unicode_errors="ignore")
        self.bigram = Phrases.load(PHRASES_PATH)
        self.w_dictionary = Dictionary.load(DICTIONARY_PATH)
        self.lda = LdaModel.load(LDA_PATH)

    def get_single_new_topic(self, decoded_text):
        bow = [i[1] for i in self.lda.get_document_topics(decoded_text)]
        return self.topics[np.array(bow).argmax()]

    def get_topics(self, texts: List[str]):
        texts = [self.prep.norm_sentence(i) if i else [] for i in texts]
        texts = [self.bigram[i] for i in texts]
        texts = [extract_keywords(i, self.w2v, top_n=10) for i in texts]
        texts = [self.w_dictionary.doc2bow(doc) for doc in texts]
        return [self.get_single_new_topic(text) for text in texts]


"""
# EXAMPLE

print(TopicGetter().get_topics(["Это какая-то новость о том, что у магазинов начались проблемы с продажей алкогольной продукции
"]))

"""
