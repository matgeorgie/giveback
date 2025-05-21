import streamlit as st
import pandas as pd
import datetime
from db import get_connection
import matplotlib.pyplot as plt

st.set_page_config(page_title="User Dashboard", layout="wide")
st.title("🎉 User Dashboard")


if "user" not in st.session_state:
    st.error("You need to be logged in as an user to view the dashboard.")
    st.stop()

user_id = st.session_state["user"]["id"]

# Emergency Section
# Emergency Section - Updated Version
# Updated Emergency Section with fix for organization_id
st.subheader("🚨 Emergency Alerts")

conn = get_connection()
cursor = conn.cursor(dictionary=True)
cursor.execute("""
    SELECT e.id, e.title, e.description, e.created_at, 
           e.organization_id, o.org_name
    FROM emergencies e
    JOIN organizations o ON e.organization_id = o.id
    WHERE e.is_active = 1 AND e.is_approved = 1
    ORDER BY e.created_at DESC
    LIMIT 5
""")
emergencies = cursor.fetchall()

if emergencies:
    for emergency in emergencies:
        with st.container(border=True):
            col1, col2 = st.columns([0.8, 0.2])
            
            with col1:
                st.markdown(f"### {emergency['title']}")
                st.caption(f"Organization: {emergency['org_name']} | Posted: {emergency['created_at'].strftime('%Y-%m-%d %H:%M')}")
                st.write(emergency['description'])
            
            with col2:
                with st.popover("Respond to Emergency"):
                    st.write(f"How would you like to help with: {emergency['title']}?")
                    
                    response_type = st.radio(
                        "Response Type",
                        ["Donate Money", "Donate Items", "Volunteer Interest"],
                        key=f"emergency_{emergency['id']}_type"
                    )
                    
                    if response_type == "Donate Money":
                        amount = st.number_input(
                            "Amount to Donate",
                            min_value=1.0,
                            value=50.0,
                            step=10.0,
                            key=f"emergency_{emergency['id']}_amount"
                        )
                        if st.button("Submit Donation", key=f"emergency_{emergency['id']}_money_btn"):
                            try:
                                cursor.execute("""
                                    INSERT INTO donations 
                                    (user_id, organization_id, amount, donation_type)
                                    VALUES (%s, %s, %s, 'money')
                                """, (user_id, emergency['organization_id'], amount))
                                conn.commit()
                                st.success("Thank you for your emergency donation!")
                            except Exception as e:
                                st.error(f"Error processing donation: {e}")
                    
                    elif response_type == "Donate Items":
                        item_desc = st.text_area(
                            "Describe items you can provide",
                            key=f"emergency_{emergency['id']}_items"
                        )
                        if st.button("Submit Item Donation", key=f"emergency_{emergency['id']}_item_btn"):
                            try:
                                cursor.execute("""
                                    INSERT INTO donations 
                                    (user_id, organization_id, item_description, donation_type)
                                    VALUES (%s, %s, %s, 'item')
                                """, (user_id, emergency['organization_id'], item_desc))
                                conn.commit()
                                st.success("Thank you for your item donation offer!")
                            except Exception as e:
                                st.error(f"Error processing item donation: {e}")
                    
                    elif response_type == "Volunteer Interest":
                        contact_info = st.text_input(
                            "Your contact info (phone/email)",
                            value=st.session_state["user"].get("email", ""),
                            key=f"emergency_{emergency['id']}_contact"
                        )
                        skills = st.text_area(
                            "Your skills/how you can help",
                            key=f"emergency_{emergency['id']}_skills"
                        )
                        if st.button("Express Interest", key=f"emergency_{emergency['id']}_volunteer_btn"):
                            st.success("Thank you for your interest in volunteering! The organization will contact you.")
    
    if len(emergencies) >= 5:
        st.button("Show More Emergencies", key="show_more_emergencies")
else:
    st.info("No active emergency alerts at the moment.")

st.divider()

# Past Donations Overview
# Past Donations Overview
st.subheader("📊 Your Donation Overview")

# Fetch donation data including organization names
cursor.execute("""
    SELECT d.date, 
           COALESCE(d.amount, 0) AS amount, 
           d.donation_type,
           o.org_name,
           d.item_description
    FROM donations d
    LEFT JOIN organizations o ON d.organization_id = o.id
    WHERE d.user_id = %s
    ORDER BY d.date ASC
""", (user_id,))
donations = cursor.fetchall()

