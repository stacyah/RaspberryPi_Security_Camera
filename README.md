# Raspberry Pi SIEM Security Camera

## Description

This is a security monitoring system built from scratch on a Raspberry Pi. It transforms a webcam into a motion detector that captures images, serves them to a web interface, and forwards security events to a Splunk SIEM for live analysis and alerting.

---

## Features

* **Motion Detection:** Uses Python and OpenCV to monitor webcam feed, detect motion, and capture timestamped images of events.
* **Web Interface:** A Flask web application serves a UI to view all captured motion event images from any device on the local network.
* **Centralized Logging (SIEM):** All motion detection events are written to a log file on the Pi.
* **Log Forwarding:** A Splunk Universal Forwarder is configured to send all security events and application logs to a central Splunk instance.
* **Data Analysis & Visualization:** Events can be searched, analyzed, and visualized in Splunk to track security events over time.
* **Hardened Linux Environment:** The Raspberry Pi OS was hardened by disabling password authentication and instead using SSH keys, configuring a 'ufw' firewall, and deploying 'fail2ban' to prevent brute force attacks.

---

## Technologies Used

* **Hardware:** Raspberry Pi, USB Webcam
* **Operating System:** Raspberry Pi OS (Debian-based Linux)
* **Core Language:** Python
* **Libraries & Frameworks:**
    * **OpenCV:** for camera interaction and image processing
    * **Flask:** for the web interface
    * **Threading:** for simultaneous task handling
* **SIEM & Logging:** Splunk Enterprise, Splunk Universal Forwarder
* **System & Security Tools:** Git, GitHub, SSH, 'ufw' Firewall, 'fail2ban' Intrusion Prevention
