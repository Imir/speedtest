import subprocess
import os
import json
import boto3
import datetime

from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

host = 'host.us-west-2.es.amazonaws.com'
region = 'us-west-2'

def test_speed():
    out_process = subprocess.Popen(['speedtest', '-f', 'json'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
    stdout, stderr = out_process.communicate()

    try:
        speed_test_result = json.loads(stdout)
        return speed_test_result
    except Exception as err:
        raise Exception(stdout)

def save_result(speed_test_result):
    date_today = datetime.date.today()
    index_name = f'speed_test_{date_today.year}_{date_today.month}_{date_today.day}'
    
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    
    es = Elasticsearch(
        hosts = [{'host': host, 'port': 443}],
        http_auth = awsauth,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )

    es.index(index=index_name, doc_type="_doc", body=speed_test_result)


if __name__ == "__main__":
    result_dir = os.path.join(os.getcwd(), 'results')

    # Retry to save previously failed test results
    if os.path.exists(result_dir):
        for f in os.listdir(result_dir):
            try:
                test_result_file_path = os.path.join(result_dir, f)

                with open(test_result_file_path) as json_file:
                    speed_test_result = json.load(json_file)
                    save_result(speed_test_result)

                os.remove(test_result_file_path)
            except Exception as err:
                print(err)

    try:
        speed_test_result = test_speed()
        
        try:
            save_result(speed_test_result)
        except Exception as err:
            print(err)

            if not os.path.exists(result_dir):
                os.mkdir(result_dir)
                
            with open(os.path.join(result_dir, speed_test_result['result']['id'] + '.json'), 'w') as out:
                json.dump(speed_test_result, out)

    except Exception as err:
        print(err)

    