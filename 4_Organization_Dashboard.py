import streamlit as st
import pandas as pd
import datetime
from db import get_connection

st.set_page_config(page_title="Organization Dashboard", layout="wide")
st.title("🏢 Organization Dashboard")

if "organization" not in st.session_state:
    st.error("You need to be logged in as an organization to view the dashboard.")
    st.stop()

# Database connection
conn = get_connection()
cursor = conn.cursor(dictionary=True)

# **Donation Analytics Dashboard**
st.subheader("📊 Donation Analytics")

organization_id = st.session_state["organization"]["id"]

# Fetch donation data including user information
cursor.execute("""
    SELECT d.date, d.amount, d.donation_type, d.item_description,
           u.name as donor_name, u.email as donor_email
    FROM donations d
    LEFT JOIN users u ON d.user_id = u.id
    WHERE d.organization_id = %s 
    ORDER BY d.date DESC
""", (organization_id,))
donations = cursor.fetchall()

if donations:
    # Create DataFrame with better formatting
    df_donations = pd.DataFrame(donations)
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
        st.markdown("### 💰 Monthly Donations")
        
        if not money_donations.empty:
            # Resample by month and sum amounts
            monthly_money = money_donations.set_index('date').resample('M')['amount'].sum()
            
            # Create area chart with custom styling
            st.area_chart(monthly_money, color="#4CAF50", height=300)
        else:
            st.info("No monetary donations received yet")
    
    with col2:
        st.markdown("### 🎁 Donation Breakdown")
        
        # Metrics row
        m1, m2 = st.columns(2)
        with m1:
            st.metric("Total Money Donated", 
                     f"₹{money_donations['amount'].sum():,.2f}",
                     f"{money_count} donations")
        with m2:
            st.metric("Item Donations Received", 
                     f"{item_count} items",
                     f"{len(item_donations[item_donations['item_description'].notna()])} described")
        
        # Horizontal bar chart showing counts
        type_counts = df_donations['donation_type'].value_counts().reset_index()
        type_counts.columns = ['Type', 'Count']
        st.bar_chart(type_counts.set_index('Type'), height=200, color="#FF9800")
    
    # Top summary metrics
    st.markdown("---")
    st.markdown("### 📈 Summary Statistics")
    stat1, stat2, stat3, stat4 = st.columns(4)
    with stat1:
        st.metric("Total Value Received", f"₹{total_donated:,.2f}")
    with stat2:
        avg_donation = money_donations['amount'].mean() if not money_donations.empty else 0
        st.metric("Average Donation", f"₹{avg_donation:,.2f}")
    with stat3:
        last_donation = df_donations.iloc[0]
        st.metric("Most Recent", 
                 f"₹{last_donation['amount']:,.2f}" if last_donation['donation_type'] == 'Money' 
                 else "Item",
                 last_donation['date'].strftime('%b %d, %Y'))
    with stat4:
        unique_donors = df_donations['donor_email'].nunique()
        st.metric("Unique Donors", unique_donors)
    
    # Enhanced donation history table
    with st.expander("🔍 View Detailed Donation Records", expanded=False):
        # Format the display dataframe
        display_df = df_donations.copy()
        display_df['amount'] = display_df['amount'].apply(lambda x: f"₹{x:,.2f}" if x > 0 else "Item")
        display_df = display_df.rename(columns={
            'date': 'Date',
            'amount': 'Amount',
            'donation_type': 'Type',
            'donor_name': 'Donor Name',
            'donor_email': 'Donor Email',
            'item_description': 'Description'
        })
        
        # Reorder and select columns
        display_df = display_df[['Date', 'Type', 'Amount', 'Donor Name', 'Donor Email', 'Description']]
        
        # Display with nice formatting
        st.dataframe(
            display_df,
            column_config={
                "Date": st.column_config.DatetimeColumn("Date", format="MMM D, YYYY"),
                "Donor Email": st.column_config.LinkColumn("Donor Email", display_text="📧")
            },
            hide_index=True,
            use_container_width=True
        )
