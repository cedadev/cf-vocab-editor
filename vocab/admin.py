from django.contrib import admin
#from django.contrib.gis import admin
from vocab.models import *
from django import forms



class ProposalAdmin(admin.ModelAdmin):
   list_display = ('proposer', 'status', 'vocab_list_version')
  # readonly_fields = ('status', 'vocab_list')
admin.site.register(Proposal, ProposalAdmin)

class TermAdmin(admin.ModelAdmin):
   list_display = ('name', 'unit',  'externalid', 'proposals_links' )
   search_fields = ('name', 'externalid',)
   list_filter = ('unit',)
admin.site.register(Term, TermAdmin)

class ProposedTermsAdmin(admin.ModelAdmin):
   list_display = ('term', 'change_date',  'proposal' )
admin.site.register(ProposedTerms, ProposedTermsAdmin)

class VocabListAdmin(admin.ModelAdmin):
   list_display = ('name',)
admin.site.register(VocabList, VocabListAdmin)

class AliasAdmin(admin.ModelAdmin):
   list_display = ('name','termname')
   search_fields = ('name','termname')
admin.site.register(Alias, AliasAdmin)

class VocabListVersionAdmin(admin.ModelAdmin):
   list_display = ('vocab_list', 'version',)
admin.site.register(VocabListVersion, VocabListVersionAdmin)


class PhraseAdminForm(forms.ModelForm):
    class Meta:
        model = Phrase
        widgets = {
            'text': forms.Textarea(attrs={'cols': 80, 'rows': 20}),
        }
	fields = {'regex', 'text'}

class PhraseAdmin(admin.ModelAdmin):
   form =PhraseAdminForm
   list_display = ('regex', 'text')
   search_fields = ('regex', 'text',)
admin.site.register(Phrase, PhraseAdmin)



