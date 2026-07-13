; DNS Jantex Installer Script
; Requires NSIS 3.0+

!include "MUI2.nsh"
!include "FileFunc.nsh"

;--------------------------------
; General Settings
;--------------------------------
Name "DNS Jantex"
OutFile "DNSJantex-Setup.exe"
InstallDir "$PROGRAMFILES\DNS Jantex"
InstallDirRegKey HKLM "Software\DNS Jantex" "InstallDir"
RequestExecutionLevel admin
Unicode True

;--------------------------------
; Version Info
;--------------------------------
VIProductVersion "3.0.4.0"
VIAddVersionKey "ProductName" "DNS Jantex"
VIAddVersionKey "CompanyName" "DNS Jantex"
VIAddVersionKey "FileDescription" "DNS Jantex Installer"
VIAddVersionKey "FileVersion" "3.0.4"
VIAddVersionKey "ProductVersion" "3.0.4"
VIAddVersionKey "LegalCopyright" "DNS Jantex"

;--------------------------------
; Interface Settings
;--------------------------------
!define MUI_ABORTWARNING
!define MUI_ICON "assets\icon.ico"
!define MUI_UNICON "assets\icon.ico"

;--------------------------------
; Pages
;--------------------------------
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
; Languages
;--------------------------------
!insertmacro MUI_LANGUAGE "English"

;--------------------------------
; Installer Sections
;--------------------------------
Section "DNS Jantex (required)" SecMain
    SectionIn RO

    ; Set output path to installation directory
    SetOutPath $INSTDIR

    ; Install main executable
    File "dist\DNSChanger\DNSChanger.exe"

    ; Install updater and the narrowly scoped elevated DNS helper
    File "dist\Updater.exe"
    File "dist\DNSHelper.exe"

    ; Install internal dependencies
    SetOutPath "$INSTDIR\_internal"
    File /r "dist\DNSChanger\_internal\*.*"

    ; Reset output path for icon
    SetOutPath $INSTDIR
    File "assets\icon.ico"

    ; Store installation folder
    WriteRegStr HKLM "Software\DNS Jantex" "InstallDir" "$INSTDIR"

    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Add to Programs and Features
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DNS Jantex" \
        "DisplayName" "DNS Jantex"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DNS Jantex" \
        "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DNS Jantex" \
        "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DNS Jantex" \
        "DisplayIcon" '"$INSTDIR\DNSChanger.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DNS Jantex" \
        "Publisher" "DNS Jantex"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DNS Jantex" \
        "URLInfoAbout" "https://dns-jantex.pages.dev/"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DNS Jantex" \
        "URLUpdateInfo" "https://github.com/ZeLoExE/dns-jantex/releases"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DNS Jantex" \
        "DisplayVersion" "3.0.4"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DNS Jantex" \
        "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DNS Jantex" \
        "NoRepair" 1

    ; Get installed size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DNS Jantex" \
        "EstimatedSize" "$0"
SectionEnd

Section "Desktop Shortcut" SecDesktop
    CreateShortCut "$DESKTOP\DNS Jantex.lnk" "$INSTDIR\DNSChanger.exe" "" "$INSTDIR\DNSChanger.exe" 0
SectionEnd

Section "Start Menu Shortcuts" SecStartMenu
    CreateDirectory "$SMPROGRAMS\DNS Jantex"
    CreateShortCut "$SMPROGRAMS\DNS Jantex\DNS Jantex.lnk" "$INSTDIR\DNSChanger.exe" "" "$INSTDIR\DNSChanger.exe" 0
    CreateShortCut "$SMPROGRAMS\DNS Jantex\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
SectionEnd

;--------------------------------
; Descriptions
;--------------------------------
LangString DESC_SecMain ${LANG_ENGLISH} "DNS Jantex application files (required)."
LangString DESC_SecDesktop ${LANG_ENGLISH} "Create a shortcut on your Desktop."
LangString DESC_SecStartMenu ${LANG_ENGLISH} "Create Start Menu shortcuts."

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecMain} $(DESC_SecMain)
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} $(DESC_SecDesktop)
    !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} $(DESC_SecStartMenu)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

;--------------------------------
; Uninstaller Section
;--------------------------------
Section "Uninstall"
    ; Remove files
    Delete "$INSTDIR\DNSChanger.exe"
    Delete "$INSTDIR\Updater.exe"
    Delete "$INSTDIR\DNSHelper.exe"
    Delete "$INSTDIR\icon.ico"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir /r "$INSTDIR\_internal"
    RMDir "$INSTDIR"

    ; Remove shortcuts
    Delete "$DESKTOP\DNS Jantex.lnk"
    Delete "$SMPROGRAMS\DNS Jantex\DNS Jantex.lnk"
    Delete "$SMPROGRAMS\DNS Jantex\Uninstall.lnk"
    RMDir "$SMPROGRAMS\DNS Jantex"

    ; Remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DNS Jantex"
    DeleteRegKey HKLM "Software\DNS Jantex"
SectionEnd