else:
    st.info("🌟 Your organization hasn't received any donations yet. Share your cause to attract donors!")

st.divider()

# **Item Donation Management**
st.subheader("📦 Item Donation Requests")

# Create a tabbed interface
tab1, tab2 = st.tabs(["➕ Create New Request", "📋 Manage Requests"])

with tab1:
    with st.container(border=True):
        st.markdown("### 🆕 New Item Request")
        
        # Item details
        col1, col2 = st.columns(2)
        with col1:
            item_name = st.text_input("Item Name*", placeholder="e.g., Blankets, Rice Bags, Medicines")
        with col2:
            category = st.selectbox("Category*", 
                                  ["Clothing", "Food", "Medical", "Educational", 
                                   "Toys", "Furniture", "Electronics", "Other"])
        
        quantity = st.number_input("Quantity Needed*", min_value=1, value=10)
        
        # Enhanced description with formatting tips
        with st.expander("📝 Item Description & Details"):
            description = st.text_area(
                "Describe the items you need (be specific):",
                help="Include details like size, type, condition requirements, etc.",
                height=150
            )
            
            # Suggested tags
            st.markdown("**Suggested tags (select relevant ones):**")
            tags = st.multiselect(
                "Tags (select up to 5)",
                ["Winter", "Summer", "Children", "Elderly", "Emergency", 
                 "New", "Used", "Urgent", "School", "Festival"],
                max_selections=5,
                label_visibility="collapsed"
            )
        
        # Urgency and timeline
        col1, col2 = st.columns(2)
        with col1:
            urgency = st.select_slider(
                "Urgency Level",
                options=["Low", "Medium", "High", "Critical"],
                value="Medium"
            )
        with col2:
            deadline = st.date_input(
                "Needed By",
                min_value=datetime.date.today(),
                help="When do you need these items by?"
            )
        
        # Image upload (simulated)
        image_upload = st.checkbox("Add reference image (coming soon)")
        if image_upload:
            st.warning("Image upload feature will be available in the next update")
        
        if st.button("Submit Request", type="primary"):
            if not item_name:
                st.error("Please enter an item name")
            else:
                # Combine description with additional metadata
                full_description = f"Category: {category}\n"
                full_description += f"Tags: {', '.join(tags)}\n"
                full_description += f"Urgency: {urgency}\n"
                full_description += f"Deadline: {deadline}\n\n"
                full_description += f"Details:\n{description}"
                
                cursor.execute("""
                    INSERT INTO item_requests 
                    (organization_id, item_name, quantity, description)
                    VALUES (%s, %s, %s, %s)
                """, (organization_id, item_name, quantity, full_description))
                conn.commit()
                
                st.success("🎉 Item request submitted successfully!")
                st.toast("Donors will now see your request", icon="📤")

