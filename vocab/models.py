from django.db import models

import datetime
import random
import re
from django.utils.safestring import mark_safe

# make a convertion table for smart quotes etc.
intab =  b'\221\222\223\224\225\226\227\240'
outtab = b'\047\047\042\042\052\055\055\040'
convert_smart_quotes_table = bytes.maketrans(intab, outtab)


class Term(models.Model):
    # the vocab term. 
    externalid = models.CharField(max_length=256, blank=True, default='', help_text="machine readable id")
    name = models.CharField(max_length=1024, blank=True, default='', help_text="term text")
    description = models.CharField(max_length=4096, blank=True, default='', help_text="description of term")
    unit = models.CharField(max_length=256, blank=True, default='', help_text="unit")
    unit_ref = models.CharField(max_length=256, blank=True, default='', help_text="reference for unit")
    amip = models.CharField(max_length=256, blank=True, default='', help_text="amip name/number for term")
    grib = models.CharField(max_length=256, blank=True, default='', help_text="Grib name/number for term")

    def __str__(self):
        return "Term: %s" % (self.name,)

    def save(self, *args, **kwargs):
        # overload save to get ride of smart quotes
        if type(self.description) == str:
            self.description = self.description.translate(convert_smart_quotes_table)
        models.Model.save(self, *args, **kwargs)

    def phrases(self):
        pp = []
        for p in Phrase.objects.all():
            text = p.isMatch(self)
            if text != '': pp.append(text)
        return ' '.join(pp)    
    
    # Generate a new id for term
    def generate_term_id(self):    
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
        pid = ''
        cnt = 0
        while cnt < 8:
            pid += random.choice(chars)
            cnt += 1         
        return pid

    def gen_externalid(self):
        for i in range(100):
            pid = self.generate_term_id()
            matchs = Term.objects.filter(externalid=pid)         
            if len(matchs) == 0:
                self.externalid = pid
                self.save()
                return 
           
    def proposals(self):
        props = Proposal.objects.filter(terms=self)
        return props

    def proposals_links(self):
        props = self.proposals()
        out = ''
        for p in props:
            if p.proposer: out += '<a href="/proposal/%s/edit">%s (%s)</a> ' % (p.id,p.id,p.proposer)
            else: out += '<a href="/proposal/%s/edit">%s</a>' % (p.id,p.id)
        return mark_safe(out)

    def vocab_list_versions(self):
        vlvs = VocabListVersion.objects.filter(terms=self)
        return vlvs

    def with_same_name(self):
        terms = Term.objects.filter(name=self.name)
        return terms

    def aliases(self):
        aliases = Alias.objects.filter(termname=self.name)
        return aliases


class Alias(models.Model):
    # an alias in a vocab. It links an old term name to a current term.
    #   term = models.ForeignKey(Term, blank=True, null=True,help_text="Term on current list")
    name = models.CharField(max_length=1024, blank=True, default='', help_text="alias name")
    termname = models.CharField(max_length=1024, blank=True, default='', help_text="real term name")

    def __str__(self):
        return "%s -> %s" % (self.name, self.termname) 

    def externalid(self): 
        term = Term.objects.filter(name=self.name)
        return term[0].externalid


class VocabList(models.Model):
    # a vocab list. e.g. "CF". Vocab lists do not have terms themselves,  only vocab list versions have terms.
    name = models.CharField(max_length=256, blank=True, default='', help_text="title of vocab")

    def new_version(self):
        latest = self.latest_version()
        if latest == None: 
            # first version of list 
            newlist = VocabListVersion(vocab_list=self, version=1, status='Blank')
            newlist.save()
  
            return newlist
        else: 
            # make a copy of the last version
            newlist = VocabListVersion(vocab_list=self, version=latest.version+1, status='copied')
            newlist.save()
            for t in latest.terms.all():
                newlist.terms.add(t)
            #for a in latest.aliases.all():
            #    newlist.aliases.add(a)

            # mark previous list as complete
            latest.status = 'complete'
            latest.save()

            # add acceppted proposals
            newlist.compile_accepted()

        return newlist

    def revert(self):
        latest = self.latest_version()
        
        # reverse proposals 
        proposals = Proposal.objects.filter(vocab_list_version=latest)
        for p in proposals:
            p.revert()
            
        latest.delete()

        # mark the last list as reverted
        latest = self.latest_version()
        latest.status = 'reverted'
        latest.save()
            
    def versions(self):
        return VocabListVersion.objects.filter(vocab_list=self)

    def latest_version(self):    
        lists = VocabListVersion.objects.filter(vocab_list=self).order_by('-version')
        if len(lists) != 0: return lists[0]
        else: return None        
       
    def __str__(self):
        return "%s" % (self.name,) 


