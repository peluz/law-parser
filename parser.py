import re
import pdb
from nltk import tokenize
import string


class Parser(object):
    def preprocess(self, citation):
        citation = re.sub(r"c\/c", "e", citation, flags=re.I)
        citation = re.sub(r"§(?!§)", "§ ", citation)
        citation = re.sub(r"(?<=\s)p[\.]?[úu]n?", "§ único", citation)
        citation = re.sub(r"(?<=' )", ",", citation, flags=re.I)
        citation = re.sub(r"[“‘']", "`` ", citation)
        citation = re.sub(r"(``\s*)*caput", "", citation)
        citation = re.sub(r"\s*\(\s*s\s*\)", "s", citation)
        citation = re.sub(r"(?<=\d.)\s+a\s+(?=\d.)", " RANGE ", citation, flags=re.I)
        citation = re.sub(r"in fine", "0", citation, flags=re.I)
        citation = re.sub(r"art(igo)?s?[.](?=\d)", "artigo ", citation, flags=re.I)
        citation = re.sub(r"(\xad)|(\bou\b)", "", citation, flags=re.I)
        tokens = tokenize.word_tokenize(citation, language="portuguese")
        tokens = [x.rstrip(".ºª°-").lstrip("-") for x in tokens]
        tokens = list(filter(lambda x: x, tokens))
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
            if self.isNumber(self.citation[0].lower()):
                self.lawObject["artigos"] = [{"id": self.citation[0].lower()}]
            else:
                return
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
                     "decreto", "convenção", "decreto-lei", "ncpc",
                     "provimento", "portaria", "consolidação", "leis",
                     "adct", "texto", "lex", "instrução", "ec",
                     "projeto", "emendas", "despacho", "magna",
                     "dl", "rlsm", "permissivo", "mpr"]:
            return True
        elif (token.startswith("res") or token.startswith("cf") or
             token.startswith("ri") or token.startswith("in") or
             token.startswith("ec") or
             (token[0] in ["c", "l"] and len(token) < 10)):
            return True
        else:
            return False

    def identifyTokenType(self, token):
        lower_token = token.lower()
        if lower_token in ["inciso", "incisos", "inc", "incs"] or self.isRomanNumeral(token):
            return "INCISO"
        elif self.isLaw(lower_token):
            return "LEI"
        elif (lower_token in ["artigo", "art", "arts", "artigos"] or
              self.isNumber(token) or
              re.search(r"\d+-[a-z]", lower_token) is not None):
            return "ARTIGO"
        elif lower_token in ["§", "parágrafo", "§§"]:
            return "PARAGRAFO"
        elif (lower_token in ["alínea", "``", "alíneas"] or
             (lower_token in list(string.ascii_lowercase) and
              lower_token not in ["e", "o"])):
            return "ALINEA"
        else:
            return "DONT_CARE"

    def processAlinea(self):
        while self.getCurrentToken().lower() in ["alínea", "``", "alíneas"]:
            self.updateToken()
        if re.search(r"[a-z]", self.getCurrentToken().lower()) is None or len(self.getCurrentToken()) > 1:
            return
        if "artigos" in self.lawObject and "incisos" in self.lawObject["artigos"][-1]:
            self.lawObject["artigos"][-1]["incisos"][-1].setdefault("alineas", []).append(self.getCurrentToken().lower())
        else:
            self.alineas.append(self.getCurrentToken().lower())


    def processInciso(self):
        if not self.isRomanNumeral(self.getCurrentToken()):
            self.updateToken()
        if not self.isRomanNumeral(self.getCurrentToken()):
            return
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
        currentToken= self.getCurrentToken()
        if currentToken.lower() == "arts":
            plural = True
        if (not self.isNumber(currentToken) and
            re.search(r"\d+-[a-z]", currentToken, flags=re.I) is None):
            self.updateToken()
        currentToken = self.getCurrentToken()
        if re.search(r"\d", currentToken) is None:
            return
        artigo = {"id": currentToken.lower()}
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
        if self.citation[self.currentTokenIndex + 1] == "RANGE":
            plural = False
            begin = currentToken
            self.updateToken()
            self.updateToken()
            end = self.getCurrentToken()
            if "artigos" not in self.lawObject:
                self.lawObject["artigos"] = []
            for i in range(int(begin) + 1, int(end) + 1):
                self.lawObject["artigos"].append({"id": str(i)})
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
               self.getCurrentToken().lower() not in ["art", "artigo",
                                                      "arts", "artigos",
                                                      "em"] + list(string.punctuation)):
            lei.append(self.getCurrentToken().lower())
        lei = " ".join(lei)
        self.lawObject["lei"] = lei.rstrip(string.punctuation + " ")

    def processParagrafo(self):
        plural = False
        currentToken = self.getCurrentToken()
        if currentToken == "§§":
            plural = True
        if not self.isNumber(currentToken):
            self.updateToken()
        currentToken = self.getCurrentToken()
        self.paragrafos.append({"id": currentToken.lower()})
        if self.citation[self.currentTokenIndex + 1] == "RANGE":
            plural = False
            begin = re.sub(r"[^\d]+", "", currentToken)
            self.updateToken()
            self.updateToken()
            end = re.sub(r"[^\d]+", "", self.getCurrentToken())
            for i in range(int(begin) + 1, int(end) + 1):
                self.paragrafos.append({"id": str(i)})
        if ("artigos" in self.lawObject and
            self.citation[self.currentTokenIndex + 1] != "do" and
            not plural):
            if "paragrafos" not in self.lawObject["artigos"][-1]:
                self.lawObject["artigos"][-1]["paragrafos"] = []
            while self.paragrafos:
                self.lawObject["artigos"][-1]["paragrafos"].append(self.paragrafos.pop(0))
        if plural:
            self.updateToken()
            while self.identifyTokenType(self.getCurrentToken()) in ["ARTIGO", "DONT_CARE"]:
                if self.identifyTokenType(self.getCurrentToken()) == "DONT_CARE":
                    if self.getCurrentToken() == "e":
                        self.updateToken()
                        self.processParagrafo()
                        self.updateToken()
                        break
                    self.updateToken()
                elif self.getCurrentToken() == "art":
                    break
                else:
                    self.processParagrafo()
                    self.updateToken()
            self.processToken()

    def isNumber(self, token):
        return re.sub(r"[^\d\/]", "", token).isdigit()
