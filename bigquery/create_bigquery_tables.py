import getopt
import sys
import os

USAGE = (sys.argv[0] +
         " -p <project_id> -d <bigquery_dataset>"
         " -s <sql_file>"
         " [-w <comma_separated_whitelist>]")

project=''
dataset=''
sql=''
whitelist=set()
try:
  opts, args = getopt.getopt(sys.argv[1:],"hp:d:s:w:",
                             ["project=","dataset=", "sql=", "whitelist="])
  for opt, arg in opts:
    if opt == '-h':
      print USAGE
      sys.exit()
    elif opt in ("-p", "--project"):
      project = arg
    elif opt in ("-d", "--dataset"):
      dataset = arg
    elif opt in ("-s", "--sql"):
      sql = arg
    elif opt in ("-w", "--whitelist"):
      whitelist = set(open(arg).read().split("\n"))
  if len(project) == 0 or len(dataset) == 0 or len(sql) == 0:
    print USAGE
    sys.exit(1)
except getopt.GetoptError:
  print USAGE
  sys.exit(1)

sql_commands = open(sql).readlines()

table_name = None
table_columns = []
for line in sql_commands:
    words = line.split()
    if table_name:
        if words[0] == ");" or words[0] == ")" or words[0] ==";":
            table_schema = ','.join(table_columns)
            os.system('bq --project_id=%s rm -f %s.%s' % (project,
                                                          dataset,
                                                          table_name))
            print "Creating %s with schema %s" % (table_name, table_schema)
            os.system('bq --project_id=%s mk %s.%s %s' % (project,
                                                          dataset,
                                                          table_name,
                                                          table_schema))
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
        table_columns.append(words[0] + ":" + t)
    elif len(words) >= 2 and words[0] == 'CREATE' and words[1] == 'TABLE':
      if len(whitelist) == 0 or words[2] in whitelist:
        table_name = words[2]
