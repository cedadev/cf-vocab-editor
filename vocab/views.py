from vocab.models import *
from django.shortcuts import redirect, render, get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.template.context_processors import csrf
from datetime import datetime
from urllib.request import urlopen
import re
import csv
import io

def viewproposal_list(request, id):
    if request.user.is_authenticated: user=request.user
    else: user = None

    # get status filter
    status = request.GET.get('status', None) 
    mailupdate = request.GET.get('mailupdate', None) 
    namefilter = request.GET.get('namefilter', None) 
    proposerfilter = request.GET.get('proposerfilter', None) 
    descfilter = request.GET.get('descfilter', None) 
    commentfilter = request.GET.get('commentfilter', None)
    unitfilter = request.GET.get('unitfilter', None)
    yearfilter = request.GET.get('yearfilter', None) 
    vocab = VocabList.objects.get(pk=id)
    proposals = Proposal.objects.filter(vocab_list=vocab)

    if status == 'accepted': proposals = proposals.filter(status='accepted')
    elif status == 'complete': proposals = proposals.filter(status='complete')
    elif status == 'rejected': proposals = proposals.filter(status='rejected')
    elif status == 'new': proposals = proposals.filter(status='new')
    elif status == 'under discussion': proposals = proposals.filter(status='under discussion')
    elif status == 'all': pass
    elif status == 'inactive': proposals = proposals.exclude(status='new').exclude(status='under discussion').exclude(status='accepted')
    else: proposals = proposals.exclude(status='complete').exclude(status='rejected')

    proposals = proposals.order_by('-created', 'mail_list_title')

    # filter by term name
    if namefilter:
        namefilters = namefilter.split()
        filtered = []
        for p in proposals:
            if p.current_term():
                for nf in namefilters:
                    if p.current_term().name.find(nf) != -1: 
                        filtered.append(p)
                        break
        proposals = filtered
    
    # filter by proposer name
    if proposerfilter:
        proposerfilters = proposerfilter.split()
        filtered = []
        for p in proposals:
            if p.proposer:
                for pf in proposerfilters:
                    if p.proposer.lower().find(pf.lower()) != -1: 
                        filtered.append(p)
                        break
        proposals = filtered

    # filter by description
    if descfilter:
        descfilters = descfilter.split()
        filtered = []
        for p in proposals:
            if p.current_term():
                for df in descfilters:
                    if p.current_term().description.lower().find(df.lower()) != -1: 
                        filtered.append(p)
                        break
        proposals = filtered

    # filter by comment
    if commentfilter:
        commentfilters = commentfilter.split()
        filtered = []
        for p in proposals:
            if p.comment:
                for cf in commentfilters:
                    if p.comment.lower().find(cf.lower()) != -1:
                        filtered.append(p)
                        break
        proposals = filtered

   # filter by unit
    if unitfilter:
        filtered = []
        for p in proposals:
            if p.current_term():
                if p.current_term().unit.find(unitfilter) != -1: filtered.append(p)
        proposals = filtered

   # filter by proposal date
    if yearfilter:
        filtered = []
        for p in proposals:
            if p.proposed_date:
                if "%s" % p.proposed_date.year == yearfilter: filtered.append(p)
        proposals = filtered

    context = {'proposals': proposals, 'vocab': vocab, 'user':user, 'status':status, 
               'mailupdate':mailupdate, 'namefilter':namefilter, 'proposerfilter':proposerfilter,
               'descfilter':descfilter, 'unitfilter':unitfilter, 'yearfilter':yearfilter, 'commentfilter':commentfilter }
    return render(request, 'vocab/view_proposal_list.html', context)  



def newproposal(request, vocab_id):
    vocab = VocabList.objects.get(pk=vocab_id)
    #flag proposal as a change to an existing term. This means it needs an alias
    # for the old term
    alias= request.GET.get('alias', False)
    if alias: alias = True
    proposal = Proposal(status='new', vocab_list=vocab, alias=alias)
    proposal.save()

    # if existing term then add that
    term= request.GET.get('term', None)
    print (term)
    if term:
        term = Term.objects.get(pk=term)
        print (term)
        proposedterm = ProposedTerms(term=term, proposal=proposal)
        proposedterm.save()

    return redirect('/proposal/%s/edit' % proposal.pk)


