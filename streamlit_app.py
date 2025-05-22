import streamlit as st 
import pandas as pd
import pymysql
import matplotlib.pyplot as plt 
import numpy as np 
import time 
import smtplib
from email.mime.text import MIMEText

# ==============================================================
# FRAUD DETECTION SYSTEM - STREAMLIT APP
# Structured code with clear comments and logical section headers.
# ==============================================================


st.set_page_config(page_title="Fraud Detection System", page_icon="🛡️", layout="wide")

# ==============================================================
# DATABASE FUNCTIONS
# ==============================================================

# Function: login_user
# Authenticates a user against the users table using email and password.
def login_user(email, password):
    try:
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="00000000",
            database="fraud_detection"
        )
        cursor = conn.cursor()
        query = "SELECT * FROM users WHERE email=%s AND password=%s"
        cursor.execute(query, (email, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user
    except Exception as e:
        st.error(f"Database error: {e}")
        return None

# Function: load_transactions
# Loads all transactions from the database into a DataFrame.
def load_transactions():
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='00000000',
        database='fraud_detection'
    )
    df = pd.read_sql("SELECT * FROM transactions", conn)
    conn.close()
    return df

# Function: get_customer_info
# Retrieves customer details (name, phone, city, email) given customer_id.
def get_customer_info(customer_id):
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='00000000',
        database='fraud_detection'
    )
    cursor = conn.cursor()
    query = "SELECT name, phone_number, city, email FROM customers WHERE customer_id = %s"
    cursor.execute(query, (customer_id,))
    customer = cursor.fetchone()
    cursor.close()
    conn.close()
    return customer

# ==============================================================
# OTP & EMAIL LOGIC
# ==============================================================

import yagmail
import keyring

# Function: send_email_confirmation
# Sends a confirmation email to the customer for a specific transaction.
def send_email_confirmation(to_email, transaction_id):
    subject = f"Transaction #{transaction_id} Confirmation"
    body = f"""
<html>
  <body>
    <p>Did you make transaction #{transaction_id}?</p>
    <p>
      <a href="http://localhost:5050/confirm?tx={transaction_id}&r=YES">YES - I Confirm</a><br>
      <a href="http://localhost:5050/confirm?tx={transaction_id}&r=NO">NO - This Was Not Me</a>
    </p>
  </body>
</html>
    """


    try:
        password = keyring.get_password("yagmail", "addminn332005@gmail.com")
        yag = yagmail.SMTP("addminn332005@gmail.com", password)
        yag.send(to=to_email, subject=subject, contents=[body])
        # Removed Streamlit message here to avoid extra message outside the table
        return True
    except Exception as e:
        st.error(f"Email sending failed: {e}")
        return False

# Function: send_otp_email
# Sends an OTP verification code to the user's email address.
def send_otp_email(to_email, otp_code):
    subject = "Your OTP Verification Code"
    body = f"""
    <html>
      <body>
        <p>Your verification code is:</p>
        <h2>{otp_code}</h2>
      </body>
    </html>
    """
    try:
        password = keyring.get_password("yagmail", "addminn332005@gmail.com")
        yag = yagmail.SMTP("addminn332005@gmail.com", password)
        yag.send(to=to_email, subject=subject, contents=[body])
        return True
    except Exception as e:
        st.error(f"❌ Failed to send OTP: {e}")
        return False

# ==============================================================
# CUSTOMER RESPONSE HANDLING
# ==============================================================

# Function: save_customer_response
# Saves a customer's YES/NO response for a transaction in the DB.
def save_customer_response(transaction_id, response):
    try:
        conn = pymysql.connect(host='localhost', user='root', password='00000000', database='fraud_detection')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO transaction_feedback (transaction_id, response) VALUES (%s, %s)",
            (transaction_id, response)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"Database error while saving response: {e}")

# Function: get_customer_responses
# Retrieves all responses for a given transaction (most recent first).
def get_customer_responses(transaction_id):
    conn = pymysql.connect(host='localhost', user='root', password='00000000', database='fraud_detection')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT response, created_at FROM transaction_feedback WHERE transaction_id = %s ORDER BY id DESC",
        (transaction_id,)
    )
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

# ==============================================================
# FRAUD DETECTION DASHBOARD UI
# ==============================================================


import joblib