with tab2:
    st.markdown("### 📋 Your Active Requests")
    
    # Fetch all requests for this organization
    cursor.execute("""
        SELECT id, item_name, quantity, description, 
               created_at, is_active
        FROM item_requests
        WHERE organization_id = %s
        ORDER BY created_at DESC
    """, (organization_id,))
    requests = cursor.fetchall()
    
    if requests:
        # Create filters
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_active = st.selectbox(
                "Status",
                ["All", "Active Only", "Inactive Only"]
            )
        with col2:
            filter_urgency = st.selectbox(
                "Urgency",
                ["All", "Critical", "High", "Medium", "Low"]
            )
        with col3:
            filter_category = st.selectbox(
                "Category",
                ["All"] + ["Clothing", "Food", "Medical", "Educational", "Other"]
            )
        
        # Apply filters
        filtered_requests = []
        for req in requests:
            desc = req['description'] or ""
            include = True
            
            # Status filter
            if filter_active == "Active Only" and not req['is_active']:
                include = False
            elif filter_active == "Inactive Only" and req['is_active']:
                include = False
            
            # Urgency filter
            if include and filter_urgency != "All":
                if f"Urgency: {filter_urgency}" not in desc:
                    include = False
            
            # Category filter
            if include and filter_category != "All":
                if f"Category: {filter_category}" not in desc:
                    include = False
            
            if include:
                filtered_requests.append(req)
        
        if filtered_requests:
            for req in filtered_requests:
                with st.container(border=True):
                    cols = st.columns([0.7, 0.3])
                    with cols[0]:
                        st.markdown(f"#### {req['item_name']}")
                        st.write(f"**Quantity Needed:** {req['quantity']}")
                        
                        # Parse description for metadata
                        desc_lines = (req['description'] or "").split('\n')
                        metadata = {}
                        details = []
                        for line in desc_lines:
                            if ':' in line:
                                key, val = line.split(':', 1)
                                metadata[key.strip()] = val.strip()
                            elif line.strip():
                                details.append(line)
                        
                        # Display metadata
                        if 'Category' in metadata:
                            st.write(f"**Category:** {metadata['Category']}")
                        if 'Urgency' in metadata:
                            urgency_color = {
                                "Critical": "red",
                                "High": "orange",
                                "Medium": "blue",
                                "Low": "green"
                            }.get(metadata['Urgency'], "gray")
                            st.write(f"**Urgency:** :{urgency_color}[{metadata['Urgency']}]")
                        if 'Deadline' in metadata:
                            deadline_date = datetime.datetime.strptime(metadata['Deadline'], "%Y-%m-%d").date()
                            days_left = (deadline_date - datetime.date.today()).days
                            deadline_status = f"{metadata['Deadline']} ({days_left} days left)"
                            st.write(f"**Deadline:** {deadline_status}")
                        
                        # Show tags if available
                        if 'Tags' in metadata:
                            st.write("**Tags:**")
                            tags = metadata['Tags'].split(', ')
                            st.write(" ".join([f"`{tag}`" for tag in tags]))
                        
                        # Show description details
                        if details:
                            with st.expander("View Details"):
                                st.write("\n".join(details))
                        
                    with cols[1]:
                        st.write(f"**Posted:** {req['created_at'].strftime('%b %d, %Y')}")
                        
                        # Toggle active status
                        current_status = bool(req['is_active'])
                        new_status = st.toggle(
                            "Active",
                            value=current_status,
                            key=f"status_{req['id']}",
                            help="Toggle to show/hide this request from donors"
                        )
                        
                        if new_status != current_status:
                            cursor.execute("""
                                UPDATE item_requests
                                SET is_active = %s
                                WHERE id = %s
                            """, (int(new_status), req['id']))
                            conn.commit()
                            st.rerun()
                        
                        # Edit button (would link to edit functionality)
                        if st.button("✏️ Edit", key=f"edit_{req['id']}", use_container_width=True):
                            st.session_state.editing_request = req['id']
                            st.rerun()
                        
                        # Delete button
                        if st.button("🗑️ Delete", key=f"delete_{req['id']}", type="secondary", use_container_width=True):
                            cursor.execute("DELETE FROM item_requests WHERE id = %s", (req['id'],))
                            conn.commit()
                            st.success("Request deleted")
                            st.rerun()
        else:
            st.info("No requests match your filters")
    else:
        st.info("Your organization hasn't created any item requests yet")

st.divider()

# **Donor Communication Center**
st.subheader("💌 Donor Updates & Engagement")

# Tabbed interface for different communication methods
tab1, tab2, tab3 = st.tabs(["📝 Individual Updates", "📨 Bulk Messaging", "📊 Engagement Analytics"])

