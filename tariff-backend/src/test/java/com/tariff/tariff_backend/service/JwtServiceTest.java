package com.tariff.tariff_backend.service;

import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import javax.crypto.SecretKey;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test; // Make sure this import is present
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.test.util.ReflectionTestUtils;

import com.tariff.tariff_backend.model.Role;
import com.tariff.tariff_backend.model.User;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;

@ExtendWith(MockitoExtension.class)
class JwtServiceTest {

    @InjectMocks
    private JwtService jwtService;

    private UserDetails userDetails;
    private String token;
    
    private final String TEST_SECRET = "24cca7e93bce7577a20cb9b4793809f1fe42514bf86665a3df7c559a64c1804e";
    private final long TEST_EXPIRATION = 86400000; // 1 day

    @BeforeEach
    void setUp() {
        // Manually inject values
        ReflectionTestUtils.setField(jwtService, "jwtSecret", TEST_SECRET);
        ReflectionTestUtils.setField(jwtService, "jwtExpiration", TEST_EXPIRATION);
        
        // --- THIS IS THE FIX ---
        // We must use ReflectionTestUtils to invoke the private @PostConstruct method
        ReflectionTestUtils.invokeMethod(jwtService, "init");

        userDetails = User.builder()
                .id(UUID.randomUUID())
                .username("test-user")
                .password("password")
                .role(Role.builder().name("user").build())
                .build();
        
        Map<String, Object> claims = new HashMap<>();
        claims.put("roles", "user");
        token = jwtService.generateToken(claims, userDetails);
    }

    @Test
    void isTokenValid_WithUserDetails_ShouldSucceed() {
        assertTrue(jwtService.isTokenValid(token, userDetails));
    }

    @Test
    void isTokenValid_WithUserDetails_ShouldFail_WhenUsernameMismatch() {
        UserDetails otherUser = User.builder().username("other-user").build();
        assertFalse(jwtService.isTokenValid(token, otherUser));
    }

    @Test
    void isTokenValid_StringOnly_ShouldSucceed() {
        assertTrue(jwtService.isTokenValid(token));
    }

    @Test
    void isTokenValid_ShouldFail_ForMalformedToken() {
        assertFalse(jwtService.isTokenValid("bad.token.jwt", userDetails));
        assertFalse(jwtService.isTokenValid("bad.token.jwt"));
    }

    @Test
    void isTokenValid_ShouldFail_ForExpiredToken() {
        SecretKey key = Keys.hmacShaKeyFor(TEST_SECRET.getBytes(StandardCharsets.UTF_8));
        String expiredToken = Jwts.builder()
                .subject("test-user")
                .issuedAt(new Date(System.currentTimeMillis() - 2000))
                .expiration(new Date(System.currentTimeMillis() - 1000)) // Expired 1 sec ago
                .signWith(key)
                .compact();
        
        assertFalse(jwtService.isTokenValid(expiredToken, userDetails));
    }
    
    // @Test
    // void isTokenValid_ShouldFail_ForWrongSignature() {
    //     SecretKey otherKey = Keys.hmacShaKeyFor("anothersecretkeyanothersecretkeyanothersecretkeyanothersecretkey".getBytes(StandardCharsets.UTF_8));
    //     String wrongSignatureToken = Jwts.builder()
    //             .subject("test-user")
    //             .expiration(new Date(System.currentTimeMillis() + TEST_EXPIRATION))
    //             .signWith(otherKey)
    //             .compact();

    //     assertFalse(jwtService.isTokenValid(wrongSignatureToken, userDetails));
    // }
    
    @Test
    void isTokenValid_ShouldFail_ForUnsupportedToken() {
        String unsupportedToken = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJ0ZXN0In0.";
        assertFalse(jwtService.isTokenValid(unsupportedToken, userDetails));
    }
    
    @Test
    void isTokenValid_ShouldFail_ForIllegalArgument() {
        assertFalse(jwtService.isTokenValid(null, userDetails));
    }

    @Test
    void hasRole_ShouldSucceed() {
        assertTrue(jwtService.hasRole(token, "user"));
        assertFalse(jwtService.hasRole(token, "admin"));
    }

    @Test
    void getTokenFromHeader_ShouldSucceed() {
        String header = "Bearer " + token;
        assertEquals(token, jwtService.getTokenFromHeader(header));
    }
}