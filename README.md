# cf-vocab-editor
===============

Editor for CF vocab.

This is a tool that enables the sheparding of human conversations 
about new and updated CF parameter names, into machine readable form
for publication.

The human conversations happen currently as [github issues](https://github.com/cf-convention/vocabularies/issues). 

This tool, the vocab editor, is deployed as https://cfeditor.ceda.ac.uk

The basic workflow is each github issue converstation may result in one or more CF names to add or update.
Each name is added as a proposal to the editor. While under-discussion the names are updated, perhaps 
with several versions. The proposals are either accepted or eventually rejected. A new CF names list is 
constructed by adding all accepted proposals to the current list. The added names are either new terms, 
simple updates to the description or units, or changes to term names. In the later case an alias to 
the predicecor term is added to the list. 

The list can be exported in various ways. These are either files to feed the NVS or files to update the 
CF website.










