import streamlit as st
import pandas as pd
from decimal import Decimal
from db import get_connection

# Page configuration
st.set_page_config(page_title="Admin Dashboard", layout="wide")
st.title("👑 Admin Dashboard")

# Database connection
conn = get_connection()
cursor = conn.cursor(dictionary=True)

# **Emergency Alerts Management Center**
st.subheader("🛡️ Emergency Alerts Management Dashboard")

# Tabbed interface for different management functions
tab1, tab2, tab3 = st.tabs(["📋 Pending Approvals", "✅ Active Emergencies", "📊 Emergency Analytics"])

with tab1:
    st.markdown("### ⏳ Pending Emergency Approvals")
    
    # Fetch pending emergencies with organization details
    cursor.execute("""
        SELECT e.id, e.title, e.description, e.created_at,
               o.org_name, o.email as org_email
        FROM emergencies e
        JOIN organizations o ON e.organization_id = o.id
        WHERE e.is_active = TRUE AND e.is_approved = FALSE
        ORDER BY e.created_at DESC
    """)
    pending_emergencies = cursor.fetchall()

    if pending_emergencies:
        for emergency in pending_emergencies:
            with st.container(border=True):
                cols = st.columns([0.7, 0.3])
                with cols[0]:
                    st.markdown(f"#### {emergency['title']}")
                    st.caption(f"From: {emergency['org_name']} ({emergency['org_email']})")
                    st.write(f"**Submitted:** {emergency['created_at'].strftime('%Y-%m-%d %H:%M')}")
                    
                    # Parse description for metadata if structured
                    if emergency['description'] and '**Type:**' in emergency['description']:
                        desc_lines = emergency['description'].split('\n')
                        metadata = {}
                        details = []
                        for line in desc_lines:
                            if line.startswith("**") and ":**" in line:
                                key = line.split("**")[1].split(":**")[0]
                                val = line.split(":**")[1].strip()
                                metadata[key] = val
                            elif line.strip():
                                details.append(line)
                        
                        if 'Type' in metadata:
                            st.write(f"**Type:** {metadata['Type']}")
                        if 'Urgency' in metadata:
                            urgency_color = {
                                "Critical": "red",
                                "High": "orange",
                                "Medium": "blue",
                                "Low": "green"
                            }.get(metadata['Urgency'], "gray")
                            st.write(f"**Urgency:** :{urgency_color}[{metadata['Urgency']}]")
                    
                    with st.expander("View Full Details"):
                        st.write(emergency['description'] or "No description provided")
                
                with cols[1]:
                    # Approval actions
                    st.write("### Admin Actions")
                    
                    if st.button("✅ Approve Emergency", key=f"approve_{emergency['id']}", 
                               use_container_width=True, type="primary"):
                        cursor.execute("""
                            UPDATE emergencies
                            SET is_approved = TRUE
                            WHERE id = %s
                        """, (emergency['id'],))
                        conn.commit()
                        st.success(f"Emergency #{emergency['id']} approved and activated!")
                        st.rerun()
                    
                    if st.button("✖️ Reject with Feedback", key=f"reject_{emergency['id']}", 
                               use_container_width=True, type="secondary"):
                        feedback = st.text_area(
                            "Rejection reason (will be emailed to organization):",
                            key=f"feedback_{emergency['id']}",
                            height=100
                        )
                        if st.button("Confirm Rejection", key=f"confirm_reject_{emergency['id']}"):
                            cursor.execute("""
                                UPDATE emergencies
                                SET is_active = FALSE
                                WHERE id = %s
                            """, (emergency['id'],))
                            conn.commit()
                            
                            # In a real app, you would send the feedback email here
                            st.warning(f"Emergency #{emergency['id']} rejected. Organization notified.")
                            st.rerun()
                    
                    if st.button("🔄 Request More Info", key=f"info_{emergency['id']}", 
                               use_container_width=True):
                        info_request = st.text_area(
                            "What additional information do you need?",
                            key=f"info_request_{emergency['id']}",
                            height=100
                        )
                        if st.button("Send Request", key=f"send_info_{emergency['id']}"):
                            # In a real app, you would send this request to the organization
                            st.info(f"Information request sent to {emergency['org_name']}")
                            st.rerun()
    else:
        st.info("No pending emergency alerts requiring approval.")

