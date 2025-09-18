package com.tariff.tariff_backend.service;

import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.Map;
import java.util.function.Function;

import javax.crypto.SecretKey;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.MalformedJwtException;
import io.jsonwebtoken.UnsupportedJwtException;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;


@Service
public class JwtService {
    @Value("${jwt.secret}")
    private String jwtSecret;

    @Value("${jwt.expiration}")
    private long jwtExpiration;

    // Initializes the key after the class is instantiated and the jwtSecret is injected, 
    // preventing the repeated creation of the key and enhancing performance
    private SecretKey secretKey;
    @PostConstruct
    private void init() {
        byte[] keyBytes = jwtSecret.getBytes(StandardCharsets.UTF_8);
        this.secretKey = Keys.hmacShaKeyFor(keyBytes);
    }







    public String generateToken(Map<String, Object> extraClaims, UserDetails userDetails) {
        return Jwts
            .builder()
            .claims(extraClaims)
            .subject(userDetails.getUsername())
            .issuedAt(new Date(System.currentTimeMillis()))
            .expiration(new Date(System.currentTimeMillis() + jwtExpiration))
            .signWith(secretKey)
            .compact();
    }







    

    public boolean isTokenValid(String token, UserDetails userDetails) {
        try {
            Jwts.parser().verifyWith(secretKey).build().parseSignedClaims(token);
            final String tokenUsername = extractUsername(token);
            if (tokenUsername.equals(userDetails.getUsername())) {
                return true;
            }
        } catch (SecurityException e) {
            System.out.println("Invalid JWT signature: " + e.getMessage());
        } catch (MalformedJwtException e) {
            System.out.println("Invalid JWT token: " + e.getMessage());
        } catch (ExpiredJwtException e) {
            System.out.println("JWT token is expired: " + e.getMessage());
        } catch (UnsupportedJwtException e) {
            System.out.println("JWT token is unsupported: " + e.getMessage());
        } catch (IllegalArgumentException e) {
            System.out.println("JWT claims string is empty: " + e.getMessage());
        }
        return false;
    }

    public boolean isTokenValid(String token) {
        try {
            Claims claims = Jwts.parser().verifyWith(secretKey).build().parseSignedClaims(token).getPayload();
            // print payload
            for (Map.Entry<String, Object> entry : claims.entrySet()) {
                System.out.println(entry.getKey() + ": " + entry.getValue());
            }
            return true;
        } catch (Exception e) {
            System.out.println("Invalid JWT received: " + token);
        }
        return false;
    }

    public boolean hasRole(String token, String role) {
        String roles = extractCustomClaim(token, "roles", String.class);
        return roles.equals(role);
    }

    public String getTokenFromHeader(String authHeader) {
        return authHeader.substring(7);
    }





    public String extractUsername(String token) {
        return extractClaim(token, Claims::getSubject); // when u wanna pass in a method as a parameter
    }
    public <T> T extractClaim(String token, Function<Claims, T> claimsResolver) {
        final Claims claims = extractAllClaims(token);
        return claimsResolver.apply(claims); // applying the getSubject method to the claims object
    }
    private Claims extractAllClaims(String token) {
        return Jwts.parser().verifyWith(secretKey).build().parseSignedClaims(token).getPayload();
    }
    public <T> T extractCustomClaim(String token, String claimKey, Class<T> type) {
        return extractClaim(token, claims -> claims.get(claimKey, type));
    }
}
