FRONT = 0.29
BACK = 0.15


default:
	echo "HI"

front:
	docker build -f Dockerfile.front -t mons-front:v${FRONT} --platform linux/amd64   .
	docker tag mons-front:v${FRONT} ${YOUR_REPO}/mons/front:v${FRONT}
	docker push ${YOUR_REPO}/mons/front:v${FRONT}
back: 
	docker build -f Dockerfile.back -t mons-back:v${BACK} --platform linux/amd64   .
	docker tag mons-back:v${BACK} ${YOUR_REPO}/mons/back:v${BACK}
	docker push ${YOUR_REPO}/mons/back:v${BACK}
