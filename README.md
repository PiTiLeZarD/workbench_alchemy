workbench_alchemy
=================

SQLAlchemy model creation for MySQL Workbench

### Want to see?

This:

<img src="example.png" alt="Example" style="width: 100%;"/>

On execution it should look like this:
```
Executing script /Users/xxx/Library/Application Support/MySQL/Workbench/scripts/sqlalchemy_grt.py...
--------------------
-- SQLAlchemy export v0.8
--------------------
 -> Working on customers
 -> Working on localities
 -> Working on invoices
Copied to clipboard

Script finished.

```

Then you just have to paste it somewhere, hopefully it looks like this:

```python
"""
This file has been automatically generated with workbench_alchemy v0.8
For more details please check here:
https://github.com/PiTiLeZarD/workbench_alchemy
"""

from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, FLOAT
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Customer(Base):
  __tablename__ = 'customers'
  
  id = Column( "id_customer", INTEGER, nullable=False, primary_key=True )
  name = Column( VARCHAR(45), index=True )
  id_locality = Column( "locality_id", INTEGER, ForeignKey("localities.id_locality", ondelete="CASCADE"), nullable=False, index=True )

  locality = relationship( "Locality", foreign_keys=[id_locality] )

  def __repr__( self ):
    return self.__str__()

  def __str__( self ):
    return '<Customer %(id)s>' % self.__dict__

class Locality(Base):
  __tablename__ = 'localities'
  
  id = Column( "id_locality", INTEGER, nullable=False, primary_key=True )
  name = Column( VARCHAR(45), unique=True )


  def __repr__( self ):
    return self.__str__()

  def __str__( self ):
    return '<Locality %(id)s>' % self.__dict__

class Invoice(Base):
  __tablename__ = 'invoices'
  
  id = Column( INTEGER, nullable=False, autoincrement=True, primary_key=True )
  total = Column( "amount", FLOAT )
  id_customer = Column( INTEGER, ForeignKey("customers.id_customer"), nullable=False, index=True )

  test = relationship( "Customer", foreign_keys=[id_customer], backref="testbackrefs" )

  def __repr__( self ):
    return self.__str__()

  def __str__( self ):
    return '<Invoice %(total)s %(id)s>' % self.__dict__
```