if donations:
    # Create DataFrame with better formatting
    df_donations = pd.DataFrame(donations)
    
    # Convert and clean data
    df_donations['date'] = pd.to_datetime(df_donations['date'])
    df_donations['amount'] = pd.to_numeric(df_donations['amount'], errors='coerce').fillna(0)
    df_donations['donation_type'] = df_donations['donation_type'].str.capitalize()
    
    # Calculate summary stats
    total_donated = df_donations['amount'].sum()
    money_donations = df_donations[df_donations['donation_type'] == 'Money']
    item_donations = df_donations[df_donations['donation_type'] == 'Item']
    money_count = len(money_donations)
    item_count = len(item_donations)
    
    # Create two columns for layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💰 Money Donations Over Time")
        
        if not money_donations.empty:
            # Resample by month and sum amounts
            monthly_money = money_donations.set_index('date').resample('M')['amount'].sum()
            
            # Create bar chart with custom styling
            st.bar_chart(monthly_money, color="#4CAF50", height=300)
        else:
            st.info("No monetary donations to display")
    
    with col2:
        st.markdown("### 🎁 Donation Type Breakdown")
        
        # Create a metrics row for donation types
        st.metric("Money Donations", 
                 f"{money_count} {'donation' if money_count == 1 else 'donations'}",
                 f"${money_donations['amount'].sum():,.2f} total")
        
        st.metric("Goods Donations", 
                 f"{item_count} {'donation' if item_count == 1 else 'donations'}",
                 f"{len(item_donations[item_donations['item_description'].notna()])} described")
        

    
    # Add metrics at the top
    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Donated", f"${total_donated:,.2f}")
    with m2:
        last_donation = df_donations.iloc[-1]
        st.metric("Last Donation", 
                 f"${last_donation['amount']:,.2f}" if last_donation['donation_type'] == 'Money' 
                 else "Item donation",
                 last_donation['date'].strftime('%b %d, %Y'))
    with m3:
        org_count = df_donations['org_name'].nunique()
        st.metric("Organizations Supported", org_count)
    
    # Enhanced donation history table
    with st.expander("📋 View Detailed Donation History", expanded=False):
        # Format the display dataframe
        display_df = df_donations.copy()
        display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:,.2f}" if x > 0 else "Item")
        display_df = display_df.rename(columns={
            'date': 'Date',
            'amount': 'Amount',
            'donation_type': 'Type',
            'org_name': 'Organization',
            'item_description': 'Description'
        })
        
        # Reorder columns
        display_df = display_df[['Date', 'Type', 'Amount', 'Organization', 'Description']]
        
        # Display with nice formatting
        st.dataframe(
            display_df,
            column_config={
                "Date": st.column_config.DatetimeColumn("Date", format="MMM D, YYYY"),
            },
            hide_index=True,
            use_container_width=True
        )
else:
    st.info("🌟 You haven't made any donations yet. Consider making your first donation today!")

st.divider()

# Donate Section
st.subheader("🎁 Make a Donation")

tab1, tab2 = st.tabs(["💰 Donate Money", "📦 Donate Items"])

with tab1:  # Donate Money Tab
    with st.container(border=True):
        st.markdown("### Select Organization")
        cursor.execute("SELECT id, org_name, description FROM organizations")
        organizations = cursor.fetchall()
        
        # Organization selection with more info
        selected_org = st.selectbox(
            "Choose an organization to support:",
            organizations,
            format_func=lambda x: x['org_name'],
            help="Select the organization you want to donate to"
        )
        
        if selected_org:
            with st.expander("ℹ️ About this organization"):
                st.write(selected_org['description'] or "No description available")
        
        st.markdown("---")
        st.markdown("### Donation Amount")
        
        # Amount selection with quick select buttons
        amount = st.number_input(
            "Enter amount (₹):",
            min_value=10.0,
            step=100.0,
            value=500.0,
            format="%.2f"
        )
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("₹100", use_container_width=True):
                amount = 100.0
        with col2:
            if st.button("₹500", use_container_width=True):
                amount = 500.0
        with col3:
            if st.button("₹1000", use_container_width=True):
                amount = 1000.0
        with col4:
            if st.button("₹5000", use_container_width=True):
                amount = 5000.0
        
        st.markdown("---")
        st.markdown("### Payment Method")
        
        payment_method = st.radio(
            "Select payment option:",
            ["UPI", "Credit/Debit Card", "Net Banking", "Wallet"],
            horizontal=True
        )
        
        # Payment method specific fields
        if payment_method == "UPI":
            upi_id = st.text_input("Enter your UPI ID:", placeholder="name@upi")
        elif payment_method == "Credit/Debit Card":
            col1, col2 = st.columns(2)
            with col1:
                card_number = st.text_input("Card Number:", placeholder="1234 5678 9012 3456")
            with col2:
                card_expiry = st.text_input("Expiry (MM/YY):", placeholder="MM/YY")
            col3, col4 = st.columns(2)
            with col3:
                card_cvv = st.text_input("CVV:", placeholder="123", max_chars=3)
            with col4:
                card_name = st.text_input("Name on Card:")
        
        st.markdown("---")
        if st.button("Donate Now", type="primary", use_container_width=True):
            # Process donation
            cursor.execute("""
                INSERT INTO donations (user_id, organization_id, amount, donation_type)
                VALUES (%s, %s, %s, 'money')
            """, (user_id, selected_org['id'], amount))
            conn.commit()
            
            # Show success message with confetti
            st.success("🎉 Thank you for your generous donation!")
            st.balloons()
            
            # Show transaction details
            with st.expander("Transaction Details", expanded=True):
                st.write(f"**Organization:** {selected_org['org_name']}")
                st.write(f"**Amount:** ₹{amount:,.2f}")
                st.write(f"**Payment Method:** {payment_method}")
                st.write(f"**Date:** {datetime.datetime.now().strftime('%d %b %Y, %I:%M %p')}")
                st.write("**Status:** Completed")

