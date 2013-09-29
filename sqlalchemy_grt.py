

import re

def camelize( name ):
    return re.sub(r"(?:^|_)(.)", lambda x: x.group(0)[-1].upper(), name)

def singular( name ):
    if name.endswith('ies'):
        name = name[:-3] + 'y'
    if name.endswith('s'):
        name = name[:-1]
    return name

for table in grt.root.wb.doc.physicalModels[0].catalog.schemata[0].tables:
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

    print "class %s(Base):" % classname
    print "  __tablename__ = '%s'" % table.name
    print "  "

    for column in table.columns:
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
        if column.name in indices:
            options.append('index=True')
        if column.name in unique:
            options.append('unique=True')

        if len(options):
            options = ', ' + ', '.join(options)
        else:
            options = ''

        print "  %s = Column( %s%s )" % (column.name, type, options)

    print ""
    for k, v in foreignKeys.items():
        fkcol, fktable, ondelete, onupdate = v
        attr = singular(fktable)
        attr = attr[0].lower() + attr[1:]
        
        backref = camelize(table.name)
        backref = backref[0].lower() + backref[1:]
        print '  %s = relationship( "%s", backref="%s" )' % (attr, singular(fktable), backref)

    print ""
    print '  def __repr__( self ):'
    print '    return self.__str__()'

    print ""

    print '  def __str__( self ):'
    print "    return '<"+classname+" "+ ' '.join(['%('+i+')s' for i in primary]) +">' % self.__dict__"

    print ""
    print ""

