@if "%DEBUG%"=="" @echo off
@rem ##########################################################################
@rem
@rem  Gradle startup script for Windows
@rem
@rem ##########################################################################

@rem Set local scope for the variables with windows NT shell
if "%OS%"=="Windows_NT" setlocal

@rem Get filename of script
set DIRNAME=%~dp0
if "%DIRNAME%"=="" set DIRNAME=.
@rem This variable is deprecated
set APP_BASE_NAME=%~n0
set APP_HOME=%DIRNAME%

@rem Resolve any "." and ".." in APP_HOME to make it shorter.
for %%i in ("%APP_HOME%") do set APP_HOME=%%~fi

@rem Add default JVM options here. You can also use JAVA_OPTS and GRADLE_OPTS to pass JVM options to this script.
set DEFAULT_JVM_OPTS=-Xmx64m -Xms64m

@rem Find java.exe
if defined JAVA_HOME goto findJavaFromJavaHome

set JAVA_EXE=java.exe
%JAVA_EXE% -version >NUL 2>&1
if "%ERRORLEVEL%"=="0" goto init

echo.
echo ERROR: JAVA_HOME is not defined and no 'java' command could be found in your PATH.
echo.
echo Please install a Java JDK (https://www.oracle.com/technetwork/java/javase/downloads).
echo Or set JAVA_HOME to point to an already installed Java JDK.
echo.
goto end

:findJavaFromJavaHome
set JAVA_HOME=%JAVA_HOME:"=%
set JAVA_EXE=%JAVA_HOME%/bin/java.exe

if exist "%JAVA_EXE%" goto init

echo.
echo ERROR: JAVA_HOME is set to an invalid directory: %JAVA_HOME%
echo.
echo Please set the JAVA_HOME variable in your environment to match the
location of your Java installation.
echo.
goto end

:init
@rem Get command-line arguments, handling Windows variants

if not "%OS%"=="Windows_NT" goto win9x_args

:win9x_args
@rem Slurp the command line arguments.
set CMD_LINE_ARGS=
:_loop
if "%1"=="" goto doneArgs
set CMD_LINE_ARGS=%*&goto :cmdInnerLoop
:cmdInnerLoop
shift
set CMD_LINE_ARGS=%CMD_LINE_ARGS% %1
shift
goto :_loop

:doneArgs
set CMD_LINE_ARGS=%CMD_LINE_ARGS:~1%

:execute
@rem Set up the command line
set CLASSPATH=%APP_HOME%\gradle\wrapper\gradle-wrapper.jar

@rem Execute Gradle
"%JAVA_EXE%" %DEFAULT_JVM_OPTS% %JAVA_OPTS% -classpath "%CLASSPATH%" org.gradle.wrapper.GradleWrapperMain %CMD_LINE_ARGS%

:end
@rem End local scope for the variables with Windows NT shell
if "%OS%"=="Windows_NT" endlocal

:done
@rem End script

@rem The following is necessary for Windows 9x/Me
:win9x_args
set CMD_LINE_ARGS=
:get_nxt_arg
if "%1"=="" goto doneArgs
shift
goto :get_nxt_arg

:eof