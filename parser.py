import re
import pdb
from nltk import tokenize
import string


class Parser(object):
    def preprocess(self, citation):
        tokens = tokenize.word_tokenize(citation, language="portuguese")
        return [x.lower() for x in tokens if x not in string.punctuation]

    def setCitation(self, citation):
        self.citation = self.preprocess(citation)
        self.currentTokenIndex = -1
        self.lawObject = {}
        self.alineas = []
        self.incisos = None
        self.paragrafos = []

    def getCurrentToken(self):
        return self.citation[self.currentTokenIndex]

    def updateToken(self):
        self.currentTokenIndex += 1
        if self.currentTokenIndex == len(self.citation):
            return False
        else:
            return True

    def processToken(self):
        tokenType = self.identifyTokenType(self.getCurrentToken())
        if tokenType == "ALINEA":
            self.processAlinea()
        elif tokenType == "INCISO":
            self.processInciso()
        elif tokenType == "ARTIGO":
            self.processArtigo()
        elif tokenType == "LEI":
            self.processLei()
        elif tokenType == "PARAGRAFO":
            self.processParagrafo()
        else:
            pass

    def parse(self, citation):
        self.setCitation(citation)
        while self.updateToken():
            try:
                self.processToken()
            except IndexError:
                break
        self.tieLooseEnds()
        print(self.lawObject)
        return self.lawObject

    def tieLooseEnds(self):
        if self.incisos:
            if "incisos" not in self.lawObject["artigos"][-1]:
                self.lawObject["artigos"][-1]["incisos"] = []
            self.lawObject["artigos"][-1]["incisos"].append(self.incisos)
            self.incisos = []
        if self.paragrafos:
            if "paragrafos" not in self.lawObject["artigos"][-1]:
                self.lawObject["artigos"][-1]["paragrafos"] = []
            self.lawObject["artigos"][-1]["paragrafos"].append(self.paragrafos)
            self.paragrafos = []

    def isRomanNumeral(self, token):
        return not set(token.upper()).difference('MDCLXVI')

    def isLaw(self, token):
        if token in ["lei", "código", "estatuto"]:
            return True
        elif token.startswith("res") or (token[0] == "c" and len(token) < 4):
            return True
        else:
            return False

    def identifyTokenType(self, token):
        if token == "alínea":
            return "ALINEA"
        elif token == "inciso" or self.isRomanNumeral(token):
            return "INCISO"
        elif token in ["artigo", "art"]:
            return "ARTIGO"
        elif token in ["§", "parágrafo"]:
            return "PARAGRAFO"
        elif self.isLaw(token):
            return "LEI"
        else:
            return "DONT_CARE"

    def processAlinea(self):
        self.updateToken()
        self.alineas.append(self.getCurrentToken())

    def processInciso(self):
        if not self.isRomanNumeral(self.getCurrentToken()):
            self.updateToken()
        self.incisos = {"id": self.getCurrentToken()}
        if self.alineas:
            self.incisos["alineas"] = self.alineas
            self.alineas = []

    def processArtigo(self):
        self.updateToken()
        artigo = {"id": self.getCurrentToken().rstrip(".º")}
        if self.incisos:
            if "incisos" not in artigo:
                artigo["incisos"] = []
            artigo["incisos"].append(self.incisos)
            self.incisos = []
        if self.paragrafos:
            if "paragrafos" not in artigo:
                artigo["paragrafos"] = []
            artigo["paragrafos"].append(self.paragrafos)
            self.paragrafos = []
        if "artigos" not in self.lawObject:
            self.lawObject["artigos"] = []
        if self.lawObject["artigos"]:
            self.lawObject["artigos"].append(artigo)
        else:
            self.lawObject["artigos"] = [artigo]

    def processLei(self):
        lei = [self.getCurrentToken()]
        while self.updateToken():
            lei.append(self.getCurrentToken())
        lei = " ".join(lei)
        self.lawObject["lei"] = lei

    def processParagrafo(self):
        self.updateToken()
        self.paragrafos = {"id": self.getCurrentToken().rstrip(".º")}
