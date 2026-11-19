docker pull mymi14s/ubuntu-wine:24.04-3.11
docker run -it --rm --name wine --network=host -v ${PWD}/src/:/scripts/ -v ${PWD}/Icon/:/Icon/ -v ${PWD}/dist:/opt/wine/dist/ mymi14s/ubuntu-wine:24.04-3.11 bash

# As we are unable to download dependencies from wine, we download them from python in advance...
python3 -m pip download -d /wheels -r /scripts/requirements.txt

# ... then, from wine, we install the wheels.
wine C:/Python311/python.exe -m pip install --no-index --find-links=Z:/wheels -r Z:/scripts/requirements.txt

wine cmd /c "C:/Python311/python.exe -m PyInstaller --onefile --collect-all pypinyin --icon /Icon/Icon.ico /scripts/ziwritecards.py"

exit

cd dist

.\ziwritecards.exe --text "见义勇为" --output "../output/cards.pdf" --font_file_paths "../Fonts/I.Ming/I.Ming-8.10.ttf;../Fonts/Stkaiti/stkaiti.ttf"