def bulkupload(request, vocab_id):
    vocab = VocabList.objects.get(pk=vocab_id)
    context = {'vocab': vocab}
    context.update(csrf(request))

    # bulk upload from a csv file
    if 'upload' in request.FILES:
        upload = request.FILES['upload']
        print (dir(upload))
    else:
        return render(request, 'vocab/bulkupload_form.html', context)
    print ("+++", upload)

    # upload is deefined so run processing of upload
	
    with io.TextIOWrapper(request.FILES["upload"], encoding="utf-8", newline='\n') as text_file:
        reader = csv.reader(text_file)
 	
        message = ''
        header = True
        proposer = None
        proposed_date = None
        thread_url = None
        thread_title = None

        for row in reader:
            #message += ', '.join(row) + '\n'

            # blank line ends the proposal header
            # check we have proposer, proposed date, thread information
            if not row[0].strip() and header:
                header = False
                if not proposer:
                    message += "Error: No proposer set\n"
                if not proposed_date: message += "Error: No proposded date set\n"
                if not thread_url: message += "Error: No thread_url set\n"
                if not thread_title: message += "Error: No thread_title set\n"
                # if propsal info not full set then stop
                if not (proposer and proposed_date and thread_url and thread_title):
                    context.update({'message': message})
                    return render(request, 'vocab/bulkupload_output.txt', context=context, content_type='text/plain')
                else:
                    message += "Proposal Info\n=============\n"
                    message += "proposer: %s\n" % proposer
                    message += "proposed_date: %s\n" % proposed_date
                    message += "thread_url: %s\n" % thread_url
                    message += "thread_title: %s\n\n\n" % thread_title
                    message += "Adding names\n============\n"

            # read key value pairs for header
            if header:
                if row[0].strip() == 'proposer': proposer = row[1].strip()
                if row[0].strip() == 'proposed_date': proposed_date = row[1].strip()
                if row[0].strip() == 'thread_url': thread_url = row[1].strip()
                if row[0].strip() == 'thread_title': thread_title = row[1].strip()

            # name, unit, definition
            if not header:
                # skip blank lines
                if row[0].strip() == '':
                    continue
                # if there in only a name and not a unit then write and error and skip
                if len(row) > 1 and row[1] == '':
                    message += "Error: No unit for %s\n" % row[0]
                    continue
                if len(row) == 2:
                    termname, unit, unitref, definition = row[0].strip(), row[1].strip(), '', ''
                elif len(row) == 3:
                    termname, unit, unitref, definition = row[0].strip(), row[1].strip(), row[2].strip(), ''
                else:
                    termname, unit, unitref, definition = row[0].strip(), row[1].strip(), row[2].strip(), row[3].strip()

                # if the definition is 'GETDEF' then insert phases
                if definition == 'GETDEF':
                    definition = ''
                    for p in Phrase.objects.all():
                        text = p.isMatch(termname)
                        if text != '':
                            definition += " " + text

                # check not existing already - only new terms
                if len(Term.objects.filter(name=termname)) != 0:
                    message += "Error: can't make a duplicate %s\n" % termname
                    continue

                # add info to db
                try:
                    p = Proposal(status='new', proposer=proposer, proposed_date=proposed_date,
                                 comment='Created by bulk upload', mail_list_url=thread_url,
                                 mail_list_title=thread_title, vocab_list=vocab)
                    p.save()
                    t = Term(name=termname, description=definition, unit=unit, unit_ref=unitref)
                    t.save()
                    pt = ProposedTerms(proposal=p, term=t)
                    pt.save()
                except Exception as e:
                    print (e)
                    message += "Error: Could not make term and/or proposal objects in db. %s\n" % termname
                    continue

                message += "Success: Added %s\n" % termname

    context.update({'message': message})
    return render(request, 'vocab/bulkupload_output.txt', context=context, content_type='text/plain')

def bulkupload_phrases(request):
    context = {}
    context.update(csrf(request))

    # bulk upload from a csv file
    if 'upload' in request.FILES:
        upload = request.FILES['upload']
    else:
        return render(request, 'vocab/bulkupload_phrases_form.html', context)

    # upload is deefined so run processing of upload
    with io.TextIOWrapper(request.FILES["upload"], encoding="utf-8", newline='\n') as text_file:
        reader = csv.reader(text_file)
        message = ''

        for row in reader:
    
            # lines of form: regex, definition
            # skip blank lines
            if row[0].strip() == '':
                continue
            # if there in only a regex then skip.
            if len(row) > 1 and row[1] == '':
                message += "Error: No definition %s\n" % row[0]
                continue

            regex = row[0].strip()
            text = row[1].strip()

            # add info to db
            try:
                p = Phrase(regex=regex, text=text)
                p.save()
            except Exception as e:
                print(e)
                message += "Error: Could not make phrase objects in db. %s\n" % regex
                continue

            message += "Success: Added %s\n" % regex

    context.update({'message': message})
    return render(request, 'vocab/bulkupload_output.txt', context=context, content_type='text/plain')

