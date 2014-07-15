from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()
from vocab.views import *

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'vocabeditor.views.home', name='home'),
    # url(r'^vocabeditor/', include('vocabeditor.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
     url(r'^admin/', include(admin.site.urls)),
     url(r'^proposal/(?P<id>\d+)$', viewproposal),
     url(r'^proposal/(?P<id>\d+)/edit$', editproposal),
     url(r'^vocab/(?P<id>\d+)$', viewvocablist),
     url(r'^vocabversion/(?P<id>\d+)$', viewvocablistversion),
     url(r'^proposals/(?P<id>\d+)$', viewproposal_list),
     url(r'^newproposal/(?P<vocab_id>\d+)', newproposal),
     url(r'^scrapproposal/(?P<proposal_id>\d+)', scrapproposal),
     url(r'^term/(?P<id>\d+)', viewterm),
     url(r'^termhistory/(?P<id>\d+)', viewtermhistory),
)