class VocabListVersion(models.Model):
    # a version of a vocab list. This has a set of terms and aliases.
    version = models.IntegerField(help_text="version number of vocab list") 
    published_date = models.DateField(auto_now_add=True, help_text="Date when list was published.")
    status = models.CharField(max_length=64, blank=True, default='Blank',
                              help_text="Status of list",
                              choices=(("Blank", "Blank"), ("copied", "copied"),
                                       ("Changed", "Changed"), ("Complete", "Complete"),
                                       ))
    # Blank  = unpopulated
    # populated = list has old names from masterlist
    # changed = added/updated accepted terms   
    # complete = ready for export
    terms = models.ManyToManyField(Term, blank=True)
    #aliases = models.ManyToManyField(Alias, blank=True)
    vocab_list = models.ForeignKey(VocabList, on_delete=models.CASCADE, blank=True, null=True,help_text="Vocab list for which this is a version")
 
    def compile_accepted(self):
        accepted_proposals = Proposal.objects.filter(vocab_list=self.vocab_list, status='accepted')
        for p in accepted_proposals:
            p.move_to_list(self)
        self.status = 'changed'
        self.save()

    def markascomplete(self):
        self.status = 'complete'
        self.save()        

    def termbyname(self,name): 
        terms = self.terms.filter(name=name)
        if len(terms)==0: return None
        else: return terms[0]

    def aliases(self): 
        vlv_aliases = []
        for t in self.terms.all():
            for a in Alias.objects.filter(termname=t.name):
                vlv_aliases.append(a)
        return vlv_aliases

    def __str__(self):
        return "%s (%s)" % (self.vocab_list, self.version) 