# Function: fraud_detection_system
# Main dashboard UI for fraud detection, staff view and customer response.
def fraud_detection_system():
    # --- TOP BAR: Professional Dashboard Header ---
    # Displays the SecureBank branding and currently logged-in user's email.
    st.markdown(f"""
        <div style='display: flex; justify-content: space-between; align-items: center; padding: 12px 24px; border-bottom: 1px solid #ccc; background-color: white;'>
            <div style='display:flex; align-items:center; gap: 12px;'>
                <img src="https://img.icons8.com/color/48/000000/security-checked.png" width="36"/>
                <span style='font-size: 20px; font-weight: bold;'>SecureBank Dashboard</span>
            </div>
            <div style='display:flex; align-items:center; gap: 15px;'>
                <span style="font-weight:600;">{st.session_state['email']}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- PAGE SELECTION ---
    page_options = ["Dashboard", "Manual Check"]
    selected_page = st.sidebar.radio("Navigation", page_options)

    # --- LOAD MODEL FOR MANUAL CHECK ---
    model = None
    try:
        model = joblib.load("fraud_detection_PKL1_model.pkl")
        st.success("✅ Model loaded successfully.")
    except Exception as e:
        st.error(f"❌ Failed to load model: {e}")

    if selected_page == "Manual Check":
        # حذف النص placeholder (لا يوجد نص سابق هنا)
        # إضافة واجهة الإدخال اليدوي كما هو مطلوب
        st.markdown("## 🧪 Manual Transaction Classification")
        st.write("Enter transaction details to test the model's prediction capability:")

        with st.form("manual_city_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                step = st.number_input("Step", min_value=1)
                amount = st.number_input("Amount", min_value=0.0)
                transaction_type = st.selectbox("Type", options=["CASH_OUT", "CASH_IN", "PAYMENT", "TRANSFER", "DEBIT"])
            with col2:
                oldBalanceOrig = st.number_input("Old Balance Orig", min_value=0.0)
                newBalanceOrig = st.number_input("New Balance Orig", min_value=0.0 )
                isFlaggedFraud = st.selectbox("Is Flagged Fraud", options=[0, 1])
            with col3:
                oldBalanceDest = st.number_input("Old Balance Dest", min_value=0.0)
                newBalanceDest = st.number_input("New Balance Dest", min_value=0.0)
                city = st.text_input("City (Optional)", value="")

            submitted = st.form_submit_button("🔍 Predict")

        if submitted:
            try:
                sample = pd.DataFrame([{
                    "transactionID": int(time.time()),
                    "step": step,
                    "type": transaction_type,
                    "amount": amount,
                    "oldBalanceOrig": oldBalanceOrig,
                    "newBalanceOrig": newBalanceOrig,
                    "oldBalanceDest": oldBalanceDest,
                    "newBalanceDest": newBalanceDest,
                    "isFlaggedFraud": isFlaggedFraud
                }])

                # تشفير العمود type قبل التنبؤ
                type_encoding = {"CASH_OUT": 0, "CASH_IN": 1, "PAYMENT": 2, "TRANSFER": 3, "DEBIT": 4}
                sample["type"] = sample["type"].map(type_encoding)

                # تأكد من أن الأعمدة مطابقة للنموذج
                required_cols = [
                    "transactionID", "step", "type", "amount",
                    "oldBalanceOrig", "newBalanceOrig",
                    "oldBalanceDest", "newBalanceDest", "isFlaggedFraud"
                ]
                if model:
                    prob = model.predict_proba(sample[required_cols])[0][1]
                    prediction = 1 if prob >= 0.9 else 0
                    st.info(f"🔍 Fraud Probability: {prob:.4f}")
                    result = "🟥 Fraudulent" if prediction == 1 else "🟩 Legitimate"
                    st.success(f"**Prediction Result:** {result}")
                    # ==== تفسير إضافي عند تصنيف العملية كاحتيال ====
                    if prediction == 1:
                        explanation = ""
                        if transaction_type == "CASH_IN" and oldBalanceOrig == 0:
                            explanation = "⚠️ Sudden large deposit into an empty account — suspicious behavior."
                        elif transaction_type == "TRANSFER" and newBalanceOrig == 0:
                            explanation = "⚠️ Full balance transferred from origin account — potential fraud pattern."
                        elif oldBalanceDest == 0 and newBalanceDest == amount:
                            explanation = "⚠️ Receiver had zero balance before receiving full transaction amount."
                        else:
                            explanation = "⚠️ The model detected suspicious transaction patterns based on training data."
                        st.warning(explanation)
                else:
                    st.warning("Model is not loaded.")
            except Exception as e:
                st.error(f"Prediction failed: {e}")

        # ==== CSV Upload and Classification ====
        st.markdown("### 📂 Upload CSV File for Bulk Classification")
        uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
        if uploaded_file and model:
            try:
                try:
                    df_csv = pd.read_csv(uploaded_file)
                except UnicodeDecodeError:
                    df_csv = pd.read_csv(uploaded_file, encoding='latin1')
                if "type" in df_csv.columns:
                    type_encoding = {"CASH_OUT": 0, "CASH_IN": 1, "PAYMENT": 2, "TRANSFER": 3, "DEBIT": 4}
                    df_csv["type"] = df_csv["type"].map(type_encoding)
                required_cols = [
                    "transactionID", "step", "type", "amount",
                    "oldBalanceOrig", "newBalanceOrig",
                    "oldBalanceDest", "newBalanceDest", "isFlaggedFraud"
                ]
                df_csv["fraud_probability"] = model.predict_proba(df_csv[required_cols])[:, 1]
                df_csv["prediction"] = df_csv["fraud_probability"].apply(lambda p: "🟥 Fraudulent" if p >= 0.9 else "🟩 Legitimate")
                st.success("✅ File processed successfully.")
                st.dataframe(df_csv[["transactionID", "amount", "type", "fraud_probability", "prediction"]])
            except Exception as e:
                st.error(f"Error processing uploaded file: {e}")
        return

    # --- CUSTOMER RESPONSE HANDLING VIA EMAIL LINK ---
    # Allows customer to respond YES/NO via email link; processes the response.
    from streamlit_autorefresh import st_autorefresh
    # Auto-refresh disabled to avoid full reloads.
    query_params = st.query_params
    # Prevent duplicate processing if already handled (e.g. on auto-reload)
    if st.session_state.get('response_already_processed'):
        return
    if 'tx' in query_params and 'r' in query_params:
        # 1. Capture YES/NO response from email link
        try:
            # 2. Convert tx value from URL to transaction_id as integer
            transaction_id_raw = query_params['tx'][0]
            transaction_id = int(transaction_id_raw)
        except Exception:
            st.error("Invalid transaction ID format in URL.")
            return
        # 3. Read response value and convert to uppercase (YES/NO)
        response = query_params['r'][0].upper()

        # 4. Check if transaction_id exists in the database
        df_check = load_transactions()
        df_check['transaction_id'] = df_check['transaction_id'].astype(int)
        if transaction_id not in df_check['transaction_id'].values:
            st.error(f"Transaction ID {transaction_id} does not exist in the transaction table.")
            return

        # 5. Save the response in transaction_feedback table
        save_customer_response(transaction_id, response)
        st.session_state['response_already_processed'] = True
        st.query_params.clear()

        # 6. Update the transaction status (is_active) according to the response
        conn = pymysql.connect(host='localhost', user='root', password='00000000', database='fraud_detection')
        cursor = conn.cursor()
        if response == 'NO':
            cursor.execute("UPDATE transactions SET is_active = 0 WHERE transaction_id = %s", (transaction_id,))
        elif response == 'YES':
            cursor.execute("UPDATE transactions SET is_active = 1 WHERE transaction_id = %s", (transaction_id,))
        conn.commit()
        cursor.close()
        conn.close()

        st.session_state[f'alert_sent_{transaction_id}'] = True
        st.session_state[f'show_alert_{transaction_id}'] = True

        # 7. Show confirmation message to the customer
        st.markdown(
            "<h2 style='color:#004085'>Response Received</h2>",
            unsafe_allow_html=True
        )
        st.success(f"Your response '{response}' for transaction ID {transaction_id} has been successfully recorded.")
        st.markdown("You may now close this page.")
        return

    # --- SIDEBAR LAYOUT ---
    # Contains logo, navigation buttons, and styles for sidebar.
    with st.sidebar:
        # Display logo at top of sidebar
        st.markdown(
            "<div style='text-align:center; padding-top:20px;'><img src='https://img.icons8.com/color/96/000000/security-checked.png'/></div>",
            unsafe_allow_html=True
        )
        # Style the sidebar with white background and vertical border
        st.markdown("""
            <style>
            section[data-testid='stSidebar'] {
                background-color: white !important;
                width: 220px !important;
                border-right: 2px solid #ccc;
            }
            div[data-testid="stSidebar"]::after {
                content: "";
                position: absolute;
                top: 0;
                left: 219px;
                width: 1px;
                height: 100vh;
                background-color: #ccc;
            }
            </style>
        """, unsafe_allow_html=True)
        # Horizontal rule below logo
        st.markdown("<hr style='border:0; border-top:1px solid #ccc; margin:20px 0;'>", unsafe_allow_html=True)
        # Sidebar navigation buttons
        st.button("Settings")
        st.button("Help & Support")
        st.button("Logout")

    # Sidebar button style
    st.markdown("""
        <style>
        div[data-testid="stSidebar"] button {
            background-color: white !important;
            border: 1px solid #ccc !important;
            color: black !important;
            font-weight: 500;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- METRIC CARDS ---
    # Display summary metrics: Fraudulent, Legitimate, and Total transactions.
    try:
        df_all = load_transactions()
        fraud_count = df_all[df_all["is_fraud"] == 1].shape[0]
        legit_count = df_all[df_all["is_fraud"] == 0].shape[0]
        total_transactions = df_all.shape[0]
        # Build a transaction_id -> customer_id map for lookup in preview_df
        id_map = df_all.set_index("transaction_id")["customer_id"].to_dict()
    except:
        st.error("❌ Failed to load live data from database.")
        fraud_count = 0
        legit_count = 0
        total_transactions = 0

    metric_cols = st.columns(3)
    with metric_cols[0]:
        # Number of fraudulent transactions
        st.markdown(f"""
        <div style='background-color:#fff; padding:20px; border-radius:10px; text-align:center'>
            <h4>Fraudulent Transactions</h4>
            <h2 style='color:#d32f2f;'>{fraud_count:,}</h2>
            <small style='color:#388E3C;'>+2.15%</small>
        </div>""", unsafe_allow_html=True)
    with metric_cols[1]:
        # Number of legitimate transactions
        st.markdown(f"""
        <div style='background-color:#fff; padding:20px; border-radius:10px; text-align:center'>
            <h4>Legitimate Transactions</h4>
            <h2 style='color:#388E3C;'>{legit_count:,}</h2>
            <small style='color:#d32f2f;'>-0.72%</small>
        </div>""", unsafe_allow_html=True)
    with metric_cols[2]:
        # Total number of transactions
        st.markdown(f"""
        <div style='background-color:#fff; padding:20px; border-radius:10px; text-align:center'>
            <h4>Total Transactions</h4>
            <h2>{total_transactions:,}</h2>
        </div>""", unsafe_allow_html=True)

    # --- PERFORMANCE CHART ---
    # Displays a stacked bar chart of fraudulent vs. legitimate transactions over months.
    st.markdown("### Performance")
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"]
    fraud_data = [1.2, 1.8, 1.5, 1.6, 1.9, 2.0, 2.2]
    legit_data = [2.2, 2.5, 2.4, 2.6, 2.7, 2.8, 2.9]
    import plotly.graph_objects as go
    fig = go.Figure(data=[
        go.Bar(name='Fraudulent', x=months, y=fraud_data, marker_color='#d32f2f'),
        go.Bar(name='Legitimate', x=months, y=legit_data, marker_color='#81c784')
    ])
    fig.update_layout(
        barmode='stack',
        xaxis_title='Month',
        yaxis_title='Transactions (Millions)',
        height=350
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- TRANSACTION FILTERING & TABLE ---
    # Allows filtering by Transaction ID, Type, and Fraud Status. Table displays main transaction details.
    st.markdown("### Transaction Table")
    if st.button("Refresh"):
        st.rerun()
    preview_df = df_all.copy()
    # Add columns for display
    preview_df['Transaction Type'] = preview_df['transaction_type']           # Transaction type column
    preview_df['Fraud Status'] = preview_df['is_fraud'].map({1: 'Fraudulent', 0: 'Not Fraud'})  # Fraud status column
    preview_df['Customer Details'] = 'View'                                   # Placeholder for details button
    if 'is_active' in preview_df.columns:
        preview_df['Transaction Status'] = preview_df['is_active'].map({1: 'Active', 0: 'Stopped'}) # Active/Stopped
        preview_df['Execution Status'] = preview_df['is_active'].map({1: 'Completed', 0: 'Cancelled'}) # Completed/Cancelled
    else:
        preview_df['Transaction Status'] = 'Unknown'
        preview_df['Execution Status'] = 'Unknown'

    # Select columns for manual table
    preview_df = preview_df[['transaction_id', 'amount', 'Transaction Type', 'Fraud Status',
                             'Customer Details', 'Transaction Status', 'Execution Status']]

    # Helper for styling fraud status
    def style_fraud_status(val):
        color = '#f8d7da' if val == 'Fraudulent' else '#d0f0c0'
        return f"background-color: {color}; border-radius:10px; text-align:center"

    # --- SEARCH & FILTERS ---
    search_term = st.text_input("🔍 Search by Transaction ID")
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        transaction_type_filter = st.selectbox("Transaction Type", options=["All", "CASH_OUT", "CASH_IN", "PAYMENT", "TRANSFER", "DEBIT"])
    with col_filter2:
        fraud_filter = st.selectbox("Fraud Filter", options=["All", "Fraud Only", "Not Fraud"])
    filtered_df = preview_df.copy()
    if search_term:
        filtered_df = filtered_df[filtered_df['transaction_id'].astype(str).str.contains(search_term)]
    if transaction_type_filter != "All":
        filtered_df = filtered_df[filtered_df['Transaction Type'] == transaction_type_filter]
    if fraud_filter == "Fraud Only":
        filtered_df = filtered_df[filtered_df['Fraud Status'] == "Fraudulent"]
    elif fraud_filter == "Not Fraud":
        filtered_df = filtered_df[filtered_df['Fraud Status'] == "Not Fraud"]

    # --- PAGINATION FOR TABLE ---
    page_size = 10
    total_rows = filtered_df.shape[0]
    total_pages = (total_rows - 1) // page_size + 1
    if "dashboard_page" not in st.session_state:
        st.session_state.dashboard_page = 1
    start_idx = (st.session_state.dashboard_page - 1) * page_size
    end_idx = start_idx + page_size
    page_data = filtered_df.iloc[start_idx:end_idx]

    # --- TRANSACTION TABLE ---
    # Table columns: Transaction ID, Amount, Type, Fraud Status, Customer Details, Transaction Status, Execution Status
    st.markdown("<h5 style='margin-top:30px;'>Current Data:</h5>", unsafe_allow_html=True)
    header1, header2, header3, header4, header5, header6, header7 = st.columns([1, 1, 1.5, 1.2, 1.2, 1.5, 1.5])
    header1.markdown("**Transaction ID**")  # Unique ID for transaction
    header2.markdown("**Amount**")          # Transaction amount
    header3.markdown("**Transaction Type**")# Type: CASH_OUT, PAYMENT, etc.
    header4.markdown("**Fraud Status**")    # Whether transaction is flagged as fraud
    header5.markdown("**Customer Details**")# Button to view customer info
    header6.markdown("**Transaction Status**") # Status: Waiting/Active/Stopped
    header7.markdown("**Execution Status**")   # Status: Completed/Cancelled/N/A
    # Horizontal rule after headers
    st.markdown("<hr>", unsafe_allow_html=True)

    for idx, row in page_data.iterrows():
        with st.container():
            cols = st.columns([1, 1, 1.5, 1.2, 1.2, 1.5, 1.5])
            # Transaction ID column
            cols[0].markdown(f"**{row['transaction_id']}**")
            # Amount column
            cols[1].markdown(f"{row['amount']:.2f}")
            # Transaction Type column
            cols[2].markdown(row['Transaction Type'])
            # Fraud Status column, styled
            bg_color = '#f8d7da' if row['Fraud Status']=='Fraudulent' else '#d0f0c0'
            cols[3].markdown(f"<div style='background-color:{bg_color};padding:5px 10px;border-radius:20px;display:inline-block;text-align:center'>{row['Fraud Status']}</div>", unsafe_allow_html=True)

            detail_key = f"detail_{row['transaction_id']}"
            alert_key = f"alert_{row['transaction_id']}"
            send_key = f"send_{row['transaction_id']}"
            response_key = f"response_{row['transaction_id']}"

            # Lookup customer_id from transaction
            customer_row = df_all[df_all['transaction_id'] == row['transaction_id']]
            customer_id = customer_row['customer_id'].values[0] if not customer_row.empty else ""

            # Customer Details column: show details if button clicked
            if cols[4].button("Details", key=detail_key):
                cust = get_customer_info(customer_id)
                if cust:
                    st.markdown(f"""
                    <div style='background-color:#eef2f7; padding:10px; border-radius:8px;'>
                    <strong>Name:</strong> {cust[0]}<br>
                    <strong>Phone:</strong> {cust[1]}<br>
                    <strong>City:</strong> {cust[2]}<br>
                    <strong>Email:</strong> {cust[3]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("No customer info found.")

            # --- Transaction Status column (cols[5]) ---
            # If fraudulent, allow sending confirmation email and show status based on response
            responses = get_customer_responses(row['transaction_id']) if row['Fraud Status'] == "Fraudulent" else []
            if row['Fraud Status'] == "Fraudulent":
                # Send button: triggers sending confirmation email to customer
                if cols[5].button("Send", key=send_key):
                    cust = get_customer_info(customer_id)
                    if cust and cust[3]:
                        success = send_email_confirmation(cust[3], row['transaction_id'])
                        if success:
                            cols[5].success("✅ Email sent successfully.")
                    else:
                        cols[5].error("No email found.")
            # Show transaction status: Waiting (no response), Active (YES), Stopped (NO)
            if row['Fraud Status'] == "Fraudulent":
                if responses:
                    latest_response = responses[0][0].upper()
                    # YES: Active, NO: Stopped, else: Waiting
                    if latest_response == "YES":
                        cols[5].markdown("<div style='background-color:#d0f0c0; padding:5px 10px; border-radius:20px; display:inline-block; text-align:center;'>Active</div>", unsafe_allow_html=True)
                    elif latest_response == "NO":
                        cols[5].markdown("<div style='background-color:#f8d7da; padding:5px 10px; border-radius:20px; display:inline-block; text-align:center;'>Stopped</div>", unsafe_allow_html=True)
                    else:
                        cols[5].markdown("<div style='background-color:#fff3cd; padding:5px 10px; border-radius:20px; display:inline-block; text-align:center;'>Waiting</div>", unsafe_allow_html=True)
                else:
                    # No response yet, show Waiting
                    cols[5].markdown("<div style='background-color:#fff3cd; padding:5px 10px; border-radius:20px; display:inline-block; text-align:center;'>Waiting</div>", unsafe_allow_html=True)
            else:
                # Not fraudulent: show Legitimate
                cols[5].markdown("<div style='background-color:#e2e3e5; padding:5px 10px; border-radius:20px; display:inline-block; text-align:center;'>Legitimate</div>", unsafe_allow_html=True)

            # --- Execution Status column (cols[6]) ---
            # Shows Completed/Cancelled if response received, Waiting otherwise
            show_details_key = f"show_exec_{row['transaction_id']}"
            detail_toggle_key = f"exec_detail_toggle_{row['transaction_id']}"
            if detail_toggle_key not in st.session_state:
                st.session_state[detail_toggle_key] = False
            if row['Fraud Status'] == "Fraudulent":
                if responses:
                    latest_response, latest_time = responses[0][0].upper(), responses[0][1]
                    if latest_response in ["YES", "NO"]:
                        status_label = "Completed" if latest_response == "YES" else "Cancelled"
                        with cols[6]:
                            if st.button(status_label, key=show_details_key):
                                st.session_state[detail_toggle_key] = not st.session_state[detail_toggle_key]
                            if st.session_state[detail_toggle_key]:
                                # Show response details with timestamp
                                st.markdown(
                                    f"<div style='background-color:#f0f0f0; padding:6px 12px; border-radius:15px; display:inline-block; font-size:13px; margin-top:5px;'>Response: <strong>{latest_response}</strong><br><small>{latest_time.strftime('%Y-%m-%d %H:%M')}</small></div>",
                                    unsafe_allow_html=True
                                )
                    else:
                        # Waiting for response
                        cols[6].markdown("<div style='background-color:#fff3cd; padding:5px 10px; border-radius:20px; display:inline-block; text-align:center;'>Waiting</div>", unsafe_allow_html=True)
                else:
                    # Waiting for response
                    cols[6].markdown("<div style='background-color:#fff3cd; padding:5px 10px; border-radius:20px; display:inline-block; text-align:center;'>Waiting</div>", unsafe_allow_html=True)
            else:
                # Not applicable for legitimate transactions
                cols[6].markdown("<div style='background-color:#e2e3e5; padding:5px 10px; border-radius:20px; display:inline-block; text-align:center;'>N/A</div>", unsafe_allow_html=True)

            # Add horizontal rule after each row for clarity
            st.markdown("<hr style='margin-top:5px; margin-bottom:5px; border-color:#ddd;'>", unsafe_allow_html=True)

    # --- PAGINATION CONTROLS ---
    col_prev, col_page, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button(" Previous", key="dashboard_prev") and st.session_state.dashboard_page > 1:
            st.session_state.dashboard_page -= 1
            st.rerun()
    with col_next:
        if st.button("Next ➡️", key="dashboard_next") and st.session_state.dashboard_page < total_pages:
            st.session_state.dashboard_page += 1
            st.rerun()
    with col_page:
        st.markdown(f"<div style='text-align:center;'>Page {st.session_state.dashboard_page} of {total_pages}</div>", unsafe_allow_html=True)
    return

# ==============================================================
# LOGIN & SESSION MANAGEMENT
# ==============================================================

# Function: main
# Handles user login, OTP verification, and routing to dashboard or customer response.
def main():
    # Initialize session state variables for authentication and OTP
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'email' not in st.session_state:
        st.session_state['email'] = None
    if 'otp_verified' not in st.session_state:
        st.session_state['otp_verified'] = False
    if 'otp_code' not in st.session_state:
        st.session_state['otp_code'] = None

    # --- CUSTOMER RESPONSE HANDLING FROM EMAIL LINK (NO LOGIN REQUIRED) ---
    query_params = st.query_params
    if 'tx' in query_params and 'r' in query_params:
        # If accessed from email confirmation link, process response without login
        fraud_detection_system()

    # --- LOGIN FORM FOR STAFF ---
    elif not st.session_state['logged_in']:
        # Login form for staff authentication
        st.markdown(
            "<h2 style='color:#004085'>🔐 Secure Employee Login</h2>",
            unsafe_allow_html=True
        )
        st.write("Please login to continue.")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        # Login button: verifies credentials and sends OTP
        if st.button("Login"):
            with st.spinner('Verifying credentials...'):
                time.sleep(1.5)
                user = login_user(email, password)
                if user:
                    st.session_state['logged_in'] = True
                    st.session_state['email'] = email
                    st.session_state['otp_code'] = str(np.random.randint(100000, 999999))
                    st.session_state['otp_verified'] = False
                    actual_email = user[1]  # Email from database
                    otp_sent = send_otp_email(actual_email, st.session_state['otp_code'])
                    if otp_sent:
                        st.success("OTP has been sent to your email.")
                    else:
                        st.error("❌ Failed to send OTP. Please check your email and try again.")
                    st.rerun()
                else:
                    st.error("Invalid Email or Password.")
        # Direct access for testing without OTP (for development only)
        if st.button("Direct Access for Testing"):
            st.session_state['logged_in'] = True
            st.session_state['email'] = "test_user@securebank.com"
            st.session_state['otp_verified'] = True
            st.session_state['otp_code'] = None
            st.success("You have logged in directly for testing purposes.")
            time.sleep(1)
            st.rerun()

    # --- OTP VERIFICATION FORM ---
    elif st.session_state['logged_in'] and not st.session_state['otp_verified']:
        # OTP check after login; user must enter OTP sent to email
        st.markdown(
            "<h2 style='color:#004085'>📨 Verify OTP Sent to Email</h2>",
            unsafe_allow_html=True
        )
        st.write("Please enter the OTP sent to your email.")
        otp_input = st.text_input("Enter OTP")
        # Verify OTP button
        if st.button("Verify OTP"):
            if otp_input == st.session_state['otp_code']:
                st.success("OTP Verified successfully!")
                st.session_state['otp_verified'] = True
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid OTP. Please try again.")

    # --- SHOW FRAUD DASHBOARD ONCE LOGGED IN AND VERIFIED ---
    else:
        fraud_detection_system()

# ==============================================================
# MAIN ENTRY POINT
# ==============================================================

if __name__ == "__main__":
    main()