with tab2:  # Donate Items Tab
    with st.container(border=True):
        st.markdown("### Available Item Requests")
        cursor.execute("""
            SELECT ir.id, o.org_name, o.description as org_desc, 
                   ir.item_name, ir.quantity, ir.description as item_desc
            FROM item_requests ir
            JOIN organizations o ON ir.organization_id = o.id
            WHERE ir.is_active = TRUE
        """)
        item_requests = cursor.fetchall()

        if item_requests:
            # Item selection with more details
            selected_request = st.selectbox(
                "Select an item request:",
                item_requests,
                format_func=lambda x: f"{x['org_name']} - {x['item_name']} ({x['quantity']} needed)",
                help="Select which item you want to donate"
            )
            
            if selected_request:
                with st.expander("📝 Request Details"):
                    st.write(f"**Organization:** {selected_request['org_name']}")
                    st.write(f"**Item Needed:** {selected_request['item_name']}")
                    st.write(f"**Quantity Needed:** {selected_request['quantity']}")
                    st.write(f"**Description:** {selected_request['item_desc'] or 'No description provided'}")
                    st.write(f"**About Organization:** {selected_request['org_desc'] or 'No description available'}")
            
            st.markdown("---")
            st.markdown("### Your Donation Details")
            
            # Item donation form
            with st.form("item_donation_form"):
                quantity = st.number_input(
                    "Quantity you're donating:",
                    min_value=1,
                    max_value=100,
                    value=1,
                    step=1
                )
                
                item_condition = st.selectbox(
                    "Item Condition:",
                    ["New", "Like New", "Good", "Fair", "Poor"]
                )
                
                item_description = st.text_area(
                    "Additional details about your donation:",
                    placeholder="Describe the items you're donating, including any important details..."
                )
                
                # Delivery options
                delivery_method = st.radio(
                    "Delivery Method:",
                    ["I will drop off", "Arrange pickup", "Already delivered"],
                    horizontal=True
                )
                
                if delivery_method == "I will drop off":
                    dropoff_date = st.date_input("Planned drop-off date:", min_value=datetime.date.today())
                elif delivery_method == "Arrange pickup":
                    st.info("The organization will contact you to arrange pickup")
                
                submitted = st.form_submit_button("Submit Item Donation", type="primary")
                
                if submitted:
                    # Process item donation
                    full_description = f"{quantity} {selected_request['item_name']} ({item_condition})\n{item_description}\nDelivery: {delivery_method}"
                    
                    cursor.execute("""
                        INSERT INTO donations (user_id, organization_id, item_description, donation_type)
                        VALUES (%s, %s, %s, 'item')
                    """, (user_id, selected_request['id'], full_description))
                    conn.commit()
                    
                    st.success("🎉 Thank you for your item donation!")
                    
                    with st.expander("Donation Summary", expanded=True):
                        st.write(f"**Organization:** {selected_request['org_name']}")
                        st.write(f"**Item:** {selected_request['item_name']}")
                        st.write(f"**Quantity:** {quantity}")
                        st.write(f"**Condition:** {item_condition}")
                        st.write(f"**Delivery Method:** {delivery_method}")
                        st.write(f"**Date:** {datetime.datetime.now().strftime('%d %b %Y, %I:%M %p')}")
        else:
            st.info("Currently there are no active item requests from organizations.")

