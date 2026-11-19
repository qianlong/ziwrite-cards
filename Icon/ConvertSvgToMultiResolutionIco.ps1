docker run --rm -it --entrypoint=magick -v ${PWD}:/img dpokidov/imagemagick convert -background none -resize 5126x512 /img/Icon.svg /img/Icon-512.png
docker run --rm -it --entrypoint=magick -v ${PWD}:/img dpokidov/imagemagick convert -background none -resize 256x256 /img/Icon.svg /img/Icon-256.png
docker run --rm -it --entrypoint=magick -v ${PWD}:/img dpokidov/imagemagick convert -background none -resize 128x128 /img/Icon.svg /img/Icon-128.png
docker run --rm -it --entrypoint=magick -v ${PWD}:/img dpokidov/imagemagick convert -background none -resize 64x64 /img/Icon.svg /img/Icon-64.png
docker run --rm -it --entrypoint=magick -v ${PWD}:/img dpokidov/imagemagick convert -background none -resize 48x48 /img/Icon.svg /img/Icon-48.png
docker run --rm -it --entrypoint=magick -v ${PWD}:/img dpokidov/imagemagick convert -background none -resize 32x32 /img/Icon.svg /img/Icon-32.png
docker run --rm -it --entrypoint=magick -v ${PWD}:/img dpokidov/imagemagick convert -background none -resize 24x24 /img/Icon.svg /img/Icon-24.png
docker run --rm -it --entrypoint=magick -v ${PWD}:/img dpokidov/imagemagick convert -background none -resize 16x16 /img/Icon.svg /img/Icon-16.png

docker run --rm -it --entrypoint=convert -v ${PWD}:/img dpokidov/imagemagick /img/Icon-512.png /img/Icon-256.png /img/Icon-128.png /img/Icon-64.png /img/Icon-48.png /img/Icon-32.png /img/Icon-24.png /img/Icon-16.png /img/Icon.ico