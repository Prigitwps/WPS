# General Assessment functional sanity testing harness for OES 1.0
# Requirements: Selenium and Chrome Drivers
# Selenium Driver: https://www.selenium.dev/downloads/
# Chrome Driver: https://chromedriver.chromium.org/downloads
# The chardet and dateutil libraries for Python 3
# Usage: python testHarness.py [-h] [-r] [-e] [-d] [-i] [-l]
# Arguments:
# -h, --headless:       Specifies headless or display mode for browser (default False)
# -r, --random:         Specifies random or set response mode for assessment (default False)
# -e, --env:            Specifies the environment to login and perform actions (default "uat")
# -d, --directory:      Specifies the directory to save any downloaded PDFs (default current working directory)
# -i, --input:          Specifies the path to the input CSV file used for issuing values and commands (default none)
# -l, --log-to-file:    Specifies whether to log to the terminal output or to a text file in --directory (default False)

import sys
from oesLibrary import *
from dateutil.relativedelta import *
from datetime import date
import getopt, csv, os, re, chardet
import pprint
import boto3, json
from contextlib import redirect_stdout, redirect_stderr

    
def runTestHarness(env="uat", headless=False, random=False, directory=None, input=None, logToFile=False):
# def runTestHarness(env="uat", headless=False, random=False, directory=None, input=None, logToFile=False, waitTime=None):
    if directory is None:
        directory = str(os.getcwd())
    
    if logToFile:
        with open(os.path.join(str(directory), os.path.splitext(os.path.basename(str(input)))[0] + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".txt"), 'w') as f:
            with redirect_stdout(f), redirect_stderr(f):
                # runTest(env=env, headless=headless, random=random, directory=directory, input=input, waitTime=waitTime)
                runTest(env=env, headless=headless, random=random, directory=directory, input=input)
    else:
        runTest(env=env, headless=headless, random=random, directory=directory, input=input)
    

