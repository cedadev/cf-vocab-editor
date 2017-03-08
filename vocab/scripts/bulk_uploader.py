# script to bulk upload terms from a CSV file.
#  The file has to have a header with proposal details and a body listing the 
#  term names, units and definitions. A blanke line signals the end of the header. 
#  Like this:
#
#proposer,Sam,
#proposed_date,2014-01-20,
#thread_url,http://badc.nerc.ac.uk,
#thread_title,test thread,
#,,
#,,
#test_bulk_term1,m,
#test_bulk_term2,C,
#test_bulk_term3,m3,
#test_bulk_term4,m3 tt,
#test_bulk_term5,ff,"def 5, 'quote' - A prob"""
#test_bulk_term6,m3 tt,def 6
#test_bulk_term7,m3 tt,
#test_bulk_term8,m3 tt,
#test_bulk_term9,m3 tt,
#
# Sam Pepler 2014

import getopt, sys
import os, errno

from django.core.management import setup_environ
import settings
setup_environ(settings)

from vocab.models import *
import csv, datetime


header = True
proposer = None
proposed_date = None
thread_url = None
thread_title = None

if __name__=="__main__":

    bulkuploadfilename = sys.argv[1]
    CSV = open(bulkuploadfilename, 'rb')
    reader = csv.reader(CSV)
    for row in reader:
        print ', '.join(row)

        cflist = VocabList.objects.get(pk=1)

        # blank line ends the proposal header
        # check we have proposer, proposed date, thread information
        if not row[0].strip(): 
            print "End of header"
            header = False
            if not proposer: raise Exception("No proposer set")  
            if not proposed_date: raise Exception("No proposded date set")  
            if not thread_url: raise Exception("No thread_url set")  
            if not thread_title: raise Exception("No thread_title set")  

        # read key value pairs for header
        if header:
            if row[0].strip() == 'proposer': proposer = row[1].strip()
            if row[0].strip() == 'proposed_date': proposed_date = row[1].strip()
            if row[0].strip() == 'thread_url': thread_url = row[1].strip()
            if row[0].strip() == 'thread_title': thread_title = row[1].strip()

        # name, unit, definition
        if not header:
            if row[0].strip() == '': continue
            termname = row[0].strip()
            unit = row[1].strip()
            definition = row[2].strip()


            p = Proposal(status='new', proposer = proposer, proposed_date=proposed_date, 
                     comment='Created by bulk upload', mail_list_url=thread_url, 
                     mail_list_title=thread_title, vocab_list=cflist)
            p.save()
            t = Term(name=termname, description=definition, unit=unit)
            t.save()
            pt = ProposedTerms(proposal = p, term = t)
            pt.save()




 

