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
-- SQLAlchemy export v0.3
--------------------
 -> Working on customers
 -> Working on localities
Copied to clipboard

Script finished.

```

Then you just have to paste it somewhere, hopefully it looks like this:

```python
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Customer(Base):
  __tablename__ = 'customers'
  
  id = Column( "id_customer", Integer, nullable=False, primary_key=True )
  name = Column( String(45), index=True )
  locality_id = Column( Integer, ForeignKey("localities.id_locality", ondelete="CASCADE"), nullable=False, index=True )

  locality = relationship( "Locality", backref="customers" )

  def __repr__( self ):
    return self.__str__()

  def __str__( self ):
    return '<Customer %(id_customer)s>' % self.__dict__

class Locality(Base):
  __tablename__ = 'localities'
  
  id = Column( "id_locality", Integer, nullable=False, primary_key=True )
  name = Column( String(45), unique=True )


  def __repr__( self ):
    return self.__str__()

  def __str__( self ):
    return '<Locality %(id_locality)s>' % self.__dict__
```