def runTest(env="uat", headless=False, random=False, directory=None, input=None):
# def runTest(env="uat", headless=False, random=False, directory=None, input=None, waitTime=None):
    if headless:
        loggingPrint("Running in headless mode")
    else:
        loggingPrint("Running in display mode")
    
    if random:
        loggingPrint("Running in random response mode")
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
    elif env=="dev":
        loginUrl = "https://practitioner-dev.wpspublish.io"
    else:
        loginUrl = env
        
    testInfo = {}
    argsListAssessment = []
    argsListValidation = []
    questionList = {}
    
    loggingPrint("Input value: " + str(input))
    
    try:
        with open(str(input), 'rb') as rawdata:
            result = chardet.detect(rawdata.read(10000))
            encode=str(result['encoding'])
        
        loggingPrint("Input file confirmed as " + encode + " encoding")
        
        with open(str(input), encoding=encode) as csvfile:
            inputCsv = csv.reader(csvfile)
            inputInfo = enumerate(inputCsv)
            for row in inputInfo:
                key = str(row[1][0]).lower()
                val = row[1][1:]
                if key == 'assessmentforminfo':
                    argsListAssessment.append([str(val[0]), str(val[1])])
                    val = argsListAssessment
                elif key == 'validationforminfo':
                    argsListValidation.append([str(val[0]), str(val[1])])
                    val = argsListValidation
                elif key == 'section':
                #elif re.compile("^q[0-9]+$").match(key):
                    try:
                        questionList[val[0]]
                    except:
                        questionList[val[0]] = {}
                    question = {}
                    response = []
                    for i in val[2:]:
                        if i is not None and i != '':
                            response.append(i)
                    question[str(val[1]).lower()] = response
                    questionList[val[0]].update(question)
                else:
                    val = val[0]
                    if str(val).lower() == 'true':
                        val = True
                    if str(val).lower() == 'false':
                        val = False
                    else:
                        testInfo[key] = val
    except:
        loggingPrint("No input file or invalid input file provided!")
            
    try:
        try:
            username = testInfo['username']
            if username == '':
                username = None
        except:
            username = None
        
        try:
            password = testInfo['password']
            if password == '':
                password = None
        except:
            password = None
        
        capsPrac = oesPractitioner(loginUrl, username=username, password=password)
        capsPrac.headless = headless
        if directory is None:
            capsPrac.download_dir = str(os.getcwd())
        else:
            capsPrac.download_dir = str(directory)
        
        capsPrac.setUp()
        capsPrac.login()
        
        try:
            if (testInfo['clientageyears'] is not None and testInfo['clientageyears'] != '') or (testInfo['clientagemonths'] is not None and testInfo['clientagemonths'] != '') or (testInfo['clientagedays'] is not None and testInfo['clientagedays'] != ''):
                try:
                    if testInfo['clientageyears'] != '':
                        clientYear = re.sub('[^0-9]+', '', testInfo['clientageyears'])
                    else:
                        clientYear = 0
                except:
                    clientYear = 0
                
                try:
                    if testInfo['clientagemonths'] != '':
                        clientMonth = re.sub('[^0-9]+', '', testInfo['clientagemonths'])
                    else:
                        clientMonth = 0
                except:
                    clientMonth = 0
                
                try:
                    if testInfo['clientagedays'] != '':
                        clientDay = re.sub('[^0-9]+', '', testInfo['clientagedays'])
                    else:
                        clientDay = 0
                except:
                    clientDay = 0
                
                today = date.today()
                dob = today+relativedelta(years=-int(clientYear), months=-int(clientMonth), days=-int(clientDay))
                clientYear = str(dob.year)
                clientMonth = str(dob.month)
                clientDay = str(dob.day)
            else:
                clientYear = None
                clientMonth = None
                clientDay = None
        except:
            clientYear = None
            clientMonth = None
            clientDay = None
        
        try:
            if testInfo['clientfirstname'] != '':
                clientFirstName = testInfo['clientfirstname']
            else:
                clientFirstName = randomString()
        except:
            clientFirstName = randomString()
            
        try:
            if testInfo['clientlastname'] != '':
                clientLastName = testInfo['clientlastname']
            else:
                clientLastName = randomString()
        except:
            clientLastName = randomString()
        
        try:
            if testInfo['clientcaseid'] != '':
                clientCaseID = testInfo['clientcaseid']
            else:
                clientCaseID = None
        except:
            clientCaseID = None
        
        try:
            if testInfo['clientgender'] != '':
                clientGender = (testInfo['clientgender'][0]).upper() + (testInfo['clientgender'][1:]).lower()
                if clientGender not in ["Female", "Male"]:
                    print("Invalid client gender option provided! Using random instead")
                    clientGender = None
            else:
                clientGender = None
        except:
            clientGender = None
            
        try:
            if testInfo['clientemail'] != '':
                regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
                if(re.search(regex, testInfo['clientemail'])):  
                    clientEmail = testInfo['clientemail']
                else:  
                    print("Invalid client email provided! Using random instead")
                    clientEmail = None
            else:
                clientEmail = None
        except:
            clientEmail = None
            
        capsPrac.createNewClient(
        clientFirstName=clientFirstName,
        clientLastName=clientLastName,
        clientMonth=clientMonth, 
        clientDay=clientDay, 
        clientYear=clientYear,
        clientCaseID=clientCaseID,
        clientEmail=clientEmail,
        clientGender=clientGender
        )
        
        try:
            assessmentType = str(re.sub('[^0-9a-zA-Z]+', ' ', testInfo['assessmenttype'])).lower()
            if assessmentType != '':
                if assessmentType not in ['dp3', 'abas3', 'spm', 'spmp', 'ppascale', 'srs2', 'smalsi', 'casl2', 'opus', 'scq', 'arizona4', 'rcmas2', 'dbc2', 'piersharris3', 'rise', 'caps', 'dp4']:
                    print("Invalid assessment type provided! Using random instead")
                    assessmentType = None
            else:
                assessmentType = None
        except:
            assessmentType = None
        loggingPrint("Assessment type has been specified as " + str(assessmentType))        
        
        try:
            assessmentForm = testInfo['assessmentform']
            if assessmentForm == '':
                assessmentForm = None
        except:
            assessmentForm = None
            
        try:
            respondentName = testInfo['respondentname']
            if respondentName == '':
                respondentName = None
        except:
            respondentName = None
        
        
        capsPrac.administerAssessment(assessmentType=assessmentType, assessmentForm=assessmentForm, respondentName=respondentName)
        capsPrac.switchToRespondent()
        
        if assessmentType is None:
            capsResp = oesRespondent(capsPrac.browser)
        else:
            capsResp = oesRespondent(capsPrac.browser, assessmentType, capsPrac.scoreOnly)
        
        loggingPrint("Populating assessment form fields: " + str(argsListAssessment))
        capsResp.navigateToQuestions(argsList=argsListAssessment)
        
        try:
            waitTime = testInfo['waittime']
            if waitTime == '':
                waitTime = 0.2
        except:
            waitTime = 0.2
        
        if random:
            capsResp.completeAssessmentRandomly(waitTime=float(waitTime))
        else:
            if capsResp.singleView:
                submitFound = False
                
                while not submitFound:
                    section = capsResp.getCurrentSection()
                    try:
                        qNum = int(capsResp.browser.execute_script("return singleSectionList[sectionCounter].ItemAndResponseList[sectionItemCounter].ItemNo;"))
                    except:
                        qNum = 0
                        
                    if qNum > 0:
                        sectionQuestions = questionList[section]
                        try:
                            questionResponseVals = questionList[section][str('q' + str(qNum))]
                            for questionResponseVal in questionResponseVals:
                                loggingPrint("Answering question number " + str(qNum) + " in section " + str(section) + " with response of " + str(questionResponseVal))
                                if str(questionResponseVal).lower() not in ["skip", "randomanswer"]:
                                    capsResp.answerQuestion(questionNumber=qNum, questionResponse=str(questionResponseVal))
                                    time.sleep(float(waitTime))
                                elif questionResponseVal == "randomAnswer":
                                    capsResp.answerQuestion(questionNumber=qNum)
                                    time.sleep(float(waitTime))
                        except:
                            loggingPrint("Question/response is missing or invalid; answering question randomly instead!")
                            capsResp.answerQuestion(questionNumber=qNum)
                            time.sleep(float(waitTime))

                    try:
                        pageNavButton = capsResp.getPageNavButton("next")
                        if pageNavButton.get_attribute("value") in capsResp.submitTranslations:
                            loggingPrint("Submit button found! Disregarding any remaining responses...")
                            submitFound = True
                        else:
                            loggingPrint("Navigating to next page...")
                            capsResp.nextPage()
                    except:
                        if capsPrac.scoreOnly:
                            loggingPrint("Reached end of assessment! Disregarding any remaining responses...")
                            submitFound = True
                        else:
                            loggingPrint("Error checking assessment form navigation; may not have loaded correctly!")

            else:
                for b in questionList.keys(): 
                    section = capsResp.getCurrentSection()
                    loggingPrint("Answering questions in section: " + str(section))
                    newPath = ''
                    for x in section.split():
                        newPath = newPath + " and contains(text(), '" + x + "')"
                    WebDriverWait(capsResp.browser, 10).until(EC.presence_of_element_located((By.XPATH, "//*//*[contains(@class, 'sectionName')" + newPath + "]")))
                    
                    questions = sorted({int(k[1:]):v for k,v in questionList[section].items() if any (regex_match(k) for regex_match in [re.compile("^q[0-9]+$").match])}.keys())
                    q = 0
                    # submitFound = False
                    
                    while q < len(questions):
                        numQuestions = len(capsResp.getQuestionsInPage())
                        loggingPrint("Number of questions in page: " + str(numQuestions))
                        if int(numQuestions) > 0:
                            for i in range(1, numQuestions+1):
                                q += 1
                                try:
                                    questionResponseVals = questionList[section][str('q' + str(questions[q-1]))]
                                    for questionResponseVal in questionResponseVals:
                                        loggingPrint("Answering question number " + str(q) + " with response of " + str(questionResponseVal))
                                        if str(questionResponseVal).lower() not in ["skip", "randomanswer"]:
                                            capsResp.answerQuestion(questionNumber=i, questionResponse=str(questionResponseVal))
                                            time.sleep(float(waitTime))
                                        elif questionResponseVal == "randomAnswer":
                                            capsResp.answerQuestion(questionNumber=i)
                                            time.sleep(float(waitTime))
                                except:
                                    loggingPrint("Question/response is missing or invalid; answering question randomly instead!")
                                    capsResp.answerQuestion(questionNumber=i)
                                    time.sleep(float(waitTime))
                        else:
                            loggingPrint("No questions found on page")
                        
                        try:
                            pageNavButton = capsResp.getPageNavButton("next")
                            if pageNavButton.get_attribute("value") in capsResp.submitTranslations:
                                loggingPrint("Submit button found! Disregarding any remaining responses...")
                                # submitFound = True
                            else:
                                loggingPrint("Navigating to next page...")
                                capsResp.nextPage()
                        except:
                            if capsPrac.scoreOnly:
                                loggingPrint("Reached end of assessment! Disregarding any remaining responses...")
                                # submitFound = True
                            else:
                                loggingPrint("Error checking assessment form navigation; may not have loaded correctly!")
                        finally:
                            q += len(questions)
                        
                # try:
                    # numQuestions = len(capsResp.getQuestionsInPage())
                # except:
                    # numQuestions = 0
                    
                # if numQuestions > 0 and not submitFound:
                    # loggingPrint("ERROR!!! Not enough question/response entries provided! Filling out form randomly, starting with this page...")
                    # capsResp.completeAssessmentRandomly()
                    
            # # Instrumental Performance Appraisal section
            # capsResp.answerQuestionsInSection(questionResponses=[2,1,2,0,0,2,1,0])
            # capsResp.nextPage()
            
            # # Social Context Appraisal section
            # capsResp.answerQuestionsInSection(questionResponses=[1,2,0,3,2,0,1,1])
            # capsResp.nextPage()
            
            # # Paralinguistic Decoding section
            # capsResp.answerQuestionsInSection(questionResponses=[0,1,2,0,0,0,3,1])
            # capsResp.nextPage()
            
            # # Instrumental Performance section
            # capsResp.answerQuestionsInSection(questionResponses=[1,1,1,0,0,0,1,2])
            # capsResp.nextPage()
            
            # # Affective Expression section
            # capsResp.answerQuestionsInSection(questionResponses=["skip",1,"skip","skip","skip","skip","skip","skip"])
            # capsResp.nextPage()
            
            # # Paralinguistic Signals section
            # capsResp.answerQuestionsInSection(questionResponses=[0,1,1,0,1,0,"skip","skip",0])
            
        if not capsPrac.scoreOnly:
            capsResp.submit()
            
        capsResp.browser.close()
        
        capsPrac.switchToPractitioner()
        capsPrac.browser.refresh()
        
        try:
            try:
                validateForm = testInfo['validateform']
                if validateForm == '' or validateForm is None:
                    validateForm = True
            except:
                validateForm = True
                
            if validateForm:
                try:
                    validateFormMessage = testInfo['validateformmessage']
                    if validateFormMessage == '':
                        validateFormMessage = None
                except:
                    validateFormMessage = None
                    
                if capsPrac.scoreOnly:
                    try:
                        capsPrac.selectPendingForm(id=capsResp.administrationFormGUID)
                    except:
                        capsPrac.selectPendingForm(formEntry=-1)
                else:
                    try:
                        capsPrac.selectCompleteForm(id=capsResp.administrationFormGUID)
                    except:
                        capsPrac.selectCompleteForm(formEntry=0)
                
                capsPrac.validateForm(expectedResponse=validateFormMessage, argsList=argsListValidation)
        except:
            loggingPrint("Validation failed!!!")
            
        try:
            try:
                scoreForm = testInfo['scoreform']
                if scoreForm == '' or scoreForm is None:
                    scoreForm = False
            except:
                scoreForm = False
                
            if scoreForm:
                capsPrac.scoreForm()
        except:
            loggingPrint("Scoring failed!!!")
            capsPrac.browser.save_screenshot(os.path.join(str(directory), "failed_save_" + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))

        try:
            try:
                isDeleteClient = testInfo['deleteclient']
                if isDeleteClient == '' or isDeleteClient is None:
                    isDeleteClient = False
            except:
                isDeleteClient = False
                
            if isDeleteClient:
                capsPrac.deleteClient(clientFirstName + " " + clientLastName)
        except:
            loggingPrint("Deleting client failed!!!")
        
        capsPrac.logout()
       
    except Exception as err:
        loggingPrint(sys.exc_info()[2])
        raise
    finally:
        capsPrac.tearDown()
    
    loggingPrint("Test completed!\r\n")
    
