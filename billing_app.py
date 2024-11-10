from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import os
import requests

app = Flask(__name__)
mongo_uri = os.getenv("MONGO_URI", "mongodb://mongodb.default.svc.cluster.local:27017")
client = MongoClient(mongo_uri)
db = client.health_records
bills_collection = db.bills

APPOINTMENT_SERVICE_URL = os.getenv("APPOINTMENT_SERVICE_URL", "http://localhost:30001")

def check_if_appointment_exists(appointment_id):
    """Check if the appointment ID exists"""
    response = requests.get(f"{APPOINTMENT_SERVICE_URL}/appointments/{appointment_id}")
    return response.status_code == 200

@app.route('/bills', methods=['POST'])
def generate_bill():
    data = request.json
    data['status'] = 'unpaid'
    data['created_at'] = datetime.utcnow()
    bill_id = bills_collection.insert_one(data).inserted_id
    return jsonify({"status": "Bill generated", "bill_id": str(bill_id)}), 201

@app.route('/bills/<bill_id>/pay', methods=['POST'])
def process_payment(bill_id):
    """Process payment for a specific bill"""
    payment_data = request.json
    bill = bills_collection.find_one({"_id": ObjectId(bill_id)})

    if not bill:
        return jsonify({"error": "Bill not found"}), 404

    appointment_id = bill.get('appointment_id')
    if appointment_id and not check_if_appointment_exists(appointment_id):
        return jsonify({"error": "Appointment ID not found"}), 400

    updated = bills_collection.update_one(
        {"_id": ObjectId(bill_id)},
        {"$set": {"status": "paid", "paid_at": datetime.utcnow(), "payment_details": payment_data}}
    )
    if updated.matched_count:
        return jsonify({"status": "Payment processed", "bill_id": bill_id}), 200
    else:
        return jsonify({"error": "Payment processing failed"}), 400

@app.route('/bills/<patient_id>', methods=['GET'])
def get_bills(patient_id):
    """Retrieve all bills for a specific patient"""
    bills = list(bills_collection.find({"patient_id": patient_id}))
    for bill in bills:
        bill["_id"] = str(bill["_id"])
    return jsonify(bills), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