class Proposal(models.Model):
    # a proposal to change a term on a list. 
    created = models.DateField(auto_now_add=True, null=True, blank=True,
                               help_text="Date when proposal was created was published.")
    status = models.CharField(max_length=64, blank=True, default='New',
                              help_text="Status of request",
                              choices=(("new", "new"),
                                       ("under discussion", "under discussion"),
                                       ("rejected", "rejected"),
                                       ("complete", "complete"),
                                       ("accepted", "accepted")))
    proposer = models.CharField(max_length=1024, blank=True, default='', help_text="name of proposer")
    proposed_date = models.DateField(null=True, blank=True, help_text="Date when proposal was first made.")
    comment = models.TextField(max_length=2048, blank=True, null=True, default='', help_text="comment on proposal")
    mail_list_url = models.URLField(max_length=1024, blank=True, default='', null=True,
                                    help_text="URL of Mailing list thread")
    mail_list_title = models.CharField(max_length=256, blank=True, default='', null=True,
                                       help_text="title of mailing list thread")
    vocab_list = models.ForeignKey(VocabList, on_delete=models.CASCADE, blank=True, null=True,
                                   help_text="If the proposal is accepted the term will be added to a version of this list.")
    vocab_list_version = models.ForeignKey(VocabListVersion, on_delete=models.CASCADE, blank=True, null=True,
                                           help_text="After it was accepted the term was added to this version of the list.")
    terms = models.ManyToManyField(Term, blank=True, through='ProposedTerms')
    alias = models.BooleanField(default=False)

    def __str__(self):
        return "%s [%s]" % (self.proposer, self.mail_list_title[0:40]) 
    
    def current_term(self):
        if len(self.terms.all())==0: return None
        else: 
            pt = ProposedTerms.objects.filter(proposal=self).order_by('-change_date')[0]
            return pt.term

    def first_term(self):
        if len(self.terms.all())==0: return None
        else: 
            pt = ProposedTerms.objects.filter(proposal=self).order_by('change_date')[0]
            return pt.term

    def proposed_terms(self):
        prop_terms = []
        pts = ProposedTerms.objects.filter(proposal=self).order_by('change_date')
        for pt in pts: prop_terms.append((pt.term,pt.change_date))
        return prop_terms 

    def move_to_list(self, version):
        self.status = "complete"
        self.vocab_list_version = version
        current_term = self.current_term()
        first_term = self.first_term()
        term_name_change = (first_term.name != current_term.name)
        existing_term = version.termbyname(current_term.name)

        # 3 posibilies: 
        #    1) its a new record 
        #               - current term not on the list and alias flag on proposal set to false.
        #    2) its an old term, but the term name has not changed. 
        #               - find and update term info
        #    3) its an old term and the term name has changed.
        #               - insert a new term record.
        #               - remove old term from list
        #               - add an alias from old to new
        #               - add aliases from any old aliases to the new record 

        # new record
        if not self.alias and not existing_term:            
            current_term.gen_externalid()            
            version.terms.add(current_term)

        # old term with no change in term name
        elif existing_term and not term_name_change:
            version.terms.remove(existing_term)
            version.terms.add(current_term)
 
        # old term with a change in the term name
        elif self.alias and term_name_change:
            version.terms.add(current_term)
            version.terms.remove(first_term)
            current_term.gen_externalid()
            
            # make aliases for old term and old aliases to first term            
            alias = Alias(name=first_term.name, termname=current_term.name)
            alias.save()
            
            old_aliases = Alias.objects.filter(termname=first_term.name)
            for a in old_aliases: 
                alias = Alias(name=a.name, termname=current_term.name)
                alias.save()
          
        self.save()

    def updatetype(self):
        current_term = self.current_term()
        first_term = self.first_term()
        if first_term == None: return "New"
        term_name_change = (first_term.name != current_term.name)

        # 3 posibilies: 
        #    1) new - current term not on the list and alias flag on proposal set to false.
        #    2) updated - its an old term, but the term name has not changed. 
        #    3) term change - its an old term and the term name has changed.

        # new record
        if not self.alias: return "New"            
        # old term with no change in term name
        elif not term_name_change: return "Updated"  
        # old term with a change in the term name
        else: return "TermChange"          


    def skosupdate(self):
        # make update skos for NERC vocab server.
        current_term = self.current_term()
        first_term = self.first_term()
        term_name_change = (first_term.name != current_term.name)
        version = self.vocab_list_version

        # new record
        if not self.alias: 
            return """<skos:Concept><skos:externalID>%s</skos:externalID>
             <skos:prefLabel>%s</skos:prefLabel><skos:altLabel>null</skos:altLabel>
             <skos:definition>%s</skos:definition><skos:changeNote>I</skos:changeNote>
             <date xmlns="http://purl.org/dc/elements/1.1/">%s</date>
             </skos:Concept>""" %(current_term.externalid, current_term.name,
                                  current_term.description, datetime.date.today().isoformat())

        # old term with no change in term name
        elif not term_name_change:
            return """<skos:Concept><skos:externalID>%s</skos:externalID>
             <skos:prefLabel>%s</skos:prefLabel><skos:altLabel>null</skos:altLabel>
             <skos:definition>%s</skos:definition><skos:changeNote>M</skos:changeNote>
             <date xmlns="http://purl.org/dc/elements/1.1/">%s</date>
             </skos:Concept>""" %(current_term.externalid, current_term.name,
                                  current_term.description, datetime.date.today().isoformat())
 
        # old term with a change in the term name
        elif self.alias and term_name_change: 
            return """<skos:Concept><skos:externalID>%s</skos:externalID>
             <skos:prefLabel>%s</skos:prefLabel><skos:altLabel>null</skos:altLabel>
             <skos:definition>%s</skos:definition><skos:changeNote>D</skos:changeNote>
             <date xmlns="http://purl.org/dc/elements/1.1/">%s</date>
             </skos:Concept>
             <skos:Concept><skos:externalID>%s</skos:externalID>
             <skos:prefLabel>%s</skos:prefLabel><skos:altLabel>null</skos:altLabel>
             <skos:definition>%s</skos:definition><skos:changeNote>I</skos:changeNote>
             <date xmlns="http://purl.org/dc/elements/1.1/">%s</date>
             </skos:Concept>""" %(first_term.externalid, first_term.name,
                                  first_term.description, datetime.date.today().isoformat(),
                                  current_term.externalid,
                                  current_term.name, current_term.description, datetime.date.today().isoformat())

    def tsvupdate(self):
        # make update tsv for NERC vocab server.
        current_term = self.current_term()
        first_term = self.first_term()
        term_name_change = (first_term.name != current_term.name)
        version = self.vocab_list_version

        # new record
        if not self.alias:
            return "%s\t%s\t\t%s\tI\n" %(current_term.externalid, current_term.name,
                                         current_term.description)

        # old term with no change in term name
        elif not term_name_change:
            return "%s\t%s\t\t%s\tM\n" % (current_term.externalid, current_term.name,
                                          current_term.description)

        # old term with a change in the term name
        elif self.alias and term_name_change:
            return "%s\t%s\t\t%s\tD\n%s\t%s\t\t%s\tI\n" %(first_term.externalid, first_term.name,
                                                        first_term.description, current_term.externalid,
                                                        current_term.name, current_term.description)

    def csv_mapping_update(self):
        current_term = self.current_term()
        first_term = self.first_term()
        term_name_change = (first_term.name != current_term.name)
        unit_change = (first_term.unit_ref != current_term.unit_ref)
        output = ''

        # add alias mappings
        for a in current_term.aliases():
            output += "P07,%s,SYN,P07,%s,I\n" % (current_term.externalid, a.externalid())

        # add unit mappings
        if current_term.unit_ref:
            # new record or term changed
            if term_name_change or not self.alias:
                output += "P07,%s,MIN,P06,%s,I\n" % (current_term.externalid, current_term.unit_ref)
            # same term with unit change
            elif unit_change:
                if first_term.unit_ref:
                    output += "P07,%s,MIN,P06,%s,D\n" % (current_term.externalid, first_term.unit_ref)
                output += "P07,%s,MIN,P06,%s,I\n" % (current_term.externalid, current_term.unit_ref)

        return output

    def revert(self):
    
        # remove new aliases
        current_term = self.current_term()
        first_term = self.first_term()
        term_name_change = (first_term.name != current_term.name)
        # old term with a change in the term name 
        if self.alias and term_name_change:
            # find aliases for new term and delete them            
            new_aliases = Alias.objects.filter(termname=current_term.name)
            for a in new_aliases: 
                a.delete() 
    
        # reverse the move to list function. 
        # Assumes vocab list version that the proposals are completed to is removed.
        self.status = "accepted"
        self.vocab_list_version = None
        self.save()
        
    def scrap(self):
        # remove terms where not on a list
        pts = ProposedTerms.objects.filter(proposal=self).order_by('change_date')
        vlvs = VocabListVersion.objects.all()

        for pt in pts:
            term_on_list=False            
            for vlv in vlvs:
                terms = vlv.terms.filter(id=pt.term.id)
                if len(terms) != 0:
                    term_on_list=True
                    break
            if not term_on_list: 
                print("remove %s" % pt.term)
                pt.term.delete()

            # remove proposed terms links
            print("remove %s" % pt)
            pt.delete()  
            # remove proposal - self
        print("remove %s" % self)
        self.delete()            


