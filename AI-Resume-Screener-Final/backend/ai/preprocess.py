import re
import spacy

nlp = spacy.load("en_core_web_sm")


class TextPreprocessor:

    @staticmethod
    def preprocess(text):

        text = text.lower()

        text = re.sub(r"[^a-zA-Z0-9 ]", " ", text)

        doc = nlp(text)

        words = []

        for token in doc:

            if token.is_stop:
                continue

            if token.is_punct:
                continue

            if token.is_space:
                continue

            words.append(token.lemma_)

        return " ".join(words)