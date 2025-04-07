@echo off
setlocal ENABLEDELAYEDEXPANSION

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
    )
)
echo.
pause