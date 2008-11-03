#!/usr/bin/env python 

import MySQLdb
from types import *

NULLSTRING = ''

class DB:
	"""
	Handles a connection to a MySQL database.
	"""
	def __init__(self, host, user, passwd, db):
		self.con = MySQLdb.connect(user = user, passwd = passwd, db = db, host = host)
		# Set auto commit mode disabled for InnoDB tables
		self.con.autocommit(False)

	def close(self):
		"""
		Closes DB connection
		"""
		self.con.close()


class DBGeneric:
	"""
	Class for Mysql SQL requests
	"""
	def __init__(self, mycon):
		"""mycon: mysql connect object"""
		self.con = mycon
		self.query = None
	
	def begin(self):
		cur = self.con.cursor()
		cur.execute('begin')

	def setTableName(self, name):
		self.table = name

	def getFieldsAndValuesFromArray(self, **data):
		"""
		Returns fields = "a,b,c", values = "val1,val2,val3" si data = {'a' : val1, 'b' : val2, 'c' : val3 }
		"""
		fields = values = NULLSTRING
		for k, v in data.iteritems():
			fields += "`%s`," % k
			if type(v) is StringType:
				values += "\"%s\"," % v.replace("\"", "'")
			else:
				values += "\"%s\"," % v
		return (fields[:-1], values[:-1])

	def insert(self, **data):
		(fields, values) = self.getFieldsAndValuesFromArray(**data)
		query = 'INSERT INTO ' + self.table +  " (%s) VALUES (%s)" % (fields, values)
		self.query = query
		cur = self.con.cursor()
		cur.execute(query)
		self.cursor = cur
			
	def update(self, **data):
		"""update(nom='toto', prenom='tata', wheres={'id' : 5}"""
		query = "UPDATE %s SET " % self.table
		for fieldname, value in data.iteritems():
			if fieldname != 'wheres' :
				if fieldname == 'passwd':
					query += "`%s`=PASSWORD(\"%s\")," % (fieldname, value)
				else:
					if type(value) is StringType:
						value = value.replace("\"", "'")
					query += "`%s`=\"%s\"," % (fieldname, value)
					
		query = query[:-1]
		query += " WHERE "
		for fieldname, value in data['wheres'].iteritems():
			query += "`%s`=\"%s\" AND " % (fieldname, value)

		query = query[:-5]
		self.query = query
		cur = self.con.cursor()
		cur.execute(query)
		self.cursor = cur

	def delete(self, **wheres):
		"""
		Builds delete from table_name where wheres_conditions
		"""
		query = "DELETE FROM %s WHERE " % self.table
		for fieldname, value in wheres.iteritems():
			query += "%s=\"%s\" AND " % (fieldname, value)
		query = query[:-5]
		self.query = query
		cur = self.con.cursor()
		cur.execute(query)

	def query(self, query):
		self.execute(self, query)

	def execute(self, query):
		"""Wrapper to cur.execute() function"""
		cur = self.con.cursor()
		cur.execute(query)
		self.cursor = cur
		return cur.fetchall()

