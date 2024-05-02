
from django.urls import re_path 
from vocab.views import *
from django.contrib import admin
from django.views.generic.base import RedirectView

urlpatterns = [
     re_path(r'^admin/', admin.site.urls),
     re_path(r'^proposal/(?P<id>\d+)$', viewproposal),
     re_path(r'^proposal/(?P<id>\d+)/edit$', editproposal),
     re_path(r'^vocab/(?P<id>\d+)$', viewvocablist),
     re_path(r'^vocabversion/(?P<id>\d+)$', viewvocablistversion),     
     re_path(r'^vocabversion/(?P<id>\d+)/updateemail$', updateemail),
     re_path(r'^proposals/(?P<id>\d+)$', viewproposal_list),
     re_path(r'^newproposal/(?P<vocab_id>\d+)', newproposal),
     re_path(r'^bulkupload/(?P<vocab_id>\d+)', bulkupload),
     re_path(r'^scrapproposal/(?P<proposal_id>\d+)', scrapproposal),
     re_path(r'^term/(?P<id>\d+)', viewterm),
     re_path(r'^termhistory/(?P<id>\d+)', viewtermhistory),
     re_path(r'^phraselist/$', viewphraselist),
     re_path(r'^bulkupload_phrases', bulkupload_phrases),
     re_path(r'^health/$', health),     
     re_path(r'^$', RedirectView.as_view(url='/proposals/1', permanent=True), name='index')
	      
	      
	       ]

