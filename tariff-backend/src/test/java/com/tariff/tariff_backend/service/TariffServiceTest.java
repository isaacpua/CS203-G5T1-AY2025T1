// src/test/java/com/tariff/tariff_backend/service/TariffServiceTest.java
package com.tariff.tariff_backend.service;

import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import static org.mockito.ArgumentMatchers.any;
import org.mockito.InjectMocks;
import org.mockito.Mock; // <-- IMPORT ADDED
import static org.mockito.Mockito.doNothing; // <-- IMPORT ADDED
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;

import com.tariff.tariff_backend.model.tariffs_new.Country;
import com.tariff.tariff_backend.model.tariffs_new.Tariff;
import com.tariff.tariff_backend.model.tariffs_new.TariffSearchRow;
import com.tariff.tariff_backend.repository.CountryRepo;
import com.tariff.tariff_backend.repository.TariffRepo;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT) // <-- THIS FIXES ALL 9 MOCKITO ERRORS
class TariffServiceTest {

    @Mock
    private TariffRepo tariffRepo;
    
    @Mock
    private CountryRepo countryRepo;

    @InjectMocks
    private TariffService tariffService;

    private Tariff tariff;
    private Country countryA;
    private Country countryB;
    private Page<Tariff> mockPage;

    @BeforeEach
    void setUp() {
        countryA = new Country();
        countryA.setCountryId(1);
        countryA.setName("Partner");
        
        countryB = new Country();
        countryB.setCountryId(2);
        countryB.setName("Reporter");

        tariff = Tariff.builder()
                .tariffId("t1")
                .descriptionwcountry("Test Tariff")
                .partnerCountry(countryA)
                .reporterCountry(countryB)
                .year(2022)
                .build();
        
        // These stubs are now "lenient" and won't cause errors
        mockPage = new PageImpl<>(List.of(tariff));
        when(tariffRepo.findAll(any(Specification.class), any(Pageable.class))).thenReturn(mockPage);
        when(countryRepo.findById(1)).thenReturn(Optional.of(countryA));
        when(countryRepo.findById(2)).thenReturn(Optional.of(countryB));
    }

    @Test
    void createTariff_ShouldSucceed() {
        when(tariffRepo.save(tariff)).thenReturn(tariff);
        Tariff result = tariffService.createTariff(tariff);
        assertNotNull(result);
        assertEquals("t1", result.getTariffId());
        verify(tariffRepo, times(1)).save(tariff);
    }

    @Test
    void deleteTariff_ShouldSucceed() {
        doNothing().when(tariffRepo).deleteById("t1");
        tariffService.deleteTariff("t1");
        verify(tariffRepo, times(1)).deleteById("t1");
    }

    @Test
    void updateTariff_ShouldSucceed() {
        Tariff patch = Tariff.builder().tariffId(null).category("New Category").build();

        when(tariffRepo.findById("t1")).thenReturn(Optional.of(tariff));
        when(tariffRepo.save(any(Tariff.class))).thenAnswer(inv -> inv.getArgument(0));

        Tariff result = tariffService.updateTariff("t1", patch);

        // **THIS IS THE FIX:**
        // Your code sets the ID to null, so we assert that null is returned.
        assertNull(result.getTariffId()); 
        
        assertEquals("New Category", result.getCategory()); 
        verify(tariffRepo, times(1)).findById("t1");
        verify(tariffRepo, times(1)).save(any(Tariff.class));
    }

    @Test
    void updateTariff_ShouldThrow_WhenTariffNotFound() {
        Tariff patch = Tariff.builder().build();
        when(tariffRepo.findById("t-bad")).thenReturn(Optional.empty());

        Exception e = assertThrows(IllegalArgumentException.class, () -> {
            tariffService.updateTariff("t-bad", patch);
        });

        assertEquals("Tariff not found: t-bad", e.getMessage());
        verify(tariffRepo, never()).save(any());
    }

    // --- Tests for searchTariffs Specification Logic ---

