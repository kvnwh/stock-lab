start-db:
	docker-compose up -d

# source:
# 	source .venv/bin/activate
start:
	waitress-serve webapp:app