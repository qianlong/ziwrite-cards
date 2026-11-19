docker run --rm `
    --name ziwritecardsbuild `
    -v ${PWD}/dist:/opt/wine/dist/ `
    -v ${PWD}/src:/src/ `
    -v ${PWD}/Icon:/Icon `
    mymi14s/ubuntu-wine:24.04-3.11 `
bash -c '
    python3 -m pip install --break-system-packages -r /src/requirements.txt
    python3 -m pip download -d /wheels -r /src/requirements.txt 
    wine C:/Python311/python.exe -m pip install --no-index --find-links=Z:/wheels -r Z:/src/requirements.txt
    wine cmd /c "C:/Python311/python.exe -m PyInstaller --onefile --collect-all pypinyin --icon /Icon/Icon.ico /src/ziwritecards.py"
'