with tab1:
    st.markdown("### Personalized Updates")
    
    # Fetch donations with user info
    cursor.execute("""
        SELECT d.id as donation_id, d.user_id, d.amount, d.donation_type, d.date,
               u.name as user_name, u.email as user_email,
               o.org_name
        FROM donations d
        JOIN users u ON d.user_id = u.id
        JOIN organizations o ON d.organization_id = o.id
        WHERE d.organization_id = %s
        ORDER BY d.date DESC
    """, (organization_id,))
    donations_info = cursor.fetchall()

    if donations_info:
        # Filter donations
        col1, col2 = st.columns(2)
        with col1:
            filter_type = st.selectbox(
                "Filter by donation type:",
                ["All", "Money", "Item"]
            )
        with col2:
            time_filter = st.selectbox(
                "Filter by time:",
                ["All time", "Last 30 days", "Last 90 days"]
            )
        
        # Apply filters
        filtered_donations = []
        for donation in donations_info:
            include = True
            
            if filter_type == "Money" and donation['donation_type'] != 'money':
                include = False
            elif filter_type == "Item" and donation['donation_type'] != 'item':
                include = False
            
            if include and time_filter != "All time":
                days = 30 if time_filter == "Last 30 days" else 90
                donation_date = donation['date']
                if (datetime.datetime.now() - donation_date).days > days:
                    include = False
            
            if include:
                filtered_donations.append(donation)
        
        if filtered_donations:
            # Template selector
            with st.expander("💡 Message Templates"):
                col1, col2 = st.columns(2)
                with col1:
                    template = st.selectbox(
                        "Select a template:",
                        ["Custom", "Thank you", "Impact update", "Receipt confirmation", "Follow-up request"],
                        help="Pre-written templates to save time"
                    )
                
                with col2:
                    if template != "Custom":
                        if st.button("Apply Template"):
                            if template == "Thank you":
                                st.session_state.message_template = f"""Dear {filtered_donations[0]['user_name']},

Thank you for your generous {'₹' + str(filtered_donations[0]['amount']) if filtered_donations[0]['donation_type'] == 'money' else filtered_donations[0]['donation_type']} donation!

Your support helps us continue our mission. Here's how your contribution is making a difference: [insert specific impact example].

With gratitude,
{st.session_state['organization']['org_name']} Team"""
                            elif template == "Impact update":
                                st.session_state.message_template = f"""Hello {filtered_donations[0]['user_name']},

We wanted to share how donations like yours are creating change:

- [Specific example 1]
- [Specific example 2]
- [Specific example 3]

Your {'₹' + str(filtered_donations[0]['amount']) if filtered_donations[0]['donation_type'] == 'money' else 'item'} donation on {filtered_donations[0]['date'].strftime('%B %d, %Y')} is part of this impact.

Thank you,
{st.session_state['organization']['org_name']}"""
            
            # Donation cards with messaging
            for donation in filtered_donations:
                with st.container(border=True):
                    cols = st.columns([0.2, 0.6, 0.2])
                    with cols[0]:
                        st.markdown(f"**{donation['user_name']}**")
                        st.caption(donation['user_email'])
                        st.write(f"**Donated:** {donation['date'].strftime('%b %d, %Y')}")
                    
                    with cols[1]:
                        if donation['donation_type'] == 'money':
                            st.markdown(f"💰 **₹{donation['amount']:,.2f}**")
                        else:
                            st.markdown(f"🎁 **Item Donation**")
                        
                        # Message input with template support
                        message_key = f"message_{donation['donation_id']}"
                        if 'message_template' in st.session_state:
                            default_message = st.session_state.message_template.replace(
                                filtered_donations[0]['user_name'], donation['user_name']
                            ).replace(
                                str(filtered_donations[0]['amount']), str(donation['amount'])
                            ).replace(
                                filtered_donations[0]['date'].strftime('%B %d, %Y'), 
                                donation['date'].strftime('%B %d, %Y')
                            )
                        else:
                            default_message = ""
                        
                        message = st.text_area(
                            "Compose your message:",
                            value=default_message,
                            key=message_key,
                            height=150
                        )
                    
                    with cols[2]:
                        if st.button("Send", key=f"send_{donation['donation_id']}", use_container_width=True):
                            cursor.execute("""
                                INSERT INTO donation_updates (user_id, organization_id, message)
                                VALUES (%s, %s, %s)
                            """, (donation['user_id'], organization_id, message))
                            conn.commit()
                            st.success(f"Message sent to {donation['user_name']}!")
                            st.toast(f"Update sent to {donation['user_name']}", icon="✉️")
        else:
            st.info("No donations match your filters")
    else:
        st.info("No donations yet to send updates for")

