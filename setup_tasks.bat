@echo off
schtasks /delete /tn "HorizonAI" /f
schtasks /delete /tn "HorizonUnity" /f
schtasks /create /tn "HorizonAI" /tr "c:\Users\李超超\Desktop\知识\run-ai.bat" /sc daily /st 08:00 /f /ru "LAPTOP-O8IA1J5L\李超超" /rp %1
schtasks /create /tn "HorizonUnity" /tr "c:\Users\李超超\Desktop\知识\run-unity.bat" /sc weekly /d MON /st 08:00 /f /ru "LAPTOP-O8IA1J5L\李超超" /rp %1
echo Tasks created with 08:00 schedule!
pause