def scrapproposal(request, proposal_id):
    proposal = Proposal.objects.get(pk=proposal_id)
    vocab = proposal.vocab_list
    if proposal.status == 'rejected' or proposal.status == 'new':
        proposal.scrap()
    return redirect('/proposals/%s' % vocab.pk)
    
   

def editproposal(request, id):
    if request.user.is_authenticated: user=request.user
    else: user = None
 
    proposal = Proposal.objects.get(pk=id)
    # update proposal info
    status= request.POST.get('status', None)
    proposer = request.POST.get('proposer', None)
    proposed_date = request.POST.get('proposed_date', None)
    comment = request.POST.get('comment', None)
    mail_list_url = request.POST.get('mail_list_url', None)
    mail_list_title = request.POST.get('mail_list_title', None) 

    if status: proposal.status = status
    if proposer: proposal.proposer = proposer.strip()
    if proposed_date: proposal.proposed_date = datetime.strptime(proposed_date, "%Y-%m-%d")
    if comment != None: proposal.comment = comment

    #try and get title from mail list 
    if mail_list_url and not mail_list_title:
        try: 
            f = urlopen(mail_list_url)
            page = f.read(500)
            m = re.search('<TITLE>(.*)', page)
            title = m.group(1)
            mail_list_title = title.strip()
        except:
            pass
  
    if mail_list_url: proposal.mail_list_url = mail_list_url.strip()
    if mail_list_title: proposal.mail_list_title = mail_list_title.strip()
    proposal.save()

    # find current term
    current_term = proposal.current_term()
    if current_term:
        (ct_name, ct_desc, ct_unit, ct_unit_ref, ct_amip, ct_grib, ct_externalid) = (current_term.name,
            current_term.description, current_term.unit, current_term.unit_ref, current_term.amip, 
            current_term.grib, current_term.externalid)
    else:
        (ct_name, ct_desc, ct_unit, ct_unit_ref, ct_amip, ct_grib, ct_externalid) = ('', '', '', '', '', '', '')

    # update new terms
    name = request.POST.get('name', None)
    if name: name = name.strip()
    description = request.POST.get('description', None)
    if description: description = description.strip()
    unit = request.POST.get('unit', None)
    if unit: unit=unit.strip()
    unit_ref = request.POST.get('unitref', None)
    amip = request.POST.get('amip', None)
    grib = request.POST.get('grib', None)
    if name: # if name is blank then don't make a new term
        if name==ct_name and description==ct_desc and unit==ct_unit and unit_ref==ct_unit_ref and amip==ct_amip and grib==ct_grib:
            # term is identical to exiting current term don't add another.
            pass
        elif name == ct_name:
            # if the term name has not changed then maintain the external id.
            newterm = Term(name=name, description=description, unit=unit, unit_ref=unit_ref, amip=amip, grib=grib, externalid=ct_externalid)
            newterm.save()
            proposedterm = ProposedTerms(term=newterm, proposal=proposal)
            proposedterm.save()
        else:    
            # new version of the term to add with new name  
            newterm = Term(name=name, description=description, unit=unit, unit_ref=unit_ref, amip=amip, grib=grib, externalid='')
            newterm.save()
            proposedterm = ProposedTerms(term=newterm, proposal=proposal)
            proposedterm.save()
        
    # phrase match
    current_term = proposal.current_term()
    if current_term: phrases = current_term.phrases()
    else: phrases = 'Not term to match yet!'     

    context = {'proposal': proposal, 'currentterm':current_term, 'phrases': phrases, 'vocab': proposal.vocab_list,
               'proposed_terms': proposal.proposed_terms(), 'user': user}
    # security thing for post requests...
    context.update(csrf(request))

    return render(request, 'vocab/proposal.html', context)  

def viewproposal(request, id):
    if request.user.is_authenticated:
        user = request.user
    else:
        user = None
 
    proposal = Proposal.objects.get(pk=id)
    context = {'proposal': proposal, 'vocab':proposal.vocab_list, 'proposed_terms':proposal.proposed_terms() }
    # security thing for post requests...
    context.update(csrf(request))

    return render(request, 'vocab/view_proposal.html', context )  


def viewvocablist(request, id):
    if request.user.is_authenticated: user=request.user
    else: user = None
 
    vocab = VocabList.objects.get(pk=id)

    # update new terms
    newversion = request.GET.get('newversion', None)
    revert = request.GET.get('revert', None)
    confirm = request.GET.get('confirm', None)
    if newversion and confirm: 
        vocab.new_version()
    if revert and confirm: 
        vocab.revert()
                
    context = {'vocab': vocab, 'newversion':newversion, 
               'confirm':confirm, 'revert':revert, 'user':user }
    # security thing for post requests...
    context.update(csrf(request))

    return render(request, 'vocab/vocab.html', context)  

