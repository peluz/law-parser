import re
import nltk


class Parser(object):
    def preprocess(self, citation):
        citation = re.sub(r'[^\w\s]', '', citation).lower()
        return re.sub(r'\s+', ' ', citation).strip()

    def setCitation(self, citation):
        self.citation = self.preprocess(citation).split(" ")
        self.currentTokenIndex = -1
        self.lawObject = {"artigos": []}
        self.alineas = []
        self.incisos = []
        self.paragrafos = []

    def getCurrentToken(self):
        return self.citation[self.currentTokenIndex]

    def updateToken(self):
        if self.currentTokenIndex == len(self.citation):
            return False
        else:
            self.currentTokenIndex += 1
            return True

    def processToken(self):
        if self.getCurrentToken() == "alínea":
            self.updateToken()
            self.alineas.append(self.getCurrentToken())
        elif self.getCurrentToken() == "inciso":
            self.updateToken()
            self.incisos.append({"id": self.getCurrentToken()})
            if self.alineas:
                self.incisos[-1]["alineas"] = self.alineas
                self.alineas = []
        elif self.getCurrentToken() == "art":
            self.updateToken()
            artigo = {"id": self.getCurrentToken(), "incisos": []}
            if self.incisos:
                artigo["incisos"].append(self.incisos)
                self.incisos = []
            if self.lawObject["artigos"]:
                self.lawObject["artigos"].append(artigo)
            else:
                self.lawObject["artigos"] = [artigo]
        elif self.getCurrentToken() == "código":
            lei = [self.getCurrentToken]
            while self.updateToken():
                lei.append(self.getCurrentToken())
            " ".join(lei)
            self.lawObject["lei"] = lei

        else:
            pass

    def parse(self, citation):
        self.setCitation(citation)
        while self.updateToken():
            try:
                self.processToken()
            except IndexError:
                break
        return self.lawObject
