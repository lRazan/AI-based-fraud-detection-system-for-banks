import streamlit as st

# ==============================================================
# IMPORTS
# ==============================================================

# --------------------------------------------------------------
# Standard Library Imports
# --------------------------------------------------------------
import os
import time
import numpy as np
import pandas as pd

# --------------------------------------------------------------
# Third Party/External Libraries
# --------------------------------------------------------------
import pymysql
import yagmail
import joblib
import plotly.graph_objects as go
from streamlit_navigation_bar import st_navbar

# Path to logo file used in header
logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.svg")

# ==============================================================
# PERFORMANCE & CACHING OPTIONS
# ==============================================================
st.cache_data(ttl=300)

# ==============================================================
# FRAUD DETECTION SYSTEM - STREAMLIT APP
# Structured code with clear comments and logical section headers.
# ==============================================================

# --------------------------------------------------------------
# PAGE CONFIGURATION & GLOBAL STYLES
# --------------------------------------------------------------
st.set_page_config(page_title="Fraud Detection System", page_icon="🛡️", layout="wide")

# --------------------------------------------------------------
# Function: show_green_header
# Displays a unified green header bar with logo and title for all pages.
# --------------------------------------------------------------
def show_green_header():
    import base64
    st.markdown(
        f'''
        <div style='
            background-color: #2e7d32;
            padding: 12px 30px;
            display: flex;
            align-items: center;
            border-radius: 0 0 10px 10px;
            margin-bottom: 10px;
        '>
            <img src="data:image/svg+xml;base64,{base64.b64encode(open(logo_path, "rb").read()).decode()}" width="30" style="margin-right:12px;" />
            <span style='color:white; font-size:16px; font-weight:bold;'>Banking Fraud Detection System</span>
        </div>
        ''',
        unsafe_allow_html=True
    )

# ==============================================================
# DATABASE FUNCTIONS
# ==============================================================

# --------------------------------------------------------------
# Function: login_user
# Authenticates user by email and password from the users table.
# --------------------------------------------------------------
def login_user(email, password):
    try:
        conn = pymysql.connect(
            host=os.getenv("MYSQLHOST"),
            user=os.getenv("MYSQLUSER"),
            password=os.getenv("MYSQLPASSWORD"),
            database=os.getenv("MYSQLDATABASE"),
            port=int(os.getenv("MYSQLPORT"))
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

# --------------------------------------------------------------
# Function: load_transactions
# Loads all transactions from the database into a DataFrame.
# --------------------------------------------------------------
def load_transactions():
    conn = pymysql.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=int(os.getenv("MYSQLPORT"))
    )
    df = pd.read_sql("SELECT * FROM transactions", conn)
    conn.close()
    return df

# --------------------------------------------------------------
# Function: get_customer_info
# Retrieves customer details (name, phone, city, email) by customer_id.
# --------------------------------------------------------------
def get_customer_info(customer_id):
    conn = pymysql.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=int(os.getenv("MYSQLPORT"))
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

# --------------------------------------------------------------
# Function: send_email_confirmation
# Sends a confirmation email to the customer for a specific transaction.
# --------------------------------------------------------------
def send_email_confirmation(to_email, transaction_id):
    subject = f"Transaction #{transaction_id} Confirmation"
    body = f"""
  <html>
    <body>
      <p>Did you make transaction #{transaction_id}?</p>
      <p>
<a href="https://flask-confirm-api.onrender.com/confirm?tx={transaction_id}&r=YES">YES - I Confirm</a>
<a href="https://flask-confirm-api.onrender.com/confirm?tx={transaction_id}&r=NO">NO - This Was Not Me</a>
      </p>
    </body>
  </html>
    """
    try:
        yag = yagmail.SMTP(
            user=st.secrets["email"]["address"],
            password=st.secrets["email"]["password"]
        )
        yag.send(to=to_email, subject=subject, contents=[body])
        return True
    except Exception as e:
        return False

# --------------------------------------------------------------
# Function: send_otp_email
# Sends an OTP verification code to the user's email address.
# --------------------------------------------------------------
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
        yag = yagmail.SMTP(
            user=st.secrets["email"]["address"],
            password=st.secrets["email"]["password"]
        )
        yag.send(to=to_email, subject=subject, contents=[body])
        return True
    except Exception as e:
        st.error(f"❌ Failed to send OTP: {e}")
        return False

