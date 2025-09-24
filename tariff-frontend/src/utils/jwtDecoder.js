/**
 * Simple JWT decoder for frontend use
 * Extracts payload without signature verification
 */

/**
 * Decodes a JWT token and returns the payload
 * @param {string} token - The JWT token to decode
 * @returns {Object} The decoded payload
 * @throws {Error} If token is invalid or malformed
 */
export function decodeJWT(token) {
  if (!token || typeof token !== 'string') {
    throw new Error('Invalid token: Token must be a non-empty string');
  }

  // Split the token into its three parts
  const parts = token.split('.');
  
  if (parts.length !== 3) {
    throw new Error('Invalid token: JWT must have 3 parts separated by dots');
  }

  try {
    // Decode the payload (second part)
    const payload = parts[1];
    
    // Add padding if needed for base64 decoding
    const paddedPayload = payload + '='.repeat((4 - payload.length % 4) % 4);
    
    // Decode base64url to string
    const decodedPayload = atob(paddedPayload.replace(/-/g, '+').replace(/_/g, '/'));
    
    // Parse JSON
    return JSON.parse(decodedPayload);
  } catch (error) {
    throw new Error(`Failed to decode token: ${error.message}`);
  }
}

/**
 * Decodes JWT header (optional utility)
 * @param {string} token - The JWT token
 * @returns {Object} The decoded header
 */
export function decodeJWTHeader(token) {
  if (!token || typeof token !== 'string') {
    throw new Error('Invalid token: Token must be a non-empty string');
  }

  const parts = token.split('.');
  if (parts.length !== 3) {
    throw new Error('Invalid token: JWT must have 3 parts separated by dots');
  }

  try {
    const header = parts[0];
    const paddedHeader = header + '='.repeat((4 - header.length % 4) % 4);
    const decodedHeader = atob(paddedHeader.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(decodedHeader);
  } catch (error) {
    throw new Error(`Failed to decode header: ${error.message}`);
  }
}

/**
 * Checks if token is expired based on 'exp' claim
 * @param {Object} payload - The decoded payload
 * @returns {boolean} True if token is expired
 */
export function isTokenExpired(payload) {
  if (!payload.exp) {
    return false; // No expiration claim
  }
  
  const currentTime = Math.floor(Date.now() / 1000);
  return payload.exp < currentTime;
}

/**
 * Gets token expiration date
 * @param {Object} payload - The decoded payload
 * @returns {Date|null} Expiration date or null if no exp claim
 */
export function getTokenExpiration(payload) {
  if (!payload.exp) {
    return null;
  }
  
  return new Date(payload.exp * 1000);
}
