FROM python:3.15.2-slim-trixie

COPY	./src ./
RUN 	pip install -r requirements.txt

# Build:
#	docker image build -t ziwritecards .

# Run:
#	docker run -it --rm -v ${PWD}/output/:/output/ -v ${PWD}/Fonts/:/Fonts/ ziwritecards python ziwritecards.py --text "你好世界学习成长" --output "/output/cards.pdf"
#	docker run -it --rm -v ${PWD}/output/:/output/ -v ${PWD}/Fonts/:/Fonts/ ziwritecards python ziwritecards.py --text "仁者爱人" --output "/output/cards.pdf"
#	docker run -it --rm -v ${PWD}/output/:/output/ -v ${PWD}/Fonts/:/Fonts/ ziwritecards python ziwritecards.py --text "见义勇为" --output "/output/cards.pdf"
#	docker run -it --rm -v ${PWD}/output/:/output/ -v ${PWD}/Fonts/:/Fonts/ ziwritecards python ziwritecards.py --text "礼尚往来" --output "/output/cards.pdf"
#	docker run -it --rm -v ${PWD}/output/:/output/ -v ${PWD}/Fonts/:/Fonts/ ziwritecards python ziwritecards.py --text "言而有信" --output "/output/cards.pdf"
#	docker run -it --rm -v ${PWD}/output/:/output/ -v ${PWD}/Fonts/:/Fonts/ ziwritecards python ziwritecards.py --text "大智若愚" --output "/output/cards.pdf"

