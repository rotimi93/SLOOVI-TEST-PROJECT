import os
import hashlib
import datetime
from flask_cors import cross_origin
from dotenv import load_dotenv
from pymongo import MongoClient
from flask import Flask, request, jsonify, render_template
from bson.objectid import ObjectId
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask import url_for, redirect
load_dotenv()

app = Flask(__name__)

jwt = JWTManager(app)
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=1)

client = MongoClient("mongodb+srv://michael93:michael93@cluster0.cjdew.mongodb.net/?retryWrites=true&w=majority")
db = client.sloovi
users_collection = db.users_collection
templates_collection = db.templates_collection

@app.route('/', methods=["GET"])
def index():
	template_name = 'index.html'
	return render_template(template_name)

@app.route('/register', methods=["POST"])
@cross_origin()
def register():
	try:
		new_user = request.get_json(force=True)
		new_user["password"] = hashlib.sha256(new_user["password"].encode("utf-8")).hexdigest()
		doc = users_collection.find_one({"email": new_user["email"]})
		if not doc:
			users_collection.insert_one(new_user)
			return jsonify({'msg': 'User created successfully'}), 201
		else:
			return jsonify({'msg': 'Username already exists'}), 409
	except Exception as ex:
		return jsonify({'msg': 'Something went wrong'}), 500

@app.route('/login', methods=["POST"])
@cross_origin()
def login():
	try:
		login_details = request.get_json()
		user_from_db = users_collection.find_one({'email': login_details['email'], 'password':login_details['password']})

		if user_from_db:
			encrpted_password = hashlib.sha256(login_details['password'].encode("utf-8")).hexdigest()
			if encrpted_password == user_from_db['password']:
				access_token = create_access_token(identity=str(user_from_db['_id']))
				return jsonify(access_token=access_token), 200

		return jsonify({'msg': 'The username or password is incorrect'}), 401
	except Exception as ex:
		return jsonify({'msg': 'Something went wrong'}), 500


@app.route("/template", methods=["GET"])
@jwt_required()
@cross_origin()
def getALLTemplates():
	try:
		templates = list(templates_collection.find({"user_id":get_jwt_identity()}))
		for template in templates:
			template['_id'] = str(template['_id'])
			del template['user_id']
		return jsonify({'msg': 'Templates fetched successfully', 'data':templates}), 200
	except Exception as ex:
		return jsonify({'msg': 'Something went wrong'}), 500


@app.route("/template", methods=["POST"])
@jwt_required()
@cross_origin()
def createTemplate():
	try:
		template_data = request.get_json()
		insert_data = {
			"template_name": template_data["template_name"],
			"subject": template_data["subject"],
			"body": template_data["body"],
			"user_id": get_jwt_identity()
		}
		templates_collection.insert_one(insert_data)
		return jsonify({'msg': 'Template stored successfully'}), 201
	except Exception as ex:
		return jsonify({'msg': 'Something went wrong'}), 500


@app.route("/template/<id>", methods=["PUT"])
@jwt_required()
@cross_origin()
def updateTemplate(id):
	request_data = request.get_json()
	update_data = {
		"template_name": request_data["template_name"],
		"subject": request_data["subject"],
        "body": request_data["body"],
    }
	try:
		template = templates_collection.update_one({ '_id': ObjectId(id) }, {"$set": update_data})
		if template.modified_count == 1:
			return jsonify({'msg': 'Template updated successfully'}), 200
		return jsonify({'msg': 'Nothing to update'}), 200
	except Exception as ex:
		return jsonify({'msg': 'Template not found'}), 200

@app.route("/template/<id>", methods=["DELETE"])
@jwt_required()
@cross_origin()
def deleteTemplate(id):
	try:
		template = templates_collection.delete_one({ '_id': ObjectId(id) })
		if template.deleted_count == 1:
			return jsonify({'msg': 'Template deleted successfully'}), 200
		return jsonify({'msg': 'Template not found'}), 200
	except Exception as ex:
		return jsonify({'msg': 'Something went wrong'}), 500
