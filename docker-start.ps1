#need to check if valid assessment
$fileExists = $false
#construct string
$AssessmentName = ''
$regressionFileName = ''
while(!$fileExists -and -not($AssessmentName.Equals("f")))
{    
    $AssessmentName = Read-Host "Please enter assessment name or type 'f' for full regression"
    $cleanedAssessmentName = $AssessmentName -replace "\W"
    $regressionFileName = "./testModules/${cleanedAssessmentName}Regression.py"
    $fileExists = Test-Path -Path $regressionFileName
    if ($AssessmentName.Equals("f"))
    {
        $regressionFileName = "fullRegression.py"
        $fileExists = $true
    }
    elseif (-not $fileExists)
    {
        Write-Host "That assessment doesn't exist."
    }    
}


#construct python script to run assessment
$runRegressionScript = "python $regressionFileName -e uat -h -u -l"

#Write-Host $runRegressionScript

Write-Host "Setting up variables"

$env:IMAGE_NAME = "qa_automation";
$env:IMAGE_TAG = "v1";
$env:CONTAINER_NAME = "sid_test";
$env:AWS_CREDS_SOURCE_PATH = "$env:USERPROFILE\.aws\";

Write-Host "Pulling Container and copying AWS creds from the host"

docker rm $env:CONTAINER_NAME -f
docker pull ghcr.io/wpspublish/${env:IMAGE_NAME}:${env:IMAGE_TAG}
docker run -t -d --name $env:CONTAINER_NAME ghcr.io/wpspublish/${env:IMAGE_NAME}:${env:IMAGE_TAG}
docker cp $env:AWS_CREDS_SOURCE_PATH "${env:CONTAINER_NAME}:/root/.aws/"

Write-Host "Entering into Docker Container"

docker exec -it $env:CONTAINER_NAME bash -c $runRegressionScript