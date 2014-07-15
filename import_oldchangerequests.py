# script to import old editor content for proposals
# Sam Pepler feb 2013

import getopt, sys
import os, errno, datetime

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

    editorxmlfilename = sys.argv[1]


    cflist = VocabList.objects.get(pk=1)

    # look at CF list xml from PCMDI site
    tree = ET.parse(editorxmlfilename)
    requests = tree.getroot()
 #   version = table.find('version_number').text

 #   cfversion = VocabListVersion(vocab_list=cflist, version=version) 
 #   cfversion.save()

    
    for request in requests.findall('ChangeRequest'):

        ID = request.find('ID').text
        ProposedDate = request.find('ProposedDate').text
        ProposedBy = request.find('ProposedBy').text
        ChangeType = request.find('ChangeType').text
        Comment = request.find('Comment')
        if Comment == None: Comment = ''
        else: Comment = Comment.text
        if Comment == None: Comment = ''
        mailThreadTitle = request.find('mailThreadTitle').text
        mailThreadUrl = request.find('mailThreadUrl').text
        CreatedDate = request.find('CreatedDate').text
        Status = request.find('Status').text
        records = request.find('Records')

        if ChangeType=='update term': alias = True
        else: alias = False

        if Status == 'Accepted': Status = 'accepted'
        elif Status == 'Completed': Status = 'complete'
        elif Status == 'Rejected': Status = 'rejected'
        elif Status == 'Under Discussion': Status = 'under discussion'

        if ProposedDate != None: ProposedDate = datetime.datetime.strptime(ProposedDate, '%Y/%m/%d')
        CreatedDate = datetime.datetime.strptime(CreatedDate, '%Y-%m-%dT%H:%M:%SZ')

        if mailThreadTitle == None: mailThreadTitle=''
        if mailThreadUrl == None: mailThreadUrl=''
        if ProposedBy == None: ProposedBy=''

        print ID, ProposedDate, ProposedBy, ChangeType, Status, Comment

        p = Proposal(created=CreatedDate, status=Status, proposer=ProposedBy, 
                     proposed_date=ProposedDate, comment=Comment, mail_list_url=mailThreadUrl,
                     mail_list_title=mailThreadTitle, vocab_list=cflist, alias=alias)
        p.save()

        for entry in records.findall('entry'):
            term_id = entry.get('id')
            canonical_units = entry.find('canonical_units')
            if canonical_units == None: canonical_units = ''
            else: canonical_units = canonical_units.text
            units_ref = entry.find('canonical_units_id')
            if units_ref == None: units_ref = ''
            else: units_ref = units_ref.text
            description = entry.find('description')
            if description == None: description = ''
            else: description = description.text
            grib = entry.find('grib')
            if grib == None: grib = ''
            else: grib = grib.text
            amip = entry.find('amip')
            if amip == None: amip = ''
            else: amip = amip.text
            # time of entry
            for e in entry:
                 for ee in e:
                    for eee in ee: 
                        entry_date = eee.text 
            print entry_date
            entry_date = datetime.datetime.strptime(entry_date, '%Y-%m-%dT%H:%M:%SZ')
            print entry_date
            
            print 'TERM:',term_id, canonical_units, units_ref, description, amip, grib, entry_date

            existing = Term.objects.filter(name=term_id, description=description, grib=grib, 
                                           amip=amip, unit=canonical_units)
            if len(existing) == 0: 
                print "no matching term"
                t = Term(name=term_id, description=description, grib=grib, 
                         amip=amip, unit=canonical_units, unit_ref=units_ref)
                t.save()
            else: 
                print "existing terms %s" % len(existing)
                for term in existing:
                    term.unit_ref=units_ref
                    term.save
                t = existing[0]

            #find an external id
            samename =  Term.objects.filter(name=term_id)
            if len(samename) >0: 
                t.externalid = samename[0].externalid
                t.save()
            
            pt = ProposedTerms(proposal=p, term=t)
            pt.save()
            pt.change_date=entry_date
            pt.save()

        # find which list the proposal was accepted onto
        current_term = p.current_term()
        print current_term
        versions =  VocabListVersion.objects.filter(terms=current_term).order_by('version')
        print versions
        print p.status
        if p.status == 'complete' and len(versions)>0:
            p.vocab_list_version = versions[0]
            p.save()

