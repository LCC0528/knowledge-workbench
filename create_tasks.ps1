$xmlPath1 = "$env:TEMP\horizon-ai.xml"
$xmlContent1 = @'
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Author>LAPTOP-O8IA1J5L\李超超</Author>
    <URI>\Horizon-AI-Daily</URI>
  </RegistrationInfo>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-21-4169494838-2609691741-1413349393-1004</UserId>
      <LogonType>Password</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <IdleSettings>
      <Duration>PT10M</Duration>
      <WaitTimeout>PT1H</WaitTimeout>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
  </Settings>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-07-27T18:00:00</StartBoundary>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Actions Context="Author">
    <Exec>
      <Command>powershell</Command>
      <Arguments>-ExecutionPolicy Bypass -File "c:\Users\李超超\Desktop\知识\run-horizon.ps1" -Topic ai</Arguments>
    </Exec>
  </Actions>
</Task>
'@

[System.IO.File]::WriteAllText($xmlPath1, $xmlContent1, [System.Text.Encoding]::Unicode)
schtasks /create /tn "Horizon-AI-Daily" /xml $xmlPath1 /f
Remove-Item $xmlPath1

$xmlPath2 = "$env:TEMP\horizon-unity.xml"
$xmlContent2 = @'
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Author>LAPTOP-O8IA1J5L\李超超</Author>
    <URI>\Horizon-Unity-Weekly</URI>
  </RegistrationInfo>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-21-4169494838-2609691741-1413349393-1004</UserId>
      <LogonType>Password</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <IdleSettings>
      <Duration>PT10M</Duration>
      <WaitTimeout>PT1H</WaitTimeout>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
  </Settings>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-07-28T18:00:00</StartBoundary>
      <ScheduleByDay>
        <DaysInterval>7</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Actions Context="Author">
    <Exec>
      <Command>powershell</Command>
      <Arguments>-ExecutionPolicy Bypass -File "c:\Users\李超超\Desktop\知识\run-horizon.ps1" -Topic unity</Arguments>
    </Exec>
  </Actions>
</Task>
'@

[System.IO.File]::WriteAllText($xmlPath2, $xmlContent2, [System.Text.Encoding]::Unicode)
schtasks /create /tn "Horizon-Unity-Weekly" /xml $xmlPath2 /f
Remove-Item $xmlPath2

Write-Host "Tasks created successfully!"