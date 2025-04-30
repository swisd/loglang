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

:interpret
for /f "tokens=1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26 delims= " %%a in ("!file!") do (
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
    set currentLine+=1
    echo !currentLine!


    rem Logic

    if /I "!arg1!" EQU "logical" (
        if /I "!arg2!" EQU "set" (
             if /I "!arg3!" EQU "variable" (
                set !arg4!=!arg6!
             )
        )
        if /I "!arg2!" EQU "compare" (
            if /I "!arg8!" EQU "and" (
                if /I "!arg10!" EQU "true" (
                    if /I "!arg11!" EQU "true" (
                        set !arg5!=true
                    ) else (
                        set !arg5!=true
                    )
                ) else (
                    set !arg5!=false
                )
            )
            if /I "!arg8!" EQU "or" (
                if /I "!arg10!" EQU "true" (
                    set !arg5!=true
                ) else (
                if /I "!arg11!" EQU "true" (
                    set !arg5!=true
                ) else (
                    set !arg5!=false
                )
                )
            )
            if /I "!arg8!" EQU "not" (
                if /I "!arg10!" EQU "true" (
                    set !arg5!=false
                ) else (
                    set !arg5!=true
                )
            )
        )
    )
    if /I "!arg1!" EQU "algebraic" (
        if /I "!arg2!" EQU "set" (
            if /I "!arg3!" EQU "variable" (
                set /a !arg4!=!arg6!!arg7!!arg8!!arg9!!arg10!!arg11!!arg12!!arg13!!arg14!!arg15!!arg16!
            )
        )
    )
    if /I "!arg1!" EQU "string" (
        if /I "!arg2!" EQU "set" (
            if /I "!arg3!" EQU "variable" (
                set "!arg4!=!arg6!!arg7!!arg8!"
            )
        )
    )
    if /I "!arg1!" EQU "general" (
        if /I "!arg2!" EQU "set" (
            if /I "!arg3!" EQU "variable" (
                set !arg4!=!arg6!
            )
            if /I "!arg3!" EQU "constant" (
                setx !arg4! !arg6!
            )
        )
    )
    if /I "!arg1!" EQU "print" (
        if /I "!arg2!" EQU "variable" (
            call echo %%!arg3!%%
        )
        if /I "!arg2!" EQU "text" (
            if /I "!arg3!" EQU "." (
                echo.
            ) else (
                echo !arg3! !arg4! !arg5! !arg6! !arg7! !arg8! !arg9! !arg10! !arg11! !arg12!
            )
        )
    )

    if /I "!arg1!" EQU "comment" (
        echo. >nul
    )

    if /I "!arg1!" EQU "name" (
        title !arg2!
    )
    echo [DEBUG INTERPRET - BEFORE USING] arg1: "!arg1!", currentFile: "!currentFile!"
    if /I "!arg1!" EQU "using" (
        echo [DEBUG USING - ENTERED] currentFile: "!currentFile!"
        if /I "!arg2!" EQU "resource" (
        echo [DEBUG USING - RESOURCE FILE]: "!resourceFile!"
           rem     start /wait %~dp0tmpinterpreter.bat "%~dp0res\!arg3!.logical"
           set "resourceFile=%~dp0res\!arg3!.logical"
           if exist "!resourceFile!" (
               set "fileStack[%stack_level%]=!currentFile!"
               set "returnLine[%stack_level%]=!lineNumber!"
               set /a stack_level+=1
               set "currentLine[!resourceFile!]=1"
               set "currentFile=!resourceFile!"
               goto process_line_start
           ) else (
            echo [ERROR USING] Resource file not found: "!resourceFile!"
           )
        )
        if /I "!arg2!" EQU "package" (
                start /wait %~dp0tmpinterpreter.bat "%~dp0pkg\!arg3!.logical"
           set "pkg_file=%~dp0pkg\!arg3!.logical"
           if exist "!pkg_file!" (
               set "stack[!stack_level!]=!file!"
               set /a stack_level+=1
               set "file=!pkg_file!"
               goto check_stack
           ) else (
               echo Error: Package file "!pkg_file!" could not be found.
           )
        )
    )

)
