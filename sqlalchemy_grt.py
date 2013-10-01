import re

version = '0.3'

def camelize( name ):
    return re.sub(r"(?:^|_)(.)", lambda x: x.group(0)[-1].upper(), name)

def singular( name ):
    if name.endswith('ies'):
        name = name[:-3] + 'y'
    if name.endswith('ses'):
        name = name[:-2]
    elif name.endswith('s'):
        name = name[:-1]
    return name

def exportTable( table ):
    export = []
    primary = []
    indices = []
    unique = []

    for index in table.indices:
        for column in index.columns:
            if index.indexType == 'PRIMARY':
                primary.append(column.referencedColumn.name)
            if index.indexType == 'UNIQUE':
                unique.append(column.referencedColumn.name)
            if index.indexType == 'INDEX':
                indices.append(column.referencedColumn.name)

    foreignKeys = {}
    for fk in table.foreignKeys:
        for i in range(0, len(fk.columns)):
            relation = '%s.%s' % (fk.referencedColumns[i].owner.name, fk.referencedColumns[i].name)
            fktable = camelize(fk.referencedColumns[i].owner.name)
            ondelete = onupdate = None
            if fk.deleteRule and fk.deleteRule != "NO ACTION":
                ondelete = fk.deleteRule
            if fk.updateRule and fk.updateRule != "NO ACTION":
                onupdate = fk.updateRule
            foreignKeys[fk.columns[i].name] = (relation, fktable, ondelete, onupdate)

    classname = singular( camelize( table.name ) )

    export.append("class %s(Base):" % classname)
    export.append("  __tablename__ = '%s'" % table.name)
    export.append("  ")

    for column in table.columns:
        column_name = column.name
        column_alias = ''

        type = camelize( column.formattedType.lower() )
        for o, n in (('Varchar', 'String'), ('Int', 'Integer')):
            type = type.replace(o,n)
        type = re.sub(r"Integer\([^\)]\)", "Integer", type)

        options = []
        if column.name in foreignKeys:
            fkcol, fktable, ondelete, onupdate = foreignKeys[column.name]
            fkopts = []
            if ondelete: fkopts.append('ondelete="%s"' % ondelete)
            if onupdate: fkopts.append('onupdate="%s"' % onupdate)
            fkopts = len(fkopts) and ', ' + ', '.join(fkopts) or ''
            options.append('ForeignKey("%s"%s)' % (fkcol, fkopts))
        if column.isNotNull == 1:
            options.append('nullable=False')
        if 'UNSIGNED' in column.flags:
            options.append('unsigned=True')
        if column.name in primary:
            options.append('primary_key=True')
            if (len(primary) == 1) and (column_name != 'id'):
                column_alias = '"%s", ' % column_name
                column_name = 'id'
        if column.name in indices:
            options.append('index=True')
        if column.name in unique:
            options.append('unique=True')

        if len(options):
            options = ', ' + ', '.join(options)
        else:
            options = ''

        export.append("  %s = Column( %s%s%s )" % (column_name, column_alias, type, options))

    export.append("")
    for k, v in foreignKeys.items():
        fkcol, fktable, ondelete, onupdate = v
        attr = singular(fktable)
        attr = attr[0].lower() + attr[1:]
        
        backref = camelize(table.name)
        backref = backref[0].lower() + backref[1:]
        export.append('  %s = relationship( "%s", backref="%s" )' % (attr, singular(fktable), backref))

    export.append("")
    export.append('  def __repr__( self ):')
    export.append('    return self.__str__()')

    export.append("")

    export.append('  def __str__( self ):')
    export.append("    return '<"+classname+" "+ ' '.join(['%('+i+')s' for i in primary]) +">' % self.__dict__")

    export.append("")
    
    return export

print "-"*20
print "-- SQLAlchemy export v%s" % version
print "-"*20

export = []

export.append("from sqlalchemy.orm import relationship")
export.append("from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey")
export.append("from sqlalchemy.ext.declarative import declarative_base")
export.append("")
export.append("Base = declarative_base()")
export.append("")

for table in grt.root.wb.doc.physicalModels[0].catalog.schemata[0].tables:
    print " -> Working on %s" % table.name
    export.extend( exportTable(table) )

grt.modules.Workbench.copyToClipboard('\n'.join(export))
print "Copied to clipboard"

