package com.tariff.tariff_backend.service;

import com.tariff.tariff_backend.dto.CalculationDTO.TransactionLineDTO;
import com.tariff.tariff_backend.model.User;
import com.tariff.tariff_backend.model.tariffs_new.TransactionLine;
import com.tariff.tariff_backend.repository.TransactionLineRepo;
import com.tariff.tariff_backend.repository.UserRepo;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
// FIX: Import these two lines
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT) // FIX: Add this line to solve the error
class CalculatorHistoryServiceTest {

    @Mock
    private TransactionLineRepo txRepo;
    @Mock
    private UserRepo userRepo;
    @InjectMocks
    private CalculatorHistoryService calculatorHistoryService;

    // Mocks for security context
    @Mock
    private Authentication authentication;
    @Mock
    private SecurityContext securityContext;

    private User testUser;
    private UUID testUserId = UUID.randomUUID();

    @BeforeEach
    void setUp() {
        // Mock the SecurityContextHolder to return a username
        when(securityContext.getAuthentication()).thenReturn(authentication);
        SecurityContextHolder.setContext(securityContext);

        testUser = User.builder().id(testUserId).username("test-user").build();
    }

    @Test
    void viewHistory_ShouldReturnUserHistory() {
        // Arrange
        when(authentication.getName()).thenReturn("test-user");
        when(userRepo.findByUsername("test-user")).thenReturn(Optional.of(testUser));

        Map<String, Object> snapshot = Map.of("total", 150.0);
        TransactionLine tx = new TransactionLine(1, testUser, Instant.now(), snapshot);
        when(txRepo.findByUser(testUser)).thenReturn(List.of(tx));

        // Act
        List<TransactionLineDTO> history = calculatorHistoryService.viewHistory();

        // Assert
        assertEquals(1, history.size());
        assertEquals(1, history.get(0).transactionId());
        assertEquals(150.0, history.get(0).snapshot().get("total"));
    }

    @Test
    void viewHistory_ShouldReturnEmptyList_WhenNoHistory() {
        // Arrange
        when(authentication.getName()).thenReturn("test-user");
        when(userRepo.findByUsername("test-user")).thenReturn(Optional.of(testUser));
        when(txRepo.findByUser(testUser)).thenReturn(Collections.emptyList());

        // Act
        List<TransactionLineDTO> history = calculatorHistoryService.viewHistory();

        // Assert
        assertTrue(history.isEmpty());
    }

    @Test
    void deleteOwn_ShouldDelete_WhenUserOwnsTransaction() {
        // Arrange
        when(authentication.getName()).thenReturn("test-user");
        when(userRepo.findByUsername("test-user")).thenReturn(Optional.of(testUser));
        when(txRepo.deleteByTransactionIdAndUserId(123, testUserId)).thenReturn(1L); // 1 row deleted

        // Act & Assert
        assertDoesNotThrow(() -> {
            calculatorHistoryService.deleteOwn(123, authentication);
        });
        verify(txRepo, times(1)).deleteByTransactionIdAndUserId(123, testUserId);
    }

    @Test
    void deleteOwn_ShouldThrow_WhenTransactionNotFound() {
        // Arrange
        when(authentication.getName()).thenReturn("test-user");
        when(userRepo.findByUsername("test-user")).thenReturn(Optional.of(testUser));
        when(txRepo.deleteByTransactionIdAndUserId(404, testUserId)).thenReturn(0L); // 0 rows deleted

        // Act & Assert
        ResponseStatusException e = assertThrows(ResponseStatusException.class, () -> {
            calculatorHistoryService.deleteOwn(404, authentication);
        });
        assertEquals(HttpStatus.NOT_FOUND, e.getStatusCode());
        assertEquals("Transaction not found", e.getReason());
    }
}