st.divider()

# Recurring Donations Section
st.subheader("🔄 Recurring Donations")

# Initialize session state for quick amount selection
if 'recurring_amount' not in st.session_state:
    st.session_state.recurring_amount = 500.0  # Default value

# Setup new recurring donation
with st.container(border=True):
    st.markdown("### ➕ Setup New Recurring Donation")
    
    # Organization selection with info toggle
    cursor.execute("SELECT id, org_name, description FROM organizations")
    organizations = cursor.fetchall()
    
    org_col1, org_col2 = st.columns([0.7, 0.3])
    with org_col1:
        recurring_org = st.selectbox(
            "Select Organization:",
            organizations,
            format_func=lambda x: x['org_name'],
            key="recurring_org",
            help="Choose the organization you want to support regularly"
        )
    
    with org_col2:
        show_org_info = st.toggle("Show organization info", key="show_org_info")
    
    if show_org_info and recurring_org:
        st.info(recurring_org['description'] or "No description available")
    
    st.markdown("---")
    st.markdown("### Donation Details")
    
    col1, col2 = st.columns(2)
    with col1:
        # Use the session state value for the number input
        recurring_amount = st.number_input(
            "Amount per cycle (₹):",
            min_value=10.0,
            step=100.0,
            value=st.session_state.recurring_amount,
            key="recurring_amount_input",
            format="%.2f"
        )
        
        # Quick amount buttons - update callback functions
        st.write("Quick select:")
        cols = st.columns(4)
        with cols[0]:
            if st.button("₹100", key="amt100"):
                st.session_state.recurring_amount = 100.0
                st.rerun()
        with cols[1]:
            if st.button("₹500", key="amt500"):
                st.session_state.recurring_amount = 500.0
                st.rerun()
        with cols[2]:
            if st.button("₹1000", key="amt1000"):
                st.session_state.recurring_amount = 1000.0
                st.rerun()
        with cols[3]:
            if st.button("₹2000", key="amt2000"):
                st.session_state.recurring_amount = 2000.0
                st.rerun()
    
    with col2:
        frequency = st.selectbox(
            "Frequency:",
            options=["weekly", "monthly", "yearly"],
            format_func=lambda x: x.capitalize(),
            help="How often the donation will be processed"
        )
        
        # Calculate next payment date
        today = datetime.date.today()
        if frequency == "weekly":
            next_payment = today + datetime.timedelta(days=7)
        elif frequency == "monthly":
            next_payment = today.replace(day=1) + datetime.timedelta(days=32)
            next_payment = next_payment.replace(day=1)
        else:  # yearly
            next_payment = today.replace(year=today.year + 1)
        
        st.markdown(f"**Next payment date:** {next_payment.strftime('%b %d, %Y')}")
    
    st.markdown("---")
    st.markdown("### Notification Preferences")
    
    notify = st.checkbox(
        "Send me reminders before each donation",
        value=True,
        help="You'll receive notifications 3 days before each scheduled donation"
    )
    
    notify_method = st.radio(
        "Notification method:",
        options=["Email", "SMS"],
        horizontal=True,
        disabled=not notify
    )
    
    if st.button("Set Up Recurring Donation", type="primary", use_container_width=True):
        cursor.execute("""
            INSERT INTO recurring_donations 
            (user_id, organization_id, amount, frequency, next_payment_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, recurring_org['id'], recurring_amount, frequency, next_payment))
        conn.commit()
        
        st.success("🎉 Recurring donation setup successfully!")
        
        # Show summary in an expander (now at root level)
        with st.expander("Donation Summary", expanded=True):
            st.write(f"**Organization:** {recurring_org['org_name']}")
            st.write(f"**Amount:** ₹{recurring_amount:,.2f} {frequency}")
            st.write(f"**Next payment:** {next_payment.strftime('%b %d, %Y')}")
            st.write(f"**Notifications:** {'Enabled' if notify else 'Disabled'} via {notify_method}")

# Current recurring donations
st.subheader("📋 Your Active Recurring Donations")

cursor.execute("""
    SELECT r.id, r.amount, r.frequency, r.next_payment_date, 
           o.org_name, o.description as org_desc
    FROM recurring_donations r
    JOIN organizations o ON r.organization_id = o.id
    WHERE r.user_id = %s AND r.is_active = TRUE
    ORDER BY r.next_payment_date ASC
""", (user_id,))
recurrings = cursor.fetchall()

if recurrings:
    for donation in recurrings:
        with st.container(border=True):
            cols = st.columns([0.7, 0.3])
            
            with cols[0]:
                st.markdown(f"#### {donation['org_name']}")
                st.write(f"**Amount:** ₹{donation['amount']:,.2f} {donation['frequency']}")
                st.write(f"**Next payment:** {donation['next_payment_date'].strftime('%b %d, %Y')}")
                
                # Days until next payment
                days_left = (donation['next_payment_date'] - datetime.date.today()).days
                if days_left > 0:
                    st.write(f"**Due in:** {days_left} day{'s' if days_left != 1 else ''}")
                elif days_left == 0:
                    st.warning("**Payment due today!**")
                else:
                    st.error("**Payment overdue!**")
            
            with cols[1]:
                if st.button("⚙️ Manage", key=f"manage_{donation['id']}", use_container_width=True):
                    st.session_state.manage_donation = donation['id']
                
                if st.session_state.get('manage_donation') == donation['id']:
                    with st.container(border=True):
                        st.write(f"Manage donation to {donation['org_name']}")
                        
                        # Update amount
                        new_amount = st.number_input(
                            "Update amount:",
                            value=float(donation['amount']),
                            min_value=10.0,
                            step=100.0,
                            key=f"update_amt_{donation['id']}"
                        )
                        
                        # Update frequency
                        new_freq = st.selectbox(
                            "Update frequency:",
                            options=["weekly", "monthly", "yearly"],
                            index=["weekly", "monthly", "yearly"].index(donation['frequency']),
                            key=f"update_freq_{donation['id']}"
                        )
                        
                        # Action buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Update", key=f"update_{donation['id']}"):
                                cursor.execute("""
                                    UPDATE recurring_donations
                                    SET amount = %s, frequency = %s
                                    WHERE id = %s
                                """, (new_amount, new_freq, donation['id']))
                                conn.commit()
                                st.success("Donation updated!")
                                st.session_state.manage_donation = None
                                st.rerun()
                        with col2:
                            if st.button("Cancel", type="secondary", key=f"cancel_{donation['id']}"):
                                cursor.execute("""
                                    UPDATE recurring_donations
                                    SET is_active = FALSE
                                    WHERE id = %s
                                """, (donation['id'],))
                                conn.commit()
                                st.success("Donation cancelled")
                                st.session_state.manage_donation = None
                                st.rerun()
                
                # Progress to next payment
                if donation['frequency'] == "weekly":
                    progress = 1 - (days_left / 7)
                elif donation['frequency'] == "monthly":
                    progress = 1 - (days_left / 30)
                else:
                    progress = 1 - (days_left / 365)
                
                progress = max(0, min(1, progress))
                st.progress(progress)
else:
    st.info("You currently have no active recurring donations.")

# Upcoming payment notifications
upcoming_payments = [d for d in recurrings if (d['next_payment_date'] - datetime.date.today()).days <= 3]
if upcoming_payments:
    st.markdown("---")
    st.subheader("🔔 Upcoming Payments")
    for payment in upcoming_payments:
        days = (payment['next_payment_date'] - datetime.date.today()).days
        st.warning(f"**{payment['org_name']}**: ₹{payment['amount']:,.2f} payment due in {days} day{'s' if days != 1 else ''}")

st.divider()


# Donation Updates Section
st.subheader("📬 Donation Updates & Messages")

# Fetch donation updates
cursor.execute("""
    SELECT du.message, du.sent_at, o.org_name
    FROM donation_updates du
    JOIN organizations o ON du.organization_id = o.id
    WHERE du.user_id = %s
    ORDER BY du.sent_at DESC
    LIMIT 10
""", (user_id,))
updates = cursor.fetchall()

if updates:
    for update in updates:
        with st.container(border=True):
            col1, col2 = st.columns([0.8, 0.2])
            
            with col1:
                st.markdown(f"**From:** {update['org_name']}")
                st.write(update['message'])
            
            with col2:
                st.caption(f"Sent: {update['sent_at'].strftime('%b %d, %Y %I:%M %p')}")
    
    if len(updates) >= 10:
        st.button("Show More Updates", key="show_more_updates")
else:
    st.info("No updates or messages from organizations yet.")

st.divider()

# Close database connection
conn.close()