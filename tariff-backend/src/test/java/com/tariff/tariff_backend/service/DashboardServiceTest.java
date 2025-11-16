// src/test/java/com/tariff/tariff_backend/service/DashboardServiceTest.java
package com.tariff.tariff_backend.service;

import java.time.LocalDate;
import java.util.Collections;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;

import com.tariff.tariff_backend.dto.TariffPatchDTO;
import com.tariff.tariff_backend.model.dashboard.DashboardMetrics;
import com.tariff.tariff_backend.model.dashboard.DashboardResponse;
import com.tariff.tariff_backend.model.tariffs_new.Country;
import com.tariff.tariff_backend.model.tariffs_new.Tariff;
import com.tariff.tariff_backend.repository.CountryRepo;
import com.tariff.tariff_backend.repository.TariffRepo;

@ExtendWith(MockitoExtension.class)
class DashboardServiceTest {

    @Mock
    private TariffRepo tariffRepo;
    @Mock
    private CountryRepo countryRepo;
    @InjectMocks
    private DashboardService dashboardService;

    private Country countryA;
    private Country countryB;
    private Tariff tariff;
    private TariffPatchDTO tariffPatchDTO;

    @BeforeEach
    void setUp() {
        countryA = new Country();
        countryA.setName("CountryA");
        countryB = new Country();
        countryB.setName("CountryB");

        tariff = Tariff.builder()
                .tariffId("t1")
                .descriptionwcountry("Test Tariff")
                .partnerCountry(countryA)
                .reporterCountry(countryB)
                .year(2023)
                .build();

        tariffPatchDTO = new TariffPatchDTO(
                "t1", "Test Tariff", "CountryA", "CountryB",
                "kg", "Category", null, null,
                LocalDate.now(), null, "Source", 2023
        );
    }

    // --- createTariff Tests ---
    @Test
    void createTariff_ShouldSucceed() {
        when(countryRepo.findByName("CountryA")).thenReturn(List.of(countryA));
        when(countryRepo.findByName("CountryB")).thenReturn(List.of(countryB));
        when(tariffRepo.save(any(Tariff.class))).thenReturn(tariff);
        when(tariffRepo.existsById("t1")).thenReturn(true);

        DashboardResponse response = dashboardService.createTariff(tariffPatchDTO);

        assertTrue(response.getSuccess());
        assertEquals("Sucessfully created the new tariff.", response.getMessage());
        verify(tariffRepo, times(1)).save(any(Tariff.class));
    }

    @Test
    void createTariff_ShouldFail_WhenPartnerCountryNotFound() {
        when(countryRepo.findByName("CountryA")).thenReturn(Collections.emptyList());

        DashboardResponse response = dashboardService.createTariff(tariffPatchDTO);

        assertFalse(response.getSuccess());
        assertTrue(response.getMessage().contains("not found in database"));
        verify(tariffRepo, never()).save(any());
    }

    @Test
    void createTariff_ShouldFail_WhenReporterCountryNotFound() {
        when(countryRepo.findByName("CountryA")).thenReturn(List.of(countryA));
        when(countryRepo.findByName("CountryB")).thenReturn(Collections.emptyList());

        DashboardResponse response = dashboardService.createTariff(tariffPatchDTO);

        assertFalse(response.getSuccess());
        assertTrue(response.getMessage().contains("not found in database"));
        verify(tariffRepo, never()).save(any());
    }

    @Test
    void createTariff_ShouldFail_WhenSaveFails() {
        when(countryRepo.findByName("CountryA")).thenReturn(List.of(countryA));
        when(countryRepo.findByName("CountryB")).thenReturn(List.of(countryB));
        when(tariffRepo.save(any(Tariff.class))).thenReturn(tariff);
        when(tariffRepo.existsById("t1")).thenReturn(false); // Simulate save failure

        DashboardResponse response = dashboardService.createTariff(tariffPatchDTO);

        assertFalse(response.getSuccess());
        assertEquals("Unable to create the new tariff.", response.getMessage());
    }

    // --- updateTariff Tests ---
    @Test
    void updateTariff_ShouldSucceed() {
        when(tariffRepo.findById("t1")).thenReturn(Optional.of(tariff));
        when(countryRepo.findByName("CountryA")).thenReturn(List.of(countryA));
        when(countryRepo.findByName("CountryB")).thenReturn(List.of(countryB));

        DashboardResponse response = dashboardService.updateTariff("t1", tariffPatchDTO);

        assertTrue(response.getSuccess());
        assertEquals("Sucessfully updated the tariff.", response.getMessage());
        verify(tariffRepo, times(1)).save(tariff);
    }

    @Test
    void updateTariff_ShouldFail_WhenTariffNotFound() {
        when(tariffRepo.findById("t1")).thenReturn(Optional.empty());

        DashboardResponse response = dashboardService.updateTariff("t1", tariffPatchDTO);

        assertFalse(response.getSuccess());
        assertEquals("Tariff with ID t1 not found", response.getMessage());
        verify(tariffRepo, never()).save(any());
    }
    