if __name__ == "__main__":
    
    short_options = "he:rd:i:l"
    long_options = ["headless", "env=", "random", "directory=", "input=", "log-to-file"]
    # short_options = "he:rd:i:lw:"
    # long_options = ["headless", "env=", "random", "directory=", "input=", "log-to-file", "wait-time="]
    # "output=",
    
    # Get full command-line arguments
    full_cmd_arguments = sys.argv
    argument_list = full_cmd_arguments[1:]

    env = "uat"
    headless = False
    random = False
    directory = None
    logToFile = False
    # waitTime = None
    
    try:
        arguments, values = getopt.getopt(argument_list, short_options, long_options)
    except getopt.error as err:
        # Output error, and return with an error code
        print (str(err))
        sys.exit(2)
    
    for current_argument, current_value in arguments:
        if current_argument in ("-h", "--headless"):
            headless = True
        elif current_argument in ("-e", "--env"):
            env = current_value
        elif current_argument in ("-d", "--directory"):
            directory = current_value
        elif current_argument in ("-i", "--input"):
            input = current_value
        # elif current_argument in ("-w", "--wait-time"):
            # waitTime = current_value
        elif current_argument in ("-r", "--random"):
            random = True
        elif current_argument in ("-l", "--log-to-file"):
            logToFile = True
            #print (("Enabling special output mode (%s)") % (current_value))

    runTestHarness(env=env, headless=headless, random=random, directory=directory, input=input, logToFile=logToFile)
