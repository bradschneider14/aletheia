import boto3
from boto3.dynamodb.conditions import Attr
from boto3.dynamodb.conditions import Key
import os
import json

class Dynamo:
    def __init__(self, url=None):
        self.url = url

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
            return s.client('dynamodb', endpoint_url=self.url)
        else:
            return s.client('dynamodb')

    def _get_resource(self):
        s = self._get_session()
        if self._IS_LOCAL:
            return s.resource('dynamodb', endpoint_url=self.url)
        else:
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

    def query_table(self, table_name, filter_expression, limit=1500):
        '''
        Submits the provided query against the table using the scan function (assumes not a key query). Returns the list of all
        matching items. Handles the pagination of scanning internally to the function.

        :param table: the table to query
        :param filter_expression: the dynamo filter expression
        '''
        response_items = []

        table = self.get_table(table_name)
        if table:
            should_continue = True
            last_evaluated = None
            
            the_kwargs = {"Limit": limit}
            if filter_expression:
                the_kwargs["FilterExpression"] = filter_expression

            while should_continue:
                if last_evaluated:
                   the_kwargs["ExclusiveStartKey"] = last_evaluated

                response = table.scan(**the_kwargs)
                response_items.extend(response.get('Items'))
                    
                last_evaluated = response.get("LastEvaluatedKey", None)
                # stop if there are no more queries
                if not last_evaluated or len(response_items) >= limit:
                    should_continue = False

        return response_items

    def get_query_expr(self, key, value, op='eq'):
        '''
        Build an implementation-specific query expression object
        '''
        if op == 'eq':
            if value == False or value == 'False':
                return Attr(key).eq(value) | Attr(key).not_exists()
            return Attr(key).eq(value)
        else:
            if value == True or value == 'True':
                return Attr(key).ne(value) | Attr(key).not_exists()
            return Attr(key).ne(value)
    
    def conjunctify_query(self, q1, q2):
        '''
        Return an implementation-specific query expression that combines the two expressions with 'and' logic
        '''
        return q1 & q2

    def query_by_id(self, table_name, key_name, key_val):
        '''
        Perform a query on the table for the item with primary key of given id. Returns at most one item.
        '''
        item = None
        table = self.get_table(table_name)
        if table:
            response = table.query(KeyConditionExpression=Key(key_name).eq(key_val))
            items = response.get('Items')
            if items and len(items) > 0:
                item = items[0]
        return items

    def update_item(self, table_name, item_id, values):
        table = self.get_table(table_name)
        if table:
            set_expr = ''
            val_map = {}
            val_counter = 0
            for ind, val_key in enumerate(values):
                set_expr += 'set ' if ind == 0 else ', '
                set_expr += f'{val_key}=:val_{val_counter}'
                val_map[f':val_{val_counter}'] = str(values[val_key])
                val_counter = val_counter + 1

            print(f'set expr: {set_expr}')
            print(f'val map: {val_map}')
            response = table.update_item(
                Key={
                    'id':item_id
                },
                UpdateExpression=set_expr,
                ExpressionAttributeValues=val_map,
                ReturnValues='UPDATED_NEW'
            )
            print(f'Response: {json.dumps(response)}')
            return {'attributes': response.get("Attributes", {})}


if __name__ == "__main__":
    import json
    from aletheia.annotations.provider import HDFProvider
    from aletheia.annotations.provider import DataSource
    from aletheia.annotations.provider import AnnotationSelector
    from aletheia.annotations.constants import AnnotationConstants

    # connect to the db
    dynamo = Dynamo('http://localhost:8000')
    
    t = dynamo.get_table(AnnotationConstants.ANNOTATION_TABLE_NAME)
    if t is None:
        print('Table does not exist. Creating it now.')
        t = dynamo.get_table(AnnotationConstants.ANNOTATION_TABLE_NAME, should_create=True)
        
        # load the data sources
        config = {}
        with open('config.json') as config_file:
            config = json.load(config_file) 

        ann_provider = HDFProvider()

        for annotation in config.get('annotation_sources', []):
            print(f'Adding annotation {annotation}')
            ann_provider.add_source(DataSource(annotation['location'], annotation['name']))

        # start submitting
        all_annotations = ann_provider.get_annotations(AnnotationSelector())
        for annotation in all_annotations:
            print(f'Inserting annotation {annotation["id"]}')
            t.put_item(Item=annotation)
    else:
        print('Table already exists. Delete it and re-run.')

        #print(t.key_schema)
        #response = t.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('id').eq('e7a64335-1b61-4f1f-a72c-935e7c4f3f41'))
        #response = t.update_item(
        #   Key={'id': 'e7a64335-1b61-4f1f-a72c-935e7c4f3f41'}, 
        #    UpdateExpression="SET verified = :true_val",
        #    ExpressionAttributeValues={':true_val':True},
        #    ReturnValues="UPDATED_NEW"
        #    )
        #print(f'update response: {response}')
        
        #response = t.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('id').eq('e7a64335-1b61-4f1f-a72c-935e7c4f3f41'))
        query_expr = dynamo.get_query_expr('verified', False)
        #query_expr = dynamo.conjunctify_query(query_expr, dynamo.get_query_expr('cons_verb', 'Object:Interact'))
        response = dynamo.query_table(AnnotationConstants.ANNOTATION_TABLE_NAME, query_expr)
        #response = dynamo.query_table(t, boto3.dynamodb.conditions.Attr('verified').eq(True))
        print(f'response: {response}')
        #print(f'{response["Items"]}')