    @Test
    void updateTariff_ShouldUpdateNullFields() {
        when(tariffRepo.findById("t1")).thenReturn(Optional.of(tariff));
        TariffPatchDTO nullDto = new TariffPatchDTO(); // All fields null
        nullDto.setEffectivedate(LocalDate.now()); // Set non-nullable field
        nullDto.setExpirydate(LocalDate.now()); // Set non-nullable field

        DashboardResponse response = dashboardService.updateTariff("t1", nullDto);

        assertTrue(response.getSuccess());
        verify(tariffRepo, times(1)).save(any(Tariff.class));
    }


    // --- deleteTariff Tests ---
    @Test
    void deleteTariff_ShouldSucceed() {
        when(tariffRepo.existsById("t1")).thenReturn(true).thenReturn(false); // Before delete, After delete

        DashboardResponse response = dashboardService.deleteTariff("t1");

        assertTrue(response.getSuccess());
        assertEquals("Sucessfully deleted the tariff.", response.getMessage());
        verify(tariffRepo, times(1)).deleteById("t1");
    }

    @Test
    void deleteTariff_ShouldFail_WhenTariffNotFound() {
        when(tariffRepo.existsById("t1")).thenReturn(false);

        DashboardResponse response = dashboardService.deleteTariff("t1");

        assertFalse(response.getSuccess());
        assertEquals("Tariff with ID t1 not found", response.getMessage());
        verify(tariffRepo, never()).deleteById(any());
    }

    @Test
    void deleteTariff_ShouldFail_WhenDeleteFails() {
        when(tariffRepo.existsById("t1")).thenReturn(true).thenReturn(true); // Before delete, After delete (still exists)

        DashboardResponse response = dashboardService.deleteTariff("t1");

        assertFalse(response.getSuccess());
        assertEquals("Failed to delete tariff with ID t1", response.getMessage());
        verify(tariffRepo, times(1)).deleteById("t1");
    }

    // --- getTariffs Tests (Branch Coverage) ---
    private Page<Tariff> mockPage() {
        return new PageImpl<>(List.of(tariff), Pageable.unpaged(), 1);
    }

    @Test
    void getTariffs_Branch1_NoYear_WithTariffId() {
        when(tariffRepo.findByTariffIdContaining(eq("t1"), any(Pageable.class))).thenReturn(mockPage());
        DashboardMetrics metrics = dashboardService.getTariffs("t1", null, Pageable.unpaged(), null, null);
        assertEquals(1, metrics.getTotalElements());
    }

    @Test
    void getTariffs_Branch2_NoYear_WithQuery() {
        when(tariffRepo.findByDescriptionwcountryContainingIgnoreCase(eq("Test"), any(Pageable.class))).thenReturn(mockPage());
        DashboardMetrics metrics = dashboardService.getTariffs(null, " Test ", Pageable.unpaged(), null, null); // Test trimming
        assertEquals(1, metrics.getTotalElements());
    }

    @Test
    void getTariffs_Branch3_NoYear_NoQuery() {
        when(tariffRepo.findAll(any(Pageable.class))).thenReturn(mockPage());
        DashboardMetrics metrics = dashboardService.getTariffs(null, null, Pageable.unpaged(), null, null);
        assertEquals(1, metrics.getTotalElements());
    }

    @Test
    void getTariffs_Branch4_WithYear_WithTariffId() {
        when(tariffRepo.findByYearBetweenAndTariffIdContaining(eq(2020), eq(2024), eq("t1"), any(Pageable.class))).thenReturn(mockPage());
        DashboardMetrics metrics = dashboardService.getTariffs("t1", null, Pageable.unpaged(), 2020, 2024);
        assertEquals(1, metrics.getTotalElements());
    }

    @Test
    void getTariffs_Branch5_WithYear_WithQuery() {
        when(tariffRepo.findByYearBetweenAndDescriptionwcountryContainingIgnoreCase(eq(2020), eq(2024), eq("Test"), any(Pageable.class))).thenReturn(mockPage());
        DashboardMetrics metrics = dashboardService.getTariffs(null, "Test", Pageable.unpaged(), 2020, 2024);
        assertEquals(1, metrics.getTotalElements());
    }

    @Test
    void getTariffs_Branch6_WithYear_NoQuery() {
        when(tariffRepo.findByYearBetween(eq(2020), eq(2024), any(Pageable.class))).thenReturn(mockPage());
        DashboardMetrics metrics = dashboardService.getTariffs(null, " ", Pageable.unpaged(), 2020, 2024); // Test blank query
        assertEquals(1, metrics.getTotalElements());
    }

    // --- getAllTariffs Test ---
    @Test
    void getAllTariffs_ShouldSucceed() {
        when(tariffRepo.findAll(any(Sort.class))).thenReturn(List.of(tariff));
        List<TariffPatchDTO> results = dashboardService.getAllTariffs();
        assertEquals(1, results.size());
        assertEquals("t1", results.get(0).getTariffId());
    }
}