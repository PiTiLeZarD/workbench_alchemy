Disclaimer
==========

After years of inactivity, I found myself needing this project again. I'm surprised it still kinda works.

TODO:
 - Check pull request and include the multi column indices if needed



workbench_alchemy
=================

SQLAlchemy model creation for MySQL Workbench

By default, you'll be using the general sqlalchemy dialect. If you want to have a MySQL/MariaDB specific dialect, you can do so by
updating the env variable DB_TYPE

```
import os
os.environ['DB_TYPE'] = 'MySQL'

from mypackage.db.schema import MyClass  # this will use the mysql dialects
```

### How to execute example.mwb file?
- Open MYSQL Workbench;
- Find & Open `example.mwb`;
- In Menubar, choose `Scripting`->`Run Workbench Script File`(`⇧+⌘+R` in os x)
- Select `sqlalchemy_grt.py` and done.

### Want to see?

This:

<img src="example.png" alt="Example" style="width: 100%;"/>

On execution it should look like this:
```
> run
 -> Working on customers
 -> Working on localities
 -> Working on invoices
--------------------
-- SQLAlchemy export v0.3
--------------------
Copied to clipboard
Execution finished
```

Then you just have to paste it somewhere, hopefully it looks like this:

```python
"""
This file has been automatically generated with workbench_alchemy v0.3
For more details please check here:
https://github.com/PiTiLeZarD/workbench_alchemy
"""

import os
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

if os.environ.get('DB_TYPE', 'MySQL') == 'MySQL':
    from sqlalchemy.dialects.mysql import INTEGER, FLOAT, VARCHAR, DATETIME
else:
    from sqlalchemy import DateTime as DATETIME, Integer, Float as FLOAT, String as VARCHAR

    class INTEGER(Integer):
        def __init__(self, *args, **kwargs):
            super(Integer, self).__init__()  # pylint: disable=bad-super-call


DECLARATIVE_BASE = declarative_base()


class Customer(DECLARATIVE_BASE):

    __tablename__ = 'customers'
    __table_args__ = (
        UniqueConstraint("name", "email", name="index2"),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    id = Column(  # pylint: disable=invalid-name
        "id_customer", INTEGER(unsigned=True), autoincrement=False, primary_key=True, nullable=False
    )
    id_locality = Column(
        "locality_id", INTEGER(unsigned=True),
        ForeignKey("localities.id_locality", ondelete="CASCADE", name="fk_customers_localities"), index=True,
        nullable=False
    )
    name = Column(VARCHAR(45))
    email = Column(VARCHAR(45))
    date_created = Column(DATETIME, default=datetime.datetime.utcnow)
    date_updated = Column(DATETIME, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    locality = relationship("Locality", foreign_keys=[id_locality], backref="customers")

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "<Customer(%(id)s)>" % self.__dict__


class Locality(DECLARATIVE_BASE):

    __tablename__ = 'localities'
    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    id = Column(  # pylint: disable=invalid-name
        "id_locality", INTEGER(unsigned=True), autoincrement=False, primary_key=True, nullable=False
    )
    name = Column(VARCHAR(45), unique=True)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "<Locality(%(id)s)>" % self.__dict__


class Invoice(DECLARATIVE_BASE):

    __tablename__ = 'invoices'
    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'sqlite_autoincrement': True, 'mysql_charset': 'utf8'}
    )

    id = Column(  # pylint: disable=invalid-name
        INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False
    )
    id_customer = Column(
        INTEGER(unsigned=True), ForeignKey("customers.id_customer", name="fk_invoices_customers1"), index=True,
        nullable=False
    )
    total = Column("amount", FLOAT)

    customer = relationship("Customer", foreign_keys=[id_customer], backref="invoices")

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "<Invoice(%(id)s, %(total)s)>" % self.__dict__

```

### List of options

I started to add options here and there, it's probably a good idea to keep track of it!

Options are done in the comment part of fields/tables on the form:
```
optname=optvalue,optname=optvalue...
```

#### Option on the table

 * norelations will disable all relations for this table (should update that to relations=False)
 * abstract will create a tablename-less abstract class

#### Option on the fields

 * relation=False : disable relationship for this column
 * backref=False : disables backref for this relationship
 * uselist=False : handled the relationship as a scalar instead of a list
 * backrefuselist=False : same as uselist except applied to the backref
 * backrefname=myName : rename the backref in the relationship
 * fkname=myName : rename the relationship itself
 * alias=myName : rename the column mapping name (DB keeps whatever the name in the schema is)
 * toprint=True : (or False) controls what's printed when using print str(myObject)
 * default works as ```default=%s``` which means you can put ```"THIS STUFF"``` as default but also ```datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow```

## Structure of code

Or rather a suggestion, this is how I use it:
```
./mylib/db/schema.py <-- I will describe this file
./mylib/db/auto/__init__.py
./mylib/db/auto/schema.py <- I copy bluntly here the result of the script
```

So about the schema file in mylib/db/schema, here is a possibile implementation which works for me:
``` python

import sqlalchemy
from sqlalchemy.orm import sessionmaker, scoped_session

from mylib.db.auto.schema import *

SESSION = None

def connect(dburi=None, **kwargs):
    dburi = dburi or 'sqlite:///'
    createtable = False
    if 'createtable' in kwargs:
        createtable = kwargs.pop('createtable')

    engine_params = {'pool_size': 5, 'pool_recycle': 3600}
    if dburi.startswith('sqlite'):
        engine_params = {}

    engine = sqlalchemy.create_engine(dburi, **engine_params)
    connection = engine.connect()

    if dburi.startswith('sqlite'):
        connection.connection.connection.text_factory = str

    session = scoped_session(sessionmaker(**kwargs))
    session.configure(bind=engine)

    if createtable:
        DECLARATIVE_BASE.metadata.create_all(engine)
        if 'autocommit' not in kwargs:
            session.commit()

    return session

if __name__ == '__main__':
    SESSION = connect(createtable=True)
    SESSION.commit()
```

So this leaves you with the possibility of creating the database by just calling:
``` bash
$ python mylib/db/schema.py
```

You can also extend the classes easily in this schema file. Though, I don't use standard inheritence 
but more extensions of objects like this:

``` python
def myFunction(self, *args, **kwargs):
    self.myfield = kwargs.get('myfield', None)
Customer.myFunction = myFunction
```

### Using SQLite in your tests? No dramas:

Just add those lines at the top of your test files:

``` python
import mylib.db.auto
mylib.db.auto.USE_MYSQL_TYPES = False
```

and you're good to go

## Tests

```
mkvirtualenv workbench_alchemy
pip install nose mock
nosetests tests.py
```

If you want coverage:
```
pip install coverage
nosetests --with-coverage tests.py 2>&1 | grep sqlalchemy
```

Which currently outputs:
```
sqlalchemy_grt.py                  325     19    94%
```
