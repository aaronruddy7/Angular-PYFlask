from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
from bson import ObjectId
import string
import jwt
import datetime
from functools import wraps
import bcrypt
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'aaronruddy'

client = MongoClient("mongodb://127.0.0.1:27017")
db = client.booksDB # update the database
books = db.books # creating link to books database
staff = db.staff # creating link to staff database
blacklist =db.blacklist

#returning a list of all the books
@app.route("/api/v1.0/books", methods=["GET"])

def show_all_books():
    page_num, page_size = 1, 10
    if request.args.get('pn'):
        page_num = int(request.args.get('pn'))
    if request.args.get('ps'):
        page_size = int(request.args.get('ps'))
    page_start = (page_size * (page_num - 1))

    data_to_return = []
    for book in books.find().skip(page_start).limit(page_size):
        book['_id'] = str(book['_id'])
        for review in book['reviews']:
            review['_id'] = str(review['_id'])
        data_to_return.append(book)

    return make_response( jsonify(data_to_return), 200 )

#return a single book
@app.route("/api/v1.0/books/<string:id>",methods=["GET"])

def show_one_book(id):
    #check if id is 24 characters longs and that all characters are in hexadecimal
    if len(id) != 24 or not all(c in string.hexdigits for c in id):
        #displays errors if criteria not met
        return make_response( jsonify({"error" : "Invalid book ID"} ), 404 )
    book = books.find_one({'_id':ObjectId(id)})
    if book is not None:
        book['_id'] = str(book['_id'])
        for review in book['reviews']:
            review['_id'] = str(review['_id'])

        return make_response( jsonify([book]), 200 )
    else:
         return make_response( jsonify({"error" : "Invalid book ID"} ), 404 )

#adding a book

@app.route("/api/v1.0/books", methods=["POST"])
def add_book():
    if "author" in request.form and \
        "country" in request.form and \
        "language" in request.form and \
        "link" in request.form and \
        "pages" in request.form and \
        "title" in request.form and \
        "year" in request.form and \
        "years_to_write" in request.form:

        new_book = {
            "_id" : ObjectId(),
            "author" : request.form["author"],
            "country" : request.form["country"],
            "language" : request.form["language"],
            "link" : request.form["link"],
            "pages" : request.form["pages"],
            "title" : request.form["title"],
            "year" : request.form["year"],
            "years_to_write" : request.form["years_to_write"],
            "reviews" : [],
            "profit" : []
        }
        new_book_id = books.insert_one(new_book)
        new_book_link = "http://localhost:5000/api/v1.0/books/" + str(new_book_id.inserted_id)
        return make_response( jsonify(
             {"url": new_book_link} ), 201)
    else:
        return make_response( jsonify(
             {"error":"Missing form data"} ), 404)

#edit a book
@app.route("/api/v1.0/books/<string:id>", methods=["PUT"])

def edit_book(id):
    #check if id is 24 characters longs and that all characters are in hexadecimal
    if len(id) != 24 or not all(c in string.hexdigits for c in id):
        #displays errors if criteria not met
        return make_response( jsonify({"error" : "Invalid book ID"} ), 404 )
    if "author" in request.form and \
        "country" in request.form and \
        "language" in request.form and \
        "link" in request.form and \
        "pages" in request.form and \
        "title" in request.form and \
        "year" in request.form and \
        "years_to_write" in request.form:

        result = books.update_one( \
        { "_id" : ObjectId(id) }, {
        "$set" : { "author" : request.form["author"],
            "country" : request.form["country"],
            "language" : request.form["language"],
            "link" : request.form["link"],
            "pages" : request.form["pages"],
            "title" : request.form["title"],
            "year" : request.form["year"],
            "years_to_write" : request.form["years_to_write"]
                }
        } )

        if result.matched_count == 1:
            edited_book_link = \
            "http://localhost:5000/api/v1.0/books/" + id
            return make_response( jsonify(
            { "url":edited_book_link } ), 200)
        else:
            return make_response( jsonify(
                { "error":"Invalid book ID" } ), 404)
    else:
        return make_response( jsonify(
             { "error" : "Missing form data" } ), 404)

#delete book
@app.route("/api/v1.0/books/<string:id>",methods=["DELETE"])


def delete_book(id):
    #check if id is 24 characters longs and that all characters are in hexadecimal
    if len(id) != 24 or not all(c in string.hexdigits for c in id):
        #displays errors if criteria not met
        return make_response( jsonify({"error" : "Invalid book ID"} ), 404 )
    result = books.delete_one( { "_id" : ObjectId(id) } )
    if result.deleted_count == 1:
        return make_response( jsonify( {} ), 204)
    else:
        return make_response( jsonify({ "error" : "Invalid book ID" } ), 404)

#add a review
@app.route("/api/v1.0/books/<string:id>/reviews", methods=["POST"])

