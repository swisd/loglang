@echo off
setlocal ENABLEDELAYEDEXPANSION

set waitprompt=1
if /I "%2" EQU "-noprompt" (
    set waitprompt=0
)
set file=%1
set "initialFile=%~1"
set "fileStack[0]=!initialFile!"
set stack_level=1
set currentLine=0
set file=%1
set /a vint=%RANDOM% * 64 / 32768 + 1
set /a tid=%RANDOM% * 30300 / 32768 + 1
set /a rtid=%tid% + %vint%
set version=0.1.0
echo RealTime ID:    %rtid%
echo V-Int:          %vint%
echo.
echo.
set start=%time%

rem === PREPROCESS DSL DEFINITIONS ===
rem capture all "int <name> def … / list /" lines into DSL_<name>
for /f "usebackq tokens=1,2,3* delims= " %%A in ("%initialFile%") do (
  if /I "%%A"=="int" if /I "%%C"=="def" (
    set "ds_name=%%B"
    rem grab everything between the first "/" and the next "/"
    setlocal ENABLEDELAYEDEXPANSION
    set "inList="
    set "capture="
    for %%V in (%%D) do (
      if defined capture (
        if "%%V"=="/" (
          endlocal & set "DSL_!ds_name!=!inList!"
        ) else (
          set "inList=!inList!%%V "
        )
      ) else if "%%V"=="/" (
        set "capture=1"
      )
    )
  )
)
rem capture "type <t> (matches any in <DS>)"
for /f "usebackq tokens=1,2,3,4,5 delims= ()" %%A in ("%initialFile%") do (
  if /I "%%A"=="type" if /I "%%C"=="matches" (
    set "TYPE_%%B=%%E"
  )
)

