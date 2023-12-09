## postgres database stuffie
import os 
from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')

## eg code, get the actual connection string from vercel 


db=SQLAlchemy(app)

class Classroom(db.Model):
   id=db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
   class_name = db.Column(db.String(100), nullable=False)
   description = db.Column(db.String(1000), unique=True, nullable=False)
   rating = db.Column(db.Integer)
   numOfRatings = db.Column(db.Integer)

   # teacher name 
   def __repr__(self):
       return f"<id: {self.id} class_name: {self.class_name}, description: {self.description}, rating: {self.rating}, numOfRatings: {self.numOfRatings})>"

@app.route('/test')
def test():
    return 'hello World';

@app.route('/')
def index():
    classes = Classroom.query.all()
    print(classes)
    for classroom in classes:
        if classroom.numOfRatings is 0:
            classroom.rating = 0
        else:
            classroom.rating /= classroom.numOfRatings
        classroom.rating = round(classroom.rating, 2)

    return render_template('./index.html', classes=classes)


@app.route('/addrating', methods=['POST'])
def add_rating():
   print(request.json)
   rating = request.json['rating']
   class_id=request.json['class_id']
   if rating == None or class_id == None: 
       return "No 'rating' or 'class_id'", 400
   
   classroom = Classroom.query.filter_by(id=class_id).first()

   if classroom == None:
       return f"None such class '{class_id}'", 400
   classroom.rating += rating
   classroom.ratingSum += rating
   classroom.numOfRatings += 1;
   
   db.session.add(classroom)
   db.session.commit()
   
   return "done", 200

# . .venv/bin/activate

### backend business 

## terminal flask shell cmds
## source /Users/pragya/Desktop/tino-class-rank/.venv/bin/activate
# source config.env 
# from app import db, Classroom
# class1=Classroom(class_name="APP1",description="taught by steemers",rating=5)
# class5=Classroom(class_name="World Literature",description="taught by avvakumovits, phelps, & chen",rating=3,numOfRatings=12)
# db.session.add(class1)
# db.session.commit()
# Classroom.query.all()

## running flask app thingy 
# export FLASK_APP=app
