import MySQLdb
from datetime import datetime  
from sqlalchemy import Column, ForeignKey, create_engine  
from sqlalchemy.dialects.mysql import \
        BIGINT, BINARY, BIT, BLOB, BOOLEAN, CHAR, DATE, \
        DATETIME, DECIMAL, DECIMAL, DOUBLE, ENUM, FLOAT, INTEGER, \
        LONGBLOB, LONGTEXT, MEDIUMBLOB, MEDIUMINT, MEDIUMTEXT, NCHAR, \
        NUMERIC, NVARCHAR, REAL, SET, SMALLINT, TEXT, TIME, TIMESTAMP, \
        TINYBLOB, TINYINT, TINYTEXT, VARBINARY, VARCHAR, YEAR 
from sqlalchemy.ext.declarative import declarative_base  
from sqlalchemy.orm import sessionmaker  
from sqlalchemy.orm.interfaces import MapperExtension  

Base = declarative_base()  
engine = create_engine('mysql+mysqldb://biren:cArrion69@birenshah.ciic9oqhvrvk.us-east-1.rds.amazonaws.com:3306/sv_test', echo=False)
SessionFactory = sessionmaker(bind=engine)
session = SessionFactory()

class _TableMixin(object):
	__table_args__ = {
		'mysql_engine':'InnoDB',
		'mysql_charset': 'utf8'
	}

	id = Column('id', INTEGER(unsigned=True), primary_key=True)
	createdAt = Column('createdAt', TIMESTAMP(), nullable=False, default=datetime.now())
	updatedAt = Column('updatedAt', TIMESTAMP(), nullable=False, default=datetime.now())

class Story(Base, _TableMixin):
	__tablename__ = 'stories'
	
	title = Column('title', VARCHAR(255), nullable=False, unique=False)  
	subtitle = Column('subtitle', TEXT(), nullable=True, unique=False)
	creatorId = Column('creatorId', INTEGER(unsigned=True), ForeignKey("creators.id"))
	creatorInfo = Column('creatorInfo', TEXT(), nullable=True)
	languageId = Column('languageId', VARCHAR(255), ForeignKey("enums.id"))
	storyText = Column('storyText', LONGTEXT())
	wordCount = Column('wordCount', INTEGER(unsigned=True))
	publicationId = Column('publicationId', INTEGER(unsigned=True), ForeignKey('publications.id'))
	publicationDate = Column('publicationDate', DATE())
	rightsOwned = Column('rightsOwned', TINYINT(unsigned=True), nullable=False, default=0)
	parseId = Column('parseId', VARCHAR(255), nullable=False, unique=True)
	
	def __init__(self, title, subtitle, creatorId, creatorInfo, languageId, storyText, 
		publicationId, publicationDate, parseId, rightsOwned=0):  
		self.title = title   
		self.subtitle = subtitle
		self.creatorId = creatorId
		self.creatorInfo = creatorInfo
		self.languageId = languageId
		self.storyText = storyText
		self.wordCount = len(storyText.replace('<p>','').replace('</p>','').split(None))
		self.publicationId = publicationId
		self.publicationDate = publicationDate
		self.parseId = parseId	
		self.rightsOwned = rightsOwned

class Creator(Base, _TableMixin):
	__tablename__ = 'creators'
	name = Column(VARCHAR(255), nullable=False, unique=False)
	email = Column(VARCHAR(255), nullable=True, unique=True, default=None)
	
	def __init__(self, name, email):  
		self.name = name
		self.email = email

class PubDetails(Base, _TableMixin):
	__tablename__ = 'pubDetails'
	
	storyId = Column('storyId', INTEGER(unsigned=True), ForeignKey('stories.id'))
	url = Column('url',VARCHAR(255), nullable=True)
	section = Column('section', VARCHAR(255), nullable=True)
	issue = Column('section', VARCHAR(255), nullable=True)
	volume = Column('volume', VARCHAR(255), nullable=True)
	doi = Column('doi',VARCHAR(255),nullable=True)
	pageViews = Column('pageViews', INTEGER(unsigned=True),nullable=True)
	fbShares = Column('fbShares', INTEGER(unsigned=True),nullable=True)
	tweets = Column('tweets', INTEGER(unsigned=True),nullable=True)
	altmetricScore = Column('altmetricScore',INTEGER(unsigned=True),nullable=True)
	altmetricContext = Column('altmetricContext',VARCHAR(255),nullable=True)

	def __init__(self, storyId, url=None, section=None, issue=None, volume=None, doi=None, 
			pageViews=None, fbShares=None, tweets=None, altmetricScore=None, altmetricContext=None):
		self.storyId = storyId
		self.url = url
		self.section = section
		self.issue = issue
		self.volume = volume
		self.doi = doi
		self.pageViews = pageViews
		self.fbShares = fbShares
		self.tweets = tweets
		self.altmetricScore = altmetricScore
		self.altmetricContext = altmetricContext


class Enum(Base):
	__tablename__ = 'enums'
	__table_args__ = {
		'mysql_engine':'InnoDB',
		'mysql_charset': 'utf8'
	}
	id = Column('id', VARCHAR(255), primary_key=True)
	enumGroup = Column('enumGroup',VARCHAR(255))
	enum = Column(VARCHAR(255), nullable=False, unique=False)  
	
	def __init__(self, enum, enumGroup):  
		self.id = enumGroup + "-" + enum
		self.enumGroup = enumGroup
		self.enum = enum 

class Publication(Base, _TableMixin):
	__tablename__ = 'publications'
	
	title = Column(VARCHAR(255), nullable=False, unique=False)  
	publisher = Column(VARCHAR(255), nullable=True, unique=False)
	rightsAgent = Column(VARCHAR(255), nullable=True, unique=False)
	
	def __init__(self, title, publisher=None, rightsAgent=None):  
		self.title = title 
		self.publisher = publisher
		self.rightsAgent = rightsAgent



class User(Base, _TableMixin):
	__tablename__ = 'users'
	
	username = Column('username', VARCHAR(25))
	email = Column('email', VARCHAR(255))
	password = Column('password', VARCHAR(255))
	parseId = Column('parseId', VARCHAR(255), nullable=False, unique=True)
	
	def __init__(self, username, email, password, parseId):  
		self.username = username
		self.email = email
		self.password = password
		self.parseId = parseId

class Stream(Base, _TableMixin):
	__tablename__ = 'stream'
	userId = Column('userId', INTEGER(unsigned=True), ForeignKey("users.id"))
	storyId = Column('storyId', INTEGER(unsigned=True), ForeignKey("stories.id"))
	rating = Column('rating', SMALLINT(unsigned=True))
	favorite = Column('favorite', TINYINT(unsigned=True))
	completedAt = Column('completedAt', DATETIME)	

	def __init__(self, userId, storyId):
		self.userId = userId
		self.storyId = storyId
		
		