with tab2:
    st.markdown("### 🔴 Active Emergency Alerts")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        filter_urgency = st.selectbox(
            "Filter by Urgency",
            ["All", "Critical", "High", "Medium", "Low"],
            key="active_filter_urgency"
        )
    with col2:
        filter_time = st.selectbox(
            "Filter by Time",
            ["All", "Last 24 hours", "Last 7 days", "Last 30 days"],
            key="active_filter_time"
        )
    
    # Fetch active emergencies
    query = """
        SELECT e.id, e.title, e.description, e.created_at,
               o.org_name, o.email as org_email
        FROM emergencies e
        JOIN organizations o ON e.organization_id = o.id
        WHERE e.is_active = TRUE AND e.is_approved = TRUE
    """
    
    if filter_time != "All":
        if filter_time == "Last 24 hours":
            query += " AND e.created_at >= NOW() - INTERVAL 1 DAY"
        elif filter_time == "Last 7 days":
            query += " AND e.created_at >= NOW() - INTERVAL 7 DAY"
        elif filter_time == "Last 30 days":
            query += " AND e.created_at >= NOW() - INTERVAL 30 DAY"
    
    query += " ORDER BY e.created_at DESC"
    
    cursor.execute(query)
    active_emergencies = cursor.fetchall()

    if active_emergencies:
        for emergency in active_emergencies:
            # Apply urgency filter
            if filter_urgency != "All":
                if not emergency['description'] or f"**Urgency:** {filter_urgency}" not in emergency['description']:
                    continue
            
            with st.container(border=True):
                cols = st.columns([0.7, 0.3])
                with cols[0]:
                    st.markdown(f"#### {emergency['title']}")
                    st.caption(f"Organization: {emergency['org_name']}")
                    st.write(f"**Activated:** {emergency['created_at'].strftime('%Y-%m-%d %H:%M')}")
                    
                    # Parse description for metadata
                    if emergency['description'] and '**Type:**' in emergency['description']:
                        desc_lines = emergency['description'].split('\n')
                        metadata = {}
                        for line in desc_lines:
                            if line.startswith("**") and ":**" in line:
                                key = line.split("**")[1].split(":**")[0]
                                val = line.split(":**")[1].strip()
                                metadata[key] = val
                        
                        if 'Type' in metadata:
                            st.write(f"**Type:** {metadata['Type']}")
                        if 'Location' in metadata:
                            st.write(f"**Location:** {metadata['Location']}")
                        if 'Urgency' in metadata:
                            urgency_color = {
                                "Critical": "red",
                                "High": "orange",
                                "Medium": "blue",
                                "Low": "green"
                            }.get(metadata['Urgency'], "gray")
                            st.write(f"**Urgency:** :{urgency_color}[{metadata['Urgency']}]")
                
                with cols[1]:
                    st.write("### Admin Controls")
                    
                    if st.button("🟢 Mark as Resolved", key=f"resolve_{emergency['id']}", 
                               use_container_width=True, type="primary"):
                        cursor.execute("""
                            UPDATE emergencies
                            SET is_active = FALSE
                            WHERE id = %s
                        """, (emergency['id'],))
                        conn.commit()
                        st.success(f"Emergency #{emergency['id']} marked as resolved!")
                        st.rerun()
                    
                    if st.button("📝 Edit Details", key=f"edit_{emergency['id']}", 
                               use_container_width=True):
                        st.session_state.editing_emergency = emergency['id']
                        st.rerun()
                    
                    if st.button("📢 Broadcast Update", key=f"broadcast_{emergency['id']}", 
                               use_container_width=True):
                        update_message = st.text_area(
                            "Send update to all donors:",
                            key=f"update_{emergency['id']}",
                            height=100
                        )
                        if st.button("Send Broadcast", key=f"send_broadcast_{emergency['id']}"):
                            # In a real app, you would send this to all relevant donors
                            st.success(f"Update sent regarding {emergency['title']}!")
                            st.rerun()
    else:
        st.info("No active emergency alerts currently.")

