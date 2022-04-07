# Assessment load testing harness for OES 1.0
# Requirements: Selenium and Chrome Drivers
# Selenium Driver: https://www.selenium.dev/downloads/
# Chrome Driver: https://chromedriver.chromium.org/downloads
# Usage: python loadTest.py <numberOfParallelThreads> <numberOfIterationsPerThread> <URL or CSV of URLS to process>
# If no number of threads/iterations provided, default is 1

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import multiprocessing, traceback
import subprocess, signal, time, sys, random, string, re

try:
    threads = int(sys.argv[1])
except:
    threads = 1

try:
    iterations = int(sys.argv[2])
except:
    iterations = 1

try:
    loginUrl = sys.argv[3]
except:
    loginUrl = "uat"

try:
    assessmentType = re.sub(r"\s+", "", (re.sub(r"[^\sa-zA-Z0-9]", "", sys.argv[4]).lower().strip()))
except:
    assessmentType = "abas3"

class loadAssessment:
    
    def __init__(self, loginUrl, assessmentType):
        self.loginUrl = loginUrl
        self.assessmentType = assessmentType
    
    def setUp(self):
        try:
            options = webdriver.ChromeOptions()
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            options.add_argument('--no-sandbox')
            options.add_argument('--headless')
            self.browser = webdriver.Chrome(options=options)
            loggingPrint("Starting navigating to " + str(self.loginUrl) + "/account/login")
            self.browser.get(self.loginUrl + "/account/login")
        except Exception:
            loggingPrint(sys.exc_info()[2])
            raise

    def tearDown(self):
        self.browser.quit()

    def login(self):
        
        try:
            loggingPrint("Attempting to respond to login popup")
            loginPopupXPath = "//*/input[@value='OK' and @class='closeX']"
            okayButton = WebDriverWait(self.browser, 15).until(EC.presence_of_element_located((By.XPATH, loginPopupXPath)))            

            # "click" the element through JavaScript
            self.browser.execute_script("arguments[0].click();", okayButton)
        except:
            loggingPrint("Login popup did not appear")
        finally:
            loggingPrint("Logging in")
            usernameField = WebDriverWait(self.browser, 60).until(EC.presence_of_element_located((By.ID, "UserName")))
            passwordField = WebDriverWait(self.browser, 60).until(EC.presence_of_element_located((By.ID, "Password")))
            
            loggingPrint("Beginning User Login Test")

            usernameField.send_keys("bjackson@wpspublish.com")
            passwordField.send_keys("WPStesting1?")

            self.browser.find_element_by_id("loginID").click()
            
            element = WebDriverWait(self.browser, 60).until(EC.presence_of_element_located((By.ID, "caseDashboard")))
            loggingPrint("Login successful")

    def newClient(self):
        loggingPrint("Attempting to create new client")
        newClientXPath = "//*/img[contains(@alt, 'Create New Client')]"
        saveClientXPath = "//*/input[@id='clientSave']"
        
        newClient = WebDriverWait(self.browser, 60).until(EC.element_to_be_clickable((By.XPATH, newClientXPath)))
        # Bit of a hack; some environments occasionally attempt to load a chat option over this
        # So trigger the click event without the actual click
        self.browser.execute_script("arguments[0].click();", newClient)
        #newClient.click()
        
        # Would love to use the ID instead, but the ID is on the parent, so gotta use the XPATH locator with the ID
        firstName = WebDriverWait(self.browser, 60).until(EC.presence_of_element_located((By.XPATH, "//*/td[@id='FirstName']/input")))
        firstName.send_keys(randomString())
        
        lastName = WebDriverWait(self.browser, 60).until(EC.presence_of_element_located((By.XPATH, "//*/td[@id='LastName']/input")))
        lastName.send_keys(randomString())
        
        caseId = WebDriverWait(self.browser, 60).until(EC.presence_of_element_located((By.XPATH, "//*/td[@id='CaseAltId']/input")))
        caseId.send_keys(randomString())
        
        genderSelect = Select(self.browser.find_element_by_id("genderOpt"))
        genderSelect.select_by_value(str(random.randrange(1,3)))

        birthMonth = Select(self.browser.find_element_by_id("dobMonth"))
        birthMonth.select_by_value(str(random.randrange(1,13)))
        
        birthDay = Select(self.browser.find_element_by_id("dobDay"))
        birthDay.select_by_value(str(random.randrange(1,28)))
        
        birthYear = Select(self.browser.find_element_by_id("dobYear"))
        birthYear.select_by_value(str(int(time.strftime("%Y"))-2))
        
        clientEmail = WebDriverWait(self.browser, 60).until(EC.presence_of_element_located((By.XPATH, "//*/td[@id='Email']/input")))
        clientEmail.send_keys(str(randomString(12))+"@"+str(randomString(6))+"."+str(randomString(3)))
        
        loggingPrint("Attempting to save client")
        self.browser.find_element_by_id('clientSave').click()
        
        interactingElement = WebDriverWait(self.browser, 60).until(EC.presence_of_element_located((By.ID, "successClientCreate")))
        interactingElement.click()
        loggingPrint("Client created successfully")

    def administerAssessment(self):
        loggingPrint("Administering new assessment")
        interactingElement = WebDriverWait(self.browser, 60).until(EC.element_to_be_clickable((By.ID, "newAdministration")))
        interactingElement.click()
        
        dp3XPath = "//*/span[@assessmentid='6']"
        abas3XPath = "//*/span[@assessmentid='4']"

        if self.assessmentType=='abas3':
            interactingElement = WebDriverWait(self.browser, 60).until(EC.element_to_be_clickable((By.XPATH, abas3XPath)))
        else:
            interactingElement = WebDriverWait(self.browser, 60).until(EC.element_to_be_clickable((By.XPATH, dp3XPath)))
        loggingPrint("Selecting "+self.assessmentType+" assessment")
        interactingElement.click()
        
        loggingPrint("Adding assessment form")        
        interactingElement = WebDriverWait(self.browser, 60).until(EC.element_to_be_clickable((By.ID, "addForm")))
        interactingElement.click()
        
        loggingPrint("Setting up assessment")
        
        try:
            try:
                interactingElement = WebDriverWait(self.browser, 60).until(EC.element_to_be_clickable((By.ID, "TestFormId")))
                interactingElement = Select(interactingElement)
                interactingElement.select_by_visible_text(self.browser.find_element_by_xpath("//*/select[@id='TestFormId']//option[contains(text(), 'Caregiver') and contains(text(), 'Parent') and not (contains(text(), 'Spanish'))]").text)
            except:
                loggingPrint("Form assignment didn't load in time!")
                self.browser.refresh()
                loggingPrint("Page refreshed, attempting one more time...")
                interactingElement = WebDriverWait(self.browser, 60).until(EC.element_to_be_clickable((By.ID, "TestFormId")))
                interactingElement = Select(interactingElement)
                interactingElement.select_by_visible_text(self.browser.find_element_by_xpath("//*/select[@id='TestFormId']//option[contains(text(), 'Caregiver') and contains(text(), 'Parent') and not (contains(text(), 'Spanish'))]").text)
        except:
            loggingPrint("Failed to assign form!")
            
        interactingElement = WebDriverWait(self.browser, 60).until(EC.element_to_be_clickable((By.XPATH, "//*/div[@class='delivMethod2']/input")))
        interactingElement.click()
        
        interactingElement = WebDriverWait(self.browser, 60).until(EC.element_to_be_clickable((By.ID, "RaterNameIsCaseName")))
        interactingElement.click()
        
        interactingElement = WebDriverWait(self.browser, 60).until(EC.element_to_be_clickable((By.ID, "saveStart")))
        interactingElement.click()
        self.browser.switch_to.window(self.browser.window_handles[-1])
        
        loggingPrint("Starting assessment")

    def runTest(self):
        try:
            loggingPrint("Waiting for assessment to load")
            
            nextSectionButtonXPath = "//*[@class='pagingNav commonNavButtons']/input[@type='button' and @class='next']"
            prevSectionButtonXPath = "//*[@class='pagingNav commonNavButtons']/input[@type='button' and @class='prev']"
            testQuestions = "//*/div[@class='testsectionContainer']"
            
            nextSectionButton = WebDriverWait(self.browser, 60).until(EC.element_to_be_clickable((By.XPATH, nextSectionButtonXPath)))
            
            loggingPrint("Navigating to assessment")
            
            try:
                questionsLoaded = self.browser.find_element_by_xpath(testQuestions)
            except:
                questionsLoaded = False
            
            while (questionsLoaded==False):
                
                try:
                    requiredValueInput = self.browser.find_element_by_xpath("//*/input[@data-val-required='True']")
                    if requiredValueInput.get_attribute("type") == "text":
                        requiredValueInput.send_keys(randomString())
                    else:
                        requiredValueInput.click()
                    
                except:
                    requiredValueInput = False
                
                try:
                    try:
                        nextSectionButton = WebDriverWait(self.browser, 60).until(EC.element_to_be_clickable((By.XPATH, nextSectionButtonXPath)))            
                        nextSectionButton.click()
                        nextSectionButton = WebDriverWait(self.browser, 60).until(EC.element_to_be_clickable((By.XPATH, nextSectionButtonXPath)))
                    except:
                        loggingPrint("Assessment questions didn't load in time!")
                        self.browser.refresh()
                        loggingPrint("Page refreshed, attempting one more time...")
                        nextSectionButton = WebDriverWait(self.browser, 60).until(EC.element_to_be_clickable((By.XPATH, nextSectionButtonXPath)))            
                        nextSectionButton.click()
                        nextSectionButton = WebDriverWait(self.browser, 60).until(EC.element_to_be_clickable((By.XPATH, nextSectionButtonXPath)))
                except:
                    loggingPrint("Failed to navigate to assessment questions!")
                    
                try:
                    questionsLoaded = self.browser.find_element_by_xpath(testQuestions)
                except:
                    questionsLoaded = False

            loggingPrint("Beginning assessment response")
            
            questionXPath = "//*/form[@id='formAdministration']//tr[contains(@class, 'response')]"
            
            assessmentPage = 1
            while nextSectionButton.get_attribute("value") != "Submit":
                
                nextSectionButton = WebDriverWait(self.browser, 60).until(EC.element_to_be_clickable((By.XPATH, nextSectionButtonXPath)))
                loggingPrint("Starting page " + str(assessmentPage))
                
                # hideInstructions = self.browser.find_elements_by_xpath("//*/img[@class='hideInstructions']")
                # if hideInstructions.is_displayed():
                    # hideInstructions.click()
                
                element = WebDriverWait(self.browser, 60).until(EC.element_to_be_clickable((By.XPATH, questionXPath+"//input[@type='radio' and not(@checked)]")))
                questionsList = self.browser.find_elements_by_xpath(questionXPath)
                
                loggingPrint(str(len(questionsList))+" questions in assessment page, changing responses")
                
                for question in range(len(questionsList)):
                    answers = self.browser.find_elements_by_xpath(questionXPath+'['+str(question+1)+"]//input[@type='radio' and not(@checked)]")
                    answers[random.randrange(len(answers))].click()
                    time.sleep(0.3)
                
                # self.browser.find_element_by_xpath(prevSectionButtonXPath).click()

                # element = WebDriverWait(self.browser, 60).until(EC.element_to_be_clickable((By.XPATH, "//*[@seqno='1']")))
                
                nextSectionButton.click()
                
                loggingPrint("Page " + str(assessmentPage)+" complete!")
                assessmentPage += 1
            
            loggingPrint("Attempting submit")
            submitConfirmation = WebDriverWait(self.browser, 60).until(EC.element_to_be_clickable((By.XPATH, "//*/*[@class='finishedTest']")))            
            submitConfirmation.click()
            
            submitSuccess = WebDriverWait(self.browser, 60).until(EC.presence_of_element_located((By.XPATH, "//*/h2[text()[contains(.,'finished this assessment')]]")))
            loggingPrint("Submit successful")
            
            self.browser.switch_to.window(self.browser.window_handles[0])
            self.browser.get(self.loginUrl + "/account/logout")
            submitSuccess = WebDriverWait(self.browser, 60).until(EC.presence_of_element_located((By.XPATH, "//*/div[@class='loginHeader'][text()[contains(.,'Practitioner Login')]]")))
            loggingPrint("Practitioner logout successful")
            
        except Exception:
            loggingPrint(sys.exc_info()[2])
            raise

