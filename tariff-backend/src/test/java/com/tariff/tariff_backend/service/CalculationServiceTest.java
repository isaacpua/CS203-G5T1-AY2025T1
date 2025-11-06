package com.tariff.tariff_backend.service;

import com.tariff.tariff_backend.dto.CalculationDTO.CalculateDutyRequest;
import com.tariff.tariff_backend.dto.CalculationDTO.CalculateDutyResponse;
import com.tariff.tariff_backend.model.User;
import com.tariff.tariff_backend.model.tariffs_new.Country;
import com.tariff.tariff_backend.model.tariffs_new.Tariff;
import com.tariff.tariff_backend.model.tariffs_new.TransactionLine;
import com.tariff.tariff_backend.repository.TariffRepo;
import com.tariff.tariff_backend.repository.TransactionLineRepo;
import com.tariff.tariff_backend.repository.UserRepo;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
// FIX: Imports for Mockito strictness
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;

import java.math.BigDecimal;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT) // FIX: Solves the UnnecessaryStubbingException
class CalculationServiceTest {

    @Mock
    private TariffRepo tariffRepo;
    @Mock
    private TransactionLineRepo txRepo;
    @Mock
    private UserRepo userRepo;
    @InjectMocks
    private CalculationService calculationService;

    // Mocks for security context
    @Mock
    private Authentication authentication;
    @Mock
    private SecurityContext securityContext;

    private User testUser;
    private Tariff adValoremTariff, specificTariff, compositeTariff, freeTariff;

    @BeforeEach
    void setUp() {
        // Mock the SecurityContextHolder to return a username
        when(securityContext.getAuthentication()).thenReturn(authentication);
        when(authentication.getName()).thenReturn("test-user");
        SecurityContextHolder.setContext(securityContext);

        testUser = User.builder().id(UUID.randomUUID()).username("test-user").build();

        // Mock tariffs for different categories
        adValoremTariff = Tariff.builder()
                .tariffId("t-advalorem")
                .category("ad_valorem")
                .adValorem(new BigDecimal("0.05")) // 5%
                .specificPerUnit(null)
                .partnerCountry(new Country())
                .reporterCountry(new Country())
                .build();

        specificTariff = Tariff.builder()
                .tariffId("t-specific")
                .category("specific_per_unit")
                .adValorem(null)
                .specificPerUnit(new BigDecimal("5.0")) // $5 per unit
                .partnerCountry(new Country())
                .reporterCountry(new Country())
                .build();

        compositeTariff = Tariff.builder()
                .tariffId("t-composite")
                .category("composite")
                .adValorem(new BigDecimal("0.10")) // 10%
                .specificPerUnit(new BigDecimal("2.0")) // $2 per unit
                .partnerCountry(new Country())
                .reporterCountry(new Country())
                .build();

        freeTariff = Tariff.builder()
                .tariffId("t-free")
                .category("free")
                .partnerCountry(new Country())
                .reporterCountry(new Country())
                .build();
    }

    @Test
    void calculateAndStore_AdValorem_ShouldSucceed() {
        // Arrange
        CalculateDutyRequest request = new CalculateDutyRequest("t-advalorem", new BigDecimal("1000.00"), new BigDecimal("10"), false);
        when(tariffRepo.findById("t-advalorem")).thenReturn(Optional.of(adValoremTariff));
        when(userRepo.findByUsername("test-user")).thenReturn(Optional.of(testUser));

        // Act
        CalculateDutyResponse response = calculationService.calculateAndStore(request);

        // Assert
        // 1000.00 * (1 + 0.05) = 1050.00
        // FIX: Use compareTo to check BigDecimal value regardless of scale
        assertEquals(0, new BigDecimal("1050.00").compareTo(response.total()));
    }

    @Test
    void calculateAndStore_Specific_ShouldSucceed() {
        // Arrange
        CalculateDutyRequest request = new CalculateDutyRequest("t-specific", new BigDecimal("1000.00"), new BigDecimal("10"), false);
        when(tariffRepo.findById("t-specific")).thenReturn(Optional.of(specificTariff));
        when(userRepo.findByUsername("test-user")).thenReturn(Optional.of(testUser));

        // Act
        CalculateDutyResponse response = calculationService.calculateAndStore(request);

        // Assert
        // 10 * 5.0 = 50.0
        assertEquals(0, new BigDecimal("50.0").compareTo(response.total()));
    }

