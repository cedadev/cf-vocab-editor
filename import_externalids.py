# script to add externalid to vocabterms.
# Sam Pepler 2013-02-12

import getopt, sys
import os, errno

from django.core.management import setup_environ
import settings
setup_environ(settings)

from vocab.models import *

import xml.etree.ElementTree as ET


def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)


   

if __name__=="__main__":

    NERCvocabxmlfilename = sys.argv[1]

    # make a table to find external id from NERC vocab server xml file
    nercvstable = {}
    tree = ET.parse(NERCvocabxmlfilename)
    root = tree.getroot()

    print root.getchildren()

    from xml.etree.ElementTree import QName

    namespace = 'http://www.w3.org/2004/02/skos/core#'
    collection = root.findall('{http://www.w3.org/2004/02/skos/core#}Collection')[0]
#    print collection.findall('{http://www.w3.org/2004/02/skos/core#}member')

    for member in collection.findall('{http://www.w3.org/2004/02/skos/core#}member'):
        concept = member.findall('{http://www.w3.org/2004/02/skos/core#}Concept')[0]
        # get external id
        extid = concept.find('{http://www.w3.org/2004/02/skos/core#}notation').text
        # get term name
        termname = concept.find('{http://www.w3.org/2004/02/skos/core#}prefLabel').text

        print extid, termname
        if extid and termname: 
            junk, extid = extid.split('::')
            nercvstable[termname]=extid


    for t in Term.objects.all():
        if nercvstable.has_key(t.name): t.externalid =  nercvstable[t.name]
        else: t.externalid = ''
        print t.name, t.externalid
        t.save()
         


