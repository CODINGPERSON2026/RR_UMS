from flask import Flask, redirect, request, session
import jwt

JWT_SECRET = "MY_SUPER_SECRET_KEY_123_4567890123"      # 32+ bytes for HMAC-SHA256
JWT_ALGO = "HS256"

def require_login():
    """Check if user is logged in via JWT token or Flask session"""
    token = request.cookies.get('token')
    
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
            if payload:
                # Keep Flask session synchronized across requests
                try:
                    if not session.get('user_id') or session.get('user_id') != payload.get('user_id'):
                        session.permanent = True
                        session['user'] = payload
                        session['user_id'] = payload.get('user_id')
                        session['role'] = payload.get('role')
                        session['company'] = payload.get('company')
                        session['username'] = payload.get('username')
                        session['army_number'] = payload.get('army_number')
                        session['email'] = payload.get('email')
                except Exception:
                    pass
                return payload
        except jwt.ExpiredSignatureError:
            pass
        except jwt.InvalidTokenError:
            pass
        except Exception:
            pass

    # Fallback to active Flask session if cookie was not provided
    try:
        if session and session.get('user_id') and session.get('role'):
            user_data = session.get('user') or {
                'user_id': session.get('user_id'),
                'username': session.get('username'),
                'role': session.get('role'),
                'company': session.get('company'),
                'army_number': session.get('army_number'),
                'email': session.get('email')
            }
            return user_data
    except Exception:
        pass

    return None