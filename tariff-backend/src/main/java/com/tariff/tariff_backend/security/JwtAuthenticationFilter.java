package com.tariff.tariff_backend.security;

import com.tariff.tariff_backend.service.JwtService;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.lang.NonNull;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private static final Logger logger = LoggerFactory.getLogger(JwtAuthenticationFilter.class);

    @Autowired
    private UserDetailsService userDetailsService;

    @Autowired
    private JwtService jwtService;

    @Override
    protected void doFilterInternal(@NonNull HttpServletRequest request, @NonNull HttpServletResponse response, 
                                  @NonNull FilterChain filterChain) throws ServletException, IOException {

        // Get JWT token from request header
        String requestToken = request.getHeader("Authorization");
        String username = null;
        String token = null;

        // JWT token format: "Bearer <token>"
        if (requestToken != null && requestToken.startsWith("Bearer ")) {
            token = requestToken.substring(7);
            try {
                username = this.jwtService.extractUsername(token);
            } catch (Exception e) {
                logger.error("Error extracting username from JWT token: " + e.getMessage());
            }
        } else {
            logger.warn("JWT Token does not begin with Bearer String");
        }

        // Validate token
        if (username != null && SecurityContextHolder.getContext().getAuthentication() == null) {
            // Try cache first
            CachedUserDetails cached = userDetailsCache.get(username);
            UserDetails userDetails;
            if (cached != null && Instant.now().isBefore(cached.expiresAt)) {
                userDetails = cached.userDetails;
            } else {
                userDetails = this.userDetailsService.loadUserByUsername(username);
                if (userDetails != null) {
                    userDetailsCache.put(username, new CachedUserDetails(userDetails, Instant.now().plusSeconds(CACHE_TTL_SECONDS)));
                }
            }
            
            if (this.jwtService.isTokenValid(token, userDetails)) {
                // Token is valid, set authentication in context
                UsernamePasswordAuthenticationToken usernamePasswordAuthenticationToken = 
                    new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities());
                
                usernamePasswordAuthenticationToken.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                SecurityContextHolder.getContext().setAuthentication(usernamePasswordAuthenticationToken);
            } else {
                logger.warn("Invalid JWT Token");
            }
        }

        filterChain.doFilter(request, response);
    }
}
