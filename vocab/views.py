from vocab.models import *
from django.shortcuts import redirect, render_to_response
from django.views.decorators import csrf
from django.template import RequestContext
from datetime import datetime
import urllib2
import re

def viewproposal_list(request, id):
    if request.user.is_authenticated(): user=request.user
    else: user = None

    # get status filter
    status = request.GET.get('status', None) 
    mailupdate = request.GET.get('mailupdate', None) 
    namefilter = request.GET.get('namefilter', None) 
    proposerfilter = request.GET.get('proposerfilter', None) 
    descfilter = request.GET.get('descfilter', None) 
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
               'descfilter':descfilter, 'unitfilter':unitfilter, 'yearfilter':yearfilter }
    return render_to_response('vocab/view_proposal_list.html', context)



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
    print term
    if term:
        term = Term.objects.get(pk=term)
        print term
        proposedterm = ProposedTerms(term=term, proposal=proposal)
        proposedterm.save()

    return redirect('/proposal/%s/edit' % proposal.pk)

def scrapproposal(request, proposal_id):
    proposal = Proposal.objects.get(pk=proposal_id)
    vocab = proposal.vocab_list
    if proposal.status == 'rejected' or proposal.status == 'new':
        proposal.scrap()
    return redirect('/proposals/%s' % vocab.pk)
    
   

def editproposal(request, id):
    if request.user.is_authenticated(): user=request.user
    else: user = None
 
    proposal = Proposal.objects.get(pk=id)
    # update proposal info
    status= request.POST.get('status', None)
    proposer = request.POST.get('proposer', None)
    proposed_date = request.POST.get('proposed_date', None)
    comment =  request.POST.get('comment', None)
    mail_list_url = request.POST.get('mail_list_url', None)
    mail_list_title = request.POST.get('mail_list_title', None) 

    if status: proposal.status = status
    if proposer: proposal.proposer = proposer.strip()
    if proposed_date: proposal.proposed_date = datetime.strptime(proposed_date, "%Y-%m-%d")
    if comment != None: proposal.comment = comment

    #try and get title from mail list 
    if mail_list_url and not mail_list_title:
        try: 
            f = urllib2.urlopen(mail_list_url)
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

    context = {'proposal': proposal, 'currentterm': current_term, 'phrases': phrases, 'vocab': proposal.vocab_list,
               'proposed_terms': proposal.proposed_terms(), 'user':user }
    # security thing for post requests...
    context.update(csrf(request))

    return render_to_response('vocab/proposal.html', context)

def viewproposal(request, id):
    if request.user.is_authenticated(): user=request.user
    else: user = None
 
    proposal = Proposal.objects.get(pk=id)
    context = {'proposal': proposal, 'vocab':proposal.vocab_list, 'proposed_terms':proposal.proposed_terms() }
    # security thing for post requests...
    context.update(csrf(request))

    return render_to_response('vocab/view_proposal.html', context)


def viewvocablist(request, id):
    if request.user.is_authenticated(): user=request.user
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
                
    context = RequestContext(request, {'vocab': vocab, 'newversion': newversion,
                                       'confirm': confirm, 'revert': revert, 'user': user})

    return render_to_response('vocab/vocab.html', context)

def viewvocablistversion(request, id):
    if request.user.is_authenticated(): user=request.user
    else: user = None

    vocabversion = VocabListVersion.objects.get(pk=id)
    xml = request.GET.get('xml', None)
    skos = request.GET.get('skos', None)
    units = request.GET.get('units', None)
    alias = request.GET.get('alias', None)
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
        response = render_to_response('vocab/vocabversionxml.xml', context)
        response['Content-Type'] = 'application/data'
        return response 
    if skos: 
        response =  render_to_response('vocab/vocabversionskosupdate.xml', context)
        response['Content-Type'] = 'application/data'
        return response 
    if units: 
        response =  render_to_response('vocab/vocabversionunitsupdate.txt', context)
        response['Content-Type'] = 'text/plain'
        return response 
    if alias: 
        response =  render_to_response('vocab/vocabversionaliasupdate.txt', context)
        response['Content-Type'] = 'text/plain'
        return response 
    if updateview: return render_to_response('vocab/vocabversionupdate.html', context)
    else:   return render_to_response('vocab/vocabversion.html', context)


def viewterm(request, id):
    term = Term.objects.get(pk=id)
    context = {'term': term, }
    return render_to_response('vocab/term.html', context)

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
    return render_to_response('vocab/termhistory.html', context)
    

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


