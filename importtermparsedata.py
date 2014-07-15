# script to add storage pot for manual fileset set up.
# Sam Pepler 2011-09-22

import getopt, sys
import os, errno

from django.core.management import setup_environ
import settings
setup_environ(settings)

from vocab.models import *


if __name__=="__main__":

    filename = sys.argv[1]
    CF = open(filename)
    cflist = VocabList.objects.get(pk=1)
    
    while 1:
        line=CF.readline()
        if line == '' : break
        line = line.strip()
        if line == '': continue
        bits = line.split(':')
        regex = bits[0]
        text= ':'.join(bits[1:])
        print "%s: %s" % (regex, text)
        
        existing = Phrase.objects.filter(regex=regex, text=text)
        if len(existing) == 0: 
            t = Phrase(regex=regex, text=text)
            t.save()

        