with tab3:
    st.markdown("### 📈 Emergency Analytics Dashboard")
    
    # Fetch stats
    cursor.execute("""
        SELECT 
            COUNT(*) as total_emergencies,
            SUM(is_approved = 1 AND is_active = 1) as active_emergencies,
            SUM(is_approved = 1 AND is_active = 0) as resolved_emergencies,
            SUM(is_approved = 0) as pending_emergencies,
            MIN(created_at) as first_emergency,
            MAX(created_at) as last_emergency
        FROM emergencies
    """)
    stats = cursor.fetchone()
    
    # Convert numeric values to integers, leave datetimes as is
    processed_stats = {}
    for k, v in stats.items():
        if k in ['first_emergency', 'last_emergency']:
            processed_stats[k] = v  # Keep datetime values as-is
        else:
            processed_stats[k] = int(v) if v is not None else 0
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Emergencies", processed_stats['total_emergencies'])
    with col2:
        st.metric("Active Now", processed_stats['active_emergencies'])
    with col3:
        st.metric("Resolved", processed_stats['resolved_emergencies'])
    with col4:
        st.metric("Pending Review", processed_stats['pending_emergencies'])
    
    # Display first and last emergency dates
    st.write(f"**First Emergency:** {processed_stats['first_emergency'].strftime('%Y-%m-%d') if processed_stats['first_emergency'] else 'N/A'}")
    st.write(f"**Most Recent Emergency:** {processed_stats['last_emergency'].strftime('%Y-%m-%d') if processed_stats['last_emergency'] else 'N/A'}")
    
    # Emergency frequency chart
    cursor.execute("""
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM emergencies
        GROUP BY DATE(created_at)
        ORDER BY date
    """)
    freq_data = cursor.fetchall()
    
    if freq_data:
        df_freq = pd.DataFrame(freq_data)
        st.markdown("#### Emergency Frequency Over Time")
        st.area_chart(df_freq.set_index('date'))
    
    # Urgency breakdown
    cursor.execute("""
        SELECT 
            SUM(description LIKE '%**Urgency:** Critical%') as critical,
            SUM(description LIKE '%**Urgency:** High%') as high,
            SUM(description LIKE '%**Urgency:** Medium%') as medium,
            SUM(description LIKE '%**Urgency:** Low%') as low
        FROM emergencies
    """)
    urgency_stats = cursor.fetchone()
    
    # Convert all numeric values to integers
    urgency_stats = {k: int(v) if v is not None else 0 for k, v in urgency_stats.items()}
    
    st.markdown("#### Emergency Urgency Breakdown")
    urgency_df = pd.DataFrame({
        "Urgency Level": ["Critical", "High", "Medium", "Low"],
        "Count": [
            urgency_stats['critical'],
            urgency_stats['high'],
            urgency_stats['medium'],
            urgency_stats['low']
        ]
    })
    st.bar_chart(urgency_df.set_index('Urgency Level'))

st.divider()

# **Organization Management Dashboard**
st.subheader("🏢 Organization Management")

