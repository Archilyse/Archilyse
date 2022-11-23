import os

from sqlalchemy import MetaData
from sqlalchemy_schemadisplay import create_schema_graph

db_host = os.environ["PGBOUNCER_HOST"]
db_port = os.environ["PGBOUNCER_PORT"]
user = os.environ["POSTGRES_USER"]
password = os.environ["POSTGRES_PASSWORD"]
database = os.environ["POSTGRES_DB"]

# create the pydot graph object by autoloading all tables via a bound
# metadata object
graph = create_schema_graph(
    metadata=MetaData(f"postgresql://{user}:{password}@{db_host}:{db_port}/{database}"),
    show_datatypes=False,  # The image would get nasty big if we'd show
    #  the datatypes
    show_indexes=False,  # ditto for indexes
    rankdir="LR",  # From left to right (instead of top to bottom)
    concentrate=False,  # Don't try to join the relation lines together
)
folder = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
file_name = os.path.join(folder, "documentation/db_entities.png")
graph.write_png(file_name)
