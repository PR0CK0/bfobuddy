##########
#  PR0CK0
# 07-22-22
##########

############################################################################
# Bare minimum command line script for quickly building a BFO-based taxonomy
# This script is a proof-of-concept; more functionality to come
############################################################################
# Call in command window like:
# >>> python3 bfobuddy.py [input file location]
# First line of file must be your intended IRI (e.g., http://test.org/test/)
# Do not forget your IRI end delimiter (/ or #)
# Second line of file must be your intended prefix (e.g., testo)
# All other lines in file are class names you want to represent in BFO
# Ensure these words only use letters and numbers
# Interact by typing the number of the class you want to extend (e.g., 0)
# Type the number twice to assert it as a sibling class (e.g., 00)
############################################################################
# Dump your domain lexicon into a file and get started using BFO
# A good exercise for learning BFO as you go
# Once done, use an editor like Protege to add relationships
############################################################################

# See also: https://www.michelepasin.org/blog/2011/07/18/inspecting-an-ontology-with-rdflib/
# See also: https://github.com/lambdamusic/Ontospy

import sys
import re
from rdflib import Graph
from rdflib import URIRef
from rdflib import Namespace
from rdflib.namespace import RDF
from rdflib.namespace import RDFS
from rdflib.namespace import OWL

##########
# "Global"
##########
bfoIRI = 'http://purl.obolibrary.org/obo/bfo.owl'
bfoGraph = Graph()
bfoGraph.parse(bfoIRI, format = 'application/rdf+xml')
bfo = Namespace('http://purl.obolibrary.org/obo/')
bfoGraph.namespace_manager.bind('bfo', bfo)

newGraph = Graph()
newGraph.namespace_manager.bind('bfo', bfo)
newGraph.bind('owl', OWL)

#########
# Methods
#########
def getSubClasses(graph, superClass):
    list = []
    for s, p, o in graph.triples((None, RDFS.subClassOf, superClass)):
        list.append(s)
    return list

def getNumClasses(graph):
    num = 0
    for s, p, o in graph.triples((None, RDF.type, OWL.Class)):
        num += 1
    for s, p, o in graph.triples((None, RDF.type, RDFS.Class)):
        num += 1
    return num

def isLeafNode(graph, clazz):
    temp = []
    for s in graph.triples((None, RDFS.subClassOf, clazz)):
        temp.append(s)
            
    if (len(temp) == 0):
        return True

def getSelection(selectionDictionary):    
    while True:
        selection = input('>>> ')
        if selection == '':
            print('>>>>> Invalid')
        elif re.match('[^0-9]{1,2}', selection):
            print('>>>>> Invalid')
        elif re.match('[0-9][^0-9]+', selection):
            print('>>>>> Invalid')
        elif int(selection) <= len(selectionDictionary) - 1 and int(selection) >= 0:
            return int(selection)
        elif re.match('[0-9][0-9]', selection) and int(selection[0]) <= len(selectionDictionary) - 1:
            return int(selection)
        else:
            print('>>>>> Invalid')

def traverseGraph(oldGraph, newGraph, newClass, newIRI):
    topClassEntity = URIRef(bfo.BFO_0000001)
    newClassIRI = newIRI + newClass.replace(' ', '')

    print(oldGraph.value(topClassEntity, RDFS.label).capitalize())

    subClasses = sorted(getSubClasses(oldGraph, topClassEntity))
    subClassesIndexed = {}

    indent = 1
    indentChar = '-'
    
    while True:
        for index, clazz in enumerate(subClasses):  
            subClassesIndexed[index] = subClasses[index]
            print(indentChar * indent
                 + '[' + str(index) + ']('
                 + oldGraph.value(clazz, RDFS.label).capitalize() + ')'
                 + '(' + str(len(getSubClasses(oldGraph, clazz))) + ' subclasses)')

        print('>>> ' + newClass + ' is a: ')
        selection = getSelection(subClassesIndexed)
        
        if len(str(selection)) == 2:
            assertedSiblingSelection = str(selection)[0]
            print('>>>>> ' + newClass + ' asserted as RDFS:subClassOf ' + oldGraph.value(subClassesIndexed[int(assertedSiblingSelection)], RDFS.label).capitalize() + '\n')
            newGraph.add((URIRef(newClassIRI), RDFS.subClassOf, subClassesIndexed[int(assertedSiblingSelection)]))
            return
        elif isLeafNode(oldGraph, subClassesIndexed[selection]):
            print('>>>>> ' + newClass + ' asserted as RDFS:subClassOf ' + oldGraph.value(subClassesIndexed[int(selection)], RDFS.label).capitalize() + '\n')
            newGraph.add((URIRef(newClassIRI), RDFS.subClassOf, subClassesIndexed[int(selection)]))
            return
        
        newGraph.add((URIRef(newClassIRI), RDF.type, OWL.Class))

        subClasses = sorted(getSubClasses(oldGraph, subClassesIndexed[int(selection)]))
        indent += 1

######
# Main
######
inputFile = sys.argv[1]

with open(inputFile) as file:
    newIRI = URIRef(next(file).strip())

    newGraph.add((newIRI, RDF.type, OWL.Ontology))
    newGraph.add((newIRI, OWL.imports, URIRef(bfoIRI)))
    newNamespace = Namespace(newIRI)
    newPrefix = next(file).strip()
    newGraph.namespace_manager.bind(newPrefix, newNamespace)

    print('#'*(len(str(newIRI)) + 6) + '\nIRI: ' + str(newIRI))
    print('Prefix: ' + newPrefix + '\n' + '#'*(len(str(newIRI)) + 6) + '\n')
    
    for line in file:
        traverseGraph(bfoGraph, newGraph, line.strip(), newIRI)

newGraph.serialize(destination = 'out.ttl', format = 'text/turtle')
print(str(getNumClasses(newGraph)) + ' new classes serialized as a turtle file in the same directory.')