# Check and add columns if they don't exist (more robust approach)
try:
    # First check if columns exist
    cursor.execute("""
        SELECT COUNT(*) as column_exists 
        FROM information_schema.columns 
        WHERE table_name = 'organizations' AND column_name = 'is_active'
    """)
    if cursor.fetchone()['column_exists'] == 0:
        cursor.execute("ALTER TABLE organizations ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
    
    cursor.execute("""
        SELECT COUNT(*) as column_exists 
        FROM information_schema.columns 
        WHERE table_name = 'organizations' AND column_name = 'is_approved'
    """)
    if cursor.fetchone()['column_exists'] == 0:
        cursor.execute("ALTER TABLE organizations ADD COLUMN is_approved BOOLEAN DEFAULT FALSE")
    
    conn.commit()
except Exception as e:
    st.warning(f"Could not modify table structure: {str(e)}")
    # Initialize variables to prevent errors
    is_active_exists = False
    is_approved_exists = False
else:
    is_active_exists = True
    is_approved_exists = True

# Tabbed interface for different management functions
tab1, tab2, tab3 = st.tabs(["🆕 Approval Queue", "✅ Active Organizations", "📊 Organization Stats"])

with tab1:
    st.markdown("### ⏳ Organizations Pending Approval")
    
    # Modified query to work even if columns don't exist
    if is_approved_exists:
        query = """
            SELECT id, org_name, email, phone, description, address, gov_id_type, gov_id_number
            FROM organizations
            WHERE is_approved = FALSE
            ORDER BY id DESC
        """
    else:
        query = """
            SELECT id, org_name, email, phone, description, address, gov_id_type, gov_id_number
            FROM organizations
            ORDER BY id DESC
            LIMIT 0  # Return nothing if column doesn't exist
        """
    
    cursor.execute(query)
    pending_orgs = cursor.fetchall()

    if pending_orgs:
        for org in pending_orgs:
            with st.container(border=True):
                cols = st.columns([0.7, 0.3])
                with cols[0]:
                    st.markdown(f"#### {org['org_name']}")
                    st.write(f"**Email:** {org['email']}")
                    st.write(f"**Phone:** {org['phone']}")
                    
                    with st.expander("View Full Details"):
                        st.write(f"**Description:** {org['description'] or 'Not provided'}")
                        st.write(f"**Address:** {org['address'] or 'Not provided'}")
                        st.write(f"**Government ID Type:** {org['gov_id_type'] or 'Not provided'}")
                        if org['gov_id_number']:
                            st.write(f"**Government ID:** `{org['gov_id_number']}`")
                
                with cols[1]:
                    st.write("### Admin Actions")
                    
                    if is_approved_exists:
                        if st.button("✅ Approve Organization", key=f"approve_{org['id']}", 
                                   use_container_width=True, type="primary"):
                            cursor.execute("""
                                UPDATE organizations
                                SET is_approved = TRUE, is_active = TRUE
                                WHERE id = %s
                            """, (org['id'],))
                            conn.commit()
                            st.success(f"Approved {org['org_name']}!")
                            st.rerun()
                    
                    if st.button("✖️ Reject with Feedback", key=f"reject_{org['id']}", 
                               use_container_width=True, type="secondary"):
                        feedback = st.text_area(
                            "Reason for rejection (will be emailed to organization):",
                            key=f"feedback_{org['id']}",
                            height=100
                        )
                        if st.button("Confirm Rejection", key=f"confirm_reject_{org['id']}"):
                            cursor.execute("DELETE FROM organizations WHERE id = %s", (org['id'],))
                            conn.commit()
                            st.warning(f"{org['org_name']} rejected and removed from system.")
                            st.rerun()
                    
                    if st.button("🔄 Request More Info", key=f"info_{org['id']}", 
                               use_container_width=True):
                        info_request = st.text_area(
                            "What additional information do you need?",
                            key=f"info_request_{org['id']}",
                            height=100
                        )
                        if st.button("Send Request", key=f"send_info_{org['id']}"):
                            st.info(f"Information request sent to {org['org_name']}")
                            st.rerun()
    else:
        st.info("No organizations pending approval.")

with tab2:
    st.markdown("### ✅ Active Organizations")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        search_term = st.text_input("Search by name or email:")
    with col2:
        if is_active_exists:
            show_inactive = st.checkbox("Show inactive organizations")
        else:
            show_inactive = False
            st.write("")  # Spacer
    
    # Build query based on filters
    if is_approved_exists and is_active_exists:
        query = """
            SELECT id, org_name, email, phone, description, is_active
            FROM organizations
            WHERE is_approved = TRUE
        """
    else:
        query = """
            SELECT id, org_name, email, phone, description, TRUE as is_active
            FROM organizations
            WHERE 1=1
        """
    
    params = []
    
    if search_term:
        query += " AND (org_name LIKE %s OR email LIKE %s)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
    
    if is_active_exists and not show_inactive:
        query += " AND is_active = TRUE"
    
    query += " ORDER BY org_name ASC"
    
    cursor.execute(query, params)
    active_orgs = cursor.fetchall()

    if active_orgs:
        for org in active_orgs:
            with st.container(border=True):
                cols = st.columns([0.7, 0.3])
                with cols[0]:
                    if is_active_exists:
                        status = "🟢 Active" if org['is_active'] else "🔴 Inactive"
                        st.markdown(f"#### {org['org_name']} {status}")
                    else:
                        st.markdown(f"#### {org['org_name']}")
                    st.write(f"**Email:** {org['email']}")
                    st.write(f"**Phone:** {org['phone']}")
                    
                    with st.expander("View Description"):
                        st.write(org['description'] or "No description provided")
                
                with cols[1]:
                    st.write("### Admin Controls")
                    
                    if is_active_exists:
                        if org['is_active']:
                            if st.button("⏸️ Deactivate", key=f"deactivate_{org['id']}", 
                                       use_container_width=True):
                                cursor.execute("""
                                    UPDATE organizations
                                    SET is_active = FALSE
                                    WHERE id = %s
                                """, (org['id'],))
                                conn.commit()
                                st.warning(f"{org['org_name']} deactivated")
                                st.rerun()
                        else:
                            if st.button("▶️ Activate", key=f"activate_{org['id']}", 
                                       use_container_width=True, type="primary"):
                                cursor.execute("""
                                    UPDATE organizations
                                    SET is_active = TRUE
                                    WHERE id = %s
                                """, (org['id'],))
                                conn.commit()
                                st.success(f"{org['org_name']} activated")
                                st.rerun()
                    
                    if st.button("📝 Edit", key=f"edit_{org['id']}", 
                               use_container_width=True):
                        st.session_state.editing_org = org['id']
                        st.rerun()
                    
                    if st.button("🗑️ Delete", key=f"delete_{org['id']}", 
                               use_container_width=True, type="secondary"):
                        if st.checkbox(f"Confirm permanent deletion of {org['org_name']}"):
                            cursor.execute("DELETE FROM organizations WHERE id = %s", (org['id'],))
                            conn.commit()
                            st.error(f"{org['org_name']} permanently deleted")
                            st.rerun()
    else:
        st.info("No organizations match your filters.")

with tab3:
    st.markdown("### 📊 Organization Statistics")
    
    # Fetch basic counts (no date-based queries since created_at doesn't exist)
    cursor.execute("""
        SELECT 
            COUNT(*) as total_orgs,
            SUM(is_approved = 1) as approved_orgs,
            SUM(is_approved = 0) as pending_orgs,
            SUM(is_active = 1) as active_orgs,
            MIN(id) as oldest_org_id,
            MAX(id) as newest_org_id
        FROM organizations
    """)
    stats = cursor.fetchone()
    
    # Convert all numeric values to integers
    stats = {
        'total_orgs': int(stats['total_orgs']),
        'approved_orgs': int(stats['approved_orgs']),
        'pending_orgs': int(stats['pending_orgs']),
        'active_orgs': int(stats['active_orgs']),
        'oldest_org_id': stats['oldest_org_id'],
        'newest_org_id': stats['newest_org_id']
    }
    
    # Get oldest and newest org names
    oldest_name = "None"
    newest_name = "None"
    if stats['oldest_org_id']:
        cursor.execute("SELECT org_name FROM organizations WHERE id = %s", (stats['oldest_org_id'],))
        result = cursor.fetchone()
        oldest_name = result['org_name'] if result else "None"
    if stats['newest_org_id']:
        cursor.execute("SELECT org_name FROM organizations WHERE id = %s", (stats['newest_org_id'],))
        result = cursor.fetchone()
        newest_name = result['org_name'] if result else "None"
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Organizations", stats['total_orgs'])
    with col2:
        st.metric("Approved Organizations", stats['approved_orgs'])
    with col3:
        st.metric("Active Organizations", stats['active_orgs'])
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Oldest Organization", oldest_name)
    with col2:
        st.metric("Newest Organization", newest_name)
    
    # Since we don't have created_at, we'll use ID-based timeline as a proxy
    st.markdown("#### Organization Registration Timeline (by ID)")
    cursor.execute("SELECT id, org_name FROM organizations ORDER BY id")
    orgs = cursor.fetchall()
    if orgs:
        df_orgs = pd.DataFrame(orgs)
        st.line_chart(df_orgs.set_index('id')['org_name'].value_counts().sort_index())

# Closing DB connection
conn.close()