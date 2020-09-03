import boto3
import os

class Dynamo:
    def __init__(self):
        self._IS_LOCAL = bool(os.environ.get('DYN_LOCAL', False))
        self._AWS_KEY = os.environ['DYN_KEY'] if not self._IS_LOCAL else 'localkey'
        self._AWS_SECRET = os.environ['DYN_SECRET'] if not self._IS_LOCAL else 'localsecret'
        
        self._REGION = 'us-east-2'
        self._session = None

    def _is_local(self):
        return bool(os.environ.get("DYN_LOCAL", False))

    def _get_session(self):
        if not self._session:
            self._session = boto3.Session(aws_access_key_id=self._AWS_KEY, aws_secret_access_key=self._AWS_SECRET, region_name=self._REGION)
        return self._session

    def _get_client(self):
        s = self._get_session()
        if self._IS_LOCAL:
            return s.client('dynamodb', endpoint_url='http://localhost:8000')
        return s.client('dynamodb')        

    def _get_resource(self):
        s = self._get_session()
        if self._IS_LOCAL:
            return s.resource('dynamodb', endpoint_url='http://localhost:8000')
        return s.resource('dynamodb')

    def get_table(self, table_name, should_create=False):
        table_found = False
        table = None

        client = self._get_client()
        tables_list = client.list_tables()
        # output is paginated so continue requesting starting with the previous end if necessary
        while True:
            if table_name in tables_list.get('TableNames', []):
                table_found = True
                break
            
            last_table = tables_list.get('LastEvaluatedTableName')
            if last_table:
                tables_list = client.list_tables(ExclusiveStartTableName=last_table)
            else:
                break

        if table_found:
            table = self._get_resource().Table(table_name)
        elif should_create:
            # need to create table
            table = self._get_resource().create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName':'id',
                        'KeyType':'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName':'id',
                        'AttributeType':'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        return table       
        

if __name__ == "__main__":
    import json
    from aletheia.annotations.provider import HDFProvider
    from aletheia.annotations.provider import DataSource
    from aletheia.annotations.provider import AnnotationSelector

    # load the data sources
    config = {}
    with open('config.json') as config_file:
        config = json.load(config_file) 

    ann_provider = HDFProvider()

    for annotation in config.get("annotation_sources", []):
        print(f'Adding annotation {annotation}')
        ann_provider.add_source(DataSource(annotation['location'], annotation['name']))

    # connect to the db
    dynamo = Dynamo()
    
    t = dynamo.get_table('test_table')
    if t is None:
        print('Table does not exist. Creating it now.')
        t = dynamo.get_table('test_table', should_create=True)
        
        all_annotations = ann_provider.get_annotations(AnnotationSelector())
        for annotation in all_annotations:
            print(f'Inserting annotation {annotation["id"]}')
            t.put_item(Item=annotation)
    else:
        print('Table already exists.')
        

    