def randomString(stringLength=6):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(stringLength))

  
def takeAssessment(packedArgs):    
    iterations = packedArgs[0][0]
    env = packedArgs[0][1]
    assessment = packedArgs[1]
    
    if env=="staging":
        loginUrl = "https://platform.stage.wpspublish.com"
    elif env=="uat":
        loginUrl = "https://practitioner-uat.wpspublish.io"
    elif env=="qa":
        loginUrl = "https://practitioner-qa.wpspublish.io"
    elif env=="prod":
        loginUrl = "https://platform.wpspublish.com"
        
    testCase = loadAssessment(loginUrl, assessment)
    for x in range(iterations):
        loggingPrint("Starting iteration "+str(x+1))
        try:
            testCase.setUp()
            testCase.login()
            testCase.newClient()
            testCase.administerAssessment()
            testCase.runTest()
        except Exception:
            loggingPrint(sys.exc_info()[2])
            raise
        finally:
            testCase.tearDown()


def gen_chunks(reader, chunksize=100):
    # not being used right now but you never know...
    chunk = []
    for row, line in enumerate(reader):
        if (row % chunksize == 0 and row > 0):
            yield chunk
            del chunk[:]
        chunk.append(line[0])
    yield chunk

def loggingPrint(message):
    poolWorker = str(multiprocessing.current_process().name)
    processWorker = str(multiprocessing.Process().name)        
    print(time.strftime("%a, %d %b %Y %H:%M:%S +0000")+" "+poolWorker+" "+processWorker+": "+message)

if __name__ == "__main__":

    loggingPrint("Attempting to start test")
    pool = multiprocessing.Pool(threads)
    try:
        
        if loginUrl[-4:] == '.csv':
            with open(loginUrl, newline='') as csvfile:
                urlList = csv.reader(csvfile)
                pool.map(takeAssessment, [((iterations, line[0]), assessmentType) for row, line in enumerate(urlList)])
        else:
            urlList = []
            for i in range(threads):
                urlList.append(loginUrl)                
            pool.map(takeAssessment, [((iterations, line), assessmentType) for line in urlList])
    except Exception:
        loggingPrint(sys.exc_info()[2])
        raise
    finally:
        pool.close()
        pool.join()

    loggingPrint("Test completed!\r\n")