"""
English translation file
"""

translations = {
    # General texts
    "app_name": "WiFi Analyzer",
    "app_description": "Real-time analysis of available networks",
    "error_not_found": "Page not found. Return to home.",
    "error_server": "Server error. Please try again later.",
    
    # Navigation
    "nav_home": "Home",
    "nav_security_report": "Security Reports",
    "nav_assistant": "Assistant",
    "nav_language": "Language",
    "nav_recommendations": "Recommendations",
    "nav_device_security": "Device Security",
    "nav_network_topology": "Network Topology",
    
    # Home page
    "best_network": "Best Recommended Network",
    "all_networks": "All Available Networks",
    "no_networks": "No networks detected at the moment...",
    "signal": "Signal",
    "frequency": "Frequency",
    "security": "Security",
    "security_unknown": "Unknown",
    "analyze_security": "Analyze security",
    "consult_assistant": "Consult assistant",
    "auto_update": "Data is automatically updated every 10 seconds.",
    "ssid": "SSID",
    "signal_strength": "Signal strength",
    
    # Security reports
    "security_reports": "Network Security Reports",
    "generate_report": "Generate a report",
    "report_name": "Report name (optional)",
    "report_name_placeholder": "My security report",
    "btn_generate_report": "Generate report",
    "no_networks_detected": "No WiFi networks detected.",
    "return_home": "Return to home to detect networks.",
    "back_home": "Back to home",
    "about_reports": "About reports",
    "reports_analyze": "Security reports analyze WiFi networks based on several criteria:",
    "encryption_type": "Encryption type (WEP, WPA, WPA2, WPA3)",
    "signal_strength_criteria": "Signal strength",
    "frequency_used": "Frequency used",
    "security_score": "Each network receives a security score and personalized recommendations.",
    "previous_reports": "Previous reports",
    "report_count": "report(s)",
    "report_date": "Date",
    "networks": "Networks",
    "actions": "Actions",
    "view": "View",
    "no_reports": "No security reports generated.",
    
    # Report details
    "report_summary": "Report summary",
    "networks_analyzed": "Networks analyzed",
    "secure_networks": "Secure networks",
    "high_security": "High security",
    "vulnerable_networks": "Vulnerable networks",
    "low_security": "Low security",
    "general_recommendations": "General recommendations",
    "security_distribution": "Security distribution",
    "networks_details": "Analyzed networks details",
    "security_score_text": "Security score",
    "network_info": "Network information",
    "detailed_assessment": "Detailed assessment",
    "back_to_reports": "Back to reports",
    
    # Assistant
    "assistant_title": "WiFi Security Assistant",
    "new_conversation": "New conversation",
    "ask_security": "Ask a question about WiFi security...",
    "select_network": "No network",
    "send": "Send",
    "greeting": "Hello! I am your WiFi security assistant. How can I help you today?",
    "now": "Now",
    "suggestions": "Suggested questions",
    "suggested_questions": [
        "How can I improve my WiFi network security?",
        "What's the difference between WPA2 and WPA3?",
        "How to create a secure WiFi password?",
        "Is my WiFi signal strong enough?",
        "How to protect my network against hackers?",
        "What are the risks of an unsecured network?"
    ],
    "error_message": "Sorry, an error occurred while communicating with the assistant.",
    
    # Device security
    "device_security_title": "Device Security",
    "device_security_subtitle": "Analyze and monitor the security of all devices connected to your network",
    "network_security_overview": "Network Security Overview",
    "global_security_score": "Global Security Score",
    "critical_devices": "Critical Devices",
    "warning_devices": "Devices at Risk",
    "secure_devices": "Secure Devices",
    "devices_list": "Devices List",
    "device_type": "Device Type",
    "manufacturer": "Manufacturer",
    "security_score": "Security Score",
    "last_seen": "Last Seen",
    "refresh_devices": "Refresh List",
    "check_security": "Check",
    "rec_device_secure": "This device is properly secured",
    "rec_update_firmware": "Update the device firmware",
    "rec_install_updates": "Install security updates",
    "rec_address_vulnerabilities": "Fix known vulnerabilities",
    "rec_close_ports": "Close unnecessary ports",
    "rec_improve_encryption": "Strengthen encryption",
    "rec_enable_password": "Enable or strengthen password protection",
    "rec_enable_firewall": "Enable or configure firewall",
    "rec_check_suspicious": "Check detected suspicious activity",
    "refresh": "Refresh",
    "security_refresh_message": "Information is automatically updated every 30 seconds",
    "connected_devices": "Connected Devices",
    "no_devices_found": "No devices found",
    "no_devices_message": "No devices have been detected on your network at the moment",
    "how_scoring_works": "How security scoring works",
    "scoring_explanation": "Our system analyzes each device connected to your network and assigns a security score based on several factors including firmware version, open ports and active security protocols.",
    "critical_score": "Critical Score",
    "warning_score": "Warning Score",
    "secure_score": "Secure Score",
    "critical_score_description": "Requires immediate attention. Major vulnerabilities have been detected.",
    "warning_score_description": "Moderate security issues have been identified and should be fixed.",
    "secure_score_description": "The device follows good security practices and has little or no risk.",
    "security_scoring_privacy": "All analysis is done locally. No data is shared with external servers.",
    "device_details": "Device Details",
    "device_info": "Device Information",
    "type": "Type",
    "first_seen": "First Seen",
    "security_issues": "Security Issues",
    "issue": "Issue",
    "status": "Status",
    "impact": "Impact",
    "security_recommendations": "Security Recommendations",
    "close": "Close",
    "recheck_device": "Recheck",
    "devices_found": "{count} devices found",
    "details": "Details",
    "unknown": "Unknown",
    "critical": "Critical",
    "warning": "Warning",
    "secure": "Secure",
    "firmware_version": "Firmware Version",
    
    # Network topology
    "topology_title": "Network Topology",
    "topology_description": "Visualize and analyze all devices connected to your network in real-time",
    "topology_total_devices": "Total devices",
    "topology_online_devices": "Online devices",
    "topology_secure_devices": "Secure devices",
    "topology_vulnerable_devices": "Vulnerable devices",
    "topology_refresh_button": "Refresh",
    "topology_reset_layout_button": "Reset layout",
    "topology_high_security": "High security",
    "topology_medium_security": "Medium security",
    "topology_low_security": "Low security",
    "topology_offline_device": "Offline device",
    "topology_explanation_title": "Topology Usage Guide",
    "topology_how_to_use": "How to use this visualization",
    "topology_drag_devices": "Drag and drop devices to organize the topology according to your preferences",
    "topology_click_details": "Click on a device to see its detailed information",
    "topology_save_layout": "The layout is automatically saved",
    "topology_security_colors": "Color meaning",
    "topology_color_explanation": "Colors indicate the security level of each device: green for well-secured devices, yellow for devices with medium security, red for vulnerable devices, and gray for offline devices.",
    "topology_signal_strength": "Signal strength",
    "topology_signal_explanation": "The thickness of the connections between devices and the router represents the signal strength: the thicker the line, the better the signal."
}
