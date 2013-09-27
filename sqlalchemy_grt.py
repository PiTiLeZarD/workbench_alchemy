

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
            foreignKeys[fk.columns[i].name] = (relation, fktable)

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
            options.append('ForeignKey("%s")' % foreignKeys[column.name][0])
        if column.isNotNull == 1:
            options.append('nullable=False')
        if 'UNSIGNED' in column.flags:
            options.append('unsigned=True')
        if column.name in primary:
            options.append('primary=True')
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
        attr = singular(v[1])
        attr = attr[0].lower() + attr[1:]
        
        backref = camelize(table.name)
        backref = backref[0].lower() + backref[1:]
        print '  %s = relationship( "%s", backref="%s" )' % (attr, v[1], backref)

    print ""
    print '  def __repr__( self ):'
    print '    return self.__str__()'

    print ""

    print '  def __str__( self ):'
    print "    return '<"+classname+" "+ ' '.join(['%('+i+')s' for i in primary]) +">' % self.__dict__"

    print ""
    print ""