class ProposedTerms(models.Model):
    change_date = models.DateTimeField(auto_now_add=True, help_text="Date the term was last changed.")
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, help_text="Link to Request that generated the term")
    term = models.ForeignKey(Term, on_delete=models.CASCADE, help_text="Link to the term")

    def __str__(self):
        return "Proposed term: %s" % (self.term,)


class Phrase(models.Model):
    regex = models.CharField(max_length=1024, blank=True, default='',
                             help_text="Regular expression to find text to replace")
    text = models.CharField(max_length=4096, blank=True, default='',
                            help_text="Text to replace in term description")

    def __str__(self):
        return "%s" % (self.text,)

    def save(self, *args, **kwargs):
        # overload save to get ride of smart quotes
        if type(self.text) == str:
            self.text = self.text.translate(convert_smart_quotes_table)
        models.Model.save(self, *args, **kwargs)

    def isMatch(self, term):
        """
        Test if the input string matches the regular expressions represented by the
        parser entry
        @param inputString: string to test the parser entry with 
        @return: True if the input string matches the parser entry, false otherwise
        """

        if type(term) == Term:
            term_text = term.name
        else:
            term_text = term

        regExpString = self.regex

        # firstly strip out any 'not' expressions
        notREs = []
        notRegexp = regExpString.split('&& !')        
        if len(notRegexp) > 1:
            notREs = notRegexp[1:]
            # NB, we assume that NOTs are placed at the end of the parser expressions
            regExpString = notRegexp[0]
            
        # now look for OR terms - NB, these are unlikely to be included alongside NOT terms
        orREs = []
        orRegexp = regExpString.split('||')        
        if len(orRegexp) > 1:
            orREs = orRegexp[1:]         
            # NB, we assume that AND regexps are placed at the start of the parser expressions
            regExpString = orRegexp[0]
        
        # lastly, load up any AND regexps
        andREs = []
        andRegexp = regExpString.split('&&')        
        if len(andRegexp) > 1:
            andREs = andRegexp
        elif orREs:
            # NB, be sure to catch cases like 'blah || blooh || bleh'
            orREs.insert(0, andRegexp[0])
        else:
            andREs = andRegexp

        for andRegexp in andREs:
            if not re.search(andRegexp.strip(), term_text):
                return ''

        if orREs:
            for orRegexp in orREs:
                if re.search(orRegexp.strip(), term_text):
                    return self.text
            return ''
        
        for notRegexp in notREs:
            if re.search(notRegexp.strip(), term_text):
                return ''

        return self.text      

