build: 
	docker build -t beacon_chain:latest .

deploy:	
	docker run -d --name beacon_chain_1 beacon_chain:latest sh -c "tail -f /dev/null"

test: 
	docker exec -it beacon_chain_1 pytest tests