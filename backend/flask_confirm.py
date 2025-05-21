from flask import Flask, request
import pymysql

app = Flask(__name__)

def save_customer_response(transaction_id, response):
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='00000000',
            database='fraud_detection'
        )
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO transaction_feedback (transaction_id, response) VALUES (%s, %s)",
            (transaction_id, response)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        import traceback
        print("❌ Database error while saving response:")
        traceback.print_exc()
        return False

@app.route('/confirm', methods=['GET'])
def confirm():
    tx = request.args.get('tx')
    r = request.args.get('r')

    if not tx or not r:
        return "Required information missing. Unable to proceed with transaction confirmation.", 400
    try:
        tx_id = int(tx)
        response = r.upper()
        if response not in ["YES", "NO"]:
            return "Invalid input detected. Please confirm the transaction using the designated response options.", 400
        saved = save_customer_response(tx_id, response)
        if saved:
            return "Your confirmation has been successfully recorded. The transaction will proceed accordingly."
        else:
            return "We were unable to process your confirmation at this time. Please try again later or contact support.", 500
    except ValueError:
        return "Invalid transaction reference. Please verify your link or contact support.", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)