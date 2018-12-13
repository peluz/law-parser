import re
import pdb
from nltk import tokenize
import string


class Parser(object):
    def preprocess(self, citation):
        citation = re.sub(r"c\/c", "e", citation, flags=re.I)
        citation = re.sub(r"§(?!§)", "§ ", citation)
        citation = re.sub(r"(?<=\s)p[\.]?[úu]n?", "§ único", citation)
        citation = re.sub(r"“", "``", citation)
        tokens = tokenize.word_tokenize(citation, language="portuguese")
        tokens = [x.rstrip(".º°") for x in tokens if x not in string.punctuation]
        return tokens

    def setCitation(self, citation):
        self.citation = self.preprocess(citation)
        self.currentTokenIndex = -1
        self.lawObject = {}
        self.alineas = []
        self.incisos = []
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
        if "artigos" not in self.lawObject:
            if self.citation[0].isdigit():
                self.lawObject["artigos"] = [{"id": self.citation[0]}]
        if self.incisos:
            if "incisos" not in self.lawObject["artigos"][-1]:
                self.lawObject["artigos"][-1]["incisos"] = []
            while self.incisos:
                self.lawObject["artigos"][-1]["incisos"].append(self.incisos.pop(0))
        if self.paragrafos:
            if "paragrafos" not in self.lawObject["artigos"][-1]:
                self.lawObject["artigos"][-1]["paragrafos"] = []
            while self.paragrafos:
                self.lawObject["artigos"][-1]["paragrafos"].append(self.paragrafos.pop(0))
        if self.alineas:
            if "incisos" in self.lawObject["artigos"][-1]:
                self.lawObject["artigos"][-1]["incisos"][-1]["alineas"] = self.alineas
            else:
                self.lawObject["artigos"][-1]["alineas"] = self.alineas

    def isRomanNumeral(self, token):
        return not set(token).difference('LXVI')

    def isLaw(self, token):
        token = token.lower()
        if token in ["lei", "código", "estatuto", "constituição", "mp",
                     "medida", "emenda", "carta", "regimento", "regulamento",
                     "decreto", "convenção", "decreto-lei", "ncpc"]:
            return True
        elif (token.startswith("res") or token.startswith("cf") or
             token.startswith("ri") or
             (token[0] in ["c", "l"] and len(token) < 5)):
            return True
        else:
            return False

    def identifyTokenType(self, token):
        lower_token = token.lower()
        if lower_token in ["inciso", "incisos"] or self.isRomanNumeral(token):
            return "INCISO"
        elif self.isLaw(lower_token):
            return "LEI"
        elif lower_token in ["artigo", "art", "arts"] or token.isdigit():
            return "ARTIGO"
        elif lower_token in ["§", "parágrafo", "§§"]:
            return "PARAGRAFO"
        elif (lower_token in ["alínea", "``"] or
             (lower_token in list(string.ascii_lowercase) and
              lower_token != "e")):
            return "ALINEA"
        else:
            return "DONT_CARE"

    def processAlinea(self):
        while self.getCurrentToken().lower() in ["alínea", "``"]:
            self.updateToken()
        self.alineas.append(self.getCurrentToken().lower())

    def processInciso(self):
        if not self.isRomanNumeral(self.getCurrentToken()):
            self.updateToken()
        self.incisos.append({"id": self.getCurrentToken().lower()})
        if self.alineas:
            self.incisos[-1]["alineas"] = self.alineas
            self.alineas = []
        if "artigos" in self.lawObject and self.citation[self.currentTokenIndex + 1] != "do":
            if "incisos" not in self.lawObject["artigos"][-1]:
                self.lawObject["artigos"][-1]["incisos"] = []
            while self.incisos:
                self.lawObject["artigos"][-1]["incisos"].append(self.incisos.pop(0))

    def processArtigo(self):
        plural = False
        if self.getCurrentToken().lower() == "arts":
            plural = True
        if not self.getCurrentToken().isdigit():
            self.updateToken()
        artigo = {"id": self.getCurrentToken().lower()}
        if self.incisos:
            if "incisos" not in artigo:
                artigo["incisos"] = []
            while self.incisos:
                artigo["incisos"].append(self.incisos.pop(0))
            self.incisos = []
        if self.paragrafos:
            if "paragrafos" not in artigo:
                artigo["paragrafos"] = []
            while self.paragrafos:
                artigo["paragrafos"].append(self.paragrafos.pop(0))
        if "artigos" not in self.lawObject:
            self.lawObject["artigos"] = []
        if self.lawObject["artigos"]:
            self.lawObject["artigos"].append(artigo)
        else:
            self.lawObject["artigos"] = [artigo]
        if plural:
            self.updateToken()
            while self.identifyTokenType(self.getCurrentToken()) in ["ARTIGO", "DONT_CARE"]:
                if self.identifyTokenType(self.getCurrentToken()) == "DONT_CARE":
                    self.updateToken()
                else:
                    self.processArtigo()
                    self.updateToken()
            self.processToken()

    def processLei(self):
        lei = [self.getCurrentToken().lower()]
        while (self.updateToken() and
               self.getCurrentToken() not in ["art", "artigo",
                                              "arts", "artigos"]):
            lei.append(self.getCurrentToken().lower())
        lei = " ".join(lei)
        self.lawObject["lei"] = lei

    def processParagrafo(self):
        plural = False
        if self.getCurrentToken() == "§§":
            plural = True
        if not self.getCurrentToken().isdigit():
            self.updateToken()
        self.paragrafos.append({"id": self.getCurrentToken().lower()})
        if "artigos" in self.lawObject:
            if "paragrafos" not in self.lawObject["artigos"][-1]:
                self.lawObject["artigos"][-1]["paragrafos"] = []
            while self.paragrafos:
                self.lawObject["artigos"][-1]["paragrafos"].append(self.paragrafos.pop(0))
        if plural:
            self.updateToken()
            while self.identifyTokenType(self.getCurrentToken()) in ["ARTIGO", "DONT_CARE"]:
                if self.identifyTokenType(self.getCurrentToken()) == "DONT_CARE":
                    self.updateToken()
                elif self.getCurrentToken() == "art":
                    break
                else:
                    self.processParagrafo()
                    self.updateToken()
            self.processToken()
