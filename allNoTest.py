import sys
from multiprocessing import Pool
sys.stdout.reconfigure(encoding='utf-8')
from oesLibrary import *
from dateutil.relativedelta import *
from datetime import date
import getopt, csv, os, re, chardet
import pprint
from contextlib import redirect_stdout, redirect_stderr
loginUrl = "https://practitioner-dev.wpspublish.io"
directory = str("C:\\Users\\bjackson\\Desktop\\Test Scripts\\DP4\\Results\\AllNo_ASCII_3")
Prac = oesPractitioner(loginUrl)
Prac.headless = False
Prac.download_dir = directory
clientFirstName="DP4-ALL"
clientLastName="NO"
assessmentType = '98'
# assessmentType = 'dp4'
assessmentForms = ['Parent/Caregiver Checklist', 'Teacher Checklist', 'Parent/Caregiver Interview', 'Clinician Rating', 'Spanish Teacher Checklist', 'Spanish Parent/Caregiver Interview', 'Spanish Parent/Caregiver Checklist']
respondentName = 'Random Respondent'
clientCaseID='1098'
clientMonth=5
clientDay=0
clientYear=16
useAscii = True
argsListValidation =[["Clinician's name/ID", randomString(stringLength=40, ascii=useAscii)], ['Confidence Interval', '90'], ['Scale Comparison', 'Standard']]
today = date.today()
dob = today+relativedelta(years=-int(clientYear), months=-int(clientMonth), days=-int(clientDay))
clientYear = str(dob.year)
clientMonth = str(dob.month)
clientDay = str(dob.day)

def basicTest(assessmentForm):
    with open(os.path.join(str(directory), str(assessmentForm.replace(' ','_').replace('/', '_') + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".txt")), 'w', encoding='utf-8') as f:
        with redirect_stdout(f), redirect_stderr(f):
            Prac.setUp()
            Prac.login()

            Prac.navigateToClient(str(clientFirstName + " " + clientLastName))

            # Prac.createNewClient(
            # clientFirstName=clientFirstName,
            # clientLastName=clientLastName,
            # clientMonth=clientMonth, 
            # clientDay=clientDay, 
            # clientYear=clientYear,
            # clientCaseID=clientCaseID
            # )

            if 'spanish' in assessmentForm.lower():
                argsListAssessment = [["Nombre", randomString(stringLength=40, ascii=useAscii)], ["relationship to child", randomString(stringLength=40, ascii=useAscii)], ["s name", randomString(stringLength=40, ascii=useAscii)], ["Clinician’s title", randomString(stringLength=40, ascii=useAscii)], ["known the child", randomString(stringLength=40, ascii=useAscii)], ["hace que conoces", randomString(stringLength=40, ascii=useAscii)]]
                assessmentResponse = 'N'
            else:
                argsListAssessment = [["Your name", randomString(stringLength=40, ascii=useAscii)], ["s name", randomString(stringLength=40, ascii=useAscii)], ["relationship", randomString(stringLength=40, ascii=useAscii)], ["Clinician’s title", randomString(stringLength=40, ascii=useAscii)], ["known the child", randomString(stringLength=40, ascii=useAscii)]]
                assessmentResponse = 'N'
            argsListAssessment.extend(argsListValidation)
            
            Prac.administerAssessment(assessmentType=assessmentType, assessmentForm=assessmentForm, respondentName=respondentName)
            Prac.switchToRespondent()
            dp4Resp = oesRespondent(Prac.browser, assessmentType, Prac.scoreOnly)
            dp4Resp.navigateToQuestions(argsList=argsListAssessment)
            waitTime = 0.2
            dp4Resp.completeAssessmentSingleResponse(response=assessmentResponse, waitTime=waitTime)

            if not Prac.scoreOnly:
                dp4Resp.submit()
                
            dp4Resp.browser.close()

            Prac.switchToPractitioner()
            Prac.browser.refresh()

            try:
                validateForm = True
                    
                if validateForm:
                    validateFormMessage = None
                    
                    formId = Prac.getFormIdFromAdministrationFormGUID(dp4Resp.administrationFormGUID)
                    
                    if Prac.scoreOnly:
                        try:
                            Prac.selectPendingForm(id=dp4Resp.administrationFormGUID)
                        except:
                            Prac.selectPendingForm(formEntry=-1)
                    else:
                        try:
                            Prac.selectCompleteForm(id=dp4Resp.administrationFormGUID)
                        except:
                            Prac.selectCompleteForm(formEntry=0)
                    
                    Prac.validateForm(expectedResponse=validateFormMessage, argsList=argsListValidation)
            except:
                loggingPrint("Validation failed!!!")
                Prac.browser.save_screenshot(os.path.join(str(os.getcwd()), str(assessmentForm.replace(' ','_').replace('/', '_')) + "_regression_failed_validation_" + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))

            try:
                Prac.scoreForm()
                loggingPrint("Generated Score Report for Form ID " + formId + "!")
            except:
                loggingPrint("Scoring failed!!!")
                Prac.browser.save_screenshot(os.path.join(str(os.getcwd()), str(assessmentForm.replace(' ','_').replace('/', '_')) + "_regression_failed_save_" + (time.strftime("_%F_%T", time.gmtime())).replace(":", "-") + ".png"))
                        
            Prac.logout()

            Prac.tearDown()
if __name__ == '__main__':
    with multiprocessing.Pool(processes=2) as pool:
        pool.map(basicTest, assessmentForms)