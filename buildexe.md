# Build

This is a step-by-step recipy to build the Windows executable from `Powershell`, using "Docker".

## Make the icon

This creates the `.ico` file from the original `.svg` image, using the "dpokidov/imagemagick" docker image for "ImageMagick".

```bash
cd Icon
.\ConvertSvgToMultiResolutionIco.ps1
cd ..
```

## Build the windows executable

### Automatic build

The following powershell command bulds the Windows executable, using: the "mymi14s/ubuntu-wine:24.04-3.11" docker image for "Wine"

```bash
.\Build.ps1
```

### "Manual" build

The Docker image "mymi14s/ubuntu-wine:24.04-3.11" for "Wine" is used to build the Windows executable.

Run the container in Docker:

```bash
docker pull mymi14s/ubuntu-wine:24.04-3.11
docker run -it --rm --name wine --network=host -v ${PWD}/src/:/src/ -v ${PWD}/Icon/:/Icon/ -v ${PWD}/dist:/opt/wine/dist/ mymi14s/ubuntu-wine:24.04-3.11 bash
```

As we are unable to download dependencies from wine, we download them from python in advance...

```bash
python3 -m pip download -d /wheels -r /src/requirements.txt
```

... then, from "Wine", we install the wheels.

```bash
wine C:/Python311/python.exe -m pip install --no-index --find-links=Z:/wheels -r Z:/src/requirements.txt
```
Create the `.exe` file:

```bash
wine cmd /c "C:/Python311/python.exe -m PyInstaller --onefile --collect-all pypinyin --icon /Icon/Icon.ico /src/ziwritecards.py"
```

Exit the Docker environment:

```bash
exit
```

The Windows executable is available in `dist/ziwritecards.exe`.

## Run

### Run the Windows executable

```bash
.\dist\ziwritecards.exe --text "见义勇为" --output "./output/cards.pdf" --font_file_paths "./Fonts/I.Ming/I.Ming-8.10.ttf;./Fonts/Stkaiti/stkaiti.ttf"
```

The result file is created in `./output/cards.pdf`.

### Run in a Docker container

Build the image:

```bash
docker image build -t ziwritecards .
```

Run the container:

```bash
docker run -it --rm -v ${PWD}/output/:/output/ -v ${PWD}/Fonts/:/Fonts/ ziwritecards python ziwritecards.py --text "你好世界学习成长" --output "/output/cards.pdf"
```