# ==============================================================
# CUSTOMER RESPONSE HANDLING
# ==============================================================

# --------------------------------------------------------------
# Function: save_customer_response
# Saves a customer's YES/NO response for a transaction in the database.
# --------------------------------------------------------------
def save_customer_response(transaction_id, response):
    try:
        conn = pymysql.connect(
            host=os.getenv("MYSQLHOST"),
            user=os.getenv("MYSQLUSER"),
            password=os.getenv("MYSQLPASSWORD"),
            database=os.getenv("MYSQLDATABASE"),
            port=int(os.getenv("MYSQLPORT"))
        )
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

# --------------------------------------------------------------
# Function: get_customer_responses
# Retrieves all responses for a given transaction (most recent first).
# --------------------------------------------------------------
def get_customer_responses(transaction_id):
    conn = pymysql.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=int(os.getenv("MYSQLPORT"))
    )
    cursor = conn.cursor()
    cursor.execute(
        "SELECT response, created_at FROM transaction_feedback WHERE transaction_id = %s ORDER BY id DESC",
        (transaction_id,)
    )
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

#
# ==============================================================
# FRAUD DETECTION DASHBOARD UI
# ==============================================================

# --------------------------------------------------------------
# Function: fraud_detection_system
# Main dashboard UI for fraud detection, staff view, and customer response.
# --------------------------------------------------------------
def fraud_detection_system():
    show_green_header()

    # ----------------------------------------------------------
    # Navigation buttons for Dashboard, Upload Transactions, Logout
    # ----------------------------------------------------------
    with st.container():
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("Dashboard", key="btn_dashboard"):
                st.session_state["selected_page"] = "Dashboard"
                st.rerun()
        with col2:
            if st.button("Upload Transactions", key="btn_upload"):
                st.session_state["selected_page"] = "Upload Transactions"
                st.rerun()
        with col3:
            if st.button("Logout", key="btn_logout"):
                st.session_state["selected_page"] = "Logout"
                st.rerun()

    selected_page = st.session_state.get("selected_page", "Dashboard")

    # Initialize DataFrame to avoid UnboundLocalError
    df_all = pd.DataFrame()

    # ----------------------------------------------------------
    # LOAD MODEL BEFORE ANY PAGE LOGIC
    # Loads the fraud detection model from local file or downloads it if missing.
    # ----------------------------------------------------------
    import urllib.request
    model_path = "fraud_detection_PKL2_model.pkl"
    model_url = "https://github.com/lRazan/AI-based-fraud-detection-system-for-banks/releases/download/v1.0.0/fraud_detection_PKL2_model.pkl"
    try:
        if not os.path.exists(model_path):
            with st.spinner("Downloading model..."):
                urllib.request.urlretrieve(model_url, model_path)
        model = joblib.load(model_path)
    except Exception as e:
        st.error(f"❌ Failed to load model: {e}")
        model = None

    # ----------------------------------------------------------
    # UPLOAD TRANSACTIONS PAGE
    # Allows staff to upload new transactions from CSV and store them in the database.
    # ----------------------------------------------------------
    if selected_page == "Upload Transactions":
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
                st.dataframe(df_csv[["transactionID", "amount", "type", "fraud_probability", "prediction"]])

                # Insert uploaded transactions into the database
                import pymysql
                try:
                    df_csv.rename(columns={
                        "transactionID": "transaction_id",
                        "type": "transaction_type",
                        "isFlaggedFraud": "is_fraud"
                    }, inplace=True)

                    conn = pymysql.connect(
                        host=os.getenv("MYSQLHOST"),
                        user=os.getenv("MYSQLUSER"),
                        password=os.getenv("MYSQLPASSWORD"),
                        database=os.getenv("MYSQLDATABASE"),
                        port=int(os.getenv("MYSQLPORT"))
                    )
                    cursor = conn.cursor()

                    for _, row in df_csv.iterrows():
                        cursor.execute("""
                            INSERT INTO transactions (transaction_id, amount, transaction_type, is_fraud)
                            VALUES (%s, %s, %s, %s)
                        """, (
                            int(row['transaction_id']), float(row['amount']), row['transaction_type'],
                            int(row['is_fraud'])
                        ))

                    conn.commit()
                    cursor.close()
                    conn.close()
                except Exception as e:
                    st.error(f"❌ Failed to insert data into database: {e}")
            except Exception as e:
                st.error(f"Error processing uploaded file: {e}")
        return
    elif selected_page == "Dashboard":
        selected_page = "dashboard"
    elif selected_page == "Logout":
        st.session_state.clear()
        st.success("You have been logged out.")
        st.rerun()
        return

    # ----------------------------------------------------------
    # CUSTOMER RESPONSE HANDLING VIA EMAIL LINK
    # Allows customer to respond YES/NO via email link; processes the response.
    # ----------------------------------------------------------
    from streamlit_autorefresh import st_autorefresh
    query_params = st.query_params
    # Prevent duplicate processing if already handled (e.g., on auto-reload)
    if st.session_state.get('response_already_processed'):
        return
    if 'tx' in query_params and 'r' in query_params:
        try:
            # Convert tx value from URL to transaction_id as integer
            transaction_id_raw = query_params['tx'][0]
            transaction_id = int(transaction_id_raw)
        except Exception:
            st.error("Invalid transaction ID format in URL.")
            return
        response = query_params['r'][0].upper()
        # Check if transaction_id exists in the database
        df_check = load_transactions()
        df_check['transaction_id'] = df_check['transaction_id'].astype(int)
        if transaction_id not in df_check['transaction_id'].values:
            st.error(f"Transaction ID {transaction_id} does not exist in the transaction table.")
            return
        # Save the response in transaction_feedback table
        save_customer_response(transaction_id, response)
        st.session_state['response_already_processed'] = True
        st.query_params.clear()
        # Update the transaction status (is_active) according to the response
        conn = None
        try:
            conn = pymysql.connect(
                host=os.getenv("MYSQLHOST"),
                user=os.getenv("MYSQLUSER"),
                password=os.getenv("MYSQLPASSWORD"),
                database=os.getenv("MYSQLDATABASE"),
                port=int(os.getenv("MYSQLPORT"))
            )
            cursor = conn.cursor()
            if response == 'NO':
                cursor.execute("UPDATE transactions SET is_active = 0 WHERE transaction_id = %s", (transaction_id,))
            elif response == 'YES':
                cursor.execute("UPDATE transactions SET is_active = 1 WHERE transaction_id = %s", (transaction_id,))
            conn.commit()
            cursor.close()
        except Exception as e:
            st.error("Could not connect to the database. Please try again later.")
            return
        finally:
            if conn:
                conn.close()
        st.session_state[f'alert_sent_{transaction_id}'] = True
        st.session_state[f'show_alert_{transaction_id}'] = True
        # Show confirmation message to the customer
        st.markdown(
            "<h2 style='color:#004085'>Response Received</h2>",
            unsafe_allow_html=True
        )
        st.success(f"Your response '{response}' for transaction ID {transaction_id} has been successfully recorded.")
        st.markdown("You may now close this page.")
        return

    # ----------------------------------------------------------
    # METRIC CARDS
    # Display summary metrics: Fraudulent, Legitimate, and Total transactions.
    # ----------------------------------------------------------
    try:
        df_all = load_transactions()
        #st.subheader("🔍 Debug: Preview of loaded transactions")
        #st.write(df_all.head())
        fraud_count = df_all[df_all["is_fraud"] == 1].shape[0]
        legit_count = df_all[df_all["is_fraud"] == 0].shape[0]
        total_transactions = df_all.shape[0]
        # Build a transaction_id -> customer_id map for lookup in preview_df
        if "customer_id" in df_all.columns:
            id_map = df_all.set_index("transaction_id")["customer_id"].fillna("N/A").to_dict()
        else:
            id_map = {}
    except:
        st.error("❌ Failed to load live data from database.")
        df_all = pd.DataFrame()
        fraud_count = 0
        legit_count = 0
        total_transactions = 0

    # ----------------------------------------------------------
    # KPI Cards: Use st.metric for summary metrics
    # ----------------------------------------------------------
    col1, col2, col3 = st.columns(3, gap="large")
    with col1:
        st.metric(label="Fraudulent", value=f"{fraud_count:,}", delta="▲ 2.15%", delta_color="inverse")
    with col2:
        st.metric(label="Legitimate", value=f"{legit_count:,}", delta="▲ 1.07%", delta_color="normal")
    with col3:
        st.metric(label="Total", value=f"{total_transactions:,}", delta="")

    # ----------------------------------------------------------
    # PERFORMANCE CHART
    # Displays a stacked bar chart of fraudulent vs. legitimate transactions over months (green theme).
    # ----------------------------------------------------------
    st.subheader("Performance Overview")
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"]
    fraud_data = [v * 8 for v in [1.2, 1.8, 1.5, 1.6, 1.9, 1.4, 2.2]]
    legit_data = [v * 8 for v in [2.2, 2.5, 2.4, 1.6, 1.7, 2, 2.9]]
    fig = go.Figure(data=[
        go.Bar(name='Fraudulent', x=months, y=fraud_data, marker_color='rgba(144, 238, 144, 0.85)', width=0.4),
        go.Bar(name='Legitimate', x=months, y=legit_data, marker_color='rgba(0, 128, 0, 0.85)', width=0.4)
    ])
    fig.update_layout(
        barmode='stack',
        xaxis_title='Month',
        yaxis_title='Transactions',
        height=280,
        yaxis=dict(range=[0, 20])
        # width omitted to allow responsive sizing
    )
    st.plotly_chart(fig, use_container_width=True)

    # ----------------------------------------------------------
    # TRANSACTION FILTERING & TABLE
    # Allows filtering by Transaction ID, Type, and Fraud Status. Table displays main transaction details.
    # ----------------------------------------------------------
    st.subheader("Transaction Table")
    # Compact row for search/type/fraud filters (no refresh)
    with st.container():
        col_search, col_filter1, col_filter2 = st.columns([2, 2, 2])
        with col_search:
            st.text_input("Transaction ID", key="search_term")
        with col_filter1:
            transaction_type_filter = st.selectbox("Type", options=["All", "CASH_OUT", "CASH_IN", "PAYMENT", "TRANSFER", "DEBIT"])
        with col_filter2:
            fraud_filter = st.selectbox("Fraud", options=["All", "Fraud Only", "Not Fraud"])

    search_term = st.session_state.get("search_term", "")
    preview_df = df_all.copy()
    # Add columns for display
    preview_df['Transaction Type'] = preview_df['transaction_type']           # Transaction type column
    preview_df['Fraud Status'] = preview_df['is_fraud'].map({1: 'Fraud', 0: 'Not Fraud'})  # Fraud status column
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

    # Helper function for styling fraud status cell
    def style_fraud_status(val):
        color = '#f8d7da' if val == 'Fraud' else '#d0f0c0'
        return f"background-color: {color}; border-radius:10px; text-align:center"

    # ----------------------------------------------------------
    # SEARCH & FILTERS
    # ----------------------------------------------------------
    filtered_df = preview_df.copy()
    if search_term:
        filtered_df = filtered_df[filtered_df['transaction_id'].astype(str).str.contains(search_term)]
    if transaction_type_filter != "All":
        filtered_df = filtered_df[filtered_df['Transaction Type'] == transaction_type_filter]
    if fraud_filter == "Fraud Only":
        filtered_df = filtered_df[filtered_df['Fraud Status'] == "Fraud"]
    elif fraud_filter == "Not Fraud":
        filtered_df = filtered_df[filtered_df['Fraud Status'] == "Not Fraud"]

    # ----------------------------------------------------------
    # PAGINATION FOR TABLE
    # ----------------------------------------------------------
    page_size = 8
    total_rows = filtered_df.shape[0]
    total_pages = (total_rows - 1) // page_size + 1
    if "dashboard_page" not in st.session_state:
        st.session_state.dashboard_page = 1
    start_idx = (st.session_state.dashboard_page - 1) * page_size
    end_idx = start_idx + page_size
    page_data = filtered_df.iloc[start_idx:end_idx]

    # ----------------------------------------------------------
    # TRANSACTION TABLE
    # Table columns: Transaction ID, Amount, Type, Fraud Status, Customer Details, Transaction Status, Execution Status
    # ----------------------------------------------------------
    header1, header2, header3, header4, header5, header6, header7 = st.columns([0.9, 0.9, 1.2, 1.1, 1.1, 1.2, 1.2])
    header1.text("Transaction ID")
    header2.text("Amount")
    header3.text("Transaction Type")
    header4.text("Fraud Status")
    header5.text("Customer Details")
    header6.text("Transaction Status")
    header7.text("Execution Status")

    for idx, row in page_data.iterrows():
        with st.container():
            cols = st.columns([0.9, 0.9, 1.2, 1.1, 1.1, 1.2, 1.2])
            # Transaction ID column
            cols[0].text(str(row['transaction_id']))
            # Amount column
            cols[1].text(f"{row['amount']:.2f}")
            # Transaction Type column
            cols[2].text(str(row['Transaction Type']))
            # Fraud Status column
            fraud_status = str(row['Fraud Status'])
            if fraud_status == "Fraud":
                cols[3].markdown("<span style='color:red;'>Fraud</span>", unsafe_allow_html=True)
            else:
                cols[3].markdown("<span style='color:green;'>Not Fraud</span>", unsafe_allow_html=True)

            detail_key = f"detail_{row['transaction_id']}"
            alert_key = f"alert_{row['transaction_id']}"
            send_key = f"send_{row['transaction_id']}"
            response_key = f"response_{row['transaction_id']}"

            # Lookup customer_id from transaction
            customer_row = df_all[df_all['transaction_id'] == row['transaction_id']]
            customer_id = customer_row['customer_id'].values[0] if not customer_row.empty and pd.notnull(customer_row['customer_id'].values[0]) else ""

            # Customer Details column: show details if button clicked
            if cols[4].button("Details", key=detail_key):
                if customer_id:
                    cust = get_customer_info(customer_id)
                else:
                    cust = None
                if cust:
                    st.text(f"Name: {cust[0]}")
                    st.text(f"Phone: {cust[1]}")
                    st.text(f"City: {cust[2]}")
                    st.text(f"Email: {cust[3]}")
                else:
                    st.warning("No customer info found.")
            else:
                cols[4].text("")

            # Transaction Status column (cols[5])
            responses = get_customer_responses(row['transaction_id']) if row['Fraud Status'] == "Fraud" else []
            # Only show "Send" button if not yet responded YES/NO
            if row['Fraud Status'] == "Fraud" and (not responses or responses[0][0].upper() not in ["YES", "NO"]):
                send_key = f"send_{row['transaction_id']}"
                if cols[5].button("Send", key=send_key):
                    cust = get_customer_info(customer_id)
                    if cust and cust[3]:
                        success = send_email_confirmation(cust[3], row['transaction_id'])
                        if success:
                            cols[5].markdown("<span style='color:green;'>Sent</span>", unsafe_allow_html=True)
                    else:
                        cols[5].markdown("<span style='color:red;'>No Email</span>", unsafe_allow_html=True)
            # Show transaction status: Active (YES), Stopped (NO), Legitimate (gray)
            if row['Fraud Status'] == "Fraud":
                if responses:
                    latest_response = responses[0][0].upper()
                    if latest_response == "YES":
                        cols[5].markdown("<span style='color:green;'>Active</span>", unsafe_allow_html=True)
                    elif latest_response == "NO":
                        cols[5].markdown("<span style='color:red;'>Stopped</span>", unsafe_allow_html=True)
                # Do NOT show 'Waiting' here per new specs
            else:
                cols[5].markdown("<span style='color:gray;'>Legitimate</span>", unsafe_allow_html=True)

            # Execution Status column (cols[6]) - refactored for button logic
            if row['Fraud Status'] == "Fraud":
                if responses:
                    latest_response, latest_time = responses[0][0].upper(), responses[0][1]
                    # YES branch
                    if latest_response == "YES":
                        if f"show_yes_{row['transaction_id']}" not in st.session_state:
                            st.session_state[f"show_yes_{row['transaction_id']}"] = False
                        if cols[6].button("Complete", key=f"complete_{row['transaction_id']}"):
                            try:
                                conn = pymysql.connect(
                                    host=os.getenv("MYSQLHOST"),
                                    user=os.getenv("MYSQLUSER"),
                                    password=os.getenv("MYSQLPASSWORD"),
                                    database=os.getenv("MYSQLDATABASE"),
                                    port=int(os.getenv("MYSQLPORT"))
                                )
                                cursor = conn.cursor()
                                try:
                                    cursor.execute("UPDATE transactions SET is_active = 1 WHERE transaction_id = %s", (row['transaction_id'],))
                                except pymysql.err.ProgrammingError as e:
                                    if "Unknown column 'is_active'" not in str(e):
                                        raise
                                conn.commit()
                                cursor.close()
                                conn.close()
                            except:
                                pass
                            st.session_state[f"show_yes_{row['transaction_id']}"] = True
                            st.session_state[f"response_time_{row['transaction_id']}"] = latest_time
                            st.session_state[f"response_value_{row['transaction_id']}"] = latest_response
                        if st.session_state.get(f"show_yes_{row['transaction_id']}"):
                            ts = st.session_state.get(f"response_time_{row['transaction_id']}", latest_time)
                            rv = st.session_state.get(f"response_value_{row['transaction_id']}", "YES")
                            cols[6].markdown(f"<span style='color:green;'>{rv} at {ts}</span>", unsafe_allow_html=True)
                    # NO branch
                    elif latest_response == "NO":
                        if f"show_no_{row['transaction_id']}" not in st.session_state:
                            st.session_state[f"show_no_{row['transaction_id']}"] = False
                        if cols[6].button("Cancel", key=f"cancel_{row['transaction_id']}"):
                            try:
                                conn = pymysql.connect(
                                    host=os.getenv("MYSQLHOST"),
                                    user=os.getenv("MYSQLUSER"),
                                    password=os.getenv("MYSQLPASSWORD"),
                                    database=os.getenv("MYSQLDATABASE"),
                                    port=int(os.getenv("MYSQLPORT"))
                                )
                                cursor = conn.cursor()
                                try:
                                    cursor.execute("UPDATE transactions SET is_active = 0 WHERE transaction_id = %s", (row['transaction_id'],))
                                except pymysql.err.ProgrammingError as e:
                                    if "Unknown column 'is_active'" not in str(e):
                                        raise
                                conn.commit()
                                cursor.close()
                                conn.close()
                            except:
                                pass
                            st.session_state[f"show_no_{row['transaction_id']}"] = True
                            st.session_state[f"response_time_{row['transaction_id']}"] = latest_time
                            st.session_state[f"response_value_{row['transaction_id']}"] = latest_response
                        if st.session_state.get(f"show_no_{row['transaction_id']}"):
                            ts = st.session_state.get(f"response_time_{row['transaction_id']}", latest_time)
                            rv = st.session_state.get(f"response_value_{row['transaction_id']}", "NO")
                            cols[6].markdown(f"<span style='color:red;'>{rv} at {ts}</span>", unsafe_allow_html=True)
                    else:
                        cols[6].markdown("<span style='color:#c97b00;'>Waiting</span>", unsafe_allow_html=True)
                else:
                    cols[6].markdown("<span style='color:#c97b00;'>Waiting</span>", unsafe_allow_html=True)
            else:
                cols[6].markdown("<span style='color:gray;'>N/A</span>", unsafe_allow_html=True)

    # ----------------------------------------------------------
    # PAGINATION CONTROLS
    # ----------------------------------------------------------
    col_prev, col_page, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("< Previous", key="dashboard_prev") and st.session_state.dashboard_page > 1:
            st.session_state.dashboard_page -= 1
            st.rerun()
    with col_next:
        if st.button("Next >", key="dashboard_next") and st.session_state.dashboard_page < total_pages:
            st.session_state.dashboard_page += 1
            st.rerun()
    with col_page:
        st.text(f"Page {st.session_state.dashboard_page} of {total_pages}")
    return

