$password = Read-Host -AsSecureString "Enter your Windows login password"
$plainPassword = [System.Net.NetworkCredential]::new("", $password).Password

schtasks /create /tn "Horizon-AI-Daily" /tr "powershell -ExecutionPolicy Bypass -File `"c:\Users\李超超\Desktop\知识\run-horizon.ps1`" -Topic ai" /sc daily /st 18:00 /f /ru "LAPTOP-O8IA1J5L\李超超" /rp ($plainPassword)
schtasks /create /tn "Horizon-Unity-Weekly" /tr "powershell -ExecutionPolicy Bypass -File `"c:\Users\李超超\Desktop\知识\run-horizon.ps1`" -Topic unity" /sc weekly /d MON /st 18:00 /f /ru "LAPTOP-O8IA1J5L\李超超" /rp ($plainPassword)

Write-Host "Tasks created successfully!"