with tab2:
    st.markdown("### Bulk Messaging")
    
    if donations_info:
        # Select recipients
        st.markdown("#### Select Recipients")
        
        # Group by donation type
        money_donors = [d for d in donations_info if d['donation_type'] == 'money']
        item_donors = [d for d in donations_info if d['donation_type'] == 'item']
        
        recipient_options = {
            "All Donors": donations_info,
            "Monetary Donors Only": money_donors,
            "Item Donors Only": item_donors,
            "Recent Donors (30 days)": [d for d in donations_info if (datetime.datetime.now() - d['date']).days <= 30],
            "Custom Selection": None
        }
        
        recipient_choice = st.selectbox(
            "Recipient Group:",
            list(recipient_options.keys())
        )
        
        selected_donors = recipient_options[recipient_choice]
        
        if recipient_choice == "Custom Selection":
            donor_names = [f"{d['user_name']} <{d['user_email']}>" for d in donations_info]
            selected_donors = st.multiselect(
                "Select individual donors:",
                donor_names
            )
            selected_donors = [d for d in donations_info if f"{d['user_name']} <{d['user_email']}>" in selected_donors]
        
        # Message composition
        st.markdown("#### Compose Message")
        
        # Personalization options
        col1, col2 = st.columns(2)
        with col1:
            include_name = st.checkbox("Personalize with donor names", value=True)
        with col2:
            include_donation = st.checkbox("Reference their donation", value=True)
        
        # Template selection
        template = st.selectbox(
            "Message template:",
            ["Custom", "Thank you", "Impact report", "Event invitation", "Newsletter"],
            help="Select a template to start with"
        )
        
        # Message editor
        message = st.text_area(
            "Your message:",
            height=200,
            help="Use {name} for donor name, {amount} for donation amount, {date} for donation date"
        )
        
        # Preview and send
        if st.button("Preview Messages"):
            if not selected_donors:
                st.warning("Please select at least one recipient")
            else:
                with st.expander("Message Previews", expanded=True):
                    for i, donor in enumerate(selected_donors[:3]):  # Show first 3 as preview
                        personalized = message
                        if include_name:
                            personalized = personalized.replace("{name}", donor['user_name'])
                        if include_donation:
                            personalized = personalized.replace("{amount}", str(donor['amount']) if donor['donation_type'] == 'money' else "item")
                            personalized = personalized.replace("{date}", donor['date'].strftime('%B %d, %Y'))
                        
                        st.markdown(f"**To:** {donor['user_name']} <{donor['user_email']}>")
                        st.text_area(f"Preview {i+1}", value=personalized, key=f"preview_{i}", height=100)
                        st.divider()
        
        if st.button("Send to All Selected", type="primary", use_container_width=True):
            if not selected_donors:
                st.warning("Please select at least one recipient")
            elif not message.strip():
                st.error("Please compose a message")
            else:
                progress_bar = st.progress(0)
                total = len(selected_donors)
                
                for i, donor in enumerate(selected_donors):
                    personalized = message
                    if include_name:
                        personalized = personalized.replace("{name}", donor['user_name'])
                    if include_donation:
                        personalized = personalized.replace("{amount}", str(donor['amount']) if donor['donation_type'] == 'money' else "item")
                        personalized = personalized.replace("{date}", donor['date'].strftime('%B %d, %Y'))
                    
                    cursor.execute("""
                        INSERT INTO donation_updates (user_id, organization_id, message)
                        VALUES (%s, %s, %s)
                    """, (donor['user_id'], organization_id, personalized))
                    conn.commit()
                    
                    progress_bar.progress((i + 1) / total)
                
                st.success(f"Messages sent to {len(selected_donors)} donors!")
                st.balloons()
    else:
        st.info("No donors available for messaging")