# ==============================================================
# LOGIN & SESSION MANAGEMENT
# ==============================================================

# --------------------------------------------------------------
# Function: main
# Handles user login, OTP verification, and routing to dashboard or customer response.
# --------------------------------------------------------------
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

    # ----------------------------------------------------------
    # CUSTOMER RESPONSE HANDLING FROM EMAIL LINK (NO LOGIN REQUIRED)
    # If a customer clicks an email link, process their response here, no login needed.
    # ----------------------------------------------------------
    query_params = st.query_params
    if 'tx' in query_params and 'r' in query_params:
        show_green_header()
        fraud_detection_system()

    # ----------------------------------------------------------
    # LOGIN FORM FOR STAFF
    # Collects email and password for staff login, sends OTP if credentials are valid.
    # ----------------------------------------------------------
    elif not st.session_state['logged_in']:
        # Custom CSS for login background and button
        st.markdown(
            """
            <style>
                .stApp {
                    background-image: url("https://images.unsplash.com/photo-1591696205602-2f950c417cb9?ixlib=rb-4.0.3&auto=format&fit=crop&w=2100&q=80");
                    background-size: cover;
                    background-position: center;
                }
            </style>
            """,
            unsafe_allow_html=True
        )
        # Green button styling
        st.markdown(
            """
            <style>
                div.stButton > button {
                    background-color: #2e7d32;
                    color: white;
                    font-weight: bold;
                    border-radius: 6px;
                }
            </style>
            """,
            unsafe_allow_html=True
        )
        with st.form("login_form"):
            email = st.text_input("Email", key="email_input")
            password = st.text_input("Password", type="password", key="pass_input")

            col_login, _ = st.columns([2, 20])
            with col_login:
                login_button = st.form_submit_button("Login")

            col_forgot, _ = st.columns([1, 5])
            with col_forgot:
                st.markdown(
                    "<div style='text-align:left; margin-top:-8px;'><a href='#' style='color:#14532d; font-size:12px;'>Forgot password?</a></div>",
                    unsafe_allow_html=True)

        # Direct Access button removed

        if login_button:
            with st.spinner('Verifying credentials...'):
                time.sleep(1.5)
                user = login_user(email, password)
                if user:
                    st.session_state['logged_in'] = True
                    st.session_state['email'] = email
                    st.session_state['otp_code'] = str(np.random.randint(100000, 999999))
                    st.session_state['otp_verified'] = False
                    actual_email = user[1]
                    otp_sent = send_otp_email(actual_email, st.session_state['otp_code'])
                    if otp_sent:
                        st.success("OTP has been sent to your email.")
                    else:
                        st.error("❌ Failed to send OTP. Please check your email and try again.")
                    st.rerun()
                else:
                    st.error("Invalid Email or Password.")

    # ----------------------------------------------------------
    # OTP VERIFICATION FORM
    # Displays OTP input after successful login; verifies OTP for access.
    # ----------------------------------------------------------
    elif st.session_state['logged_in'] and not st.session_state['otp_verified']:
        # Custom CSS for green background and button styling during OTP form
        st.markdown(
            """
            <style>
                .stApp {
                    background-image: url("https://images.unsplash.com/photo-1591696205602-2f950c417cb9?ixlib=rb-4.0.3&auto=format&fit=crop&w=2100&q=80");
                    background-size: cover;
                    background-position: center;
                }
                div.stButton > button {
                    background-color: #2e7d32;
                    color: white;
                    font-weight: bold;
                    border-radius: 6px;
                }
            </style>
            """,
            unsafe_allow_html=True
        )
        show_green_header()
        # OTP input field and verify button
        col_otp, _ = st.columns([5, 5])
        with col_otp:
            otp_input = st.text_input("Enter OTP", key="otp_input")
        col_btn_verify, _ = st.columns([1, 9])
        with col_btn_verify:
            if st.button("Verify"):
                if otp_input == st.session_state['otp_code']:
                    st.markdown("<p style='color:green; font-size:14px;'>Successfully</p>", unsafe_allow_html=True)
                    st.session_state['otp_verified'] = True
                    time.sleep(1)
                    st.rerun()
                else:
                    st.markdown("<p style='color:red; font-size:14px;'>Please try again</p>", unsafe_allow_html=True)

    # ----------------------------------------------------------
    # SHOW FRAUD DASHBOARD ONCE LOGGED IN AND VERIFIED
    # Displays the main dashboard after successful login and OTP verification.
    # ----------------------------------------------------------
    else:
        
        fraud_detection_system()

# ==============================================================
# MAIN ENTRY POINT
# ==============================================================

if __name__ == "__main__":
    main()