def viewvocablistversion(request, id):
    if request.user.is_authenticated: user=request.user
    else: user = None

    vocabversion = VocabListVersion.objects.get(pk=id)
    xml = request.GET.get('xml', None)
    skos = request.GET.get('skos', None)
    tsv = request.GET.get('tsv', None)
    units = request.GET.get('units', None)
    updateview = request.GET.get('updateview', None)
    
    terms =  vocabversion.terms.all().order_by('name')
    for t in terms:
        aliases = t.aliases()   

    proposals = Proposal.objects.filter(vocab_list_version=vocabversion)
      
    context = {'vocabversion': vocabversion, 'terms':terms, 'user':user, 
               'vocab':vocabversion.vocab_list, 'proposals':proposals}
    # security thing for post requests...
    context.update(csrf(request))

    if xml:
        response =  render(request, 'vocab/vocabversionxml.xml', context)
        response['Content-Type'] = 'application/data'
        return response 
    if skos: 
        response =  render(request, 'vocab/vocabversionskosupdate.xml', context)
        response['Content-Type'] = 'application/data'
        return response 
    if tsv:
        response = render(request, 'vocab/vocabversiontsvupdate.txt', context)
        response['Content-Type'] = 'text/plain'
        return response
    if units:
        response =  render(request, 'vocab/vocabversionunitsupdate.txt', context)
        response['Content-Type'] = 'text/plain'
        return response 
    if updateview: return render(request, 'vocab/vocabversionupdate.html', context)
    else:   return render(request, 'vocab/vocabversion.html', context)  

def updateemail(request, id):
    if request.user.is_authenticated: user=request.user
    else: user = None

    vocabversion = VocabListVersion.objects.get(pk=id)
    
    terms =  vocabversion.terms.all().order_by('name')

    proposals = Proposal.objects.filter(vocab_list_version=vocabversion)
    
    
    new, updated, contribs, aliases = [], [], [], []
    for p in proposals:
        proptype = p.updatetype()
        if p.proposer not in contribs: contribs.append(p.proposer)

        if proptype == "New": 
            new.append(p.current_term().name) 
        elif proptype == "Updated": 
            updated.append(p.current_term().name) 
        elif proptype == "TermChange": 
            updated.append(p.current_term().name)
            for a in p.current_term().aliases(): aliases.append(a)
      
    new.sort()
    updated.sort()  
    context = {'vocabversion': vocabversion, 'proposals':proposals, 'new':new, 
               'updated':updated, 'contrib':contribs, 
               'aliases':aliases }
    # security thing for post requests...
    context.update(csrf(request))

    response =  render(request, 'vocab/updateemail.txt', context)
    response['Content-Type'] = 'text/plain'
    return response 


def viewterm(request, id):
    term = Term.objects.get(pk=id)
    context = {'term': term, }
    return render(request, 'vocab/term.html', context)  

def viewtermhistory(request, id):
    term = Term.objects.get(pk=id)
    
    hasaliasterms = []    
    for a in term.aliases(): 
        aliasterms = Term.objects.filter(name=a.name)
        for at in aliasterms: 
            if at not in hasaliasterms: hasaliasterms.append(at)
    
    isaliasedterms = []
    for a in Alias.objects.filter(name=term.name):
        if a.term not in isaliasedterms: 
            isaliasedterms.append(a.term)
        
         
 
    context = {'term': term, 'hasaliasterms': hasaliasterms, 'isaliasedterms':isaliasedterms}
    return render(request, 'vocab/termhistory.html', context)  
    
def viewphraselist(request):
    phrases = Phrase.objects.all().order_by('regex')
    context = {'phrases': phrases}
    return render(request, 'vocab/view_phrase_list.html', context)


def health(request):
    return render(request, 'vocab/health.html')


#def viewvocablistversiondiff(request, id):
# 
#    vocabversion = VocabListVersion.objects.get(pk=id)
#    vocabversionprev = VocabListVersion.objects.filter(vocab_list=vocabversion.vocab_list, version=vocabversion.version-1)
#    if len(vocabversionprev) == 0: vocabversionprev=None
#    else: vocabversionprev= vocabversionprev[0]
#
#    newterms = []
#    deletedterms = []
#    changedterms = []
#
#    for t in vocabversion.terms.all():
#    context = {'vocab': vocabversion, }
#    # security thing for post requests...
#    context.update(csrf(request))
# 
#    print xml
#    if xml: return render_to_response('vocabversionxml.html', context)  
#    else:   return render_to_response('vocabversion.html', context)  
#


