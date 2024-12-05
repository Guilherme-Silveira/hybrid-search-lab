# hybrid-search-lab

## Summary

- [hybrid-search-lab](#hybrid-search-lab)
  - [Summary](#summary)
  - [Deploy Models from Hugging Face into Elasticsearch using Eland](#deploy-models-from-hugging-face-into-elasticsearch-using-eland)
  - [Create the inference API using the deployed model](#create-the-inference-api-using-the-deployed-model)
  - [Create the index and define the semantic\_text field mapping](#create-the-index-and-define-the-semantic_text-field-mapping)
  - [Ingest the data on the index](#ingest-the-data-on-the-index)

## Deploy Models from Hugging Face into Elasticsearch using Eland

Open the `import_model.sh` file and replace the value of the `--url`, `--es-username` and `--es-password` parameters with the actual value to connect and authenticate to your Elasticsearch cluster.

Execute the import script:

```bash
bash import_model.sh
```

## Create the inference API using the deployed model

On Kibana Dev Tools, execute:

```
PUT _inference/text_embedding/my-minilm-model
{
  "service": "elasticsearch",
  "service_settings": {
    "num_allocations": 1,
    "num_threads": 4,
    "model_id": "all-minilm-l12-v2"
  }
}
```

## Create the index and define the [semantic_text](https://www.elastic.co/guide/en/elasticsearch/reference/current/semantic-search-semantic-text.html) field mapping

```
PUT search-movies
{
  "mappings": {
    "dynamic": "true",
    "dynamic_templates": [
      {
        "all_text_fields": {
          "match_mapping_type": "string",
          "mapping": {
            "analyzer": "english",
            "fields": {
              "keyword": {
                "ignore_above": 2048,
                "type": "keyword"
              }
            }
          }
        }
      }
    ],
    "properties": {
      "title": {
        "type": "text",
        "copy_to": "title_vector"
      },
      "title_vector": {
        "type": "semantic_text",
        "inference_id": "my-minilm-model"
      },
      "overview": {
        "type": "text",
        "copy_to": "overview_vector"
      },
      "overview_vector": {
        "type": "semantic_text",
        "inference_id": "my-minilm-model"
      }
    }
  }
}
```

## Ingest the data on the index

On the terminal, execute the following steps to ingest the data located on the `movies-sample.json.gz` file in to Elasticsearch: 

- Create Python Virtual Environment

```bash
python3 -m venv venv
```

- Activate Virtual Environment and Install Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

- Execute Python Script (replace the `<es_user>`, `<es_password>` and `<es_url>` with the actual values of your Elasticsearch environment)

```bash
python ingest.py --es_password=<es_password> --es_url=<es_url> --es_user=<es_user>
```

- To verify if all documents were ingested on Elasticsearch, on Kibana Dev Tools, execute the following request (the result must be `302`):

```
GET search-movies/_count
```