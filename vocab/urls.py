
from django.conf.urls import url
from vocab.views import *
from django.contrib import admin

urlpatterns = [
     url(r'^admin/', admin.site.urls),
     url(r'^proposal/(?P<id>\d+)$', viewproposal),
     url(r'^proposal/(?P<id>\d+)/edit$', editproposal),
     url(r'^vocab/(?P<id>\d+)$', viewvocablist),
     url(r'^vocabversion/(?P<id>\d+)$', viewvocablistversion),     
     url(r'^vocabversion/(?P<id>\d+)/updateemail$', updateemail),
     url(r'^proposals/(?P<id>\d+)$', viewproposal_list),
     url(r'^newproposal/(?P<vocab_id>\d+)', newproposal),
     url(r'^scrapproposal/(?P<proposal_id>\d+)', scrapproposal),
     url(r'^term/(?P<id>\d+)', viewterm),
     url(r'^termhistory/(?P<id>\d+)', viewtermhistory),
     url(r'^phraselist/$', viewphraselist),
               ]

