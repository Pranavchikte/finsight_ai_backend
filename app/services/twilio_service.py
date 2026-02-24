import os
import hmac
import hashlib
import base64
import urllib.parse
from flask import current_app
import requests
from requests.auth import HTTPBasicAuth


class TwilioService:
    def __init__(self):
        self.account_sid = None
        self.auth_token = None
        self.phone_number = None
        self._loaded = False

    def _ensure_loaded(self):
        if not self._loaded:
            self.account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
            self.auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
            self.phone_number = current_app.config.get('TWILIO_PHONE_NUMBER')
            self._loaded = True

            if not all([self.account_sid, self.auth_token, self.phone_number]):
                current_app.logger.warning("Twilio credentials not configured")

    def verify_twilio_signature(self, url, params, signature):
        """
        Verify that the request came from Twilio.
        
        Args:
            url: The full URL of the request (without query string)
            params: Dictionary of POST parameters
            signature: Value from X-Twilio-Signature header
            
        Returns:
            bool: True if signature is valid
        """
        self._ensure_loaded()
        
        if not self.auth_token:
            return False
        
        # Sort params and create sorted string
        sorted_params = sorted(params.items())
        param_string = ''.join(f'{k}{v}' for k, v in sorted_params)
        
        # Create the data to sign
        data_to_sign = url + param_string
        
        # Calculate expected signature
        try:
            expected_signature = base64.b64encode(
                hmac.new(
                    self.auth_token.encode(),
                    data_to_sign.encode(),
                    hashlib.sha1
                ).digest()
            ).decode()
            
            # Compare signatures (timing-safe)
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            current_app.logger.error(f"Error verifying Twilio signature: {e}")
            return False

    def send_whatsapp_message(self, to_number, message):
        """
        Send a WhatsApp message via Twilio API.
        
        Args:
            to_number: WhatsApp number in format 'whatsapp:+1234567890'
            message: The message body to send
            
        Returns:
            dict: Twilio response with message SID or None on failure
        """
        self._ensure_loaded()
        
        if not all([self.account_sid, self.auth_token, self.phone_number]):
            current_app.logger.error("Twilio not configured")
            return None

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        
        data = {
            "From": f"whatsapp:{self.phone_number}",
            "To": to_number,
            "Body": message
        }

        try:
            response = requests.post(
                url,
                auth=HTTPBasicAuth(self.account_sid, self.auth_token),
                data=data,
                timeout=30
            )
            
            if response.status_code == 201:
                current_app.logger.info(f"WhatsApp message sent to {to_number}")
                return response.json()
            else:
                current_app.logger.error(f"Twilio error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            current_app.logger.error(f"Failed to send WhatsApp message: {e}")
            return None

    def send_verification_code(self, to_number, code):
        """Send a verification code to the user's WhatsApp."""
        message = f"🔐 Your FinSight AI verification code is: *{code}*\n\nThis code expires in 10 minutes.\n\nIf you didn't request this, please ignore."
        return self.send_whatsapp_message(to_number, message)

    def format_whatsapp_number(self, phone_number):
        """
        Format phone number for WhatsApp API.
        Example: +1234567890 -> whatsapp:+1234567890
        
        Validates Indian mobile numbers (10 digits starting with 6-9)
        """
        if not phone_number:
            return None
        
        # Remove any spaces or special characters except +
        clean_number = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        
        # Remove + if present for processing
        if clean_number.startswith('+'):
            clean_number = clean_number[1:]
        
        # Validate: must be 10 digits for Indian mobile
        if len(clean_number) != 10 or not clean_number.isdigit():
            return None
        
        # Validate: first digit should be 6-9 (Indian mobile)
        if clean_number[0] not in '6789':
            return None
        
        # Format with country code
        return f"whatsapp:+{clean_number}"

    def validate_phone_number(self, phone_number):
        """
        Validate if phone number is a valid Indian mobile number.
        Returns: (is_valid, error_message)
        """
        if not phone_number:
            return False, "Phone number is required"
        
        # Remove spaces and special chars
        clean = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        
        if '+' in clean:
            clean = clean[1:]  # Remove +
        
        if len(clean) != 10:
            return False, "Must be 10 digits"
        
        if not clean.isdigit():
            return False, "Must contain only digits"
        
        if clean[0] not in '6789':
            return False, "Number must start with 6, 7, 8, or 9"
        
        return True, None


twilio_service = TwilioService()
