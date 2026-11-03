@echo off
setlocal
set "OUT=C:\ProgramData\Aurora\VpnPilot"
if not exist "%OUT%" mkdir "%OUT%"
(
  echo START=%DATE% %TIME%
  echo COMPUTER=%COMPUTERNAME%
  whoami
  ipconfig ^| findstr /C:"10.253.91."
  nltest /dsgetsite
  nltest /dsgetdc:aurora-logistics.local /force
  powershell.exe -NoProfile -Command "Test-Path '\\spb-dc1-al.aurora-logistics.local\SYSVOL'"
  echo END=%DATE% %TIME%
) > "%OUT%\startup.txt" 2>&1
