# script to add terms from cf xml files.
# Sam Pepler 2012

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

    cfxmlfilename = sys.argv[1]


    cflist = VocabList.objects.get(pk=1)

    # look at CF list xml from PCMDI site
    tree = ET.parse(cfxmlfilename)
    table = tree.getroot()
    version = table.find('version_number').text

    cfversion = VocabListVersion(vocab_list=cflist, version=version) 
    cfversion.save()
    
    for entry in table.findall('entry'):
        term = entry.get('id').strip()
        desc = entry.find('description')
        if desc != None: 
            desc = desc.text
            if desc == None: desc=''
            else: desc =desc.strip()
        else: desc =''
        grib = entry.find('grib')
        if grib != None: grib = grib.text.strip()
        else: grib =''
        amip = entry.find('amip')
        if amip != None: amip = amip.text.strip()
        else: amip =''
        units = entry.find('canonical_units')
        if units != None: units = units.text.strip()
        else: units =''
                
        print "%s (%s): %s (GRIB:%s, AMIP:%s)" % (term, units, desc[0:30], grib, amip)
        existing = Term.objects.filter(name=term, description=desc, grib=grib, amip=amip, unit=units)
        if len(existing) == 0: 
            t = Term(name=term, description=desc, grib=grib, amip=amip, unit=units, externalid='')
            t.save()
        else: 
            t = existing[0]
        cfversion.terms.add(t)


    for alias in table.findall("alias"):
        alias_id = alias.get('id').strip()
        
        name = alias.find('entry_id')
        if name != None: name = name.text.strip()
        else: name = ''
     
        print "ALIAS: %s -> %s" % (alias_id, name)
        existing = Term.objects.filter(name=name)
        if len(existing) == 0: 
            raise "alias to non-existing term"
        else: 
            a = Alias(name=alias_id, term=existing[0])
            a.save()
            cfversion.aliases.add(a)