:interpret
FOR /F "tokens=* delims=" %%x in ('type %1') DO (
    set data=%%x
    for /f "tokens=1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26 delims= " %%a in ("!data!") do (
        set arg1=%%a
        set arg2=%%b
        set arg3=%%c
        set arg4=%%d
        set arg5=%%e
        set arg6=%%f
        set arg7=%%g
        set arg8=%%h
        set arg9=%%i
        set arg10=%%j
        set arg11=%%k
        set arg12=%%l
        set arg13=%%m
        set arg14=%%n
        set arg15=%%o
        set arg16=%%p
        set arg17=%%q
        set arg18=%%r
        set arg19=%%s
        set arg20=%%t
        set arg21=%%u
        set arg22=%%v
        set arg23=%%w
        set arg24=%%x
        set arg25=%%y
        set arg26=%%z
        set /a currentLine+=1
        set /a loopid=!currentLine! + !rtid!
        set known=0

        rem ──────────────────────────────
        rem SKIP all of our DSL‐declaration lines
        rem anything that begins with "*" (like *FILETYPE)
        if "!arg1:~0,1!"=="*" (
            set known=1
        )
        
        rem skip "int", "type" & "fclass" declarations
        if /I "!arg1!"=="int"    set known=1
        if /I "!arg1!"=="type"   set known=1
        if /I "!arg1!"=="fclass" set known=1
        
        rem skip entire function bodies
        if /I "!arg1!"=="function" (
            set skipBlock=1
            set known=1
        )
        if defined skipBlock (
            rem exit skip mode when we see a lone "}"
            if /I "!arg1!"=="}" set skipBlock=
            set known=1
        )
        
        if "!known!"=="1" (
            rem we already “handled” (i.e. skipped) this line
            goto :afterLogic
        )
        
        rem ──────────────────────────────
        :afterLogic


        rem echo !currentLine!
        rem —————————————————————————————
        rem  Was this line a call to a captured function?
        if exist "%~dp0func_!arg1!.dsl" (
          rem push current context
          set "fileStack[%stack_level%]=!file!"
          set "lineStack[%stack_level%]=!currentLine!"
          set /a stack_level+=1

          rem map DSL parameters into %param:…% vars
          for /L %%i in (2,1,26) do (
            if defined arg%%i (
              set "param%%i=!arg%%i!"
            )
          )

          rem jump into the function’s file
          set "file=%~dp0func_!arg1!.dsl"
          set known=1
          rem reset currentLine so that the outer FOR/F calls the new file from its top
          set /a currentLine=0
        )

        rem Logic

        if /I "!arg1!" EQU "logical" (
            if /I "!arg2!" EQU "set" (
                 if /I "!arg3!" EQU "variable" (
                    set !arg4!=!arg6!
                    set known=1
                 )
            )
            if /I "!arg2!" EQU "compare" (
                if /I "!arg8!" EQU "and" (
                    if /I "!arg10!" EQU "true" (
                        if /I "!arg11!" EQU "true" (
                            set !arg5!=true
                            set known=1
                        ) else (
                            set !arg5!=true
                            set known=1
                        )
                    ) else (
                        set !arg5!=false
                        set known=1
                    )
                )
                if /I "!arg8!" EQU "or" (
                    if /I "!arg10!" EQU "true" (
                        set !arg5!=true
                        set known=1
                    ) else (
                    if /I "!arg11!" EQU "true" (
                        set !arg5!=true
                        set known=1
                    ) else (
                        set !arg5!=false
                        set known=1
                    )
                    )
                )
                if /I "!arg8!" EQU "not" (
                    if /I "!arg10!" EQU "true" (
                        set !arg5!=false
                        set known=1
                    ) else (
                        set !arg5!=true
                        set known=1
                    )
                )
            )
        )
        if /I "!arg1!" EQU "algebraic" (
            if /I "!arg2!" EQU "set" (
                if /I "!arg3!" EQU "variable" (
                    set /a !arg4!=!arg6!!arg7!!arg8!!arg9!!arg10!!arg11!!arg12!!arg13!!arg14!!arg15!!arg16!
                    set known=1
                )
            )
        )
        if /I "!arg1!" EQU "string" (
            if /I "!arg2!" EQU "set" (
                if /I "!arg3!" EQU "variable" (
                    set "!arg4!=!arg6!!arg7!!arg8!"
                    set known=1
                )
            )
        )
        if /I "!arg1!" EQU "general" (
            if /I "!arg2!" EQU "set" (
                if /I "!arg3!" EQU "variable" (
                    set !arg4!=!arg6!
                    set known=1
                )
                if /I "!arg3!" EQU "constant" (
                    setx !arg4! !arg6!
                    set known=1
                )
            )
        )
        if /I "!arg1!" EQU "print" (
            if /I "!arg2!" EQU "variable" (
                call echo %%!arg3!%%
                set known=1
            )
            if /I "!arg2!" EQU "text" (
                if /I "!arg3!" EQU "." (
                    echo.
                    set known=1
                ) else (
                    echo !arg3! !arg4! !arg5! !arg6! !arg7! !arg8! !arg9! !arg10! !arg11! !arg12!
                    set known=1
                )
            )
        )

        if /I "!arg1!" EQU "comment" (
            echo. >nul
            set known=1
        )

        if /I "!arg1!" EQU "name" (
            title !arg2!
            set known=1
        )

        if /I "!arg1!" EQU "if" (
            if /I "!arg2!" EQU "variable" (
                call :errordisplay "IF", "If statements not available in this version (!version!)"
                set known=1
            )
        )

        if /I "!arg1!" EQU "using" (
            if /I "!arg2!" EQU "resource" (
               set "resourceFile=%~dp0res\!arg3!.logical"
               if exist "!resourceFile!" (
                   call :errordisplay "USING", "Resource imports not allowed in this context"
                   set known=1
                   rem goto endfile
               ) else (
                   call :errordisplay "USING", "Resource file not found: '!resourceFile!'"
                   call :errordisplay "USING", "Resource imports not allowed in this context"
                   set known=1
                   rem goto endfile
               )
            )
            if /I "!arg2!" EQU "package" (
               set "pkg_file=%~dp0pkg\!arg3!.logical"
               if exist "!pkg_file!" (
                   call :errordisplay "USING", "Package imports not allowed in this context"
                   set known=1
                   rem goto endfile
               ) else (
                   call :errordisplay "USING", "Package File file not found: '!pkg_file!'"
                   call :errordisplay "USING", "Package imports not allowed in this context"
                   set known=1
                   rem goto endfile
               )
            )
        )
        if /I "!arg1!"=="return" (
          rem grab the return-value
          set "retVal=!arg2!"
          rem pop stack
          set /a stack_level-=1
          set "file=!fileStack[%stack_level%]!"
          set /a currentLine=!lineStack[%stack_level%]!
          set known=1
        )
        rem —————————————————————————————
        rem  Detect start of a DSL function
        if /I "!arg1!"=="function" (
          set "fnName=!arg2!"
          rem create a temp file for this function
          set "fnFile=%~dp0func_!fnName!.dsl"
          >"%fnFile%" echo :: %data%
          rem now read subsequent lines until a lone "}" appears
          setlocal disableDelayedExpansion
          for /f "usebackq delims=" %%L in ('more +!currentLine! "%initialFile%"') do (
            echo %%L>>"%fnFile%"
            echo %%L|findstr /R /X "}" >nul && goto :_fnDone
          )
          :_fnDone
          endlocal
          set known=1
        )
        if /I "!known!" EQU "0" (
            call :errordisplay "CRITICAL" , "!arg1! not available (DVAR_UNKNOWN)"
        )
    )
)
goto endfile


:endfile
set /a exec_time=0
set end=%time%
set options="tokens=1-4 delims=:.,"
for /f %options% %%a in ("%start%") do set start_h=%%a&set /a start_m=100%%b %% 100&set /a start_s=100%%c %% 100&set /a start_ms=100%%d %% 100
for /f %options% %%a in ("%end%") do set end_h=%%a&set /a end_m=100%%b %% 100&set /a end_s=100%%c %% 100&set /a end_ms=100%%d %% 100

set /a hours=%end_h%-%start_h%
set /a mins=%end_m%-%start_m%
set /a secs=%end_s%-%start_s%
set /a ms=%end_ms%-%start_ms%
if %ms% lss 0 set /a secs = %secs% - 1 & set /a ms = 100%ms%
if %secs% lss 0 set /a mins = %mins% - 1 & set /a secs = 60%secs%
if %mins% lss 0 set /a hours = %hours% - 1 & set /a mins = 60%mins%
if 1%ms% lss 100 set ms=0%ms%

set /a totalsecs = %hours%*3600 + %mins%*60 + %secs%
echo.
echo.
echo Executed in ~%totalsecs%.%ms%s
if /I "%waitprompt%" EQU "1" (
    pause
)
exit /b


:errordisplay
set type=%~1
set message=%~2
echo [91m!rtid! [!loopid!:!currentLine!] [ERROR !type!] !message![0m