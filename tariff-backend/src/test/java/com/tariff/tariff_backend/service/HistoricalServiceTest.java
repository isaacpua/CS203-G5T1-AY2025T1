package com.tariff.tariff_backend.service;

import com.tariff.tariff_backend.model.history.HistoricalResponse;
import com.tariff.tariff_backend.model.history.HistoryPreset;
import com.tariff.tariff_backend.model.history.Unit;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class HistoricalServiceTest {

    private final HistoricalService historicalService = new HistoricalService();

    @Test
    void getHistory_ShouldReturnMockData() {
        // Arrange
        LocalDate start = LocalDate.of(2023, 1, 1);
        LocalDate end = LocalDate.of(2023, 3, 1);

        // Act
        HistoricalResponse response = historicalService.getHistory("USA", "CHN", "12345", start, end, Unit.PERCENT);

        // Assert
        assertEquals("USA", response.getReporter());
        assertEquals("CHN", response.getPartner());
        assertEquals("12345", response.getItemCode());
        assertEquals(Unit.PERCENT, response.getUnit());
        assertEquals(start, response.getStartDate());
        assertEquals(end, response.getEndDate());
        
        // Should contain 3 data points (Jan, Feb, Mar)
        assertEquals(3, response.getPoints().size());
        assertEquals(start, response.getPoints().get(0).getDate());
        assertEquals(LocalDate.of(2023, 2, 1), response.getPoints().get(1).getDate());
    }

    @Test
    void getHistory_ShouldHandleNullDates() {
        // Act
        HistoricalResponse response = historicalService.getHistory(null, null, null, null, null, Unit.VALUE);

        // Assert
        assertNotNull(response.getStartDate());
        assertNotNull(response.getEndDate());
        assertTrue(response.getPoints().size() > 1); // Should generate default range
        assertEquals(Unit.VALUE, response.getUnit());
    }

    @Test
    void presets_ShouldReturnPresets() {
        // Act
        List<HistoryPreset> presets = historicalService.presets();

        // Assert
        assertNotNull(presets);
        assertFalse(presets.isEmpty());
        assertEquals("TW→SG Semiconductors", presets.get(0).getTitle());
    }
}