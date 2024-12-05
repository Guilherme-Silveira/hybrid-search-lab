docker run -it --rm docker.elastic.co/eland/eland:8.15.0 \
eland_import_hub_model \
--url https://meetup.es.southamerica-east1.gcp.elastic-cloud.com \
--es-username elastic \
--es-password changeme \
--hub-model-id sentence-transformers/all-MiniLM-L12-v2 \
--es-model-id all-minilm-l12-v2 \
--task-type text_embedding \
--start

docker run -it --rm docker.elastic.co/eland/eland:8.15.0 \
eland_import_hub_model \
--url https://meetup.es.southamerica-east1.gcp.elastic-cloud.com \
--es-username elastic \
--es-password changeme \
--hub-model-id cross-encoder/ms-marco-MiniLM-L-6-v2 \
--task-type text_similarity \
--start