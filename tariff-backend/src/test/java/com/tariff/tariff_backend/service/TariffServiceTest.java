// src/test/java/com/tariff/tariff_backend/service/TariffServiceTest.java
package com.tariff.tariff_backend.service;

import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import static org.mockito.ArgumentMatchers.any;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;

import com.tariff.tariff_backend.model.tariffs_new.Country;
import com.tariff.tariff_backend.model.tariffs_new.Tariff;
import com.tariff.tariff_backend.model.tariffs_new.TariffSearchRow;
import com.tariff.tariff_backend.repository.TariffRepo;

@ExtendWith(MockitoExtension.class)
class TariffServiceTest {

    @Mock
    private TariffRepo tariffRepo;
    @InjectMocks
    private TariffService tariffService;

    private Tariff tariff;
    private Country countryA;
    private Country countryB;

    @BeforeEach
    void setUp() {
        countryA = new Country();
        countryA.setName("Partner");
        countryB = new Country();
        countryB.setName("Reporter");

        tariff = Tariff.builder()
                .tariffId("t1")
                .descriptionwcountry("Test Tariff")
                .partnerCountry(countryA)
                .reporterCountry(countryB)
                .build();
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

    // @Test
    // void updateTariff_ShouldSucceed() {
    //     Tariff patch = Tariff.builder().category("New Category").build();

    //     when(tariffRepo.findById("t1")).thenReturn(Optional.of(tariff));
    //     when(tariffRepo.save(any(Tariff.class))).thenAnswer(inv -> inv.getArgument(0));

    //     Tariff result = tariffService.updateTariff("t1", patch);

    //     assertEquals("t1", result.getTariffId());
    //     assertEquals("New Category", result.getCategory()); // Check that field was updated
    //     verify(tariffRepo, times(1)).findById("t1");
    //     verify(tariffRepo, times(1)).save(any(Tariff.class));
    // }

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

    @Test
    void searchTariffs_ShouldSucceedAndMapToRow() {
        // This test also covers the private 'toRow' method
        Page<Tariff> mockPage = new PageImpl<>(List.of(tariff));
        when(tariffRepo.findAll(any(Specification.class), any(Pageable.class))).thenReturn(mockPage);

        Page<TariffSearchRow> result = tariffService.searchTariffs(
                null, "Test", countryA, countryB,
                null, null, null, null, Pageable.unpaged()
        );

        assertEquals(1, result.getTotalElements());
        TariffSearchRow row = result.getContent().get(0);
        assertEquals("t1", row.tariffId());
        assertEquals("Test Tariff", row.descriptionwcountry());
        assertEquals("Partner", row.partnerCountry().getName());
        
        // Also test the specification builder with all-nulls
        tariffService.searchTariffs(null, null, null, null, null, null, null, null, Pageable.unpaged());
        verify(tariffRepo, times(2)).findAll(any(Specification.class), any(Pageable.class));
    }
}