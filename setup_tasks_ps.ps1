$password = Read-Host -AsSecureString "Enter Windows password"
$plainPassword = [System.Net.NetworkCredential]::new("", $password).Password

$psPath = "powershell"
$scriptPath = "c:\Users\李超超\Desktop\知识\run-horizon.ps1"
$argAI = "-ExecutionPolicy Bypass -File `"$scriptPath`" -Topic ai"
$argUnity = "-ExecutionPolicy Bypass -File `"$scriptPath`" -Topic unity"

schtasks /delete /tn "HorizonAI" /f | Out-Null
schtasks /delete /tn "HorizonUnity" /f | Out-Null

schtasks /create /tn "HorizonAI" /tr "$psPath $argAI" /sc daily /st 08:00 /f /ru "LAPTOP-O8IA1J5L\李超超" /rp $plainPassword
schtasks /create /tn "HorizonUnity" /tr "$psPath $argUnity" /sc weekly /d MON /st 08:00 /f /ru "LAPTOP-O8IA1J5L\李超超" /rp $plainPassword

Write-Host "Done!"