with tab3:
    st.markdown("### Engagement Analytics")
    
    # Fetch sent messages
    cursor.execute("""
        SELECT COUNT(*) as total_messages, 
               COUNT(DISTINCT user_id) as unique_donors_contacted,
               MIN(sent_at) as first_message,
               MAX(sent_at) as last_message
        FROM donation_updates
        WHERE organization_id = %s
    """, (organization_id,))
    stats = cursor.fetchone()
    
    if stats['total_messages'] > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Messages Sent", stats['total_messages'])
        with col2:
            st.metric("Unique Donors Contacted", stats['unique_donors_contacted'])
        with col3:
            st.metric("Last Message Sent", stats['last_message'].strftime('%b %d, %Y'))
        
        # Message frequency chart
        cursor.execute("""
            SELECT DATE(sent_at) as date, COUNT(*) as count
            FROM donation_updates
            WHERE organization_id = %s
            GROUP BY DATE(sent_at)
            ORDER BY date
        """, (organization_id,))
        frequency_data = cursor.fetchall()
        
        if frequency_data:
            df_freq = pd.DataFrame(frequency_data)
            st.markdown("#### Message Frequency Over Time")
            st.line_chart(df_freq.set_index('date'))
    else:
        st.info("No messages sent yet")

st.divider()

# **Emergency Alerts Section**
# **Emergency Response Center**
st.subheader("🆘 Emergency Response Center")

# Tabbed interface for different emergency functions
tab1, tab2, tab3 = st.tabs(["🚨 Create Alert", "📋 Active Emergencies", "📊 Response Dashboard"])

with tab1:
    with st.container(border=True):
        st.markdown("### 🚨 Create New Emergency Alert")
        
        # Emergency details
        emergency_title = st.text_input(
            "Alert Title*", 
            placeholder="e.g., Flood Relief Needed - Mumbai Area",
            help="Clear, concise title that explains the emergency"
        )
        
        # Emergency type selector
        emergency_type = st.selectbox(
            "Emergency Type*",
            ["Natural Disaster", "Medical Crisis", "Food Shortage", 
             "Shelter Needed", "Other Urgent Need"],
            help="Categorize your emergency for better response"
        )
        
        # Location details
        col1, col2 = st.columns(2)
        with col1:
            location = st.text_input(
                "Location*",
                placeholder="City, District, or Specific Address",
                help="Where is help needed?"
            )
        with col2:
            radius = st.selectbox(
                "Affected Radius",
                ["Local (under 1km)", "Community (1-5km)", "Regional (5-20km)", "Wide Area (20+km)"],
                help="How widespread is the emergency?"
            )
        
        # Rich text description with formatting options
        with st.expander("📝 Detailed Emergency Description"):
            emergency_description = st.text_area(
                "Full Description*",
                height=200,
                help="Include:\n- What happened\n- Immediate needs\n- Safety concerns\n- Contact info"
            )
            
            # Urgency level
            urgency = st.select_slider(
                "Urgency Level",
                options=["Monitor", "Concern", "Serious", "Critical", "Life-Threatening"],
                value="Serious"
            )
            
            # Estimated duration
            duration = st.selectbox(
                "Expected Duration",
                ["Hours", "Days", "Weeks", "Ongoing"],
                help="How long will this emergency last?"
            )
        
        # Resources needed checklist
        st.markdown("**Immediate Needs (check all that apply):**")
        needs_cols = st.columns(3)
        with needs_cols[0]:
            need_food = st.checkbox("Food/Water")
            need_medical = st.checkbox("Medical Supplies")
        with needs_cols[1]:
            need_shelter = st.checkbox("Shelter")
            need_volunteers = st.checkbox("Volunteers")
        with needs_cols[2]:
            need_clothing = st.checkbox("Clothing")
            need_other = st.checkbox("Other Resources")
        
        # Image upload option
        upload_image = st.checkbox("Add emergency photo (optional)")
        if upload_image:
            st.warning("Image upload coming in next update - describe visually in text for now")
        
        if st.button("Submit Emergency Alert", type="primary"):
            if not emergency_title or not emergency_description or not location:
                st.error("Please fill all required fields (marked with *)")
            else:
                # Build comprehensive description
                full_description = f"**Type:** {emergency_type}\n"
                full_description += f"**Location:** {location} ({radius})\n"
                full_description += f"**Urgency:** {urgency}\n"
                full_description += f"**Duration:** {duration}\n\n"
                full_description += "**Immediate Needs:** "
                needs = []
                if need_food: needs.append("Food/Water")
                if need_medical: needs.append("Medical")
                if need_shelter: needs.append("Shelter")
                if need_volunteers: needs.append("Volunteers")
                if need_clothing: needs.append("Clothing")
                if need_other: needs.append("Other")
                full_description += ", ".join(needs) + "\n\n"
                full_description += "**Details:**\n" + emergency_description
                
                cursor.execute("""
                    INSERT INTO emergencies 
                    (organization_id, title, description, is_approved)
                    VALUES (%s, %s, %s, %s)
                """, (organization_id, emergency_title, full_description, 0))
                conn.commit()
                
                st.success("""
                    🚨 Emergency alert submitted for admin approval!\n
                    Our team will review it immediately. You'll be notified when approved.
                """)

