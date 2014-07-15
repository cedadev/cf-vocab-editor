'''
 Extend the standard vocab server client to include methods to submit updates
 to vocab server list data and track the progress of these
 
 @author: C Byrom, Tessella, Mar 09
'''
import logging, urllib
from xml.etree import ElementTree as ET
from ndg.common.src.clients.http.vocabserverclient import VocabServerClient
from ndg.common.src.models.codetablerecord import CodeTableRecord
import vocabtermeditor.model.changetype as ct
from vocabtermeditor.model.vocabterm import createVocabTermWithRecord
from vocabtermeditor.model.standardname import StandardName

#temporary fudge until BODC can handle associated terms via their editor - email to designated person in config
from ndg.common.src.lib.mailer import mailHandler

HTTP_400_ERROR_CODE_MESSAGE = "HTTP Error 400"
HTTP_401_ERROR_CODE_MESSAGE = "HTTP Error 401"
HTTP_500_ERROR_CODE_MESSAGE = "HTTP Error 500"

class UpdateVocabServerClient(VocabServerClient):
    
    INSERT_MODE = 'I'
    MODIFY_MODE = 'M'
    DEPRECATE_MODE = 'D'
    
    ASSOCIATED_ELEMENT_ATTRIBUTE_NAME = "associatedTerm"
    ASSOCIATED_ELEMENT_ATTRIBUTE_ELEMENT_NAME = "associatedTermElement"
    
    EDITOR_RETRY_ATTEMPTS = 5
    
    def __init__(self, 
                 path = "http://vocab.ndg.nerc.ac.uk/axis2/services/vocab/",
                 sessionPath = "https://vocab.ndg.nerc.ac.uk/session/",
                 updatePath = None,
                 proxyServer = None,
                 userID = None,
                 pw = None,
                 associatedTermsEmail = None,
                 mailServer = None
                 ):
        '''
        Constructor for vocab server client
        @keyword path: base path to the vocab service web services
        @keyword sessionPath: path to use to get a session ID for using the service
        @keyword updatePath: path to use when updating or creating new vocab terms in
        the vocab server 
        @keyword proxyServer: proxy server to use in comms
        @keyword userID: user ID to use for authentication with vocab server
        @keyword pw: password for user ID for authentication with vocab server    
        '''
        logging.info("Instantiating VocabServerClient")
        super(UpdateVocabServerClient, self).__init__(proxyServer = proxyServer,
                                                      path = path)
        self.sessionPath = sessionPath
        self.updatePath = updatePath
        self.userID = userID
        self.pw = pw
        
        #additional parameters for handling email
        self.associatedTermsEmail = associatedTermsEmail
        self.mailServer = mailServer
                
        logging.info("VocabServerClient instantiated")


    def __getSessionID(self):
        '''
        Use the authentication details to login and get a session ID for using with
        the service
        @return sessionID, following successful login, None otherwise
        '''
        logging.info("Getting session ID from vocab server")
        headersDict = {"email":self.userID, "password": self.pw}
        doc = self.readURL(self.sessionPath, headersDict = headersDict)
        
        # strip off text preface to the XML
        doc = doc.replace('securing web services', '')

        if not doc:
            # a failed login doesn't return anything
            logging.warning("Login to vocab server failed")
            return None
        
        et = ET.fromstring(doc)
        
        logging.info("- session ID retrieved - now returning")
        return et.findtext('sessionid')


    def updateList(self, vocabListURL, changeType, vocabTerms, multipleSessionID = None):
        '''
        Update the specified vocab list with the input vocab term data
        @param vocabListURL: url to the vocab list to update
        @param changeType: ChangeType representing the type of update to do 
        @param vocabTerms: list of VocabTerm or CodeTableRecord objects with 
        data to update in the list
        @raise ValueError: if invalid change type specified
        @return True, if successful, False otherwise
        '''
        logging.info("Updating vocab list, '%s'" %vocabListURL)
        
        sessionID = None
        
        if multipleSessionID is not None:
        	sessionID = multipleSessionID
        	logging.info("A sessionID has been supplied (%s)" %multipleSessionID)
        
      
        if not vocabTerms:
            logging.info("- no records to update - returning")
            return True
           
        
        if not isinstance(changeType, ct.ChangeType):
            changeType = ct.getChangeType(changeType)
            if not changeType:
                raise ValueError("changeType [%s] is not a ChangeType object" %changeType)
               
        
        if changeType.typeFlag & ct.NEW_TERM_FLAG:
            changeNote = self.INSERT_MODE
        elif changeType.typeFlag & ct.UPDATE_TERM_FLAG + ct.UPDATE_GLOBAL_FLAG:
            changeNote = self.MODIFY_MODE
        elif changeType.typeFlag & ct.DEPRECATE_TERM_FLAG:
            changeNote = self.DEPRECATE_MODE
        else:
            raise ValueError("Change type, '%s' not recognised by vocab server client" %changeType)

        # convert any CodeTableRecords to VocabTerms, if need be
        records = []
        for term in vocabTerms:
            if isinstance(term, CodeTableRecord):
                term = createVocabTermWithRecord(term)
            
            records.append(term)
            
        for term in records:
            term.changeNote = changeNote

        # NB for standard names data, we only want to update the vocab term stuff
        # - so use the super toET() method
        isSN = False
        if isinstance(term, StandardName):
            isSN = True

        if isSN:
            # ensure the mapping is done correctly
            records[0].definition = records[0].description
            records[0].prefLabel = records[0].id
            et = super(StandardName, records[0]).toET()
        else:
            et = records[0].toET()
            
            
        # now add any other elements to this elementtree
        # NB, the vocab terms come wrapped in an rdf element, whereas this service
        # expects vocab terms to be wrapped in Concept elements and then enclosed
        # in a single rdf element
        
        if len(records) > 1:
            for term in records[1:]:
                if isSN:
                    newET = super(StandardName, term).toET()
                else:
                    newET = term.toET()
                et.append(newET.getchildren()[0])

        if sessionID is None:
			logging.info("No sessionID supplied so generating one here...")
			sessionID = self.__getSessionID()
                
        if not sessionID:
        	raise IOError("Failed to retrieve session ID from vocab server")
        	return False
        
        #import pdb
        #pdb.set_trace()
           
        self.vocabRecords = records
        self.editorSession = sessionID

        # get the vocab list ID 
        listID = urllib.unquote(vocabListURL).split('/')[-2]
        url = "%s%s" %(self.updatePath, listID)
        
        # if this returns, it means things have been successful - no body is returned
        # - just an HTML 200 code - otherwise an IOError will be thrown
        # NB, only the first update of a particular term can be POSTed/day
        # - to overwrite this, we need to do a PUT instead - if the POST fails with
        # code 400, then retry with a PUT
        
        #UPDATED 16/03/11 : BODC editor sporadically fails with large numbers of updates - so must put in retry attempts to try and resubmit to prevent errors
        postAttempts = 0
        postAttemptSuccessfull = False
        postAttemptFundamentalError = False # use this to record an error OTHER than a 500 error
        
        logging.info("*************************************** Using sessionID: %s *************************************" %sessionID)
        
        #keep submitting until successfull or attempts is less than retry attempts
        while postAttempts < self.EDITOR_RETRY_ATTEMPTS:
			
			try:
				if postAttempts > 0:
					logging.info("RETRYING editor post attempt: %s" %str(postAttempts))
				
				doc = self.readURL(url, payload = ET.tostring(et), headersDict = {"sessionid": sessionID},
                               httpMethod = 'POST')
				logging.info("Update complete - NB, the process will be completed overnight on the vocab server(details: %s, %s, %s)" %(vocabTerms[-1].externalID,vocabTerms[-1].prefLabel,vocabTerms[-1].changeNote))
            
				postAttemptSuccessfull = True

			except IOError, e:
            
				if e.message.find(HTTP_400_ERROR_CODE_MESSAGE) > -1:
            	
					logging.error("- data has already been posted once today, retry as a PUT to overwrite this data (details: %s, %s, %s)" %(vocabTerms[-1].externalID,vocabTerms[-1].prefLabel,vocabTerms[-1].changeNote))
					doc = self.readURL(url, payload = ET.tostring(et),headersDict = {"sessionid": sessionID}, httpMethod = 'PUT')
					
					
					postAttemptFundamentalError = True
					
				#have we run out of sessions..
				elif e.message.find(HTTP_401_ERROR_CODE_MESSAGE) > -1:
				
					logging.info("Possible loss of session - need to try and get local sessionID.. (problem with that..)")
					logging.error("Error writing update term info to BODC vocab editor (%s)" %e.message)
					postAttempts += 1
					#headersDict = {"email":self.userID, "password": self.pw}
					#newSesh = self.readURL(self.sessionPath, headersDict = headersDict)

					#if not newSesh:
            		#	# a failed login doesn't return anything
					#	logging.warning("Login to vocab server failed")

					#else:
					#	et = ET.fromstring(newSess)        
						#sessionID =  et.findtext('sessionid')
					#	logging.info("- session ID retrieved (%s)- now returning" %sessionID)
					
				else:
            	
					#This is the error instance where we want to retry					
					logging.error ("(details: %s, %s, %s)" %(vocabTerms[-1].externalID,vocabTerms[-1].prefLabel,vocabTerms[-1].changeNote))
					logging.error("Error writing update term info to BODC vocab editor (%s)" %e.message)
					postAttempts += 1
			
			#cr@p python doesnt let you reassign booleans in a while if value is part of the evaluation in the statement... sigh.		
			if postAttemptSuccessfull or postAttemptFundamentalError:
				postAttempts = self.EDITOR_RETRY_ATTEMPTS + 10
            	
        if postAttempts >= self.EDITOR_RETRY_ATTEMPTS and not postAttemptSuccessfull:
        	logging.error("EXCEEDED Maximum number of BODC editor retry attempts")
            	
        if postAttemptSuccessfull:
        	return True
        else:
        	return False 
        
        
        