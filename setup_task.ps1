$taskName = "Horizon-AI-Daily"
$scriptPath = Join-Path $PSScriptRoot "run-horizon.ps1"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$scriptPath`" -Topic ai"
$trigger = New-ScheduledTaskTrigger -Daily -At 08:00
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

Write-Host "Current user: $currentUser"
$pwd = Read-Host "Enter Windows password" -AsSecureString
$plainPwd = [System.Net.NetworkCredential]::new("", $pwd).Password

$principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Password -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings

Register-ScheduledTask -TaskName $taskName -InputObject $task -User $currentUser -Password $plainPwd -Force
Write-Host "Done! Task created."