with tab2:
    st.markdown("### 📋 Active Emergency Alerts")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        filter_status = st.selectbox(
            "Filter by Status",
            ["All", "Pending Approval", "Active", "Resolved"]
        )
    with col2:
        filter_urgency = st.selectbox(
            "Filter by Urgency",
            ["All", "Critical", "Serious", "Concern"]
        )
    
    # Fetch emergencies with filters
    query = """
        SELECT id, title, description, created_at, is_active, is_approved
        FROM emergencies
        WHERE organization_id = %s
    """
    params = [organization_id]
    
    if filter_status != "All":
        if filter_status == "Pending Approval":
            query += " AND is_approved = 0"
        elif filter_status == "Active":
            query += " AND is_approved = 1 AND is_active = 1"
        elif filter_status == "Resolved":
            query += " AND is_active = 0"
    
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    emergencies = cursor.fetchall()
    
    if emergencies:
        filtered_emergencies = []
        for emergency in emergencies:
            include = True
            
            # Apply urgency filter if needed
            if filter_urgency != "All":
                desc = emergency['description'] or ""
                if f"**Urgency:** {filter_urgency}" not in desc:
                    include = False
            
            if include:
                filtered_emergencies.append(emergency)
        
        if filtered_emergencies:
            for emergency in filtered_emergencies:
                with st.container(border=True):
                    cols = st.columns([0.7, 0.3])
                    with cols[0]:
                        st.markdown(f"#### {emergency['title']}")
                        
                        # Parse description for metadata
                        desc_lines = (emergency['description'] or "").split('\n')
                        metadata = {}
                        details = []
                        for line in desc_lines:
                            if line.startswith("**") and ":**" in line:
                                key = line.split("**")[1].split(":**")[0]
                                val = line.split(":**")[1].strip()
                                metadata[key] = val
                            elif line.strip():
                                details.append(line)
                        
                        # Display metadata
                        if 'Type' in metadata:
                            st.write(f"**Type:** {metadata['Type']}")
                        if 'Location' in metadata:
                            st.write(f"**Location:** {metadata['Location']}")
                        if 'Urgency' in metadata:
                            urgency_color = {
                                "Critical": "red",
                                "Serious": "orange",
                                "Concern": "blue",
                                "Monitor": "green"
                            }.get(metadata['Urgency'], "gray")
                            st.write(f"**Urgency:** :{urgency_color}[{metadata['Urgency']}]")
                        if 'Duration' in metadata:
                            st.write(f"**Duration:** {metadata['Duration']}")
                        
                        # Show details
                        if details:
                            with st.expander("View Full Details"):
                                st.write("\n".join(details))
                    
                    with cols[1]:
                        status_badge = ""
                        if emergency['is_approved'] == 0:
                            status_badge = "🟡 Pending Approval"
                        elif emergency['is_active'] == 1:
                            status_badge = "🔴 Active Emergency"
                        else:
                            status_badge = "🟢 Resolved"
                        
                        st.write(f"**Status:** {status_badge}")
                        st.write(f"**Created:** {emergency['created_at'].strftime('%b %d, %Y %H:%M')}")
                        
                        # Action buttons
                        if emergency['is_active'] == 1 and emergency['is_approved'] == 1:
                            if st.button("Mark as Resolved", key=f"resolve_{emergency['id']}", use_container_width=True):
                                cursor.execute("""
                                    UPDATE emergencies
                                    SET is_active = 0
                                    WHERE id = %s
                                """, (emergency['id'],))
                                conn.commit()
                                st.success("Emergency marked as resolved!")
                                st.rerun()
                        
                        if st.button("Update", key=f"update_{emergency['id']}", use_container_width=True):
                            st.session_state.editing_emergency = emergency['id']
                            st.rerun()
        else:
            st.info("No emergencies match your filters")
    else:
        st.info("No emergency alerts created yet")

