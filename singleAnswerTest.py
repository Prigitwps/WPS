import sys
from multiprocessing import Pool
sys.stdout.reconfigure(encoding='utf-8')
from oesLibrary import *
from dateutil.relativedelta import *
from datetime import date, datetime
import getopt, csv, os, re, chardet
import pprint, pytz
from contextlib import redirect_stdout, redirect_stderr

def basicTest(env="uat", headless=False, directory=None, logToFile=False, useAscii=False, answer=None, assessmentForm=None, logName=None):
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
    elif env=="dev2":
        loginUrl = "https://practitioner-dev2.wpspublish.io"
    elif env=="dev1":
        loginUrl = "https://practitioner-dev1.wpspublish.io"
    elif env=="qa1":
        loginUrl = "https://practitioner-qa1.wpspublish.io"
    elif env=="uat1":
        loginUrl = "https://practitioner-uat1.wpspublish.io"
    elif env=="perf":
        loginUrl = "https://platform.perf.wpspublish.com"
    else:
        loginUrl = env
    # directory = str("C:\\Users\\bjackson\\Desktop\\Test Scripts\\DP4\\Results\\AllYes_ASCII_3")
    
    if logToFile:
        if logName is None:
            logName = str(os.path.splitext(os.path.basename(str(__file__)))[0])
            
        logNameStamped = str(logName) + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-")

        Prac = oesPractitioner(loginUrl, logName=logNameStamped)
    else:
        Prac = oesPractitioner(loginUrl)
    logger = Prac.logger
    Prac.headless = headless
    Prac.download_dir = directory
    clientFirstName="DP4-ALL"
    clientLastName=str(answer)
    # assessmentType = '98'
    assessmentType = 'dp4'
    respondentName = 'Respondent ' + pytz.utc.localize(dt=datetime.utcnow()).astimezone(pytz.timezone("America/Los_Angeles")).strftime("%I:%M:%S%p")

    clientCaseID='1099'
    argsListValidation =[["Clinician's name/ID", randomString(stringLength=40, ascii=useAscii)], ['Confidence Interval', '90'], ['Scale Comparison', 'Standard']]
    clientDate = adjustedDateCalculator(yearsAdjust=16, monthsAdjust=5, daysAdjust=0)
    clientYear = str(clientDate.year)
    clientMonth = str(clientDate.month)
    clientDay = str(clientDate.day)

    
    # with open(os.path.join(str(directory), str(assessmentForm.replace(' ','_').replace('/', '_') + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".txt")), 'w', encoding='utf-8') as f:
        # with redirect_stdout(f), redirect_stderr(f):
    Prac.setUp()
    Prac.login()

    try:    
        Prac.navigateToClient(str(clientFirstName + " " + clientLastName))
        Prac.updateClient(
        clientFirstName=clientFirstName,
        clientLastName=clientLastName,
        clientMonth=clientMonth, 
        clientDay=clientDay, 
        clientYear=clientYear,
        clientCaseID=clientCaseID
        )
    except:
        Prac.createNewClient(
        clientFirstName=clientFirstName,
        clientLastName=clientLastName,
        clientMonth=clientMonth, 
        clientDay=clientDay, 
        clientYear=clientYear,
        clientCaseID=clientCaseID
        )
        
    if str(answer).lower() in ["yes", "y"]:
        if 'spanish' in assessmentForm.lower():
            answer = 'S'
        else:
            answer = 'Y'

    if 'spanish' in assessmentForm.lower():
        argsListAssessment = [["Nombre", randomString(stringLength=40, ascii=useAscii)], ["relationship to child", randomString(stringLength=40, ascii=useAscii)], ["s name", randomString(stringLength=40, ascii=useAscii)], ["Clinician’s title", randomString(stringLength=40, ascii=useAscii)], ["known the child", randomString(stringLength=40, ascii=useAscii)], ["hace que conoces", randomString(stringLength=40, ascii=useAscii)]]
    else:
        argsListAssessment = [["Your name", randomString(stringLength=40, ascii=useAscii)], ["s name", randomString(stringLength=40, ascii=useAscii)], ["relationship", randomString(stringLength=40, ascii=useAscii)], ["Clinician’s title", randomString(stringLength=40, ascii=useAscii)], ["known the child", randomString(stringLength=40, ascii=useAscii)]]

    argsListAssessment.extend(argsListValidation)
    
    Prac.administerAssessment(assessmentType=assessmentType, assessmentForm=assessmentForm, respondentName=respondentName)
    Prac.switchToRespondent()
    Resp = oesRespondent(browser=Prac.browser, assessment=assessmentType, scoreOnly=Prac.scoreOnly, logName=Prac.logger)
    Resp.navigateToQuestions(argsList=argsListAssessment)
    waitTime = 0.2
    Resp.completeAssessmentSingleResponse(response=str(answer), waitTime=waitTime)

    if not Prac.scoreOnly:
        Resp.submit()
        
    Resp.browser.close()

    Prac.switchToPractitioner()
    Prac.browser.refresh()

    try:
        validateForm = True
            
        if validateForm:
            validateFormMessage = None
            
            formId = Prac.getFormIdFromAdministrationFormGUID(Resp.administrationFormGUID)
            
            if Prac.scoreOnly:
                try:
                    Prac.selectPendingForm(id=Resp.administrationFormGUID)
                except:
                    Prac.selectPendingForm(formEntry=-1)
            else:
                try:
                    Prac.selectCompleteForm(id=Resp.administrationFormGUID)
                except:
                    Prac.selectCompleteForm(formEntry=0)
            
            Prac.validateForm(expectedResponse=validateFormMessage, argsList=argsListValidation)
    except:
        logger.exception("Validation failed!!!")
        Prac.browser.save_screenshot(os.path.join(str(os.getcwd()), str(assessmentForm.replace(' ','_').replace('/', '_')) + "_regression_failed_validation_" + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))

    try:
        Prac.scoreForm()
        logger.warning("Generated Score Report for Form ID " + formId + "!")
    except:
        logger.exception("Scoring failed!!!")
        Prac.browser.save_screenshot(os.path.join(str(os.getcwd()), str(assessmentForm.replace(' ','_').replace('/', '_')) + "_regression_failed_save_" + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                
    Prac.logout()

    Prac.tearDown()

if __name__ == '__main__':
    
    short_options = "he:d:lna"
    long_options = ["headless", "env=", "directory=", "log-to-file", "non-ascii", "answer"]
    # short_options = "he:rd:i:lw:"
    # long_options = ["headless", "env=", "random", "directory=", "input=", "log-to-file", "wait-time="]
    # "output=",
    
    # Get full command-line arguments
    full_cmd_arguments = sys.argv
    argument_list = full_cmd_arguments[1:]

    env = "uat"
    headless = False
    random = False
      = str(os.getcwd())
    logToFile = False
    answer = None
    useAscii = True
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
            topDirectory = current_value
        # elif current_argument in ("-w", "--wait-time"):
            # waitTime = current_value
        elif current_argument in ("-l", "--log-to-file"):
            logToFile = True
        elif current_argument in ("-n", "--non-ascii"):
            useAscii = False
        elif current_argument in ("-a", "--answer"):
            answer = str(current_value)
            #print (("Enabling special output mode (%s)") % (current_value))

    if answer is None:
        answer = 'Y'
    
    try:
        topDirectory = str(os.path.join(str(topDirectory), str(os.path.splitext("all_" + str(answer) + "_ASCII_" + str(useAscii) + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-"))))
        os.mkdir(topDirectory)
    except:
        logging.exception("Unable to create sub-directory for all tests! Outputting to specified directory instead")
    
    assessmentForms = ['Parent/Caregiver Checklist', 'Teacher Checklist', 'Parent/Caregiver Interview', 'Clinician Rating', 'Spanish Teacher Checklist', 'Spanish Parent/Caregiver Interview', 'Spanish Parent/Caregiver Checklist']
    dataInputs = [[env, headless, str(topDirectory), logToFile, useAscii, answer, form] for form in assessmentForms]
    
    # dataInputs = [[env, headless, random, str(topDirectory), logToFile, logName, sheets[f]] for f in range(20, len(sheets))]
    
    with multiprocessing.Pool(processes=2) as pool:
        pool.starmap(basicTest, dataInputs)