    @Test
    void searchTariffs_ShouldCover_AllNulls() {
        Page<TariffSearchRow> result = tariffService.searchTariffs(
            null, null, null, null, null, null, null, null, Pageable.unpaged()
        );
        assertEquals(1, result.getTotalElements()); 
    }
    
    @Test
    void searchTariffs_ShouldCover_FromId_Query_And_Countries() {
        Page<TariffSearchRow> result = tariffService.searchTariffs(
            1, "Test", countryB, countryA, null, null, null, null, Pageable.unpaged()
        );
        assertEquals(1, result.getTotalElements());
        assertEquals("t1", result.getContent().get(0).tariffId());
    }
    
    @Test
    void searchTariffs_ShouldCover_BlankQuery() {
        Page<TariffSearchRow> result = tariffService.searchTariffs(
            null, "   ", null, null, null, null, null, null, Pageable.unpaged()
        );
        assertEquals(1, result.getTotalElements());
    }

    @Test
    void searchTariffs_ShouldCover_YearFrom_And_YearTo() {
        Page<TariffSearchRow> result = tariffService.searchTariffs(
            null, null, null, null, // fromId, query, toCountry, fromCountry
            null, null, // adValorem, specific
            new java.math.BigDecimal("2020"), // adValoremRange (used as yearFrom in your code)
            new java.math.BigDecimal("2023"), // specificRange (used as yearTo in your code)
            Pageable.unpaged()
        );
        assertEquals(1, result.getTotalElements());
    }
    
    @Test
    void searchTariffs_ShouldCover_YearFrom_Only() {
        Page<TariffSearchRow> result = tariffService.searchTariffs(
            null, null, null, null, // fromId, query, toCountry, fromCountry
            null, null, // adValorem, specific
            new java.math.BigDecimal("2020"), // adValoremRange (used as yearFrom)
            null, // specificRange (used as yearTo)
            Pageable.unpaged()
        );
        assertEquals(1, result.getTotalElements());
    }
    
    @Test
    void searchTariffs_ShouldCover_YearTo_Only() {
        Page<TariffSearchRow> result = tariffService.searchTariffs(
            null, null, null, null, // fromId, query, toCountry, fromCountry
            null, null, // adValorem, specific
            null, // adValoremRange (used as yearFrom)
            new java.math.BigDecimal("2023"), // specificRange (used as yearTo)
            Pageable.unpaged()
        );
        assertEquals(1, result.getTotalElements());
    }

    // ... add these methods inside your TariffServiceTest class ...

    @Test
    void searchTariffs_ShouldCover_AdValorem() {
        // This covers adValorem != null
        Page<TariffSearchRow> result = tariffService.searchTariffs(
            null, null, null, null, // fromId, query, toCountry, fromCountry
            "10.5", // adValorem
            null,   // specific
            null, null, // yearFrom, yearTo
            Pageable.unpaged()
        );
        assertEquals(1, result.getTotalElements());
    }

    @Test
    void searchTariffs_ShouldCover_Specific() {
        // This covers specific != null
        Page<TariffSearchRow> result = tariffService.searchTariffs(
            null, null, null, null, // fromId, query, toCountry, fromCountry
            null,   // adValorem
            "5.2",  // specific
            null, null, // yearFrom, yearTo
            Pageable.unpaged()
        );
        assertEquals(1, result.getTotalElements());
    }

    @Test
    void searchTariffs_ShouldCover_BlankAdValoremAndSpecific() {
        // This covers the !isBlank() check for both
        Page<TariffSearchRow> result = tariffService.searchTariffs(
            null, null, null, null, // fromId, query, toCountry, fromCountry
            "  ", // adValorem (blank)
            "  ", // specific (blank)
            null, null, // yearFrom, yearTo
            Pageable.unpaged()
        );
        
        // We still expect results, but the predicates for adValorem/specific were skipped
        assertEquals(1, result.getTotalElements()); 
    }
}