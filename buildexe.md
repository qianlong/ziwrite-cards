# Build manually

This is a step-by-step recipy to build the Windows executable from `Powershell`.

## Make the icon

This creates the `.ico` file from the original `.svg` image.

```bash
cd Icon
ConvertSvgToMultiResolutionIco.ps1
cd ..
```

## Build the windows executable

A docker image with "Wine" is used to build the Windows executable.

```bash
docker pull mymi14s/ubuntu-wine:24.04-3.11
docker run -it --rm --name wine --network=host -v ${PWD}/src/:/scripts/ -v ${PWD}/Icon/:/Icon/ -v ${PWD}/dist:/opt/wine/dist/ mymi14s/ubuntu-wine:24.04-3.11 bash
```

As we are unable to download dependencies from wine, we download them from python in advance...

```bash
python3 -m pip download -d /wheels -r /scripts/requirements.txt
```

... then, from "Wine", we install the wheels.

```bash
wine C:/Python311/python.exe -m pip install --no-index --find-links=Z:/wheels -r Z:/scripts/requirements.txt
```
Create the `.exe` file:

```bash
wine cmd /c "C:/Python311/python.exe -m PyInstaller --onefile --collect-all pypinyin --icon /Icon/Icon.ico /scripts/ziwritecards.py"
```

Exit the Docker environment:

```bash
exit
```

The Windows executable is available in `dist/ziwritecards.exe`.

## Run

```bash
.\dist\ziwritecards.exe --text "见义勇为" --output "./output/cards.pdf" --font_file_paths "./Fonts/I.Ming/I.Ming-8.10.ttf;./Fonts/Stkaiti/stkaiti.ttf"
```

The result file is created in `./output/cards.pdf`.