def add_new_review(id):
    new_review = {
        "_id" : ObjectId(),
        "user_id" : "499384bc75hd3quex73218",
        "username" : request.form["username"],
        "comment" : request.form["comment"],
        "date" : request.form["date"],
        "stars" : request.form["stars"],
        "funny" : 0,
        "cool" : 0,
        "useful" : 0
    }  
    books.update_one( 
        { "_id" : ObjectId(id) },{ "$push": { "reviews" : new_review } } )
    new_review_link = "http://localhost:5000/api/v1.0/books/" + id +"/reviews/" + str(new_review['_id'])
    return make_response( jsonify({ "url" : new_review_link } ), 201 )

#get all reviews
@app.route("/api/v1.0/books/<string:id>/reviews", methods=["GET"])

def fetch_all_reviews(id):
    data_to_return = []
    book = books.find_one( \
        { "_id" : ObjectId(id) }, \
        { "reviews" : 1, "_id" : 0 } )
    for review in book["reviews"]:
        review["_id"] = str(review["_id"])
        data_to_return.append(review)
    return make_response( jsonify(data_to_return ), 200 )

#get one review
@app.route("/api/v1.0/books/<bid>/reviews/<rid>", methods=["GET"])

def fetch_one_review(bid, rid):
    #check if bid is 24 characters longs and that all characters are in hexadecimal
    if len(bid) != 24 or not all(c in string.hexdigits for c in bid):
        #displays errors if criteria not met
        return make_response( jsonify({"error" : "Invalid book ID"} ), 404 )

    #check if rid is 24 characters longs and that all characters are in hexadecimal
    if len(rid) != 24 or not all(c in string.hexdigits for c in rid):
        #displays errors if criteria not met
        return make_response( jsonify({"error" : "Invalid review ID"} ), 404 )
    
    book = books.find_one( \
        { "reviews._id" : ObjectId(rid) }, \
        { "_id" : 0, "reviews.$" : 1 } )
    if book is None:
        return make_response( \
        jsonify( \
        {"error":"Invalid book ID or review ID"}),404)
    book['reviews'][0]['_id'] = str(book['reviews'][0]['_id'])

    return make_response( jsonify(book['reviews'][0]), 200)

#edit review
@app.route("/api/v1.0/books/<bid>/reviews/<rid>", methods=["PUT"])

def edit_review(bid, rid):
    #check if bid is 24 characters longs and that all characters are in hexadecimal
    if len(bid) != 24 or not all(c in string.hexdigits for c in bid):
        #displays errors if criteria not met
        return make_response( jsonify({"error" : "Invalid book ID"} ), 404 )

    #check if rid is 24 characters longs and that all characters are in hexadecimal
    if len(rid) != 24 or not all(c in string.hexdigits for c in rid):
        #displays errors if criteria not met
        return make_response( jsonify({"error" : "Invalid review ID"} ), 404 )

    edited_review = {
        "reviews.$.username" : request.form["username"],
        "reviews.$.comment" : request.form["comment"],
        "reviews.$.stars" : request.form['stars'],
        "reviews.$.date" : request.form['date']
    }
    books.update_one( \
        { "reviews._id" : ObjectId(rid) }, \
        { "$set" : edited_review } )
    edit_review_url = "http://localhost:5000/api/v1.0/books/" + bid + "/reviews/" + rid
    return make_response( jsonify({"url":edit_review_url} ), 200)

#delete review
@app.route("/api/v1.0/books/<bid>/reviews/<rid>", methods=["DELETE"])

def delete_review(bid, rid):
    #check if bid is 24 characters longs and that all characters are in hexadecimal
    if len(bid) != 24 or not all(c in string.hexdigits for c in bid):
        #displays errors if criteria not met
        return make_response( jsonify({"error" : "Invalid book ID"} ), 404 )

    #check if rid is 24 characters longs and that all characters are in hexadecimal
    if len(rid) != 24 or not all(c in string.hexdigits for c in rid):
        #displays errors if criteria not met
        return make_response( jsonify({"error" : "Invalid review ID"} ), 404 )

    books.update_one( \
        { "_id" : ObjectId(bid) }, \
        { "$pull" : { "reviews" : \
            { "_id" : ObjectId(rid) } } } )
    return make_response( jsonify( {} ), 204)

#login
@app.route('/api/v1.0/login', methods=['GET'])
def login():
    auth = request.authorization

    if auth:
        user = staff.find_one( {'username':auth.username } )
        if user is not None:
            if bcrypt.checkpw(bytes(auth.password, 'UTF-8'), user["password"]):

                token = jwt.encode({
                    'user' : auth.username,
                    'admin' : user["admin"],
                    'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=120)}, \
                    app.config['SECRET_KEY'])
                return make_response(jsonify( {'token':token.decode('UTF-8')}), 200)
            else:
                return make_response(jsonify( {'message':'Bad password'}), 401)
        else:
                return make_response(jsonify({'message':'Bad username'}), 401)

    return make_response(jsonify( {'message':'Authentication required'}), 401)

# application functionality
if __name__ == "__main__":
    app.run(debug=True)