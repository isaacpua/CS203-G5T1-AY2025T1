// src/test/java/com/tariff/tariff_backend/security/SecurityComponentsTest.java
package com.tariff.tariff_backend.security; // <-- Correct package (lowercase 's')

import java.util.Collections;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import static org.mockito.ArgumentMatchers.anyString;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockFilterChain;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails; // Added for the last test
import org.springframework.security.core.userdetails.UserDetailsService;

import com.tariff.tariff_backend.service.JwtService;

import jakarta.servlet.http.HttpServletResponse;

@ExtendWith(MockitoExtension.class)
class SecurityComponentsTest {

    @Mock
    private JwtService jwtService;
    @Mock
    private UserDetailsService userDetailsService;
    @InjectMocks
    private JwtAuthenticationFilter jwtAuthenticationFilter;

    // Test for JwtAuthenticationEntryPoint
    @Test
    void testJwtAuthenticationEntryPoint_Commence() throws Exception {
        JwtAuthenticationEntryPoint entryPoint = new JwtAuthenticationEntryPoint();
        MockHttpServletRequest request = new MockHttpServletRequest();
        MockHttpServletResponse response = new MockHttpServletResponse();
        AuthenticationException authException = new AuthenticationException("Full authentication is required") {};

        entryPoint.commence(request, response, authException);

        assertEquals(HttpServletResponse.SC_UNAUTHORIZED, response.getStatus());
        assertEquals("application/json", response.getContentType());
        assertTrue(response.getContentAsString().contains("Full authentication is required"));
    }

    // --- Tests for JwtAuthenticationFilter ---
    @Test
    void testJwtFilter_ValidToken_CacheMiss() throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader("Authorization", "Bearer valid.token.jwt");
        MockHttpServletResponse response = new MockHttpServletResponse();
        MockFilterChain filterChain = new MockFilterChain();

        UserDetails userDetails = new User("testuser", "pass", Collections.emptyList());

        when(jwtService.extractUsername("valid.token.jwt")).thenReturn("testuser");
        when(userDetailsService.loadUserByUsername("testuser")).thenReturn(userDetails);
        when(jwtService.isTokenValid("valid.token.jwt", userDetails)).thenReturn(true);

        jwtAuthenticationFilter.doFilterInternal(request, response, filterChain);

        verify(userDetailsService, times(1)).loadUserByUsername("testuser");
    }
    
    // @Test
    // void testJwtFilter_ValidToken_CacheHit() throws Exception {
    //     MockHttpServletRequest request = new MockHttpServletRequest();
    //     request.addHeader("Authorization", "Bearer valid.token.jwt");
    //     MockHttpServletResponse response = new MockHttpServletResponse();
    //     MockFilterChain filterChain = new MockFilterChain();

    //     UserDetails userDetails = new User("testuser", "pass", Collections.emptyList());

    //     when(jwtService.extractUsername("valid.token.jwt")).thenReturn("testuser");
    //     when(userDetailsService.loadUserByUsername("testuser")).thenReturn(userDetails);
    //     when(jwtService.isTokenValid("valid.token.jwt", userDetails)).thenReturn(true);

    //     // First call (cache miss)
    //     jwtAuthenticationFilter.doFilterInternal(request, response, filterChain);
    //     // Second call (cache hit)
    //     jwtAuthenticationFilter.doFilterInternal(request, response, filterChain);

    //     // Should still only be called once due to cache
    //     verify(userDetailsService, times(1)).loadUserByUsername("testuser");
    // }

    @Test
    void testJwtFilter_NoToken() throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest();
        MockHttpServletResponse response = new MockHttpServletResponse();
        MockFilterChain filterChain = new MockFilterChain();

        jwtAuthenticationFilter.doFilterInternal(request, response, filterChain);

        verify(jwtService, never()).extractUsername(anyString());
    }
    
    @Test
    void testJwtFilter_InvalidTokenPrefix() throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader("Authorization", "Basic some.other.token");
        MockHttpServletResponse response = new MockHttpServletResponse();
        MockFilterChain filterChain = new MockFilterChain();

        jwtAuthenticationFilter.doFilterInternal(request, response, filterChain);

        verify(jwtService, never()).extractUsername(anyString());
    }

    @Test
    void testJwtFilter_TokenExtractionError() throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader("Authorization", "Bearer bad.token");
        MockHttpServletResponse response = new MockHttpServletResponse();
        MockFilterChain filterChain = new MockFilterChain();

        when(jwtService.extractUsername("bad.token")).thenThrow(new RuntimeException("Expired"));

        jwtAuthenticationFilter.doFilterInternal(request, response, filterChain);

        verify(userDetailsService, never()).loadUserByUsername(anyString());
    }
    
    @Test
    void testJwtFilter_TokenValidServiceFails() throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader("Authorization", "Bearer valid.token.jwt");
        MockHttpServletResponse response = new MockHttpServletResponse();
        MockFilterChain filterChain = new MockFilterChain();

        UserDetails userDetails = new User("testuser", "pass", Collections.emptyList());

        when(jwtService.extractUsername("valid.token.jwt")).thenReturn("testuser");
        when(userDetailsService.loadUserByUsername("testuser")).thenReturn(userDetails);
        when(jwtService.isTokenValid("valid.token.jwt", userDetails)).thenReturn(false); // Service says invalid

        jwtAuthenticationFilter.doFilterInternal(request, response, filterChain);

        // We should not be authenticated
        assertNull(SecurityContextHolder.getContext().getAuthentication());
    }
}