    @Test
    void calculateAndStore_Composite_ShouldSucceed() {
        // Arrange
        CalculateDutyRequest request = new CalculateDutyRequest("t-composite", new BigDecimal("1000.00"), new BigDecimal("10"), false);
        when(tariffRepo.findById("t-composite")).thenReturn(Optional.of(compositeTariff));
        when(userRepo.findByUsername("test-user")).thenReturn(Optional.of(testUser));

        // Act
        CalculateDutyResponse response = calculationService.calculateAndStore(request);

        // Assert
        // specPart = 10 * 2.0 = 20.0
        // total = 20.0 * (1 + 0.10) = 22.00
        // FIX: Use compareTo to check BigDecimal value regardless of scale
        assertEquals(0, new BigDecimal("22.00").compareTo(response.total()));
    }
    
    @Test
    void calculateAndStore_Free_ShouldSucceed() {
        // Arrange
        CalculateDutyRequest request = new CalculateDutyRequest("t-free", null, null, false);
        when(tariffRepo.findById("t-free")).thenReturn(Optional.of(freeTariff));
        when(userRepo.findByUsername("test-user")).thenReturn(Optional.of(testUser));

        // Act
        CalculateDutyResponse response = calculationService.calculateAndStore(request);

        // Assert
        assertEquals(0, BigDecimal.ZERO.compareTo(response.total()));
    }

    @Test
    void calculateAndStore_ShouldSaveTransaction_WhenSaveIsTrue() {
        // Arrange
        CalculateDutyRequest request = new CalculateDutyRequest("t-advalorem", new BigDecimal("1000.00"), new BigDecimal("10"), true);
        TransactionLine savedTx = new TransactionLine();
        savedTx.setTransactionId(123);

        when(tariffRepo.findById("t-advalorem")).thenReturn(Optional.of(adValoremTariff));
        when(userRepo.findByUsername("test-user")).thenReturn(Optional.of(testUser));
        when(txRepo.save(any(TransactionLine.class))).thenReturn(savedTx);

        // Act
        CalculateDutyResponse response = calculationService.calculateAndStore(request);

        // Assert
        verify(txRepo, times(1)).save(any(TransactionLine.class));
        assertEquals(123, response.transactionId());
    }

    @Test
    void calculateAndStore_ShouldNotSave_WhenSaveIsFalse() {
        // Arrange
        CalculateDutyRequest request = new CalculateDutyRequest("t-advalorem", new BigDecimal("1000.00"), new BigDecimal("10"), false);

        when(tariffRepo.findById("t-advalorem")).thenReturn(Optional.of(adValoremTariff));
        when(userRepo.findByUsername("test-user")).thenReturn(Optional.of(testUser));

        // Act
        CalculateDutyResponse response = calculationService.calculateAndStore(request);

        // Assert
        verify(txRepo, never()).save(any(TransactionLine.class));
        assertNull(response.transactionId());
    }

    @Test
    void calculateAndStore_ShouldThrow_WhenTariffNotFound() {
        // Arrange
        CalculateDutyRequest request = new CalculateDutyRequest("t-bad", new BigDecimal("1000.00"), new BigDecimal("10"), false);
        when(tariffRepo.findById("t-bad")).thenReturn(Optional.empty());

        // Act & Assert
        Exception e = assertThrows(IllegalArgumentException.class, () -> {
            calculationService.calculateAndStore(request);
        });
        assertEquals("Tariff not found: t-bad", e.getMessage());
    }

    @Test
    void calculateAndStore_ShouldThrow_WhenUserNotFound() {
        // Arrange
        CalculateDutyRequest request = new CalculateDutyRequest("t-advalorem", new BigDecimal("1000.00"), new BigDecimal("10"), false);
        when(tariffRepo.findById("t-advalorem")).thenReturn(Optional.of(adValoremTariff));
        when(userRepo.findByUsername("test-user")).thenReturn(Optional.empty());

        // Act & Assert
        Exception e = assertThrows(IllegalArgumentException.class, () -> {
            calculationService.calculateAndStore(request);
        });
        assertEquals("User not found: test-user", e.getMessage());
    }
}