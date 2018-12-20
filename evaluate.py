from parser import Parser


parser = Parser()

with open("data/legislation.txt", "r") as source:
	for line in source:
		parser.parse(line)
