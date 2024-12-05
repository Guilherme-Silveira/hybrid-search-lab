from flask import Flask, request, jsonify
import os
from elasticsearch import Elasticsearch
from elasticsearch.client import SearchApplicationClient
import logging

ES_URL = os.environ["ES_URL"]
ES_USER = os.environ["ELASTICSEARCH_USERNAME"]
ES_PASSWORD = os.environ["ELASTICSEARCH_PASSWORD"]
logging.basicConfig(
    level=logging.DEBUG,                 # Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Define the log format
    handlers=[
        logging.FileHandler("app.log"),  # Write logs to a file called 'app.log'
        logging.StreamHandler()          # Also print logs to the console
    ]
)

client = SearchApplicationClient(Elasticsearch(hosts=ES_URL, basic_auth=(ES_USER, ES_PASSWORD)))


datasets = {
    "movies": {
        "id": "movies",
        "label": "Movies",
        "index": "search-movies",
        "search_fields": ["title"],
        "semantic_search_field": "title_vector",
        "result_fields": ["title", "overview"],
        "mapping_fields": {"text": "overview", "title": "title"},
    }
}

app = Flask(__name__)


@app.route("/api/search/<index>")
def route_api_search(index):
    """
    Execute the search
    """
    [query, hybrid, type, k, datasetId] = [
        request.args.get("q"),
        request.args.get("hybrid", default=False, type=lambda v: v.lower() == "true"),
        request.args.get("type", default="bm25"),
        request.args.get("k", default=0),
        request.args.get("dataset", default="movies"),
    ]

    if type == "semantic":
        search_result = run_semantic_search(
            query, index, **{"hybrid": hybrid, "k": k, "dataset": datasetId}
        )
    elif type == "bm25":
        search_result = run_full_text_search(query, index, **{"dataset": datasetId})


    transformed_search_result = transform_search_response(
        search_result, datasets[datasetId]["mapping_fields"]
    )
    return jsonify(response=transformed_search_result)


@app.route("/api/datasets", methods=["GET"])
def route_api_datasets():
    """
    Return the available datasets
    """
    return datasets


@app.errorhandler(404)
def resource_not_found(e):
    """
    Return a JSON response of the error and the URL that was requested
    """
    return jsonify(error=str(e)), 404



def get_semantic_request_body(query, size=10, **options):
    """
    Generates an ES semantic search request.
    """

    fields = datasets[options["dataset"]]["result_fields"]
    search_field = datasets[options["dataset"]]["semantic_search_field"]
    return {
        "params": { "query_string" : query }
    }


def get_hybrid_request_body(query, size=10, **options):
    """
    Generates an ES semantic search request.
    """

    fields = datasets[options["dataset"]]["result_fields"]
    semantic_search_field = datasets[options["dataset"]]["semantic_search_field"]
    search_fields = datasets[options["dataset"]]["search_fields"]
    return {
        "params": { "query_string" : query }
    }


def get_text_search_request_body(query, size=10, **options):
    """
    Generates an ES full text search request.
    """
    fields = datasets[options["dataset"]]["result_fields"]
    search_fields = datasets[options["dataset"]]["search_fields"]
    return {
        "params": { "query_string" : query }
    }


def execute_search_request(index, body, search_app):
    """
    Executes an ES search request and returns the JSON response.
    """
    logging.info("execute_search_request");
    logging.info(body);

    response = client.search(
        name = search_app,
        body=body
    )

    return response


def execute_search_request_using_raw_dsl(index, body):
    """
    Executes an ES search request using the request library and returns the JSON response.
    """
      
    response = client.perform_request(
        "POST",
        f"/{index}/_search",
        headers={"content-type": "application/json", "accept": "application/json"},
        body=body,
    )

    return response


def run_full_text_search(query, index, **options):
    """
    Runs a full text search on the given index using the passed query.
    """
    if query is None or query.strip() == "":
        raise Exception("Query cannot be empty")
    body = get_text_search_request_body(query, **options)
    search_app = "text-search"
    response = execute_search_request(index, body, search_app)

    return response["hits"]["hits"]


def run_semantic_search(query, index, **options):
    """
    Runs a semantic search of the provided query on the target index, and reranks the KNN and BM25 results.
    """

    if options.get("hybrid") == True:
        logging.info("hybrid search");
        body = get_hybrid_request_body(query, **options)
        search_app = "hybrid-search"
        # Execute the request using the raw DSL to avoid the ES Python client since sub_searches query are not supported yet
        response_json = execute_search_request(index, body, search_app)
    else:
        body = get_semantic_request_body(query, **options)
        logging.info("body");
        logging.info(body);
        search_app = "semantic-search"
        response_json = execute_search_request(index, body, search_app)

    return response_json["hits"]["hits"]



def find_id_index(id: int, hits: list):
    """
    Finds the index of an object in `hits` which has _id == `id`.
    """

    for i, v in enumerate(hits):
        if v["_id"] == id:
            return i + 1
    return 0


def transform_search_response(searchResults, mappingFields):
    for hit in searchResults:
        fields = hit["fields"]
        hit["fields"] = {
            "text": fields[mappingFields["text"]],
            "title": fields[mappingFields["title"]],
        }
    return searchResults
