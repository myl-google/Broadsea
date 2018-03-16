"""This is used to generate the deployment manager config for the CDM tables and OHDSI tables.

To re-generate the tables:
- edit ohdsi.jinja and remove all the biguery tables at the end
- download a release of the common data model at https://github.com/OHDSI/CommonDataModel/releases 
- unzip the release and set the CDM_PATH environment variable to point at the directory
- run: python create_bigquery_deployment.py -d cdmDataset -s ${CDM_PATH?}/PostgreSQL/OMOP\ CDM\ postgresql\ ddl.txt >> ohdsi.jinja
  - Optional: append -b to the above command if you want to update the BigQuery schema files as well.
- ssh to the deployed vm and run the following:
  docker exec -i -t ${BROADSEA_WEBTOOLS_CONTAINER_ID?} pg_dump "host=${POSTGRES_HOST_IP} dbname=postgres user=postgres password=ohdsi" > ~/ohdsi.sql
- on your workstation:
  gcloud beta compute scp --zone us-central1-a ohdsi-deployment-vm:~/ohdsi.sql .
  python create_bigquery_deployment.py -d ohdsiDataset -s ohdsi.sql -w ../results_tables_whitelist.txt >> ohdsi.jinja
"""

import getopt
import sys
import json

USAGE = (sys.argv[0] +
         " -d <bigquery_dataset>"
         " -s <sql_file>"
         " [-w <comma_separated_whitelist>]"
         " [-b]")

dataset=''
sql=''
whitelist=set()
bq_schema=False
try:
  opts, args = getopt.getopt(sys.argv[1:],"hp:d:s:w:b",
                             ["dataset=", "sql=", "whitelist=", "bq_schema"])
  for opt, arg in opts:
    if opt == '-h':
      print USAGE
      sys.exit()
    elif opt in ("-d", "--dataset"):
      dataset = arg
    elif opt in ("-s", "--sql"):
      sql = arg
    elif opt in ("-w", "--whitelist"):
      whitelist = set(open(arg).read().split("\n"))
    elif opt in ("-b", "--bq_schema"):
      bq_schema = True
  if len(dataset) == 0 or len(sql) == 0:
    print USAGE
    sys.exit(1)
except getopt.GetoptError:
  print USAGE
  sys.exit(1)

sql_commands = open(sql).readlines()

def generate_schema(table_name, table_columns):
  """
  Generates BigQuery schema for a table as a JSON file.

  @param table_name: the name of the table
  @param table_columns: a list of tuples of column name and type
  """
  schema = map(lambda c: {'name': c[0], 'type': c[1].upper()}, table_columns)
  with open("schema/%s.json" % table_name, 'w') as f:
    f.write(json.dumps(schema, sort_keys=True, indent=4, separators=(',', ': ')))

TABLE_TEMPLATE = """- name: %s_%s
  type: bigquery.v2.table
  metadata:
    dependsOn:
    - %sResource
  properties:
    datasetId: {{ properties['%s'] }}
    tableReference:
      tableId: %s
    schema:
      fields:"""

table_name = None
table_columns = []
for line in sql_commands:
    words = line.split()
    if table_name:
        if words[0] == ");" or words[0] == ")" or words[0] ==";":
          print TABLE_TEMPLATE % (dataset, table_name, dataset, dataset, table_name)
          print "\n".join(map(
            lambda c: "      - name: %s\n        type: %s" % (c[0], c[1]),
            table_columns))
          if bq_schema: generate_schema(table_name, table_columns)
          table_name = None
          table_columns = []
          continue
        if words[0] == "(": continue
        column_type = words[1].lower()
        if column_type[-1] == ',': column_type = column_type[:-1]
        if column_type.find('(') != -1: column_type = column_type.split('(')[0]
        if (column_type == "bigint"): t = "integer"
        elif (column_type == "integer"): t = "integer"
        elif (column_type == "timestamp"): t = "timestamp"
        elif (column_type == "character"): t = "string"
        elif (column_type == "varchar"): t = "string"
        elif (column_type == "text"): t = "string"
        elif (column_type == "char"): t = "string"
        elif (column_type == "double"): t = "float"
        elif (column_type == "numeric"): t = "float"
        elif (column_type == "date"): t = "date"
        else: assert False, "Unknown type: %s" % column_type
        table_columns.append((words[0], t))
    elif len(words) >= 2 and words[0] == 'CREATE' and words[1] == 'TABLE':
      if len(whitelist) == 0 or words[2] in whitelist:
        table_name = words[2]