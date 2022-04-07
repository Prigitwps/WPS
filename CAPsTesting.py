# CAPs Assessment functional sanity testing harness for OES 1.0
# Requirements: Selenium and Chrome Drivers
# Selenium Driver: https://www.selenium.dev/downloads/
# Chrome Driver: https://chromedriver.chromium.org/downloads
# Usage: python CAPsTesting.py [-h] [-r] [-e]
# Arguments:
# -h, --headless: Specifies headless or display mode for browser (default False)
# -r, --random:   Specifies random or set response mode for assessment (default False)
# -e, --env:      Specifies the environment to login and perform actions (default "uat")




import sys
from oesPractitioner import *
from oesRespondent import *
from dateutil.relativedelta import *
from datetime import date
import getopt
import os

if __name__ == "__main__":
    
    short_options = "he:r"
    long_options = ["headless", "env=", "random"]
    # "output=",
    
    # Get full command-line arguments
    full_cmd_arguments = sys.argv
    argument_list = full_cmd_arguments[1:]

    env = "uat"
    headless = False
    random = False
    
    try:
        arguments, values = getopt.getopt(argument_list, short_options, long_options)
    except getopt.error as err:
        # Output error, and return with an error code
        print (str(err))
        sys.exit(2)
    
    for current_argument, current_value in arguments:
        if current_argument in ("-h", "--headless"):
            headless = True
            if headless:
                loggingPrint("Running in headless mode")
        elif current_argument in ("-e", "--env"):
            env = current_value
        elif current_argument in ("-r", "--random"):
            random = True
            loggingPrint("Running in random response mode")
            #print (("Enabling special output mode (%s)") % (current_value))
    
    if headless:
        loggingPrint("Running in headless mode")
    else:
        loggingPrint("Running in display mode")
    
    if random:
        loggingPrint("Running in random responde mode")
    else:
        loggingPrint("Running in set response mode")
    
    if env=="staging":
        loginUrl = "https://platform.stage.wpspublish.com"
    elif env=="uat":
        loginUrl = "https://practitioner-uat.wpspublish.io"
    elif env=="qa":
        loginUrl = "https://practitioner-qa.wpspublish.io"
    elif env=="prod":
        loginUrl = "https://platform.wpspublish.com"
    
    try:
        capsPrac = oesPractitioner(loginUrl)
        capsPrac.headless = headless
        capsPrac.download_dir = str(os.getcwd())
        capsPrac.setUp()
        capsPrac.login()
        
        today = date.today()
        dob = today+relativedelta(years=-9, months=-3, days=-16)
        
        capsPrac.createNewClient(
        clientFirstName='Johnny',
        clientLastName='Sample',
        clientMonth=str(dob.month), 
        clientDay=str(dob.day), 
        clientYear=str(dob.year)
        )
        
        capsPrac.administerAssessment(assessmentType="caps")
        capsPrac.switchToRespondent()
        
        capsResp = oesRespondent(capsPrac.browser, "caps")
        
        
        capsResp.navigateToQuestions(
        examinerName="Mrs. Smith", 
        examinerTitle="School Psychologist",
        clientGrade="6",
        clientSchool="Test School"
        )
        
        if random:
            capsResp.completeAssessmentRandomly()
        else:
            # Instrumental Performance Appraisal section
            capsResp.answerQuestionsInSection(questionResponses=[2,1,2,0,0,2,1,0])
            capsResp.nextPage()
            
            # Social Context Appraisal section
            capsResp.answerQuestionsInSection(questionResponses=[1,2,0,3,2,0,1,1])
            capsResp.nextPage()
            
            # Paralinguistic Decoding section
            capsResp.answerQuestionsInSection(questionResponses=[0,1,2,0,0,0,3,1])
            capsResp.nextPage()
            
            # Instrumental Performance section
            capsResp.answerQuestionsInSection(questionResponses=[1,1,1,0,0,0,1,2])
            capsResp.nextPage()
            
            # Affective Expression section
            capsResp.answerQuestionsInSection(questionResponses=["skip",1,"skip","skip","skip","skip","skip","skip"])
            capsResp.nextPage()
            
            # Paralinguistic Signals section
            capsResp.answerQuestionsInSection(questionResponses=[0,1,1,0,1,0,"skip","skip",0])
            
        capsResp.submit()
        
        capsPrac.switchToPractitioner()
        capsPrac.browser.refresh()
        
        try:
            capsPrac.selectCompleteForm(1)
            capsPrac.validateForm()
            capsPrac.scoreForm()
        except:
            loggingPrint("Validation and scoring failed!!!")
            
        capsPrac.deleteClient("Johnny Sample")
        capsPrac.logout()
        capsPrac.tearDown()
        
    except Exception as err:
        loggingPrint(sys.exc_info()[2])
        capsPrac.tearDown()
        raise
    
    loggingPrint("Test completed!\r\n")