with tab3:
    st.markdown("### 📊 Emergency Response Dashboard")
    
    # Fetch emergency stats
    cursor.execute("""
        SELECT 
            COUNT(*) as total_emergencies,
            SUM(is_approved = 1 AND is_active = 1) as active_emergencies,
            SUM(is_approved = 1 AND is_active = 0) as resolved_emergencies,
            MIN(created_at) as first_emergency,
            MAX(created_at) as last_emergency
        FROM emergencies
        WHERE organization_id = %s
    """, (organization_id,))
    stats = cursor.fetchone()
    
    if stats['total_emergencies'] > 0:
        # Convert Decimal values to integers
        total_emergencies = int(stats['total_emergencies'])
        active_emergencies = int(stats['active_emergencies'])
        resolved_emergencies = int(stats['resolved_emergencies'])
        
        # Key metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Emergencies", total_emergencies)
        with col2:
            st.metric("Active Now", active_emergencies)
        with col3:
            st.metric("Resolved", resolved_emergencies)
        
        # Emergency frequency chart
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM emergencies
            WHERE organization_id = %s
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (organization_id,))
        frequency_data = cursor.fetchall()
        
        if frequency_data:
            df_freq = pd.DataFrame(frequency_data)
            st.markdown("#### Emergency Frequency Over Time")
            st.area_chart(df_freq.set_index('date'))
        
        # Urgency breakdown
        cursor.execute("""
            SELECT 
                SUM(description LIKE '%**Urgency:** Critical%') as critical,
                SUM(description LIKE '%**Urgency:** Serious%') as serious,
                SUM(description LIKE '%**Urgency:** Concern%') as concern,
                SUM(description LIKE '%**Urgency:** Monitor%') as monitor
            FROM emergencies
            WHERE organization_id = %s
        """, (organization_id,))
        urgency_stats = cursor.fetchone()
        
        # Convert Decimal values to integers
        urgency_stats = {k: int(v) for k, v in urgency_stats.items()}
        
        st.markdown("#### Emergency Urgency Breakdown")
        urgency_df = pd.DataFrame({
            "Level": ["Critical", "Serious", "Concern", "Monitor"],
            "Count": [
                urgency_stats['critical'],
                urgency_stats['serious'],
                urgency_stats['concern'],
                urgency_stats['monitor']
            ]
        })
        st.bar_chart(urgency_df.set_index('Level'))
    else:
        st.info("No emergency data available yet")
        
st.divider()

conn.close()