workbench_alchemy
=================

SQLAlchemy model creation for MySQL Workbench

### Want to see?

This:
<img src="example.png" alt="Example" style="width: 100%;"/>

Translates to that:
```python
class Customer(Base):
  __tablename__ = 'customers'
  
  id = Column( Integer, nullable=False, primary_key=True )
  name = Column( String(45), index=True )
  locality_id = Column( Integer, ForeignKey("localities.id", ondelete="CASCADE"), nullable=False, index=True )

  locality = relationship( "Locality", backref="customers" )

  def __repr__( self ):
    return self.__str__()

  def __str__( self ):
    return '<Customer %(id)s>' % self.__dict__


class Locality(Base):
  __tablename__ = 'localities'
  
  id = Column( Integer, nullable=False, primary_key=True )
  name = Column( String(45), unique=True )


  def __repr__( self ):
    return self.__str__()

  def __str__( self ):
    return '<Locality %(id)s>' % self.__dict__
```