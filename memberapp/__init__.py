from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from flask_wtf.csrf import CSRFProtect

#we want to make the object-based config available
from memberapp import config

app = Flask(__name__,instance_relative_config=True)

csrf = CSRFProtect(app) #initialize extension, this will protect all your post routes against csrf and you must pass the csrf_token when submitting to these routes

#load the config from instance folder file
app.config.from_pyfile("config.py", silent=False)
#load the config from object-based config that is within your package
app.config.from_object(config.Liveconfig)
db = SQLAlchemy(app)


#load the routes
from memberapp import adminroutes,userroutes